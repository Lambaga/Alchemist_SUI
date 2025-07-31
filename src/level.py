# src/level.py
# Level/Gameplay-Zustand - Hier läuft das eigentliche Spiel
import pygame
import os
from settings import *
from game import Game as GameLogic
from camera import Camera
from map_loader import MapLoader

class GameRenderer:
    """Rendering-System für das Level"""
    
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.Font(None, 50)
        self.small_font = pygame.font.Font(None, 36)
        self.generate_ground_stones()
        
    def generate_ground_stones(self):
        """Generiert zufällige Steine für den Boden"""
        import random
        self.stones = []
        world_width = SCREEN_WIDTH * 3
        
        for _ in range(200):
            x = random.randint(-world_width // 2, world_width // 2)
            y = random.randint(SCREEN_HEIGHT - 200 + 10, SCREEN_HEIGHT - 20)
            size = random.randint(3, 12)
            gray = random.randint(80, 140)
            color = (gray, gray, gray)
            
            self.stones.append({
                'x': x, 'y': y, 'size': size, 'color': color
            })
    
    def draw_background(self, map_loader=None, camera=None):
        """Zeichnet den Hintergrund"""
        if map_loader and camera and map_loader.tmx_data:
            self.screen.fill((50, 50, 50))
            map_loader.render(self.screen, camera)
        else:
            self.screen.fill(BACKGROUND_COLOR)
            # Standard-Hintergrund mit Boden und Bäumen
            tree_rect = pygame.Rect(0, SCREEN_HEIGHT - 400, SCREEN_WIDTH, 200)
            pygame.draw.rect(self.screen, (34, 139, 34), tree_rect)
            ground_rect = pygame.Rect(0, SCREEN_HEIGHT - 200, SCREEN_WIDTH, 200)
            pygame.draw.rect(self.screen, (139, 69, 19), ground_rect)
    
    def draw_ground_stones(self, camera):
        """Zeichnet Steine mit Kamera-Transformation"""
        for stone in self.stones:
            stone_rect = pygame.Rect(stone['x'], stone['y'], stone['size'], stone['size'])
            stone_pos = camera.apply_rect(stone_rect)
            
            if -50 < stone_pos.x < SCREEN_WIDTH + 50:
                scaled_size = int(stone['size'] * camera.zoom_factor)
                pygame.draw.circle(self.screen, stone['color'], 
                                 (int(stone_pos.x + scaled_size//2), 
                                  int(stone_pos.y + scaled_size//2)), 
                                 max(1, scaled_size//2))
    
    def draw_player(self, player, camera):
        """Zeichnet den Spieler mit Kamera und Zoom"""
        if hasattr(player, 'image') and player.image:
            player_pos = camera.apply(player)  # Gibt bereits skaliertes Rect zurück
            # Skaliere das Bild auf die Größe, die camera.apply() berechnet hat
            scaled_image = pygame.transform.scale(player.image, (player_pos.width, player_pos.height))
            self.screen.blit(scaled_image, (player_pos.x, player_pos.y))
        else:
            # Fallback für fehlende Sprites - camera.apply() gibt bereits skaliertes Rect
            player_pos = camera.apply(player)
            pygame.draw.rect(self.screen, (100, 255, 100), player_pos)
    
    def draw_ui(self, game_logic):
        """Zeichnet die Benutzeroberfläche"""
        # UI-Hintergrund
        ui_rect = pygame.Rect(20, 20, 600, 250)
        pygame.draw.rect(self.screen, UI_BACKGROUND, ui_rect)
        pygame.draw.rect(self.screen, TEXT_COLOR, ui_rect, 3)
        
        y_offset = 40
        
        # Titel
        title = self.font.render(GAME_TITLE, True, TEXT_COLOR)
        self.screen.blit(title, (40, y_offset))
        y_offset += 50
        
        # Punkte
        score_text = f"Punkte: {game_logic.score}"
        score_surface = self.font.render(score_text, True, TEXT_COLOR)
        self.screen.blit(score_surface, (40, y_offset))
        y_offset += 40
        
        # Aktive Zutaten
        zutaten_text = f"Inventar ({len(game_logic.aktive_zutaten)}/5):"
        zutaten_surface = self.font.render(zutaten_text, True, TEXT_COLOR)
        self.screen.blit(zutaten_surface, (40, y_offset))
        y_offset += 35
        
        # Zutaten-Symbole
        zutaten_farben = {
            "wasserkristall": (0, 150, 255),
            "feueressenz": (255, 100, 0),
            "erdkristall": (139, 69, 19)
        }
        
        start_x = 50
        for i, zutat in enumerate(game_logic.aktive_zutaten):
            color = zutaten_farben.get(zutat, (200, 200, 200))
            rect_x = start_x + i * 70
            pygame.draw.rect(self.screen, color, (rect_x, y_offset, 50, 50))
        
        y_offset += 70
        
        # Letztes Brau-Ergebnis
        result_lines = game_logic.last_brew_result.split('\n')
        for line in result_lines:
            if line.strip():
                result_surface = self.small_font.render(line, True, TEXT_COLOR)
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
            "+ / - : Zoom ein/aus",
            "R: Reset",
            "M: Musik ein/aus",
            "ESC: Beenden"
        ]
        
        start_y = SCREEN_HEIGHT - 270
        for i, control in enumerate(controls):
            color = TEXT_COLOR if i > 0 else (255, 255, 0)
            control_surface = self.small_font.render(control, True, color)
            self.screen.blit(control_surface, (SCREEN_WIDTH - 300, start_y + i * 30))

class Level:
    """Hauptspiel-Level - Verwaltet Gameplay-Zustand"""
    
    def __init__(self, screen):
        self.screen = screen  # Verwende die übergebene Surface
        self.game_logic = GameLogic()
        # FIX: Verwende die Surface-Dimensionen für die Kamera, nicht SCREEN_-Konstanten
        surface_width = screen.get_width()
        surface_height = screen.get_height()
        self.camera = Camera(surface_width, surface_height, DEFAULT_ZOOM)
        self.renderer = GameRenderer(self.screen)
        
        # Map laden
        self.load_map()
        
        # Input-Status
        self.keys_pressed = {'left': False, 'right': False, 'up': False, 'down': False}
        
        print("🎮 Level initialisiert!")
    
    def load_map(self):
        """Lädt die Spielkarte und extrahiert Spawn-Punkte"""
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(script_dir)
            map_path = os.path.join(project_root, "assets", "maps", "Map1.tmx")
            
            self.map_loader = MapLoader(map_path)
            if self.map_loader.tmx_data:
                print(f"🗺️ Map erfolgreich geladen")
                self.use_map = True
                
                # Datengesteuertes Spawning: Spieler-Position aus Tiled-Map extrahieren
                self.spawn_entities_from_map()
                
            else:
                print("⚠️ Verwende Standard-Hintergrund")
                self.map_loader = None
                self.use_map = False
                # Fallback: Standard-Position
                self.game_logic.player.rect.bottom = SCREEN_HEIGHT - 200
                
        except Exception as e:
            print(f"⚠️ Map-Fehler: {e}")
            self.map_loader = None
            self.use_map = False
            # Fallback: Standard-Position
            self.game_logic.player.rect.bottom = SCREEN_HEIGHT - 200
    
    def spawn_entities_from_map(self):
        """Spawnt Entities basierend auf Tiled-Map Objekten (datengesteuert)"""
        if not self.map_loader or not self.map_loader.tmx_data:
            return
            
        player_spawned = False
        spawn_count = 0
        
        # Durchsuche alle Objekt-Layer nach Spawn-Punkten
        for layer in self.map_loader.tmx_data.visible_layers:
            if hasattr(layer, 'objects'):  # Objekt-Layer
                for obj in layer.objects:
                    spawn_count += 1
                    
                    # Player Spawn-Punkt
                    if obj.name and obj.name.lower() in ['player', 'spawn', 'player_spawn']:
                        print(f"🧙‍♂️ Player-Spawn gefunden bei: ({obj.x}, {obj.y})")
                        self.game_logic.player.rect.centerx = obj.x
                        self.game_logic.player.rect.centery = obj.y
                        player_spawned = True
                    
                    # Weitere Spawn-Typen für zukünftige Erweiterung
                    elif obj.name and obj.name.lower() in ['enemy', 'orc', 'monster']:
                        print(f"👹 Enemy-Spawn gefunden bei: ({obj.x}, {obj.y}) - noch nicht implementiert")
                        # Hier könnte später Enemy-Spawning implementiert werden
                        
                    elif obj.name and obj.name.lower() in ['item', 'treasure', 'ingredient']:
                        print(f"💎 Item-Spawn gefunden bei: ({obj.x}, {obj.y}) - noch nicht implementiert")
                        # Hier könnte später Item-Spawning implementiert werden
        
        # Fallback falls kein Player-Spawn in der Map definiert ist
        if not player_spawned:
            print("⚠️ Kein Player-Spawn in Map gefunden - verwende Standard-Position")
            self.game_logic.player.rect.bottom = SCREEN_HEIGHT - 200
            self.game_logic.player.rect.centerx = SCREEN_WIDTH // 2
        
        print(f"📊 Spawn-Analyse: {spawn_count} Objekte durchsucht, Player gespawnt: {player_spawned}")
    
    def handle_input(self, event):
        """Behandelt Input-Events"""
        if event.type == pygame.KEYDOWN:
            # Bewegung starten
            for direction, keys in MOVEMENT_KEYS.items():
                if event.key in keys:
                    self.keys_pressed[direction] = True
            
            # Aktionen
            if event.key == ACTION_KEYS['brew']:
                self.game_logic.brew()
            elif event.key == ACTION_KEYS['remove_ingredient']:
                self.game_logic.remove_last_zutat()
            elif event.key == ACTION_KEYS['reset']:
                self.game_logic.reset_game()
            elif event.key == ACTION_KEYS['music_toggle']:
                self.toggle_music()
            elif event.key in ACTION_KEYS['zoom_in']:
                self.camera.zoom_in()
                print(f"🔍 Zoom: {self.camera.zoom_factor:.1f}x")
            elif event.key == ACTION_KEYS['zoom_out']:
                self.camera.zoom_out()
                print(f"🔍 Zoom: {self.camera.zoom_factor:.1f}x")
            
            # Test-Zutaten
            elif event.key == pygame.K_1:
                self.game_logic.add_zutat("wasserkristall")
            elif event.key == pygame.K_2:
                self.game_logic.add_zutat("feueressenz")
            elif event.key == pygame.K_3:
                self.game_logic.add_zutat("erdkristall")
        
        elif event.type == pygame.KEYUP:
            # Bewegung stoppen
            for direction, keys in MOVEMENT_KEYS.items():
                if event.key in keys:
                    self.keys_pressed[direction] = False
    
    def toggle_music(self):
        """Schaltet Musik ein/aus"""
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.pause()
            print("🔇 Musik pausiert")
        else:
            pygame.mixer.music.unpause()
            print("🔊 Musik fortgesetzt")
    
    def update(self, dt):
        """Update-Schleife mit Delta Time"""
        # Bewegung verarbeiten
        self.handle_movement(dt)
        
        # Spiel-Logik updaten mit Delta Time
        self.game_logic.update(dt)
        
        # Kamera updaten
        self.camera.update(self.game_logic.player)
    
    def handle_movement(self, dt):
        """Behandelt kontinuierliche Bewegung mit Delta Time"""
        total_dx = 0
        total_dy = 0
        is_moving = False
        
        # Basis-Bewegung sammeln
        if self.keys_pressed['left']:
            dx, dy = self.game_logic.player.get_movement_left()
            total_dx += dx
            is_moving = True
        if self.keys_pressed['right']:
            dx, dy = self.game_logic.player.get_movement_right()
            total_dx += dx
            is_moving = True
        if self.keys_pressed['up']:
            dx, dy = self.game_logic.player.get_movement_up()
            total_dy += dy
            is_moving = True
        if self.keys_pressed['down']:
            dx, dy = self.game_logic.player.get_movement_down()
            total_dy += dy
            is_moving = True
        
        # Delta Time anwenden für framerate-unabhängige Bewegung
        if total_dx != 0 or total_dy != 0:
            # Basis-Geschwindigkeit mit Delta Time multiplizieren
            base_speed = self.game_logic.player.speed
            total_dx *= dt * 60  # * 60 für 60 FPS Referenz
            total_dy *= dt * 60
            
            # Diagonalbewegung normalisieren
            if total_dx != 0 and total_dy != 0:
                import math
                length = math.sqrt(total_dx * total_dx + total_dy * total_dy)
                if length > 0:
                    total_dx = (total_dx / length) * (base_speed * dt * 60)
                    total_dy = (total_dy / length) * (base_speed * dt * 60)
        
        # Bewegung stoppen wenn keine Taste gedrückt
        if not is_moving:
            self.game_logic.player.stop_moving()
        
        # Bewegung mit Kollision ausführen
        if total_dx != 0 or total_dy != 0:
            collision_objects = self.map_loader.collision_objects if self.use_map and self.map_loader else None
            self.game_logic.move_player_with_collision(total_dx, total_dy, collision_objects)
    
    def render(self):
        """Rendering des Levels"""
        # Hintergrund
        if self.use_map:
            self.renderer.draw_background(self.map_loader, self.camera)
        else:
            self.renderer.draw_background()
            self.renderer.draw_ground_stones(self.camera)
        
        # Spieler
        self.renderer.draw_player(self.game_logic.player, self.camera)
        
        # UI
        self.renderer.draw_ui(self.game_logic)
        self.renderer.draw_controls()
    
    def run(self, dt):
        """Haupt-Update-Methode für das Level"""
        self.update(dt)
        self.render()
