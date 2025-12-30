import pygame
import os
from .constants import *
from .entities import PlayerCar, OpponentCar

class GameRenderer:
    """
    Handles all Pygame drawing and asset loading.
    Decoupled from game logic.
    """
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Road Fighter - Gym Mode")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        
        self.lane_marker_offset = 0
        
        # Load assets
        self.crash_sound = None
        self.point_sound = None
        self.load_assets()

    def load_assets(self):
        """Load game images"""
        try:
            # Player Car
            self.player_img = pygame.image.load(os.path.join("assets", "player_car.png")).convert_alpha()
            self.player_img = pygame.transform.scale(self.player_img, (CAR_WIDTH, CAR_HEIGHT))
            
            # Opponent Cars
            self.opponent_imgs = {}
            colors = ['green', 'yellow', 'red', 'truck']
            for color in colors:
                img = pygame.image.load(os.path.join("assets", f"{color}_car.png")).convert_alpha()
                self.opponent_imgs[color] = pygame.transform.scale(img, (CAR_WIDTH, CAR_HEIGHT))
                
            # Sounds
            self.crash_sound = pygame.mixer.Sound(os.path.join("assets", "crash.wav"))
            self.point_sound = pygame.mixer.Sound(os.path.join("assets", "point.wav"))
            
        except Exception as e:
            # Silent fallback
            self.player_img = None
            self.opponent_imgs = None

    def render(self, core_game):
        """Draw the current state of the CoreGame"""
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
        self._draw_lane_markers(core_game)
        
        # Draw opponents
        for opp in core_game.opponents:
            self._draw_car(opp, is_player=False)
            
        # Draw player
        if core_game.player:
            self._draw_car(core_game.player, is_player=True)
            
        # Draw HUD
        self._draw_hud(core_game)
        
        # Update display
        pygame.display.flip()
        
        # Cap frame rate
        self.clock.tick(60)

    def _draw_car(self, entity, is_player):
        # Note: entity.x/y are top-left coordinates (defined in entities.py)
        
        if is_player and self.player_img:
            self.screen.blit(self.player_img, (entity.x, entity.y))
        elif not is_player and self.opponent_imgs and entity.car_type in self.opponent_imgs:
            self.screen.blit(self.opponent_imgs[entity.car_type], (entity.x, entity.y))
        else:
            # Fallback rect
            if is_player:
                color = COLOR_PLAYER
            else:
                # Use the entity's own color if available, otherwise fallback
                color = getattr(entity, 'color', COLOR_OPPONENT)
                
            pygame.draw.rect(self.screen, color, 
                           (entity.x, entity.y, CAR_WIDTH, CAR_HEIGHT))
                           
            # Draw simple details to distinguish front/back
            # Windshield (light blue)
            pygame.draw.rect(self.screen, (150, 200, 255),
                           (entity.x + 5, entity.y + 5, CAR_WIDTH - 10, CAR_HEIGHT // 4))
                           
            # Wheels (black)
            wheel_w, wheel_h = 6, 14
            wheel_color = (0, 0, 0)
            # FL, FR, RL, RR
            pygame.draw.rect(self.screen, wheel_color, (entity.x - 2, entity.y + 10, wheel_w, wheel_h))
            pygame.draw.rect(self.screen, wheel_color, (entity.x + CAR_WIDTH - 4, entity.y + 10, wheel_w, wheel_h))
            pygame.draw.rect(self.screen, wheel_color, (entity.x - 2, entity.y + CAR_HEIGHT - 24, wheel_w, wheel_h))
            pygame.draw.rect(self.screen, wheel_color, (entity.x + CAR_WIDTH - 4, entity.y + CAR_HEIGHT - 24, wheel_w, wheel_h))

            # Draw Blinkers (for Red/Yellow opponents)
            if not is_player and hasattr(entity, 'car_type') and entity.car_type in ['yellow', 'red']:
                if hasattr(entity, 'movement_direction') and hasattr(entity, 'movement_timer'):
                    # Blink 3 times/sec
                    blink_on = int(entity.movement_timer * 3) % 2 == 0
                    
                    if blink_on:
                        # Yellow cars -> Red blinkers, Red cars -> Yellow blinkers
                        blinker_color = (255, 0, 0) if entity.car_type == 'yellow' else (255, 255, 0)
                        blinker_size = 6
                        back_y = int(entity.y) + CAR_HEIGHT - 10
                        
                        if entity.movement_direction < 0: # Moving Left
                             pygame.draw.circle(self.screen, blinker_color,
                                              (int(entity.x) + 10, back_y), blinker_size)
                        elif entity.movement_direction > 0: # Moving Right
                             pygame.draw.circle(self.screen, blinker_color,
                                              (int(entity.x) + CAR_WIDTH - 10, back_y), blinker_size)

    def _draw_lane_markers(self, core_game):
        # Determine speed for marker animation
        player_speed = core_game.player.velocity_y if core_game.player else 0
        speed_factor = player_speed / PLAYER_MAX_SPEED
        
        # Update offset based on speed
        self.lane_marker_offset += (5 + 15 * speed_factor)
        if self.lane_marker_offset >= 40:
            self.lane_marker_offset = 0
            
        for i in range(1, NUM_LANES):
            x = ROAD_LEFT_EDGE + i * LANE_WIDTH
            for y in range(int(-40 + self.lane_marker_offset), SCREEN_HEIGHT, 40):
                pygame.draw.line(self.screen, COLOR_LANE_MARKER, (x, y), (x, y + 20), 2)

    def _draw_hud(self, core_game):
        # HUD Area (Right side)
        hud_x = ROAD_RIGHT_EDGE + 20
        hud_width = SCREEN_WIDTH - ROAD_RIGHT_EDGE - 40
        
        # Draw HUD Background Panel
        panel_rect = pygame.Rect(hud_x, 20, hud_width, SCREEN_HEIGHT - 40)
        pygame.draw.rect(self.screen, (0, 100, 0), panel_rect) # Dark green panel
        pygame.draw.rect(self.screen, (255, 255, 255), panel_rect, 2) # White border

        # Stats
        y = 40
        line_height = 40
        
        # Title
        self._draw_text("ROAD FIGHTER", (255, 255, 0), hud_x + 20, y, size=48)
        y += 60
        
        # Score
        self._draw_text(f"SCORE: {int(core_game.score)}", COLOR_TEXT, hud_x + 20, y)
        y += line_height
        
        # Time
        time_color = (255, 255, 255)
        if core_game.time_remaining < 10: time_color = (255, 0, 0)
        self._draw_text(f"TIME: {int(core_game.time_remaining)} s", time_color, hud_x + 20, y)
        y += line_height
        
        # Speed
        if core_game.player:
            speed = int(core_game.player.velocity_y)
            self._draw_text(f"SPEED: {speed} km/h", COLOR_TEXT, hud_x + 20, y)
        y += line_height
        
        # Distance (Current / Total (Percentage%))
        dist_current = int(core_game.distance_traveled)
        dist_total = TARGET_DISTANCE
        percent = min(100, int((dist_current / dist_total) * 100))
        # Removed size=24 to use default size
        self._draw_text(f"DISTANCE: {dist_current}/{dist_total}m ({percent}%)", COLOR_TEXT, hud_x + 20, y)
        y += line_height 
        
        # Multiplier (Difficulty)
        mult = core_game._get_speed_multiplier()
        # Color scale from White (1.0) to Red (2.0)
        c_val = min(255, int((mult - 1.0) * 255))
        mult_color = (255, 255 - c_val, 255 - c_val)
        self._draw_text(f"LEVEL: x{mult:.2f}", mult_color, hud_x + 20, y)
        y += line_height * 2
        
        # Cars Passed (Bonus info)
        self._draw_text("CARS PASSED:", (200, 200, 200), hud_x + 20, y, size=24)
        y += 30
        self._draw_text(f"Green: {core_game.green_cars_passed}", COLOR_OPPONENT_GREEN, hud_x + 20, y, size=24)
        y += 25
        self._draw_text(f"Yellow: {core_game.yellow_cars_passed}", COLOR_OPPONENT_YELLOW, hud_x + 20, y, size=24)
        y += 25
        self._draw_text(f"Red: {core_game.red_cars_passed}", COLOR_OPPONENT_RED, hud_x + 20, y, size=24)

        # Alerts (Center Screen Overlays)
        if core_game.end_reason == 'collision':
            self._draw_center_text("CRASH!", (255, 0, 0))
        elif core_game.end_reason == 'timeout':
            self._draw_center_text("TIME UP!", (255, 0, 0))
        elif core_game.victory:
            self._draw_center_text("VICTORY!", (0, 255, 0))
            
        # Restart Prompt
        if core_game.game_over:
             self._draw_center_text("Press ENTER to Restart or ESC to Quit", (255, 255, 255), y_offset=80, size=30)

    def _draw_text(self, text, color, x, y, size=36):
        font = pygame.font.Font(None, size)
        surface = font.render(text, True, color)
        self.screen.blit(surface, (x, y))

    def _draw_text_with_bg(self, text, color, x, y):
        # Kept for backward compatibility if needed, but not used in new HUD
        surface = self.font.render(text, True, color)
        bg_rect = surface.get_rect(topleft=(x, y)).inflate(10, 6)
        bg_surface = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
        bg_surface.fill((0, 0, 0, 180)) 
        self.screen.blit(bg_surface, bg_rect)
        self.screen.blit(surface, (x, y))

    def _draw_center_text(self, text, color, y_offset=0, size=72):
        font_large = pygame.font.Font(None, size)
        surface = font_large.render(text, True, color)
        # Add black outline for visibility
        if size > 40: # Only outline large text
             outline = font_large.render(text, True, (0,0,0))
             rect = surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + y_offset))
             for dx, dy in [(-2,-2), (-2,2), (2,-2), (2,2)]:
                 self.screen.blit(outline, (rect.x + dx, rect.y + dy))
        else:
             rect = surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + y_offset))
             # Small bg for readability
             bg_rect = rect.inflate(20, 10)
             pygame.draw.rect(self.screen, (0,0,0), bg_rect)
             
        self.screen.blit(surface, rect)
