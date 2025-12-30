# Road Fighter - Python Game

A Python port of the Road Fighter racing game.

## Files

- `src/constants.py` - All game constants (screen size, physics, colors, etc.)
- `src/entities.py` - PlayerCar and OpponentCar classes
- `src/core.py` - Main game logic (headless)
- `src/renderer.py` - Pygame rendering
- `src/main.py` - Launcher for human play
- `src/gym_env.py` - Gymnasium wrapper for RL

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

**Goal:** Reach 9500m in 120 seconds

## Run Tests
To run all tests (includes logic, ML integration, and game rules):
```bash
python -m unittest discover tests
```

To see the **list of individual tests** being run (Verbose mode):
```bash
python -m unittest discover tests -v
```

## ML Training

To use the environment in your training script:

```python
from src.gym_env import RacingGameEnv

env = RacingGameEnv()
# ... training loop ...
```

## Code Structure

The game is organized into the `src/` package:

1. **src/constants.py** - Configuration
2. **src/entities.py** - Game objects (`PlayerCar`, `OpponentCar`)
3. **src/core.py** - Logic (`RoadFighterGame` class)
4. **src/renderer.py** - Visuals (`GameRenderer` class)
5. **src/gym_env.py** - RL Interface

## Game State

The game tracks:
- Player position, speed, lane
- Opponent positions and states
- Distance traveled
- Time remaining
- Score
- Collision detection

You can access these from `src/core.py` for building ML on top of this.
