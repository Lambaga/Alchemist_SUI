# -*- coding: utf-8 -*-
# src/level.py
import pygame
import os
from os import path
import math  # Füge den math import hinzu
from settings import *
from game import Game as GameLogic
from camera import Camera
from map_loader import MapLoader
from enemy_manager import EnemyManager
from health_bar_py27 import HealthBarManager, create_player_health_bar, create_enemy_health_bar
from input_system import get_input_system
from systems.pathfinding import GridPathfinder

class GameRenderer:
    """🚀 Task 6: Rendering-System mit Alpha/Transparenz-Optimierung"""
    
    def __init__(self, screen):
        self.screen = screen
        # Kompaktere Fonts für kleineres Overlay
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 22)  # Kleinere Schrift für Inventar-Items
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
        # UI-Hintergrund (kompakter)
        ui_rect = pygame.Rect(16, 16, 520, 260)
        pygame.draw.rect(self.screen, UI_BACKGROUND, ui_rect)
        pygame.draw.rect(self.screen, TEXT_COLOR, ui_rect, 3)
        
        # Innenabstände für Layout-Berechnung
        inner_left = ui_rect.x + 20
        inner_right = ui_rect.right - 20
        y_offset = ui_rect.y + 20

        # Helfer: Abstand für eine Reihe Slots berechnen, sodass bis zu N Elemente passen
        def compute_spacing(n_items: int, slot_size: int) -> int:
            n = max(1, n_items)
            total_slots = n * slot_size
            max_width = max(0, inner_right - inner_left)
            gaps = max(1, n - 1)
            # Mindestens 10px, höchstens 80px Abstand, restliche Breite gleichmäßig verteilen
            return max(10, min(80, (max_width - total_slots) // gaps if max_width > total_slots else 10))
        
        # Titel
        title = self.font.render(GAME_TITLE, True, TEXT_COLOR)
        self.screen.blit(title, (inner_left, y_offset))
        y_offset += 38
        
        # Punkte
        score_text = "Punkte: {}".format(game_logic.score)
        score_surface = self.font.render(score_text, True, TEXT_COLOR)
        self.screen.blit(score_surface, (inner_left, y_offset))
        y_offset += 30
        
        # Aktive Zutaten
        zutaten_text = "Inventar ({}/5):".format(len(game_logic.aktive_zutaten))
        zutaten_surface = self.font.render(zutaten_text, True, TEXT_COLOR)
        self.screen.blit(zutaten_surface, (inner_left, y_offset))
        y_offset += 28
        
        # Zutaten-Symbole und Namen
        zutaten_farben = {
            "wasserkristall": (0, 150, 255),
            "feueressenz": (255, 100, 0),
            "erdkristall": (139, 69, 19),
            "holzstab": (139, 69, 19),
            "stahlerz": (169, 169, 169),
            "mondstein": (200, 200, 255),
            "kristall": (160, 32, 240),  # Lila für Kristall
            "goldreif": (255, 215, 0)  # Gold für Goldreif
        }
        
        slot_size_main = 40
        # Bis zu 5 Items in einer Reihe sinnvoll einpassen
        n_main = max(1, min(5, len(game_logic.aktive_zutaten)))
        item_spacing = compute_spacing(n_main, slot_size_main)
        start_x = inner_left
        for i, zutat in enumerate(game_logic.aktive_zutaten[:5]):
            color = zutaten_farben.get(zutat, (200, 200, 200))
            rect_x = start_x + i * (slot_size_main + item_spacing)
            # Zeichne Gegenstand-Symbol
            pygame.draw.rect(self.screen, color, (rect_x, y_offset, slot_size_main, slot_size_main))
            
            # Zeichne Namen darunter
            item_name = zutat.capitalize()
            name_surface = self.small_font.render(item_name, True, TEXT_COLOR)
            name_rect = name_surface.get_rect(centerx=rect_x + slot_size_main // 2, top=y_offset + slot_size_main + 6)
            self.screen.blit(name_surface, name_rect)
        
        y_offset += slot_size_main + 30

        # Gesammelte Items (aus Level.quest_items / collectible_items)
        try:
            level_instance = getattr(game_logic, '_level_ref', None)
            collected_ids = []
            seen = set()
            if level_instance is not None:
                # Quest-Items Liste
                if hasattr(level_instance, 'quest_items') and isinstance(level_instance.quest_items, list):
                    for name in level_instance.quest_items:
                        nid = str(name).lower()
                        if nid not in seen:
                            collected_ids.append(nid)
                            seen.add(nid)
                # Collectibles mit collected=True
                if hasattr(level_instance, 'collectible_items') and isinstance(level_instance.collectible_items, dict):
                    for nid, meta in level_instance.collectible_items.items():
                        try:
                            if isinstance(meta, dict) and meta.get('collected'):
                                nid_l = str(nid).lower()
                                if nid_l not in seen:
                                    collected_ids.append(nid_l)
                                    seen.add(nid_l)
                        except Exception:
                            continue
            if collected_ids:
                header = self.small_font.render("Gesammelte Items:", True, TEXT_COLOR)
                self.screen.blit(header, (inner_left, y_offset))
                y_offset += 24

                # Bis zu 5 gesammelte Items kompakt einpassen
                slot_size_col = 40
                n_col = max(1, min(5, len(collected_ids)))
                item_spacing_items = compute_spacing(n_col, slot_size_col)
                start_x_items = inner_left
                for i, item_id in enumerate(collected_ids[:5]):
                    color = zutaten_farben.get(item_id, (200, 200, 200))
                    rect_x = start_x_items + i * (slot_size_col + item_spacing_items)
                    pygame.draw.rect(self.screen, color, (rect_x, y_offset, slot_size_col, slot_size_col))
                    # Anzeigename: falls schöner Name vorhanden
                    display_name = item_id.capitalize()
                    try:
                        if (hasattr(level_instance, 'collectible_items') and 
                            item_id in level_instance.collectible_items and 
                            isinstance(level_instance.collectible_items[item_id], dict)):
                            dn = level_instance.collectible_items[item_id].get('name')
                            if dn:
                                display_name = str(dn)
                    except Exception:
                        pass
                    name_surface = self.small_font.render(display_name, True, TEXT_COLOR)
                    name_rect = name_surface.get_rect(centerx=rect_x + slot_size_col // 2, top=y_offset + slot_size_col + 6)
                    self.screen.blit(name_surface, name_rect)

                y_offset += slot_size_col + 28
        except Exception:
            # UI sollte robust gegen Fehler bleiben
            pass
        
        # Magie-System UI (falls Player verfügbar)
        if hasattr(game_logic, 'player') and game_logic.player:
            self.draw_magic_ui(game_logic.player, inner_left, y_offset)
            y_offset += 80
        
        # Letztes Brau-Ergebnis
        result_lines = game_logic.last_brew_result.split('\n')
        for line in result_lines:
            if line.strip():
                result_surface = self.small_font.render(line, True, TEXT_COLOR)
                self.screen.blit(result_surface, (inner_left, y_offset))
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
        self.screen.blit(map_surface, (inner_left, y_offset))
    
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
        # 0. Hintergrund/Map zuerst rendern, um alte Frames zu überschreiben
        #    Damit bleiben keine Menu-Überreste sichtbar, wenn der State wechselt.
        self.draw_background(map_loader, camera)

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

        # 2.5. Magie-Projektile und Effekte rendern (über Entities, unter Foreground)
        try:
            if player and hasattr(player, 'magic_system') and player.magic_system:
                player.magic_system.draw_projectiles(self.screen, camera)
        except Exception:
            pass
        
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

        # ✅ NEU: Map-Progression System - STARTET IN MAP3
        self.current_map_index = 0  # Index 0 = Map3.tmx (START MAP)
        self.map_progression = [
            "Map3.tmx",        # 0. Map: Map3 (START MAP)
            "Map_Village.tmx"  # 1. Map: Map_Village (nach Abschluss von Map3)
        ]
        self.map_completed = False

        # Depth-Objekte für 3D-ähnliche Darstellung
        self.depth_objects = []

        # Referenz für UI-Status-Anzeige
        self.game_logic._level_ref = self
        # FIX: Verwende die Surface-Dimensionen für die Kamera, nicht SCREEN_-Konstanten
        surface_width = screen.get_width()
        surface_height = screen.get_height()
        self.camera = Camera(surface_width, surface_height)  # Kein Zoom-Parameter mehr nötig
        self.renderer = GameRenderer(self.screen)
        # Pathfinding grid (built from map collisions)
        self.pathfinder = None
        # Attach back-reference to level on player for enemy helpers
        try:
            if hasattr(self.game_logic, 'player') and self.game_logic.player:
                setattr(self.game_logic.player, '_level_ref', self)
        except Exception:
            pass
        
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
                'text': 'Elara (Nachbarin):\n"Lumo ist ins Dorf gerannt - aber die Brücke ist eingestürzt!\nRepariere sie, sonst kommst du nicht hinüber!"',
                'active': False,
                'is_checkpoint': True,  # Markiere als Checkpoint
                'required_items': ['stahlerz', 'holzstab'],  # Benötigte Gegenstände
                'completion_text': 'Du hast alle Gegenstände gefunden und die Brücke repariert!',
                'completed': False
            },
            'brann_dialog': {
                'pos': pygame.math.Vector2(902, 603),
                'radius': 150,
                'text': 'Meister Brann (Kräuterkundler):\n"Der Weg zur Mühle ist voller Sporennebel.\nNur ein starkes Elixier kann ihn vertreiben!"',
                'active': False,
                'is_checkpoint': True,  # Dies ist ein Checkpoint wie Elara
                'required_items': ['mondstein', 'kristall'],  # Benötigte Gegenstände
                'completion_text': 'Herzlichen Glückwunsch, Level erfolgreich abgeschlossen!',
                'completed': False,
                'map_specific': True,  # Kennzeichnet, dass dieser NPC nur in Map 2 erscheint
                'allowed_map': 'Map_Village.tmx'
            }
        }
        print(f"Interaktionszone erstellt bei Position: {self.interaction_zones['elara_dialog']['pos']}")
    
        self.show_interaction_text = False
        self.interaction_text = ""
        self.interaction_font = pygame.font.Font(None, 32)  # Schriftgröße angepasst für bessere Lesbarkeit
        # Schrift für Item-Namen über Sammelobjekten
        self.item_name_font = pygame.font.Font(None, 22)

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
            'kristall': {
                'pos': pygame.math.Vector2(24, 885),
                'name': 'Kristall',
                'collected': False,
                'radius': 50,
                'color': (186, 85, 211),  # Lila/Violett
                'available': True
            },
            'goldreif': {
                'pos': pygame.math.Vector2(2453, 33),
                'name': 'Goldreif',
                'collected': False,
                'radius': 50,
                'color': (255, 215, 0),  # Gold
                'available': True
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

    def _configure_collectibles_for_map(self, map_filename: str):
        """Enable/disable collectibles and set their positions based on the current map."""
        # Definiere die Map-spezifischen Positionen
        positions = {
            'Map3.tmx': {  # Level 1 Positionen
                'holzstab': pygame.math.Vector2(27, 59),
                'stahlerz': pygame.math.Vector2(3056, 39),
                'mondstein': pygame.math.Vector2(2296, 913),
                'kristall': pygame.math.Vector2(24, 885),
                'goldreif': pygame.math.Vector2(2453, 33)
            },
            'Map_Village.tmx': {  # Level 2 Positionen
                'holzstab': pygame.math.Vector2(1205, 380),
                'stahlerz': pygame.math.Vector2(38, 165),
                'mondstein': pygame.math.Vector2(2073, 760),
                'kristall': pygame.math.Vector2(337, 1081),
                'goldreif': pygame.math.Vector2(2421, 356)
            }
        }
        
        try:
            # Setze die Positionen für die aktuelle Map
            if map_filename in positions:
                map_positions = positions[map_filename]
                for item_name, pos in map_positions.items():
                    if item_name in self.collectible_items:
                        self.collectible_items[item_name]['pos'] = pos
                        self.collectible_items[item_name]['collected'] = False
                        self.collectible_items[item_name]['available'] = True
                print(f"✅ Sammelobjekte für {map_filename} konfiguriert")
            
            # Objekte für nicht-definierte Maps deaktivieren
            else:
                for item in self.collectible_items.values():
                    item['available'] = False
                print(f"⚠️ Keine Sammelobjekte für {map_filename} definiert")
                    
        except Exception as e:
            print(f"❌ Fehler beim Konfigurieren der Sammelobjekte: {str(e)}")
            
            if not hasattr(self, 'collectible_items') or not isinstance(self.collectible_items, dict):
                return
            for it in self.collectible_items.values():
                if isinstance(it, dict):
                    it['collected'] = False
                    it['available'] = False
            if 'Map3.tmx' in map_filename:
                for it in self.collectible_items.values():
                    if isinstance(it, dict):
                        it['available'] = True
        except Exception:
            pass

    def load_map(self):
        """Lädt die Spielkarte und extrahiert Spawn-Punkte"""
        try:
            # ✅ Lade die aktuelle Map aus der Progression
            current_map = self.map_progression[self.current_map_index]
            map_path = path.join(MAP_DIR, current_map)
            
            self.map_loader = MapLoader(map_path)
            
            if self.map_loader and self.map_loader.tmx_data:
                self.use_map = True
                print(f"✅ Map geladen: {map_path}")
                
                # Debug: Zeige alle verfügbaren Layer UND Object Groups
                print("🗂️ Verfügbare Layer:")
                for layer in self.map_loader.tmx_data.visible_layers:
                    layer_type = "Objekt" if hasattr(layer, 'objects') else "Tile"
                    object_count = len(layer.objects) if hasattr(layer, 'objects') else 0
                    layer_name = getattr(layer, 'name', 'None')
                    print(f"  - {layer_name} ({layer_type}) - {object_count} Objekte")
                
                # Debug: Zeige Object Groups separat (robustere Fehlerbehandlung)
                if hasattr(self.map_loader.tmx_data, 'objectgroups'):
                    print("🗂️ Object Groups:")
                    for obj_group in self.map_loader.tmx_data.objectgroups:
                        group_name = getattr(obj_group, 'name', 'Unnamed')
                        try:
                            objects_list = obj_group.objects if hasattr(obj_group, 'objects') else []
                            print(f"  - {group_name} - {len(objects_list)} Objekte")
                            for obj in objects_list:
                                obj_name = getattr(obj, 'name', 'unnamed')
                                obj_x = getattr(obj, 'x', 0)
                                obj_y = getattr(obj, 'y', 0)
                                print(f"    * '{obj_name}' bei ({obj_x}, {obj_y})")
                        except AttributeError as e:
                            print(f"  - {group_name} - Fehler beim Lesen der Objekte: {e}")
                else:
                    print("🗂️ Keine Object Groups gefunden")
            
                # Datengesteuertes Spawning: Spieler-Position aus Tiled-Map extrahieren
                self._configure_collectibles_for_map(current_map)
                self.spawn_entities_from_map()

                # Gegner aus der Map spawnen (ObjectGroup "Enemy" etc.)
                # und direkt Health-Bars für die gespawnten Gegner hinzufügen
                self.respawn_enemies_only()
                
            else:
                print(f"❌ Map konnte nicht geladen werden: {map_path}")
                self.map_loader = None
                self.use_map = False
                # Fallback
                self.game_logic.player.rect.bottom = self.screen.get_height() - 200
                self.game_logic.player.rect.centerx = self.screen.get_width() // 2
                self.game_logic.player.update_hitbox()
                
        except Exception as e:
            print(f"❌ Fehler beim Laden der Map: {e}")
            import traceback
            traceback.print_exc()
            
            self.map_loader = None
            self.use_map = False
            # Fallback: Standard-Position
            self.game_logic.player.rect.bottom = self.screen.get_height() - 200
            self.game_logic.player.rect.centerx = self.screen.get_width() // 2
            self.game_logic.player.update_hitbox()
            print("⚠️ Fallback auf Standard-Position")
    
    def spawn_entities_from_map(self):
        """Lädt Entities aus der Map oder verwendet Fallback - mit Object Group Support"""
        if not self.map_loader or not self.map_loader.tmx_data:
            return

        player_spawned = False

        # 1. Durchsuche alle Layer (auch unsichtbare) nach Spawn-Objekten
        for layer in self.map_loader.tmx_data.layers:
            if hasattr(layer, 'objects'):  # Objekt-Layer
                # ✅ BEHALTEN: Sichere Layer-Name Behandlung
                print(f"🔍 Prüfe Objekt-Layer: {getattr(layer, 'name', 'None')}")
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
                    
                    elif obj.name and 'enemy' in obj.name.lower():
                        print(f"🎯 Enemy-Spawn gefunden: {obj.name} bei ({obj.x}, {obj.y})")
                        # Enemy-Spawning wird vom EnemyManager gehandhabt
            
            if player_spawned:
                break  # Stoppe die Suche nach dem ersten gefundenen Player-Spawn

        # 2. NEU: Durchsuche Object Groups nach Spawn-Objekten (per Name-Lookup)
        if not player_spawned and hasattr(self.map_loader.tmx_data, 'objectgroups'):
            print("🔍 Prüfe Object Groups...")
            try:
                # Suche nach Object Groups mit Namen wie "spawn", "Spawn", etc.
                spawn_group_names = ['spawn', 'Spawn', 'SPAWN', 'player_spawn', 'Player']
                
                for group_name in spawn_group_names:
                    try:
                        spawn_layer = self.map_loader.tmx_data.get_layer_by_name(group_name)
                        if spawn_layer and hasattr(spawn_layer, 'objects'):
                            print(f"  ✅ Spawn Object Group gefunden: '{group_name}'")
                            
                            for obj in spawn_layer.objects:
                                obj_name = getattr(obj, 'name', None)
                                print(f"    - Objekt: '{obj_name}' bei ({obj.x}, {obj.y})")
                                
                                # Spawn an erstem Objekt in der Spawn-Gruppe
                                if obj_name and obj_name.lower() in ['spawn', 'player', 'start'] or not obj_name:
                                    # Validiere Spawn-Position
                                    spawn_x = max(50, min(obj.x, self.map_loader.width - 50))
                                    spawn_y = max(50, min(obj.y, self.map_loader.height - 50))
                                    
                                    self.game_logic.player.rect.centerx = spawn_x
                                    self.game_logic.player.rect.centery = spawn_y
                                    self.game_logic.player.update_hitbox()
                                    player_spawned = True
                                    print(f"✅ Player gespawnt bei ({spawn_x}, {spawn_y}) von Spawn Group '{group_name}'")
                                    break
                        
                        if player_spawned:
                            break
                            
                    except ValueError:
                        # Gruppe existiert nicht
                        continue
                    except Exception as e:
                        print(f"  ⚠️ Fehler beim Prüfen der Gruppe '{group_name}': {e}")
                        continue
            
            except Exception as e:
                print(f"⚠️ Fehler bei Object Group Suche: {e}")

        # 3. NEU: Finde Spawn über Tile-Layer namens "Spawn" (erstes nicht-leeres Tile)
        if not player_spawned:
            try:
                spawn_layer_names = ['spawn', 'Spawn', 'SPAWN']
                for layer in self.map_loader.tmx_data.layers:
                    layer_name = getattr(layer, 'name', None)
                    if layer_name in spawn_layer_names and not hasattr(layer, 'objects'):
                        print(f"🔍 Prüfe Tile-Layer '{layer_name}' für Spawn-Tiles...")
                        # layer.tiles() liefert (x, y, gid) für nicht-leere Tiles
                        found_tile = None
                        if hasattr(layer, 'tiles'):
                            for (tx, ty, gid) in layer.tiles():
                                if gid:  # erstes belegtes Tile genügt als Marker
                                    found_tile = (tx, ty)
                                    break
                        # Alternative Iteration (pytmx >= 3) falls tiles() fehlt
                        if not found_tile and hasattr(layer, 'width') and hasattr(layer, 'height'):
                            for ty in range(layer.height):
                                for tx in range(layer.width):
                                    gid = self.map_loader.tmx_data.get_tile_gid(tx, ty, self.map_loader.tmx_data.layers.index(layer)) if hasattr(self.map_loader.tmx_data, 'get_tile_gid') else 0
                                    if gid:
                                        found_tile = (tx, ty)
                                        break
                                if found_tile:
                                    break

                        if found_tile:
                            tile_w = self.map_loader.tmx_data.tilewidth
                            tile_h = self.map_loader.tmx_data.tileheight
                            spawn_x = int(found_tile[0] * tile_w + tile_w / 2)
                            spawn_y = int(found_tile[1] * tile_h + tile_h / 2)

                            # Begrenze auf Kartenbereich
                            spawn_x = max(0, min(spawn_x, self.map_loader.width))
                            spawn_y = max(0, min(spawn_y, self.map_loader.height))

                            self.game_logic.player.rect.centerx = spawn_x
                            self.game_logic.player.rect.centery = spawn_y
                            self.game_logic.player.update_hitbox()
                            player_spawned = True
                            print(f"✅ Player aus Tile-Layer '{layer_name}' bei ({spawn_x}, {spawn_y}) gespawnt")
                            break
            except Exception as e:
                print(f"⚠️ Fehler beim Spawn aus Tile-Layer: {e}")

        # 3b. XML-Fallback: Lese direkt aus TMX die ObjectGroup "Spawn" und das Objekt "spawn"
        if not player_spawned:
            try:
                import xml.etree.ElementTree as ET
                # Pfad zur aktuellen Map ermitteln
                map_path = getattr(self.map_loader.tmx_data, 'filename', None)
                if not map_path and hasattr(self.map_loader, 'map_path'):
                    map_path = getattr(self.map_loader, 'map_path')

                if map_path:
                    tree = ET.parse(map_path)
                    root = tree.getroot()
                    spawn_found = False
                    for objectgroup in root.findall('objectgroup'):
                        group_name = (objectgroup.get('name') or '').lower()
                        if group_name == 'spawn':
                            for obj in objectgroup.findall('object'):
                                obj_name = (obj.get('name') or '').lower()
                                if obj_name == 'spawn':
                                    x = float(obj.get('x', '0'))
                                    y = float(obj.get('y', '0'))
                                    spawn_x = int(max(0, min(x, self.map_loader.width)))
                                    spawn_y = int(max(0, min(y, self.map_loader.height)))
                                    self.game_logic.player.rect.centerx = spawn_x
                                    self.game_logic.player.rect.centery = spawn_y
                                    self.game_logic.player.update_hitbox()
                                    player_spawned = True
                                    spawn_found = True
                                    print(f"✅ Player via XML-Fallback bei ({spawn_x}, {spawn_y}) aus ObjectGroup 'Spawn'/'spawn' gespawnt")
                                    break
                        if spawn_found:
                            break
            except Exception as e:
                print(f"⚠️ XML-Fallback für Spawn fehlgeschlagen: {e}")

        # 4. Fallback falls kein Spawn-Punkt gefunden
        if not player_spawned:
            print("⚠️ Kein Player-Spawn in Map gefunden - verwende mapspezifische Standard-Position")
            
            # ✅ BEHALTEN: Mapspezifische Fallback-Positionen
            if hasattr(self.map_loader, 'tmx_data') and self.map_loader.tmx_data:
                map_filename = str(getattr(self.map_loader.tmx_data, 'filename', ''))
                
                if 'Map3.tmx' in map_filename:
                    # Map3: Standard-Position
                    self.game_logic.player.rect.centerx = 800
                    self.game_logic.player.rect.centery = 400
                    self.game_logic.player.update_hitbox()
                    print("✅ Player in Map3 Standard-Position gespawnt (800, 400)")
                    
                elif 'Map_Village.tmx' in map_filename:
                    # Map_Village: Zentriert
                    self.game_logic.player.rect.centerx = 1280  # Mitte der 80x80 Map
                    self.game_logic.player.rect.centery = 1280
                    self.game_logic.player.update_hitbox()
                    print("✅ Player in Map_Village Mitte gespawnt (1280, 1280)")
                    
                elif 'Map_Town.tmx' in map_filename:
                    # Map_Town: unten rechts  
                    map_width = self.map_loader.tmx_data.width * self.map_loader.tmx_data.tilewidth
                    map_height = self.map_loader.tmx_data.height * self.map_loader.tmx_data.tileheight
                    self.game_logic.player.rect.centerx = map_width - 100
                    self.game_logic.player.rect.centery = map_height - 100
                    self.game_logic.player.update_hitbox()
                    print("✅ Player unten rechts auf Map_Town gespawnt")
                    
                else:
                    # Unbekannte Map: Allgemeine Standard-Position
                    self.game_logic.player.rect.centerx = 400
                    self.game_logic.player.rect.centery = 300
                    self.game_logic.player.update_hitbox()
                    print("✅ Player in unbekannter Map Standard-Position gespawnt (400, 300)")

    def respawn_enemies_only(self):
        """Spawnt nur die Feinde neu, ohne die Spieler-Position zu verändern"""
        if not self.map_loader or not self.map_loader.tmx_data:
            return
        
        # Demons aus der Map spawnen
        self.enemy_manager.add_enemies_from_map(self.map_loader)
        
        # Kein generischer Fallback mehr: Maps ohne Gegner bleiben gegnerfrei
        if len(self.enemy_manager.enemies) == 0:
            print("ℹ️ Keine Gegner-Objekte in dieser Map gefunden – keine Gegner gespawnt.")

        # Health-Bars für alle (neuen) Gegner hinzufügen, die noch keine haben
        try:
            for enemy in list(self.enemy_manager.enemies):
                if self.health_bar_manager.get_health_bar(enemy) is None:
                    self.add_enemy_health_bar(enemy)
        except Exception as e:
            print(f"⚠️ Fehler beim Zuweisen der Enemy Health-Bars: {e}")
    
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

            # Build pathfinding grid once
            try:
                tmx = self.map_loader.tmx_data
                mw, mh = getattr(tmx, 'width', 100), getattr(tmx, 'height', 100)
                tw, th = getattr(tmx, 'tilewidth', 32), getattr(tmx, 'tileheight', 32)
                self.pathfinder = GridPathfinder(mw, mh, tw, th)
                self.pathfinder.build_from_collision_rects(self.map_loader.collision_objects)
                # Provide to enemy manager so enemies can request paths
                if hasattr(self.enemy_manager, 'set_pathfinder'):
                    self.enemy_manager.set_pathfinder(self.pathfinder)
            except Exception as e:
                print(f"⚠️ Pfadfinder-Initialisierung fehlgeschlagen: {e}")
    
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
        # Timer für styled message
        if event.type == pygame.USEREVENT + 1:
            self.show_interaction_text = False
            pygame.time.set_timer(pygame.USEREVENT + 1, 0)  # Timer deaktivieren
        # Universal Input System für Actions verwenden
        action = self.input_system.handle_event(event)
        
        if action:
            # Action-Mapping
            if action == 'brew':
                # Primary action: cast spell if combo ready, else brew potion
                try:
                    mixer = getattr(self.main_game, 'element_mixer', None)
                    has_combo = False
                    if mixer and hasattr(mixer, 'get_current_spell_elements'):
                        elements = mixer.get_current_spell_elements()
                        has_combo = bool(elements)
                    if has_combo:
                        self.handle_cast_magic()
                    else:
                        self.game_logic.brew()
                except Exception:
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
            elif action in ('ingredient_1', 'magic_water'):
                # 1 = Wasser-Element für Magie
                self.handle_magic_element('water')
            elif action in ('ingredient_2', 'magic_fire'):
                # 2 = Feuer-Element für Magie
                self.handle_magic_element('fire')
            elif action in ('ingredient_3', 'magic_stone'):
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
                status = "AN" if self.show_collision_debug else "AUS"
                print(f"🧪 Kollisions-/Range-Debug: {status}")
            elif event.key == pygame.K_F2:
                # Toggle Health-Bars ein/aus
                self.toggle_health_bars()
            elif event.key == pygame.K_k and "Map_Village.tmx" in self.map_progression[self.current_map_index]:
                # Koordinatenanzeige nur in Map_Village
                self.show_coordinates = not self.show_coordinates
                print(f"🎯 Koordinatenanzeige: {'An' if self.show_coordinates else 'Aus'}")
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

        # Bewegungs-Input anwenden (Keyboard/Gamepad via UniversalInputSystem)
        try:
            if self.input_system and hasattr(self.game_logic, 'player') and self.game_logic.player:
                move_vec = self.input_system.get_movement_vector()
                self.game_logic.player.set_direction(move_vec)
                self.game_logic.player.move(dt)
        except Exception as e:
            print(f"⚠️ Bewegungs-Update Fehler: {e}")

        # Game Logic Update (Animationen, Magie, etc.)
        result = self.game_logic.update(dt)
        # Propagate game over when player dies
        try:
            player_dead = False
            if hasattr(self.game_logic, 'player') and self.game_logic.player:
                p = self.game_logic.player
                player_dead = (getattr(p, 'current_health', 1) <= 0) or \
                              (hasattr(p, 'is_dead') and p.is_dead())
            if result == "game_over" or player_dead:
                return "game_over"
        except Exception:
            pass

        # Feinde aktualisieren
        self.enemy_manager.update(dt, self.game_logic.player)

        # Kamera aktualisieren
        if hasattr(self.game_logic, 'player'):
            self.camera.update(self.game_logic.player)

        # Health-Bars aktualisieren
        self.health_bar_manager.update(dt)

        # Interaktionszonen prüfen
        self.check_interaction_zones()

        # Sammelobjekte prüfen (Quest-Gegenstände einsammeln)
        self.check_collectibles()

        # Level-Abschluss prüfen
        self.check_level_completion()
    
    def show_styled_message(self, message: str):
        """Zeigt eine Nachricht im gleichen Stil wie der Elara-Dialog an"""
        self.show_interaction_text = True
        self.interaction_text = message
        # Zeitverzögerte Ausblendung nach 3 Sekunden
        pygame.time.set_timer(pygame.USEREVENT + 1, 3000)  # Event in 3 Sekunden
        
    def check_interaction_zones(self):
        """Überprüft ob der Spieler in der Nähe einer Interaktionszone ist"""
        if not self.game_logic or not self.game_logic.player:
            return

        player_pos = pygame.math.Vector2(self.game_logic.player.rect.center)
        self.show_interaction_text = False
        
        # Aktuelle Map ermitteln
        current_map = ""
        if self.map_loader and hasattr(self.map_loader, 'tmx_data'):
            map_path = str(getattr(self.map_loader.tmx_data, 'filename', ''))
            current_map = os.path.basename(map_path) if map_path else ""
            
        for zone_id, zone in self.interaction_zones.items():
            # Prüfen ob die Zone map-spezifisch ist und zur aktuellen Map passt
            if zone.get('map_specific', False):
                allowed_map = zone.get('allowed_map', '')
                if allowed_map != current_map:
                    continue
                
            distance = player_pos.distance_to(zone['pos'])

            if distance <= zone['radius']:
                zone['active'] = True
                
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

        # Update die Collection Message Timer
        if self.collection_message_timer > 0:
            self.collection_message_timer = max(0, self.collection_message_timer - pygame.time.get_ticks())
    
    def check_collectibles(self):
        """Überprüft Kollision (Nähe) mit vordefinierten Sammelobjekten und sammelt sie ein."""
        if not self.game_logic or not self.game_logic.player:
            return

        player_center = pygame.math.Vector2(self.game_logic.player.rect.center)

        # Durch gehe alle definierten Sammelobjekte
        for key, item in self.collectible_items.items():
            if not item.get('available', True):
                continue
            if item.get('collected', False):
                continue

            pos: pygame.math.Vector2 = item['pos']
            radius: int = item.get('radius', 40)
            if player_center.distance_to(pos) <= radius:
                # Markiere als gesammelt
                item['collected'] = True
                item['available'] = False

                # Trage in Questliste ein
                item_name = key.lower()
                if item_name not in self.quest_items:
                    self.quest_items.append(item_name)

                # Füge auch der Alchemie/Inventar-Liste hinzu (Kompatibilität)
                try:
                    self.game_logic.add_zutat(item_name)
                except Exception:
                    pass

                # Anzeige-Meldung
                self.collection_message = f"🎒 {item.get('name', key)} eingesammelt!"
                self.collection_message_timer = pygame.time.get_ticks() + self.collection_message_duration
                print(self.collection_message)

    def _draw_collectibles(self):
        """Zeichnet sichtbare Sammelobjekte in die Welt."""
        if not self.collectible_items:
            return
        for key, item in self.collectible_items.items():
            if item.get('available', True) and not item.get('collected', False):
                world_pos: pygame.math.Vector2 = item['pos']
                color = item.get('color', (200, 200, 200))
                # Erzeuge ein kleines Rechteck um die Position, damit wir die Kamera anwenden können
                size = 24
                rect = pygame.Rect(int(world_pos.x - size/2), int(world_pos.y - size/2), size, size)
                screen_rect = self.camera.apply_rect(rect)
                # Zeichnen (gefüllter Kreis + Rand)
                center = (screen_rect.centerx, screen_rect.centery)
                pygame.draw.circle(self.screen, color, center, max(6, screen_rect.width // 3))
                pygame.draw.circle(self.screen, (255, 255, 255), center, max(7, screen_rect.width // 3), 2)

                # Name über dem Item anzeigen (konfigurierbar)
                try:
                    if SHOW_ITEM_NAMES:
                        name_text = item.get('name', key)
                        font = getattr(self, 'item_name_font', None)
                        if font is None:
                            font = pygame.font.Font(None, 22)
                        text_surf = font.render(str(name_text), True, (255, 255, 255))
                        # Einfacher Outline für Lesbarkeit
                        outline_color = (0, 0, 0)
                        text_rect = text_surf.get_rect()
                        text_rect.midbottom = (center[0], screen_rect.top - 4)

                        # Outline zeichnen
                        for dx, dy in ((-1,0),(1,0),(0,-1),(0,1)):
                            shadow = font.render(str(name_text), True, outline_color)
                            self.screen.blit(shadow, (text_rect.x + dx, text_rect.y + dy))
                        # Haupttext
                        self.screen.blit(text_surf, text_rect)
                except Exception:
                    pass
    
    def trigger_level_completion(self):
        """Wird aufgerufen wenn ein Level abgeschlossen ist - lädt nächste Map"""
        print("🎉 Level abgeschlossen!")
        
        # Markiere aktuelles Level als abgeschlossen
        self.map_completed = True

        # Gegner und zugehörige Health-Bars bereinigen, bevor wir wechseln
        try:
            self.clear_enemies()
        except Exception as e:
            print(f"⚠️ Fehler beim Aufräumen der Gegner vor Map-Wechsel: {e}")

        # Zeige immer die gleiche Level-Abschluss Nachricht an
        self.show_styled_message("Herzlichen Glückwunsch, Level erfolgreich abgeschlossen!")
        
        # Prüfe ob es eine nächste Map gibt
        if self.current_map_index + 1 < len(self.map_progression):
            next_map_index = self.current_map_index + 1
            next_map_name = self.map_progression[next_map_index]
            
            print(f"🗺️ Lade nächste Map: {next_map_name}")
            
            # Wechsle zur nächsten Map
            self.load_next_map(next_map_name, next_map_index)
            
        else:
            self.show_styled_message("Herzlichen Glückwunsch, Level erfolgreich abgeschlossen!")
            if hasattr(self, 'main_game') and self.main_game:
                self.main_game.show_message("Herzlichen Glückwunsch! Level erfolgreich abgeschlossen!")

    def clear_enemies(self):
        """Entfernt alle Gegner und deren Health-Bars (z.B. beim Map-Wechsel)."""
        try:
            # Entferne Health-Bars der Gegner
            for enemy in list(self.enemy_manager.enemies):
                try:
                    self.health_bar_manager.remove_entity(enemy)
                except Exception:
                    pass
            # Leere die Gegnerliste/-gruppe
            if hasattr(self.enemy_manager, 'reset_enemies'):
                self.enemy_manager.reset_enemies()
            else:
                self.enemy_manager.enemies.empty()
            print("🧹 Gegner und Health-Bars entfernt")
        except Exception as e:
            print(f"⚠️ clear_enemies Fehler: {e}")

    def load_next_map(self, map_name, map_index=None):
        """Lädt die nächste Map in der Progression"""
        try:
            print(f"🔄 Wechsle zu Map: {map_name}")
            
            # Update Map-Index
            if map_index is not None:
                self.current_map_index = map_index
            
            # Wenn wir zu Map_Village wechseln (Level 2), setzen wir alles zurück
            if "Map_Village.tmx" in map_name:
                print("🔄 Wechsel zu Level 2 - Setze Spielzustand zurück...")
                
                # Inventar zurücksetzen
                if hasattr(self.game_logic, 'inventory'):
                    self.game_logic.inventory = []
                if hasattr(self.game_logic, 'quest_items'):
                    self.game_logic.quest_items = []
                
                # Sammelobjekte zurücksetzen
                for item in self.collectible_items.values():
                    item['collected'] = False
                    item['available'] = True
                
                # Quest-Items zurücksetzen
                self.quest_items = []
                
                # Interaktionszonen zurücksetzen
                for zone in self.interaction_zones.values():
                    zone['active'] = False
                    zone['completed'] = False
                
                # UI/Magic-System zurücksetzen
                if hasattr(self.game_logic, 'reset_magic_system'):
                    self.game_logic.reset_magic_system()
                
                print("✅ Spielzustand erfolgreich zurückgesetzt")

            # Neue Map laden
            map_path = path.join(MAP_DIR, map_name)
            self.map_loader = MapLoader(map_path)
            
            if self.map_loader and self.map_loader.tmx_data:
                self.use_map = True
                print(f"✅ Neue Map geladen: {map_path}")
                
                # Level-Status zurücksetzen
                self.map_completed = False
                
                # Konfiguriere Sammelobjekte für diese Map
                self._configure_collectibles_for_map(map_name)
                
                # Spieler-Position für neue Map setzen (nutzt die neue Spawn-Erkennung!)
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

    def restart_level(self):
        """Setzt das aktuelle Level zurück und lädt die aktuelle Map neu."""
        try:
            print("🔁 Level-Neustart wird ausgeführt…")

            # UI/Magic: Auswahl zurücksetzen
            if self.main_game and hasattr(self.main_game, 'element_mixer') and self.main_game.element_mixer:
                try:
                    self.main_game.element_mixer.reset_combination()
                except Exception:
                    pass

            # Sammel-Status und Meldungen zurücksetzen
            try:
                self.collection_message = ""
                self.collection_message_timer = 0
                if hasattr(self, 'collectible_items') and isinstance(self.collectible_items, dict):
                    for it in self.collectible_items.values():
                        if isinstance(it, dict):
                            it['collected'] = False
                if hasattr(self, 'quest_items'):
                    self.quest_items = []
            except Exception:
                pass

            # Interaktionszonen zurücksetzen
            try:
                if hasattr(self, 'interaction_zones') and isinstance(self.interaction_zones, dict):
                    for z in self.interaction_zones.values():
                        if isinstance(z, dict):
                            if 'active' in z:
                                z['active'] = False
                            if 'completed' in z:
                                z['completed'] = False
            except Exception:
                pass

            # Map-Status zurücksetzen
            self.map_completed = False

            # Health-Bars und Gegner bereinigen
            if hasattr(self, 'health_bar_manager') and self.health_bar_manager:
                try:
                    self.health_bar_manager.reset()
                except Exception:
                    pass
            try:
                self.clear_enemies()
            except Exception:
                pass

            # Spiellogik zurücksetzen (HP/Position/Alchemy etc.)
            if hasattr(self, 'game_logic') and self.game_logic and hasattr(self.game_logic, 'reset_game'):
                self.game_logic.reset_game()

            # Aktuelle Map neu laden (nutzt Spawn-Erkennung, Kollisionsaufbau und Health-Bars)
            current_name = None
            try:
                if hasattr(self, 'map_progression'):
                    current_name = self.map_progression[self.current_map_index]
            except Exception:
                current_name = None

            if current_name:
                self.load_next_map(current_name, self.current_map_index)
            else:
                # Fallback falls Progression nicht gesetzt ist
                self.load_map()
                self.setup_collision_objects()
                self.setup_health_bars()
                self.respawn_enemies_only()

            # Kamera auf Spieler zentrieren
            try:
                if hasattr(self.game_logic, 'player') and self.game_logic.player:
                    self.camera.center_on_target(self.game_logic.player)
            except Exception:
                pass

            print("✅ Level erfolgreich neu gestartet")
        except Exception as e:
            print(f"⚠️ restart_level Fehler: {e}")

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

    def render(self):
        """Hauptrender-Methode für das Level"""
        if not self.renderer:
            return
        
        # Delegiere das Rendering an den GameRenderer
        self.renderer.render_with_foreground_layer(
            self.game_logic.player if self.game_logic else None,
            list(self.enemy_manager.enemies) if self.enemy_manager else [],
            self.depth_objects,
            self.camera,
            self.map_loader
        )

        # Sammelobjekte über der Map aber unter UI rendern
        self._draw_collectibles()

        # Health-Bars über der Welt rendern
        try:
            cam_off = (self.camera.camera_rect.x, self.camera.camera_rect.y)
            self.health_bar_manager.draw_all(self.screen, camera_offset=cam_off)
        except Exception:
            pass

        # Linkes UI (Score, Inventar, Magie, Map-Status) rendern
        try:
            self.renderer.draw_ui(self.game_logic)
        except Exception:
            pass

        # Koordinaten anzeigen (nur in Map_Village wenn aktiviert)
        if self.show_coordinates and "Map_Village.tmx" in self.map_progression[self.current_map_index]:
            try:
                if hasattr(self.game_logic, 'player') and self.game_logic.player:
                    player = self.game_logic.player
                    pos_text = f"Position: ({int(player.rect.centerx)}, {int(player.rect.centery)})"
                    coord_surface = self.interaction_font.render(pos_text, True, (255, 255, 255))
                    coord_rect = coord_surface.get_rect(topleft=(10, 10))
                    
                    # Hintergrund für bessere Lesbarkeit
                    bg_rect = coord_rect.inflate(20, 10)
                    s = pygame.Surface((bg_rect.width, bg_rect.height))
                    s.set_alpha(200)
                    s.fill((0, 0, 50))
                    self.screen.blit(s, bg_rect)
                    self.screen.blit(coord_surface, coord_rect)
            except Exception as e:
                print(f"Fehler beim Anzeigen der Koordinaten: {e}")

        # Interaktionstext anzeigen
        if self.show_interaction_text and self.interaction_text:
            try:
                # Text in Zeilen aufteilen
                lines = self.interaction_text.split('\n')
                
                # Größe des Textfelds berechnen
                line_surfaces = [self.interaction_font.render(line, True, (255, 255, 255)) for line in lines]
                line_heights = [surface.get_height() for surface in line_surfaces]
                max_width = max(surface.get_width() for surface in line_surfaces)
                total_height = sum(line_heights) + (len(lines) - 1) * 5  # 5 Pixel Abstand zwischen Zeilen
                
                # Hintergrundfeld erstellen
                padding = 20  # Polsterung um den Text
                bg_rect = pygame.Rect(
                    self.screen.get_width() // 2 - (max_width + padding) // 2,
                    self.screen.get_height() - 120 - total_height // 2,
                    max_width + padding,
                    total_height + padding
                )
                
                # Hintergrund zeichnen (Dunkelblau mit Transparenz)
                s = pygame.Surface((bg_rect.width, bg_rect.height))
                s.set_alpha(200)  # Transparenz (0-255)
                s.fill((0, 0, 50))  # Dunkelblau RGB
                self.screen.blit(s, bg_rect)
                
                # Text zeichnen
                current_y = bg_rect.top + padding // 2
                for surface in line_surfaces:
                    text_rect = surface.get_rect(centerx=self.screen.get_width() // 2, top=current_y)
                    self.screen.blit(surface, text_rect)
                    current_y += surface.get_height() + 5  # 5 Pixel Abstand
                    
            except Exception as e:
                print(f"Fehler beim Rendern des Interaktionstextes: {e}")

        # Einfache Meldungsanzeige beim Einsammeln
        if self.collection_message and pygame.time.get_ticks() < self.collection_message_timer:
            try:
                font = pygame.font.Font(None, 28)
                text = font.render(self.collection_message, True, (255, 255, 255))
                bg = text.get_rect()
                bg.centerx = self.screen.get_width() // 2
                bg.y = 80
                pygame.draw.rect(self.screen, (0, 0, 0), bg.inflate(16, 10))
                pygame.draw.rect(self.screen, (180, 180, 220), bg.inflate(16, 10), 2)
                self.screen.blit(text, (bg.x, bg.y))
            except Exception:
                pass

        # F1: Kollisions- und Range-Debug einblenden (nach Welt, vor UI/Overlay reicht)
        try:
            if getattr(self, 'show_collision_debug', False):
                # Kollisionsobjekte zeichnen
                if self.map_loader and getattr(self.map_loader, 'collision_objects', None):
                    self.renderer.draw_collision_debug(self.game_logic.player, self.camera, self.map_loader.collision_objects)
                # Enemy Debug (Hitbox + Ranges + Aggro-Line)
                if self.enemy_manager:
                    self.enemy_manager.draw_debug(self.screen, self.camera)
        except Exception as e:
            print(f"⚠️ Debug-Overlay Fehler: {e}")

    # --- Magic handlers (called from input/action system) ---
    def handle_magic_element(self, element_name: str):
        try:
            # Prefer routing through ElementMixer to keep a single source of truth
            if self.main_game and hasattr(self.main_game, 'element_mixer') and self.main_game.element_mixer:
                ui_map = {
                    'fire': 'fire', 'wasser': 'water', 'water': 'water',
                    'stone': 'stone', 'stein': 'stone'
                }
                ui_id = ui_map.get(element_name.lower())
                if ui_id:
                    try:
                        self.main_game.element_mixer.handle_element_press(ui_id)
                    except Exception:
                        pass
            else:
                # Fallback: update core magic system directly if mixer not available
                if self.game_logic and hasattr(self.game_logic, 'player') and self.game_logic.player:
                    from systems.magic_system import ElementType
                    mapping = {
                        'fire': ElementType.FEUER,
                        'wasser': ElementType.WASSER,
                        'water': ElementType.WASSER,
                        'stone': ElementType.STEIN,
                        'stein': ElementType.STEIN,
                    }
                    element = mapping.get(element_name.lower())
                    if element:
                        self.game_logic.player.magic_system.add_element(element)
        except Exception as e:
            print(f"⚠️ handle_magic_element error: {e}")

    def handle_cast_magic(self):
        try:
            if self.game_logic and hasattr(self.game_logic, 'player') and self.game_logic.player:
                player = self.game_logic.player
                if hasattr(player, 'magic_system'):
                    # If ElementMixer has a ready combo, use it as source of truth
                    used_element_mixer = False
                    if self.main_game and hasattr(self.main_game, 'element_mixer') and self.main_game.element_mixer:
                        mixer = self.main_game.element_mixer
                        try:
                            elements = mixer.get_current_spell_elements()
                        except Exception:
                            elements = None
                        if elements:
                            print(f"🧪 Casting via ElementMixer elements: {elements}")
                            try:
                                # Map UI element ids (de: feuer/wasser/stein) to ElementType
                                from systems.magic_system import ElementType
                                map_ui_to_enum = {
                                    'feuer': ElementType.FEUER,
                                    'wasser': ElementType.WASSER,
                                    'stein': ElementType.STEIN,
                                }
                                player.magic_system.clear_elements()
                                for eid in elements:
                                    et = map_ui_to_enum.get(eid.lower())
                                    if et:
                                        player.magic_system.add_element(et)
                                # Start cooldown and reset UI selection
                                try:
                                    mixer.handle_cast_spell()
                                except Exception:
                                    pass
                                used_element_mixer = True
                            except Exception:
                                used_element_mixer = False
                    # Cast via MagicSystem (works whether elements came from mixer or direct input)
                    try:
                        dbg_elems = [e.value for e in player.magic_system.selected_elements]
                        print(f"✨ Casting with core elements: {dbg_elems}")
                    except Exception:
                        pass
                    player.magic_system.cast_magic(caster=player)
        except Exception as e:
            print(f"⚠️ handle_cast_magic error: {e}")

    def handle_clear_magic(self):
        try:
            if self.game_logic and hasattr(self.game_logic, 'player') and self.game_logic.player:
                player = self.game_logic.player
                if hasattr(player, 'magic_system'):
                    player.magic_system.clear_elements()
                # Also clear ElementMixer UI selection if present
                if self.main_game and hasattr(self.main_game, 'element_mixer') and self.main_game.element_mixer:
                    try:
                        self.main_game.element_mixer.reset_combination()
                    except Exception:
                        pass
        except Exception as e:
            print(f"⚠️ handle_clear_magic error: {e}")
