import gymnasium as gym
from gymnasium import spaces
import numpy as np
import pygame
from .core import RoadFighterGame

class RacingGameEnv(gym.Env):
    """Gymnasium-compatible wrapper for RoadFighterGame"""
    
    metadata = {"render_modes": ["human"], "render_fps": 60}
    
    def __init__(self, render_mode=None, frame_skip=4):
        super().__init__()
        # Core Game Logic (Headless)
        self.game = RoadFighterGame()
        self.render_mode = render_mode
        self.renderer = None
        self.frame_skip = frame_skip
        
        # Initialize Renderer only if needed
        if self.render_mode == "human":
            from .renderer import GameRenderer
            self.renderer = GameRenderer()
        
        # Define action space: 0=nothing, 1=left, 2=right, 3=brake
        self.action_space = spaces.Discrete(4)
        
        # Define observation space: 32 continuous features (State V3)
        # Player[4] + Global[3] + 5 * Objects[5]
        # Range includes negative relative coordinates, so use ample bounds
        self.observation_space = spaces.Box(
            low=-3.0, high=3.0, shape=(32,), dtype=np.float32
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
        
        total_reward = 0.0
        terminated = False
        truncated = False
        final_info = {}
        
        # Frame Skipping Loop
        # If frame_skip=1, this loop runs once (Standard 60Hz)
        # If frame_skip=4, this loop runs 4 times (15Hz)
        for _ in range(self.frame_skip):
            # Step the core logic
            state, raw_reward, done, info = self.game.step(left, right, brake)
            
            # 1. Base reward from engine
            reward = raw_reward
            
            # 2. Penalties from core tracking
            if self.game.lane_camping_mode:
                reward -= 0.5
            
            if self.game.player.is_changing_lane:
                reward -= 0.05
                
            total_reward += reward
            final_info = info # Keep latest info
            
            if done:
                terminated = True
                break
        
        return (
            np.array(state, dtype=np.float32),
            float(total_reward),
            terminated,
            truncated,
            final_info
        )
    
    def render(self):
        if self.render_mode == "human" and self.renderer:
            self.renderer.render(self.game)
    
    def close(self):
        if pygame.get_init():
            pygame.quit()
