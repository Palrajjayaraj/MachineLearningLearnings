
import pytest
import sys
import os

# Add game directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core import RoadFighterGame
from src.entities import OpponentCar
from src.constants import *

def test_reward_initially_zero():
    """
    Verify that even if the player drives fast, 
    the reward is 0.0 as long as no opponents have appeared.
    """
    game = RoadFighterGame()
    
    # Force player speed
    game.player.velocity_y = 200 # 200 km/h
    
    # Verify pre-condition
    assert game.rewards_active == False
    assert len(game.opponents) == 0
    
    # Run a few steps
    for _ in range(5):
        _, reward, _, _ = game.step(False, False, False)
        assert reward == 0.0, f"Reward should be 0.0 initially, got {reward}"
        
def test_reward_activates_with_opponent():
    """
    Verify that reward becomes non-zero once an opponent is on screen.
    """
    game = RoadFighterGame()
    game.player.velocity_y = 200 
    
    # 1. Inject an opponent visible on screen
    opp = OpponentCar(1, 0, 0) # Lane 1
    opp.y = 100 # Clearly on screen (Screen H is usually 600+)
    game.opponents.append(opp)
    
    # 2. Run step -> Should trigger 'rewards_active = True' inside update loop
    _, reward, _, _ = game.step(False, False, False)
    
    assert game.rewards_active == True, "Flag should flip to True when opponent is visible"
    assert reward > 0.0, f"Reward should be positive now, got {reward}"

def test_reward_activates_natural_spawn():
    """
    Simulate time passing until natural spawn occurs, verifying logic integration.
    """
    game = RoadFighterGame()
    game.player.velocity_y = 200
    
    # Opponents spawn every ~2.33s base.
    # We step until an opponent is added and enters screen.
    
    # Force spawn timer to be ready
    game.time_since_last_spawn = 10.0 # Over threshold
    
    # Initially 0
    _, reward, _, _ = game.step(False, False, False)
    assert reward == 0.0
    
    # Now keep stepping until opponent spawns and enters screen
    # Opponents spawn at Y = -100 (offscreen). They move DOWN relative to world? 
    # Wait, in this game:
    # Player moves UP (stationary Y, world scrolls).
    # Opponents usually move slower than player, so relative to player they move DOWN?
    # Actually logic in OpponentCar.update: 
    # y += (speed - player_speed) * dt  OR  y += speed * dt depending on implementation
    # Let's just trust that the game logic eventually puts them on screen.
    # We'll rely on the core logic: OpponentCar starts at -100 (above). 
    # If player Speed > Opponent Speed, Opponent moves DOWN relative to screen (y increases).
    # Player V = 200, Opponent V = 100 -> Relative = -100 (Approaching from top??)
    # Wait, if Player is faster, he catches up to cars in front.
    # Cars in front spawn at -100 (Top of screen).
    # If Player moves UP, existing objects move DOWN.
    # So Y increases. Yes.
    
    max_steps = 600 # 10 seconds at 60fps
    activated = False
    
    for _ in range(max_steps):
        _, reward, _, _ = game.step(False, False, False)
        if game.rewards_active:
            activated = True
            break
            
    assert activated == True, "Rewards failed to activate continuously after spawn"
    assert reward > 0.0, "Reward zero after activation"
