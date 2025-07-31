# main_simple.py - Vereinfachtes Spiel ohne Level-System
import pygame
import sys
from settings import *
from player import Player
from camera import Camera

def main_simple():
    # Pygame setup
    pygame.init()
    pygame.mixer.init()
    
    # Display - DIREKT auf window_size, keine game_surface!
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption(GAME_TITLE)
    clock = pygame.time.Clock()
    
    # Player direkt erstellen
    player = Player("assets/Wizard Pack", WINDOW_WIDTH//2, WINDOW_HEIGHT//2)
    
    # Kamera für das direkte Window
    camera = Camera(WINDOW_WIDTH, WINDOW_HEIGHT, DEFAULT_ZOOM)
    
    print("🎮 Vereinfachtes Spiel gestartet!")
    print("🎯 WASD/Pfeiltasten = Bewegung, ESC = Beenden")
    
    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        
        # Events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
        
        # Input - Vector2 basiert wie in optimierter Player-Klasse
        keys = pygame.key.get_pressed()
        direction = pygame.math.Vector2(0, 0)
        
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: direction.x = -1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: direction.x = 1
        if keys[pygame.K_UP] or keys[pygame.K_w]: direction.y = -1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]: direction.y = 1
        
        # Player aktualisieren
        player.set_direction(direction)
        player.move(dt)
        player.update(dt)
        
        # Kamera aktualisieren
        camera.update(player)
        
        # Rendering - DIREKT auf screen
        screen.fill(BACKGROUND_COLOR)
        
        # Player rendern
        if hasattr(player, 'image') and player.image:
            player_pos = camera.apply(player)
            # Korrekte Skalierung
            scaled_image = pygame.transform.scale(player.image, (player_pos.width, player_pos.height))
            screen.blit(scaled_image, (player_pos.x, player_pos.y))
        else:
            # Fallback
            player_pos = camera.apply(player)
            pygame.draw.rect(screen, (0, 255, 0), player_pos)
        
        # Debug-Info
        if DEBUG_MODE:
            font = pygame.font.Font(None, 24)
            info = [
                f"FPS: {int(clock.get_fps())}",
                f"Player: {int(player.rect.x)}, {int(player.rect.y)}",
                f"Camera: {int(camera.camera_rect.x)}, {int(camera.camera_rect.y)}",
                f"Zoom: {camera.zoom_factor:.1f}x"
            ]
            for i, text in enumerate(info):
                surface = font.render(text, True, (255, 255, 255))
                screen.blit(surface, (10, 10 + i * 25))
        
        pygame.display.flip()
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main_simple()
