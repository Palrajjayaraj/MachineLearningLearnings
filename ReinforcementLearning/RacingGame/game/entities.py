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
            # Allow continuous movement while holding keys
            if left:
                # Move half lane left (50 pixels)
                half_lane = LANE_WIDTH / 2.0
                new_x = self.x - half_lane
                # Check boundaries
                if new_x >= ROAD_LEFT_EDGE:
                    self._start_lane_change(new_x)
                    
            elif right:  # Changed to elif to prevent simultaneous left+right
                # Move half lane right (50 pixels)
                half_lane = LANE_WIDTH / 2.0
                new_x = self.x + half_lane
                # Check boundaries
                if new_x + self.width <= ROAD_RIGHT_EDGE:
                    self._start_lane_change(new_x)
        
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
        
        # All cars start centered in their lane
        # Red cars will move across all lanes during gameplay
        # (No random initial position)
        
        # Movement state for zig-zagging  
        self.movement_timer = 0
        self.zig_zag_progress = 0
        
        # For yellow cars: pick ONE adjacent lane to alternate with
        # This ensures yellow cars only move between 2 adjacent lanes
        if self.car_type == 'yellow':
            # Pick left or right adjacent lane
            if self.start_lane == 0:
                self.target_adjacent_lane = 1  # Can only go right
            elif self.start_lane == NUM_LANES - 1:
                self.target_adjacent_lane = NUM_LANES - 2  # Can only go left
            else:
                # Pick randomly: left or right adjacent
                self.target_adjacent_lane = self.start_lane + random.choice([-1, 1])
            
            # IMPORTANT: Always start by moving TOWARDS target_adjacent_lane
            # This ensures yellow car starts moving immediately upon spawn
            self.movement_direction = 1
        elif self.car_type == 'red':
            # Red cars start with random direction
            self.movement_direction = random.choice([-1, 1])
            self.target_adjacent_lane = None
        else:
            # Green cars don't move horizontally
            self.movement_direction = 0
            self.target_adjacent_lane = None
        
    def update(self, delta_time, player_speed, speed_multiplier=1.0):
        if not self.active:
            return
            
        # Move vertically - fixed speed downward with multiplier for progressive difficulty
        # Base speed is 120 pixels/second, multiplied by difficulty factor
        base_speed = 120
        self.y += base_speed * speed_multiplier * delta_time
        
        # Horizontal movement based on car type
        if self.car_type == 'green':
            # Green: Drive straight
            pass
            
        elif self.car_type == 'yellow':
            # Yellow: Zig-zag between start_lane and target_adjacent_lane ONLY
            # Flip direction immediately when reaching target for fluid movement
            
            # Alternate between start_lane and target_adjacent_lane
            if self.movement_direction > 0:
                target_lane = self.target_adjacent_lane
            else:
                target_lane = self.start_lane
            
            # Move towards target lane center with speed multiplier
            target_x = LANE_CENTERS[target_lane] - self.width // 2
            if abs(self.x - target_x) > 2:
                horizontal_speed = 100 * speed_multiplier  # Increased from 60 for faster visible movement
                if self.x < target_x:
                    self.x += horizontal_speed * delta_time  # Move right
                else:
                    self.x -= horizontal_speed * delta_time  # Move left
            else:
                # Reached target - snap to center and immediately flip direction for fluid movement
                self.x = target_x
                self.movement_direction *= -1  # Flip direction immediately
            
        elif self.car_type == 'red':
            # Red: Zig-zag across ALL 4 lanes with speed multiplier
            self.movement_timer += delta_time
            
            # Move continuously at constant speed with multiplier
            horizontal_speed = 70 * speed_multiplier  # Apply multiplier
            self.x += self.movement_direction * horizontal_speed * delta_time
            
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
