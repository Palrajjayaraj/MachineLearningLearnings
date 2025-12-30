import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add game directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock pygame
with patch.dict('sys.modules', {'pygame': MagicMock(), 'pygame.mixer': MagicMock()}):
    import pygame
    from src.entities import OpponentCar
    from src.constants import LANE_CENTERS, ROAD_LEFT_EDGE, ROAD_RIGHT_EDGE, OPPONENT_WIDTH

class TestMovementLogic(unittest.TestCase):
    def test_yellow_car_zigzag(self):
        """
        Verify Yellow Cars flip direction when reaching their target lane.
        Yellow cars oscillate between 'start_lane' and 'target_adjacent_lane'.
        """
        # Create Yellow Car in Lane 1
        # It usually targets Lane 0 or 2.
        # Let's force target to be Lane 0 for deterministic testing.
        
        car = OpponentCar(lane=1, force_type='yellow')
        car.start_lane = 1
        car.target_adjacent_lane = 0
        
        # 1. Start moving towards target (Lane 0)
        # If movement_direction > 0, target is target_adjacent_lane (0).
        car.movement_direction = 1 
        
        # Place it within snapping threshold of Target (Lane 0)
        target_x = LANE_CENTERS[0] - OPPONENT_WIDTH // 2
        car.x = target_x + 1.0 
        
        # Update
        # It should detect it's close to target (Lane 0), snap, and FLIP direction.
        car.update(0.001, player_speed=0)
        
        # 2. Logic should detect it reached target and FLIP direction to -1
        # (Meaning next target is start_lane)
        self.assertEqual(car.movement_direction, -1, "Yellow car should flip to -1 (Left/Back) after reaching Target")
        self.assertAlmostEqual(car.x, target_x, delta=1.0, msg="Car should snap to target X")
        
        print("✓ Yellow Car direction flip verified")

    def test_red_car_edge_bounce(self):
        """
        Verify Red Cars flip direction when hitting Road Edges.
        """
        car = OpponentCar(lane=2, force_type='red')
        
        # 1. Test Right Edge Bounce
        # Set car close to right edge, moving Right (+1)
        right_bound = ROAD_RIGHT_EDGE - OPPONENT_WIDTH
        car.x = right_bound - 2
        car.movement_direction = 1
        
        # Update
        car.update(0.1, player_speed=0)
        
        # Should bounce
        self.assertEqual(car.movement_direction, -1, "Red car should bounce off Right edge")
        self.assertLessEqual(car.x, right_bound, "Car should be clamped inside boundary")
        
        # 2. Test Left Edge Bounce
        # Set car close to left edge, moving Left (-1)
        left_bound = ROAD_LEFT_EDGE
        car.x = left_bound + 2
        car.movement_direction = -1
        
        car.update(0.1, player_speed=0)
        
        self.assertEqual(car.movement_direction, 1, "Red car should bounce off Left edge")
        self.assertGreaterEqual(car.x, left_bound, "Car should be clamped inside boundary")
        
        print("✓ Red Car edge bounce verified")

if __name__ == '__main__':
    unittest.main()
