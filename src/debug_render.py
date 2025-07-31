# debug_render.py - Debugging für schwarzen Bildschirm
import pygame
from settings import *
from player import Player
from camera import Camera

def debug_render():
    pygame.init()
    
    # Erstelle Display
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("🔍 Render Debug")
    clock = pygame.time.Clock()
    
    # Erstelle Player direkt
    try:
        player = Player("assets/Wizard Pack", WINDOW_WIDTH//2, WINDOW_HEIGHT//2)  # Verwende WINDOW_ statt SCREEN_
        print("✅ Player erstellt")
    except:
        # Erstelle Fallback Player
        player = pygame.sprite.Sprite()
        player.image = pygame.Surface(PLAYER_SIZE)
        player.image.fill((0, 255, 0))  # Grün
        player.rect = player.image.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2))  # WINDOW_
        print("⚠️ Fallback Player erstellt")
    
    # Erstelle Kamera - für das Window, nicht die große Screen-Surface
    camera = Camera(WINDOW_WIDTH, WINDOW_HEIGHT, DEFAULT_ZOOM)
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        # DIREKT RENDERN - Ohne Level-System
        screen.fill(BACKGROUND_COLOR)
        
        # Kamera aktualisieren
        camera.update(player)
        
        # Player rendern mit Debug-Info
        if hasattr(player, 'rect'):
            # Originale Position (rot)
            pygame.draw.rect(screen, (255, 0, 0), 
                           (player.rect.x // 4, player.rect.y // 4, 20, 20))
            
            # Kamera-transformierte Position
            camera_pos = camera.apply(player)
            
            if hasattr(player, 'image'):
                screen.blit(player.image, (camera_pos.x, camera_pos.y))
            else:
                pygame.draw.rect(screen, (0, 255, 0), camera_pos)
            
            # Debug-Info
            font = pygame.font.Font(None, 24)
            info_text = [
                f"Player Pos: {player.rect.x}, {player.rect.y}",
                f"Camera Pos: {camera.camera_rect.x}, {camera.camera_rect.y}",
                f"Rendered At: {camera_pos.x}, {camera_pos.y}",
                f"Zoom: {camera.zoom_factor}x"
            ]
            
            for i, text in enumerate(info_text):
                surface = font.render(text, True, (255, 255, 255))
                screen.blit(surface, (10, 10 + i * 25))
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()

if __name__ == "__main__":
    debug_render()
