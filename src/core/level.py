# -*- coding: utf-8 -*-
# src/level.py
import pygame
from os import path
import math  # Füge den math import hinzu
from settings import *
from game import Game as GameLogic
from camera import Camera
from map_loader import MapLoader
from enemy_manager import EnemyManager
from health_bar_py27 import HealthBarManager, create_player_health_bar, create_enemy_health_bar
from input_system import get_input_system

class GameRenderer:
    """🚀 Task 6: Rendering-System mit Alpha/Transparenz-Optimierung"""
    
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.Font(None, 50)
        self.small_font = pygame.font.Font(None, 36)
        self.generate_ground_stones()
        
        # Performance-Optimierung: Asset Manager für gecachte Sprite-Skalierung
        from asset_manager import AssetManager
        self.asset_manager = AssetManager()
        
        # 🚀 Task 6: Alpha-Caching für transparente Effekte (Performance-Optimierung)
        self._alpha_cache = {}  # Cache für transparente Surfaces
        self._max_alpha_cache_size = 50  # Begrenzt Memory-Verbrauch
        
    def generate_ground_stones(self):
        """🚀 Task 5: Generiert zufällige Steine - Multi-Resolution-kompatibel"""
        import random
        self.stones = []
        # 🚀 Task 5: Dynamische Screen-Größen
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()
        world_width = screen_width * 3
        
        for _ in range(200):
            x = random.randint(-world_width // 2, world_width // 2)
            y = random.randint(screen_height - 200 + 10, screen_height - 20)
            size = random.randint(3, 12)
            gray = random.randint(80, 140)
            color = (gray, gray, gray)
            
            self.stones.append({
                'x': x, 'y': y, 'size': size, 'color': color
            })
    
    def _get_cached_transparent_sprite(self, original_surface, alpha_value, size):
        """🚀 Task 6: Erstellt gecachte transparente Sprite-Versionen für bessere Performance"""
        cache_key = (id(original_surface), alpha_value, size)
        
        # Cache-Hit: Bereits erstellte transparente Version zurückgeben
        if cache_key in self._alpha_cache:
            return self._alpha_cache[cache_key]
        
        # Cache-Miss: Neue transparente Version erstellen
        if len(self._alpha_cache) >= self._max_alpha_cache_size:
            # Ältesten Cache-Eintrag entfernen (einfaches FIFO)
            oldest_key = next(iter(self._alpha_cache))
            del self._alpha_cache[oldest_key]
        
        # Skaliere erst das Original (mit vorhandenem Cache)
        scaled_image = self.asset_manager.get_scaled_sprite(original_surface, size)
        
        # Erstelle transparente Version
        transparent_surface = pygame.Surface(size, pygame.SRCALPHA)
        transparent_surface.blit(scaled_image, (0, 0))
        transparent_surface.set_alpha(alpha_value)
        
        # Cache die transparente Version
        self._alpha_cache[cache_key] = transparent_surface
        return transparent_surface
    
    def get_alpha_cache_info(self):
        """🚀 Task 6: Debug-Info für Alpha-Cache"""
        return {
            'size': len(self._alpha_cache),
            'max_size': self._max_alpha_cache_size,
            'memory_usage': len(self._alpha_cache) * 50  # Geschätzt KB pro Entry
        }
    
    def draw_background(self, map_loader=None, camera=None):
        """🚀 Task 5: Zeichnet den Hintergrund - Multi-Resolution-kompatibel"""
        if map_loader and camera and map_loader.tmx_data:
            self.screen.fill((0, 0, 0))  # Schwarzer Hintergrund für besseren Kontrast
            map_loader.render(self.screen, camera)
        else:
            self.screen.fill(BACKGROUND_COLOR)
            # 🚀 Task 5: Standard-Hintergrund mit dynamischen Größen
            screen_width = self.screen.get_width()
            screen_height = self.screen.get_height()
            tree_rect = pygame.Rect(0, screen_height - 400, screen_width, 200)
            pygame.draw.rect(self.screen, (34, 139, 34), tree_rect)
            ground_rect = pygame.Rect(0, screen_height - 200, screen_width, 200)
            pygame.draw.rect(self.screen, (139, 69, 19), ground_rect)
    
    def draw_ground_stones(self, camera):
        """🚀 Task 5: Zeichnet Steine mit Kamera-Transformation - Multi-Resolution"""
        screen_width = self.screen.get_width()  # 🚀 Task 5: Dynamische Screen-Breite
        for stone in self.stones:
            stone_rect = pygame.Rect(stone['x'], stone['y'], stone['size'], stone['size'])
            stone_pos = camera.apply_rect(stone_rect)
            
            if -50 < stone_pos.x < screen_width + 50:
                scaled_size = int(stone['size'] * camera.zoom_factor)
                pygame.draw.circle(self.screen, stone['color'], 
                                 (int(stone_pos.x + scaled_size//2), 
                                  int(stone_pos.y + scaled_size//2)), 
                                 max(1, scaled_size//2))
    
    def draw_player(self, player, camera):
        """🚀 Task 6: Zeichnet den Spieler - Alpha-optimiert für bessere Performance"""
        # Prüfe Unsichtbarkeit
        if hasattr(player, 'magic_system') and player.magic_system.is_invisible(player):
            # 🚀 Task 6: Nutze Alpha-Cache für unsichtbare Spieler
            if hasattr(player, 'image') and player.image:
                player_pos = camera.apply(player)
                # Nutze optimierte Alpha-Caching statt per-Frame Surface-Erstellung
                transparent_sprite = self._get_cached_transparent_sprite(
                    player.image, 80, (player_pos.width, player_pos.height)
                )
                self.screen.blit(transparent_sprite, (player_pos.x, player_pos.y))
            else:
                # 🚀 Task 6: Transparenter Fallback mit Alpha-Cache-Pattern
                player_pos = camera.apply(player)
                # Erstelle einfachen transparenten Rechteck-Cache (für Fallback)
                fallback_key = ('fallback_transparent_rect', player_pos.width, player_pos.height, 80)
                if fallback_key not in self._alpha_cache:
                    transparent_surface = pygame.Surface((player_pos.width, player_pos.height), pygame.SRCALPHA)
                    pygame.draw.rect(transparent_surface, (255, 255, 0, 80), (0, 0, player_pos.width, player_pos.height))
                    self._alpha_cache[fallback_key] = transparent_surface
                self.screen.blit(self._alpha_cache[fallback_key], (player_pos.x, player_pos.y))
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
                
                # 🚀 Task 6: Schild-Effekt mit Low-Effects-Mode (RPi4-Optimierung)
                if hasattr(player, 'magic_system') and player.magic_system.is_shielded(player):
                    from config import DisplayConfig
                    settings = DisplayConfig.get_optimized_settings()
                    
                    if settings.get('LOW_EFFECTS', False):
                        # 🚀 RPi4: Einfacher Schild-Kreis ohne Animation
                        shield_center = (player_pos.centerx, player_pos.centery)
                        pygame.draw.circle(self.screen, (100, 150, 255), shield_center, 
                                         int(player_pos.width // 2 + 10), 3)
                    else:
                        # PC: Animierter Schild mit Pulsierender Effekt
                        import math
                        shield_center = (player_pos.centerx, player_pos.centery)
                        current_time = pygame.time.get_ticks()
                        pulse = abs(math.sin(current_time * 0.01)) * 10 + 5
                        pygame.draw.circle(self.screen, (100, 150, 255), shield_center, 
                                         int(player_pos.width // 2 + pulse), 3)
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
        
        # Zutaten-Symbole und Namen
        zutaten_farben = {
            "wasserkristall": (0, 150, 255),
            "feueressenz": (255, 100, 0),
            "erdkristall": (139, 69, 19),
            "holzstab": (139, 69, 19),
            "stahlerz": (169, 169, 169),
            "mondstein": (200, 200, 255)
        }
        
        start_x = 50
        for i, zutat in enumerate(game_logic.aktive_zutaten):
            color = zutaten_farben.get(zutat, (200, 200, 200))
            rect_x = start_x + i * 70
            # Zeichne Gegenstand-Symbol
            pygame.draw.rect(self.screen, color, (rect_x, y_offset, 50, 50))
            
            # Zeichne Namen darunter
            item_name = zutat.capitalize()
            name_surface = self.small_font.render(item_name, True, TEXT_COLOR)
            name_rect = name_surface.get_rect(centerx=rect_x + 25, top=y_offset + 55)
            self.screen.blit(name_surface, name_rect)
        
        y_offset += 70
        
        # Magie-System UI (falls Player verfügbar)
        if hasattr(game_logic, 'player') and game_logic.player:
            self.draw_magic_ui(game_logic.player, 40, y_offset)
            y_offset += 80
        
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
        """🚀 Task 5: Zeichnet die Steuerungshinweise - Multi-Resolution-optimiert"""
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
        
        # 🚀 Task 5: Dynamische Screen-Größen statt Konstanten
        screen_height = self.screen.get_height()
        screen_width = self.screen.get_width()
        start_y = screen_height - 380  # Mehr Platz für zusätzliche Zeilen
        for i, control in enumerate(controls):
            color = TEXT_COLOR if i > 0 else (255, 255, 0)
            # Magie-Titel hervorheben
            if control.startswith("🔮"):
                color = (150, 255, 255)
            # Speicher-Titel hervorheben
            elif control.startswith("💾"):
                color = (255, 200, 100)
            control_surface = self.small_font.render(control, True, color)
            self.screen.blit(control_surface, (screen_width - 350, start_y + i * 23))
    
    def draw_magic_ui(self, player, x, y):
        """Zeichnet die Magie-System UI mit Mana-Anzeige"""
        magic_system = player.magic_system
        
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
        
        # Mana-Anzeige
        mana_text = f"Mana: {int(player.current_mana)}/{player.max_mana}"
        mana_surface = self.small_font.render(mana_text, True, (100, 100, 255))
        self.screen.blit(mana_surface, (x, y + 60))
        
        # Mana-Balken
        bar_width = 120
        bar_height = 8
        bar_x = x + 120
        bar_y = y + 65
        
        # Hintergrund (schwarz)
        pygame.draw.rect(self.screen, (0, 0, 0), (bar_x, bar_y, bar_width, bar_height))
        
        # Mana-Füllstand (blau)
        fill_width = int(bar_width * player.get_mana_percentage())
        if fill_width > 0:
            pygame.draw.rect(self.screen, (50, 150, 255), (bar_x, bar_y, fill_width, bar_height))

    def render_entities_with_depth(self, player, enemies, depth_objects, camera):
        """🎮 Fake-3D: Rendert alle Entities nach Y-Position sortiert"""
        entities = []
        
        # Player hinzufügen
        entities.append({
            'type': 'player',
            'entity': player,
            'y_bottom': player.rect.bottom,
            'render_func': lambda: self.draw_player(player, camera)
        })
        
        # Enemies hinzufügen
        if enemies:
            for enemy in enemies:
                entities.append({
                    'type': 'enemy', 
                    'entity': enemy,
                    'y_bottom': enemy.rect.bottom,
                    'render_func': lambda e=enemy: self.draw_enemy(e, camera)
                })
        
        # Depth-Objekte aus der Map hinzufügen
        if depth_objects:
            for obj in depth_objects:
                entities.append({
                    'type': 'depth_object',
                    'entity': obj,
                    'y_bottom': obj['y_bottom'],
                    'render_func': lambda o=obj: self.draw_depth_object(o, camera)
                })
        
        # Nach Y-Position sortieren (je weiter unten, desto später gerendert = vor anderen Objekten)
        entities.sort(key=lambda x: x['y_bottom'])
        
        # Alle Entities in der richtigen Reihenfolge rendern
        for entity_data in entities:
            entity_data['render_func']()
    
    def render_with_foreground_layer(self, player, enemies, depth_objects, camera, map_loader):
        """🎮 Rendert mit separatem Foreground-Layer"""
        
        # 1. Normale Depth-Sorting (Player + Enemies + Depth-Objects)
        entities = []
        
        # Player hinzufügen
        entities.append({
            'type': 'player',
            'entity': player,
            'y_bottom': player.rect.bottom,
            'render_func': lambda: self.draw_player(player, camera)
        })
        
        # Enemies hinzufügen
        if enemies:
            for enemy in enemies:
                entities.append({
                    'type': 'enemy',
                    'entity': enemy,
                    'y_bottom': enemy.rect.bottom,
                    'render_func': lambda e=enemy: self.draw_enemy(e, camera)
                })
        
        # Depth-Objekte hinzufügen
        if depth_objects:
            for obj in depth_objects:
                entities.append({
                    'type': 'depth_object',
                    'entity': obj,
                    'y_bottom': obj['y_bottom'],
                    'render_func': lambda o=obj: self.draw_depth_object(o, camera)
                })
        
        # Nach Y-Position sortieren
        entities.sort(key=lambda x: x['y_bottom'])
        
        # 2. Alle sortierten Entities rendern
        for entity_data in entities:
            entity_data['render_func']()
        
        # 3. Foreground-Layer rendern (ÜBER ALLEM!)
        if map_loader and hasattr(map_loader, 'render_foreground'):
            map_loader.render_foreground(self.screen, camera)
    
    def draw_depth_object(self, obj, camera):
        """Zeichnet ein Depth-Objekt aus der Map"""
        # Kamera-Transformation anwenden
        screen_rect = camera.apply_rect(obj['rect'])
        
        # Prüfe ob Objekt im sichtbaren Bereich ist
        if (screen_rect.right < 0 or screen_rect.left > self.screen.get_width() or 
            screen_rect.bottom < 0 or screen_rect.top > self.screen.get_height()):
            return
        
        # Verschiedene Objekt-Typen zeichnen
        obj_name = obj['name'].lower()
        
        if 'tree' in obj_name:
            self.draw_tree_object(screen_rect, obj)
        elif 'rock' in obj_name or 'stone' in obj_name:
            self.draw_rock_object(screen_rect, obj)
        elif 'building' in obj_name or 'house' in obj_name:
            self.draw_building_object(screen_rect, obj)
        elif 'fence' in obj_name:
            self.draw_fence_object(screen_rect, obj)
        else:
            # Fallback: Einfaches Rechteck
            pygame.draw.rect(self.screen, obj['color'], screen_rect)
            pygame.draw.rect(self.screen, (0, 0, 0), screen_rect, 2)  # Rahmen
    
    def draw_tree_object(self, screen_rect, obj):
        """Zeichnet einen Baum"""
        # Stamm (untere 40% der Höhe)
        trunk_height = int(screen_rect.height * 0.4)
        trunk_width = int(screen_rect.width * 0.3)
        trunk_rect = pygame.Rect(
            screen_rect.centerx - trunk_width // 2,
            screen_rect.bottom - trunk_height,
            trunk_width,
            trunk_height
        )
        pygame.draw.rect(self.screen, (101, 67, 33), trunk_rect)  # Braun
        
        # Krone (obere 80% der Höhe, überlappend)
        crown_height = int(screen_rect.height * 0.8)
        crown_width = int(screen_rect.width * 0.9)
        crown_rect = pygame.Rect(
            screen_rect.centerx - crown_width // 2,
            screen_rect.top,
            crown_width,
            crown_height
        )
        pygame.draw.ellipse(self.screen, (34, 139, 34), crown_rect)  # Grün
        
        # Schatten-Effekt
        shadow_rect = crown_rect.copy()
        shadow_rect.inflate_ip(-4, -4)
        pygame.draw.ellipse(self.screen, (0, 100, 0), shadow_rect, 3)
    
    def draw_rock_object(self, screen_rect, obj):
        """Zeichnet einen Stein/Felsen"""
        # Hauptstein
        pygame.draw.ellipse(self.screen, (105, 105, 105), screen_rect)
        # Highlight
        highlight_rect = screen_rect.copy()
        highlight_rect.width //= 3
        highlight_rect.height //= 3
        pygame.draw.ellipse(self.screen, (169, 169, 169), highlight_rect)
        # Schatten
        pygame.draw.ellipse(self.screen, (64, 64, 64), screen_rect, 2)
    
    def draw_building_object(self, screen_rect, obj):
        """Zeichnet ein Gebäude"""
        # Hauptgebäude
        pygame.draw.rect(self.screen, (139, 69, 19), screen_rect)
        
        # Dach (Dreieck oben)
        roof_points = [
            (screen_rect.centerx, screen_rect.top - 20),
            (screen_rect.left - 10, screen_rect.top),
            (screen_rect.right + 10, screen_rect.top)
        ]
        pygame.draw.polygon(self.screen, (160, 82, 45), roof_points)
        
        # Fenster (falls groß genug)
        if screen_rect.width > 40 and screen_rect.height > 40:
            window_size = min(screen_rect.width // 4, screen_rect.height // 4)
            window_rect = pygame.Rect(
                screen_rect.left + window_size,
                screen_rect.top + window_size,
                window_size,
                window_size
            )
            pygame.draw.rect(self.screen, (135, 206, 235), window_rect)  # Hellblau
    
    def draw_fence_object(self, screen_rect, obj):
        """Zeichnet einen Zaun"""
        # Horizontale Balken
        rail_height = screen_rect.height // 4
        for i in range(3):
            rail_y = screen_rect.top + i * rail_height + rail_height // 2
            pygame.draw.rect(self.screen, (160, 82, 45), 
                           (screen_rect.left, rail_y, screen_rect.width, rail_height // 2))
        
        # Vertikale Pfosten
        post_width = screen_rect.width // 8
        for i in range(0, screen_rect.width, screen_rect.width // 4):
            post_x = screen_rect.left + i
            pygame.draw.rect(self.screen, (101, 67, 33),
                           (post_x, screen_rect.top, post_width, screen_rect.height))
    
    def draw_enemy(self, enemy, camera):
        """Zeichnet einen Feind (erweitert falls nötig)"""
        # Deine existierende Enemy-Render-Logik hier
        enemy_pos = camera.apply(enemy)
        if hasattr(enemy, 'image') and enemy.image:
            scaled_image = self.asset_manager.get_scaled_sprite(
                enemy.image, (enemy_pos.width, enemy_pos.height)
            )
            self.screen.blit(scaled_image, (enemy_pos.x, enemy_pos.y))
        else:
            # Fallback
            pygame.draw.rect(self.screen, (255, 0, 0), enemy_pos)
    
class Level:
    """Hauptspiel-Level - Verwaltet Gameplay-Zustand"""
    
    def __init__(self, screen, main_game=None):
        self.screen = screen  # Verwende die übergebene Surface
        self.main_game = main_game  # Reference to main game for spell bar access
        self.game_logic = GameLogic()
        
        # Debug-Attribute für Koordinatenanzeige (nur Initialisierung)
        self.show_coordinates = True
        self.debug_font = pygame.font.Font(None, 24)  # Dies ist okay, da Font keine Video-Initialisierung benötigt

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

        # Interaktionszonen hinzufügen
        # Debug-Ausgabe für Initialisierung
        print("Initialisiere Interaktionszonen...")
        self.interaction_zones = {
            'elara_dialog': {
                'pos': pygame.math.Vector2(1580, 188),
                'radius': 150,
                'text': 'Elara (Nachbarin): "Lumo ist ins Dorf gerannt - aber die Brücke ist eingestürzt! Repariere sie, sonst kommst du nicht hinüber!"',
                'active': False,
                'is_checkpoint': True,  # Markiere als Checkpoint
                'required_items': ['stahlerz', 'holzstab'],  # Benötigte Gegenstände
                'completion_text': 'Du hast alle Gegenstände gefunden und die Brücke repariert!',
                'completed': False
            }
        }
        print(f"Interaktionszone erstellt bei Position: {self.interaction_zones['elara_dialog']['pos']}")
    
        self.show_interaction_text = False
        self.interaction_text = ""
        self.interaction_font = pygame.font.Font(None, 32)  # Schriftgröße angepasst für bessere Lesbarkeit

        # Neues System für Questgegenstände/Sammelitems
        self.quest_items = []  # Liste der gesammelten Questgegenstände
        self.collectible_items = {
            # Gegenstände auf dieser Map
            'holzstab': {
                'pos': pygame.math.Vector2(27, 59),
                'name': 'Holzstab',
                'collected': False,
                'radius': 50,
                'color': (139, 69, 19),  # Braun
                'available': True  # Gegenstand ist auf dieser Map verfügbar
            },
            'stahlerz': {
                'pos': pygame.math.Vector2(3056, 39),
                'name': 'Stahlerz',
                'collected': False,
                'radius': 50,
                'color': (169, 169, 169),  # Silber
                'available': True
            },
            'mondstein': {
                'pos': pygame.math.Vector2(2296, 913),
                'name': 'Mondstein',
                'collected': False,
                'radius': 50,
                'color': (200, 200, 255),  # Bläulich-weiß
                'available': True
            },
            # Vorbereitete Gegenstände für spätere Maps
            'kristallsplitter': {
                'name': 'Kristallsplitter',
                'collected': False,
                'color': (173, 216, 230),  # Hellblau
                'available': False  # Noch nicht auf dieser Map verfügbar
            },
            'goldener_reif': {
                'name': 'Goldener Reif',
                'collected': False,
                'color': (255, 215, 0),  # Gold
                'available': False
            }
        }
        
        # Füge Attribute für die Sammel-Nachricht hinzu
        self.collection_message = ""
        self.collection_message_timer = 0
        self.collection_message_duration = 3000  # 3 Sekunden Anzeigedauer

        # Map-Progression System
        self.current_map_index = 0
        self.map_progression = [
            "Map3.tmx",        # 1. Map: Map3 
            "Map_Village.tmx"  # 2. Map: Map_Village nach Abschluss
        ]
        self.map_completed = False
    def load_map(self):
        """Lädt die Spielkarte und extrahiert Spawn-Punkte"""
        try:
            map_path = path.join(MAP_DIR, "Map3.tmx")  # ✅ Zurück zu Map3 als Start-Map
            
            self.map_loader = MapLoader(map_path)
            
            if self.map_loader and self.map_loader.tmx_data:
                self.use_map = True
                print(f"✅ Map geladen: {map_path}")
                
                # Debug: Zeige alle verfügbaren Layer
                print("🗂️ Verfügbare Layer:")
                for layer in self.map_loader.tmx_data.visible_layers:
                    layer_type = "Objekt" if hasattr(layer, 'objects') else "Tile"
                    object_count = len(layer.objects) if hasattr(layer, 'objects') else 0
                    print(f"  - {layer.name or 'None'} ({layer_type}) - {object_count} Objekte")
            
                # Datengesteuertes Spawning: Spieler-Position aus Tiled-Map extrahieren
                self.spawn_entities_from_map()
                
            else:
                self.map_loader = None
                self.use_map = False
                # Fallback: Standard-Position (nur wenn keine Map)
                self.game_logic.player.rect.bottom = self.screen.get_height() - 200
                self.game_logic.player.rect.centerx = self.screen.get_width() // 2
                self.game_logic.player.update_hitbox()
                print("⚠️ Map konnte nicht geladen werden - Standard-Position verwendet")
                
        except Exception as e:
            print(f"❌ Fehler beim Laden der Map: {e}")
            if self.map_loader and self.map_loader.tmx_data:
                self.use_map = True
            else:
                self.map_loader = None
                self.use_map = False
                # Fallback: Standard-Position (nur wenn Map fehlschlägt)
                self.game_logic.player.rect.bottom = self.screen.get_height() - 200
                self.game_logic.player.rect.centerx = self.screen.get_width() // 2
                self.game_logic.player.update_hitbox()
                print("⚠️ Fallback auf Standard-Position")
    
    def spawn_entities_from_map(self):
        """Lädt Entities aus der Map oder verwendet Fallback"""
        if not self.map_loader or not self.map_loader.tmx_data:
            return

        player_spawned = False

        # Durchsuche alle Objekt-Layer nach Spawn-Punkten
        for layer in self.map_loader.tmx_data.visible_layers:
            if hasattr(layer, 'objects'):  # Objekt-Layer
                print(f"🔍 Prüfe Objekt-Layer: {layer.name}")
                for obj in layer.objects:
                    print(f"  - Objekt gefunden: '{obj.name}' bei ({obj.x}, {obj.y})")
                    
                    # Player Spawn-Punkt - erweiterte Erkennung
                    if obj.name and obj.name.lower() in ['player', 'spawn', 'player_spawn', 'start']:
                        # Korrigiere negative Koordinaten für Map_Village
                        spawn_x = obj.x
                        spawn_y = obj.y
                        
                        # Prüfe ob Koordinaten außerhalb des gültigen Bereichs sind
                        map_width = self.map_loader.tmx_data.width * self.map_loader.tmx_data.tilewidth
                        map_height = self.map_loader.tmx_data.height * self.map_loader.tmx_data.tileheight
                        
                        if spawn_x < 0 or spawn_y < 0 or spawn_x > map_width or spawn_y > map_height:
                            print(f"⚠️ Spawn-Position ({spawn_x}, {spawn_y}) ist außerhalb der Map (0,0 - {map_width},{map_height})")
                            # Korrigiere zu gültiger Position in der Mitte der Map
                            spawn_x = map_width // 2
                            spawn_y = map_height // 2
                            print(f"🔧 Korrigiert zu Map-Mitte: ({spawn_x}, {spawn_y})")
                        
                        self.game_logic.player.rect.centerx = spawn_x
                        self.game_logic.player.rect.centery = spawn_y
                        self.game_logic.player.update_hitbox()
                        player_spawned = True
                        print(f"✅ Player gespawnt bei ({spawn_x}, {spawn_y}) von Objekt '{obj.name}'")
                        break
                    
                    # Enemy Spawns
                    elif obj.name and 'enemy' in obj.name.lower():
                        print(f"🎯 Enemy-Spawn gefunden: {obj.name} bei ({obj.x}, {obj.y})")
                        # Enemy-Spawning wird vom EnemyManager gehandhabt
            
                if player_spawned:
                    break  # Stoppe die Suche nach dem ersten gefundenen Player-Spawn

        # Fallback falls kein Spawn-Punkt gefunden
        if not player_spawned:
            print("⚠️ Kein Player-Spawn in Map gefunden - verwende Standard-Position")
            
            # Spezielle Behandlung für bekannte Maps
            if hasattr(self.map_loader, 'tmx_data') and self.map_loader.tmx_data:
                map_filename = str(getattr(self.map_loader.tmx_data, 'filename', ''))
                
                # Berechne Map-Dimensionen
                map_width = self.map_loader.tmx_data.width * self.map_loader.tmx_data.tilewidth
                map_height = self.map_loader.tmx_data.height * self.map_loader.tmx_data.tileheight
                
                if 'Map_Village.tmx' in map_filename:
                    # Map_Village: 80x80 Tiles = 2560x2560 Pixel - spawn in der Mitte
                    spawn_x = map_width // 2  # 1280
                    spawn_y = map_height // 2  # 1280
                    self.game_logic.player.rect.centerx = spawn_x
                    self.game_logic.player.rect.centery = spawn_y
                    self.game_logic.player.update_hitbox()
                    print(f"✅ Player in Mitte von Map_Village gespawnt ({spawn_x}, {spawn_y})")
                else:
                    # Standard-Spawn für andere Maps
                    self.game_logic.player.rect.centerx = 800
                    self.game_logic.player.rect.centery = 400
                    self.game_logic.player.update_hitbox()
                    print("✅ Standard-Spawn verwendet (800, 400)")

        # Enemy-Spawning delegieren an EnemyManager
        self.enemy_manager.add_enemies_from_map(self.map_loader)
    
    def respawn_enemies_only(self):
        """Spawnt nur die Feinde neu, ohne die Spieler-Position zu verändern"""
        if not self.map_loader or not self.map_loader.tmx_data:
            return
        
        # Demons aus der Map spawnen
        self.enemy_manager.add_enemies_from_map(self.map_loader)
        
        # FALLBACK: Falls keine Gegner aus Map geladen wurden
        if len(self.enemy_manager.enemies) == 0:
            print("⚠️ Keine Gegner aus Map geladen - verwende Test-Gegner")
            self.enemy_manager.respawn_default_enemies()
    
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
            elif event.key == pygame.K_F5:
                self.show_coordinates = not self.show_coordinates
                print(f"Koordinatenanzeige: {'An' if self.show_coordinates else 'Aus'}")

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
        """Aktualisiert das Level und alle Entities"""
        if not self.game_logic:
            return
        
        # Game Logic Update
        self.game_logic.update(dt)
        
        # Feinde aktualisieren
        self.enemy_manager.update(dt, self.game_logic.player)
        
        # Kamera aktualisieren
        if hasattr(self.game_logic, 'player'):
            self.camera.update(self.game_logic.player)
        
        # Health-Bars aktualisieren
        self.health_bar_manager.update(dt)
        
        # Interaktionszonen prüfen
        self.check_interaction_zones()
        
        # ✅ NEU: Level-Abschluss prüfen
        self.check_level_completion()
    
    def check_interaction_zones(self):
        """Überprüft ob der Spieler in der Nähe einer Interaktionszone ist"""
        if not self.game_logic or not self.game_logic.player:
            return

        player_pos = pygame.math.Vector2(self.game_logic.player.rect.center)
        self.show_interaction_text = False

        for zone_id, zone in self.interaction_zones.items():
            distance = player_pos.distance_to(zone['pos'])

            if distance <= zone['radius']:
                zone['active'] = True
                
                # Debug-Ausgabe um zu sehen welche Items wir haben
                print(f"Aktuelle Quest-Items: {self.quest_items}")
                print(f"Benötigte Items: {zone.get('required_items', [])}")
                
                # Prüfe ob dies ein Checkpoint ist
                if zone.get('is_checkpoint', False) and not zone.get('completed', False):
                    required_items = set(zone.get('required_items', []))
                    collected_items = set(self.quest_items)
                    
                    # Debug-Ausgabe für Item-Überprüfung
                    print(f"Prüfe Items - Benötigt: {required_items}, Gesammelt: {collected_items}")
                    
                    if required_items.issubset(collected_items):
                        print("Alle benötigten Items gefunden!")
                        # Alle Items vorhanden - zeige Abschlusstext
                        self.show_interaction_text = True
                        self.interaction_text = zone['completion_text']
                        zone['completed'] = True
                        
                        # Speichere das Spiel und kehre zum Hauptmenü zurück
                        print("Starte Level-Abschluss...")
                        self.trigger_level_completion()
                    else:
                        # Nicht alle Items vorhanden - zeige normalen Dialog
                        self.show_interaction_text = True
                        self.interaction_text = zone['text']
                        print(f"Noch nicht alle Items gefunden. Fehlende Items: {required_items - collected_items}")
                else:
                    # Normale Interaktionszone oder bereits abgeschlossen
                    self.show_interaction_text = True
                    self.interaction_text = zone.get('text', '')
                break
            else:
                zone['active'] = False

    def update(self, dt):
        """Update-Schleife mit Delta Time"""
        # Universal Input System updaten
        self.input_system.update()
        
        # Bewegung verarbeiten
        if self.game_logic and self.game_logic.player:
            # Hole Bewegungsvektor vom Input System
            direction = pygame.math.Vector2(0, 0)
            
            # Tastatur-Input verarbeiten
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                direction.x = -1
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                direction.x = 1
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                direction.y = -1
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                direction.y = 1
                
            # Normalisiere den Vektor für diagonale Bewegung
            if direction.length() > 0:
                direction = direction.normalize()
            
            # Setze die Bewegungsrichtung im Player
            self.game_logic.player.direction = direction
            
            # Führe die Bewegung aus
            self.game_logic.player.move(dt)
    
        # Rest des Update-Codes...
        game_result = self.game_logic.update(dt, enemies=list(self.enemy_manager.enemies) if self.enemy_manager else [])
        
        if game_result == "game_over":
            return "game_over"
        
        # Magic System updaten
        if self.game_logic and self.game_logic.player and hasattr(self.game_logic.player, 'magic_system'):
            enemies_list = list(self.enemy_manager.enemies) if self.enemy_manager else []
            self.game_logic.player.magic_system.update(dt, enemies_list)
        
        # Demons updaten
        self.enemy_manager.update(dt, self.game_logic.player)
        
        # Health-Bar System updaten
        self.health_bar_manager.update(dt)
        
        # Kamera updaten
        self.camera.update(self.game_logic.player)
        
        # Prüfe Interaktionszonen
        self.check_interaction_zones()
        
        # Sammelbare Gegenstände überprüfen
        self.check_collectibles()
        
        # Update die Collection Message Timer
        if self.collection_message_timer > 0:
            self.collection_message_timer = max(0, self.collection_message_timer - pygame.time.get_ticks())
    
    def trigger_level_completion(self):
        """Wird aufgerufen wenn ein Level abgeschlossen ist - lädt nächste Map"""
        print("🎉 Level abgeschlossen!")
        
        # Markiere aktuelles Level als abgeschlossen
        self.map_completed = True
        
        # Prüfe ob es eine nächste Map gibt
        if self.current_map_index + 1 < len(self.map_progression):
            next_map_index = self.current_map_index + 1
            next_map_name = self.map_progression[next_map_index]
            
            print(f"🗺️ Lade nächste Map: {next_map_name}")
            
            # Level-Abschluss Nachricht anzeigen
            if hasattr(self, 'main_game') and self.main_game:
                if next_map_index == 1:  # Map_Village
                    self.main_game.show_message("🏆 Map3 abgeschlossen! Willkommen im Dorf!")
                else:
                    self.main_game.show_message(f"🏆 Level abgeschlossen! Nächste Map: {next_map_name}")
            
            # Wechsle zur nächsten Map
            self.load_next_map(next_map_name, next_map_index)
            
        else:
            print("🎊 Alle Maps abgeschlossen! Spiel beendet!")
            if hasattr(self, 'main_game') and self.main_game:
                self.main_game.show_message("🎊 Herzlichen Glückwunsch! Alle Maps abgeschlossen!")
            
            # Hier könntest du zum Hauptmenü zurückkehren oder Credits anzeigen
            # self.main_game.return_to_menu()
    
    def load_next_map(self, map_name, map_index=None):
        """Lädt die nächste Map in der Progression"""
        try:
            print(f"🔄 Wechsle zu Map: {map_name}")
            
            # Update Map-Index
            if map_index is not None:
                self.current_map_index = map_index
            
            # Neue Map laden
            map_path = path.join(MAP_DIR, map_name)
            self.map_loader = MapLoader(map_path)
            
            if self.map_loader and self.map_loader.tmx_data:
                self.use_map = True
                print(f"✅ Neue Map geladen: {map_path}")
                
                # Level-Status zurücksetzen
                self.map_completed = False
                
                # Spieler-Position für neue Map setzen
                self.spawn_entities_from_map()
                
                # Enemies für neue Map laden
                self.respawn_enemies_only()
                
                # Kollisionsobjekte neu aufbauen
                self.setup_collision_objects()
                
                # Health-Bars neu einrichten
                self.setup_health_bars()
                
                # Kamera zentrieren
                if hasattr(self.game_logic, 'player'):
                    self.camera.center_on_target(self.game_logic.player)
                
                print(f"🎮 Map-Wechsel zu {map_name} abgeschlossen!")
                
            else:
                print(f"❌ Fehler beim Laden von {map_name}")
                
        except Exception as e:
            print(f"❌ Fehler beim Map-Wechsel zu {map_name}: {e}")

    def render(self):
        """Rendering mit Foreground-Layer"""
        # 1. Hintergrund (immer zuerst)
        if self.use_map:
            self.renderer.draw_background(self.map_loader, self.camera)
        else:
            self.renderer.draw_background()
            self.renderer.draw_ground_stones(self.camera)
        
        # 2. Sammelbare Gegenstände (Boden-Layer)
        self.render_collectibles()
        
        # 3. 🎭 ENTITIES + FOREGROUND-LAYER
        enemies = list(self.enemy_manager.enemies) if self.enemy_manager else []
        depth_objects = getattr(self.map_loader, "depth_objects", []) if self.map_loader and hasattr(self.map_loader, "depth_objects") else []

        # Nutze das Foreground-Layer System
        self.renderer.render_with_foreground_layer(
            player=self.game_logic.player,
            enemies=enemies,
            depth_objects=depth_objects,
            camera=self.camera,
            map_loader=self.map_loader
        )
        
        # 4. Collection Message anzeigen
        if self.collection_message_timer > pygame.time.get_ticks():
            message_surface = self.debug_font.render(self.collection_message, True, (255, 255, 255))
            message_rect = message_surface.get_rect()
            message_rect.centerx = self.screen.get_width() // 2
            message_rect.centery = self.screen.get_height() // 2 - 50
            
            bg_rect = message_rect.inflate(20, 10)
            bg_surface = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
            pygame.draw.rect(bg_surface, (0, 0, 0, 128), bg_surface.get_rect())
            self.screen.blit(bg_surface, bg_rect)
            self.screen.blit(message_surface, message_rect)
        
        # 5. Magie-Projektile (über Foreground!)
        if self.game_logic and self.game_logic.player:
            self.game_logic.player.magic_system.draw_projectiles(self.screen, self.camera)
        
        # 6. Health-Bars (über allem)
        camera_offset = (self.camera.camera_rect.x, self.camera.camera_rect.y)
        self.health_bar_manager.draw_all(self.screen, camera_offset)
        
        # 7. UI und Debug (immer oben)
        if hasattr(self, 'show_collision_debug') and self.show_collision_debug:
            self.renderer.draw_collision_debug(self.game_logic.player, self.camera, 
                                             self.map_loader.collision_objects if self.map_loader else [])
            self.enemy_manager.draw_debug(self.screen, self.camera)
        
        self.renderer.draw_ui(self.game_logic)
        if self.show_coordinates:
            self.render_coordinates()
        self.renderer.draw_controls()
        
        if self.show_interaction_text:
            self.render_interaction_text()
    
    def check_collectibles(self):
        """Überprüft ob der Spieler sammelbare Gegenstände einsammelt"""
        if not self.game_logic or not self.game_logic.player:
            return

        player_pos = pygame.math.Vector2(self.game_logic.player.rect.center)
        
        for item_id, item_data in self.collectible_items.items():
            # Prüfe nur Items die verfügbar und noch nicht gesammelt sind
            if not item_data.get('available', True) or item_data.get('collected', False):
                continue
            
            # Prüfe ob der Spieler nah genug ist
            if 'pos' in item_data:
                item_pos = item_data['pos']
                distance = player_pos.distance_to(item_pos)
                
                if distance <= item_data.get('radius', 50):
                    # Item einsammeln
                    item_data['collected'] = True
                    item_name = item_data.get('name', item_id)
                    
                    # Zur Quest-Items-Liste hinzufügen
                    if item_id not in self.quest_items:
                        self.quest_items.append(item_id)
                    
                    # Zur Spiel-Logik-Inventar hinzufügen (für UI-Anzeige)
                    if item_id not in self.game_logic.aktive_zutaten:
                        self.game_logic.aktive_zutaten.append(item_id)
                    
                    # Sammel-Nachricht anzeigen
                    self.collection_message = f"✅ {item_name} eingesammelt!"
                    self.collection_message_timer = pygame.time.get_ticks() + self.collection_message_duration
                    
                    print(f"✅ Item gesammelt: {item_name} ({item_id})")
                    print(f"Quest-Items: {self.quest_items}")
                    
                    # Sound-Effekt (optional)
                    try:
                        # Hier könntest du einen Sammel-Sound abspielen
                        pass
                    except:
                        pass
    
    def render_collectibles(self):
        """Rendert sammelbare Gegenstände auf der Map"""
        if not self.camera:
            return
        
        for item_id, item_data in self.collectible_items.items():
            # Nur verfügbare und noch nicht gesammelte Items rendern
            if not item_data.get('available', True) or item_data.get('collected', False):
                continue
            
            if 'pos' not in item_data:
                continue
            
            # Item-Position in Screen-Koordinaten umrechnen
            item_world_rect = pygame.Rect(
                item_data['pos'].x - 25,  # Hälfte der Item-Größe
                item_data['pos'].y - 25,
                50, 50
            )
            item_screen_rect = self.camera.apply_rect(item_world_rect)
            
            # Prüfe ob Item im sichtbaren Bereich ist
            if (item_screen_rect.right < 0 or item_screen_rect.left > self.screen.get_width() or
                item_screen_rect.bottom < 0 or item_screen_rect.top > self.screen.get_height()):
                continue
            
            # Item zeichnen
            item_color = item_data.get('color', (255, 255, 255))
            
            # Hauptkreis (Item)
            pygame.draw.circle(self.screen, item_color, item_screen_rect.center, 20)
            
            # Glanz-Effekt
            highlight_center = (item_screen_rect.centerx - 5, item_screen_rect.centery - 5)
            pygame.draw.circle(self.screen, (255, 255, 255), highlight_center, 8)
            
            # Rahmen
            pygame.draw.circle(self.screen, (0, 0, 0), item_screen_rect.center, 20, 2)
            
            # Pulsierender Effekt (optional)
            current_time = pygame.time.get_ticks()
            pulse = abs(math.sin(current_time * 0.005)) * 5 + 2
            pygame.draw.circle(self.screen, item_color, item_screen_rect.center, int(20 + pulse), 2)
            
            # Item-Name (falls nah genug am Spieler)
            if self.game_logic and self.game_logic.player:
                player_pos = pygame.math.Vector2(self.game_logic.player.rect.center)
                distance = player_pos.distance_to(item_data['pos'])
                
                if distance <= item_data.get('radius', 50) + 30:  # Etwas größerer Radius für Text
                    item_name = item_data.get('name', item_id)
                    name_surface = self.debug_font.render(item_name, True, (255, 255, 255))
                    name_rect = name_surface.get_rect(center=(item_screen_rect.centerx, item_screen_rect.top - 15))
                    
                    # Hintergrund für bessere Lesbarkeit
                    bg_rect = name_rect.inflate(10, 5)
                    bg_surface = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
                    pygame.draw.rect(bg_surface, (0, 0, 0, 128), bg_surface.get_rect())
                    self.screen.blit(bg_surface, bg_rect)
                    self.screen.blit(name_surface, name_rect)
    
    def render_coordinates(self):
        """Rendert Debug-Koordinaten des Spielers"""
        if not self.game_logic or not self.game_logic.player:
            return
        
        player = self.game_logic.player
        coords_text = f"Player: ({int(player.rect.centerx)}, {int(player.rect.centery)})"
        
        # Kamera-Position
        camera_text = f"Camera: ({int(self.camera.camera_rect.x)}, {int(self.camera.camera_rect.y)})"
        
        # Mausposition (falls verfügbar)
        mouse_pos = pygame.mouse.get_pos()
        world_mouse_x = mouse_pos[0] + self.camera.camera_rect.x
        world_mouse_y = mouse_pos[1] + self.camera.camera_rect.y
        mouse_text = f"Mouse: ({world_mouse_x}, {world_mouse_y})"
        
        # Texte rendern
        coord_surface = self.debug_font.render(coords_text, True, (255, 255, 0))
        camera_surface = self.debug_font.render(camera_text, True, (255, 255, 0))
        mouse_surface = self.debug_font.render(mouse_text, True, (255, 255, 0))
        
        # Position (oben rechts)
        screen_width = self.screen.get_width()
        
        self.screen.blit(coord_surface, (screen_width - 250, 10))
        self.screen.blit(camera_surface, (screen_width - 250, 35))
        self.screen.blit(mouse_surface, (screen_width - 250, 60))
    
    def render_interaction_text(self):
        """Rendert Interaktionstext wenn der Spieler in einer Interaktionszone ist"""
        if not self.show_interaction_text or not self.interaction_text:
            return
        
        # Mehrzeiligen Text aufteilen
        lines = []
        words = self.interaction_text.split(' ')
        current_line = ""
        max_width = self.screen.get_width() - 100  # Margin
        
        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            test_surface = self.interaction_font.render(test_line, True, (255, 255, 255))
            
            if test_surface.get_width() <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        # Hintergrund berechnen
        line_height = 35
        total_height = len(lines) * line_height + 20  # Padding
        max_line_width = max(self.interaction_font.render(line, True, (255, 255, 255)).get_width() for line in lines)
        bg_width = max_line_width + 40  # Padding
        
        # Position (mittig unten)
        bg_x = (self.screen.get_width() - bg_width) // 2
        bg_y = self.screen.get_height() - total_height - 50
        
        # Hintergrund zeichnen
        bg_surface = pygame.Surface((bg_width, total_height), pygame.SRCALPHA)
        pygame.draw.rect(bg_surface, (0, 0, 0, 200), bg_surface.get_rect())
        pygame.draw.rect(bg_surface, (255, 255, 255), bg_surface.get_rect(), 2)
        self.screen.blit(bg_surface, (bg_x, bg_y))
        
        # Text zeichnen
        for i, line in enumerate(lines):
            line_surface = self.interaction_font.render(line, True, (255, 255, 255))
            line_x = bg_x + (bg_width - line_surface.get_width()) // 2
            line_y = bg_y + 10 + i * line_height
            self.screen.blit(line_surface, (line_x, line_y))
    
    def handle_magic_element(self, element_name):
        """Behandelt Magie-Element-Eingabe"""
        if not self.game_logic or not self.game_logic.player:
            return
        
        from systems.magic_system import ElementType
        magic_system = self.game_logic.player.magic_system
        
        if element_name == 'water':
            magic_system.add_element(ElementType.WASSER)
        elif element_name == 'fire':
            magic_system.add_element(ElementType.FEUER)
        elif element_name == 'stone':
            magic_system.add_element(ElementType.STEIN)
    
    def handle_cast_magic(self):
        """Behandelt Magie-Zauber-Eingabe"""
        if not self.game_logic or not self.game_logic.player:
            return
        
        magic_system = self.game_logic.player.magic_system
        magic_system.cast_magic(self.game_logic.player)
    
    def handle_clear_magic(self):
        """Behandelt Magie-Elemente-Löschen"""
        if not self.game_logic or not self.game_logic.player:
            return
        
        magic_system = self.game_logic.player.magic_system
        magic_system.clear_elements()
    
    def add_enemies_from_map(self, map_loader):
        """Spawnt ALLE Gegner aus Tiled-Objekten auf allen passenden Ebenen."""
        if not map_loader or not map_loader.tmx_data:
            return
        
        pytmx_success = False
        
        # Versuche zuerst mit pytmx zu laden
        try:
            import pytmx
            # Dynamischer Pfad basierend auf map_loader
            map_path = getattr(map_loader, 'map_path', None)
            if not map_path:
                # Fallback für Map_Village
                map_path = r"d:\Jonas\Alchemist_SUI\assets\maps\Map_Village.tmx"  # ✅ Geändert
            
            tmx_data = pytmx.load_pygame(map_path, pixelalpha=True)
            pytmx_success = True
            
            # Durchlaufe alle Objekt-Layer in der Reihenfolge
            for layer in tmx_data.visible_layers:
                if isinstance(layer, pytmx.TiledObjectGroup):
                    for obj in layer:
                        # Spawne den Gegner an der Objekt-Position
                        enemy_type = obj.name.lower() if obj.name else "default_enemy"
                        print(f"Spawne {enemy_type} bei ({obj.x}, {obj.y})")
                        
                        # Nutze die EnemyManager Methode zum Spawnen
                        self.enemy_manager.spawn_enemy(enemy_type, obj.x, obj.y)
        
        except Exception as e:
            print(f"⚠️ Fehler beim Laden der Map mit pytmx: {e}")
        
        # Fallback: XML-Parsing nur wenn pytmx versagt
        if not pytmx_success:
            print("⚠️ pytmx failed, using XML fallback...")
            try:
                import xml.etree.ElementTree as ET
                # Dynamischer Pfad basierend auf map_loader
                map_path = getattr(map_loader, 'map_path', None)
                if not map_path:
                    # Fallback für Map_Village
                    map_path = r"d:\Jonas\Alchemist_SUI\assets\maps\Map_Village.tmx"  # ✅ Geändert
                
                tree = ET.parse(map_path)
                root = tree.getroot()
                
                # Durchlaufe alle Objekte in der XML
                for elem in root.iter('object'):
                    obj_name = elem.get('name')
                    obj_type = elem.get('type')
                    x = float(elem.get('x', 0))
                    y = float(elem.get('y', 0))
                    
                    # Spawne den Gegner an der Objekt-Position
                    enemy_type = obj_name.lower() if obj_name else "default_enemy"
                    print(f"Spawne {enemy_type} bei ({x}, {y})")
                    
                    # Nutze die EnemyManager Methode zum Spawnen
                    self.enemy_manager.spawn_enemy(enemy_type, x, y)
            
            except Exception as e:
                print(f"❌ Fehler beim XML-Parsing der Map: {e}")
    
    def check_level_completion(self):
        """Prüft ob die aktuellen Level-Ziele erreicht wurden"""
        if self.map_completed:
            return  # Bereits abgeschlossen
        
        current_map = self.map_progression[self.current_map_index]
        
        # Map3 Abschluss-Bedingungen
        if current_map == "Map3.tmx":
            # Beispiel-Bedingungen für Map3:
            # 1. Alle Enemies besiegt
            enemies_defeated = len(self.enemy_manager.enemies) == 0
            
            # 2. Spieler erreicht bestimmte Position (z.B. Ausgang)
            player_pos = (self.game_logic.player.rect.centerx, self.game_logic.player.rect.centery)
            exit_zone = pygame.Rect(2400, 1800, 200, 200)  # Beispiel-Ausgangszone für Map3
            player_at_exit = exit_zone.collidepoint(player_pos)
            
            # 3. Kombiniere Bedingungen
            if enemies_defeated and player_at_exit:
                print("🎯 Map3 Abschluss-Bedingungen erfüllt!")
                self.trigger_level_completion()
        
        # Map_Village Abschluss-Bedingungen  
        elif current_map == "Map_Village.tmx":
            # Beispiel-Bedingungen für Map_Village:
            # 1. Alle Enemies besiegt
            enemies_defeated = len(self.enemy_manager.enemies) == 0
            
            # 2. Bestimmte Interaktion abgeschlossen
            village_task_completed = True  # Hier deine spezifische Logik
            
            if enemies_defeated and village_task_completed:
                print("🎯 Map_Village Abschluss-Bedingungen erfüllt!")
                self.trigger_level_completion()
