import pygame
import sys
from .core import RoadFighterGame
from .renderer import GameRenderer

def main():
    # 1. Initialize Components
    game = RoadFighterGame()
    renderer = GameRenderer()
    
    clock = pygame.time.Clock()
    running = True
    
    clock = pygame.time.Clock()
    running = True
    
    while running:
        # 2. Input Handling
        left = False
        right = False
        brake = False
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
        
        # Continuous key checks
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]: left = True
        if keys[pygame.K_RIGHT]: right = True
        if keys[pygame.K_DOWN]: brake = True
        if keys[pygame.K_UP]: 
            pass # Acceleration is automatic, but we capture the key just in case logic changes
            
        # 3. Game Logic Step
        # The core game handles physics and rules
        # We pass just the controls
        # Note: 'step' in core returns (state, reward, done, info)
        # but for human play we can call 'update' directly if we want more control,
        # or just use step and ignore ML returns.
        # Let's use 'update' directly for clarity in human loop
        
        dt = 1/60.0
        if not game.game_over:
            game.update(dt, left, right, brake)
        else:
            # Simple restart logic on key press
             if keys[pygame.K_RETURN] or keys[pygame.K_r]:
                 game.reset()
        
        # 4. Render Step
        renderer.render(game)
        
        # 5. Audio (Optional - triggered by events in future)
        # For now, simplistic check or we can add an event system later
        if game.end_reason == 'collision' and game.game_over:
            # Play crash sound only once? 
            # (Renderer handles sound loading, but maybe logic triggers it?)
            if renderer.crash_sound:
                # Basic check to avoid looping sound every frame of game over
                # (Ideally we'd have an event queue from Core to Renderer)
                pass

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
