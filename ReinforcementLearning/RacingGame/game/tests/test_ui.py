import unittest
from unittest.mock import MagicMock, patch
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock pygame
with patch.dict('sys.modules', {'pygame': MagicMock(), 'pygame.mixer': MagicMock()}):
    import pygame
    mock_font = MagicMock()
    mock_font.render.return_value = MagicMock()
    pygame.font.Font.return_value = mock_font
    
    from src.renderer import GameRenderer
    from src.core import RoadFighterGame, TARGET_DISTANCE

class TestUI(unittest.TestCase):
    def test_game_over_prompt_content(self):
        """Verify that the Game Over prompt includes both Restart and Quit instructions"""
        renderer = GameRenderer()
        renderer.screen = MagicMock()
        game = RoadFighterGame()
        game.game_over = True
        
        with patch.object(renderer, '_draw_center_text') as mock_draw:
            renderer.render(game)
            found_prompt = False
            for call in mock_draw.call_args_list:
                args, kwargs = call
                if "ENTER to Restart" in args[0] and "ESC to Quit" in args[0]:
                    found_prompt = True
            self.assertTrue(found_prompt)
            
    def test_hud_formats(self):
        """Verify Time unit 's' and Distance format 'Current/Total (Percent%)'"""
        renderer = GameRenderer()
        renderer.screen = MagicMock()
        game = RoadFighterGame()
        game.time_remaining = 60
        game.distance_traveled = TARGET_DISTANCE * 0.5 # 50%
        
        with patch.object(renderer, '_draw_text') as mock_draw:
            renderer.render(game)
            
            found_time = False
            found_dist = False
            
            for call in mock_draw.call_args_list:
                text = call.args[0]
                if "TIME: 60 s" in text:
                    found_time = True
                if f"DISTANCE: {int(TARGET_DISTANCE*0.5)}/{TARGET_DISTANCE}m (50%)" in text:
                    found_dist = True
                    
            self.assertTrue(found_time, "Time should include 's' unit")
            self.assertTrue(found_dist, "Distance should show Current/Total and Percentage")
            print("✓ HUD formats verified")

if __name__ == '__main__':
    unittest.main()
