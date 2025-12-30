Road Fighter - Requirements Specification
=======================================

1. Core Gameplay Rules
----------------------
*   **Goal**: Reach the finish line (9500m) within the time limit (120s).
*   **Failure Conditions**:
    *   **Failure Conditions**:
    *   Running out of time.
    *   Crashing into an opponent car.
*   **Controls**:
    *   **Left/Right Arrows**: Steer player car.
    *   **Down Arrow**: Brake (Decelerate).
    *   **No Input**: Auto-accelerate to max speed (300 km/h).
    *   **Enter**: Restart game (on Game Over).
    *   **Esc**: Quit game (on Game Over).

2. Opponent Logic
-----------------
*   **Car Types & Ratios**:
    *   Ratio 5:3:2 (Green:Yellow:Red).
    *   **Green**: Moves straight.
    *   **Yellow**: Zig-zags between 2 adjacent lanes. Horizontal Speed: ~100px/s (Base).
    *   **Red**: Zig-zags across all 4 lanes (bounces off edges). Horizontal Speed: ~70px/s (Base).
*   **Spawning Constraints**:
    *   **Vertical Spacing**: Min 180px gap between cars.
    *   **Diversity**: Max 2 consecutive cars of the same color.
    *   **Congestion**: Max 2 consecutive cars in the same lane.
    *   **Red Car Spacing**: Consecutive Red cars must be separated by at least 2 lanes.
*   **Anti-Camping**:
    *   If player passes 2 cars in the same lane without moving, the next spawn is forced into the player's lane.

3. Difficulty Progression
-------------------------
Speed multiplier increases based on **Elapsed Time**.
This multiplier affects Opponent Speed (Vertical) and Zig-Zag Speed (Horizontal).

*   **0-30s**: 1.0x (Normal)
*   **30-46s**: 1.2x
*   **46-60s**: 1.4x
*   **60-80s**: 1.6x
*   **80-100s**: 1.8x
*   **100s+**: 2.0x (Max)

4. Scoring System
-----------------
*   **Score Accumulation**: Points are awarded for distance traveled.
*   **Multiplier Bonus**: Points per meter are scaled by the current Difficulty Multiplier.
    *   *Formula*: `Score += (Distance_Delta * 10 * Multiplier)`
*   **Passing Bonus**: Extra points for safely overtaking cars.

5. Visuals & UI (HUD)
---------------------
*   **Player Color**: Dark Blue.
*   **HUD Location**: Right-side green panel.
*   **Displayed Metrics**:
    *   **SCORE**: Current score.
    *   **TIME**: Remaining time (Unit: `s`, e.g., "60 s").
    *   **SPEED**: Current speed (Unit: `km/h`).
    *   **DISTANCE**: Progress (Format: `Current/Total m (Percent%)`).
    *   **LEVEL**: Current Multiplier (e.g., "x1.20").
*   **Feedback**:
    *   Red/Yellow cars must have functional **Blinkers** indicating movement direction.
    *   Game Over screen must display "Press ENTER to Restart or ESC to Quit".

6. Physics Simulation
---------------------
*   **Velocity**: Handled internally in `m/s` derived from `km/h` (Vel / 3.6).
*   **Duration**: A perfect run (Max speed 300km/h constant) should take approxiately **114 seconds**.

7. AI / ML Interface
--------------------
The game provides a Gymnasium Environment (`src.gym_env.RacingGameEnv`) for Reinforcement Learning.

*   **Configuration**:
    *   `frame_skip`: (int) Default 4. Number of physics frames to advance per action.

*   **Observation Space**: Box(32,) - A vector of 32 normalized continuous values.
    1.  **Player (4)**: `[X, Vel_Y, Lane, is_Changing]`
    2.  **Global (3)**: `[Time, Progress, Multiplier]`
    3.  **Neighbors (5x5)**: The 5 nearest cars, each with:
        *   `Relative X` (Distance normalized to screen width)
        *   `Relative Y` (Distance normalized to screen height)
        *   `Type ID` (0.0=Green, 0.5=Yellow, 1.0=Red)
        *   `Velocity X` (Direction: -1=Left, 0=Straight, 1=Right)
        *   `Relative Velocity Y` (Closing Speed: +ve = Approaching fast)

*   **Action Space**: Discrete(4)
    *   0: Do Nothing
    *   1: Steer Left
    *   2: Steer Right
    *   3: Brake
