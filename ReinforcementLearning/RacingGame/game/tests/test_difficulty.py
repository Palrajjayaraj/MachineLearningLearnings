import unittest
from unittest.mock import MagicMock, patch
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock pygame before importing
with patch.dict('sys.modules', {'pygame': MagicMock(), 'pygame.mixer': MagicMock()}):
    from src.core import RoadFighterGame
    from src.constants import TARGET_DISTANCE

class TestDifficultyScaling(unittest.TestCase):
    def test_multiplier_time_steps(self):
        """Verify speed multiplier increases in discrete steps based on Elapsed Time"""
        game = RoadFighterGame()
        game.reset()
        
        # Test Case 1: 0-30s -> 1.0
        game.elapsed_time = 10.0
        self.assertEqual(game._get_speed_multiplier(), 1.0)
        
        # Test Case 2: 30-46s -> 1.2
        game.elapsed_time = 31.0
        self.assertEqual(game._get_speed_multiplier(), 1.2)
        game.elapsed_time = 45.9
        self.assertEqual(game._get_speed_multiplier(), 1.2)
        
        # Test Case 3: 46-60s -> 1.4
        game.elapsed_time = 46.1
        self.assertEqual(game._get_speed_multiplier(), 1.4)
        game.elapsed_time = 59.9
        self.assertEqual(game._get_speed_multiplier(), 1.4)
        
        # Test Case 4: 60-80s -> 1.6
        game.elapsed_time = 60.1
        self.assertEqual(game._get_speed_multiplier(), 1.6)
        game.elapsed_time = 79.9
        self.assertEqual(game._get_speed_multiplier(), 1.6)

        # Test Case 5: 80-100s -> 1.8
        game.elapsed_time = 80.1
        self.assertEqual(game._get_speed_multiplier(), 1.8)
        game.elapsed_time = 99.9
        self.assertEqual(game._get_speed_multiplier(), 1.8)
        
        # Test Case 6: >100s -> 2.0
        game.elapsed_time = 100.1
        self.assertEqual(game._get_speed_multiplier(), 2.0)
        game.elapsed_time = 120.0
        self.assertEqual(game._get_speed_multiplier(), 2.0)
        
        print(f"✓ Stepped difficulty verified across all time zones")

if __name__ == '__main__':
    unittest.main()
