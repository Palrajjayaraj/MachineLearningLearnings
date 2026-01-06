import gymnasium as gym
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.logger import configure
from src.gym_env import RacingGameEnv
import os

# =========================================================
# =========================================================
# CONFIGURATION
# =========================================================
BASE_DIR = "modelTraining"
LOG_DIR = os.path.join(BASE_DIR, "logs")
MODEL_DIR = os.path.join(BASE_DIR, "models")

TOTAL_TIMESTEPS = 1_00_000
CHECK_FREQ = 10_000  # Steps (not episodes) to verify/render
FRAME_SKIP = 4
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
                writer.writerow(["Timestamp", "Step", "EpisodeLen", "Reward", "Distance", "Score", "EndReason", "Victory"])
        
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
                # We assume single env for simplicity of this calc, or we track per-env.
                # Since n_envs=1, this is simple.
                episode_len = current_step - self.last_step
                self.last_step = current_step
                
                # Extract stats
                reward = info.get('episode', {}).get('r', 0) # Total reward from Monitor wrapper if present
                
                distance = info.get('distance', 0)
                score = info.get('score', 0)
                end_reason = info.get('end_reason', 'unknown')
                victory = info.get('victory', False)
                ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                with open(self.log_path, mode='a', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([ts, current_step, episode_len, f"{reward:.2f}", f"{distance:.1f}", score, end_reason, victory])
                    
        return True

def main():
    final_model_path = f"{MODEL_PATH}_final.zip"
    resume_training = False
    
    # 0. User Decision Loop
    if os.path.exists(final_model_path):
        print(f"\n⚠️  Found existing model: {final_model_path}")
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
    # We use a Vectorized Environment for efficiency (allows parallel training if needed)
    # For now, 1 env is fine.
    train_env = make_vec_env(lambda: RacingGameEnv(frame_skip=FRAME_SKIP), n_envs=1)

    # 2. Initialize PPO Model
    if resume_training:
        try:
            model = PPO.load(
                final_model_path, 
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
                ent_coef=0.01, 
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
            ent_coef=0.01, 
            batch_size=256,   
            n_epochs=20,       
            tensorboard_log=LOG_DIR
        )

    print("Starting Training... (Headless)")
    print(f" visualization will occur every {CHECK_FREQ} steps.")
    print(f" Logging to {LOG_DIR}/training_log.csv (Episodes) and {LOG_DIR}/progress.csv (Training Stats)")
    
    # Configure Logger to write to CSV
    # This captures the 'ep_len_mean', 'loss', etc.
    new_logger = configure(LOG_DIR, ["stdout", "csv", "tensorboard"])
    model.set_logger(new_logger)

    # 3. Train with Callback
    if not os.path.exists(MODEL_DIR):
        os.makedirs(MODEL_DIR)
        
    # Combine callbacks
    callbacks = [
        PeriodicRenderCallback(check_freq=CHECK_FREQ),
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
