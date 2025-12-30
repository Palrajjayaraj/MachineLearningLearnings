import unittest
from unittest.mock import MagicMock, patch
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

with patch.dict('sys.modules', {'pygame': MagicMock(), 'pygame.mixer': MagicMock()}):
    from src.core import RoadFighterGame

class TestScore(unittest.TestCase):
    def test_score_calculation(self):
        """Verify score updates based on distance and bonuses"""
        game = RoadFighterGame()
        game.reset()
        
        # Initial score 0
        self.assertEqual(game.score, 0)
        
        # Simulate distance travel at base multiplier (1.0)
        game.elapsed_time = 10.0 # < 30s -> 1.0x
        game.update(0.1, False, False, False)
        score_low = game.score
        
        game.reset()
        
        # Simulate distance travel at high multiplier (2.0)
        game.elapsed_time = 110.0 # > 100s -> 2.0x
        game.update(0.1, False, False, False)
        score_high = game.score
        
        # Since same distance delta (approx), score_high should be ~2x score_low
        # Actually update() adds to score. 
        # score_low ended at ~ (dist * 10 * 1.0)
        # score_high ended at ~ (dist * 10 * 2.0)
        
        self.assertGreater(score_high, score_low * 1.8, "Score should be significantly higher with 2.0x multiplier")
        print(f"✓ Score logic verified: Base={score_low}, Max({game._get_speed_multiplier()}x)={score_high}")

if __name__ == '__main__':
    unittest.main()
