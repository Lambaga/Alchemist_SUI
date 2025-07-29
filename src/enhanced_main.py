# enhanced_main.py
# Hauptspiel mit Spieler-Bewegung und vollständiger Steuerung

import pygame
import random
from enhanced_game import EnhancedGame

# --- Konstanten ---
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
WINDOW_WIDTH = 1280   # Kleinere Anzeige
WINDOW_HEIGHT = 720   # Kleinere Anzeige
FPS = 60

# Farben
BACKGROUND_COLOR = (25, 25, 50)      # Dunkelblau
TEXT_COLOR = (255, 255, 255)         # Weiß
PLAYER_COLOR = (100, 255, 100)       # Hellgrün
GROUND_COLOR = (139, 69, 19)         # Braun
UI_BACKGROUND = (50, 50, 80)         # Dunkelblau-Grau

# Zutaten-Farben
ZUTATEN_FARBEN = {
    "wasserkristall": (0, 150, 255),    # Blau
    "feueressenz": (255, 100, 0),       # Orange
    "erdkristall": (139, 69, 19)        # Braun
}

class GameRenderer:
    """Klasse für das Rendering des Spiels"""
    
    def __init__(self, screen, font):
        self.screen = screen
        self.font = font
        self.small_font = pygame.font.Font(None, 36)
        
    def draw_background(self):
        """Zeichnet den Hintergrund"""
        self.screen.fill(BACKGROUND_COLOR)
        
        # Boden zeichnen
        pygame.draw.rect(self.screen, GROUND_COLOR, 
                        (0, SCREEN_HEIGHT - 200, SCREEN_WIDTH, 200))
        
    def draw_player(self, player):
        """Zeichnet den animierten Spieler"""
        if hasattr(player, 'image') and player.image:
            # Zeichne das animierte Sprite
            self.screen.blit(player.image, player.rect)
        else:
            # Fallback: Zeichne als Rechteck falls keine Animation vorhanden
            pygame.draw.rect(self.screen, PLAYER_COLOR, 
                            (player.x, player.y, player.width, player.height))
            
            # Spieler-"Gesicht" (zwei Punkte für Augen)
            eye_size = 6
            pygame.draw.circle(self.screen, (0, 0, 0), 
                              (player.x + 15, player.y + 20), eye_size)
            pygame.draw.circle(self.screen, (0, 0, 0), 
                              (player.x + 45, player.y + 20), eye_size)
                          
    def draw_ui(self, game):
        """Zeichnet die Benutzeroberfläche"""
        # UI-Hintergrund
        ui_rect = pygame.Rect(20, 20, 600, 250)
        pygame.draw.rect(self.screen, UI_BACKGROUND, ui_rect)
        pygame.draw.rect(self.screen, TEXT_COLOR, ui_rect, 3)
        
        y_offset = 40
        
        # Titel
        title = self.font.render("🧙‍♂️ Der Alchemist", True, TEXT_COLOR)
        self.screen.blit(title, (40, y_offset))
        y_offset += 50
        
        # Punkte
        score_text = f"Punkte: {game.score}"
        score_surface = self.font.render(score_text, True, TEXT_COLOR)
        self.screen.blit(score_surface, (40, y_offset))
        y_offset += 40
        
        # Aktive Zutaten
        zutaten_text = f"Inventar ({len(game.aktive_zutaten)}/5):"
        zutaten_surface = self.font.render(zutaten_text, True, TEXT_COLOR)
        self.screen.blit(zutaten_surface, (40, y_offset))
        y_offset += 35
        
        # Zutaten-Symbole zeichnen
        start_x = 50
        for i, zutat in enumerate(game.aktive_zutaten):
            color = ZUTATEN_FARBEN.get(zutat, (200, 200, 200))
            rect_x = start_x + i * 70
            pygame.draw.rect(self.screen, color, (rect_x, y_offset, 50, 50))
            
        y_offset += 70
        
        # Letztes Brau-Ergebnis
        result_lines = game.last_brew_result.split('\n')
        for line in result_lines:
            if line.strip():
                result_surface = self.small_font.render(line, True, TEXT_COLOR)
                self.screen.blit(result_surface, (40, y_offset))
                y_offset += 30
                
    def draw_controls(self):
        """Zeichnet die Steuerungshinweise"""
        controls = [
            "🎮 STEUERUNG:",
            "← → Bewegung",
            "1,2,3 Zutaten sammeln", 
            "Leertaste: Brauen",
            "Backspace: Zutat entfernen",
            "R: Reset",
            "ESC: Beenden"
        ]
        
        start_y = SCREEN_HEIGHT - 250
        for i, control in enumerate(controls):
            color = TEXT_COLOR if i > 0 else (255, 255, 0)  # Gelb für Titel
            control_surface = self.small_font.render(control, True, color)
            self.screen.blit(control_surface, (SCREEN_WIDTH - 300, start_y + i * 30))

def main():
    """Hauptfunktion des erweiterten Spiels"""
    
    # Pygame initialisieren
    pygame.init()
    # Erstelle eine große Spielfläche (1920x1080)
    game_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    # Aber zeige sie in einem kleineren Fenster an
    display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Der Alchemist - Erweiterte Version")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 50)
    
    # Spiel und Renderer erstellen
    game = EnhancedGame()
    renderer = GameRenderer(game_surface, font)
    
    # Tastaturstatus für sanfte Bewegung
    keys_pressed = {'left': False, 'right': False}
    
    print("🎮 Erweiterte Version gestartet!")
    print("Verwenden Sie die Pfeiltasten oder A/D für Bewegung!")
    
    # Hauptspiel-Schleife
    running = True
    while running:
        
        # Event-Handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
            elif event.type == pygame.KEYDOWN:
                # Beenden
                if event.key == pygame.K_ESCAPE:
                    running = False
                    
                # Bewegung starten
                elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                    keys_pressed['left'] = True
                elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                    keys_pressed['right'] = True
                    
                # Zutaten manuell hinzufügen (für Test)
                elif event.key == pygame.K_1:
                    game.add_zutat("wasserkristall")
                elif event.key == pygame.K_2:
                    game.add_zutat("feueressenz") 
                elif event.key == pygame.K_3:
                    game.add_zutat("erdkristall")
                    
                # Zutat entfernen
                elif event.key == pygame.K_BACKSPACE:
                    game.remove_last_zutat()
                    
                # Brauen
                elif event.key == pygame.K_SPACE:
                    game.brew()
                    
                # Reset
                elif event.key == pygame.K_r:
                    game.reset_game()
                    
            elif event.type == pygame.KEYUP:
                # Bewegung stoppen
                if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                    keys_pressed['left'] = False
                elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                    keys_pressed['right'] = False
        
        # Kontinuierliche Bewegung
        is_moving = False
        if keys_pressed['left']:
            game.player.move_left()
            is_moving = True
        if keys_pressed['right']:
            game.player.move_right()
            is_moving = True
            
        # Stoppe Bewegung wenn keine Taste gedrückt
        if not is_moving:
            game.player.stop_moving()
            
        # Spiel-Update
        game.update()
        
        # Rendering auf die große Spielfläche
        renderer.draw_background()
        renderer.draw_player(game.player)
        renderer.draw_ui(game)
        renderer.draw_controls()
        
        # Skaliere die große Spielfläche auf das kleinere Fenster
        scaled_surface = pygame.transform.scale(game_surface, (WINDOW_WIDTH, WINDOW_HEIGHT))
        display_surface.blit(scaled_surface, (0, 0))
        
        # Bildschirm aktualisieren
        pygame.display.flip()
        clock.tick(FPS)
    
    # Spiel beenden
    pygame.quit()
    print(f"🏁 Spiel beendet! Endpunktzahl: {game.score}")

if __name__ == "__main__":
    main()
