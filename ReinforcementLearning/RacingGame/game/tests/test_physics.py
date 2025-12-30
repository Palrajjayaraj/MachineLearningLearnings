import unittest
from unittest.mock import MagicMock, patch
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock pygame
with patch.dict('sys.modules', {'pygame': MagicMock(), 'pygame.mixer': MagicMock()}):
    import pygame
    from src.core import RoadFighterGame, PLAYER_MAX_SPEED
    from src.constants import TARGET_DISTANCE, RACE_TIME_LIMIT

class TestGamePhysics(unittest.TestCase):
    def test_game_duration_at_max_speed(self):
        """
        Verify that maintaining MAX SPEED (300 km/h) results in logical completion time.
        
        Math:
        Speed = 300 km/h = 83.33 m/s
        Target = 9500 m
        Time = 9500 / 83.33 = 114.0 seconds
        
        Requirement: Minimum 110 seconds.
        """
        game = RoadFighterGame()
        
        # Override start parameters to pure physics state
        game.reset()
        game.player.velocity_y = PLAYER_MAX_SPEED # Force 300 immediately
        
        # Disable Spawning Logic for Physics Math Verification
        game.spawn_interval = 9999.0 
        game.opponents = [] # Clear any initial
        
        # Step simulation
        dt = 0.1
        total_time = 0
        steps = 0
        
        while not game.game_over and total_time < 200: # Safety cap
            # Force max speed persistence (simulate perfect driving)
            game.player.velocity_y = PLAYER_MAX_SPEED 
            
            # Use 'update' logic logic
            # Note: update calls player.update which might accelerate, 
            # so we force velocity back to max exactly for pure math test.
            
            # We call update with NO inputs so it doesn't brake
            game.update(dt, left=False, right=False, brake=False)
            
            # Force speed back to max (in case acceleration logic does something weird, 
            # though at max it should clamp)
            game.player.velocity_y = PLAYER_MAX_SPEED 
            
            # CLEAR OPPONENTS to ensure pure physics test without collision
            game.opponents = []
            
            total_time += dt
            steps += 1
            
        print(f"\nCompleted in {total_time:.2f} seconds (Simulated)")
        print(f"End Reason: {game.end_reason}")
        print(f"Distance: {game.distance_traveled}")
        print(f"Time Remaining: {game.time_remaining}")
        print(f"Victory: {game.victory}")
            
        # Verification
        self.assertTrue(game.victory, f"Should win at max speed. Reason: {game.end_reason}")
        
        # Assertions based on Math
        # 114s expected. Allow small margin for floating point / frame alignment
        self.assertGreater(total_time, 110.0, "Game finished too fast! Under 110s implies bad physics.")
        self.assertLess(total_time, RACE_TIME_LIMIT, "Game took too long! Should finish before 120s limit.")
        
        print("✓ Physics verified: 300km/h run takes ~114s")

if __name__ == '__main__':
    unittest.main()
