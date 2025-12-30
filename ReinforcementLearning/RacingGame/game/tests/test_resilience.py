import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add game directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock pygame before import
with patch.dict('sys.modules', {'pygame': MagicMock(), 'pygame.mixer': MagicMock()}):
    import pygame
    
    # Setup minimalistic mocks for Renderer
    mock_rect = MagicMock()
    mock_rect.inflate.return_value = mock_rect
    pygame.Rect = MagicMock(return_value=mock_rect)
    
    # Mock display
    mock_surface = MagicMock()
    mock_surface.get_rect.return_value = mock_rect
    pygame.display.set_mode.return_value = mock_surface
    
    from src.renderer import GameRenderer
    from src.core import RoadFighterGame

class TestRendererResilience(unittest.TestCase):
    def test_missing_assets_resilience(self):
        """
        Regression Test for AttributeError: crash_sound
        Simulates total failure of asset loading (e.g. missing files).
        Verifies that Renderer initializes safe defaults (None) instead of crashing.
        """
        
        # We need to force load_assets to fail.
        # It calls pygame.image.load.
        
        # Configure pygame.image.load to raise Exception
        pygame.image.load.side_effect = Exception("File not found")
        
        # Instantiate Renderer
        # This calls __init__ -> load_assets -> pygame.image.load -> Exception
        # The Exception should be caught, and defaults set.
        renderer = GameRenderer()
        
        # 1. Verify attributes exist (The Bug Fix)
        self.assertTrue(hasattr(renderer, 'crash_sound'), "crash_sound attribute missing after load failure")
        self.assertTrue(hasattr(renderer, 'point_sound'), "point_sound attribute missing after load failure")
        self.assertIsNone(renderer.crash_sound, "crash_sound should be None on failure")
        
        # 2. Verify Render loop doesn't crash when accessing these None attributes in logic
        game = RoadFighterGame()
        
        # Force a state that might try to play sound
        game.game_over = True
        game.end_reason = 'collision'
        
        try:
            renderer.render(game)
        except Exception as e:
            self.fail(f"Renderer crashed with missing assets: {e}")
            
        print("\nTEST: Resilience (Missing Assets) passed")

if __name__ == '__main__':
    unittest.main()
