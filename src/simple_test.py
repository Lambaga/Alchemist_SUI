# simple_test.py - Minimaler Test für Sichtbarkeit
import pygame
from settings import *

def simple_test():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("🔍 Einfacher Sichtbarkeitstest")
    clock = pygame.time.Clock()
    
    # Einfache Objekte
    player_rect = pygame.Rect(WINDOW_WIDTH//2 - 50, WINDOW_HEIGHT//2 - 50, 100, 100)
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
        
        # Bewegung mit Pfeiltasten
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]: player_rect.x -= 5
        if keys[pygame.K_RIGHT]: player_rect.x += 5
        if keys[pygame.K_UP]: player_rect.y -= 5
        if keys[pygame.K_DOWN]: player_rect.y += 5
        
        # Rendering - SEHR einfach
        screen.fill((50, 50, 100))  # Dunkelblaues Background
        
        # Heller grüner Player
        pygame.draw.rect(screen, (0, 255, 0), player_rect)
        
        # Weißer Rahmen
        pygame.draw.rect(screen, (255, 255, 255), player_rect, 3)
        
        # Info-Text
        font = pygame.font.Font(None, 36)
        text = font.render("Pfeiltasten = Bewegung, ESC = Beenden", True, (255, 255, 255))
        screen.blit(text, (10, 10))
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()

if __name__ == "__main__":
    simple_test()
