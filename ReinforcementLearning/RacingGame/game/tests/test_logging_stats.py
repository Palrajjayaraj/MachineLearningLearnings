
import unittest
import sys
import os

# Add game directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core import RoadFighterGame

class TestLoggingStats(unittest.TestCase):
    def setUp(self):
        self.game = RoadFighterGame()
        self.game.reset()

    def test_stats_initially_zero(self):
        """Verify stats start at 0"""
        _, _, _, info = self.game.step(False, False, False)
        stats = info.get('cars_passed', {})
        self.assertEqual(stats.get('green'), 0)
        self.assertEqual(stats.get('yellow'), 0)
        self.assertEqual(stats.get('red'), 0)

    def test_stats_mock_increment(self):
        """Verify step() returns correct stats when counters are manually incremented"""
        self.game.green_cars_passed = 5
        self.game.yellow_cars_passed = 3
        self.game.red_cars_passed = 1
        
        _, _, _, info = self.game.step(False, False, False)
        stats = info.get('cars_passed', {})
        
        self.assertEqual(stats.get('green'), 5, "Green cars count mismatch")
        self.assertEqual(stats.get('yellow'), 3, "Yellow cars count mismatch")
        self.assertEqual(stats.get('red'), 1, "Red cars count mismatch")

if __name__ == '__main__':
    unittest.main()
