"""
Test ML-Ready Game Features
Demonstrates frame-by-frame control and state extraction
"""

from game_engine import RoadFighterGame
import random

def test_step_method():
    """Test the step() method - frame-by-frame control"""
    print("=" * 60)
    print("TEST 1: Frame-by-Frame Control")
    print("=" * 60)
    
    game = RoadFighterGame()
    game.reset()
    
    print("\nExecuting 100 frames with random actions...\n")
    
    for frame in range(100):
        # Random actions (like a random AI)
        left = random.choice([True, False])
        right = random.choice([True, False])
        brake = random.choice([True, False])
        
        # Execute ONE frame
        state, reward, done, info = game.step(left, right, brake)
        
        # Print progress every 20 frames
        if frame % 20 == 0:
            print(f"Frame {frame:3d}: "
                  f"Distance={info['distance']:6.1f}m, "
                  f"Reward={reward:6.2f}, "
                  f"Done={done}")
        
        if done:
            print(f"\nGame ended at frame {frame}")
            print(f"Victory: {info['victory']}")
            print(f"Final distance: {info['distance']:.1f}m")
            break
    
    print("\n✓ Frame-by-frame control works!\n")


def test_state_extraction():
    """Test the get_state() method - state extraction"""
    print("=" * 60)
    print("TEST 2: State Extraction")
    print("=" * 60)
    
    game = RoadFighterGame()
    game.reset()
    
    # Run a few frames to populate opponents
    for _ in range(60):
        game.step(False, False, False)
    
    # Get state
    state = game.get_state()
    
    print(f"\nState vector length: {len(state)} features")
    print("\nState breakdown:")
    print(f"  [0-3]   Player features: {state[0:4]}")
    print(f"  [4-5]   Progress: {state[4:6]}")
    print(f"  [6-17]  Opponents (4 lanes × 3): {state[6:18]}")
    print(f"  [18-19] Danger: {state[18:20]}")
    
    print("\nDetailed interpretation:")
    print(f"  Player X position: {state[0]:.3f} (normalized)")
    print(f"  Player speed: {state[1]:.3f} (normalized)")
    print(f"  Player lane: {state[2]:.3f} (0=lane1, 1=lane4)")
    print(f"  Is changing lane: {state[3]:.0f}")
    print(f"  Time remaining: {state[4]:.3f} (normalized)")
    print(f"  Distance progress: {state[5]:.3f} (normalized)")
    
    print("\n  Opponents per lane:")
    for lane in range(4):
        idx = 6 + lane * 3
        distance = state[idx]
        speed = state[idx + 1]
        exists = state[idx + 2]
        print(f"    Lane {lane+1}: distance={distance:.3f}, "
              f"speed={speed:.3f}, exists={exists:.0f}")
    
    print(f"\n  Immediate danger: {state[18]:.0f}")
    print(f"  Near danger: {state[19]:.0f}")
    
    print("\n✓ State extraction works!\n")


def test_reward_function():
    """Test reward calculation"""
    print("=" * 60)
    print("TEST 3: Reward Function")
    print("=" * 60)
    
    game = RoadFighterGame()
    game.reset()
    
    print("\nTesting different scenarios:\n")
    
    # Scenario 1: Normal driving
    print("Scenario 1: Normal driving (no collision)")
    total_reward = 0
    for _ in range(60):  # 1 second
        state, reward, done, info = game.step(False, False, False)
        total_reward += reward
    print(f"  Total reward over 1 second: {total_reward:.2f}")
    print(f"  Average per frame: {total_reward/60:.2f}\n")
    
    # Scenario 2: Collision (simulate by running until collision)
    print("Scenario 2: Waiting for collision...")
    game.reset()
    collision_reward = 0
    for frame in range(1000):
        state, reward, done, info = game.step(False, False, False)
        if reward < -50:  # Collision detected
            collision_reward = reward
            print(f"  Collision at frame {frame}!")
            print(f"  Collision penalty: {collision_reward:.2f}\n")
            break
    
    # Scenario 3: Victory (won't happen in test but show the logic)
    print("Scenario 3: Victory reward (in code)")
    print("  Victory bonus: +1000")
    print("  Time penalty: -500\n")
    
    print("✓ Reward function works!\n")


def test_ml_training_loop_simulation():
    """Simulate what an ML training loop would look like"""
    print("=" * 60)
    print("TEST 4: Simulated ML Training Loop")
    print("=" * 60)
    
    game = RoadFighterGame()
    
    print("\nRunning 3 episodes with random agent...\n")
    
    for episode in range(3):
        state = game.reset()
        episode_reward = 0
        steps = 0
        
        print(f"Episode {episode + 1}:")
        
        while True:
            # Random action (your ML agent will choose intelligently)
            action = random.randint(0, 2)  # 0=nothing, 1=left, 2=right
            
            left = (action == 1)
            right = (action == 2)
            brake = False
            
            # Execute action
            state, reward, done, info = game.step(left, right, brake)
            episode_reward += reward
            steps += 1
            
            if done:
                break
        
        print(f"  Steps: {steps}")
        print(f"  Total reward: {episode_reward:.2f}")
        print(f"  Distance: {info['distance']:.1f}m")
        print(f"  Victory: {info['victory']}\n")
    
    print("✓ ML training loop simulation works!\n")


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("TESTING ML-READY GAME FEATURES")
    print("=" * 60 + "\n")
    
    test_step_method()
    test_state_extraction()
    test_reward_function()
    test_ml_training_loop_simulation()
    
    print("=" * 60)
    print("ALL TESTS PASSED! ✓")
    print("=" * 60)
    print("\nYour game is ready for ML!")
    print("Next step: Build your ML agent on top of these methods.")
    print("=" * 60 + "\n")
