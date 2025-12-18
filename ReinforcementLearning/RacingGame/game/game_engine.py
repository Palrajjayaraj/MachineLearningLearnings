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
        self.spawn_interval = 2.33  # 280px spacing = 180px gap (1.8 car lengths)
        self.lane_marker_offset = 0
        
        # Track last spawned car type to prevent consecutive yellow/red
        self.last_spawned_type = None
        self.last_spawned_lane = None  # Track lane of last red car
        self.consecutive_same_type = 0  # Track consecutive spawns of same type
        
        # Lane camping prevention
        self.player_current_lane_cars_passed = 0
        self.last_player_lane = None
        
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
        self.spawn_interval = 2.33  # 280px spacing = 180px gap (1.8 car lengths)
        self.lane_marker_offset = 0
        
        # Reset car passing counters
        self.green_cars_passed = 0
        self.yellow_cars_passed = 0
        self.red_cars_passed = 0
        
        # Reset last spawned type
        self.last_spawned_type = None
        self.last_spawned_lane = None
        self.consecutive_same_type = 0
        
        # Reset lane camping prevention
        self.player_current_lane_cars_passed = 0
        self.last_player_lane = None
        
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
                    
                    # Track lane camping (staying in same lane too long)
                    current_player_lane = self.player.current_lane
                    if self.last_player_lane is None:
                        # First car - initialize
                        self.last_player_lane = current_player_lane
                        self.player_current_lane_cars_passed = 1
                    elif self.last_player_lane == current_player_lane:
                        # Same lane - increment counter
                        self.player_current_lane_cars_passed += 1
                    else:
                        # Changed lanes - reset
                        self.player_current_lane_cars_passed = 1
                        self.last_player_lane = current_player_lane
                    
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
        
        # Adjust spawn interval based on speed multiplier to maintain consistent spacing
        # At higher speeds, opponents move faster, so we need to spawn less frequently
        # to maintain 1.8 car lengths (180px) gap
        # Formula: interval = 280px / (120 px/s * multiplier) = 2.33 / multiplier
        speed_multiplier = self._get_speed_multiplier()
        adjusted_interval = self.spawn_interval / speed_multiplier
        
        if self.time_since_last_spawn >= adjusted_interval:
            # Try to spawn - only reset timer if successful
            spawned = self._spawn_opponent()
            if spawned:
                self.time_since_last_spawn = 0
            
    def _spawn_opponent(self):
        """Spawn opponents in patterns to prevent straight-line driving
        
        Returns:
            bool: True if a car was spawned, False otherwise
        """
        
        # Only 15% chance to spawn blocking pattern (reduced from 30%)
        if random.random() < 0.15:
            return self._spawn_blocking_pattern()
        else:
            return self._spawn_single_car()
    
    def _spawn_single_car(self):
        """Spawn a single car in a random lane
        
        Returns:
            bool: True if spawned successfully, False otherwise
        """
        # Lane camping prevention: if player stayed in same lane for 2+ opponents, 
        # spawn an obstruction in that lane
        if self.player_current_lane_cars_passed >= 2 and self.last_player_lane is not None:
            # Validate lane is within bounds
            lane = max(0, min(NUM_LANES - 1, self.last_player_lane))
            self.player_current_lane_cars_passed = 0  # Reset counter
        else:
            lane = random.randint(0, NUM_LANES - 1)
        
        # CRITICAL FIX: Check PHYSICAL OVERLAP, not just lane property
        # Yellow/red cars change lanes, so opp.lane != physical position
        # min_spacing ensures proper gap between cars
        # Formula: gap = min_spacing - car_height = 300 - 100 = 200px (2 car lengths)
        min_spacing = OPPONENT_MIN_SPACING  # Ensures 2 car lengths gap
        spawn_y = -100  # Where new car will spawn
        
        # Check against ALL opponents for vertical overlap
        # RED CARS move across ALL lanes, so we can't rely on horizontal checks
        # Simply check if any car is within min_spacing vertically
        for opp in self.opponents:
            vertical_distance = abs(opp.y - spawn_y)
            if vertical_distance < min_spacing:
                return False  # Too close vertically - don't spawn
        
        # Red car horizontal spacing: check BEFORE creating car
        # Need to preview car type WITHOUT consuming random state
        if self.last_spawned_type == 'red' and self.last_spawned_lane is not None:
            # Save random state, create preview car, restore state
            saved_state = random.getstate()
            preview_car = OpponentCar(lane, 0, 0)
            will_be_red = (preview_car.car_type == 'red')
            random.setstate(saved_state)  # Restore so next OpponentCar gets same random
            
            if will_be_red:
                # Both current and next are red - ensure 2 lanes apart
                lane_distance = abs(lane - self.last_spawned_lane)
                if lane_distance < 2:
                    # Too close - pick opposite side
                    if self.last_spawned_lane <= 1:
                        lane = random.choice([2, 3])
                    else:
                        lane = random.choice([0, 1])
        
        # Prevent more than 2 consecutive red or yellow cars
        # If we've had 2 consecutive of same type, force green
        force_green = False
        if self.consecutive_same_type >= 2 and self.last_spawned_type in ['red', 'yellow']:
            force_green = True
        
        # Random spawn - maintains 5:3:2 ratio (green:yellow:red)
        if force_green:
            new_car = OpponentCar(lane, 0, 0, force_type='green')
        else:
            new_car = OpponentCar(lane, 0, 0)
        
        # Update consecutive counter
        if new_car.car_type == self.last_spawned_type:
            self.consecutive_same_type += 1
        else:
            self.consecutive_same_type = 1
        
        self.last_spawned_type = new_car.car_type
        if new_car.car_type == 'red':
            self.last_spawned_lane = lane
        
        self.opponents.append(new_car)
        return True  # Successfully spawned
    
    def _spawn_blocking_pattern(self):
        """Spawn multiple cars to block straight-line driving
        
        Returns:
            bool: True if at least one car was spawned, False otherwise
        """
        # Only spawn 2 cars with HUGE vertical spacing
        # CRITICAL: Never spawn in adjacent lanes - always leave gaps for player to escape
        num_cars = 2
        
        # Select non-adjacent lanes only (e.g., lanes 0 and 2, or 1 and 3)
        # This ensures player always has escape routes
        possible_lane_pairs = [
            [0, 2],  # Lanes 0 and 2 (lane 1 open between them)
            [0, 3],  # Lanes 0 and 3 (lanes 1,2 open)
            [1, 3],  # Lanes 1 and 3 (lane 2 open between them)
        ]
        lanes_to_spawn = random.choice(possible_lane_pairs)
        
        # Track cars spawned in THIS pattern to check against each other
        pattern_cars = []
        any_spawned = False
        
        for i, lane in enumerate(lanes_to_spawn):
            # Calculate spawn position for this car
            # Consistent spacing with single car spawns: 280px apart
            spawn_y = -100 - (i * 280)  # First at -100, second at -380
            min_spacing = OPPONENT_MIN_SPACING  # Ensures 2 car lengths gap
            
            # Calculate spawn lane boundaries
            lane_left = ROAD_LEFT_EDGE + lane * LANE_WIDTH
            lane_right = lane_left + LANE_WIDTH
            
            
            lane_clear = True
            
            # Check against existing opponents - vertical distance only
            # Red cars can move anywhere horizontally, so only check vertical spacing
            for opp in self.opponents:
                vertical_distance = abs(opp.y - spawn_y)
                if vertical_distance < min_spacing:
                    lane_clear = False
                    break
            
            # ALSO check against cars we just spawned in this pattern
            for pattern_car in pattern_cars:
                vertical_distance = abs(pattern_car.y - spawn_y)
                if vertical_distance < min_spacing:
                    lane_clear = False
                    break
            
            if lane_clear:
                # Consistent vertical offset - 280px apart for 1.8 car length gap
                vertical_offset = -(i * 280)
                horizontal_variance = 0  # No variance - keep cars centered in lanes
                
                # Random spawn - maintains natural 5:3:2 ratio
                new_car = OpponentCar(lane, vertical_offset, horizontal_variance)
                self.last_spawned_type = new_car.car_type
                
                self.opponents.append(new_car)
                pattern_cars.append(new_car)  # Track for checking against next car in pattern
                any_spawned = True
        
        return any_spawned
        
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
    
    def _draw_text_with_bg(self, text, color, x, y):
        """Draw text with semi-transparent background for better visibility"""
        text_surface = self.font.render(text, True, color)
        text_rect = text_surface.get_rect()
        text_rect.topleft = (x, y)
        
        # Draw semi-transparent black background
        bg_rect = text_rect.inflate(10, 6)  # Add padding
        bg_surface = pygame.Surface((bg_rect.width, bg_rect.height))
        bg_surface.set_alpha(180)  # Semi-transparent (0=transparent, 255=opaque)
        bg_surface.fill((0, 0, 0))  # Black background
        self.screen.blit(bg_surface, bg_rect.topleft)
        
        # Draw text on top
        self.screen.blit(text_surface, text_rect)
        
        return text_rect.height  # Return height for spacing calculations
            
    def _draw_hud(self):
        """Draw heads-up display with semi-transparent backgrounds"""
        # HUD on RIGHT side - completely off the track (road ends at x=550)
        hud_x = 570  # Right side, past the road edge
        
        # Distance
        self._draw_text_with_bg(
            f"Distance: {int(self.distance_traveled)}m / {int(TARGET_DISTANCE)}m",
            (255, 255, 255), hud_x, 10)
        
        # Time
        self._draw_text_with_bg(
            f"Time: {int(self.time_remaining)}s",
            (255, 255, 255), hud_x, 50)
        
        # Speed
        self._draw_text_with_bg(
            f"Player Speed: {int(self.player.velocity_y)} km/h",
            (255, 255, 255), hud_x, 90)
        
        # Opponent speed (decreases with multiplier - correct physics!)
        multiplier = self._get_speed_multiplier()
        # As difficulty increases, opponents go SLOWER forward (not faster)
        # This creates larger speed difference = faster overtaking visual
        opponent_forward_speed = int(OPPONENT_SPEED / multiplier)
        self._draw_text_with_bg(
            f"Opponent Speed: {opponent_forward_speed} km/h",
            (255, 200, 100), hud_x, 130)
        
        # Speed difference (relative speed - how fast you're overtaking)
        speed_difference = int(self.player.velocity_y - opponent_forward_speed)
        diff_color = (0, 255, 0) if speed_difference > 0 else (255, 100, 100)
        self._draw_text_with_bg(
            f"Overtaking Speed: +{speed_difference} km/h",
            diff_color, hud_x, 170)
        
        # Speed multiplier (difficulty indicator)
        if multiplier > 1.0:
            self._draw_text_with_bg(
                f"Difficulty: {multiplier}x",
                (255, 100, 100), hud_x, 210)
        
        # Cars passed counter (total cars overtaken by player)
        # Adjust position based on whether difficulty multiplier is shown
        y_offset = 260 if multiplier > 1.0 else 220
        
        self._draw_text_with_bg(
            f"Green Cars Passed: {self.green_cars_passed}",
            (0, 255, 0), hud_x, y_offset)
        
        self._draw_text_with_bg(
            f"Yellow Cars Passed: {self.yellow_cars_passed}",
            (255, 255, 0), hud_x, y_offset + 40)
        
        self._draw_text_with_bg(
            f"Red Cars Passed: {self.red_cars_passed}",
            (255, 100, 100), hud_x, y_offset + 80)
        
        # Total cars passed
        total_passed = self.green_cars_passed + self.yellow_cars_passed + self.red_cars_passed
        self._draw_text_with_bg(
            f"Total Cars Passed: {total_passed}",
            (255, 255, 255), hud_x, y_offset + 120)
        
        # Score (same position on right)
        self._draw_text_with_bg(
            f"Score: {self.score}",
            (255, 255, 255), hud_x, y_offset + 170)
        
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
