import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

with patch.dict('sys.modules', {'pygame': MagicMock(), 'pygame.mixer': MagicMock()}):
    from src.gym_env import RacingGameEnv

class TestMLReadiness(unittest.TestCase):
    def test_reward_consistency(self):
        """Verify reward does not explode over time (Step Reward vs Cumulative)"""
        env = RacingGameEnv()
        env.reset()
        
        # 1. Step at start (Time 0)
        action = 0 # No op
        obs1, reward1, done1, trunc1, info1 = env.step(action)
        
        # 2. Fast forward game state (High distance)
        env.game.distance_traveled = 5000.0
        env.game.time_remaining = 60.0
        
        # 3. Step again (Time 60)
        # If velocity is same, reward should be same.
        # If logic was 'distance_traveled * 0.01', reward1 would be small, reward2 huge.
        obs2, reward2, done2, trunc2, info2 = env.step(action)
        
        print(f"Reward Start: {reward1}")
        print(f"Reward Mid:   {reward2}")
        
        self.assertAlmostEqual(reward1, reward2, delta=0.5, 
            msg="Reward should depend on Speed (Step Delta), not Cumulative Distance.")
            
    def test_observation_space_shape(self):
        """Verify Gym obs shape matches core output (V3 State = 32)"""
        env = RacingGameEnv()
        obs, _ = env.reset()
        
        self.assertEqual(obs.shape, (32,), "Observation shape must match V3 Space definition (32)")
        self.assertEqual(env.observation_space.shape, (32,))
        
    def test_frame_skipping_default(self):
        """Verify Default Frame Skipping is 4"""
        env = RacingGameEnv() # Default frame_skip=4
        env.reset()
        
        start_time = env.game.time_remaining
        env.step(0)
        end_time = env.game.time_remaining
        
        # Expected dt = 1/60 * 4
        delta = start_time - end_time
        self.assertAlmostEqual(delta, 4.0/60.0, delta=0.001, 
            msg=f"Default should be Skip=4. Delta was {delta:.4f}")

    def test_frame_skipping_explicit_one(self):
        """Verify Customizable Frame Skipping (e.g. 1)"""
        env = RacingGameEnv(frame_skip=1) # Explicit Skip=1
        env.reset()
        
        start_time = env.game.time_remaining
        env.step(0)
        end_time = env.game.time_remaining
        
        # Expected dt = 1/60 * 1
        delta = start_time - end_time
        self.assertAlmostEqual(delta, 1.0/60.0, delta=0.001, 
            msg=f"Custom Skip=1 should advance 1 frame. Delta was {delta:.4f}")

if __name__ == '__main__':
    unittest.main()
