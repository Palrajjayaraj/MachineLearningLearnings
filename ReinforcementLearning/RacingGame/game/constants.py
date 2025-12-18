"""
Road Fighter - Game Constants
"""

# Screen
SCREEN_WIDTH = 1100  # Expanded to show full HUD on right side with extra buffer
SCREEN_HEIGHT = 800  # Increased for better vertical fit
FPS = 60

# Road
NUM_LANES = 4
LANE_WIDTH = 100
ROAD_LEFT_EDGE = 150
ROAD_RIGHT_EDGE = 550
ROAD_WIDTH = ROAD_RIGHT_EDGE - ROAD_LEFT_EDGE

# Lane centers
LANE_CENTERS = [
    ROAD_LEFT_EDGE + LANE_WIDTH // 2,
    ROAD_LEFT_EDGE + LANE_WIDTH + LANE_WIDTH // 2,
    ROAD_LEFT_EDGE + 2 * LANE_WIDTH + LANE_WIDTH // 2,
    ROAD_LEFT_EDGE + 3 * LANE_WIDTH + LANE_WIDTH // 2
]

# Player car dimensions (define before using in PLAYER_START_X)
PLAYER_WIDTH = 60
PLAYER_HEIGHT = 100

# Player car position (centered in lane, positioned at bottom with 0.5 car height gap)
PLAYER_START_X = LANE_CENTERS[1] - PLAYER_WIDTH // 2  # Center the car in lane
PLAYER_Y = SCREEN_HEIGHT - PLAYER_HEIGHT - 50  # 50px gap = 0.5 car height from bottom
PLAYER_BASE_SPEED = 150.0
PLAYER_MAX_SPEED = 300.0
PLAYER_MIN_SPEED = 50.0
PLAYER_ACCELERATION = 250.0
PLAYER_BRAKE_FORCE = 400.0

# Racing
RACE_TIME_LIMIT = 120.0
TARGET_DISTANCE = 9500.0

# Opponent cars
OPPONENT_WIDTH = 60
OPPONENT_HEIGHT = 100
OPPONENT_SPEED = 180.0
OPPONENT_MIN_SPACING = 250.0  # Min check. Target: 280px spacing = 180px gap (1.8 car lengths)

# Spawn probabilities (5:3:2 ratio - Green:Yellow:Red)
GREEN_CAR_PROBABILITY = 0.500
YELLOW_CAR_PROBABILITY = 0.300
RED_CAR_PROBABILITY = 0.200

# Visual
LANE_MARKER_HEIGHT = 40
LANE_MARKER_GAP = 20

# Colors (RGB)
COLOR_ROAD = (45, 45, 45)
COLOR_GRASS = (34, 139, 34)
COLOR_LANE_MARKER = (255, 255, 255)
COLOR_ROAD_EDGE = (255, 255, 0)
COLOR_PLAYER = (255, 0, 0)
COLOR_OPPONENT_GREEN = (0, 255, 0)
COLOR_OPPONENT_YELLOW = (255, 255, 0)
COLOR_OPPONENT_RED = (255, 100, 100)
