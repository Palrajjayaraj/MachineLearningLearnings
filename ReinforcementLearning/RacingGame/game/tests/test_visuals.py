import unittest
from src.constants import COLOR_PLAYER
from src.entities import OpponentCar
from src.core import RoadFighterGame

class TestVisualFeatures(unittest.TestCase):
    def test_player_color_dark_blue(self):
        """Verify player color is Dark Blue (0, 0, 139)"""
        expected_color = (0, 0, 139)
        self.assertEqual(COLOR_PLAYER, expected_color, f"Player color should be Dark Blue {expected_color}, found {COLOR_PLAYER}")
        print("✓ Player color verified: Dark Blue")

    def test_blinker_state_logic(self):
        """
        Verify that OpponentCars maintain the state needed for blinkers:
        - movement_direction (driving the left/right decision)
        - movement_timer (driving the blink frequency)
        """
        # 1. Yellow Car (Zig-zags)
        yellow_car = OpponentCar(lane=1, force_type='yellow')
        # Simulate update to check timer
        dt = 0.1
        yellow_car.update(dt, 0)
        
        self.assertTrue(hasattr(yellow_car, 'movement_direction'), "Yellow car needs movement_direction for blinkers")
        self.assertTrue(hasattr(yellow_car, 'movement_timer'), "Yellow car needs movement_timer for blinkers")
        self.assertNotEqual(yellow_car.movement_direction, 0, "Yellow car should be moving laterally")
        print("✓ Yellow car blinker state verified")
        
        # 2. Red Car (Zig-zags)
        red_car = OpponentCar(lane=1, force_type='red')
        red_car.update(dt, 0)
        
        self.assertTrue(hasattr(red_car, 'movement_direction'), "Red car needs movement_direction for blinkers")
        self.assertNotEqual(red_car.movement_direction, 0, "Red car should be moving laterally")
        print("✓ Red car blinker state verified")
        
        # 3. Green Car (Straight - No Blinkers needed, but state check)
        green_car = OpponentCar(lane=1, force_type='green')
        green_car.update(dt, 0)
        self.assertEqual(green_car.movement_direction, 0, "Green car should go straight (no blinker)")
        print("✓ Green car no-blinker state verified")

if __name__ == '__main__':
    unittest.main()
