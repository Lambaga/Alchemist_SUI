# enhanced_main_hardware.py
# Hauptspiel mit Hardware-Integration für NFC-Tokens und LED-Feedback

import pygame
import random
from enhanced_game import EnhancedGame
from hardware_interface import HardwareInterface

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

class HardwareGameRenderer:
    """Erweiterte Renderer-Klasse mit Hardware-Feedback"""
    
    def __init__(self, screen, font, hardware_interface):
        self.screen = screen
        self.font = font
        self.small_font = pygame.font.Font(None, 36)
        self.hardware = hardware_interface
        
    def draw_background(self):
        """Zeichnet den Hintergrund"""
        self.screen.fill(BACKGROUND_COLOR)
        
        # Boden zeichnen
        pygame.draw.rect(self.screen, GROUND_COLOR, 
                        (0, SCREEN_HEIGHT - 200, SCREEN_WIDTH, 200))
        
    def draw_player(self, player):
        """Zeichnet den Spieler"""
        pygame.draw.rect(self.screen, PLAYER_COLOR, 
                        (player.x, player.y, player.width, player.height))
        
        # Spieler-"Gesicht" (zwei Punkte für Augen)
        eye_size = 6
        pygame.draw.circle(self.screen, (0, 0, 0), 
                          (player.x + 15, player.y + 20), eye_size)
        pygame.draw.circle(self.screen, (0, 0, 0), 
                          (player.x + 45, player.y + 20), eye_size)
                          
    def draw_world_zutaten(self, zutaten):
        """Zeichnet die Zutaten in der Welt"""
        for zutat in zutaten:
            if not zutat.collected:
                pygame.draw.rect(self.screen, zutat.color,
                               (zutat.x, zutat.y, zutat.width, zutat.height))
                
                # Zutat-Name anzeigen
                name_surface = self.small_font.render(zutat.name[:4], True, TEXT_COLOR)
                self.screen.blit(name_surface, (zutat.x, zutat.y - 25))
                
    def draw_ui(self, game):
        """Zeichnet die Benutzeroberfläche"""
        # UI-Hintergrund
        ui_rect = pygame.Rect(20, 20, 700, 350)
        pygame.draw.rect(self.screen, UI_BACKGROUND, ui_rect)
        pygame.draw.rect(self.screen, TEXT_COLOR, ui_rect, 3)
        
        y_offset = 40
        
        # Titel
        title = self.font.render("🧙‍♂️ Der Alchemist", True, TEXT_COLOR)
        self.screen.blit(title, (40, y_offset))
        y_offset += 50
        
        # Hardware-Status
        hw_status = "🔌 Hardware: Verbunden" if self.hardware.is_connected else "🔌 Hardware: Mock-Mode"
        hw_surface = self.small_font.render(hw_status, True, (0, 255, 0) if self.hardware.is_connected else (255, 255, 0))
        self.screen.blit(hw_surface, (40, y_offset))
        y_offset += 35
        
        # Punkte
        score_text = f"Punkte: {game.score}"
        score_surface = self.font.render(score_text, True, TEXT_COLOR)
        self.screen.blit(score_surface, (40, y_offset))
        y_offset += 40
        
        # Aktive Zutaten
        zutaten_text = f"Alchemisten-Feld ({len(game.aktive_zutaten)}/5):"
        zutaten_surface = self.font.render(zutaten_text, True, TEXT_COLOR)
        self.screen.blit(zutaten_surface, (40, y_offset))
        y_offset += 35
        
        # Zutaten-Symbole zeichnen
        start_x = 50
        for i, zutat in enumerate(game.aktive_zutaten):
            color = ZUTATEN_FARBEN.get(zutat, (200, 200, 200))
            rect_x = start_x + i * 70
            pygame.draw.rect(self.screen, color, (rect_x, y_offset, 50, 50))
            
            # Token-Symbol (NFC-Indikator)
            pygame.draw.circle(self.screen, TEXT_COLOR, (rect_x + 40, y_offset + 10), 5)
            
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
            "🎯 NFC-Tokens auf Feld legen", 
            "🔘 Brau-Button drücken",
            "R: Reset",
            "ESC: Beenden",
            "",
            "💡 Hardware-Integration:",
            "• NFC-Tokens werden automatisch erkannt",
            "• LED-Ring zeigt Spielstatus",
            "• Physischer Brau-Button verfügbar"
        ]
        
        start_y = SCREEN_HEIGHT - 350
        for i, control in enumerate(controls):
            color = TEXT_COLOR if i > 0 else (255, 255, 0)  # Gelb für Titel
            if control.startswith("💡"):
                color = (0, 255, 255)  # Cyan für Hardware-Info
            control_surface = self.small_font.render(control, True, color)
            self.screen.blit(control_surface, (SCREEN_WIDTH - 400, start_y + i * 25))

def main():
    """Hauptfunktion des Hardware-integrierten Spiels"""
    
    # Pygame initialisieren
    pygame.init()
    # Erstelle eine große Spielfläche (1920x1080)
    game_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    # Aber zeige sie in einem kleineren Fenster an
    display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Der Alchemist - Hardware Edition")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 50)
    
    # Hardware Interface initialisieren
    hardware = HardwareInterface(mock_mode=True)  # Setze auf False für echte Hardware
    hardware.connect()
    
    # Spiel und Renderer erstellen
    game = EnhancedGame()
    renderer = HardwareGameRenderer(game_surface, font, hardware)
    
    # Hardware-Callbacks registrieren
    def on_token_placed(data):
        token_name = data['token_name']
        token_id = data['token_id']
        print(f"🎯 NFC-Token erkannt: {token_name} (ID: {token_id})")
        game.add_zutat(token_name)
        hardware.set_led_effect("token_placed", "blue")
    
    def on_token_removed(data):
        token_name = data['token_name'] 
        token_id = data['token_id']
        print(f"🔄 NFC-Token entfernt: {token_name} (ID: {token_id})")
        # Hier könnte man spezifische Zutat entfernen
        hardware.set_led_effect("token_removed", "red")
    
    def on_button_pressed(data):
        button = data['button']
        print(f"🔘 Hardware-Button gedrückt: {button}")
        if button == "brew":
            result = game.brew()
            if "Heiltrank" in result or "Wasserzauber" in result or "Feuerball" in result:
                hardware.set_led_effect("success", "green")
            else:
                hardware.set_led_effect("fail", "red")
    
    hardware.register_callback("TOKEN_PLACED", on_token_placed)
    hardware.register_callback("TOKEN_REMOVED", on_token_removed)
    hardware.register_callback("BUTTON_PRESSED", on_button_pressed)
    
    # Tastaturstatus für sanfte Bewegung
    keys_pressed = {'left': False, 'right': False}
    
    print("🎮 Hardware-Edition gestartet!")
    print("🎯 Platzieren Sie NFC-Tokens auf das Alchemisten-Feld!")
    print("🔘 Drücken Sie den Brau-Button zum Brauen!")
    
    # Starteffekt
    hardware.set_led_effect("startup", "rainbow")
    
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
                    
                # Entwickler-Funktionen (simulieren Hardware)
                elif event.key == pygame.K_1:
                    hardware.simulate_token_placed("wasserkristall")
                elif event.key == pygame.K_2:
                    hardware.simulate_token_placed("feueressenz")
                elif event.key == pygame.K_3:
                    hardware.simulate_token_placed("erdkristall")
                elif event.key == pygame.K_SPACE:
                    hardware.simulate_button_press("brew")
                elif event.key == pygame.K_BACKSPACE:
                    game.remove_last_zutat()
                elif event.key == pygame.K_r:
                    game.reset_game()
                    hardware.set_led_effect("reset", "purple")
                    
            elif event.type == pygame.KEYUP:
                # Bewegung stoppen
                if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                    keys_pressed['left'] = False
                elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                    keys_pressed['right'] = False
        
        # Kontinuierliche Bewegung
        if keys_pressed['left']:
            game.player.move_left()
        if keys_pressed['right']:
            game.player.move_right()
            
        # Spiel-Update
        game.update()
        
        # Rendering auf die große Spielfläche
        renderer.draw_background()
        renderer.draw_world_zutaten(game.world_zutaten)
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
    hardware.set_led_effect("shutdown", "red")
    hardware.disconnect()
    pygame.quit()
    print(f"🏁 Hardware-Edition beendet! Endpunktzahl: {game.score}")

if __name__ == "__main__":
    main()
