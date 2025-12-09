"""
Road Fighter - Game Entities
"""

import pygame
import random
from constants import *


class PlayerCar:
    """Player-controlled car"""
    
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = PLAYER_WIDTH
        self.height = PLAYER_HEIGHT
        self.velocity_y = PLAYER_BASE_SPEED
        self.active = True
        
        # Lane changing
        self.is_changing_lane = False
        self.target_x = x
        self.start_x = x
        self.lane_change_progress = 0
        self.lane_change_speed = 5.0
        self.current_lane = 1
        
        # Key tracking
        self.left_was_pressed = False
        self.right_was_pressed = False
        
    def update(self, delta_time, left, right, brake):
        """Update car state"""
        if not self.active:
            return
            
        # Lane changing
        if self.is_changing_lane:
            self.lane_change_progress += self.lane_change_speed * delta_time
            if self.lane_change_progress >= 1.0:
                self.x = self.target_x
                self.is_changing_lane = False
                self.lane_change_progress = 0
            else:
                self.x = self.start_x + (self.target_x - self.start_x) * self.lane_change_progress
        else:
            if left and not self.left_was_pressed:
                half_lane = LANE_WIDTH / 2.0
                new_x = self.x - half_lane
                if new_x >= ROAD_LEFT_EDGE:
                    self._start_lane_change(new_x)
                    
            if right and not self.right_was_pressed:
                half_lane = LANE_WIDTH / 2.0
                new_x = self.x + half_lane
                if new_x <= ROAD_RIGHT_EDGE - self.width:
                    self._start_lane_change(new_x)
        
        self.left_was_pressed = left
        self.right_was_pressed = right
        
        # Speed
        if brake:
            self.velocity_y -= PLAYER_BRAKE_FORCE * delta_time
        else:
            self.velocity_y += PLAYER_ACCELERATION * delta_time
            
        self.velocity_y = max(PLAYER_MIN_SPEED, min(PLAYER_MAX_SPEED, self.velocity_y))
        self._update_current_lane()
        
    def _start_lane_change(self, new_x):
        self.is_changing_lane = True
        self.start_x = self.x
        self.target_x = new_x
        self.lane_change_progress = 0
        
    def _update_current_lane(self):
        car_center = self.x + self.width / 2.0
        for i, lane_center in enumerate(LANE_CENTERS):
            lane_start = ROAD_LEFT_EDGE + i * LANE_WIDTH
            lane_end = lane_start + LANE_WIDTH
            if lane_start <= car_center < lane_end:
                self.current_lane = i
                break
                
    def get_rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.width, self.height)
        
    def render(self, screen):
        if not self.active:
            return
            
        # Car body
        pygame.draw.rect(screen, COLOR_PLAYER, 
                        (int(self.x), int(self.y), self.width, self.height))
        pygame.draw.rect(screen, (255, 255, 255),
                        (int(self.x), int(self.y), self.width, self.height), 2)
        
        # Windshield
        pygame.draw.rect(screen, (100, 150, 255),
                        (int(self.x) + 5, int(self.y) + 5, 
                         self.width - 10, self.height // 4))
        
        # Wheels
        wheel_w, wheel_h = 8, 20
        positions = [(int(self.x) - wheel_w//2, int(self.y) + 15),
                     (int(self.x) - wheel_w//2, int(self.y) + self.height - 35),
                     (int(self.x) + self.width - wheel_w//2, int(self.y) + 15),
                     (int(self.x) + self.width - wheel_w//2, int(self.y) + self.height - 35)]
        for pos in positions:
            pygame.draw.rect(screen, (0, 0, 0), (*pos, wheel_w, wheel_h))


class OpponentCar:
    """AI opponent car with different behaviors"""
    
    def __init__(self, lane, y_offset=0, x_variance=0, force_type=None):
        self.lane = lane
        self.start_lane = lane
        self.x = LANE_CENTERS[lane] - OPPONENT_WIDTH // 2 + x_variance
        self.y = -OPPONENT_HEIGHT + y_offset  # Spawn at top edge of screen
        self.width = OPPONENT_WIDTH
        self.height = OPPONENT_HEIGHT
        self.speed = OPPONENT_SPEED
        self.active = True
        
        # Choose color and behavior (or force a type)
        if force_type:
            # Force specific car type (to avoid overlap issues)
            if force_type == 'green':
                self.color = COLOR_OPPONENT_GREEN
                self.car_type = 'green'
            elif force_type == 'yellow':
                self.color = COLOR_OPPONENT_YELLOW
                self.car_type = 'yellow'
            elif force_type == 'red':
                self.color = COLOR_OPPONENT_RED
                self.car_type = 'red'
        else:
            # Random selection based on probability
            rand = random.random()
            if rand < GREEN_CAR_PROBABILITY:
                self.color = COLOR_OPPONENT_GREEN
                self.car_type = 'green'
            elif rand < GREEN_CAR_PROBABILITY + YELLOW_CAR_PROBABILITY:
                self.color = COLOR_OPPONENT_YELLOW
                self.car_type = 'yellow'
            else:
                self.color = COLOR_OPPONENT_RED
                self.car_type = 'red'
        
        # Red cars start at random x position for varied patterns
        if self.car_type == 'red' and not force_type:
            self.x = random.randint(ROAD_LEFT_EDGE, ROAD_RIGHT_EDGE - self.width)
        
        # Movement state for zig-zagging
        self.movement_timer = 0
        self.movement_direction = random.choice([-1, 1])  # Random start direction
        self.zig_zag_progress = 0
        
    def update(self, delta_time, player_speed):
        if not self.active:
            return
            
        # Move vertically - fixed speed downward for visibility
        # Opponents drive towards player at constant visual speed
        self.y += 120 * delta_time  # Move down at 120 pixels/second
        
        # Horizontal movement based on car type
        if self.car_type == 'green':
            # Green: Drive straight
            pass
            
        elif self.car_type == 'yellow':
            # Yellow: Zig-zag fully between two lanes
            self.movement_timer += delta_time
            if self.movement_timer >= 3.0:  # Change lanes every 3 seconds
                self.movement_timer = 0
                self.movement_direction *= -1
            
            # Calculate target lane (start_lane or adjacent lane)
            if self.movement_direction > 0:
                target_lane = min(NUM_LANES - 1, self.start_lane + 1)
            else:
                target_lane = max(0, self.start_lane - 1)
            
            # Move towards target lane center
            target_x = LANE_CENTERS[target_lane] - self.width // 2
            if abs(self.x - target_x) > 2:
                if self.x < target_x:
                    self.x += 60 * delta_time  # Move right
                else:
                    self.x -= 60 * delta_time  # Move left
            else:
                self.x = target_x  # Snap to center
            
        elif self.car_type == 'red':
            # Red: Zig-zag across ALL 4 lanes
            self.movement_timer += delta_time
            
            # Move continuously at constant speed
            self.x += self.movement_direction * 70 * delta_time
            
            # Check boundaries and reverse when reaching edges
            left_bound = ROAD_LEFT_EDGE
            right_bound = ROAD_RIGHT_EDGE - self.width
            
            if self.x <= left_bound:
                self.x = left_bound
                self.movement_direction = 1  # Start moving right
            elif self.x >= right_bound:
                self.x = right_bound
                self.movement_direction = -1  # Start moving left
        
        # Update current lane based on position
        car_center = self.x + self.width / 2.0
        for i, lane_center in enumerate(LANE_CENTERS):
            lane_start = ROAD_LEFT_EDGE + i * LANE_WIDTH
            lane_end = lane_start + LANE_WIDTH
            if lane_start <= car_center < lane_end:
                self.lane = i
                break
        
        # Deactivate if off screen bottom
        if self.y > SCREEN_HEIGHT + 100:
            self.active = False
            
    def get_rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.width, self.height)
        
    def render(self, screen):
        if not self.active:
            return
            
        pygame.draw.rect(screen, self.color,
                        (int(self.x), int(self.y), self.width, self.height))
        pygame.draw.rect(screen, (255, 255, 255),
                        (int(self.x), int(self.y), self.width, self.height), 2)
        pygame.draw.rect(screen, (150, 200, 255),
                        (int(self.x) + 5, int(self.y) + 5,
                         self.width - 10, self.height // 4))
