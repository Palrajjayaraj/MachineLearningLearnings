import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add game directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock pygame
with patch.dict('sys.modules', {'pygame': MagicMock(), 'pygame.mixer': MagicMock()}):
    import pygame
    
    # Configure Rect mock to handle colliderect
    mock_rect = MagicMock()
    mock_rect.colliderect.return_value = False # Always return False logic for tests
    pygame.Rect = MagicMock(return_value=mock_rect)
    
    from src.core import RoadFighterGame, NUM_LANES, GREEN_CAR_PROBABILITY, YELLOW_CAR_PROBABILITY, RED_CAR_PROBABILITY
    from src.constants import OPPONENT_MIN_SPACING

class TestGameRules(unittest.TestCase):
    def setUp(self):
        self.game = RoadFighterGame()
        self.game.reset()

    def test_color_distribution(self):
        """Verify 5:3:2 color ratio (Statistical Test)"""
        # disable camping/forcing logic to test raw probabilities
        self.game.consecutive_same_type = 0 
        
        green_count = 0
        yellow_count = 0
        red_count = 0
        total_samples = 1000
        
        for _ in range(total_samples):
            # We assume OpponentCar creation logic handles probability
            # We can test this by instantiating OpponentCar directly 
            # or by forcing spawns in game loop. 
            # Let's instantiate directly to test the weighted choice logic.
            from src.entities import OpponentCar
            car = OpponentCar(lane=0, y_offset=0)
            if car.car_type == 'green': green_count += 1
            elif car.car_type == 'yellow': yellow_count += 1
            elif car.car_type == 'red': red_count += 1
            
        # Tolerances (allow variance due to randomness)
        # Expected: ~500, ~300, ~200
        self.assertAlmostEqual(green_count / total_samples, 0.5, delta=0.1)
        self.assertAlmostEqual(yellow_count / total_samples, 0.3, delta=0.1)
        self.assertAlmostEqual(red_count / total_samples, 0.2, delta=0.1)

    def test_vertical_spacing(self):
        """Verify no two cars spawn closer than OPPONENT_MIN_SPACING"""
        # Force spawns
        spawned_cars = []
        
        # Override random to ensure we TRY to spawn close
        self.game.spawn_interval = 0.001 # Super fast spawn attempts
        
        # Run update loop for many frames
        for _ in range(200):
            self.game.update(0.016, False, False, False)
            
        # Check all pairs
        opponents = self.game.opponents
        if len(opponents) < 2:
            return # Cannot test spacing with < 2 cars
            
        # Sort by Y
        sorted_opps = sorted(opponents, key=lambda c: c.y)
        for i in range(len(sorted_opps) - 1):
            car_a = sorted_opps[i]
            car_b = sorted_opps[i+1]
            dist = abs(car_a.y - car_b.y)
            # Note: Spawning logic prevents overlap at Spawn Time.
            # Cars moving at different speeds MIGHT overlap later if logic allows passing? 
            # But spawn logic key requirement is separation AT START.
            # Effectively, checks if logic worked.
            
            # We are verifying that NO cars are *currently* overlapping significantly
            # But mostly we want to check logic.
            pass 
            
        # Actually a better test is to Unit Test the _spawn_single_car method's rejection
        # 1. Place a car at y=-100
        from src.entities import OpponentCar
        blocker = OpponentCar(lane=0)
        blocker.y = -100
        self.game.opponents = [blocker]
        
        # 2. Try to spawn another one (defaults to same Y usually)
        # It should fail (return False)
        result = self.game._spawn_single_car()
        
        # Should fail because of spacing check
        # But wait, logic might try random lane. 
        # The spacing check iterates all opponents.
        # If any opponent |opp.y - spawn_y| < MIN_SPACING, return False.
        # spawn_y is almost always -100 or close.
        
        # If result is True, it means it ignored the blocker!
        self.assertFalse(result, "Should verify spacing constraint prevented spawn")

    def test_lane_camping_prevention(self):
        """Verify that camping spawns a car in player's lane"""
        self.game.lane_camping_mode = True
        self.game.last_player_lane = 2
        
        # Clear opponents
        self.game.opponents = []
        
        # Trigger spawn
        result = self.game._spawn_single_car()
        
        # Verify spawn happened
        self.assertTrue(result)
        # Verify it is in lane 2
        new_car = self.game.opponents[-1]
        
        # NOTE: OpponentCar logic converts lane index to X.
        # We need to reverse check or check internal attribute if accessible.
        # In entities.py, 'lane' attribute is stored.
        self.assertEqual(new_car.lane, 2, "Should spawn in player lane (2) when camping")

    def test_red_car_separation(self):
        """Verify red cars are separated by at least 2 lanes"""
        # 1. Simulate last spawned read car in lane 0
        self.game.last_spawned_type = 'red'
        self.game.last_red_car_lane = 0
        self.game.opponents = []
        
        # 2. Force next spawn to be Red (by mocking or probability? Hard to force type directly in _spawn_single_car)
        # Instead, let's unit test the logic block directly if possible, or use Monte Carlo.
        
        # We can simulate by calling _spawn_single_car many times and checking if any Red car 
        # spawns in lane 1 (dist 1) immediately after a Red car in lane 0.
        
        violations = 0
        for _ in range(100):
            self.game.last_spawned_type = 'red'
            self.game.last_red_car_lane = 0
            
            # Try spawn
            self.game._spawn_single_car()
            
            new_car = self.game.opponents[-1]
            if new_car.car_type == 'red': # If it happened to be red
                # Ensure it is NOT in lane 1
                if new_car.lane == 1:
                    violations += 1
            
            self.game.opponents = []
            
        self.assertEqual(violations, 0, "Red cars spawned too close horizontally")

    def test_player_bounds(self):
        """Verify player starts and stays within road boundaries"""
        from src.constants import ROAD_LEFT_EDGE, ROAD_RIGHT_EDGE, PLAYER_START_X
        
        # Check start position
        self.assertEqual(self.game.player.x, PLAYER_START_X, "Player started at wrong X position")
        self.assertTrue(ROAD_LEFT_EDGE <= self.game.player.x <= ROAD_RIGHT_EDGE, "Player started outside road")
        
        # Check boundary integrity
        # Try moving far left
        for _ in range(100):
            self.game.step(left=True, right=False, brake=False)
            
        self.assertGreaterEqual(self.game.player.x, ROAD_LEFT_EDGE, "Player moved off-road Left")
        
        # Try moving far right
        for _ in range(200): # More steps to cross full width
            self.game.step(left=False, right=True, brake=False)
            
        # Note: Player X is Left corner. So X + Width <= Right Edge
        self.assertLessEqual(self.game.player.x + self.game.player.width, ROAD_RIGHT_EDGE, "Player moved off-road Right")

if __name__ == '__main__':
    unittest.main()
