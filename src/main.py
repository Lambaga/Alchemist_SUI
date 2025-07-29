# src/main.py
import pygame
import random
import os
from game import Game
from camera import Camera # Kamera-Klasse importieren
from map_loader import MapLoader # Map-Loader hinzufügen
from config import WindowConfig, Colors, Paths

# --- Konstanten und Konfiguration ---
SCREEN_WIDTH = WindowConfig.SCREEN_WIDTH
SCREEN_HEIGHT = WindowConfig.SCREEN_HEIGHT
WINDOW_WIDTH = WindowConfig.WINDOW_WIDTH
WINDOW_HEIGHT = WindowConfig.WINDOW_HEIGHT
FPS = WindowConfig.FPS

# Farben werden jetzt aus config.py importiert
GROUND_COLOR = (139, 69, 19)         # Braun
UI_BACKGROUND = (50, 50, 80)         # Dunkelblau-Grau
SKY_COLOR = (135, 206, 235)          # Hellblau für den Himmel
TREE_COLOR = (34, 139, 34)           # Dunkelgrün für die "Bäume"

# Zutaten-Farben
ZUTATEN_FARBEN = {
    "wasserkristall": (0, 150, 255),    # Blau
    "feueressenz": (255, 100, 0),       # Orange
    "erdkristall": (139, 69, 19)        # Braun
}

# Position des Bodens
GROUND_Y_POSITION = SCREEN_HEIGHT - 200 # Wo der Boden beginnt

class GameRenderer:
    """Klasse für das Rendering des Spiels"""
    
    def __init__(self, screen, font):
        self.screen = screen
        self.font = font
        self.small_font = pygame.font.Font(None, 36)
        
        # Generiere zufällige Steine für den Boden
        self.generate_ground_stones()
        
    def generate_ground_stones(self):
        """Generiert zufällige Steine für den Boden"""
        self.stones = []
        # Erstelle Steine über eine große Breite (viel größer als Bildschirm)
        world_width = SCREEN_WIDTH * 3  # 3x so breit wie der Bildschirm
        
        for _ in range(200):  # 200 Steine
            x = random.randint(-world_width // 2, world_width // 2)
            y = random.randint(GROUND_Y_POSITION + 10, GROUND_Y_POSITION + 180)
            size = random.randint(3, 12)  # Verschiedene Größen
            # Verschiedene Grautöne für die Steine
            gray = random.randint(80, 140)
            color = (gray, gray, gray)
            
            self.stones.append({
                'x': x,
                'y': y, 
                'size': size,
                'color': color
            })
        
    def draw_background(self, map_loader=None, camera=None):
        """Zeichnet den Hintergrund - entweder die Map oder den Standard-Hintergrund"""
        if map_loader and camera and map_loader.tmx_data:
            # Zunächst einen Hintergrund zeichnen, falls die Map Löcher hat
            self.screen.fill((50, 50, 50))  # Dunkelgrauer Hintergrund
            # Zeichne die TMX-Map
            map_loader.render(self.screen, camera)
        else:
            # Fallback: Standard-Hintergrund
            self.screen.fill(Colors.BACKGROUND_BLUE)
            
            # "Bäume"-Schicht
            tree_rect = pygame.Rect(0, GROUND_Y_POSITION - 200, SCREEN_WIDTH, 200)
            pygame.draw.rect(self.screen, TREE_COLOR, tree_rect)

            # "Boden"-Schicht
            ground_rect = pygame.Rect(0, GROUND_Y_POSITION, SCREEN_WIDTH, 200)
            pygame.draw.rect(self.screen, GROUND_COLOR, ground_rect)
        
    def draw_ground_stones(self, camera):
        """Zeichnet die Steine am Boden durch die Kamera"""
        for stone in self.stones:
            # Erstelle ein temporäres Objekt für die Kamera-Transformation
            stone_rect = pygame.Rect(stone['x'], stone['y'], stone['size'], stone['size'])
            stone_pos = camera.apply_rect(stone_rect)
            
            # Zeichne nur Steine, die im sichtbaren Bereich sind
            if -50 < stone_pos.x < SCREEN_WIDTH + 50:
                pygame.draw.circle(self.screen, stone['color'], 
                                 (stone_pos.x + stone['size']//2, stone_pos.y + stone['size']//2), 
                                 stone['size']//2)
        
    def draw_player(self, player, camera):
        """Zeichnet den animierten Spieler mit Kamera"""
        if hasattr(player, 'image') and player.image:
            # Zeichne das animierte Sprite durch die Kamera
            self.screen.blit(player.image, camera.apply(player))
        else:
            # Fallback: Zeichne als Rechteck falls keine Animation vorhanden
            player_pos = camera.apply(player)
            pygame.draw.rect(self.screen, Colors.PLAYER_GREEN, 
                            (player_pos.x, player_pos.y, player.width, player.height))
            
            # Spieler-"Gesicht" (zwei Punkte für Augen)
            eye_size = 6
            pygame.draw.circle(self.screen, (0, 0, 0), 
                              (player_pos.x + 15, player_pos.y + 20), eye_size)
            pygame.draw.circle(self.screen, (0, 0, 0), 
                              (player_pos.x + 45, player_pos.y + 20), eye_size)
                          
    def draw_ui(self, game):
        """Zeichnet die Benutzeroberfläche"""
        # UI-Hintergrund
        ui_rect = pygame.Rect(20, 20, 600, 250)
        pygame.draw.rect(self.screen, UI_BACKGROUND, ui_rect)
        pygame.draw.rect(self.screen, Colors.WHITE, ui_rect, 3)
        
        y_offset = 40
        
        # Titel
        title = self.font.render("🧙‍♂️ Der Alchemist", True, Colors.WHITE)
        self.screen.blit(title, (40, y_offset))
        y_offset += 50
        
        # Punkte
        score_text = f"Punkte: {game.score}"
        score_surface = self.font.render(score_text, True, Colors.WHITE)
        self.screen.blit(score_surface, (40, y_offset))
        y_offset += 40
        
        # Aktive Zutaten
        zutaten_text = f"Inventar ({len(game.aktive_zutaten)}/5):"
        zutaten_surface = self.font.render(zutaten_text, True, Colors.WHITE)
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
                result_surface = self.small_font.render(line, True, Colors.WHITE)
                self.screen.blit(result_surface, (40, y_offset))
                y_offset += 30
                
    def draw_controls(self):
        """Zeichnet die Steuerungshinweise"""
        controls = [
            "🎮 STEUERUNG:",
            "← → ↑ ↓ / WASD Bewegung",
            "1,2,3 Zutaten sammeln", 
            "Leertaste: Brauen",
            "Backspace: Zutat entfernen",
            "R: Reset",
            "M: Musik ein/aus",
            "ESC: Beenden"
        ]
        
        start_y = SCREEN_HEIGHT - 250
        for i, control in enumerate(controls):
            color = Colors.WHITE if i > 0 else Colors.YELLOW  # Gelb für Titel
            control_surface = self.small_font.render(control, True, color)
            self.screen.blit(control_surface, (SCREEN_WIDTH - 300, start_y + i * 30))

def main():
    """Hauptfunktion des Spiels mit Kamera und erweiterten Features"""
    
    # --- Initialisierung ---
    pygame.init()
    pygame.mixer.init()  # Musik-System initialisieren
    
    # --- Hintergrundmusik laden und starten ---
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        music_path = os.path.join(project_root, Paths.MUSIC_KOROL)
        
        pygame.mixer.music.load(music_path)
        pygame.mixer.music.set_volume(0.7)  # Lautstärke auf 70%
        pygame.mixer.music.play(-1)  # -1 = Endlos-Schleife
        print(f"🎵 Hintergrundmusik gestartet: {music_path}")
    except Exception as e:
        print(f"⚠️ Musik konnte nicht geladen werden: {e}")
    
    # Erstelle eine große Spielfläche (1920x1080)
    game_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    # Aber zeige sie in einem kleineren Fenster an
    display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Der Alchemist - Mit Kamera")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 50)

    # --- Spiel-Instanz erstellen ---
    game = Game()
    renderer = GameRenderer(game_surface, font)
    
    # Map-Loader erstellen und Map laden
    # Robuster Pfad zur Map-Datei, der vom Speicherort des Skripts ausgeht
    try:
        # __file__ ist der Pfad zum aktuellen Skript (main.py)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Gehe ein Verzeichnis nach oben zum Projektstamm (von 'src' zu 'Alchemist')
        project_root = os.path.dirname(script_dir)
        # Baue den Pfad zur Map-Datei im 'assets/maps'-Ordner
        map_path = os.path.join(project_root, "assets", "maps", "Map1.tmx")
    except NameError:
        # Fallback für interaktive Umgebungen, wo __file__ nicht existiert
        map_path = os.path.join("assets", "maps", "Map1.tmx")
    
    try:
        map_loader = MapLoader(map_path)
        if map_loader.tmx_data:
            print(f"🗺️ Map erfolgreich geladen von: {map_path}")
            use_map = True
        else:
            print(f"⚠️ Map-Daten sind leer für: {map_path} - verwende Standard-Hintergrund")
            map_loader = None
            use_map = False
    except Exception as e:
        print(f"⚠️ Map konnte nicht geladen werden von {map_path}: {e}")
        print("🎨 Verwende Standard-Hintergrund")
        map_loader = None
        use_map = False
    
    # Spieler auf dem Boden platzieren
    game.player.rect.bottom = GROUND_Y_POSITION

    # Kamera erstellen
    camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT)

    all_sprites = pygame.sprite.Group()
    all_sprites.add(game.player)
    
    # Tastaturstatus für sanfte Bewegung
    keys_pressed = {'left': False, 'right': False, 'up': False, 'down': False}
    
    print("🎮 Der Alchemist mit Kamera gestartet!")
    print("Verwenden Sie die Pfeiltasten oder A/D für Bewegung!")

    # --- Haupt-Spiel-Loop ---
    running = True
    while running:
        # 1. Event-Handling
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
                elif event.key == pygame.K_UP or event.key == pygame.K_w:
                    keys_pressed['up'] = True
                elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                    keys_pressed['down'] = True
                    
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
                    
                # Musik ein-/ausschalten
                elif event.key == pygame.K_m:
                    if pygame.mixer.music.get_busy():
                        pygame.mixer.music.pause()
                        print("🔇 Musik pausiert")
                    else:
                        pygame.mixer.music.unpause()
                        print("🔊 Musik fortgesetzt")
                    
            elif event.type == pygame.KEYUP:
                # Bewegung stoppen
                if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                    keys_pressed['left'] = False
                elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                    keys_pressed['right'] = False
                elif event.key == pygame.K_UP or event.key == pygame.K_w:
                    keys_pressed['up'] = False
                elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                    keys_pressed['down'] = False

        # 2. Kontinuierliche Bewegung
        total_dx = 0
        total_dy = 0
        is_moving = False
        
        if keys_pressed['left']:
            dx, dy = game.player.get_movement_left()
            total_dx += dx
            is_moving = True
        if keys_pressed['right']:
            dx, dy = game.player.get_movement_right()
            total_dx += dx
            is_moving = True
        if keys_pressed['up']:
            dx, dy = game.player.get_movement_up()
            total_dy += dy
            is_moving = True
        if keys_pressed['down']:
            dx, dy = game.player.get_movement_down()
            total_dy += dy
            is_moving = True
            
        # Stoppe Bewegung wenn keine Taste gedrückt
        if not is_moving:
            game.player.stop_moving()
        
        # Führe die Bewegung mit Kollisionserkennung aus
        if total_dx != 0 or total_dy != 0:
            collision_objects = map_loader.collision_objects if use_map and map_loader else None
            game.move_player_with_collision(total_dx, total_dy, collision_objects)

        # 3. Update
        game.update()
        all_sprites.update()
        camera.update(game.player) # Kamera auf den Spieler aktualisieren

        # 4. Zeichnen (Rendering) auf die große Spielfläche
        if use_map:
            renderer.draw_background(map_loader, camera)  # Zeichne TMX-Map
        else:
            renderer.draw_background()  # Zeichne Standard-Hintergrund
            renderer.draw_ground_stones(camera)  # Steine nur bei Standard-Hintergrund
            
        renderer.draw_player(game.player, camera)
        renderer.draw_ui(game)
        renderer.draw_controls()

        # 5. Skaliere die große Spielfläche auf das kleinere Fenster
        scaled_surface = pygame.transform.scale(game_surface, (WINDOW_WIDTH, WINDOW_HEIGHT))
        display_surface.blit(scaled_surface, (0, 0))
        
        # 6. Bildschirm aktualisieren
        pygame.display.flip()
        clock.tick(FPS)

    # --- Spiel beenden ---
    pygame.quit()
    print(f"🏁 Spiel beendet! Endpunktzahl: {game.score}")

if __name__ == "__main__":
    main()
