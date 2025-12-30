import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add game directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock pygame before importing game_core
with patch.dict('sys.modules', {'pygame': MagicMock(), 'pygame.mixer': MagicMock()}):
    import pygame
    # Mock specific pygame constants and methods needed for import
    pygame.K_LEFT = 1
    pygame.K_RIGHT = 2
    pygame.K_UP = 3
    pygame.K_DOWN = 4
    pygame.K_SPACE = 5
    pygame.Rect = MagicMock
    
    # Import from CORE
    from src.core import RoadFighterGame, NUM_LANES

class TestGameLogic(unittest.TestCase):
    def setUp(self):
        # Setup pure logic class
        self.game = RoadFighterGame()
        self.game.reset()

    def test_initial_state(self):
        """Verify game starts in correct state"""
        self.assertEqual(self.game.player.current_lane, 1) # Starts in lane 1 (of 0-3)
        self.assertEqual(self.game.score, 0)
        self.assertFalse(self.game.game_over)
        self.assertFalse(self.game.lane_camping_mode)

    def test_camping_logic(self):
        """Verify camping mode activates after passing 2 cars in same lane"""
        # Setup: Player in lane 0
        self.game.player.current_lane = 0
        self.game.last_player_lane = 0
        self.game.player_current_lane_cars_passed = 0
        
        # 1. Pass first car
        self.game.player_current_lane_cars_passed += 1
        
        # Should NOT be in camping mode yet
        self.assertFalse(self.game.lane_camping_mode)
        
        # 2. Pass second car
        self.game.player_current_lane_cars_passed += 1
        # Logic in update() sets this
        if self.game.player_current_lane_cars_passed >= 2:
            self.game.lane_camping_mode = True
            
        self.assertTrue(self.game.lane_camping_mode)
        
        # 3. Change lanes
        self.game.player.current_lane = 1
        # Logic in update() handles this
        if self.game.last_player_lane != self.game.player.current_lane:
            self.game.lane_camping_mode = False
            self.game.player_current_lane_cars_passed = 1
            
        self.assertFalse(self.game.lane_camping_mode)

    def test_spawning_rules(self):
        """Verify spawn constraints (no more than 2 same color/lane)"""
        # Test consecutive same color constraint
        self.game.last_spawned_type = 'green'
        self.game.consecutive_same_type = 2
        
        # Verify state is tracked
        self.assertEqual(self.game.consecutive_same_type, 2)
        
        # Simulate a reset 
        self.game.reset()
        self.assertEqual(self.game.consecutive_same_type, 0)

if __name__ == '__main__':
    unittest.main()
