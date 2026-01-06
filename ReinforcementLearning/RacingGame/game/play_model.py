import gymnasium as gym
from stable_baselines3 import PPO
from src.gym_env import RacingGameEnv
import os
import time

# =========================================================
# CONFIGURATION
# =========================================================
BASE_MODEL_TRAINING_DIR_NAME = "modelTraining"
MODEL_PATH = os.path.join(BASE_MODEL_TRAINING_DIR_NAME, "models", "road_fighter_ppo_final")
FRAME_SKIP = 4

def main():
    print(f"Loading model from: {MODEL_PATH}")
    
    # 1. Check if model exists
    if not os.path.exists(f"{MODEL_PATH}.zip"):
        print(f"❌ Error: Model file '{MODEL_PATH}.zip' not found.")
        print("Did you run 'python train.py' first?")
        return

    # 2. Create Environment (Human Render Mode)
    # We want to see the game, so render_mode="human"
    env = RacingGameEnv(render_mode="human", frame_skip=FRAME_SKIP)
    
    # 3. Load the Trained Agent
    model = PPO.load(MODEL_PATH)
    
    print("\n🎮 Starting Replay... Press ESC to Quit.")
    
    episodes = 0
    while True:
        episodes += 1
        obs, _ = env.reset()
        done = False
        total_reward = 0
        
        print(f"--- Episode {episodes} ---")
        
        while not done:
            # Predict action (Deterministic = Best known action)
            action, _ = model.predict(obs, deterministic=True)
            
            # Step environment
            obs, reward, terminated, truncated, _ = env.step(action)
            done = terminated or truncated
            total_reward += reward
            
            # Render the game
            env.render()
            
            # Optional: Slow down slightly if needed, though renderer caps FPS
            # time.sleep(0.01) 
            
        print(f"Episode Finished. Total Neural Reward: {total_reward:.2f}")
        
        # Determine if we should quit based on pygame events (handled in env)
        # If the window was closed, env.close() handles it usually, 
        # but let's check if we can detect quit.
        # Ideally, we just loop until the user kills the window.

if __name__ == "__main__":
    main()
