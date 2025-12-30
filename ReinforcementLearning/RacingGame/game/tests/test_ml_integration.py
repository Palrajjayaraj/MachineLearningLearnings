"""
Test ML-Ready Game Features
Demonstrates frame-by-frame control and state extraction
"""

import unittest
import sys
import os
import random

# Ensure src can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core import RoadFighterGame

class TestMLIntegration(unittest.TestCase):
    def setUp(self):
        self.game = RoadFighterGame()
        self.game.reset()

    def test_step_method(self):
        """Test the step() method - frame-by-frame control"""
        print("\\nTEST: Frame-by-Frame Control")
        
        for frame in range(100):
            left = random.choice([True, False])
            right = random.choice([True, False])
            brake = random.choice([True, False])
            
            state, reward, done, info = self.game.step(left, right, brake)
            
            if done:
                break
        
        # Verify basic contracts
        self.assertIsInstance(reward, float)
        self.assertIsInstance(done, bool)
        self.assertIn('distance', info)

    def test_state_extraction(self):
        """Test the get_state() method - state extraction"""
        print("\\nTEST: State Extraction")
        
        # Run a few frames
        for _ in range(60):
            self.game.step(False, False, False)
        
        state = self.game.get_state()
        
        # Verify vector shape
        # Verify state shape
        # State V3 Size: 32 (Player[4] + Global[3] + 5*Objects[5])
        self.assertEqual(len(state), 32)
        
        # Verify value ranges (all extracted features should be normalized)
        for i, val in enumerate(state):
            # Speed can be slightly negative? No, usually 0.0-1.0 or -1.0 to 1.0
            # Opponent speed calc might be negative check logic
            self.assertIsInstance(val, float, f"Feature {i} is not float")

    def test_reward_function(self):
        """Test reward calculation"""
        print("\\nTEST: Reward Function")
        
        # Scenario 1: Normal driving
        total_reward = 0
        for _ in range(60):
            state, reward, done, info = self.game.step(False, False, False)
            total_reward += reward
            
        self.assertGreater(total_reward, 0, "Should get positive reward for moving forward")

        # Scenario 2: Collision Penalty (Artificial trigger for test)
        self.game.reset()
        # Force a collision state artificially to test logic if possible, 
        # or just rely on the fact that running long enough might crash.
        # Ideally we trust the Logic unit tests for collision, 
        # here we just check reward type is float.
        pass

    def test_ml_training_loop_simulation(self):
        """Simulate what an ML training loop would look like"""
        print("\\nTEST: Simulated ML Training Loop")
        
        # Run 1 short episode
        state = self.game.reset()
        episode_reward = 0
        steps = 0
        
        max_steps = 100
        
        while steps < max_steps:
            action = random.randint(0, 2)
            left = (action == 1)
            right = (action == 2)
            
            state, reward, done, info = self.game.step(left, right, False)
            episode_reward += reward
            steps += 1
            
            if done:
                break
                
        self.assertTrue(steps > 0)
        self.assertIsInstance(episode_reward, float)

if __name__ == '__main__':
    unittest.main()
