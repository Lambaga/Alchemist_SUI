# -*- coding: utf-8 -*-
# src/level.py
# Level/Gameplay state - Here the actual game runs
import pygame
from os import path
from settings import *
from game import Game as GameLogic
from camera import Camera
from map_loader import MapLoader
from enemy_manager import EnemyManager

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
            self.screen.fill((0, 0, 0))  # Schwarzer Hintergrund für besseren Kontrast
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
            # Fallback für fehlende Sprites - helle Farbe für bessere Sichtbarkeit
            player_pos = camera.apply(player)
            pygame.draw.rect(self.screen, (255, 255, 0), player_pos)  # Gelb statt grün
            # Zusätzlicher Rahmen für noch bessere Sichtbarkeit
            pygame.draw.rect(self.screen, (255, 255, 255), player_pos, 3)
    
    def draw_collision_debug(self, player, camera, collision_objects):
        """Zeichnet Kollisionsboxen für Debugging"""
        # Player-Hitbox zeichnen
        player_hitbox_transformed = camera.apply_rect(player.hitbox)
        pygame.draw.rect(self.screen, (255, 0, 0), player_hitbox_transformed, 2)  # Rot für Player-Hitbox
        
        # Kollisionsobjekte zeichnen
        for collision_rect in collision_objects:
            collision_transformed = camera.apply_rect(collision_rect)
            pygame.draw.rect(self.screen, (0, 255, 255), collision_transformed, 2)  # Cyan für Kollisionsobjekte
    
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
        score_text = "Punkte: {}".format(game_logic.score)
        score_surface = self.font.render(score_text, True, TEXT_COLOR)
        self.screen.blit(score_surface, (40, y_offset))
        y_offset += 40
        
        # Aktive Zutaten
        zutaten_text = "Inventar ({}/5):".format(len(game_logic.aktive_zutaten))
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
        
        # Map-Status anzeigen
        y_offset += 10
        map_status = "🗺️ Map geladen" if hasattr(game_logic, 'level') and game_logic.level and game_logic.level.use_map else "⚠️ Standard-Grafik"
        # Fallback für wenn game_logic keine level-Referenz hat
        try:
            level_instance = getattr(game_logic, '_level_ref', None)
            if level_instance and hasattr(level_instance, 'use_map') and level_instance.use_map:
                map_status = "🗺️ Map geladen"
        except:
            pass
        map_surface = self.small_font.render(map_status, True, (150, 255, 150))
        self.screen.blit(map_surface, (40, y_offset))
    
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
            "F1: Kollisions-Debug",
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
        # Referenz für UI-Status-Anzeige
        self.game_logic._level_ref = self
        # FIX: Verwende die Surface-Dimensionen für die Kamera, nicht SCREEN_-Konstanten
        surface_width = screen.get_width()
        surface_height = screen.get_height()
        self.camera = Camera(surface_width, surface_height, DEFAULT_ZOOM)
        self.renderer = GameRenderer(self.screen)
        
        # Enemy Manager initialisieren (BEFORE map loading!)
        self.enemy_manager = EnemyManager()
        
        # Map laden
        self.load_map()
        
        # Kollisionsobjekte einmalig setzen (nicht bei jeder Bewegung!)
        self.setup_collision_objects()
        
        # Input-Status
        self.keys_pressed = {'left': False, 'right': False, 'up': False, 'down': False}
        
        # Debug-Optionen
        self.show_collision_debug = False  # Standardmäßig aus, mit F1 aktivierbar
    
    def load_map(self):
        """Lädt die Spielkarte und extrahiert Spawn-Punkte"""
        try:
            map_path = path.join(MAP_DIR, "Map2.tmx") # Verwende MAP_DIR aus settings
            
            self.map_loader = MapLoader(map_path)
            
            if self.map_loader and self.map_loader.tmx_data:
                self.use_map = True
                
                # Datengesteuertes Spawning: Spieler-Position aus Tiled-Map extrahieren
                self.spawn_entities_from_map()
                
            else:
                self.map_loader = None
                self.use_map = False
                # Fallback: Standard-Position (nur wenn keine Map)
                self.game_logic.player.rect.bottom = self.screen.get_height() - 200
                self.game_logic.player.rect.centerx = self.screen.get_width() // 2
                self.game_logic.player.update_hitbox()  # Hitbox nach Positionsänderung aktualisieren
                
        except Exception as e:
            if self.map_loader and self.map_loader.tmx_data:
                self.use_map = True
            else:
                self.map_loader = None
                self.use_map = False
                # Fallback: Standard-Position (nur wenn Map fehlschlägt)
                self.game_logic.player.rect.bottom = self.screen.get_height() - 200
                self.game_logic.player.rect.centerx = self.screen.get_width() // 2
                self.game_logic.player.update_hitbox()  # Hitbox nach Positionsänderung aktualisieren
    
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
                        self.game_logic.player.rect.centerx = obj.x
                        self.game_logic.player.rect.centery = obj.y
                        self.game_logic.player.update_hitbox()  # Hitbox nach Positionsänderung aktualisieren
                        player_spawned = True
                    
                    # Weitere Spawn-Typen für zukünftige Erweiterung
                    elif obj.name and obj.name.lower() in ['enemy', 'orc', 'monster', 'demon']:
                        # Hier könnte später Enemy-Spawning implementiert werden
                        pass
                        
                    elif obj.name and obj.name.lower() in ['item', 'treasure', 'ingredient']:
                        # Hier könnte später Item-Spawning implementiert werden
                        pass
        
        # Demons aus der Map spawnen
        self.enemy_manager.add_enemies_from_map(self.map_loader)
        
        # Teste Demons manuell (entferne das später wenn deine Map Demon-Objekte hat)
        if self.map_loader and self.map_loader.tmx_data:
            # Hole die Player-Position für relative Spawns
            player_x = self.game_logic.player.rect.centerx
            player_y = self.game_logic.player.rect.centery
            
            # Spawne verschiedene Enemies relativ zum Player (einige Tiles entfernt)
            # 64 Pixel = etwa 1 Tile, spawne sehr nah zum Player
            demon1 = self.enemy_manager.add_demon(player_x + 100, player_y, scale=3.0, facing_right=False)  # Direkt rechts vom Player
            demon2 = self.enemy_manager.add_demon(player_x - 100, player_y, scale=3.0, facing_right=True)   # Direkt links vom Player  
            fireworm1 = self.enemy_manager.add_fireworm(player_x, player_y - 100, scale=2.0, facing_right=False) # FireWorm über dem Player
        
        # Fallback falls kein Player-Spawn in der Map definiert ist
        if not player_spawned:
            # Positioniere Player innerhalb der Map-Grenzen, nicht außerhalb!
            if self.map_loader and self.map_loader.tmx_data:
                # Setze Player in die untere Hälfte der Map, aber oberhalb der Kollisionen
                map_height = self.map_loader.height
                self.game_logic.player.rect.centerx = self.map_loader.width // 2  # Mitte der Map
                self.game_logic.player.rect.centery = map_height - 100  # 100 Pixel vom unteren Rand
                self.game_logic.player.update_hitbox()  # Hitbox nach Positionsänderung aktualisieren
            else:
                # Fallback für wenn keine Map geladen ist
                self.game_logic.player.rect.bottom = self.screen.get_height() - 200
                self.game_logic.player.rect.centerx = self.screen.get_width() // 2
                self.game_logic.player.update_hitbox()  # Hitbox nach Positionsänderung aktualisieren
    
    def setup_collision_objects(self):
        """Setzt die Kollisionsobjekte für den Player (einmalig)"""
        if self.use_map and self.map_loader and self.map_loader.collision_objects:
            # Konvertiere collision_objects zu einer Sprite-Gruppe
            collision_sprites = pygame.sprite.Group()
            for collision_rect in self.map_loader.collision_objects:
                # Erstelle ein temporäres Sprite für jedes Kollisionsobjekt
                sprite = pygame.sprite.Sprite()
                sprite.hitbox = collision_rect
                sprite.rect = collision_rect  # Auch rect setzen für Konsistenz
                collision_sprites.add(sprite)
            self.game_logic.player.set_obstacle_sprites(collision_sprites)
            
            # Set obstacle sprites for all enemies through enemy manager
            self.enemy_manager.set_obstacle_sprites(collision_sprites)
    
    def handle_event(self, event):
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
            elif event.key == ACTION_KEYS['zoom_out']:
                self.camera.zoom_out()
            
            # Test-Zutaten
            elif event.key == pygame.K_1:
                self.game_logic.add_zutat("wasserkristall")
            elif event.key == pygame.K_2:
                self.game_logic.add_zutat("feueressenz")
            elif event.key == pygame.K_3:
                self.game_logic.add_zutat("erdkristall")
            
            # Debug-Toggle
            elif event.key == pygame.K_F1:
                self.show_collision_debug = not self.show_collision_debug
        
        elif event.type == pygame.KEYUP:
            # Bewegung stoppen
            for direction, keys in MOVEMENT_KEYS.items():
                if event.key in keys:
                    self.keys_pressed[direction] = False
    
    def toggle_music(self):
        """Schaltet Musik ein/aus"""
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.pause()
        else:
            pygame.mixer.music.unpause()
    
    def update(self, dt):
        """Update-Schleife mit Delta Time"""
        # Bewegung verarbeiten
        self.handle_movement(dt)
        
        # Spiel-Logik updaten mit Delta Time
        self.game_logic.update(dt)
        
        # Demons updaten mit Player-Referenz für AI
        self.enemy_manager.update(dt, self.game_logic.player)
        
        # Kamera updaten
        self.camera.update(self.game_logic.player)
    
    def handle_movement(self, dt):
        """Behandelt Spieler-Bewegung mit dt-System"""
        import pygame
        
        # Sammle alle Eingaben als Richtungsvektor
        direction = pygame.math.Vector2(0, 0)
        is_moving = False
        
        if self.keys_pressed['left']:
            direction.x -= 1
            is_moving = True
        if self.keys_pressed['right']:
            direction.x += 1
            is_moving = True
        if self.keys_pressed['up']:
            direction.y -= 1
            is_moving = True
        if self.keys_pressed['down']:
            direction.y += 1
            is_moving = True
        
        # Setze die Bewegungsrichtung im Player
        self.game_logic.player.direction = direction
        
        # Führe die Bewegung aus (Player macht dt-Berechnung intern)
        self.game_logic.player.move(dt)
    
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
        
        # Demons zeichnen
        self.enemy_manager.draw(self.screen, self.camera)
        
        # Debug: Kollisionsboxen zeichnen (falls aktiviert)
        if hasattr(self, 'show_collision_debug') and self.show_collision_debug:
            self.renderer.draw_collision_debug(self.game_logic.player, self.camera, 
                                             self.map_loader.collision_objects if self.map_loader else [])
            # Demon debug hitboxes
            self.enemy_manager.draw_debug(self.screen, self.camera)
        
        # UI
        self.renderer.draw_ui(self.game_logic)
        self.renderer.draw_controls()
    
    def run(self, dt):
        """Haupt-Update-Methode für das Level"""
        self.update(dt)
        self.render()
