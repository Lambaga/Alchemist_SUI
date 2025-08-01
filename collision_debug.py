import pygame
import sys
import os

# Initialize pygame
pygame.init()

# Add src to path
sys.path.append('src')
from level import Level
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, WINDOW_WIDTH, WINDOW_HEIGHT

# Create surfaces
game_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Collision Debug - F1 to toggle debug boxes")

# Create level
level = Level(game_surface)

print("=== COLLISION DIAGNOSTIC ===")
print(f"Player position: ({level.game_logic.player.rect.centerx}, {level.game_logic.player.rect.centery})")
print(f"Player hitbox: {level.game_logic.player.hitbox}")
print(f"Total collision objects: {len(level.map_loader.collision_objects) if level.map_loader else 0}")

# Show first few collision objects
if level.map_loader and level.map_loader.collision_objects:
    print("\nFirst 10 collision objects:")
    for i, rect in enumerate(level.map_loader.collision_objects[:10]):
        print(f"  {i+1}: {rect}")

# Game loop
clock = pygame.time.Clock()
running = True

print("\n🎮 Use WASD to move")
print("🔍 Press F1 to toggle collision debug boxes")
print("📦 Red = Player hitbox, Cyan = Collision objects")
print("Press ESC to exit")

while running:
    dt = clock.tick(60) / 1000.0
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
        level.handle_input(event)
    
    # Update and render
    level.update(dt)
    level.render()
    
    # Scale and display
    scaled_surface = pygame.transform.scale(game_surface, (WINDOW_WIDTH, WINDOW_HEIGHT))
    display_surface.blit(scaled_surface, (0, 0))
    
    # Show debug info
    font = pygame.font.Font(None, 36)
    player_pos = f"Player: ({level.game_logic.player.rect.centerx}, {level.game_logic.player.rect.centery})"
    camera_pos = f"Camera: ({level.camera.camera_rect.x:.0f}, {level.camera.camera_rect.y:.0f})"
    debug_text = f"{player_pos} | {camera_pos}"
    if level.show_collision_debug:
        debug_text += " | DEBUG: ON"
    
    text = font.render(debug_text, True, (255, 255, 0))
    display_surface.blit(text, (10, 10))
    
    pygame.display.flip()

pygame.quit()
