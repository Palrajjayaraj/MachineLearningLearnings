import unittest
from unittest.mock import MagicMock, patch
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock constants if needed, but we can import from src
# Mock pygame
with patch.dict('sys.modules', {'pygame': MagicMock(), 'pygame.mixer': MagicMock()}):
    from src.entities import OpponentCar
    from src.constants import LANE_CENTERS, NUM_LANES, OPPONENT_WIDTH

class TestMovementSpeed(unittest.TestCase):
    def test_zigzag_speed_difference(self):
        """Verify Yellow cars move horizontally faster than Red cars"""
        
        # Create Yellow Car (Force type)
        # We need a start lane where it can move. Lane 1 is safe (can go left or right)
        yellow_car = OpponentCar(lane=1, force_type='yellow')
        # Ensure it needs to move. 
        # Yellow logic: moves towards target_adjacent_lane.
        # Let's force target to be lane 2.
        yellow_car.start_lane = 1
        yellow_car.target_adjacent_lane = 2 
        yellow_car.movement_direction = 1 # Towards 2 (Right)
        yellow_car.x = LANE_CENTERS[1] - OPPONENT_WIDTH//2 # Start at center of lane 1
        
        # Create Red Car (Force type)
        red_car = OpponentCar(lane=1, force_type='red')
        red_car.movement_direction = 1 # Moving Right
        red_car.x = LANE_CENTERS[1] - OPPONENT_WIDTH//2
        
        # Check Initial Positions match (Sanity)
        self.assertEqual(yellow_car.x, red_car.x, "Start X should match")
        start_x = yellow_car.x
        
        # Update both with same delta_time and multiplier
        dt = 0.1
        multiplier = 1.0
        
        yellow_car.update(dt, 0, multiplier)
        red_car.update(dt, 0, multiplier)
        
        # Calculate distance moved
        yellow_dist = yellow_car.x - start_x
        red_dist = red_car.x - start_x
        
        print(f"Yellow moved: {yellow_dist:.2f} px")
        print(f"Red moved:    {red_dist:.2f} px")
        
        # Assertions
        # Yellow should be 100 * 1.0 * 0.1 = 10.0
        self.assertAlmostEqual(yellow_dist, 10.0, delta=0.1, msg="Yellow speed should be ~100px/s")
        
        # Red should be 70 * 1.0 * 0.1 = 7.0
        self.assertAlmostEqual(red_dist, 7.0, delta=0.1, msg="Red speed should be ~70px/s")
        
        self.assertGreater(yellow_dist, red_dist, "Yellow car should be faster horizontally")
        
    def test_multiplier_scaling_speed(self):
        """Verify horizontal speed scales with Difficulty Multiplier"""
        multiplier = 2.0
        dt = 0.1
        
        # Yellow Car
        yellow_car = OpponentCar(lane=1, force_type='yellow')
        yellow_car.start_lane = 1
        yellow_car.target_adjacent_lane = 2
        yellow_car.movement_direction = 1
        start_x = yellow_car.x
        
        yellow_car.update(dt, 0, multiplier)
        dist = yellow_car.x - start_x
        
        # Should be 100 * 2.0 * 0.1 = 20.0
        self.assertAlmostEqual(dist, 20.0, delta=0.1, msg="Speed should double with 2.0x multiplier")
        print(f"Yellow (2.0x) moved: {dist:.2f} px")

if __name__ == '__main__':
    unittest.main()
