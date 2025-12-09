# Road Fighter - Python Game

A Python port of the Road Fighter racing game.

## Files

- `constants.py` - All game constants (screen size, physics, colors, etc.)
- `entities.py` - PlayerCar and OpponentCar classes
- `game_engine.py` - Main game loop and logic
- `play.py` - Run to play the game

## Setup

```bash
pip install -r requirements.txt
```

## Play the Game

```bash
python play.py
```

**Controls:**
- LEFT/RIGHT arrows: Move half-lane left/right
- DOWN arrow: Brake
- Car accelerates automatically

**Goal:** Reach 3500m in 120 seconds

## Game Mechanics

### Player Car
- Starts at 150 km/h
- Auto-accelerates to 300 km/h max
- Can brake down to 50 km/h min
- Moves in half-lane increments
- Slows down on collision

### Opponent Cars
- Travel at 180 km/h
- Spawn in random lanes
- Three colors (green, yellow, red)
- Spawn rate increases with distance

### Winning
- Reach 3500m before time runs out
- Avoid collisions to maintain speed

## Code Structure

The game is organized into:

1. **constants.py** - Configuration
   - Screen dimensions
   - Physics parameters
   - Colors
   - Game rules

2. **entities.py** - Game objects
   - `PlayerCar` - Player-controlled car with lane changing
   - `OpponentCar` - AI traffic cars

3. **game_engine.py** - Game logic
   - `RoadFighterGame` - Main game class
   - Update loop
   - Collision detection
   - Spawning system
   - Rendering

4. **play.py** - Entry point
   - Creates and runs the game

## Game State

The game tracks:
- Player position, speed, lane
- Opponent positions and states
- Distance traveled
- Time remaining
- Score
- Collision detection

You can access these from `game_engine.py` for building ML on top of this.

## Next Steps

Now you can build your own ML solution on top of this game! The game provides all the mechanics - you add the intelligence.
