# -*- coding: utf-8 -*-
"""
Minimal Test - Direkter Tastatur-Test für Magie
"""

import pygame
import sys
import os

# Pygame initialisieren
pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Magie Test - Drücke F/W/S/C/X oder ESC zum Beenden")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 36)

# Test-Status
test_messages = []

def add_message(msg):
    """Fügt eine Nachricht zum Log hinzu"""
    test_messages.append(msg)
    print(msg)
    if len(test_messages) > 10:
        test_messages.pop(0)

def main():
    running = True
    add_message("🎮 Magie-Test gestartet!")
    add_message("F = Feuer, W = Wasser, S = Stein")  
    add_message("C = Zaubern, X = Löschen, ESC = Beenden")
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_f:
                    add_message("🔥 F-Taste: Feuer-Element!")
                elif event.key == pygame.K_w:
                    add_message("💧 W-Taste: Wasser-Element!")
                elif event.key == pygame.K_s:
                    add_message("🗿 S-Taste: Stein-Element!")
                elif event.key == pygame.K_c:
                    add_message("✨ C-Taste: Zaubern!")
                elif event.key == pygame.K_x:
                    add_message("🧹 X-Taste: Elemente löschen!")
                elif event.key == pygame.K_h:
                    add_message("💚 H-Taste: Direktheilung Test!")
                else:
                    add_message(f"❓ Unbekannte Taste: {pygame.key.name(event.key)}")
        
        # Bildschirm zeichnen
        screen.fill((20, 20, 40))
        
        # Nachrichten zeichnen
        y_offset = 50
        for msg in test_messages:
            text_surface = font.render(msg, True, (255, 255, 255))
            screen.blit(text_surface, (20, y_offset))
            y_offset += 40
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()

if __name__ == "__main__":
    main()
