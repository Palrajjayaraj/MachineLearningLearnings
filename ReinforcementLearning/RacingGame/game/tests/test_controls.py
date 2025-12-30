import unittest
from unittest.mock import MagicMock, patch
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock pygame
with patch.dict('sys.modules', {'pygame': MagicMock(), 'pygame.mixer': MagicMock()}):
    import pygame
    from src.core import RoadFighterGame, PLAYER_BASE_SPEED, PLAYER_ACCELERATION, PLAYER_BRAKE_FORCE, PLAYER_MAX_SPEED

class TestPlayerControls(unittest.TestCase):
    def setUp(self):
        self.game = RoadFighterGame()
        self.game.reset()
        # Ensure we start in a clean state for physics
        # Base speed is 150.
        self.start_speed = self.game.player.velocity_y 
        self.start_x = self.game.player.x
        
    def test_auto_acceleration(self):
        """Verify car accelerates when no inputs are pressed"""
        dt = 0.1
        # No inputs
        self.game.update(dt, left=False, right=False, brake=False)
        
        new_speed = self.game.player.velocity_y
        expected_increase = PLAYER_ACCELERATION * dt
        
        self.assertGreater(new_speed, self.start_speed, "Car should auto-accelerate")
        self.assertAlmostEqual(new_speed, self.start_speed + expected_increase, delta=1.0)
        print("✓ Auto-acceleration verified")

    def test_braking_response(self):
        """Verify car decelerates when BRAKE is pressed"""
        dt = 0.1
        # Brake input
        self.game.update(dt, left=False, right=False, brake=True)
        
        new_speed = self.game.player.velocity_y
        expected_decrease = PLAYER_BRAKE_FORCE * dt
        
        self.assertLess(new_speed, self.start_speed, "Car should decelerate on brake")
        self.assertAlmostEqual(new_speed, self.start_speed - expected_decrease, delta=1.0)
        print("✓ Braking response verified")
        
    def test_steering_left(self):
        """Verify Left input moves player Left"""
        dt = 0.1
        # Run for a few frames to allow lane change animation to start moving X
        for _ in range(5):
            self.game.update(dt, left=True, right=False, brake=False)
        
        # Check that X changed or target changed
        self.assertNotEqual(self.game.player.x, self.start_x, "Player X should change on Left input (after animation starts)")
        self.assertLess(self.game.player.x, self.start_x, "Player should move to the Left (smaller X)")
        print("✓ Left steering verified")

    def test_steering_right(self):
        """Verify Right input moves player Right"""
        dt = 0.1
        # Run for a few frames
        for _ in range(5):
            self.game.update(dt, left=False, right=True, brake=False)
        
        self.assertNotEqual(self.game.player.x, self.start_x, "Player X should change on Right input (after animation starts)")
        self.assertGreater(self.game.player.x, self.start_x, "Player should move to the Right (larger X)")
        print("✓ Right steering verified")

if __name__ == '__main__':
    unittest.main()
