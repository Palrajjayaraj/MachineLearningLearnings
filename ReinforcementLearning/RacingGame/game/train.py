import gymnasium as gym
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.logger import configure
from src.gym_env import RacingGameEnv
import os
import signal
import sys

# =========================================================
# =========================================================
# CONFIGURATION
# =========================================================
BASE_DIR = "modelTraining"
LOG_DIR = os.path.join(BASE_DIR, "logs")
MODEL_DIR = os.path.join(BASE_DIR, "models")

TOTAL_TIMESTEPS = 50_000_000  # Overnight: 50M steps for better learning
CHECK_FREQ = 10_000  # Steps (not episodes) to verify/render
FRAME_SKIP = 8  # Increased from 4 to reduce zigzagging and speed up simulation
CHECKPOINT_FREQ = 1_000_000  # Save checkpoint every 1M steps
MODEL_PATH = os.path.join(MODEL_DIR, "road_fighter_ppo")


class PeriodicRenderCallback(BaseCallback):
    """
    Custom Callback to visualize the agent's performance periodically.
    It pauses training to run ONE episode in 'human' render mode.
    """
    def __init__(self, check_freq: int, verbose=1):
        super().__init__(verbose)
        self.check_freq = check_freq

    def _on_step(self) -> bool:
        if self.n_calls % self.check_freq == 0:
            print(f"\n--- Visualizing Performance at Step {self.num_timesteps} ---")
            
            # Create a separate environment for visualization
            # We must use 'human' render mode here
            test_env = RacingGameEnv(render_mode="human", frame_skip=FRAME_SKIP)
            obs, _ = test_env.reset()
            done = False
            total_reward = 0
            
            while not done:
                # Predict action using the current model
                action, _ = self.model.predict(obs, deterministic=True)
                
                # Step the environment
                obs, reward, terminated, truncated, _ = test_env.step(action)
                done = terminated or truncated
                total_reward += reward
                
                # Render is handled automatically by the env in human mode
                test_env.render()
                
            test_env.close()
            print(f"--- Visualization Complete. Score: {total_reward:.2f} ---\n")
            
        return True

import csv
import datetime

class CheckpointCallback(BaseCallback):
    """
    Saves model checkpoints periodically during training.
    """
    def __init__(self, save_freq: int, save_path: str, verbose=1):
        super().__init__(verbose)
        self.save_freq = save_freq
        self.save_path = save_path
        self.checkpoint_count = 0

    def _on_step(self) -> bool:
        if self.n_calls % self.save_freq == 0:
            self.checkpoint_count += 1
            checkpoint_path = f"{self.save_path}_checkpoint_{self.checkpoint_count}"
            self.model.save(checkpoint_path)
            print(f"\n💾 Checkpoint saved at {self.num_timesteps} steps: {checkpoint_path}.zip\n")
        return True

class CSVLoggingCallback(BaseCallback):
    """
    Logs episode results to a CSV file.
    """
    def __init__(self, log_dir: str, verbose=1):
        super().__init__(verbose)
        self.log_dir = log_dir
        self.log_path = os.path.join(log_dir, "training_log.csv")
        # Ensure log dir exists
        os.makedirs(log_dir, exist_ok=True)
        
        # Initialize CSV with headers if it doesn't exist
        if not os.path.exists(self.log_path):
            with open(self.log_path, mode='w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Timestamp", "Step", "EpisodeLen", "Reward", "Distance", "Score", "EndReason", "Victory", "GreenPassed", "YellowPassed", "RedPassed"])
        
        # Track last step to calculate duration
        self.last_step = 0

    def _on_step(self) -> bool:
        # Check if any episode ended
        # 'dones' is a boolean array for vectorized envs
        dones = self.locals.get("dones", [False])
        infos = self.locals.get("infos", [{}])
        
        current_step = self.num_timesteps
        
        for idx, done in enumerate(dones):
            if done:
                info = infos[idx]
                
                # Calculate Duration
                # We assume single env for simplicity of this calc
                episode_len = current_step - self.last_step
                self.last_step = current_step
                
                # Extract stats
                reward = info.get('episode', {}).get('r', 0)
                distance = info.get('distance', 0)
                score = info.get('score', 0)
                end_reason = info.get('end_reason', 'unknown')
                victory = info.get('victory', False)
                ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Extract Car Stats (Default to 0 if missing)
                cars_passed = info.get('cars_passed', {})
                green = cars_passed.get('green', 0)
                yellow = cars_passed.get('yellow', 0)
                red = cars_passed.get('red', 0)
                
                with open(self.log_path, mode='a', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([ts, current_step, episode_len, f"{reward:.2f}", f"{distance:.1f}", score, end_reason, victory, green, yellow, red])
                    
        return True

# Global variable to handle graceful shutdown
model_to_save = None

def signal_handler(sig, frame):
    """
    Handles Ctrl+C (SIGINT) gracefully by saving the model before exit.
    """
    print("\n\n🛑 Training interrupted by user (Ctrl+C)...")
    if model_to_save is not None:
        interrupt_path = f"{MODEL_PATH}_interrupted"
        model_to_save.save(interrupt_path)
        print(f"💾 Model saved to: {interrupt_path}.zip")
        print("✅ You can resume training later by choosing 'y' when prompted.")
    else:
        print("⚠️ No model to save yet.")
    sys.exit(0)

def main():
    global model_to_save
    
    # Register signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    final_model_path = f"{MODEL_PATH}_final.zip"
    interrupted_path = f"{MODEL_PATH}_interrupted.zip"
    resume_training = False
    
    # 0. User Decision Loop
    model_to_load = None
    if os.path.exists(final_model_path):
        model_to_load = final_model_path
        print(f"\n⚠️  Found existing FINAL model: {final_model_path}")
    elif os.path.exists(interrupted_path):
        model_to_load = interrupted_path
        print(f"\n⚠️  Found INTERRUPTED model: {interrupted_path}")
    
    if model_to_load:
        while True:
            choice = input(f"Do you want to RESUME training (y) or START FRESH (n)? [y/n]: ").strip().lower()
            if choice == 'y':
                resume_training = True
                print("🔄 OK, Resuming Training...")
                break
            elif choice == 'n':
                resume_training = False
                print("✨ OK, Starting Fresh Session...")
                break
            else:
                print("Please enter 'y' or 'n'.")
    else:
        print("✨ No existing model found. Starting New Session.")
        resume_training = False

    # 0.5 Clean up logs ONLY if starting fresh
    if not resume_training:
        if os.path.exists(LOG_DIR):
            import shutil
            print(f"🧹 Cleaning up old logs in {LOG_DIR}...")
            shutil.rmtree(LOG_DIR)
    else:
        print(f"📂 Keeping existing logs in {LOG_DIR} (Appending)...")

    # 1. Create Headless Training Environment
    # Use 8 parallel environments for ~8x speedup (overnight training)
    train_env = make_vec_env(lambda: RacingGameEnv(frame_skip=FRAME_SKIP), n_envs=8)

    # 2. Initialize PPO Model
    if resume_training:
        try:
            model = PPO.load(
                model_to_load, 
                env=train_env,
                tensorboard_log=LOG_DIR 
            )
            print("✅ Model loaded successfully.")
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            print("Falling back to new model.")
            model = PPO(
                "MlpPolicy", 
                train_env, 
                verbose=1,
                learning_rate=3e-4,
                ent_coef=0.1, 
                batch_size=256,   
                n_epochs=20,       
                tensorboard_log=LOG_DIR
            )
    else:
        model = PPO(
            "MlpPolicy", 
            train_env, 
            verbose=1,
            learning_rate=3e-4,
            ent_coef=0.1, 
            batch_size=256,   
            n_epochs=20,       
            tensorboard_log=LOG_DIR
        )
    
    # Set global reference for signal handler
    model_to_save = model

    print("\n" + "="*60)
    print("🚀 STARTING OVERNIGHT TRAINING")
    print("="*60)
    print(f"📊 Total Steps: {TOTAL_TIMESTEPS:,}")
    print(f"🎮 Parallel Envs: 8")
    print(f"⚡ Frame Skip: {FRAME_SKIP} (reduced zigzagging)")
    print(f"💾 Checkpoints: Every {CHECKPOINT_FREQ:,} steps")
    print(f"🛑 Safe Interrupt: Press Ctrl+C to save and exit")
    print(f"📁 Logs: {LOG_DIR}/")
    print("="*60 + "\n")
    
    # Configure Logger to write to CSV
    # This captures the 'ep_len_mean', 'loss', etc.
    new_logger = configure(LOG_DIR, ["stdout", "csv", "tensorboard"])
    model.set_logger(new_logger)

    # 3. Train with Callback
    if not os.path.exists(MODEL_DIR):
        os.makedirs(MODEL_DIR)
        
    # Combine callbacks - VISUALIZATION DISABLED for speed
    callbacks = [
        CheckpointCallback(save_freq=CHECKPOINT_FREQ, save_path=MODEL_PATH),
        CSVLoggingCallback(log_dir=LOG_DIR)
    ]
        
    model.learn(
        total_timesteps=TOTAL_TIMESTEPS, 
        callback=callbacks
    )
    
    # 4. Save Final Model
    model.save(f"{MODEL_PATH}_final")
    print("Training Complete. Model Saved.")

if __name__ == "__main__":
    main()
