import gymnasium as gym
from gymnasium import spaces
import numpy as np
import pygame
from .core import RoadFighterGame

class RacingGameEnv(gym.Env):
    """Gymnasium-compatible wrapper for RoadFighterGame"""
    
    metadata = {"render_modes": ["human"], "render_fps": 60}
    
    def __init__(self, render_mode=None):
        super().__init__()
        # Core Game Logic (Headless)
        self.game = RoadFighterGame()
        self.render_mode = render_mode
        self.renderer = None
        
        # Initialize Renderer only if needed
        if self.render_mode == "human":
            from .renderer import GameRenderer
            self.renderer = GameRenderer()
        
        # Define action space: 0=nothing, 1=left, 2=right, 3=brake
        self.action_space = spaces.Discrete(4)
        
        # Define observation space: 20 continuous features [0, 1]
        self.observation_space = spaces.Box(
            low=0.0, high=1.0, shape=(20,), dtype=np.float32
        )
    
    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        state_vec = self.game.reset()
        return np.array(state_vec, dtype=np.float32), {}
    
    def step(self, action):
        # Convert discrete action to game controls
        left = (action == 1)
        right = (action == 2)
        brake = (action == 3)
        
        # Step the core logic
        state, raw_reward, done, info = self.game.step(left, right, brake)
        
        # ML Reward Shaping (moved from Engine to Here)
        # This keeps the engine pure and allows experimenting with rewards here
        
        # 1. Base reward from engine (distance based)
        reward = raw_reward
        
        # 2. Add extra shaping logic here if needed
        # (Initially matching original logic)
        
        # 3. Penalties from core tracking
        if self.game.lane_camping_mode:
            reward -= 0.5
        
        if self.game.player.is_changing_lane:
            reward -= 0.05
            
        # Passing bonus constraint check
        # (Core engine adds this to 'score' or similar usually, 
        # but if we want RL specific bonus we can track diff)
        
        truncated = False
        
        return (
            np.array(state, dtype=np.float32),
            float(reward),
            done,
            truncated,
            info
        )
    
    def render(self):
        if self.render_mode == "human" and self.renderer:
            self.renderer.render(self.game)
    
    def close(self):
        if pygame.get_init():
            pygame.quit()
