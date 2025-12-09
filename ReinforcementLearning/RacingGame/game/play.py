"""
Road Fighter - Play the game
"""

from game_engine import RoadFighterGame


if __name__ == '__main__':
    print("=" * 60)
    print("ROAD FIGHTER")
    print("=" * 60)
    print("\nControls:")
    print("  LEFT ARROW  - Move half-lane left")
    print("  RIGHT ARROW - Move half-lane right")
    print("  DOWN ARROW  - Brake")
    print("  (Car accelerates automatically)")
    print("\nGoal:")
    print("  Reach 9500m in 120 seconds!")
    print("=" * 60)
    
    game = RoadFighterGame()
    game.run()
