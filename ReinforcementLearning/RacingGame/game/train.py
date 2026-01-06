import gymnasium as gym
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.env_util import make_vec_env
from src.gym_env import RacingGameEnv
import os

# =========================================================
# CONFIGURATION
# =========================================================
TOTAL_TIMESTEPS = 1_000_000
CHECK_FREQ = 10_000  # Steps (not episodes) to verify/render
FRAME_SKIP = 4
MODEL_PATH = "models/road_fighter_ppo"

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

def main():
    # 1. Create Headless Training Environment
    # We use a Vectorized Environment for efficiency (allows parallel training if needed)
    # For now, 1 env is fine.
    train_env = make_vec_env(lambda: RacingGameEnv(frame_skip=FRAME_SKIP), n_envs=1)

    # 2. Initialize PPO Model
    # Check if a saved model exists to resume training
    final_model_path = f"{MODEL_PATH}_final.zip"
    
    if os.path.exists(final_model_path):
        print(f"🔄 Resuming training from: {final_model_path}")
        # Load the model, attaching the new environment
        # We pass other parameters (ent_coef, etc.) via custom_objects or keyword args if we wanted to change them,
        # but usually loading preserves the core policy. 
        # However, to be safe with hyperparameters like learning_rate if we changed them, we can set them.
        # Simple load is best for now.
        model = PPO.load(
            final_model_path, 
            env=train_env,
            tensorboard_log="./logs/" # Ensure logging continues
        )
        
        # NOTE: If we drastically changed hyperparameters (like batch_size), 
        # PPO.load might stick to the old ones saved in the zip.
        # But for 'Continuing', this is fine.
        
    else:
        print("✨ Starting New Training Session")
        # MlpPolicy is standard for vector inputs (State V3)
        model = PPO(
            "MlpPolicy", 
            train_env, 
            verbose=1,
            learning_rate=3e-4,
            ent_coef=0.01, # Encourage exploration
            batch_size=256,    # <--- NEW: Bigger chunks
            n_epochs=20,       # <--- NEW: Study harder
            tensorboard_log="./logs/"
        )

    print("Starting Training... (Headless)")
    print(f" visualization will occur every {CHECK_FREQ} steps.")

    # 3. Train with Callback
    if not os.path.exists("models"):
        os.makedirs("models")
        
    model.learn(
        total_timesteps=TOTAL_TIMESTEPS, 
        callback=PeriodicRenderCallback(check_freq=CHECK_FREQ)
    )
    
    # 4. Save Final Model
    model.save(f"{MODEL_PATH}_final")
    print("Training Complete. Model Saved.")

if __name__ == "__main__":
    main()
