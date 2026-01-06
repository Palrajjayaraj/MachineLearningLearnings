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

## Play the Game (Human)

```bash
python play.py
```

**Controls:**
- LEFT/RIGHT arrows: Move half-lane left/right
- DOWN arrow: Brake
- Car accelerates automatically to 400 km/h

**Goal:** Reach 9500m in 120 seconds

---

## 🤖 AI / Reinforcement Learning

This game is designed to train an Autonomous Agent using PPO (Proximal Policy Optimization).

### 1. Training
To train the agent (headless mode):
```bash
python train.py
```
*Note: The visualization window will pop up periodically (every 10k steps) to show progress.*

### 2. Visualization
To watch the trained model play:
```bash
python play_model.py
```

### 3. Rewards & Costs (The "Price List")
The agent is trained using the following incentive structure:

| Event | Reward | Reason |
| :--- | :--- | :--- |
| **Move Forward** | `+0.1` to `+0.3` / frame | Encourages speed and distance coverage. |
| **Overtake Car** | `+2.0` / car | 🍬 **Sugar Hit**: Strong incentive to pass traffic actively. |
| **VICTORY** | `+100.0` | 🏆 **Jackpot**: Reaching the finish line. |
| **CRASH** | `-100.0` | 🔨 **Death**: Massive penalty ensures survival is #1 priority. |
| **Lane Camping** | `-0.5` / frame | ⛺ Punishment for exploiting safe lanes without moving. |
| **Lane Change** | `-0.05` / action | ↔️  Minor tax to prevent jittery/shaky steering. |

### 4. Input (Observation Space)
The AI sees a Normalize Vector of **32 numbers** (State V3):
- **Self**: X Position, Speed, Current Lane, Changing Lane Flag.
- **Global**: Time Remaining, Distance Required, Difficulty Multiplier.
- **Opponents**: For the nearest 5 cars: [Relative X, Relative Y, Car Type, Direction, Relative Speed].

### 5. Output (Action Space)
Discrete Actions:
- `0`: Do Nothing
- `1`: Move Left
- `2`: Move Right
- `3`: Brake

---

## Run Tests
To run all tests (includes logic, ML integration, and game rules):
```bash
python -m unittest discover tests
```

## Code Structure

The game is organized into the `src/` package:

1. **src/constants.py** - Configuration
2. **src/entities.py** - Game objects (`PlayerCar`, `OpponentCar`)
3. **src/core.py** - Logic (`RoadFighterGame` class)
4. **src/renderer.py** - Visuals (`GameRenderer` class)
5. **src/gym_env.py** - RL Interface
