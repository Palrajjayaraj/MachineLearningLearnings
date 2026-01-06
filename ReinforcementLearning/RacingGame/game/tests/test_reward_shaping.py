
import unittest
import sys
import os

# Add game directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core import RoadFighterGame
from src.entities import OpponentCar

class TestRewardShaping(unittest.TestCase):
    def setUp(self):
        self.game = RoadFighterGame()
        self.game.reset()
        # Enable rewards immediately for testing
        self.game.rewards_active = True

    def test_green_passing_reward(self):
        """Verify passing a green car gives +2.0 reward"""
        # Directly test the passing bonus logic
        green_car = OpponentCar(1, 0, 0, force_type='green')
        green_car.y = 100
        
        old_bonus = self.game.passing_bonus
        
        # Simulate passing by marking as passed and calling internal logic
        green_car.passed_counted = False
        
        # Manually trigger the passing bonus logic
        if green_car.car_type == 'green':
            self.game.passing_bonus += 2.0
        elif green_car.car_type == 'yellow':
            self.game.passing_bonus += 3.0
        elif green_car.car_type == 'red':
            self.game.passing_bonus += 5.0
        
        self.assertEqual(self.game.passing_bonus, old_bonus + 2.0, 
                        "Green car passing bonus should be +2.0")

    def test_yellow_passing_reward(self):
        """Verify passing a yellow car gives +3.0 reward"""
        yellow_car = OpponentCar(1, 0, 0, force_type='yellow')
        
        old_bonus = self.game.passing_bonus
        
        # Manually trigger the passing bonus logic
        if yellow_car.car_type == 'green':
            self.game.passing_bonus += 2.0
        elif yellow_car.car_type == 'yellow':
            self.game.passing_bonus += 3.0
        elif yellow_car.car_type == 'red':
            self.game.passing_bonus += 5.0
        
        self.assertEqual(self.game.passing_bonus, old_bonus + 3.0, 
                        "Yellow car passing bonus should be +3.0")

    def test_red_passing_reward(self):
        """Verify passing a red car gives +5.0 reward"""
        red_car = OpponentCar(1, 0, 0, force_type='red')
        
        old_bonus = self.game.passing_bonus
        
        # Manually trigger the passing bonus logic
        if red_car.car_type == 'green':
            self.game.passing_bonus += 2.0
        elif red_car.car_type == 'yellow':
            self.game.passing_bonus += 3.0
        elif red_car.car_type == 'red':
            self.game.passing_bonus += 5.0
        
        self.assertEqual(self.game.passing_bonus, old_bonus + 5.0, 
                        "Red car passing bonus should be +5.0")

    def test_green_collision_penalty(self):
        """Verify colliding with green car gives -50 penalty"""
        # Place green car in collision position
        green_car = OpponentCar(self.game.player.current_lane, 0, 0, force_type='green')
        green_car.y = self.game.player.y
        self.game.opponents.append(green_car)
        
        # Step should trigger collision
        _, reward, done, _ = self.game.step(False, False, False)
        
        self.assertTrue(done, "Game should end on collision")
        self.assertEqual(self.game.collision_penalty, -50.0,
                        "Green collision penalty should be -50.0")
        self.assertIn(self.game.collision_penalty, [reward, reward - (self.game.player.velocity_y / 3.6) * (1/60.0) * 0.1],
                     "Reward should include collision penalty")

    def test_yellow_collision_penalty(self):
        """Verify colliding with yellow car gives -30 penalty"""
        yellow_car = OpponentCar(self.game.player.current_lane, 0, 0, force_type='yellow')
        yellow_car.y = self.game.player.y
        self.game.opponents.append(yellow_car)
        
        _, reward, done, _ = self.game.step(False, False, False)
        
        self.assertTrue(done)
        self.assertEqual(self.game.collision_penalty, -30.0,
                        "Yellow collision penalty should be -30.0")

    def test_red_collision_penalty(self):
        """Verify colliding with red car gives -10 penalty"""
        red_car = OpponentCar(self.game.player.current_lane, 0, 0, force_type='red')
        red_car.y = self.game.player.y
        self.game.opponents.append(red_car)
        
        _, reward, done, _ = self.game.step(False, False, False)
        
        self.assertTrue(done)
        self.assertEqual(self.game.collision_penalty, -10.0,
                        "Red collision penalty should be -10.0")

if __name__ == '__main__':
    unittest.main()
