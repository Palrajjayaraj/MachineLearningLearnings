import random
from .constants import *
from .entities import PlayerCar, OpponentCar

class RoadFighterGame:
    """
    Headless Game Engine
    Handles logic, physics, and state. No rendering.
    """
    def __init__(self):
        # Game State
        self.running = True
        self.game_over = False
        self.victory = False
        self.end_reason = None
        self.score = 0
        self.distance_traveled = 0.0
        self.time_remaining = RACE_TIME_LIMIT
        
        # Difficulty scaling
        self.elapsed_time = 0
        
        # Entities
        self.player = None
        self.opponents = []
        
        # Helper lists for spawning logic
        self.lane_positions = [
            ROAD_LEFT_EDGE + LANE_WIDTH * i + LANE_WIDTH // 2 
            for i in range(NUM_LANES)
        ]
        
        # Spawning State
        self.time_since_last_spawn = 0
        self.spawn_interval = 2.33
        
        # Logic - Camping Prevention
        self.player_current_lane_cars_passed = 0
        self.last_player_lane = None
        self.lane_camping_mode = False
        
        # Logic - Passing Bonus
        self.green_cars_passed = 0
        self.yellow_cars_passed = 0
        self.red_cars_passed = 0
        self.passing_bonus = 0
        self.total_cars_spawned = 0
        
        # Logic - Spawn Constraint Tracking
        self.last_spawned_type = None
        self.consecutive_same_type = 0
        self.last_spawned_lane_for_consecutive = None
        self.consecutive_same_lane = 0
        self.last_red_car_lane = None
        
        self.reset()
        
    def reset(self):
        """Reset game to starting state"""
        self.running = True
        self.game_over = False
        self.victory = False
        self.end_reason = None
        self.score = 0
        self.weighted_distance_score = 0.0 # NEW: Weighted accumulator
        self.distance_traveled = 0.0
        self.time_remaining = RACE_TIME_LIMIT
        self.elapsed_time = 0
        
        # Reset entities
        self.player = PlayerCar(PLAYER_START_X, PLAYER_Y)
        self.opponents = []
        
        # Reset tracking
        self.time_since_last_spawn = 0
        self.player_current_lane_cars_passed = 0
        self.last_player_lane = self.player.current_lane
        self.lane_camping_mode = False
        
        self.green_cars_passed = 0
        self.yellow_cars_passed = 0
        self.red_cars_passed = 0
        self.passing_bonus = 0
        self.total_cars_spawned = 0
        
        self.last_spawned_type = None
        self.consecutive_same_type = 0
        self.last_spawned_lane_for_consecutive = None
        self.consecutive_same_lane = 0
        self.last_red_car_lane = None
        
        return self.get_state()

    def step(self, left, right, brake):
        """Execute one frame of logic"""
        if self.game_over:
            return self.get_state(), 0, True, {'victory': self.victory}
            
        dt = 1/60.0
        
        # Update Game Logic
        self.update(dt, left, right, brake)
        
        # Calculate Reward (Step Based)
        # Reward should be proportional to distance covered THIS STEP
        # distance_delta = (velocity_y / 3.6) * dt
        # 3.6 is the conversion factor to convert km/h to m/s (1000m / 3600s)
        distance_delta = (self.player.velocity_y / 3.6) * dt
        reward = distance_delta * 0.1 # 10m/s -> 1.0 reward per frame roughly
        
        done = self.game_over
        info = {
            'victory': self.victory,
            'distance': self.distance_traveled,
            'score': self.score
        }
        
        return self.get_state(), reward, done, info

    def update(self, delta_time, left, right, brake):
        """Main update loop"""
        if self.game_over:
            return

        self.elapsed_time += delta_time
        
        # 1. Update Player
        self.player.update(delta_time, left, right, brake)
        # Convert km/h to m/s for distance calculation
        # distance (m) = velocity (km/h) / 3.6 * time (s)
        distance_delta = (self.player.velocity_y / 3.6) * delta_time
        self.distance_traveled += distance_delta
        
        # 2. Update Time
        self.time_remaining -= delta_time
        if self.time_remaining <= 0 and not self.victory:
            self.game_over = True
            self.victory = False
            self.end_reason = 'timeout'
            return

        # 3. Check Victory
        if self.distance_traveled >= TARGET_DISTANCE:
            self.game_over = True
            self.victory = True
            self.end_reason = 'victory'
            return
            
        # 4. Spawning
        speed_multiplier = self._get_speed_multiplier()
        self._update_spawning(delta_time)
        
        # 5. Update Score
        # Score = Sum (Distance Delta * 10 * Multiplier) + Passing Bonuses
        # Passing bonuses are tracked in self.passing_bonus
        
        # distance_delta was calculated earlier (line 126). 
        # But we need it here. Let's recalculate or move logic.
        # Actually it's cleaner to just do:
        # weighted_score += distance_delta * 10 * speed_multiplier
        
        # Since distance_delta is local to this function (wait, it was local var).
        # We need to access it. Let's just use:
        # distance_delta = (self.player.velocity_y / 3.6) * delta_time
        # which is exactly what line 126 did.
        
        # Wait, I can't access local var from previous block nicely without reorganizing.
        # I will just recalculate it here for scoring purposes, it's cheap.
        
        d_delta = (self.player.velocity_y / 3.6) * delta_time
        self.weighted_distance_score += d_delta * 10 * speed_multiplier
        
        self.score = int(self.weighted_distance_score) + self.passing_bonus
        
        # 5. Update Opponents
        for opp in self.opponents:
            old_y = opp.y
            opp.update(delta_time, self.player.velocity_y, speed_multiplier)
            
            # Check for passing
            if old_y < self.player.y and opp.y >= self.player.y:
                if not hasattr(opp, 'passed_counted') or not opp.passed_counted:
                    opp.passed_counted = True
                    self.passing_bonus += 2.0
                    self._update_cars_passed_stats(opp)
                    self._check_camping_logic()

        # 6. Clean up off-screen components
        self.opponents = [opp for opp in self.opponents if opp.y < SCREEN_HEIGHT + 100]

        # 7. Collisions
        if self._check_collisions():
            self.game_over = True
            self.victory = False
            self.end_reason = 'collision'

    def _get_speed_multiplier(self):
        return 1.0 + min(self.elapsed_time / 60.0, 1.0)

    def _update_cars_passed_stats(self, opp):
        if opp.car_type == 'green': self.green_cars_passed += 1
        elif opp.car_type == 'yellow': self.yellow_cars_passed += 1
        elif opp.car_type == 'red': self.red_cars_passed += 1

    def _check_camping_logic(self):
        current_lane = self.player.current_lane
        if self.last_player_lane == current_lane:
            self.player_current_lane_cars_passed += 1
            if self.player_current_lane_cars_passed >= 2:
                self.lane_camping_mode = True
        else:
            self.player_current_lane_cars_passed = 1
            self.last_player_lane = current_lane
            self.lane_camping_mode = False

    def _update_spawning(self, delta_time):
        self.time_since_last_spawn += delta_time
        current_interval = self.spawn_interval / self._get_speed_multiplier()
        if self.time_since_last_spawn >= current_interval:
            spawned = False
            if random.random() < 0.15 and len(self.opponents) < 3:
                spawned = self._spawn_blocking_pattern()
            if not spawned:
                spawned = self._spawn_single_car()
            if spawned:
                self.time_since_last_spawn = 0

    def _spawn_single_car(self):
        # Lane camping prevention
        if self.lane_camping_mode and self.last_player_lane is not None:
            lane = max(0, min(NUM_LANES - 1, self.last_player_lane))
        else:
            lane = random.randint(0, NUM_LANES - 1)
        
        # Check PHYSICAL OVERLAP
        min_spacing = OPPONENT_MIN_SPACING
        spawn_y = -100
        
        for opp in self.opponents:
            vertical_distance = abs(opp.y - spawn_y)
            if vertical_distance < min_spacing:
                return False
        
        # RULE 1: No more than 2 cars in same lane consecutively
        if self.last_spawned_lane_for_consecutive == lane and self.consecutive_same_lane >= 2:
            available_lanes = [l for l in range(NUM_LANES) if l != lane]
            if available_lanes:
                lane = random.choice(available_lanes)
        
        # Red car horizontal spacing
        if self.last_spawned_type == 'red' and self.last_red_car_lane is not None:
             lane_distance = abs(lane - self.last_red_car_lane)
             if lane_distance < 2:
                 if self.last_red_car_lane <= 1: lane = random.choice([2, 3])
                 else: lane = random.choice([0, 1])

        # RULE 2: No more than 2 consecutive same color
        force_different_type = False
        if self.consecutive_same_type >= 2:
            force_different_type = True
        
        if force_different_type:
            available_types = [t for t in ['green', 'yellow', 'red'] if t != self.last_spawned_type]
            forced_type = random.choice(available_types)
            new_car = OpponentCar(lane, 0, 0, force_type=forced_type)
        else:
            new_car = OpponentCar(lane, 0, 0)
        
        if new_car.car_type == self.last_spawned_type:
            self.consecutive_same_type += 1
        else:
            self.consecutive_same_type = 1
        
        if lane == self.last_spawned_lane_for_consecutive:
            self.consecutive_same_lane += 1
        else:
            self.consecutive_same_lane = 1
        
        self.last_spawned_type = new_car.car_type
        self.last_spawned_lane_for_consecutive = lane
        if new_car.car_type == 'red':
            self.last_red_car_lane = lane
        
        self.opponents.append(new_car)
        return True

    def _get_speed_multiplier(self):
        """
        Calculate difficulty multiplier based on Time Elapsed (Stepped)
        0-30s   -> 1.0 (Base)
        30-46s  -> 1.2
        46-60s  -> 1.4
        60-80s  -> 1.6
        80-100s -> 1.8
        100s+   -> 2.0 (Max)
        """
        time = self.elapsed_time
        
        if time < 30: return 1.0
        elif time < 46: return 1.2
        elif time < 60: return 1.4
        elif time < 80: return 1.6
        elif time < 100: return 1.8
        else: return 2.0

    def _spawn_blocking_pattern(self):
        possible_lane_pairs = [[0, 2], [0, 3], [1, 3]]
        lanes_to_spawn = random.choice(possible_lane_pairs)
        
        if self.lane_camping_mode and self.last_player_lane is not None:
            player_lane = max(0, min(NUM_LANES - 1, self.last_player_lane))
            other_lanes = [l for l in range(NUM_LANES) if l != player_lane]
            if other_lanes:
                lanes_to_spawn = [player_lane, random.choice(other_lanes)]
        
        pattern_cars = []
        any_spawned = False
        
        for i, lane in enumerate(lanes_to_spawn):
            spawn_y = -100 - (i * 280)
            min_spacing = OPPONENT_MIN_SPACING
            lane_clear = True
            
            for opp in self.opponents:
                if abs(opp.y - spawn_y) < min_spacing:
                    lane_clear = False
                    break
            for pattern_car in pattern_cars:
                if abs(pattern_car.y - spawn_y) < min_spacing:
                    lane_clear = False
                    break
            
            if lane_clear:
                vertical_offset = -(i * 280)
                force_different_type = (self.consecutive_same_type >= 2)
                
                if force_different_type:
                    available_types = [t for t in ['green', 'yellow', 'red'] if t != self.last_spawned_type]
                    forced_type = random.choice(available_types)
                    new_car = OpponentCar(lane, vertical_offset, 0, force_type=forced_type)
                else:
                    new_car = OpponentCar(lane, vertical_offset, 0)
                
                if new_car.car_type == self.last_spawned_type:
                    self.consecutive_same_type += 1
                else:
                    self.consecutive_same_type = 1
                    
                if lane == self.last_spawned_lane_for_consecutive:
                    self.consecutive_same_lane += 1
                else:
                    self.consecutive_same_lane = 1
                
                self.last_spawned_type = new_car.car_type
                self.last_spawned_lane_for_consecutive = lane
                if new_car.car_type == 'red':
                    self.last_red_car_lane = lane
                
                self.opponents.append(new_car)
                pattern_cars.append(new_car)
                any_spawned = True
        
        return any_spawned

    def _check_collisions(self):
        player_rect = self.player.get_rect()
        for opp in self.opponents:
            if player_rect.colliderect(opp.get_rect()):
                return True
        return False

    def get_state(self):
        # State V3: Enhanced Object Awareness
        # Size: 32 (Player[4] + Global[3] + 5 * Car[5])
        
        state = []
        player = self.player
        
        # 1. Player features [4]
        state.extend([
            player.x / SCREEN_WIDTH,                 # Normalized X
            player.velocity_y / PLAYER_MAX_SPEED,    # Normalized Speed
            player.current_lane / (NUM_LANES - 1),   # Lane Index
            1.0 if player.is_changing_lane else 0.0  # Lane Change Flag
        ])
        
        # 2. Global Progress [3]
        current_mult = self._get_speed_multiplier()
        state.extend([
            self.time_remaining / RACE_TIME_LIMIT,
            min(self.distance_traveled / TARGET_DISTANCE, 1.0),
            current_mult / 2.0  # Normalized Multiplier (1.0-2.0 -> 0.5-1.0)
        ])
        
        # 3. Nearest Opponents (KNN) [5 * 5 = 25]
        opp_data = []
        for opp in self.opponents:
            if not opp.active: continue
            
            # Relative Position
            dx = (opp.x - player.x) / SCREEN_WIDTH
            dy = (opp.y - player.y) / SCREEN_HEIGHT
            dist = (dx*dx + dy*dy)**0.5
            
            # Type Encoding
            type_val = 0.0
            if opp.car_type == 'yellow': type_val = 0.5
            elif opp.car_type == 'red': type_val = 1.0
            
            # Direction/Vel X
            dir_val = float(opp.movement_direction)
            
            # Relative Velocity Y (Opponent Screen Speed)
            # Calculated as (120 * Mult) / Max_Speed_Reference (~300)
            # Negative because they move "down" towards player? 
            # Actually they move +Y (down screen). Player is fixed.
            # So they effectively have speed +Y.
            opp_speed_y = (120 * current_mult) / 300.0
            
            opp_data.append({
                'dist': dist,
                'features': [dx, dy, type_val, dir_val, opp_speed_y]
            })
            
        # Sort by distance
        opp_data.sort(key=lambda x: x['dist'])
        
        # Take nearest 5
        k = 5
        for i in range(k):
            if i < len(opp_data):
                state.extend(opp_data[i]['features'])
            else:
                # Padding: Far away, no speed
                state.extend([0.0, -2.0, 0.0, 0.0, 0.0]) 
                
        return state
