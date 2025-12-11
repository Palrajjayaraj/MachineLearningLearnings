"""
Road Fighter - Game Engine
"""

import pygame
import random
from constants import *
from entities import PlayerCar, OpponentCar


class RoadFighterGame:
    """Main game engine"""
    
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Road Fighter")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        
        self.player = None
        self.opponents = []
        self.distance_traveled = 0
        self.time_remaining = RACE_TIME_LIMIT
        self.score = 0
        self.running = False
        self.game_over = False
        self.victory = False
        self.end_reason = None  # 'collision', 'timeout', or 'victory'
        
        # Car passing counters
        self.green_cars_passed = 0
        self.yellow_cars_passed = 0
        self.red_cars_passed = 0
        
        self.time_since_last_spawn = 0
        self.spawn_interval = 2.0
        self.lane_marker_offset = 0
        
        # Track last spawned car type to prevent consecutive yellow/red
        self.last_spawned_type = None
        
    def reset(self):
        """Reset game to starting state"""
        self.player = PlayerCar(PLAYER_START_X, PLAYER_Y)
        self.opponents = []
        self.distance_traveled = 0
        self.time_remaining = RACE_TIME_LIMIT
        self.score = 0
        self.running = True
        self.game_over = False
        self.victory = False
        self.end_reason = None
        self.time_since_last_spawn = 0
        self.spawn_interval = 2.0
        self.lane_marker_offset = 0
        
        # Reset car passing counters
        self.green_cars_passed = 0
        self.yellow_cars_passed = 0
        self.red_cars_passed = 0
        
        # Reset last spawned type
        self.last_spawned_type = None
        
    def step(self, left, right, brake):
        """
        Execute one frame of the game (for ML control)
        
        Args:
            left: Boolean - move left
            right: Boolean - move right  
            brake: Boolean - brake
            
        Returns:
            state: List of numbers representing game state
            reward: Float - reward for this step
            done: Boolean - is episode over?
            info: Dict with additional information
        """
        # Store previous state for reward calculation
        prev_distance = self.distance_traveled
        prev_num_opponents = len(self.opponents)
        
        # Update game
        self.update(left, right, brake)
        
        # Get current state
        state = self.get_state()
        
        # Calculate reward
        distance_delta = self.distance_traveled - prev_distance
        collision_occurred = len(self.opponents) < prev_num_opponents  # Simplified
        reward = self.calculate_reward(distance_delta, collision_occurred)
        
        # Check if done
        done = self.game_over
        
        # Additional info
        info = {
            'distance': self.distance_traveled,
            'time_remaining': self.time_remaining,
            'score': self.score,
            'victory': self.victory,
            'collision': collision_occurred,
            'green_cars_passed': self.green_cars_passed,
            'yellow_cars_passed': self.yellow_cars_passed,
            'red_cars_passed': self.red_cars_passed,
            'total_cars_passed': self.green_cars_passed + self.yellow_cars_passed + self.red_cars_passed
        }
        
        return state, reward, done, info
    
    def update(self, left, right, brake):
        """Update game state"""
        delta_time = 1.0 / FPS
        
        # Update player
        self.player.update(delta_time, left, right, brake)
        
        # Update distance and time
        distance_delta = (self.player.velocity_y / 3.6) * delta_time
        self.distance_traveled += distance_delta
        self.score += int(distance_delta)
        self.time_remaining -= delta_time
        
        # Spawn opponents
        self._update_spawning(delta_time)
        
        # Get current speed multiplier for progressive difficulty
        speed_multiplier = self._get_speed_multiplier()
        
        # Update opponents with speed multiplier and track cars passed
        for opp in self.opponents:
            # Store position before update
            old_y = opp.y
            
            # Update opponent position
            opp.update(delta_time, self.player.velocity_y, speed_multiplier)
            
            # Check if car crossed the player position (we passed it)
            # Player is at y=450, opponents move from negative y to positive y
            # If old_y was above player and new y is at or below player, we passed it
            if old_y < self.player.y and opp.y >= self.player.y:
                # Check if we haven't counted this car yet
                if not hasattr(opp, 'passed_counted') or not opp.passed_counted:
                    opp.passed_counted = True
                    
                    # Increment appropriate counter based on car type
                    if opp.car_type == 'green':
                        self.green_cars_passed += 1
                    elif opp.car_type == 'yellow':
                        self.yellow_cars_passed += 1
                    elif opp.car_type == 'red':
                        self.red_cars_passed += 1
        
        # Remove inactive opponents
        self.opponents = [opp for opp in self.opponents if opp.active]
        
        # Check collisions
        collision = self._check_collisions()
        
        # Check win/loss
        if self.distance_traveled >= TARGET_DISTANCE:
            self.victory = True
            self.game_over = True
            self.end_reason = 'victory'
        elif self.time_remaining <= 0:
            self.victory = False
            self.game_over = True
            self.end_reason = 'timeout'
            
        return collision
    
    def get_state(self):
        """
        Extract game state as numbers (for ML)
        
        Returns 20 features:
        [0-3]   Player: x_pos, speed, lane, is_changing_lane
        [4-5]   Progress: time_remaining, distance_progress
        [6-17]  Opponents: For each lane (4 lanes × 3 features):
                - distance to closest car ahead (0-1)
                - relative speed (0-1)
                - car exists (0 or 1)
        [18-19] Danger: immediate_danger, near_danger
        """
        state = []
        
        # Player features (4)
        state.append(self.player.x / SCREEN_WIDTH)  # Normalized x position
        state.append(self.player.velocity_y / PLAYER_MAX_SPEED)  # Normalized speed
        state.append(self.player.current_lane / (NUM_LANES - 1))  # Normalized lane (0-1)
        state.append(1.0 if self.player.is_changing_lane else 0.0)
        
        # Progress features (2)
        state.append(self.time_remaining / RACE_TIME_LIMIT)
        state.append(min(1.0, self.distance_traveled / TARGET_DISTANCE))
        
        # Opponent detection per lane (12 features: 4 lanes × 3)
        for lane in range(NUM_LANES):
            closest_distance = 999999
            closest_speed = 0
            exists = 0
            
            for opp in self.opponents:
                if opp.lane == lane and opp.active:
                    distance = opp.y - self.player.y
                    # Only consider cars ahead
                    if 0 < distance < closest_distance:
                        closest_distance = distance
                        closest_speed = opp.speed
                        exists = 1
            
            # Normalize and add to state
            state.append(min(1.0, closest_distance / 600.0))  # Distance (0-1)
            state.append(closest_speed / OPPONENT_SPEED if exists else 0)  # Speed (0-1)
            state.append(exists)  # Exists (0 or 1)
        
        # Danger indicators (2)
        immediate_danger = any(
            opp.active and opp.lane == self.player.current_lane and
            0 < (opp.y - self.player.y) < 100
            for opp in self.opponents
        )
        near_danger = any(
            opp.active and opp.lane == self.player.current_lane and
            0 < (opp.y - self.player.y) < 200
            for opp in self.opponents
        )
        
        state.append(1.0 if immediate_danger else 0.0)
        state.append(1.0 if near_danger else 0.0)
        
        return state
    
    def calculate_reward(self, distance_delta, collision_occurred):
        """
        Calculate reward for this step (for ML)
        
        This is the most important function for training!
        Adjust these values to change what the AI learns.
        
        Args:
            distance_delta: How far the car moved this frame
            collision_occurred: Did a collision happen?
            
        Returns:
            reward: Float
        """
        reward = 0
        
        # Progress reward - encourage moving forward
        reward += distance_delta * 0.1
        
        # Survival reward - encourage staying alive
        reward += 0.1
        
        # Speed bonus - encourage going fast
        if self.player.velocity_y > 250:
            reward += 0.5
        
        # Collision penalty - discourage crashes
        if collision_occurred:
            reward -= 100
        
        # Episode end rewards
        if self.game_over:
            if self.victory:
                reward += 1000  # Big reward for winning
            else:
                reward -= 500   # Penalty for running out of time
        
        return reward
            
    def _get_speed_multiplier(self):
        """
        Calculate speed multiplier based on elapsed time
        Progressive difficulty scaling
        
        Returns:
            multiplier: Float (1.0 to 2.0)
        """
        elapsed_time = RACE_TIME_LIMIT - self.time_remaining
        
        if elapsed_time < 30:
            return 1.0   # 0-30s: Normal speed
        elif elapsed_time < 60:
            return 1.2   # 30-60s: 1.2x speed
        elif elapsed_time < 80:
            return 1.4   # 60-80s: 1.4x speed
        elif elapsed_time < 100:
            return 1.6   # 80-100s: 1.6x speed
        elif elapsed_time < 120:
            return 1.8   # 100-120s: 1.8x speed
        else:
            return 2.0   # 120s+: 2.0x speed
    
    def _update_spawning(self, delta_time):
        """Spawn new opponents"""
        self.time_since_last_spawn += delta_time
        # Slower spawn interval - 2 seconds between spawns
        self.spawn_interval = 2.0
        
        if self.time_since_last_spawn >= self.spawn_interval:
            self._spawn_opponent()
            self.time_since_last_spawn = 0
            
    def _spawn_opponent(self):
        """Spawn opponents in patterns to prevent straight-line driving"""
        
        # Only 15% chance to spawn blocking pattern (reduced from 30%)
        if random.random() < 0.15:
            self._spawn_blocking_pattern()
        else:
            self._spawn_single_car()
    
    def _spawn_single_car(self):
        """Spawn a single car in a random lane"""
        lane = random.randint(0, NUM_LANES - 1)
        
        # Strict checking - make sure NO cars are nearby in this lane
        for opp in self.opponents:
            # Check if any car in this lane is too close
            if opp.lane == lane:
                # If car is anywhere near spawn area (from -400 to +200 pixels)
                if -400 < opp.y < 200:
                    return  # Don't spawn - too crowded
        
        # Force green car if last spawn was yellow or red
        # This ensures green car separates yellow/red cars
        force_green = (self.last_spawned_type in ['yellow', 'red'])
        
        if force_green:
            # Force green to separate yellow/red cars
            new_car = OpponentCar(lane, 0, 0, force_type='green')
            self.last_spawned_type = 'green'
        else:
            # Normal random spawn - maintains 5:3:1 ratio
            new_car = OpponentCar(lane, 0, 0)
            self.last_spawned_type = new_car.car_type
        
        self.opponents.append(new_car)
    
    def _spawn_blocking_pattern(self):
        """Spawn multiple cars to block straight-line driving"""
        # Only spawn 2 cars (not 3) with huge vertical spacing
        num_cars = 2
        
        # Always leave at least 2 lanes open
        lanes_to_spawn = random.sample(range(NUM_LANES), num_cars)
        
        for i, lane in enumerate(lanes_to_spawn):
            # Check if lane is clear
            lane_clear = True
            for opp in self.opponents:
                if opp.lane == lane and opp.y < 300 and opp.y > -300:
                    lane_clear = False
                    break
            
            if lane_clear:
                # HUGE vertical offset so cars are very staggered
                # First car at 0, second at -300
                vertical_offset = -i * 300
                # Small horizontal variance
                horizontal_variance = random.randint(-20, 20)
                
                # Force green car if last spawn was yellow or red
                force_green = (self.last_spawned_type in ['yellow', 'red'])
                
                if force_green:
                    # Force green to separate yellow/red cars
                    new_car = OpponentCar(lane, vertical_offset, horizontal_variance, force_type='green')
                    self.last_spawned_type = 'green'
                else:
                    # Normal random spawn - maintains natural 5:3:1 ratio
                    new_car = OpponentCar(lane, vertical_offset, horizontal_variance)
                    self.last_spawned_type = new_car.car_type
                
                self.opponents.append(new_car)
        
    def _check_collisions(self):
        """
        Check collisions with opponents
        
        Returns:
            collision: Boolean - did a collision occur?
        """
        player_rect = self.player.get_rect()
        collision = False
        
        for opp in self.opponents:
            if opp.active and player_rect.colliderect(opp.get_rect()):
                collision = True
                # Game over on collision
                self.game_over = True
                self.victory = False
                self.end_reason = 'collision'
                break
                
        return collision
                
    def render(self):
        """Render game"""
        # Clear screen
        self.screen.fill(COLOR_GRASS)
        
        # Draw road
        pygame.draw.rect(self.screen, COLOR_ROAD,
                        (ROAD_LEFT_EDGE, 0, ROAD_WIDTH, SCREEN_HEIGHT))
        
        # Draw road edges
        pygame.draw.line(self.screen, COLOR_ROAD_EDGE,
                        (ROAD_LEFT_EDGE, 0), (ROAD_LEFT_EDGE, SCREEN_HEIGHT), 3)
        pygame.draw.line(self.screen, COLOR_ROAD_EDGE,
                        (ROAD_RIGHT_EDGE, 0), (ROAD_RIGHT_EDGE, SCREEN_HEIGHT), 3)
        
        # Draw lane markers
        self._draw_lane_markers()
        
        # Draw opponents
        for opp in self.opponents:
            opp.render(self.screen)
            
        # Draw player
        self.player.render(self.screen)
        
        # Draw HUD
        self._draw_hud()
        
        pygame.display.flip()
        
    def _draw_lane_markers(self):
        """Draw lane dividing lines"""
        for lane in range(1, NUM_LANES):
            x = ROAD_LEFT_EDGE + lane * LANE_WIDTH
            y = int(self.lane_marker_offset)
            
            while y < SCREEN_HEIGHT:
                pygame.draw.rect(self.screen, COLOR_LANE_MARKER,
                               (x - 2, y, 4, LANE_MARKER_HEIGHT))
                y += LANE_MARKER_HEIGHT + LANE_MARKER_GAP
                
        self.lane_marker_offset += self.player.velocity_y / 20
        if self.lane_marker_offset > LANE_MARKER_HEIGHT + LANE_MARKER_GAP:
            self.lane_marker_offset = 0
            
    def _draw_hud(self):
        """Draw heads-up display"""
        # Distance
        dist_text = self.font.render(
            f"Distance: {int(self.distance_traveled)}m / {int(TARGET_DISTANCE)}m",
            True, (255, 255, 255))
        self.screen.blit(dist_text, (10, 10))
        
        # Time
        time_text = self.font.render(
            f"Time: {int(self.time_remaining)}s",
            True, (255, 255, 255))
        self.screen.blit(time_text, (10, 50))
        
        # Speed
        speed_text = self.font.render(
            f"Speed: {int(self.player.velocity_y)} km/h",
            True, (255, 255, 255))
        self.screen.blit(speed_text, (10, 90))
        
        # Speed multiplier (difficulty indicator)
        multiplier = self._get_speed_multiplier()
        if multiplier > 1.0:
            multiplier_text = self.font.render(
                f"Difficulty: {multiplier}x",
                True, (255, 100, 100))  # Red color for increased difficulty
            self.screen.blit(multiplier_text, (10, 130))
        
        # Cars passed counter (total cars overtaken by player)
        y_offset = 170 if multiplier > 1.0 else 130
        
        green_text = self.font.render(f"Green passed: {self.green_cars_passed}", True, (0, 255, 0))
        self.screen.blit(green_text, (10, y_offset))
        
        yellow_text = self.font.render(f"Yellow passed: {self.yellow_cars_passed}", True, (255, 255, 0))
        self.screen.blit(yellow_text, (10, y_offset + 30))
        
        red_text = self.font.render(f"Red passed: {self.red_cars_passed}", True, (255, 100, 100))
        self.screen.blit(red_text, (10, y_offset + 60))
        
        # Total cars passed
        total_passed = self.green_cars_passed + self.yellow_cars_passed + self.red_cars_passed
        total_text = self.font.render(f"Total passed: {total_passed}", True, (255, 255, 255))
        self.screen.blit(total_text, (10, y_offset + 100))
        
        # Score
        score_text = self.font.render(
            f"Score: {self.score}",
            True, (255, 255, 255))
        self.screen.blit(score_text, (SCREEN_WIDTH - 200, 10))
        
        # Game over
        if self.game_over:
            big_font = pygame.font.Font(None, 72)
            medium_font = pygame.font.Font(None, 48)
            
            if self.end_reason == 'victory':
                msg1 = "VICTORY!"
                color = (0, 255, 0)
            elif self.end_reason == 'collision':
                msg1 = "COLLISION!"
                color = (255, 0, 0)
            else:  # timeout
                msg1 = "TIME'S UP!"
                color = (255, 165, 0)  # Orange
            
            # Main message
            msg_text1 = big_font.render(msg1, True, color)
            rect1 = msg_text1.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 40))
            self.screen.blit(msg_text1, rect1)
            
            # GAME OVER text (unless victory)
            if self.end_reason != 'victory':
                msg_text2 = medium_font.render("GAME OVER", True, (255, 255, 255))
                rect2 = msg_text2.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 40))
                self.screen.blit(msg_text2, rect2)
            
    def run(self):
        """Main game loop"""
        self.reset()
        
        while self.running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    
            # Get keyboard input
            keys = pygame.key.get_pressed()
            left = keys[pygame.K_LEFT]
            right = keys[pygame.K_RIGHT]
            brake = keys[pygame.K_DOWN]
            
            # Update
            self.update(left, right, brake)
            
            # Render
            self.render()
            
            # Control frame rate
            self.clock.tick(FPS)
            
            # Check if done
            if self.game_over:
                # Show game over message for 2 seconds then close
                for _ in range(2 * FPS):
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            self.running = False
                            break
                    self.render()
                    self.clock.tick(FPS)
                # Close the game
                self.running = False
                
        pygame.quit()
