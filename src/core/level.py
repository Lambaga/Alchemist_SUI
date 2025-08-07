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
from health_bar_py27 import HealthBarManager, create_player_health_bar, create_enemy_health_bar
from input_system import get_input_system

class GameRenderer:
    """Rendering-System für das Level"""
    
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.Font(None, 50)
        self.small_font = pygame.font.Font(None, 36)
        self.generate_ground_stones()
        
        # Performance-Optimierung: Asset Manager für gecachte Sprite-Skalierung
        from asset_manager import AssetManager
        self.asset_manager = AssetManager()
        
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
        """Zeichnet den Spieler mit Kamera und Zoom - Performance-optimiert"""
        # Prüfe Unsichtbarkeit
        if hasattr(player, 'magic_system') and player.magic_system.is_invisible(player):
            # Spieler ist unsichtbar - halb-transparente Darstellung
            if hasattr(player, 'image') and player.image:
                player_pos = camera.apply(player)
                scaled_image = self.asset_manager.get_scaled_sprite(
                    player.image, 
                    (player_pos.width, player_pos.height)
                )
                # Transparente Darstellung erstellen
                transparent_surface = pygame.Surface((player_pos.width, player_pos.height), pygame.SRCALPHA)
                transparent_surface.blit(scaled_image, (0, 0))
                transparent_surface.set_alpha(80)  # 30% Sichtbarkeit
                self.screen.blit(transparent_surface, (player_pos.x, player_pos.y))
            else:
                # Transparenter Fallback
                player_pos = camera.apply(player)
                transparent_surface = pygame.Surface((player_pos.width, player_pos.height), pygame.SRCALPHA)
                pygame.draw.rect(transparent_surface, (255, 255, 0, 80), (0, 0, player_pos.width, player_pos.height))
                self.screen.blit(transparent_surface, (player_pos.x, player_pos.y))
        else:
            # Normale Darstellung
            if hasattr(player, 'image') and player.image:
                player_pos = camera.apply(player)  # Gibt bereits skaliertes Rect zurück
                # Performance-Optimierung: Nutze gecachte Skalierung statt jedes Mal neu zu skalieren
                scaled_image = self.asset_manager.get_scaled_sprite(
                    player.image, 
                    (player_pos.width, player_pos.height)
                )
                self.screen.blit(scaled_image, (player_pos.x, player_pos.y))
                
                # Schild-Effekt zeichnen
                if hasattr(player, 'magic_system') and player.magic_system.is_shielded(player):
                    # Blauer Schild-Ring um den Spieler
                    import math
                    shield_center = (player_pos.centerx, player_pos.centery)
                    current_time = pygame.time.get_ticks()
                    pulse = abs(math.sin(current_time * 0.01)) * 10 + 5  # Pulsierender Effekt
                    pygame.draw.circle(self.screen, (100, 150, 255), shield_center, int(player_pos.width // 2 + pulse), 3)
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
        ui_rect = pygame.Rect(20, 20, 600, 320)  # Größer für Magie-Anzeige
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
        
        # Magie-System UI (falls Player verfügbar)
        if hasattr(game_logic, 'player') and game_logic.player:
            self.draw_magic_ui(game_logic.player.magic_system, 40, y_offset)
            y_offset += 50
        
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
            "1,2,3 Magic-Elemente", 
            "Leertaste: Brauen",
            "Backspace: Zutat entfernen",
            "🔮 MAGIE:",
            "1: Wasser, 2: Feuer, 3: Stein",
            "C: Zaubern, X: Elemente löschen",
            "R: Reset, M: Musik ein/aus",
            "F1: Kollisions-Debug",
            "F2: Health-Bars ein/aus",
            "💾 SPEICHERN:",
            "F9-F12: Speichern (Slot 1-4)",
            "Shift+F9-F12: Löschen (Slot 1-4)",
            "ESC: Zurück zum Menü"
        ]
        
        start_y = SCREEN_HEIGHT - 380  # Mehr Platz für zusätzliche Zeilen
        for i, control in enumerate(controls):
            color = TEXT_COLOR if i > 0 else (255, 255, 0)
            # Magie-Titel hervorheben
            if control.startswith("🔮"):
                color = (150, 255, 255)
            # Speicher-Titel hervorheben
            elif control.startswith("💾"):
                color = (255, 200, 100)
            control_surface = self.small_font.render(control, True, color)
            self.screen.blit(control_surface, (SCREEN_WIDTH - 350, start_y + i * 23))
    
    def draw_magic_ui(self, magic_system, x, y):
        """Zeichnet die Magie-System UI"""
        # Titel
        magic_title = self.small_font.render("🔮 Magie:", True, (150, 255, 255))
        self.screen.blit(magic_title, (x, y))
        
        # Ausgewählte Elemente
        if magic_system.selected_elements:
            elements_text = f"Elemente: {magic_system.get_selected_elements_str()}"
        else:
            elements_text = "Elemente: Keine ausgewählt"
            
        elements_surface = self.small_font.render(elements_text, True, TEXT_COLOR)
        self.screen.blit(elements_surface, (x, y + 25))
        
        # Element-Symbole zeichnen
        element_colors = {
            "feuer": (255, 100, 0),
            "wasser": (0, 150, 255), 
            "stein": (139, 69, 19)
        }
        
        start_x = x + 200
        for i, element in enumerate(magic_system.selected_elements):
            color = element_colors.get(element.value, (200, 200, 200))
            rect_x = start_x + i * 35
            pygame.draw.circle(self.screen, color, (rect_x + 12, y + 35), 12)
            # Element-Symbol
            symbol = {"feuer": "🔥", "wasser": "💧", "stein": "🗿"}.get(element.value, "?")
            # Kleiner Text für Symbole (falls Font verfügbar)
            try:
                symbol_surface = self.small_font.render(symbol, True, (255, 255, 255))
                symbol_rect = symbol_surface.get_rect(center=(rect_x + 12, y + 35))
                self.screen.blit(symbol_surface, symbol_rect)
            except:
                # Fallback: Einfache Farbe
                pass

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
        self.camera = Camera(surface_width, surface_height)  # Kein Zoom-Parameter mehr nötig
        self.renderer = GameRenderer(self.screen)
        
        # Health-Bar Manager initialisieren
        self.health_bar_manager = HealthBarManager()
        
        # Enemy Manager initialisieren (BEFORE map loading!)
        self.enemy_manager = EnemyManager()
        
        # Map laden
        self.load_map()
        
        # Kollisionsobjekte einmalig setzen (nicht bei jeder Bewegung!)
        self.setup_collision_objects()
        
        # Health-Bars für alle Entitäten hinzufügen
        self.setup_health_bars()
        
        # Input-System initialisieren
        self.input_system = get_input_system()
        
        # Input-Status (wird jetzt vom Universal Input System verwaltet)
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
            
            # Spawne verschiedene Enemies relativ zum Player
            demon1 = self.enemy_manager.add_demon(player_x + 100, player_y, scale=3.0, facing_right=False)
            demon2 = self.enemy_manager.add_demon(player_x - 100, player_y, scale=3.0, facing_right=True)  
            fireworm1 = self.enemy_manager.add_fireworm(player_x, player_y - 100, scale=2.0, facing_right=False)
            
            # Health-Bars für alle gespawnten Enemies hinzufügen
            if demon1:
                self.add_enemy_health_bar(demon1)
            if demon2:
                self.add_enemy_health_bar(demon2)
            if fireworm1:
                self.add_enemy_health_bar(fireworm1)
        
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
    
    def respawn_enemies_only(self):
        """Spawnt nur die Feinde neu, ohne die Spieler-Position zu verändern"""
        if not self.map_loader or not self.map_loader.tmx_data:
            return
        
        # Demons aus der Map spawnen
        self.enemy_manager.add_enemies_from_map(self.map_loader)
        
        # Teste Demons manuell (entferne das später wenn deine Map Demon-Objekte hat)
        # Hole die Player-Position für relative Spawns
        player_x = self.game_logic.player.rect.centerx
        player_y = self.game_logic.player.rect.centery
        
        # Spawne verschiedene Enemies relativ zum Player
        demon1 = self.enemy_manager.add_demon(player_x + 100, player_y, scale=3.0, facing_right=False)
        demon2 = self.enemy_manager.add_demon(player_x - 100, player_y, scale=3.0, facing_right=True)  
        fireworm1 = self.enemy_manager.add_fireworm(player_x, player_y - 100, scale=2.0, facing_right=False)
        
        # Health-Bars für alle gespawnten Enemies hinzufügen
        if demon1:
            self.add_enemy_health_bar(demon1)
        if demon2:
            self.add_enemy_health_bar(demon2)
        if fireworm1:
            self.add_enemy_health_bar(fireworm1)
    
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
    
    def setup_health_bars(self):
        """Erstellt Health-Bars für alle Entitäten im Level"""
        # Player Health-Bar hinzufügen
        player_health_bar = create_player_health_bar(
            self.game_logic.player,
            width=100,
            height=12,
            offset_y=-35,
            show_when_full=True  # Spieler Health-Bar immer sichtbar
        )
        self.health_bar_manager.add_entity(
            self.game_logic.player, 
            renderer=player_health_bar.renderer,
            width=player_health_bar.width,
            height=player_health_bar.height,
            offset_y=player_health_bar.offset_y,
            show_when_full=player_health_bar.show_when_full
        )
        
        # Enemy Health-Bars werden automatisch hinzugefügt wenn Enemies gespawnt werden
        # Das passiert in add_enemy_health_bar() Methode
        
        print("✅ Health-Bar System initialisiert")
    
    def add_enemy_health_bar(self, enemy):
        """Fügt eine Health-Bar für einen neuen Feind hinzu"""
        try:
            # Größere Health-Bars für Gegner mit mehr HP
            if hasattr(enemy, 'max_health') and enemy.max_health >= 200:
                # Größere Health-Bar für stärkere Gegner
                width = 80
                height = 10
                offset_y = -30
            else:
                # Normale Größe für schwächere Gegner
                width = 60
                height = 8
                offset_y = -25
                
            enemy_health_bar = create_enemy_health_bar(
                enemy,
                width=width,
                height=height,
                offset_y=offset_y,
                show_when_full=True,  # Immer sichtbar für bessere Übersicht
                fade_delay=3.0  # Länger sichtbar
            )
            self.health_bar_manager.add_entity(
                enemy, 
                renderer=enemy_health_bar.renderer,
                width=enemy_health_bar.width,
                height=enemy_health_bar.height,
                offset_y=enemy_health_bar.offset_y,
                show_when_full=enemy_health_bar.show_when_full,
                fade_delay=enemy_health_bar.fade_delay
            )
            print(f"✅ Health-Bar für {type(enemy).__name__} hinzugefügt (HP: {enemy.max_health})")
        except Exception as e:
            print(f"⚠️ Fehler beim Hinzufügen der Enemy Health-Bar: {e}")
    
    def handle_event(self, event):
        """Behandelt Input-Events - Erweitert für Joystick-Support"""
        # Universal Input System für Actions verwenden
        action = self.input_system.handle_event(event)
        
        if action:
            # Action-Mapping
            if action == 'brew':
                self.game_logic.brew()
            elif action == 'remove_ingredient':
                self.game_logic.remove_last_zutat()
            elif action == 'reset':
                self.game_logic.reset_game()
            elif action == 'music_toggle':
                self.toggle_music()
            elif action == 'pause':
                # Pause wird vom Main Game gehandhabt
                pass
            elif action == 'ingredient_1':
                # 1 = Wasser-Element für Magie
                self.handle_magic_element('water')
            elif action == 'ingredient_2':
                # 2 = Feuer-Element für Magie
                self.handle_magic_element('fire')
            elif action == 'ingredient_3':
                # 3 = Stein-Element für Magie
                self.handle_magic_element('stone')
            # Magie-System Actions
            elif action == 'cast_magic':
                self.handle_cast_magic()
            elif action == 'clear_magic':
                self.handle_clear_magic()
        
        # Traditionelle Tastatur-Events für Kompatibilität
        if event.type == pygame.KEYDOWN:
            # Check for Shift modifier
            keys_pressed = pygame.key.get_pressed()
            shift_pressed = keys_pressed[pygame.K_LSHIFT] or keys_pressed[pygame.K_RSHIFT]
            
            # Save game shortcuts (F9 - F12 for save slots)
            if event.key == pygame.K_F9:
                if shift_pressed:
                    self.trigger_delete_save(1)
                else:
                    self.trigger_save_game(1)
            elif event.key == pygame.K_F10:
                if shift_pressed:
                    self.trigger_delete_save(2)
                else:
                    self.trigger_save_game(2)
            elif event.key == pygame.K_F11:
                if shift_pressed:
                    self.trigger_delete_save(3)
                else:
                    self.trigger_save_game(3)
            elif event.key == pygame.K_F12:
                if shift_pressed:
                    self.trigger_delete_save(4)
                else:
                    self.trigger_save_game(4)
            
            # Debug-Toggle
            elif event.key == pygame.K_F1:
                self.show_collision_debug = not self.show_collision_debug
            elif event.key == pygame.K_F2:
                # Toggle Health-Bars ein/aus
                self.toggle_health_bars()
            # DIREKTER MAGIC-TEST
            elif event.key == pygame.K_h:  # H für direkten Heilungstest
                if self.game_logic and self.game_logic.player:
                    player = self.game_logic.player
                    # Schaden zum Test
                    player.current_health = max(1, player.current_health - 20)
                    # Direkte Heilung
                    player.current_health = min(player.max_health, player.current_health + 50)
            elif event.key == pygame.K_t:  # T für Test Magie
                if self.game_logic and self.game_logic.player:
                    from systems.magic_system import ElementType
                    magic_system = self.game_logic.player.magic_system
                    magic_system.clear_elements()
                    magic_system.add_element(ElementType.FEUER)
                    magic_system.add_element(ElementType.WASSER)
                    magic_system.cast_magic(self.game_logic.player)
    
    def toggle_health_bars(self):
        """Schaltet Health-Bars ein/aus"""
        # Alle Health-Bars durchgehen und Sichtbarkeit umschalten
        for health_bar in self.health_bar_manager.health_bars.values():
            health_bar.visible = not health_bar.visible
        print(f"🔧 Health-Bars: {'Ein' if any(hb.visible for hb in self.health_bar_manager.health_bars.values()) else 'Aus'}")
    
    def trigger_save_game(self, slot_number: int):
        """Trigger save game event (to be handled by main game)"""
        # This will be called by the main game loop
        if hasattr(self, '_save_callback') and self._save_callback:
            self._save_callback(slot_number)
        else:
            print(f"💾 Speichere Spiel in Slot {slot_number}...")
    
    def trigger_delete_save(self, slot_number: int):
        """Trigger delete save event"""
        from managers.save_system import save_manager
        
        # Check if save exists
        save_slots = save_manager.get_save_slots_info()
        slot_exists = False
        slot_name = f"Slot {slot_number}"
        
        for slot in save_slots:
            if slot["slot"] == slot_number and slot["exists"]:
                slot_exists = True
                slot_name = slot["name"]
                break
        
        if slot_exists:
            # Delete the save
            if save_manager.delete_save(slot_number):
                print(f"🗑️ Spielstand '{slot_name}' (Slot {slot_number}) gelöscht!")
            else:
                print(f"❌ Fehler beim Löschen von Slot {slot_number}")
        else:
            print(f"📭 Kein Spielstand in Slot {slot_number} vorhanden")
    
    def set_save_callback(self, callback):
        """Set callback function for save game functionality"""
        self._save_callback = callback
    
    def clear_input_state(self):
        """Clears all input states - useful when pausing/resuming"""
        self.keys_pressed = {'left': False, 'right': False, 'up': False, 'down': False}
        # Also reset player direction to stop movement
        if hasattr(self.game_logic, 'player') and hasattr(self.game_logic.player, 'direction'):
            import pygame
            self.game_logic.player.direction = pygame.math.Vector2(0, 0)
        print("🔧 Input-Status zurückgesetzt")
    
    def toggle_music(self):
        """Schaltet Musik ein/aus"""
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.pause()
        else:
            pygame.mixer.music.unpause()
    
    def update(self, dt):
        """Update-Schleife mit Delta Time - Erweitert für Universal Input"""
        # Universal Input System updaten
        self.input_system.update()
        
        # Bewegung verarbeiten (nutzt jetzt Universal Input System)
        self.handle_movement(dt)
        
        # Spiel-Logik updaten mit Delta Time
        game_result = self.game_logic.update(dt, enemies=list(self.enemy_manager.enemies) if self.enemy_manager else [])
        
        # Prüfe auf Game Over
        if game_result == "game_over":
            return "game_over"
        
        # Magic System explizit updaten mit Feindliste für Kollision
        if self.game_logic and self.game_logic.player and hasattr(self.game_logic.player, 'magic_system'):
            enemies_list = list(self.enemy_manager.enemies) if self.enemy_manager else []
            self.game_logic.player.magic_system.update(dt, enemies_list)
        
        # Demons updaten mit Player-Referenz für AI
        self.enemy_manager.update(dt, self.game_logic.player)
        
        # Health-Bar System updaten
        self.health_bar_manager.update(dt)
        
        # Kamera updaten
        self.camera.update(self.game_logic.player)
        
        return None
    
    def handle_movement(self, dt):
        """Behandelt Spieler-Bewegung mit Universal Input System"""
        import pygame
        
        # Bewegungsvektor vom Universal Input System holen
        direction = self.input_system.get_movement_vector()
        
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
        
        # Magie-Projektile zeichnen (nach Spieler, vor Feinden für korrekte Layering)
        if self.game_logic and self.game_logic.player:
            self.game_logic.player.magic_system.draw_projectiles(self.screen, self.camera)
        
        # Demons zeichnen
        self.enemy_manager.draw(self.screen, self.camera)
        
        # Health-Bars zeichnen (nach Entitäten, damit sie darüber erscheinen)
        camera_offset = (self.camera.camera_rect.x, self.camera.camera_rect.y)
        self.health_bar_manager.draw_all(self.screen, camera_offset)
        
        # Debug: Kollisionsboxen zeichnen (falls aktiviert)
        if hasattr(self, 'show_collision_debug') and self.show_collision_debug:
            self.renderer.draw_collision_debug(self.game_logic.player, self.camera, 
                                             self.map_loader.collision_objects if self.map_loader else [])
            # Demon debug hitboxes
            self.enemy_manager.draw_debug(self.screen, self.camera)
        
        # UI
        self.renderer.draw_ui(self.game_logic)
        self.renderer.draw_controls()
    
    def restart_level(self):
        """Startet das Level nach Game Over neu"""
        print("🔄 Level wird neu gestartet...")
        
        # Spiel-Logik zurücksetzen
        if self.game_logic:
            self.game_logic.reset_game()
        
        # Spieler-Position zurücksetzen und wiederbeleben
        if self.game_logic and self.game_logic.player:
            start_x, start_y = PLAYER_START_POS
            self.game_logic.player.rect.centerx = start_x
            self.game_logic.player.rect.centery = start_y
            self.game_logic.player.update_hitbox()
            # Wichtig: Spieler wiederbeleben!
            self.game_logic.player.revive()
            print("💖 Spieler wiederbelebt mit voller Gesundheit")
        
        # Gegner komplett zurücksetzen - KEIN respawn_default_enemies mehr
        if self.enemy_manager:
            self.enemy_manager.reset_enemies()
            # Spawne nur die Feinde neu, ohne Spieler-Position zu verändern
            self.respawn_enemies_only()
        
        # Health-Bar System zurücksetzen
        if self.health_bar_manager:
            self.health_bar_manager.reset()
            # Health-Bars für Player und neue Feinde erstellen
            self._setup_health_bars()
        
        # Kamera zurücksetzen
        if self.camera and self.game_logic and self.game_logic.player:
            self.camera.update(self.game_logic.player)
        
        # Input-Status leeren
        self.clear_input_state()
        
        print("✅ Level neu gestartet!")
    
    def handle_magic_element(self, element_name: str):
        """Behandelt Magie-Element Eingabe"""
        if self.game_logic and self.game_logic.player:
            from systems.magic_system import ElementType
            
            # Element-Namen zu ElementType mappen
            element_map = {
                'fire': ElementType.FEUER,
                'water': ElementType.WASSER, 
                'stone': ElementType.STEIN
            }
            
            element = element_map.get(element_name)
            if element:
                success = self.game_logic.player.magic_system.add_element(element)
                if not success:
                    print(f"❌ Element-Maximum erreicht!")
    
    def handle_cast_magic(self):
        """Behandelt Magie wirken"""
        if self.game_logic and self.game_logic.player:
            # Feindesliste für Magie-Effekte bereitstellen
            enemies = []
            if self.enemy_manager:
                enemies = list(self.enemy_manager.enemies)
                
            # target_pos wird jetzt ignoriert, da Projektile in Blickrichtung fliegen
            result = self.game_logic.player.magic_system.cast_magic(
                caster=self.game_logic.player,
                target_pos=None,  # Wird ignoriert für Projektile
                enemies=enemies
            )
    
    def handle_clear_magic(self):
        """Behandelt Magie-Auswahl löschen"""
        if self.game_logic and self.game_logic.player:
            self.game_logic.player.magic_system.clear_elements()
    
    def _setup_health_bars(self):
        """Private Methode zum Neuerstellen der Health-Bars nach Reset"""
        # Player Health-Bar hinzufügen
        if self.game_logic and self.game_logic.player:
            player_health_bar = create_player_health_bar(
                self.game_logic.player,
                width=100,
                height=12,
                offset_y=-35,
                show_when_full=True
            )
            self.health_bar_manager.add_entity(
                self.game_logic.player, 
                renderer=player_health_bar.renderer,
                width=player_health_bar.width,
                height=player_health_bar.height,
                offset_y=player_health_bar.offset_y,
                show_when_full=player_health_bar.show_when_full
            )
        
        # Health-Bars für alle Feinde hinzufügen
        if self.enemy_manager:
            for enemy in self.enemy_manager.enemies:
                self.add_enemy_health_bar(enemy)
        
        print("🔄 Health-Bars neu erstellt")
    
    def run(self, dt):
        """Haupt-Update-Methode für das Level"""
        self.update(dt)
        self.render()
