# -*- coding: utf-8 -*-
# src/level.py
import pygame
from typing import Any, cast
import os
from os import path
import math  # Füge den math import hinzu
from settings import *
from game import Game as GameLogic
from world.camera import Camera
from world.map_loader import MapLoader
from managers.enemy_manager import EnemyManager
from managers.font_manager import get_font_manager
from ui.health_bar_py27 import HealthBarManager, create_player_health_bar, create_enemy_health_bar
from ui.dialogue_system import DialogueBox
from systems.input_system import get_input_system
from core.settings import VERBOSE_LOGS
from systems.pathfinding import GridPathfinder
from entities.npc_beckalof import BeckalofNPC, reset_beckalof
from entities.dragon_lord import DragonLord, reset_dragon_lord
from entities.gambler_npc import GamblerNPC
from ui.blackjack_game import BlackjackGame
from entities.shopkeeper_npc import ShopkeeperNPC
from entities.soldier_npc import SoldierNPC
from entities.knight_companion import KnightCompanion
from systems.shop_system import ShopManager
from ui.shop_ui import ShopUI
from systems.quest_manager import QuestManager, Quest, QuestObjective
from systems.score_system import ScoreTracker
from ui.mission_display import MissionDisplay

class GameRenderer:
    """Rendering-System mit Alpha/Transparenz-Optimierung"""
    
    def __init__(self, screen):
        self.screen = screen
        # RPi-Optimierung: FontManager für gecachte Fonts
        self._font_manager = get_font_manager()
        self.font = self._font_manager.get_font(36)
        self.small_font = self._font_manager.get_font(22)  # Kleinere Schrift für Inventar-Items
        self.generate_ground_stones()
        
        # Performance-Optimierung: Asset Manager für gecachte Sprite-Skalierung
        from managers.asset_manager import AssetManager
        self.asset_manager = AssetManager()
        
        # Item-Icons Cache für Inventar
        self._item_icons = {}
        self._load_item_icons()
        
        # Alpha-Caching für transparente Effekte (Performance-Optimierung)
        self._alpha_cache = {}  # Cache für transparente Surfaces
        self._max_alpha_cache_size = 50  # Begrenzt Memory-Verbrauch

        # UI caching (RPi/7-inch performance): avoid per-frame font rendering
        self._inventory_ui_cache_key = None
        self._inventory_ui_cache_surface = None
        self._controls_cache_surfaces = None
        self._magic_title_surface = None
        self._magic_elements_cache_key = None
        self._magic_elements_surface = None
        self._magic_mana_cache_key = None
        self._magic_mana_surface = None
    
    def _load_item_icons(self):
        """Lädt Item-Icons aus assets/ui/items/ falls vorhanden."""
        import os
        items_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                   "assets", "ui", "items")
        
        item_names = ["holzstab", "stahlerz", "mondstein", "kristall", "goldreif", 
                      "wasserkristall", "feueressenz", "erdkristall"]
        
        for item_name in item_names:
            icon_path = os.path.join(items_path, f"{item_name}.png")
            if os.path.exists(icon_path):
                try:
                    icon = pygame.image.load(icon_path).convert_alpha()
                    # Skaliere auf Slot-Größe (44x44 für inneren Bereich)
                    icon = pygame.transform.smoothscale(icon, (44, 44))
                    self._item_icons[item_name] = icon
                    print(f"✅ Item-Icon geladen: {item_name}")
                except Exception as e:
                    print(f"⚠️ Fehler beim Laden von {item_name}.png: {e}")
        
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
        """🚀 Task 5: Zeichnet den Hintergrund - Multi-Resolution-kompatibel
        Zeichnet einen atmosphärischen Rand statt reinem Schwarz außerhalb der Map.
        """
        if map_loader and camera and map_loader.tmx_data:
            # Atmosphärischer Hintergrund statt reinem Schwarz
            self.screen.fill((8, 6, 18))  # Sehr dunkles Blau-Lila
            self._draw_map_border_atmosphere(map_loader, camera)
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
    
    def _draw_map_border_atmosphere(self, map_loader, camera):
        """Zeichnet einen atmosphärischen Nebel-/Dunkelheits-Gradient am Map-Rand.
        Statt reinem Schwarz sieht man einen stimmungsvollen Übergang.
        """
        if not map_loader or not camera:
            return
        
        screen_w = self.screen.get_width()
        screen_h = self.screen.get_height()
        map_w = map_loader.width
        map_h = map_loader.height
        cam = camera.camera_rect
        
        # Berechne die Map-Grenzen in Screen-Koordinaten
        map_left = int(-cam.x * camera.zoom_factor)
        map_top = int(-cam.y * camera.zoom_factor)
        map_right = int((map_w - cam.x) * camera.zoom_factor)
        map_bottom = int((map_h - cam.y) * camera.zoom_factor)
        
        # Breite des Nebel-Gradienten (in Pixeln auf dem Screen)
        fog_depth = 80
        
        # Cache-Key für die Gradient-Streifen (werden nur einmal erzeugt)
        cache_key = ('border_fog', screen_w, screen_h, fog_depth)
        if cache_key not in self._alpha_cache:
            # Horizontaler Gradient-Streifen (fog_depth breit, 1px hoch, wird gestreckt)
            h_grad = pygame.Surface((fog_depth, 1), pygame.SRCALPHA)
            for i in range(fog_depth):
                # Von transparent (Mapseite) nach undurchsichtig (Außenseite)
                alpha = int(255 * (1 - i / fog_depth) ** 1.5)
                h_grad.set_at((i, 0), (12, 8, 28, alpha))
            
            # Vertikaler Gradient-Streifen (1px breit, fog_depth hoch)
            v_grad = pygame.Surface((1, fog_depth), pygame.SRCALPHA)
            for i in range(fog_depth):
                alpha = int(255 * (1 - i / fog_depth) ** 1.5)
                v_grad.set_at((0, i), (12, 8, 28, alpha))
            
            self._alpha_cache[cache_key] = (h_grad, v_grad)
        
        h_grad, v_grad = self._alpha_cache[cache_key]
        
        # --- Ränder außerhalb der Map füllen (dunkles Blau-Lila) ---
        bg_color = (8, 6, 18)
        
        # Links
        if map_left > 0:
            pygame.draw.rect(self.screen, bg_color, (0, 0, map_left, screen_h))
            # Nebel-Gradient am linken Map-Rand (nach innen)
            grad_w = min(fog_depth, screen_w - map_left)
            if grad_w > 0:
                fog = pygame.transform.flip(h_grad, True, False)  # Spiegeln
                fog_scaled = pygame.transform.scale(fog, (grad_w, screen_h))
                self.screen.blit(fog_scaled, (map_left, 0))
        
        # Rechts
        if map_right < screen_w:
            pygame.draw.rect(self.screen, bg_color, (map_right, 0, screen_w - map_right, screen_h))
            # Nebel-Gradient am rechten Map-Rand (nach innen)
            grad_w = min(fog_depth, map_right)
            if grad_w > 0:
                fog_scaled = pygame.transform.scale(h_grad, (grad_w, screen_h))
                self.screen.blit(fog_scaled, (map_right - grad_w, 0))
        
        # Oben
        if map_top > 0:
            pygame.draw.rect(self.screen, bg_color, (0, 0, screen_w, map_top))
            # Nebel-Gradient am oberen Map-Rand (nach innen)
            grad_h = min(fog_depth, screen_h - map_top)
            if grad_h > 0:
                fog = pygame.transform.flip(v_grad, False, True)  # Spiegeln
                fog_scaled = pygame.transform.scale(fog, (screen_w, grad_h))
                self.screen.blit(fog_scaled, (0, map_top))
        
        # Unten
        if map_bottom < screen_h:
            pygame.draw.rect(self.screen, bg_color, (0, map_bottom, screen_w, screen_h - map_bottom))
            # Nebel-Gradient am unteren Map-Rand (nach innen)
            grad_h = min(fog_depth, map_bottom)
            if grad_h > 0:
                fog_scaled = pygame.transform.scale(v_grad, (screen_w, grad_h))
                self.screen.blit(fog_scaled, (0, map_bottom - grad_h))
    
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
        """Modernes Pixel-Art Inventar-UI mit Gradient und mehrstufigem Rahmen."""
        import math
        
        # Ermittele zusätzliche gesammelte Items (aus Level-Referenz)
        level_ref = getattr(game_logic, '_level_ref', None)
        collected_extra = []
        try:
            if level_ref and hasattr(level_ref, 'quest_items'):
                collected_extra = list(level_ref.quest_items)
                collected_extra = [it for it in collected_extra if it not in game_logic.aktive_zutaten]
        except Exception:
            collected_extra = []

        # Alle Items zusammenführen für einheitliche Anzeige (nur oben)
        all_items = list(game_logic.aktive_zutaten[:5]) + collected_extra[:5]
        all_items = all_items[:5]  # Max 5 Items anzeigen
        
        # Animation Zeit für pulsierende Effekte
        anim_time = pygame.time.get_ticks()
        
        # Cache key (ohne Animation - nur statische Elemente cachen)
        cache_key = (
            self.screen.get_width(),
            self.screen.get_height(),
            tuple(all_items),
        )

        # UI-Dimensionen
        slot_size = 52
        slot_spacing = 8
        padding = 14
        n_slots = 5
        
        # Berechne Breite basierend auf Slots
        ui_width = n_slots * slot_size + (n_slots - 1) * slot_spacing + padding * 2 + 10
        ui_height = 94

        # Design-Farben (konsistent mit anderen UI-Elementen)
        bg_color_top = (15, 20, 45)
        bg_color_bottom = (8, 12, 28)
        border_outer = (30, 40, 60)
        border_middle = (60, 80, 120)
        border_inner = (100, 130, 180)
        border_glow = (120, 160, 255)
        corner_accent = (180, 140, 80)  # Gold
        title_color = (220, 200, 140)   # Warmes Gold für Titel
        
        # Item-Definitionen mit Farben
        item_config = {
            "holzstab": {"color": (139, 90, 43), "glow": (180, 120, 60), "name": "Holzstab"},
            "stahlerz": {"color": (120, 130, 140), "glow": (180, 190, 200), "name": "Stahlerz"},
            "mondstein": {"color": (180, 180, 255), "glow": (220, 220, 255), "name": "Mondstein"},
            "kristall": {"color": (180, 100, 255), "glow": (220, 150, 255), "name": "Kristall"},
            "goldreif": {"color": (255, 200, 50), "glow": (255, 230, 100), "name": "Goldreif"},
            "wasserkristall": {"color": (60, 160, 255), "glow": (100, 200, 255), "name": "Wasser"},
            "feueressenz": {"color": (255, 100, 30), "glow": (255, 150, 80), "name": "Feuer"},
            "erdkristall": {"color": (139, 90, 43), "glow": (180, 120, 60), "name": "Erde"},
        }

        # Statischen Hintergrund aus Cache holen oder erstellen
        if cache_key != self._inventory_ui_cache_key or self._inventory_ui_cache_surface is None:
            ui_surface = pygame.Surface((ui_width, ui_height), pygame.SRCALPHA)
            
            # === GRADIENT HINTERGRUND ===
            for row in range(ui_height):
                ratio = row / ui_height
                r = int(bg_color_top[0] * (1 - ratio) + bg_color_bottom[0] * ratio)
                g = int(bg_color_top[1] * (1 - ratio) + bg_color_bottom[1] * ratio)
                b = int(bg_color_top[2] * (1 - ratio) + bg_color_bottom[2] * ratio)
                pygame.draw.line(ui_surface, (r, g, b, 240), (0, row), (ui_width, row))
            
            # === MEHRSTUFIGER RAHMEN (Pixel-Art Style) ===
            # Äußerer Rahmen (dunkel)
            pygame.draw.rect(ui_surface, border_outer, (0, 0, ui_width, ui_height), 2)
            # Mittlerer Rahmen
            pygame.draw.rect(ui_surface, border_middle, (2, 2, ui_width-4, ui_height-4), 2)
            # Innerer heller Rahmen
            pygame.draw.rect(ui_surface, border_inner, (4, 4, ui_width-8, ui_height-8), 1)
            
            # === DEKORATIVE GOLD-ECKEN ===
            corner_size = 6
            corners = [
                (0, 0),                              # Oben links
                (ui_width - corner_size, 0),         # Oben rechts
                (0, ui_height - corner_size),        # Unten links
                (ui_width - corner_size, ui_height - corner_size)  # Unten rechts
            ]
            for cx, cy in corners:
                pygame.draw.rect(ui_surface, corner_accent, (cx, cy, corner_size, corner_size))
                pygame.draw.rect(ui_surface, (255, 220, 140), (cx+2, cy+2, 2, 2))
            
            # === TITEL MIT DEKORATION ===
            # Kleines Deko-Symbol vor dem Titel
            deco_x = padding + 2
            deco_y = 12
            pygame.draw.polygon(ui_surface, corner_accent, [
                (deco_x, deco_y + 4),
                (deco_x + 6, deco_y),
                (deco_x + 6, deco_y + 8)
            ])
            
            # Titel-Text
            title_text = "Inventar"
            title_surface = self.small_font.render(title_text, True, title_color)
            ui_surface.blit(title_surface, (padding + 12, 8))
            
            # Item-Zähler rechts
            count_text = f"{len(all_items)}/5"
            count_color = (100, 255, 150) if len(all_items) < 5 else (255, 200, 100)
            count_surface = self.small_font.render(count_text, True, count_color)
            ui_surface.blit(count_surface, (ui_width - padding - count_surface.get_width() - 4, 8))
            
            # Trennlinie unter Titel
            line_y = 24
            pygame.draw.line(ui_surface, border_middle, (padding, line_y), (ui_width - padding, line_y), 1)

            # === ITEM-SLOTS ===
            slot_y = 34
            start_x = padding + 3
            
            for i in range(n_slots):
                slot_x = start_x + i * (slot_size + slot_spacing)
                slot_rect = pygame.Rect(slot_x, slot_y, slot_size, slot_size)
                
                if i < len(all_items):
                    # Gefüllter Slot
                    item_key = all_items[i].lower()
                    config = item_config.get(item_key, {"color": (150, 150, 150), "glow": (180, 180, 180), "name": item_key.capitalize()})
                    
                    # Slot-Hintergrund (dunkel)
                    pygame.draw.rect(ui_surface, (20, 25, 40), slot_rect, border_radius=4)
                    
                    # Prüfe ob Item-Icon vorhanden ist
                    if item_key in self._item_icons:
                        icon = self._item_icons[item_key]
                        icon_rect = icon.get_rect(center=slot_rect.center)
                        ui_surface.blit(icon, icon_rect)
                    else:
                        # Fallback: Farbiger Platzhalter
                        inner_rect = slot_rect.inflate(-10, -10)
                        pygame.draw.rect(ui_surface, config["color"], inner_rect, border_radius=4)
                        # Highlight oben
                        highlight_rect = pygame.Rect(inner_rect.x + 2, inner_rect.y + 2, inner_rect.width - 4, inner_rect.height // 3)
                        pygame.draw.rect(ui_surface, (*config["glow"], 100), highlight_rect, border_radius=2)
                    
                    # Mehrstufiger Slot-Rahmen
                    pygame.draw.rect(ui_surface, (40, 50, 70), slot_rect, width=2, border_radius=4)
                    pygame.draw.rect(ui_surface, config["glow"], slot_rect.inflate(-2, -2), width=1, border_radius=3)
                    
                else:
                    # Leerer Slot
                    pygame.draw.rect(ui_surface, (18, 22, 35), slot_rect, border_radius=4)
                    pygame.draw.rect(ui_surface, (40, 50, 65), slot_rect, width=1, border_radius=4)
                    
                    # Plus-Symbol für leeren Slot (dezent)
                    plus_color = (50, 60, 80)
                    cx, cy = slot_rect.center
                    pygame.draw.line(ui_surface, plus_color, (cx - 6, cy), (cx + 6, cy), 2)
                    pygame.draw.line(ui_surface, plus_color, (cx, cy - 6), (cx, cy + 6), 2)

            # Cache speichern
            self._inventory_ui_cache_key = cache_key
            self._inventory_ui_cache_surface = ui_surface

        # Position: Unten rechts auf dem Bildschirm
        screen_w = self.screen.get_width()
        screen_h = self.screen.get_height()
        ui_x = screen_w - ui_width - 12
        ui_y = screen_h - ui_height - 12
        
        # Zeichne gecachten Hintergrund
        self.screen.blit(self._inventory_ui_cache_surface, (ui_x, ui_y))
        
        # === ANIMIERTE EFFEKTE (nicht gecacht) ===
        # Pulsierender Glow-Rahmen
        glow_alpha = int(60 + 30 * math.sin(anim_time / 350))
        glow_surf = pygame.Surface((ui_width - 10, ui_height - 10), pygame.SRCALPHA)
        pygame.draw.rect(glow_surf, (*border_glow, glow_alpha), (0, 0, ui_width - 10, ui_height - 10), 1, border_radius=2)
        self.screen.blit(glow_surf, (ui_x + 5, ui_y + 5))
        
        # 💰 Münzen-Anzeige über dem Inventar
        try:
            if hasattr(game_logic, 'player') and game_logic.player:
                coins = game_logic.player.coins
                coin_y = ui_y - 34
                
                # Hintergrund für Münzen
                coin_bg = pygame.Surface((90, 28), pygame.SRCALPHA)
                for row in range(28):
                    alpha = int(180 - row * 2)
                    pygame.draw.line(coin_bg, (15, 20, 45, alpha), (0, row), (90, row))
                self.screen.blit(coin_bg, (ui_x, coin_y))
                pygame.draw.rect(self.screen, (60, 80, 120), (ui_x, coin_y, 90, 28), 1, border_radius=4)
                
                # Münz-Text
                coin_font = pygame.font.Font(None, 24)
                coin_text = coin_font.render(f"💰 {coins}", True, (255, 215, 0))
                self.screen.blit(coin_text, (ui_x + 8, coin_y + 5))
                
                # 🌟 Level & XP-Anzeige über den Münzen
                player = game_logic.player
                lvl = getattr(player, 'level', 1)
                xp = getattr(player, 'xp', 0)
                xp_next = getattr(player, 'xp_to_next', 50)
                
                lvl_bar_w = ui_width
                lvl_bar_h = 28
                lvl_y = coin_y - lvl_bar_h - 4
                
                # Hintergrund
                lvl_bg = pygame.Surface((lvl_bar_w, lvl_bar_h), pygame.SRCALPHA)
                for row in range(lvl_bar_h):
                    alpha = int(180 - row * 2)
                    pygame.draw.line(lvl_bg, (15, 20, 45, alpha), (0, row), (lvl_bar_w, row))
                self.screen.blit(lvl_bg, (ui_x, lvl_y))
                pygame.draw.rect(self.screen, (60, 80, 120), (ui_x, lvl_y, lvl_bar_w, lvl_bar_h), 1, border_radius=4)
                
                # Level-Text
                lvl_font = pygame.font.Font(None, 22)
                lvl_text = lvl_font.render(f"Lv.{lvl}", True, (255, 215, 0))
                self.screen.blit(lvl_text, (ui_x + 6, lvl_y + 3))
                
                # XP-Balken
                bar_x = ui_x + 48
                bar_y = lvl_y + 6
                bar_w = lvl_bar_w - 58
                bar_h = 14
                
                # Bar-Hintergrund
                pygame.draw.rect(self.screen, (20, 25, 40), (bar_x, bar_y, bar_w, bar_h), border_radius=3)
                pygame.draw.rect(self.screen, (40, 50, 70), (bar_x, bar_y, bar_w, bar_h), 1, border_radius=3)
                
                # XP-Füllung
                xp_ratio = xp / xp_next if xp_next > 0 else 0
                fill_w = max(0, int((bar_w - 2) * xp_ratio))
                if fill_w > 0:
                    # Gradient von blau nach cyan
                    for px in range(fill_w):
                        ratio = px / max(1, bar_w - 2)
                        r = int(50 + 100 * ratio)
                        g = int(120 + 135 * ratio)
                        b = 255
                        pygame.draw.line(self.screen, (r, g, b),
                                        (bar_x + 1 + px, bar_y + 1),
                                        (bar_x + 1 + px, bar_y + bar_h - 2))
                
                # XP-Text auf dem Balken
                xp_font = pygame.font.Font(None, 18)
                xp_text = xp_font.render(f"{xp}/{xp_next}", True, (220, 220, 255))
                xp_rect = xp_text.get_rect(center=(bar_x + bar_w // 2, bar_y + bar_h // 2))
                self.screen.blit(xp_text, xp_rect)
        except:
            pass
        
        # Glow für gefüllte Slots (pulsiert leicht)
        slot_y = 34
        start_x = padding + 3
        for i in range(min(len(all_items), n_slots)):
            item_key = all_items[i].lower()
            config = item_config.get(item_key, {"glow": (180, 180, 180)})
            
            slot_x = start_x + i * (slot_size + slot_spacing)
            slot_rect = pygame.Rect(ui_x + slot_x, ui_y + slot_y, slot_size, slot_size)
            
            # Äußerer Glow (pulsiert)
            glow_intensity = int(40 + 20 * math.sin(anim_time / 400 + i * 0.5))
            glow_surf = pygame.Surface((slot_size + 8, slot_size + 8), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (*config["glow"], glow_intensity), (0, 0, slot_size + 8, slot_size + 8), border_radius=6)
            self.screen.blit(glow_surf, (slot_rect.x - 4, slot_rect.y - 4))
    
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
        
        # Pre-render static control text once (font.render is expensive on RPi)
        if self._controls_cache_surfaces is None:
            cached = []
            for i, control in enumerate(controls):
                color = TEXT_COLOR if i > 0 else (255, 255, 0)
                if control.startswith("🔮"):
                    color = (150, 255, 255)
                elif control.startswith("💾"):
                    color = (255, 200, 100)
                cached.append(self.small_font.render(control, True, color))
            self._controls_cache_surfaces = cached

        screen_height = self.screen.get_height()
        screen_width = self.screen.get_width()
        start_y = screen_height - 380  # Mehr Platz für zusätzliche Zeilen
        for i, control_surface in enumerate(self._controls_cache_surfaces):
            self.screen.blit(control_surface, (screen_width - 350, start_y + i * 23))
    
    def draw_magic_ui(self, player, x, y):
        """Zeichnet die Magie-System UI mit Mana-Anzeige"""
        magic_system = player.magic_system
        
        # Titel
        if self._magic_title_surface is None:
            self._magic_title_surface = self.small_font.render("🔮 Magie:", True, (150, 255, 255))
        self.screen.blit(self._magic_title_surface, (x, y))
        
        # Ausgewählte Elemente (nur neu rendern, wenn Auswahl sich ändert)
        try:
            selected_key = tuple([getattr(e, 'value', str(e)) for e in (magic_system.selected_elements or [])])
        except Exception:
            selected_key = ()

        if selected_key != self._magic_elements_cache_key or self._magic_elements_surface is None:
            if magic_system.selected_elements:
                elements_text = f"Elemente: {magic_system.get_selected_elements_str()}"
            else:
                elements_text = "Elemente: Keine ausgewählt"
            self._magic_elements_surface = self.small_font.render(elements_text, True, TEXT_COLOR)
            self._magic_elements_cache_key = selected_key

        self.screen.blit(self._magic_elements_surface, (x, y + 25))
        
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
        
        # Mana-Anzeige (nur bei Integer-Änderung neu rendern)
        mana_key = (int(getattr(player, 'current_mana', 0)), int(getattr(player, 'max_mana', 0)))
        if mana_key != self._magic_mana_cache_key or self._magic_mana_surface is None:
            mana_text = f"Mana: {mana_key[0]}/{mana_key[1]}"
            self._magic_mana_surface = self.small_font.render(mana_text, True, (100, 100, 255))
            self._magic_mana_cache_key = mana_key
        self.screen.blit(self._magic_mana_surface, (x, y + 60))
        
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

        # 3. Foreground-Layer rendern (über Entities)
        if map_loader and hasattr(map_loader, 'render_foreground'):
            map_loader.render_foreground(self.screen, camera)
        
        # 4. Magie-Projektile und Effekte rendern (ÜBER Foreground, immer sichtbar)
        try:
            if player and hasattr(player, 'magic_system') and player.magic_system:
                player.magic_system.draw_projectiles(self.screen, camera)
        except Exception:
            pass
    
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

        # Draw FireWorm projectiles if present
        if hasattr(enemy, 'draw_fireballs'):
            try:
                enemy.draw_fireballs(self.screen, camera)
            except Exception:
                pass

class Level:
    """Hauptspiel-Level - Verwaltet Gameplay-Zustand"""
    
    def __init__(self, screen, main_game=None):
        self.screen = screen  # Verwende die übergebene Surface
        self.main_game = main_game  # Reference to main game for spell bar access
        self.countdown_timer = 5  # Countdown von 5 Sekunden
        self.countdown_active = False  # Ob der Countdown aktiv ist
        self.game_logic = GameLogic()
        
        # Debug-Attribute für Koordinatenanzeige (nur Initialisierung)
        self.show_coordinates = True
        self.debug_font = pygame.font.Font(None, 24)  # Dies ist okay, da Font keine Video-Initialisierung benötigt

        # ✅ NEU: Map-Progression System - STARTET IN MAP3
        self.current_map_index = 0  # Index 0 = Map3.tmx (START MAP)
        self.map_progression = [
            "Map3.tmx",        # 0. Map: Map3 (START MAP)
            "Map_Village.tmx", # 1. Map: Map_Village (nach Abschluss von Map3)
            "Map_Town.tmx",    # 2. Map: Map_Town (nach Abschluss von Map_Village)
            "Map3Castle.tmx"   # 3. Map: Map3Castle (nach Abschluss von Map_Town)
        ]
        self.map_completed = False

        # Depth-Objekte für 3D-ähnliche Darstellung
        self.depth_objects = []

        # Referenz für UI-Status-Anzeige
        # Typing: allow back-reference assignment for Pylance
        self.game_logic._level_ref = cast(Any, self)
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
                setattr(self.game_logic.player, '_score_tracker', None)  # wird nach init gesetzt
        except Exception:
            pass
        
        # Health-Bar Manager initialisieren
        self.health_bar_manager = HealthBarManager()
        
        # Enemy Manager initialisieren (BEFORE map loading!)
        self.enemy_manager = EnemyManager()
        
        # 🧙 The Great Beckalof NPC (MUSS VOR load_map() initialisiert werden!)
        self.beckalof_npc = None
        self._beckalof_gift_given = False  # Einmalig 25 Münzen auf Map_Town
        
        # 🐉 Dragon Lord Boss (MUSS VOR load_map() initialisiert werden!)
        self.dragon_lord = None
        self._dragon_intro_shown = False  # Persistent flag: Intro nur einmal zeigen
        
        # 🎰 Gambler NPC für Blackjack
        self.gambler_npc = None
        self.blackjack_game = None
        self._gambler_introduced = False  # Einmaliger Intro-Dialog
        self._blackjack_was_active = False  # Für Gambler end_dialog() Erkennung
        
        # � Shopkeeper NPC + Shop-System
        self.shopkeeper_npc = None
        self.shop_manager = ShopManager()
        self.shop_ui = ShopUI()
        self._shop_was_active = False  # Für Merchant end_dialog() Erkennung
        
        # Soldat NPC (Map_Town Warnung + Kill-Gate)
        self.soldier_npc = None
        self._town_kill_count = 0
        self._town_kills_required = 10
        self._town_respawn_timer = 0.0
        self._town_respawn_interval = 8.0
        self._soldier_talked = False
        self._soldier_recruited = False  # Ritter angeheuert?
        self.knight_companion = None      # Begleiter-Ritter (nach Anheuerung)
        
        # 📊 Score-System
        self.score_tracker = ScoreTracker()
        self._score_data = None  # ScoreData nach Finale-Berechnung

        # 🏆 Finale-Sequenz (Final Picture + Credits nach Boss-Kill)
        self._finale_active = False
        self._finale_phase = None  # 'score', 'picture' oder 'credits'
        self._finale_picture = None  # Geladenes Bild
        self._finale_alpha = 0  # Einblendung
        self._credits_scroll_y = 0  # Credits-Scroll-Position
        self._credits_start_time = 0
        
        # Map laden
        self.load_map()
        
        # 📊 Score-Timer starten + an Player anbinden
        self.score_tracker.start()
        try:
            if hasattr(self.game_logic, 'player') and self.game_logic.player:
                self.game_logic.player._score_tracker = self.score_tracker
        except Exception:
            pass
        
        # Kollisionsobjekte einmalig setzen (nicht bei jeder Bewegung!)
        self.setup_collision_objects()
        
        # Health-Bars für alle Entitäten hinzufügen
        self.setup_health_bars()
        
        # Input-System initialisieren (reuse instance from main game if available)
        if self.main_game and hasattr(self.main_game, 'input_system') and self.main_game.input_system:
            self.input_system = self.main_game.input_system
        else:
            self.input_system = get_input_system()
        
        # Input-Status (wird jetzt vom Universal Input System verwaltet)
        self.keys_pressed = {'left': False, 'right': False, 'up': False, 'down': False}
        
        # Debug-Optionen
        self.show_collision_debug = False  # Standardmäßig aus, mit F1 aktivierbar

        # Interaktionszonen hinzufügen
        # Debug-Ausgabe für Initialisierung
        if VERBOSE_LOGS:
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
                'completion_text': 'Gut gemacht! In der nächsten Stadt wartet Ritter Konrad auf dich.\nSprich unbedingt mit ihm – er weiß, was dich erwartet!',
                'completed': False,
                'map_specific': True,  # Kennzeichnet, dass dieser NPC nur in Map 2 erscheint
                'allowed_map': 'Map_Village.tmx'
            },
            'aldric_dialog': {
                'pos': pygame.math.Vector2(1900, 1400),
                'radius': 150,
                'text': 'Wächter Aldric (Stadtwache):\n"Die Stadt wird von Dämonen belagert!\nBesiege alle Feinde, damit ich das Schutzschild aktivieren kann!"',
                'active': False,
                'is_checkpoint': False,
                'required_items': [],
                'completion_text': 'Alle Dämonen besiegt! Die Stadt ist gerettet!',
                'completed': False,
                'map_specific': True,
                'allowed_map': 'Map_Town.tmx'
            },

        }
        if VERBOSE_LOGS:
            print(f"Interaktionszone erstellt bei Position: {self.interaction_zones['elara_dialog']['pos']}")
    
        self.show_interaction_text = False
        self.interaction_text = ""
        self.interaction_font = pygame.font.Font(None, 32)  # Schriftgröße angepasst für bessere Lesbarkeit
        # Schrift für Item-Namen über Sammelobjekten
        self.item_name_font = pygame.font.Font(None, 22)
        
        # NPC-Interaktionssystem: Welcher NPC ist gerade in Reichweite?
        self.active_npc_zone = None  # Zone-ID des NPCs in Reichweite
        self.npc_interaction_font = pygame.font.Font(None, 24)
        # 🚀 RPi-Optimierung: Cache für collection_message Font (vermeidet Font-Erstellung pro Frame)
        self.collection_message_font = pygame.font.Font(None, 28)

        # Modal Dialogue UI
        self.dialogue_box = DialogueBox(self.screen)

        # 📜 Quest / Mission System
        self.quest_manager = QuestManager()
        self.mission_display = MissionDisplay()

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

        # 💰 Coin-Drop-System: Münzen die von besiegten Monstern fallen
        self.dropped_coins = []  # Liste von {pos: Vector2, amount: int, spawn_time: int}
        self._alive_enemies_set = set()  # Tracking welche Gegner am Leben sind
        self.coin_pickup_radius = 40  # Pixel-Radius zum Aufsammeln

        # Map-Progression System
        self.current_map_index = 0
        self.map_progression = [
            "Map3.tmx",        # 1. Map: Map3 
            "Map_Village.tmx", # 2. Map: Map_Village nach Abschluss
            "Map_Town.tmx",    # 3. Map: Map_Town nach Abschluss
            "Map3Castle.tmx"   # 4. Map: Map3Castle nach Abschluss
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
            # Map_Town und Map3Castle: keine Sammelobjekte
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
                if VERBOSE_LOGS:
                    print(f"✅ Sammelobjekte für {map_filename} konfiguriert")
            else:
                # Objekte für nicht-definierte Maps deaktivieren
                for item in self.collectible_items.values():
                    item['available'] = False
                if VERBOSE_LOGS:
                    print(f"⚠️ Keine Sammelobjekte für {map_filename} definiert")
        except Exception as e:
            if VERBOSE_LOGS:
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

    def load_map(self):
        """Lädt die Spielkarte und extrahiert Spawn-Punkte"""
        try:
            # ✅ Lade die aktuelle Map aus der Progression
            current_map = self.map_progression[self.current_map_index]
            map_path = path.join(MAP_DIR, current_map)
            
            self.map_loader = MapLoader(map_path)
            
            if self.map_loader and self.map_loader.tmx_data:
                self.use_map = True
                if VERBOSE_LOGS:
                    print(f"✅ Map geladen: {map_path}")
                
                # Kamera an Map-Grenzen binden
                self.camera.set_map_bounds(self.map_loader.width, self.map_loader.height)
                
                # Debug: Zeige alle verfügbaren Layer UND Object Groups
                if VERBOSE_LOGS:
                    print("🗂️ Verfügbare Layer:")
                    for layer in self.map_loader.tmx_data.visible_layers:
                        layer_type = "Objekt" if hasattr(layer, 'objects') else "Tile"
                        object_count = len(layer.objects) if hasattr(layer, 'objects') else 0
                        layer_name = getattr(layer, 'name', 'None')
                        print(f"  - {layer_name} ({layer_type}) - {object_count} Objekte")
                
                # Debug: Zeige Object Groups separat (robustere Fehlerbehandlung)
                if hasattr(self.map_loader.tmx_data, 'objectgroups') and VERBOSE_LOGS:
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
                elif VERBOSE_LOGS:
                    print("🗂️ Keine Object Groups gefunden")
            
                # Datengesteuertes Spawning: Spieler-Position aus Tiled-Map extrahieren
                self._configure_collectibles_for_map(current_map)
                self.spawn_entities_from_map()

                # Gegner aus der Map spawnen (ObjectGroup "Enemy" etc.)
                # und direkt Health-Bars für die gespawnten Gegner hinzufügen
                self.respawn_enemies_only()
                
                # 🧙 The Great Beckalof spawnen (nur auf Map3.tmx)
                self._spawn_beckalof(current_map)
                
                # 🐉 Dragon Lord Boss spawnen (links vom Spieler zum Testen)
                player_x = self.game_logic.player.rect.centerx
                player_y = self.game_logic.player.rect.centery
                self._spawn_dragon_lord(player_x, player_y)
                
                # 🎰 Gambler NPC spawnen (oben links vom Spieler)
                self._spawn_gambler(player_x, player_y)
                
                # 🏪 Shopkeeper NPC spawnen (nur auf Map3 und Map_Town)
                self._spawn_shopkeeper(current_map, player_x, player_y)
                
                # ⚔️ Soldat NPC spawnen (nur auf Map_Town)
                self._spawn_soldier(current_map, player_x, player_y)
                
                # ⚔️ Ritter-Begleiter spawnen (wenn angeheuert)
                self._spawn_knight_companion(player_x, player_y)
                
            else:
                if VERBOSE_LOGS:
                    print(f"❌ Map konnte nicht geladen werden: {map_path}")
                self.map_loader = None
                self.use_map = False
                # Fallback
                self.game_logic.player.rect.bottom = self.screen.get_height() - 200
                self.game_logic.player.rect.centerx = self.screen.get_width() // 2
                self.game_logic.player.update_hitbox()
                
        except Exception as e:
            if VERBOSE_LOGS:
                print(f"❌ Fehler beim Laden der Map: {e}")
            import traceback
            traceback.print_exc()
            
            self.map_loader = None
            self.use_map = False
            # Fallback: Standard-Position
            self.game_logic.player.rect.bottom = self.screen.get_height() - 200
            self.game_logic.player.rect.centerx = self.screen.get_width() // 2
            self.game_logic.player.update_hitbox()
            if VERBOSE_LOGS:
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
                if VERBOSE_LOGS:
                    print(f"🔍 Prüfe Objekt-Layer: {getattr(layer, 'name', 'None')}")
                for obj in layer.objects:
                    if VERBOSE_LOGS:
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
                            if VERBOSE_LOGS:
                                print(f"⚠️ Spawn-Position ({spawn_x}, {spawn_y}) ist außerhalb der Map (0,0 - {map_width},{map_height})")
                            # Korrigiere zu gültiger Position in der Mitte der Map
                            spawn_x = map_width // 2
                            spawn_y = map_height // 2
                            if VERBOSE_LOGS:
                                print(f"🔧 Korrigiert zu Map-Mitte: ({spawn_x}, {spawn_y})")
                        
                        self.game_logic.player.rect.centerx = spawn_x
                        self.game_logic.player.rect.centery = spawn_y
                        self.game_logic.player.update_hitbox()
                        player_spawned = True
                        if VERBOSE_LOGS:
                            print(f"✅ Player gespawnt bei ({spawn_x}, {spawn_y}) von Objekt '{obj.name}'")
                        
                        break
                    
                    elif obj.name and 'enemy' in obj.name.lower():
                        if VERBOSE_LOGS:
                            print(f"🎯 Enemy-Spawn gefunden: {obj.name} bei ({obj.x}, {obj.y})")
                        # Enemy-Spawning wird vom EnemyManager gehandhabt
            
            if player_spawned:
                break  # Stoppe die Suche nach dem ersten gefundenen Player-Spawn

        # 2. NEU: Durchsuche Object Groups nach Spawn-Objekten (per Name-Lookup)
        if not player_spawned and hasattr(self.map_loader.tmx_data, 'objectgroups'):
            if VERBOSE_LOGS:
                print("🔍 Prüfe Object Groups...")
            try:
                # Suche nach Object Groups mit Namen wie "spawn", "Spawn", etc.
                spawn_group_names = ['spawn', 'Spawn', 'SPAWN', 'player_spawn', 'Player']
                
                for group_name in spawn_group_names:
                    try:
                        spawn_layer = self.map_loader.tmx_data.get_layer_by_name(group_name)
                        if spawn_layer and hasattr(spawn_layer, 'objects'):
                            if VERBOSE_LOGS:
                                print(f"  ✅ Spawn Object Group gefunden: '{group_name}'")
                            
                            # Typing: cast for Pylance (pytmx ObjectGroup has 'objects')
                            for obj in cast(Any, spawn_layer).objects:
                                obj_name = getattr(obj, 'name', None)
                                if VERBOSE_LOGS:
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
                                    if VERBOSE_LOGS:
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
                        if VERBOSE_LOGS:
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
                                    if VERBOSE_LOGS:
                                        print(f"✅ Player via XML-Fallback bei ({spawn_x}, {spawn_y}) aus ObjectGroup 'Spawn'/'spawn' gespawnt")
                                    break
                        if spawn_found:
                            break
            except Exception as e:
                if VERBOSE_LOGS:
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
                    # Map_Town: Kreuzung in der Mitte der Stadt
                    self.game_logic.player.rect.centerx = 1248
                    self.game_logic.player.rect.centery = 1024
                    self.game_logic.player.update_hitbox()
                    print("✅ Player an der Kreuzung auf Map_Town gespawnt (1248, 1024)")
                    
                elif 'Map3Castle.tmx' in map_filename:
                    # Map3Castle: Spawn-Punkt oben rechts (aus Tiled)
                    self.game_logic.player.rect.centerx = 2816
                    self.game_logic.player.rect.centery = 92
                    self.game_logic.player.update_hitbox()
                    print("✅ Player in Map3Castle gespawnt (2816, 92)")
                    
                else:
                    # Unbekannte Map: Allgemeine Standard-Position
                    self.game_logic.player.rect.centerx = 400
                    self.game_logic.player.rect.centery = 300
                    self.game_logic.player.update_hitbox()
                    print("✅ Player in unbekannter Map Standard-Position gespawnt (400, 300)")

    def _spawn_beckalof(self, map_name: str):
        """Spawnt The Great Beckalof NPC auf Map3.tmx und Map_Town.tmx."""
        is_map3 = 'Map3.tmx' in map_name and 'Castle' not in map_name
        is_town = map_name == 'Map_Town.tmx'

        if not is_map3 and not is_town:
            self.beckalof_npc = None
            reset_beckalof()
            return
        
        try:
            if is_town:
                # Map_Town: rechts unten, abseits vom Soldaten / Shopkeeper
                player_x = self.game_logic.player.rect.centerx if self.game_logic and self.game_logic.player else 400
                player_y = self.game_logic.player.rect.centery if self.game_logic and self.game_logic.player else 400
                beckalof_x = player_x + 350
                beckalof_y = player_y + 120
            else:
                # Map3: unten links
                beckalof_x = 150
                beckalof_y = 950
            
            reset_beckalof()
            self.beckalof_npc = BeckalofNPC(beckalof_x, beckalof_y)
            print(f"🧙 The Great Beckalof gespawnt bei ({beckalof_x}, {beckalof_y}) auf {map_name}")
        except Exception as e:
            print(f"⚠️ Fehler beim Spawnen von Beckalof: {e}")
            import traceback
            traceback.print_exc()
            self.beckalof_npc = None

    def _spawn_dragon_lord(self, player_spawn_x: int, player_spawn_y: int):
        """Spawnt den Dragon Lord - Intro-Cutscene auf Map3, Boss-Fight auf Map3Castle."""
        current_map = self.map_progression[self.current_map_index]
        is_first_map = 'Map3.tmx' in current_map and 'Castle' not in current_map
        is_castle_map = 'Map3Castle' in current_map
        
        if not is_first_map and not is_castle_map:
            self.dragon_lord = None
            return
        
        # Intro-Map: Dragon Lord nicht erneut spawnen wenn Intro schon gezeigt wurde (Retry)
        if is_first_map and getattr(self, '_dragon_intro_shown', False):
            self.dragon_lord = None
            print("Dragon Lord Intro bereits gezeigt - nicht erneut spawnen (Retry)")
            return
        
        try:
            # Position bestimmen
            dragon_x = player_spawn_x + 150
            dragon_y = player_spawn_y
            
            if is_castle_map:
                # Feste Fallback-Position für Map3Castle (Boss-Arena Mitte)
                dragon_x = 1800
                dragon_y = 1700
            
            # Versuche Position aus TMX Boss-Objektgruppe zu lesen
            if self.map_loader and self.map_loader.tmx_data:
                try:
                    from pytmx import TiledObjectGroup
                except ImportError:
                    TiledObjectGroup = None
                for layer in self.map_loader.tmx_data.layers:
                    is_obj_group = isinstance(layer, TiledObjectGroup) if TiledObjectGroup else hasattr(layer, '__iter__')
                    if (getattr(layer, 'name', '') or '').lower() == 'boss' and is_obj_group:
                        for obj in layer:
                            obj_name = (getattr(obj, 'name', '') or '').lower()
                            if obj_name in ('dragonlord', 'dragon_lord', 'dragon lord', 'dragon'):
                                dragon_x = int(float(getattr(obj, 'x', 0) or 0))
                                dragon_y = int(float(getattr(obj, 'y', 0) or 0))
                                break
                        break
            
            self.dragon_lord = DragonLord(dragon_x, dragon_y)
            
            # Health Bar für Dragon Lord erstellen
            from ui.health_bar_py27 import StandardHealthBarRenderer
            dragon_renderer = StandardHealthBarRenderer(
                health_color_full=(200, 50, 50),     # Dunkelrot für Boss
                health_color_medium=(255, 100, 0),   # Orange
                health_color_low=(100, 0, 0),        # Sehr dunkelrot
                border_width=2
            )
            self.health_bar_manager.add_entity(
                self.dragon_lord,
                renderer=dragon_renderer,
                width=80,
                height=8,
                offset_y=-10
            )
            
            # Intro-Dialog verzögern (dialogue_box noch nicht initialisiert)
            # Wird in update() beim ersten Frame angezeigt
            # Bei Retry (Noch mal) wird der Dialog NICHT erneut gezeigt
            if not getattr(self, '_dragon_intro_shown', False):
                self._dragon_intro_pending = True
            else:
                self._dragon_intro_pending = False
                # Dragon Lord direkt kampfbereit machen
                self.dragon_lord.intro_shown = True
            # Merken ob es ein Intro-Cutscene ist (Dragon Lord verschwindet danach)
            self._dragon_intro_only = is_first_map
            
            print(f"Dragon Lord gespawnt bei ({dragon_x}, {dragon_y}) [{'Intro' if is_first_map else 'Boss-Fight'}]")
        except Exception as e:
            print(f"Fehler beim Spawnen von Dragon Lord: {e}")
            import traceback
            traceback.print_exc()
            self.dragon_lord = None

    def _show_dragon_intro_dialog(self):
        """Zeigt den Dragon Lord Dialog - Intro-Cutscene (Map1) oder Boss-Fight (Castle)."""
        print("=== Dragon Lord Intro Dialog wird gestartet ===")
        if not self.dragon_lord or not self.dialogue_box:
            print(f"  Abbruch: dragon_lord={self.dragon_lord is not None}, dialogue_box={self.dialogue_box is not None}")
            return
            
        level_ref = self
        dragon_ref = self.dragon_lord
        is_intro_only = getattr(self, '_dragon_intro_only', False)
        
        if is_intro_only:
            # === INTRO-CUTSCENE auf der ersten Map ===
            def show_part2():
                def show_part3():
                    def remove_dragon():
                        if dragon_ref:
                            dragon_ref.intro_shown = True
                            if dragon_ref in level_ref.health_bar_manager.health_bars:
                                level_ref.health_bar_manager.remove_entity(dragon_ref)
                            level_ref.dragon_lord = None
                            print("Dragon Lord ist nach Intro verschwunden!")
                    level_ref.dialogue_box.open(
                        "Versuch es gar nicht erst... HAHAHA!",
                        speaker="Dragon Lord",
                        on_close=remove_dragon
                    )
                level_ref.dialogue_box.open(
                    "Du wirst ihn niemals wiedersehen!",
                    speaker="Dragon Lord",
                    on_close=show_part3
                )
            
            print("=== Dragon Lord Intro-Cutscene ===")
            self.dialogue_box.open(
                "HAHA! Dobo ist bei mir!",
                speaker="Dragon Lord",
                on_close=show_part2
            )
        else:
            # === BOSS-FIGHT Dialog auf Map3Castle ===
            def show_second_part():
                print("=== Dragon Lord Boss Dialog Teil 2 ===")
                level_ref.dialogue_box.open(
                    "Jetzt wirst du fallen!",
                    speaker="Dragon Lord",
                    on_close=lambda: setattr(dragon_ref, 'intro_shown', True)
                )
            
            print("=== Dragon Lord Boss-Fight Dialog ===")
            self.dialogue_box.open(
                "Du hast es also bis hierher geschafft... Beeindruckend.",
                speaker="Dragon Lord",
                on_close=show_second_part
            )

    def _spawn_gambler(self, player_spawn_x: int, player_spawn_y: int):
        """Spawnt den Gambler NPC neben dem Dragon Lord."""
        try:
            # Position: Neben dem Dragon Lord (der bei player_x - 200 ist)
            # Gambler steht links vom Dragon Lord
            gambler_x = player_spawn_x - 300  # 300 Pixel links (neben Dragon Lord)
            gambler_y = player_spawn_y        # Gleiche Höhe
            
            self.gambler_npc = GamblerNPC(gambler_x, gambler_y)
            
            # Blackjack-Spiel initialisieren
            screen_size = (self.screen.get_width(), self.screen.get_height())
            self.blackjack_game = BlackjackGame(screen_size)
            
            # Callback für Gewinn/Verlust
            def on_game_end(coins_change: int):
                if self.game_logic and self.game_logic.player:
                    self.game_logic.player.coins += coins_change
                    if coins_change > 0:
                        print(f"💰 Du hast {coins_change} Münze(n) gewonnen! ({self.game_logic.player.coins} total)")
                    elif coins_change < 0:
                        print(f"💸 Du hast {-coins_change} Münze(n) verloren! ({self.game_logic.player.coins} total)")
            
            self.blackjack_game.on_game_end = on_game_end
            
            print(f"🎰 Gambler NPC gespawnt bei ({gambler_x}, {gambler_y})")
        except Exception as e:
            print(f"⚠️ Fehler beim Spawnen von Gambler: {e}")
            import traceback
            traceback.print_exc()
            self.gambler_npc = None
            self.blackjack_game = None

    def _spawn_shopkeeper(self, map_name: str, player_spawn_x: int, player_spawn_y: int):
        """Spawnt den Shopkeeper NPC – nur auf Map3.tmx und Map_Town.tmx."""
        # Nur auf erster und vorletzter Map
        if map_name not in ("Map3.tmx", "Map_Town.tmx"):
            self.shopkeeper_npc = None
            return
        try:
            # Rechts vom Spieler (gegenüber vom Gambler)
            shop_x = player_spawn_x + 250
            shop_y = player_spawn_y - 50
            self.shopkeeper_npc = ShopkeeperNPC(shop_x, shop_y)
            print(f"🏪 Shopkeeper NPC gespawnt bei ({shop_x}, {shop_y}) auf {map_name}")
        except Exception as e:
            print(f"⚠️ Fehler beim Spawnen von Shopkeeper: {e}")
            import traceback
            traceback.print_exc()
            self.shopkeeper_npc = None

    def _open_shop(self):
        """Öffnet das Shop-UI."""
        if not self.shop_ui or not self.game_logic or not self.game_logic.player:
            return
        self.shop_ui.open(self.shop_manager, self.game_logic.player)
        # Merchant-Animation in Dialog-Modus setzen
        if self.shopkeeper_npc:
            self.shopkeeper_npc.start_dialog()

    def _spawn_soldier(self, map_name: str, player_spawn_x: int, player_spawn_y: int):
        """Spawnt den Soldaten NPC – nur auf Map_Town.tmx."""
        if map_name != "Map_Town.tmx":
            self.soldier_npc = None
            return
        try:
            # Soldat steht am Eingang der Stadt (links vom Spieler)
            soldier_x = player_spawn_x - 200
            soldier_y = player_spawn_y + 80
            self.soldier_npc = SoldierNPC(soldier_x, soldier_y)
            self._town_kill_count = 0
            self._soldier_talked = False
            self._town_respawn_timer = 0.0
            print(f"⚔️ Soldat NPC gespawnt bei ({soldier_x}, {soldier_y}) auf {map_name}")
        except Exception as e:
            print(f"⚠️ Fehler beim Spawnen von Soldat: {e}")
            import traceback
            traceback.print_exc()
            self.soldier_npc = None

    def _spawn_knight_companion(self, player_x: int, player_y: int):
        """Spawnt den Ritter-Begleiter wenn er angeheuert wurde."""
        if not self._soldier_recruited:
            self.knight_companion = None
            return
        try:
            # Begleiter rechts hinter dem Spieler spawnen
            comp_x = player_x + 60
            comp_y = player_y + 10
            self.knight_companion = KnightCompanion(comp_x, comp_y)
            # Hindernisse setzen falls vorhanden
            if hasattr(self, 'obstacle_sprites') and self.obstacle_sprites:
                self.knight_companion.set_obstacles(self.obstacle_sprites)
            print(f"⚔️ Ritter-Begleiter gespawnt bei ({comp_x}, {comp_y})")
        except Exception as e:
            print(f"⚠️ Fehler beim Spawnen des Ritter-Begleiters: {e}")
            import traceback
            traceback.print_exc()
            self.knight_companion = None

    def _open_soldier_dialogue(self):
        """Öffnet den Dialog mit dem Soldaten (mehrstufig beim ersten Mal)."""
        if not self.soldier_npc or not self.dialogue_box:
            return

        kills = self._town_kill_count
        needed = self._town_kills_required

        # --- Erstes Gespräch: Spieler fragt, Ritter erklärt, dann Auftrag ---
        if not self._soldier_talked:
            # Schritt 1: Spieler fragt
            step1_text = (
                'Zauberer:\n'
                '"Was ist hier passiert?! Der Wald... alles ist verwüstet!\n'
                'Wer hat das getan?"'
            )

            def _step2():
                # Schritt 2: Ritter antwortet – Dragon Lord Erklärung
                step2_text = (
                    'Ritter Konrad (Stadtwache):\n'
                    '"Das war der Dragon Lord. Er versucht unsere Welt\n'
                    'zu zerstören – Dorf für Dorf, Wald für Wald.\n'
                    'Wir müssen ihn aufhalten, bevor es zu spät ist!"'
                )
                self.dialogue_box.open(
                    text=step2_text,
                    speaker="Ritter Konrad",
                    on_close=_step3
                )

            def _step3():
                # Schritt 3: Ritter gibt Auftrag
                step3_text = (
                    f'Ritter Konrad:\n'
                    f'"Aber du bist noch nicht bereit, Zauberer.\n'
                    f'Trainiere zuerst – besiege {needed} Kreaturen hier\n'
                    f'und kauf dir bessere Ausrüstung beim Händler.\n'
                    f'Erst dann hast du eine Chance gegen den Dragon Lord."\n\n'
                    f'⚔️ Besiegte Gegner: {kills}/{needed}'
                )
                self._soldier_talked = True
                self.dialogue_box.open(
                    text=step3_text,
                    speaker="Ritter Konrad"
                )

            self.dialogue_box.open(
                text=step1_text,
                speaker="Zauberer",
                on_close=_step2
            )

        # --- Folge-Gespräche: Kills noch nicht genug ---
        elif kills < needed:
            text = (
                f'Ritter Konrad:\n'
                f'"Du brauchst noch mehr Training, Zauberer.\n'
                f'Besiege die Kreaturen und komm wieder!"\n\n'
                f'⚔️ Besiegte Gegner: {kills}/{needed}'
            )
            self.dialogue_box.open(
                text=text,
                speaker="Ritter Konrad"
            )

        # --- Bereits angeheuert → nur Weiterziehen oder Trainieren ---
        elif self._soldier_recruited:
            text = (
                f'Ritter Konrad:\n'
                f'"Mein neues Schwert ist bereit, Zauberer!\n'
                f'Ich kämpfe an deiner Seite.\n'
                f'Willst du weiterziehen oder noch trainieren?"'
            )
            def on_choice_recruited(idx):
                if idx == 0:
                    print("⚔️ Spieler zieht mit Ritter Konrad weiter!")
                    self.trigger_level_completion()
                else:
                    print("⚔️ Spieler bleibt zum Trainieren")

            self.dialogue_box.open_with_choices(
                text=text,
                choices=["Ja, vorwärts!", "Noch etwas trainieren..."],
                on_choice=on_choice_recruited,
                speaker="Ritter Konrad"
            )

        # --- Genug Kills – Wahl anbieten (mit Anheuer-Option) ---
        else:
            player_coins = 0
            if self.game_logic and self.game_logic.player:
                player_coins = self.game_logic.player.coins

            text = (
                f'Ritter Konrad:\n'
                f'"Beeindruckend, Zauberer! Du hast {kills} Feinde bezwungen.\n'
                f'Du bist bereit für den Dragon Lord.\n'
                f'Allerdings... der Dragon Lord hat mein Schwert zerstört.\n'
                f'Für 100 Gold könnte ich mir ein neues kaufen\n'
                f'und an deiner Seite kämpfen!"\n\n'
                f'💰 Dein Gold: {player_coins}'
            )
            def on_choice(idx):
                if idx == 0:
                    print("⚔️ Spieler entscheidet sich weiterzuziehen (ohne Ritter)!")
                    self.trigger_level_completion()
                elif idx == 1:
                    # Ritter anheuern
                    if self.game_logic and self.game_logic.player:
                        if self.game_logic.player.coins >= 100:
                            self.game_logic.player.coins -= 100
                            self._soldier_recruited = True
                            print(f"⚔️ Ritter Konrad angeheuert! (-100 Gold, verbleibend: {self.game_logic.player.coins})")
                            self.dialogue_box.open(
                                text=(
                                    'Ritter Konrad:\n'
                                    '"Ausgezeichnet! Mit einem neuen Schwert\n'
                                    'werde ich den Dragon Lord in Stücke hauen!\n'
                                    'Lass uns gemeinsam kämpfen, Zauberer!"'
                                ),
                                speaker="Ritter Konrad"
                            )
                            self.show_styled_message("⚔️ Ritter Konrad schließt sich dir an! (-100 Gold)")
                        else:
                            print("⚔️ Nicht genug Gold für den Ritter")
                            self.dialogue_box.open(
                                text=(
                                    'Ritter Konrad:\n'
                                    '"Du hast leider nicht genug Gold, Zauberer.\n'
                                    'Ich brauche 100 Gold für ein neues Schwert.\n'
                                    'Besiege mehr Gegner oder finde Schätze!"'
                                ),
                                speaker="Ritter Konrad"
                            )
                else:
                    print("⚔️ Spieler bleibt zum Trainieren")

            self.dialogue_box.open_with_choices(
                text=text,
                choices=[
                    "Ja, ich gehe allein weiter!",
                    "Ritter anheuern (100 Gold) ⚔️",
                    "Noch etwas trainieren..."
                ],
                on_choice=on_choice,
                speaker="Ritter Konrad"
            )

    def _start_blackjack(self):
        """Öffnet den Gambler-Dialog – beim ersten Mal mit Intro, danach direkt Spiel."""
        if not self.blackjack_game or not self.game_logic or not self.game_logic.player:
            return
        
        # Gambler-Animation in Dialog-Modus
        if self.gambler_npc:
            self.gambler_npc.start_dialog()
        
        if not self._gambler_introduced:
            # Erster Dialog: Intro-Geschichte mit Auswahl
            self._gambler_introduced = True
            
            def on_choice(choice_index: int):
                if choice_index == 0:
                    # Spielen!
                    player_coins = self.game_logic.player.coins
                    self.blackjack_game.player_coins = player_coins
                    self.blackjack_game.start_invite(player_coins)
                    print(f"🎰 Kronenschlag-Einladung gestartet (Spieler hat {player_coins} Münzen)")
                else:
                    # Weggehen
                    if self.gambler_npc:
                        self.gambler_npc.end_dialog()
                    print("🎰 Spieler lehnt das Kronenschlag-Spiel ab")
            
            self.dialogue_box.open_with_choices(
                text=(
                    "Psst! Komm her, Fremder! Ich war einst Zauberbrauerin, aber "
                    "dieses ewige Rühren und Mischen... so LANGWEILIG! "
                    "Also hab ich etwas viel Spannenderes erfunden: "
                    "Das Kronenschlag! Ein Kartenduell, bei dem Verstand und Glück "
                    "entscheiden. Einsatz: eine Münze. Traust du dich?"
                ),
                choices=["Ja, ich fordere dich heraus!", "Nein, vielleicht später..."],
                on_choice=on_choice,
                speaker="Die Kartenlegerin"
            )
        else:
            # Bereits vorgestellt – direkt zum Spiel
            player_coins = self.game_logic.player.coins
            self.blackjack_game.player_coins = player_coins
            self.blackjack_game.start_invite(player_coins)
            print(f"🎰 Kronenschlag-Einladung gestartet (Spieler hat {player_coins} Münzen)")

    def _open_beckalof_dialogue(self):
        """Öffnet einen Dialog mit The Great Beckalof."""
        if not self.beckalof_npc or not self.dialogue_box:
            return
        
        current_map = self.map_progression[self.current_map_index]
        
        # Spezieller Dialog auf Map_Town: Geschenk + Glückwunsch
        if current_map == 'Map_Town.tmx':
            if not self._beckalof_gift_given:
                # Erste Begegnung auf Map_Town: 25 Münzen schenken
                self._beckalof_gift_given = True
                if self.game_logic and self.game_logic.player:
                    self.game_logic.player.coins += 25
                    print(f"🪙 Beckalof schenkt 25 Münzen! Spieler hat jetzt {self.game_logic.player.coins} Münzen.")
                self.dialogue_box.open(
                    "Mein junger Freund! Ich habe gehört, du ziehst gegen den Dragon Lord! "
                    "Hier, nimm diese 25 Münzen – kauf dir was Nützliches im Shop. "
                    "Und vergiss nicht: Eine heiße Milchschokolade vor dem Kampf wirkt Wunder! "
                    "Viel Erfolg, ich glaube an dich! 💰",
                    speaker="The Great Beckalof"
                )
            else:
                # Wiederholte Gespräche auf Map_Town
                self.dialogue_box.open(
                    "Du bist noch hier? Geh, besiege den Dragon Lord! "
                    "Und denk dran: Milchschokolade macht unsterblich! "
                    "...Naja, fast unsterblich. Viel Glück! 🍫",
                    speaker="The Great Beckalof"
                )
            return
        
        # Standard-Dialog auf anderen Maps (Milchschokolade-Geschichten)
        dialogue_text = self.beckalof_npc.get_next_dialogue()
        self.dialogue_box.open(dialogue_text, speaker="The Great Beckalof")
        print("💬 Beckalof erzählt von Milchschokolade!")

    def _open_npc_dialogue(self, zone_id: str):
        """Öffnet einen Dialog mit einem NPC basierend auf der Zone-ID."""
        if zone_id not in self.interaction_zones:
            return
        
        zone = self.interaction_zones[zone_id]
        if not self.dialogue_box or self.dialogue_box.is_active:
            return
        
        # Prüfe ob bereits abgeschlossen
        if zone.get('completed', False):
            return
        
        # Alle Items gesammelt → Abschluss-Dialog mit Bestätigung
        if zone.get('items_ready', False):
            self._open_completion_dialogue(zone_id, zone)
            return
        
        # Normaler Auftrags-Dialog
        self.dialogue_box.open(zone.get('text', ''))
        zone['dialogue_shown'] = True
        print(f"💬 NPC-Dialog geöffnet: {zone_id}")

        # 📜 Quest aktivieren wenn dieser NPC eine Sammel-Aufgabe hat
        self._activate_quest_for_zone(zone_id, zone)

    def _open_completion_dialogue(self, zone_id: str, zone: dict):
        """Öffnet den Abschluss-Dialog wenn alle Gegenstände gesammelt wurden.
        Der NPC fragt, ob der Spieler weiterreisen möchte (Ja/Warte)."""
        # NPC-Name ableiten
        npc_name = zone_id.replace('_dialog', '').replace('_', ' ').title()
        raw_text = zone.get('text', '')
        if ':' in raw_text.split('\n')[0]:
            npc_name = raw_text.split('\n')[0].split(':')[0].strip()

        # Abschluss-Text zusammenbauen
        completion = zone.get('completion_text', 'Alle Gegenstände gefunden!')
        dialogue_text = (
            f"{npc_name}:\n"
            f"\"{completion}\n"
            f"Bist du bereit, weiterzuziehen?\""
        )

        def _on_choice(choice_index: int):
            """Wird aufgerufen wenn der Spieler eine Auswahl trifft."""
            if choice_index == 0:
                # "Ja, weiter!" gewählt
                zone['completed'] = True
                zone['items_ready'] = False
                self.quest_manager.complete_quest(zone_id)
                print(f"📜 Quest abgeschlossen: {zone_id}")
                print("Starte Level-Abschluss...")
                self.trigger_level_completion()
            else:
                # "Warte..." gewählt - Dialog schließt sich, Spieler bleibt
                print(f"⏳ Spieler wartet noch auf Map ({zone_id})")

        self.dialogue_box.open_with_choices(
            dialogue_text,
            choices=["Ja, weiter!", "Warte..."],
            on_choice=_on_choice
        )
        print(f"💬 Abschluss-Dialog mit Auswahl geöffnet: {zone_id}")

    def _activate_quest_for_zone(self, zone_id: str, zone: dict):
        """Erstellt und aktiviert eine Quest basierend auf den Daten einer Interaktionszone."""
        if not zone.get('is_checkpoint', False):
            return
        if zone.get('completed', False):
            return

        required = zone.get('required_items', [])
        if not required:
            return

        # Quest nicht doppelt anlegen
        if self.quest_manager.has_quest(zone_id):
            return

        # NPC-Name aus dem Dialog-Text ableiten (erster Teil vor dem Doppelpunkt)
        npc_name = zone_id.replace('_dialog', '').replace('_', ' ').title()
        raw_text = zone.get('text', '')
        if ':' in raw_text.split('\n')[0]:
            npc_name = raw_text.split('\n')[0].split(':')[0].strip()

        # Freundliche Item-Namen aus collectible_items holen
        item_labels = {}
        if hasattr(self, 'collectible_items'):
            for k, v in self.collectible_items.items():
                item_labels[k] = v.get('name', k.title())

        objectives = []
        for item_key in required:
            label = item_labels.get(item_key, item_key.title())
            already_done = item_key in self.quest_items
            objectives.append(QuestObjective(key=item_key, label=f"{label} finden", done=already_done))

        # Titel aus der completion_text oder generisch
        title = "Gegenstände sammeln"
        if zone_id == 'elara_dialog':
            title = "Brücke reparieren"
        elif zone_id == 'brann_dialog':
            title = "Elixier brauen"

        quest = Quest(
            id=zone_id,
            title=title,
            npc_name=npc_name,
            objectives=objectives,
        )
        self.quest_manager.add_quest(quest)
        print(f"📜 Quest aktiviert: {quest.title} ({quest.progress_text})")

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
                sprite: Any = pygame.sprite.Sprite()
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
        
        try:
            from core.settings import VERBOSE_LOGS
        except Exception:
            VERBOSE_LOGS = False
        if VERBOSE_LOGS:
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
            if VERBOSE_LOGS:
                print(f"✅ Health-Bar für {type(enemy).__name__} hinzugefügt (HP: {enemy.max_health})")
        except Exception as e:
            print(f"⚠️ Fehler beim Hinzufügen der Enemy Health-Bar: {e}")
    
    def handle_event(self, event):
        """Behandelt Input-Events - Erweitert für Joystick-Support"""
        # 🏆 Finale-Sequenz konsumiert alle Events
        if self._finale_active:
            self._handle_finale_event(event)
            return
        
        # If dialogue is active, consume advance keys and block gameplay events
        if self.dialogue_box and self.dialogue_box.is_active:
            if self.dialogue_box.handle_event(event):
                return
            # Allow ESC to close dialogue
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.dialogue_box.close()
                return

        # Timer für styled message
        if event.type == pygame.USEREVENT + 1:
            self.show_interaction_text = False
            self._styled_message_active = False
            pygame.time.set_timer(pygame.USEREVENT + 1, 0)  # Timer deaktivieren
        # Timer für Countdown und Rückkehr zum Hauptmenü
        elif event.type == pygame.USEREVENT + 2:
            if self.countdown_active:
                # Map3Castle (finale Map) - Countdown nach Spielabschluss
                if self.current_map_index == 3 and self.map_completed:
                    self.countdown_timer -= 1
                    if self.countdown_timer <= 0:
                        pygame.time.set_timer(pygame.USEREVENT + 2, 0)
                        self.countdown_active = False
                        self.trigger_save_game(1)
                        if hasattr(self, 'main_game') and self.main_game:
                            self.main_game.return_to_menu()
                # Map_Village - Countdown nach Brann Quest
                else:
                    brann_quest = self.interaction_zones.get('brann_dialog', {})
                    if self.current_map_index == 1 and brann_quest.get('completed', False):
                        self.countdown_timer -= 1
                        if self.countdown_timer <= 0:
                            pygame.time.set_timer(pygame.USEREVENT + 2, 0)
                            self.countdown_active = False
                            self.trigger_save_game(1)
                            if hasattr(self, 'main_game') and self.main_game:
                                self.main_game.return_to_menu()
        # � Shop-Event-Handling (HÖCHSTE Priorität)
        if self.shop_ui and self.shop_ui.is_active:
            if self.shop_ui.handle_event(event):
                return  # Event wurde von Shop konsumiert
        # �🎰 Blackjack-Event-Handling (HÖCHSTE Priorität - VOR Input System!)
        if self.blackjack_game and self.blackjack_game.is_active:
            if self.blackjack_game.handle_event(event):
                return  # Event wurde von Blackjack konsumiert - blockiert ALLES andere
        
        # Universal Input System für Actions verwenden (nur wenn Blackjack nicht aktiv)
        action = self.input_system.handle_event(event)
        
        # Wenn Dialog aktiv ist: Hardware- oder Action-System-Events für Weiter/Schließen nutzen
        if (self.dialogue_box and self.dialogue_box.is_active) and action:
            if action in ('brew', 'cast_magic'):
                self.dialogue_box.advance()
                return
            if action in ('clear_magic', 'reset'):
                self.dialogue_box.close()
                return
            # Sonstige Actions während Dialog ignorieren
            return
        
        if action and not (self.dialogue_box and self.dialogue_box.is_active):
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
                # � Shop-Event-Handling (höchste Priorität)
                if self.shop_ui and self.shop_ui.is_active:
                    return  # Shop übernimmt Events selbst
                # 🎰 Blackjack-Event-Handling (höchste Priorität)
                elif self.blackjack_game and self.blackjack_game.is_active:
                    return  # Blackjack übernimmt Events selbst
                # 🏪 Shopkeeper NPC Interaktion
                elif self.shopkeeper_npc and self.shopkeeper_npc.can_interact:
                    self._open_shop()
                # ⚔️ Soldat NPC Interaktion
                elif self.soldier_npc and self.soldier_npc.can_interact:
                    self._open_soldier_dialogue()
                # 🎰 Gambler NPC Interaktion
                elif self.gambler_npc and self.gambler_npc.can_interact:
                    self._start_blackjack()
                # Prüfe erst ob ein NPC in der Nähe ist für Dialog
                elif self.beckalof_npc and self.beckalof_npc.can_interact:
                    self._open_beckalof_dialogue()
                elif self.active_npc_zone:
                    self._open_npc_dialogue(self.active_npc_zone)
                else:
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
            elif event.key == pygame.K_k:
                # 🔧 DEBUG: K-Taste zum Überspringen zum nächsten Level
                if self.current_map_index < len(self.map_progression) - 1:
                    next_index = self.current_map_index + 1
                    next_map = self.map_progression[next_index]
                    print(f"⏭️ DEBUG: Überspringe zu Map {next_index}: {next_map}")
                    self.load_next_map(next_map, next_index)
                else:
                    print("⏭️ DEBUG: Bereits auf der letzten Map!")
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
            elif event.key == pygame.K_j:
                # 🔧 DEBUG: J-Taste für 200 Damage-Modus
                if self.game_logic and self.game_logic.player:
                    p = self.game_logic.player
                    if p.base_attack_damage == 200:
                        p.base_attack_damage = 30
                        p.attack_damage = int(p.base_attack_damage * p.get_damage_multiplier())
                        self.show_styled_message("🔧 Debug-Schaden AUS (normal)")
                        print("🔧 DEBUG: Schaden zurück auf normal (30)")
                    else:
                        p.base_attack_damage = 200
                        p.attack_damage = int(p.base_attack_damage * p.get_damage_multiplier())
                        self.show_styled_message("🔧 Debug-Schaden AN (200)")
                        print("🔧 DEBUG: Schaden auf 200 gesetzt!")
            elif event.key == pygame.K_F5:
                self.show_coordinates = not self.show_coordinates
                print(f"Koordinatenanzeige: {'An' if self.show_coordinates else 'Aus'}")
            
            # 🔧 DEBUG: U-Taste zum Überspringen der aktuellen Map

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
        try:
            from core.settings import VERBOSE_LOGS
        except Exception:
            VERBOSE_LOGS = False  # type: ignore
        if VERBOSE_LOGS:  # type: ignore[name-defined]
            print("🔧 Input-Status zurückgesetzt")
    
    def toggle_music(self):
        """Schaltet Musik ein/aus"""
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.pause()
        else:
            pygame.mixer.music.unpause()
    
    def update(self, dt):
        """Aktualisiert das Level und alle Entities"""
        # 🏆 Finale-Sequenz hat Vorrang
        if self._finale_active:
            self._update_finale(dt)
            return
        
        if not self.game_logic:
            return

        # 🐉 Dragon Lord Intro-Dialog anzeigen (verzögert, da dialogue_box erst später initialisiert wird)
        if getattr(self, '_dragon_intro_pending', False) and self.dragon_lord and not self.dragon_lord.intro_shown:
            self._dragon_intro_pending = False
            self._dragon_intro_shown = True
            self._show_dragon_intro_dialog()

        # Pausiert wenn Dialog ODER Blackjack ODER Shop aktiv ist
        blackjack_active = bool(self.blackjack_game and self.blackjack_game.is_active)
        shop_active = bool(self.shop_ui and self.shop_ui.is_active)
        paused = bool(self.dialogue_box and self.dialogue_box.is_active) or blackjack_active or shop_active

        # Bewegungs-Input anwenden, es sei denn, ein Dialog oder Blackjack oder Shop blockiert
        try:
            if self.input_system and hasattr(self.game_logic, 'player') and self.game_logic.player and not paused:
                move_vec = self.input_system.get_movement_vector()
                self.game_logic.player.set_direction(move_vec)
                self.game_logic.player.move(dt)
        except Exception as e:
            print(f"⚠️ Bewegungs-Update Fehler: {e}")

        # Game Logic Update (Animationen, Magie, etc.)
        # Provide enemies to game logic so magic projectiles can damage them
        try:
            enemies_list = self.enemy_manager.enemies.sprites() if hasattr(self.enemy_manager, 'enemies') else []
            # 🐉 Dragon Lord zur Enemy-Liste hinzufügen damit Magie ihn trifft
            if self.dragon_lord and self.dragon_lord.is_alive():
                enemies_list = list(enemies_list) + [self.dragon_lord]
        except Exception:
            enemies_list = None
        if not paused:
            result = self.game_logic.update(dt, enemies=enemies_list)
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
        else:
            # Keep systems alive without advancing gameplay
            try:
                self.game_logic.update(0, enemies=enemies_list)
            except Exception:
                pass

        # Feinde aktualisieren
        if not paused:
            # Ritter-Begleiter als mögliches Ziel für Gegner übergeben
            companions = []
            if self.knight_companion and self.knight_companion.is_alive():
                companions.append(self.knight_companion)
            self.enemy_manager.update(dt, self.game_logic.player, companions if companions else None)
            # 💰 Coin-Drops: Prüfe ob Gegner gestorben sind
            self._check_enemy_deaths()

        # 🧙 Beckalof NPC aktualisieren (Idle + Drinking Animationen)
        if self.beckalof_npc and not paused:
            self.beckalof_npc.update(dt)
            # Prüfe ob Spieler nah genug für Interaktion ist
            if hasattr(self.game_logic, 'player') and self.game_logic.player:
                self.beckalof_npc.check_player_distance(self.game_logic.player.rect)

        # 🐉 Dragon Lord Boss aktualisieren
        if self.dragon_lord and not paused:
            self.dragon_lord.update(dt, self.game_logic.player)

        # 🎰 Gambler NPC aktualisieren
        if self.gambler_npc and not paused:
            self.gambler_npc.update(dt)
            # Prüfe ob Spieler nah genug für Interaktion ist
            if hasattr(self.game_logic, 'player') and self.game_logic.player:
                player_pos = (self.game_logic.player.rect.centerx, self.game_logic.player.rect.centery)
                self.gambler_npc.check_player_nearby(player_pos)
        
        # 🎰 Blackjack-Spiel aktualisieren
        bj_now_active = bool(self.blackjack_game and self.blackjack_game.is_active)
        if bj_now_active:
            self.blackjack_game.update(dt)
        # Blackjack wurde gerade geschlossen → Gambler zurück in Idle
        if self._blackjack_was_active and not bj_now_active:
            if self.gambler_npc:
                self.gambler_npc.end_dialog()
        self._blackjack_was_active = bj_now_active

        # 🏪 Shopkeeper NPC aktualisieren
        if self.shopkeeper_npc and not paused:
            self.shopkeeper_npc.update(dt)
            if hasattr(self.game_logic, 'player') and self.game_logic.player:
                player_pos = (self.game_logic.player.rect.centerx, self.game_logic.player.rect.centery)
                self.shopkeeper_npc.check_player_nearby(player_pos)
        
        # 🏪 Shop-UI aktualisieren
        shop_now_active = bool(self.shop_ui and self.shop_ui.is_active)
        if shop_now_active:
            self.shop_ui.update(dt)
        # Shop wurde gerade geschlossen → Merchant zurück in Idle
        if self._shop_was_active and not shop_now_active:
            if self.shopkeeper_npc:
                self.shopkeeper_npc.end_dialog()
        self._shop_was_active = shop_now_active

        # ⚔️ Soldat NPC aktualisieren
        if self.soldier_npc and not paused:
            self.soldier_npc.update(dt)
            if hasattr(self.game_logic, 'player') and self.game_logic.player:
                player_pos = (self.game_logic.player.rect.centerx, self.game_logic.player.rect.centery)
                self.soldier_npc.check_player_nearby(player_pos)
        
        # ⚔️ Ritter-Begleiter aktualisieren
        if self.knight_companion and self.knight_companion.is_alive() and not paused:
            try:
                enemies_for_knight = list(self.enemy_manager.enemies.sprites()) if hasattr(self.enemy_manager, 'enemies') else []
                if self.dragon_lord and self.dragon_lord.is_alive():
                    enemies_for_knight.append(self.dragon_lord)
                self.knight_companion.update(dt, self.game_logic.player, enemies_for_knight)
            except Exception as e:
                print(f"⚠️ KnightCompanion Update-Fehler: {e}")

        # ⚔️ Map_Town: Gegner respawnen wenn wenige übrig
        if self.current_map_index == 2 and not paused and not self.map_completed:
            self._town_respawn_timer += dt
            alive_enemies = sum(1 for e in self.enemy_manager.enemies if getattr(e, 'alive_status', True))
            if alive_enemies <= 1 and self._town_respawn_timer >= self._town_respawn_interval:
                self._town_respawn_timer = 0.0
                self.respawn_enemies_only()
                print(f"🔄 Gegner respawnen auf Map_Town! (Kills: {self._town_kill_count}/{self._town_kills_required})")

        # Kamera aktualisieren
        if hasattr(self.game_logic, 'player'):
            self.camera.update(self.game_logic.player)

        # Health-Bars aktualisieren
        self.health_bar_manager.update(dt)

        # Interaktionszonen prüfen (unterdrücken wenn Dialog offen)
        if not paused:
            self.check_interaction_zones()

        # Sammelobjekte prüfen (Quest-Gegenstände einsammeln)
        if not paused:
            self.check_collectibles()
            self._check_coin_pickups()

        # Level-Abschluss prüfen
        if not paused:
            self.check_level_completion()
    
    def show_styled_message(self, message: str):
        """Zeigt eine Nachricht im gleichen Stil wie der Elara-Dialog an"""
        self.show_interaction_text = True
        self.interaction_text = message
        self._styled_message_active = True  # Verhindert Überschreibung durch check_interaction_zones
        # Zeitverzögerte Ausblendung nach 8 Sekunden
        pygame.time.set_timer(pygame.USEREVENT + 1, 8000)  # Event in 8 Sekunden
        
    def check_interaction_zones(self):
        """Überprüft ob der Spieler in der Nähe einer Interaktionszone ist (ohne automatischen Dialog)"""
        if not self.game_logic or not self.game_logic.player:
            return

        player_pos = pygame.math.Vector2(self.game_logic.player.rect.center)
        # Styled message nicht überschreiben (z.B. Dragon Lord besiegt Hinweis)
        if not getattr(self, '_styled_message_active', False):
            self.show_interaction_text = False
        self.active_npc_zone = None  # Reset aktiver NPC
        
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
                self.active_npc_zone = zone_id  # Merke welcher NPC in Reichweite ist
                
                # Prüfe ob dies ein Checkpoint ist und ob er abgeschlossen wurde
                if zone.get('is_checkpoint', False) and not zone.get('completed', False):
                    required_items = set(zone.get('required_items', []))
                    collected_items = set(self.quest_items)
                    missing_items = required_items - collected_items

                    # Nur bei Zustandsänderung loggen
                    prev_missing = zone.get('last_missing_items', None)
                    if prev_missing != missing_items:
                        if VERBOSE_LOGS:
                            print(f"Prüfe Items - Benötigt: {required_items}, Gesammelt: {collected_items}")
                        zone['last_missing_items'] = set(missing_items)

                    # Bei vollständigen Items: Bereit zum Abgeben (kein Auto-Teleport)
                    if not missing_items:
                        zone['items_ready'] = True  # NPC wartet auf Gespräch
                break
            else:
                # Beim Verlassen der Zone zurücksetzen
                zone['active'] = False
                if 'last_missing_items' in zone:
                    del zone['last_missing_items']
                if 'dialogue_shown' in zone:
                    del zone['dialogue_shown']

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

                # 📜 Quest-Fortschritt aktualisieren
                self.quest_manager.mark_item_collected(item_name)

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
        """Zeichnet sichtbare Sammelobjekte in die Welt mit Item-Icons."""
        if not self.collectible_items:
            return
        
        # Hole Item-Icons vom Renderer (falls vorhanden)
        item_icons = {}
        if self.renderer and hasattr(self.renderer, '_item_icons'):
            item_icons = self.renderer._item_icons
        
        for key, item in self.collectible_items.items():
            if item.get('available', True) and not item.get('collected', False):
                world_pos: pygame.math.Vector2 = item['pos']
                color = item.get('color', (200, 200, 200))
                
                # Größe für Item auf dem Boden (größer als vorher)
                size = 40
                rect = pygame.Rect(int(world_pos.x - size/2), int(world_pos.y - size/2), size, size)
                screen_rect = self.camera.apply_rect(rect)
                center = (screen_rect.centerx, screen_rect.centery)
                
                # Prüfe ob Icon für dieses Item existiert
                item_key = key.lower()
                if item_key in item_icons:
                    # Icon zeichnen
                    icon = item_icons[item_key]
                    # Skaliere Icon auf Bildschirmgröße (basierend auf Kamera-Zoom)
                    icon_size = max(24, screen_rect.width)
                    scaled_icon = pygame.transform.smoothscale(icon, (icon_size, icon_size))
                    icon_rect = scaled_icon.get_rect(center=center)
                    
                    # Leichter Schatten/Glow unter dem Icon
                    glow_color = (*color[:3], 100) if len(color) >= 3 else (200, 200, 200, 100)
                    glow_surf = pygame.Surface((icon_size + 8, icon_size + 8), pygame.SRCALPHA)
                    pygame.draw.ellipse(glow_surf, glow_color, glow_surf.get_rect())
                    glow_rect = glow_surf.get_rect(center=center)
                    self.screen.blit(glow_surf, glow_rect)
                    
                    # Icon zeichnen
                    self.screen.blit(scaled_icon, icon_rect)
                else:
                    # Fallback: Farbiger Kreis (wie vorher)
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
    
    def _check_enemy_deaths(self):
        """Prüft ob Gegner gestorben sind und spawnt Coin-Drops + XP."""
        import random
        current_enemies = set()
        for enemy in self.enemy_manager.enemies:
            enemy_id = id(enemy)
            current_enemies.add(enemy_id)
            if enemy_id not in self._alive_enemies_set and getattr(enemy, 'alive_status', True):
                # Neuer lebender Gegner → merken
                self._alive_enemies_set.add(enemy_id)
        
        # Finde Gegner die gerade gestorben sind (waren alive, jetzt dead oder entfernt)
        for enemy in self.enemy_manager.enemies:
            enemy_id = id(enemy)
            if enemy_id in self._alive_enemies_set and not getattr(enemy, 'alive_status', True):
                # Gegner ist gerade gestorben → Coins droppen
                coin_amount = random.randint(1, 3)
                drop_pos = pygame.math.Vector2(enemy.rect.centerx, enemy.rect.centery)
                self.dropped_coins.append({
                    'pos': drop_pos,
                    'amount': coin_amount,
                    'spawn_time': pygame.time.get_ticks()
                })
                
                # 🌟 XP vergeben (5-10 pro Gegner)
                if self.game_logic and self.game_logic.player:
                    xp_amount = random.randint(5, 10)
                    leveled_up = self.game_logic.player.gain_xp(xp_amount)
                    if leveled_up:
                        self.show_styled_message(f"LEVEL UP! Level {self.game_logic.player.level}!")
                    if VERBOSE_LOGS:
                        print(f"🌟 +{xp_amount} XP! ({self.game_logic.player.xp}/{self.game_logic.player.xp_to_next})")
                
                # 📊 Score: Kill zählen
                self.score_tracker.add_kill()
                
                # ⚔️ Kill-Counter für Map_Town
                if self.current_map_index == 2:
                    self._town_kill_count += 1
                    if self._town_kill_count == self._town_kills_required:
                        self.show_styled_message(f"⚔️ {self._town_kills_required} Gegner besiegt! Sprich mit Ritter Konrad.")
                        print(f"⚔️ Kill-Ziel erreicht: {self._town_kill_count}/{self._town_kills_required}")
                
                self._alive_enemies_set.discard(enemy_id)
                if VERBOSE_LOGS:
                    print(f"💰 {coin_amount} Münze(n) gedroppt bei ({int(drop_pos.x)}, {int(drop_pos.y)})")
        
        # Entfernte Gegner aus dem Tracking entfernen
        self._alive_enemies_set &= current_enemies

    def _check_coin_pickups(self):
        """Prüft ob der Spieler gedropte Münzen aufsammelt."""
        if not self.dropped_coins or not self.game_logic or not self.game_logic.player:
            return
        
        player_pos = pygame.math.Vector2(self.game_logic.player.rect.center)
        picked_up = 0
        
        remaining = []
        for coin in self.dropped_coins:
            dist = player_pos.distance_to(coin['pos'])
            if dist <= self.coin_pickup_radius:
                # Münzen dem Spieler gutschreiben
                self.game_logic.player.coins += coin['amount']
                picked_up += coin['amount']
            else:
                remaining.append(coin)
        
        if picked_up > 0:
            self.dropped_coins = remaining
            self.collection_message = f"💰 +{picked_up} Münze{'n' if picked_up > 1 else ''} aufgesammelt!"
            self.collection_message_timer = pygame.time.get_ticks() + 2000

    def _start_finale(self):
        """Startet die Finale-Sequenz: Score → Final Picture → Credits → Hauptmenü."""
        print("🏆 Finale-Sequenz gestartet!")
        self.score_tracker.stop()
        self._score_data = self.score_tracker.calculate()
        print(f"📊 Score: {self._score_data.final_score} ({self._score_data.grade}) "
              f"Zeit={ScoreTracker.format_time(self._score_data.total_time)} "
              f"Kills={self._score_data.total_kills} "
              f"Schaden={self._score_data.total_damage_taken}")
        self._finale_active = True
        self._finale_phase = 'score'
        self._finale_alpha = 0
        self._score_display_start = 0
        self._credits_scroll_y = 0
        self._credits_start_time = 0
        
        # Bild laden
        try:
            img_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'assets', 'FinalPicture.jpeg')
            img_path = os.path.normpath(img_path)
            self._finale_picture = pygame.image.load(img_path).convert()
            # Skalieren auf Bildschirmgröße (Aspect Ratio beibehalten)
            sw, sh = self.screen.get_size()
            iw, ih = self._finale_picture.get_size()
            scale = max(sw / iw, sh / ih)
            new_w, new_h = int(iw * scale), int(ih * scale)
            self._finale_picture = pygame.transform.smoothscale(self._finale_picture, (new_w, new_h))
            # Zentrieren
            crop_x = (new_w - sw) // 2
            crop_y = (new_h - sh) // 2
            self._finale_picture = self._finale_picture.subsurface((crop_x, crop_y, sw, sh)).copy()
            print(f"✅ FinalPicture geladen: {img_path}")
        except Exception as e:
            print(f"⚠️ FinalPicture konnte nicht geladen werden: {e}")
            # Fallback: schwarzer Bildschirm
            self._finale_picture = pygame.Surface(self.screen.get_size())
            self._finale_picture.fill((0, 0, 0))
    
    def _handle_finale_event(self, event):
        """Behandelt Input während der Finale-Sequenz."""
        if not self._finale_active:
            return False
        
        # Tastendruck oder Mausklick
        if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
            if self._finale_phase == 'score' and self._finale_alpha >= 255:
                # Score-Screen → Weiter zum Bild
                self._finale_phase = 'picture'
                self._finale_alpha = 0
                print("🖼️ Final Picture gestartet")
                return True
            elif self._finale_phase == 'picture' and self._finale_alpha >= 255:
                # Weiter zu Credits
                self._finale_phase = 'credits'
                self._credits_scroll_y = self.screen.get_height()
                self._credits_start_time = pygame.time.get_ticks()
                print("📜 Credits gestartet")
                return True
            elif self._finale_phase == 'credits':
                # Credits überspringen → zurück zum Menü
                self._finale_active = False
                if hasattr(self, 'main_game') and self.main_game:
                    self.main_game.return_to_menu()
                return True
        return True  # Alle Events konsumieren während Finale
    
    def _update_finale(self, dt):
        """Aktualisiert die Finale-Sequenz."""
        if not self._finale_active:
            return
        
        if self._finale_phase == 'score':
            # Score-Screen Fade-In
            if self._finale_alpha < 255:
                self._finale_alpha = min(255, self._finale_alpha + 5)
            if self._score_display_start == 0:
                self._score_display_start = pygame.time.get_ticks()
        
        elif self._finale_phase == 'picture':
            # Einblendung (Fade-In)
            if self._finale_alpha < 255:
                self._finale_alpha = min(255, self._finale_alpha + 3)
        
        elif self._finale_phase == 'credits':
            # Credits scrollen nach oben
            self._credits_scroll_y -= 1.2  # Scroll-Geschwindigkeit
            
            # Credits-Zeilen berechnen für Auto-Ende
            credit_lines = self._get_credit_lines()
            total_height = len(credit_lines) * 40 + 200
            if self._credits_scroll_y < -total_height:
                # Credits sind fertig → zurück zum Menü
                self._finale_active = False
                if hasattr(self, 'main_game') and self.main_game:
                    self.main_game.return_to_menu()
    
    def _get_credit_lines(self):
        """Gibt die Credits-Zeilen zurück."""
        return [
            ("DAS ALCHEMIST SPIEL", 60, (255, 215, 0)),
            ("", 30, None),
            ("Du hast den Dragon Lord besiegt!", 36, (255, 255, 255)),
            ("Die Welt ist gerettet.", 36, (200, 200, 200)),
            ("", 30, None),
            ("", 30, None),
            ("--- CREDITS ---", 48, (255, 215, 0)),
            ("", 30, None),
            ("Programmierung", 32, (180, 180, 255)),
            ("Kirill", 28, (255, 255, 255)),
            ("", 30, None),
            ("Game Design", 32, (180, 180, 255)),
            ("Jonas", 28, (255, 255, 255)),
            ("", 30, None),
            ("Spiellogik & Testing", 32, (180, 180, 255)),
            ("Christian", 28, (255, 255, 255)),
            ("", 30, None),
            ("Hardware & Gehaeusebau", 32, (180, 180, 255)),
            ("Simon", 28, (255, 255, 255)),
            ("Loeten, Verkabelung, Arduino,", 24, (200, 200, 200)),
            ("Mainboard & Raspberry Pi", 24, (200, 200, 200)),
            ("", 30, None),
            ("Hardware-Assistent", 32, (180, 180, 255)),
            ("Wassem", 28, (255, 255, 255)),
            ("", 30, None),
            ("Grafik & Assets", 32, (180, 180, 255)),
            ("Beckalof Pack / Demon Pack", 28, (255, 255, 255)),
            ("Dragon Lord / Wizard Pack", 28, (255, 255, 255)),
            ("", 30, None),
            ("Musik & Sound", 32, (180, 180, 255)),
            ("Kirill", 28, (255, 255, 255)),
            ("", 30, None),
            ("", 30, None),
            ("Danke fuers Spielen!", 44, (255, 215, 0)),
            ("", 30, None),
            ("", 30, None),
            ("2026", 36, (200, 200, 200)),
        ]
    
    def _render_finale(self):
        """Rendert die Finale-Sequenz (Score, Final Picture oder Credits)."""
        if not self._finale_active:
            return
        
        sw, sh = self.screen.get_size()
        
        if self._finale_phase == 'score':
            self._render_score_screen(sw, sh)
        
        elif self._finale_phase == 'picture':
            # Schwarzer Hintergrund
            self.screen.fill((0, 0, 0))
            
            # Bild mit Fade-In
            if self._finale_picture:
                pic = self._finale_picture.copy()
                pic.set_alpha(self._finale_alpha)
                self.screen.blit(pic, (0, 0))
            
            # "Drücke eine Taste" Hinweis (erst wenn voll eingeblendet)
            if self._finale_alpha >= 255:
                try:
                    import math
                    t = pygame.time.get_ticks() / 1000
                    alpha = int(128 + 127 * math.sin(t * 2))
                    font = pygame.font.Font(None, 28)
                    hint = font.render("Drücke eine Taste...", True, (255, 255, 255))
                    hint.set_alpha(alpha)
                    hint_rect = hint.get_rect(centerx=sw // 2, bottom=sh - 30)
                    self.screen.blit(hint, hint_rect)
                except Exception:
                    pass
        
        elif self._finale_phase == 'credits':
            # Schwarzer Hintergrund
            self.screen.fill((0, 0, 0))
            
            # Credits scrollen
            y = self._credits_scroll_y
            credit_lines = self._get_credit_lines()
            
            for text, size, color in credit_lines:
                if color is None or text == "":
                    y += 30
                    continue
                try:
                    font = pygame.font.Font(None, size)
                    surf = font.render(text, True, color)
                    rect = surf.get_rect(centerx=sw // 2, top=y)
                    # Nur zeichnen wenn im sichtbaren Bereich
                    if -50 < rect.bottom and rect.top < sh + 50:
                        self.screen.blit(surf, rect)
                    y += size + 12
                except Exception:
                    y += size + 12
            
            # Hinweis unten
            try:
                font_sm = pygame.font.Font(None, 22)
                skip = font_sm.render("Drücke eine Taste zum Überspringen", True, (120, 120, 120))
                self.screen.blit(skip, skip.get_rect(centerx=sw // 2, bottom=sh - 10))
            except Exception:
                pass

    def _render_score_screen(self, sw: int, sh: int):
        """Rendert den Score-Screen mit Statistiken und Rang."""
        import math as _math
        
        self.screen.fill((5, 8, 20))
        
        sd = self._score_data
        if not sd:
            return
        
        alpha = min(self._finale_alpha, 255)
        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        
        # ---- Titel ----
        title_font = pygame.font.Font(None, 64)
        title = title_font.render("ERGEBNIS", True, (255, 215, 0))
        overlay.blit(title, title.get_rect(centerx=sw // 2, top=60))
        
        # ---- Trennlinie ----
        pygame.draw.line(overlay, (255, 215, 0, 150),
                         (sw // 2 - 200, 130), (sw // 2 + 200, 130), 2)
        
        # ---- Statistik-Zeilen ----
        stat_font = pygame.font.Font(None, 36)
        label_font = pygame.font.Font(None, 30)
        
        stats = [
            ("⏱  Zeit", ScoreTracker.format_time(sd.total_time), sd.time_score, (180, 220, 255)),
            ("⚔  Besiegte Gegner", str(sd.total_kills), sd.kill_score, (255, 180, 80)),
            ("🛡  Erhaltener Schaden", str(sd.total_damage_taken), sd.damage_score, (255, 100, 100)),
        ]
        
        y = 170
        bar_w = 300
        bar_h = 18
        bar_x = sw // 2 - bar_w // 2
        
        for label, value, sub_score, color in stats:
            # Label + Wert
            lbl = stat_font.render(label, True, (220, 220, 230))
            val = stat_font.render(value, True, color)
            overlay.blit(lbl, (sw // 2 - 250, y))
            overlay.blit(val, (sw // 2 + 180, y))
            y += 40
            
            # Fortschrittsbalken
            ratio = sub_score / 10000.0
            # Hintergrund
            pygame.draw.rect(overlay, (30, 35, 50, 200), (bar_x, y, bar_w, bar_h), 0, 6)
            # Füllung (Farbe je nach Score)
            if sub_score >= 8000:
                fill_col = (80, 220, 80)
            elif sub_score >= 5000:
                fill_col = (220, 200, 60)
            elif sub_score >= 3000:
                fill_col = (220, 140, 40)
            else:
                fill_col = (200, 60, 60)
            fill_w = int(bar_w * ratio)
            if fill_w > 0:
                pygame.draw.rect(overlay, fill_col, (bar_x, y, fill_w, bar_h), 0, 6)
            pygame.draw.rect(overlay, (80, 90, 110), (bar_x, y, bar_w, bar_h), 1, 6)
            
            # Punkte rechts neben Balken
            pts = label_font.render(f"{sub_score}", True, (160, 160, 180))
            overlay.blit(pts, (bar_x + bar_w + 12, y - 2))
            y += bar_h + 25
        
        # ---- Trennlinie vor Gesamtscore ----
        pygame.draw.line(overlay, (100, 110, 140, 150),
                         (sw // 2 - 200, y), (sw // 2 + 200, y), 1)
        y += 20
        
        # ---- Gesamtscore ----
        score_font = pygame.font.Font(None, 48)
        score_text = score_font.render(f"Gesamtscore:  {sd.final_score}", True, (255, 255, 255))
        overlay.blit(score_text, score_text.get_rect(centerx=sw // 2, top=y))
        y += 60
        
        # ---- Rang (groß, mit Glow) ----
        grade_colors = {
            'S': (255, 215, 0),    # Gold
            'A': (100, 255, 100),  # Grün
            'B': (100, 180, 255),  # Blau
            'C': (220, 200, 60),   # Gelb
            'D': (200, 100, 100),  # Rot
        }
        grade_names = {
            'S': 'Meister', 'A': 'Exzellent', 'B': 'Gut',
            'C': 'Durchschnitt', 'D': 'Anfänger',
        }
        gc = grade_colors.get(sd.grade, (255, 255, 255))
        
        # Glow-Effekt
        t = pygame.time.get_ticks() / 1000
        glow = int(30 + 20 * _math.sin(t * 3))
        glow_surf = pygame.Surface((200, 120), pygame.SRCALPHA)
        pygame.draw.ellipse(glow_surf, (gc[0], gc[1], gc[2], glow), (0, 0, 200, 120))
        overlay.blit(glow_surf, glow_surf.get_rect(centerx=sw // 2, centery=y + 40))
        
        grade_font = pygame.font.Font(None, 100)
        grade_surf = grade_font.render(sd.grade, True, gc)
        overlay.blit(grade_surf, grade_surf.get_rect(centerx=sw // 2, top=y))
        y += 100
        
        # Rang-Name
        name_font = pygame.font.Font(None, 32)
        name_surf = name_font.render(f"Rang: {grade_names.get(sd.grade, '')}", True, gc)
        overlay.blit(name_surf, name_surf.get_rect(centerx=sw // 2, top=y))
        
        # ---- Hinweis ----
        if self._finale_alpha >= 255:
            pulse = int(128 + 127 * _math.sin(t * 2))
            hint_font = pygame.font.Font(None, 26)
            hint = hint_font.render("Drücke eine Taste...", True, (255, 255, 255))
            hint.set_alpha(pulse)
            overlay.blit(hint, hint.get_rect(centerx=sw // 2, bottom=sh - 30))
        
        # Overlay mit Fade anwenden
        overlay.set_alpha(alpha)
        self.screen.blit(overlay, (0, 0))

    def _draw_dropped_coins(self):
        """Zeichnet gedropte Münzen in die Welt mit Animation."""
        if not self.dropped_coins:
            return
        
        import math
        now = pygame.time.get_ticks()
        
        for coin in self.dropped_coins:
            world_pos = coin['pos']
            amount = coin['amount']
            age = now - coin['spawn_time']
            
            # Leichtes Auf-und-Ab-Schweben
            bob = int(3 * math.sin(now / 300 + world_pos.x * 0.1))
            
            # Einblend-Animation (erste 300ms)
            if age < 300:
                scale = age / 300
            else:
                scale = 1.0
            
            # Münz-Größe (mehr Münzen = etwas größer)
            base_size = 10 + amount * 2
            size = int(base_size * scale)
            if size < 2:
                continue
            
            rect = pygame.Rect(int(world_pos.x - size), int(world_pos.y - size + bob), size * 2, size * 2)
            screen_rect = self.camera.apply_rect(rect)
            cx, cy = screen_rect.centerx, screen_rect.centery
            r = max(4, screen_rect.width // 2)
            
            # Goldener Glow
            glow_surf = pygame.Surface((r * 4, r * 4), pygame.SRCALPHA)
            glow_alpha = int(60 + 30 * math.sin(now / 250 + world_pos.y * 0.1))
            pygame.draw.circle(glow_surf, (255, 200, 50, glow_alpha), (r * 2, r * 2), r * 2)
            self.screen.blit(glow_surf, (cx - r * 2, cy - r * 2))
            
            # Münze (goldener Kreis)
            pygame.draw.circle(self.screen, (218, 165, 32), (cx, cy), r)  # Dunkles Gold
            pygame.draw.circle(self.screen, (255, 215, 0), (cx, cy), r - 2)  # Helles Gold
            pygame.draw.circle(self.screen, (255, 235, 100), (cx, cy), max(1, r // 3))  # Highlight
            pygame.draw.circle(self.screen, (180, 130, 20), (cx, cy), r, 1)  # Rand
            
            # Anzahl anzeigen wenn > 1
            if amount > 1:
                try:
                    font = getattr(self, 'item_name_font', None) or pygame.font.Font(None, 20)
                    num_surf = font.render(str(amount), True, (255, 255, 220))
                    num_rect = num_surf.get_rect(center=(cx, cy - r - 8))
                    self.screen.blit(num_surf, num_rect)
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

        # Prüfe ob die finale Quest abgeschlossen wurde
        is_final_completion = False
        if self.current_map_index == 3:  # Map3Castle.tmx (letzte Map)
            is_final_completion = True

        # Zeige entsprechende Level-Abschluss Nachricht an
        if is_final_completion:
            self.show_styled_message("Herzlichen Glückwunsch! Du hast das Spiel erfolgreich abgeschlossen!")
            # Countdown starten
            self.countdown_timer = 5
            self.countdown_active = True
            # Timer für Countdown-Updates starten (jede Sekunde)
            pygame.time.set_timer(pygame.USEREVENT + 2, 1000)
        else:
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
            
            # Bei Map-Wechsel Spielzustand zurücksetzen
            if "Map_Village.tmx" in map_name or "Map_Town.tmx" in map_name or "Map3Castle.tmx" in map_name:
                level_num = 4 if "Map3Castle" in map_name else (3 if "Map_Town" in map_name else 2)
                print(f"🔄 Wechsel zu Level {level_num} - Setze Spielzustand zurück...")
                
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
                
                # Coin-Drops zurücksetzen
                self.dropped_coins = []
                self._alive_enemy_ids = set()
                
                # Konfiguriere Sammelobjekte für diese Map
                self._configure_collectibles_for_map(map_name)
                
                # Spieler-Position für neue Map setzen (nutzt die neue Spawn-Erkennung!)
                self.spawn_entities_from_map()
                
                # Alte Gegner entfernen
                self.clear_enemies()
                
                # Enemies für neue Map laden
                self.respawn_enemies_only()
                
                # 🧙 The Great Beckalof spawnen
                self._spawn_beckalof(map_name)
                
                # 🐉 Dragon Lord Boss spawnen (nur auf Map3Castle)
                player_x = self.game_logic.player.rect.centerx
                player_y = self.game_logic.player.rect.centery
                self._spawn_dragon_lord(player_x, player_y)
                
                # 🎰 Gambler NPC spawnen
                self._spawn_gambler(player_x, player_y)
                
                # 🏪 Shopkeeper NPC spawnen (nur auf Map3 und Map_Town)
                self._spawn_shopkeeper(map_name, player_x, player_y)
                
                # ⚔️ Soldat NPC spawnen (nur auf Map_Town)
                self._spawn_soldier(map_name, player_x, player_y)
                
                # ⚔️ Ritter-Begleiter spawnen (wenn angeheuert)
                self._spawn_knight_companion(player_x, player_y)
                
                # Kollisionsobjekte neu aufbauen
                self.setup_collision_objects()
                
                # Health-Bars neu einrichten
                self.setup_health_bars()
                
                # Kameragrenzen aktualisieren
                self.camera.set_map_bounds(self.map_loader.width, self.map_loader.height)
                
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
                self._spawn_beckalof("Map3.tmx")  # Fallback spawn

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
        
        # Map_Town Abschluss-Bedingungen (Level 3)
        # → Progression wird über Soldat NPC gesteuert (min. 10 Kills + Dialog)
        elif current_map == "Map_Town.tmx":
            pass  # Kein Auto-Complete – Spieler muss mit Ritter Konrad sprechen
        
        # Map3Castle Abschluss-Bedingungen (Level 4 - Final)
        elif current_map == "Map3Castle.tmx":
            # 1. Alle regulären Enemies besiegt
            enemies_defeated = len(self.enemy_manager.enemies) == 0
            
            # 2. Dragon Lord Boss besiegt
            dragon_lord_defeated = (
                self.dragon_lord is not None and not self.dragon_lord.is_alive()
            )
            
            # Wenn Dragon Lord besiegt: Bonus-XP + Finale-Sequenz starten
            if dragon_lord_defeated and not self._finale_active:
                # 🌟 Boss-XP (50 XP für Dragon Lord)
                if self.game_logic and self.game_logic.player:
                    self.game_logic.player.gain_xp(50)
                    print("🌟 +50 XP für Dragon Lord Kill!")
                print("🏆 Dragon Lord besiegt! Starte Finale...")
                self._start_finale()

    def render(self):
        """Hauptrender-Methode für das Level"""
        # 🏆 Finale-Sequenz überlagert alles
        if self._finale_active:
            self._render_finale()
            return
        
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

        # 🧙 The Great Beckalof NPC rendern (vor Collectibles für richtige Tiefe)
        if self.beckalof_npc:
            try:
                self.beckalof_npc.render(self.screen, self.camera)
            except Exception as e:
                print(f"⚠️ Beckalof Render-Fehler: {e}")

        # 🐉 Dragon Lord Boss rendern
        if self.dragon_lord and not self.dragon_lord.death_animation_complete:
            try:
                self.dragon_lord.render(self.screen, self.camera)
            except Exception as e:
                print(f"⚠️ Dragon Lord Render-Fehler: {e}")

        # 🎰 Gambler NPC rendern
        if self.gambler_npc:
            try:
                self.gambler_npc.draw(self.screen, self.camera)
                self.gambler_npc.draw_interaction_prompt(self.screen, self.camera)
            except Exception as e:
                print(f"⚠️ Gambler Render-Fehler: {e}")

        # 🏪 Shopkeeper NPC rendern
        if self.shopkeeper_npc:
            try:
                self.shopkeeper_npc.draw(self.screen, self.camera)
                self.shopkeeper_npc.draw_interaction_prompt(self.screen, self.camera)
            except Exception as e:
                print(f"⚠️ Shopkeeper Render-Fehler: {e}")

        # ⚔️ Soldat NPC rendern
        if self.soldier_npc:
            try:
                self.soldier_npc.draw(self.screen, self.camera)
                self.soldier_npc.draw_interaction_prompt(self.screen, self.camera)
            except Exception as e:
                print(f"⚠️ Soldat Render-Fehler: {e}")

        # ⚔️ Ritter-Begleiter rendern
        if self.knight_companion and self.knight_companion.is_alive():
            try:
                self.knight_companion.draw(self.screen, self.camera)
            except Exception as e:
                print(f"⚠️ KnightCompanion Render-Fehler: {e}")

        # Sammelobjekte über der Map aber unter UI rendern
        self._draw_collectibles()

        # 💰 Gedropte Münzen rendern
        self._draw_dropped_coins()

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

        # 💬 Interaktions-Hinweis über dem NPC anzeigen (wenn NPC in Reichweite)
        npc_in_range = (self.beckalof_npc and self.beckalof_npc.can_interact) or self.active_npc_zone
        if npc_in_range and not (self.dialogue_box and self.dialogue_box.is_active):
            try:
                # NPC-Weltposition ermitteln
                npc_world_pos = None
                
                if self.active_npc_zone and self.active_npc_zone in self.interaction_zones:
                    zone = self.interaction_zones[self.active_npc_zone]
                    npc_world_pos = zone['pos']
                elif self.beckalof_npc and self.beckalof_npc.can_interact:
                    npc_world_pos = pygame.math.Vector2(
                        self.beckalof_npc.rect.centerx,
                        self.beckalof_npc.rect.top
                    )
                
                if npc_world_pos:
                    # NPC-Position auf dem Bildschirm (Welt → Screen)
                    cam = self.camera.camera_rect
                    screen_x = int((npc_world_pos.x - cam.x) * self.camera.zoom_factor)
                    screen_y = int((npc_world_pos.y - cam.y) * self.camera.zoom_factor)
                    
                    # Hint-Text
                    hint_text = "[ C ] Sprechen"
                    hint_surf = self.npc_interaction_font.render(hint_text, True, (255, 255, 200))
                    
                    # Pulsierende Animation
                    anim_time = pygame.time.get_ticks()
                    bob_offset = int(3 * math.sin(anim_time / 400))
                    
                    # Hintergrund
                    padding = 8
                    bg_width = hint_surf.get_width() + padding * 2
                    bg_height = hint_surf.get_height() + padding * 2
                    bg_x = int(screen_x - bg_width // 2)
                    bg_y = int(screen_y - 50 + bob_offset)
                    
                    # Halbtransparenter Hintergrund mit Gradient
                    bg_surf = pygame.Surface((bg_width, bg_height), pygame.SRCALPHA)
                    for row in range(bg_height):
                        alpha = int(200 - row * 0.5)
                        pygame.draw.line(bg_surf, (15, 20, 45, alpha), (0, row), (bg_width, row))
                    self.screen.blit(bg_surf, (bg_x, bg_y))
                    
                    # Rahmen
                    pygame.draw.rect(self.screen, (80, 120, 180), (bg_x, bg_y, bg_width, bg_height), 2)
                    pygame.draw.rect(self.screen, (120, 160, 255), (bg_x + 2, bg_y + 2, bg_width - 4, bg_height - 4), 1)
                    
                    # Kleines Dreieck nach unten (Sprechblase)
                    tri_x = bg_x + bg_width // 2
                    tri_y = bg_y + bg_height
                    pygame.draw.polygon(self.screen, (15, 20, 45), [
                        (tri_x - 6, tri_y),
                        (tri_x + 6, tri_y),
                        (tri_x, tri_y + 8)
                    ])
                    pygame.draw.line(self.screen, (80, 120, 180), (tri_x - 6, tri_y), (tri_x, tri_y + 8), 1)
                    pygame.draw.line(self.screen, (80, 120, 180), (tri_x + 6, tri_y), (tri_x, tri_y + 8), 1)
                    
                    # Text
                    text_x = bg_x + padding
                    text_y = bg_y + padding
                    self.screen.blit(hint_surf, (text_x, text_y))
            except Exception as e:
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

        # Interaktionstext anzeigen (nur wenn kein Dialog geöffnet ist)
        if (not (self.dialogue_box and self.dialogue_box.is_active)) and self.show_interaction_text and self.interaction_text:
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

        # Modal Dialogue rendern (oberhalb der UI)
        if self.dialogue_box:
            self.dialogue_box.render()

        # 🎰 Blackjack-Spiel rendern (ganz oben)
        if self.blackjack_game and self.blackjack_game.is_active:
            self.blackjack_game.render(self.screen)

        # 🏪 Shop-UI rendern (ganz oben)
        if self.shop_ui and self.shop_ui.is_active:
            self.shop_ui.render(self.screen)

        # Einfache Meldungsanzeige beim Einsammeln
        if self.collection_message and pygame.time.get_ticks() < self.collection_message_timer:
            try:
                # 🚀 RPi-Optimierung: Nutze gecachte Font statt per-Frame Erstellung
                text = self.collection_message_font.render(self.collection_message, True, (255, 255, 255))
                bg = text.get_rect()
                bg.centerx = self.screen.get_width() // 2
                bg.y = 80
                pygame.draw.rect(self.screen, (0, 0, 0), bg.inflate(16, 10))
                pygame.draw.rect(self.screen, (180, 180, 220), bg.inflate(16, 10), 2)
                self.screen.blit(text, (bg.x, bg.y))
            except Exception:
                pass

        # 📜 Missions-Anzeige oben rechts rendern
        try:
            # Kill-Counter an Mission-Display übergeben (erst nach Gespräch mit Ritter)
            if self.current_map_index == 2 and self._soldier_talked:
                self.mission_display.set_kill_counter(self._town_kill_count, self._town_kills_required)
            else:
                self.mission_display.clear_kill_counter()
            self.mission_display.update(self.quest_manager)
            self.mission_display.render(self.screen, self.quest_manager)
        except Exception as e:
            if VERBOSE_LOGS:
                print(f"⚠️ Mission-Display Fehler: {e}")

        # Countdown-Timer anzeigen wenn aktiv
        if self.countdown_active and self.countdown_timer > 0:
            try:
                countdown_text = f"Rückkehr zum Hauptmenü in {self.countdown_timer}..."
                text_surface = self.interaction_font.render(countdown_text, True, (255, 255, 0))  # Gelbe Farbe
                text_rect = text_surface.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() // 2 + 50))
                
                # Hintergrund für bessere Lesbarkeit
                bg_rect = text_rect.inflate(20, 10)
                bg_surface = pygame.Surface((bg_rect.width, bg_rect.height))
                bg_surface.set_alpha(200)
                bg_surface.fill((0, 0, 50))  # Dunkelblauer Hintergrund
                
                self.screen.blit(bg_surface, bg_rect)
                self.screen.blit(text_surface, text_rect)
            except Exception as e:
                print(f"⚠️ Fehler beim Rendern des Countdown-Timers: {e}")

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
                    # Collect current enemies for projectile/area-hit processing
                    try:
                        enemies_list = self.enemy_manager.enemies.sprites() if hasattr(self.enemy_manager, 'enemies') else []
                        # 🐉 Dragon Lord zur Enemy-Liste hinzufügen
                        if self.dragon_lord and self.dragon_lord.is_alive():
                            enemies_list = list(enemies_list) + [self.dragon_lord]
                    except Exception:
                        enemies_list = None
                    # Prefer ElementMixer as the single source of truth and enforce cooldown
                    if self.main_game and hasattr(self.main_game, 'element_mixer') and self.main_game.element_mixer:
                        mixer = self.main_game.element_mixer
                        cooldown_mgr = getattr(self.main_game, 'spell_cooldown_manager', None)

                        # Require a ready combination
                        spell_id = None
                        try:
                            spell_id = mixer.get_current_spell_id()
                        except Exception:
                            spell_id = None

                        if not spell_id:
                            if VERBOSE_LOGS:
                                print("🚫 No spell combination ready")
                            return

                        # Enforce cooldown strictly
                        if cooldown_mgr is not None and not cooldown_mgr.is_ready(spell_id):
                            try:
                                remaining = cooldown_mgr.time_remaining(spell_id)
                            except Exception:
                                remaining = 0.0
                            print(f"🚫 Spell {spell_id} on cooldown: {remaining:.1f}s remaining")
                            return

                        # Map mixer elements into core magic system selection
                        try:
                            elements = mixer.get_current_spell_elements()
                        except Exception:
                            elements = None
                        if not elements:
                            print("🚫 No elements available for casting")
                            return

                        print(f"🧪 Casting via ElementMixer elements: {elements}")
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

                        # Start cooldown via mixer; only proceed if mixer confirms cast
                        cast_info = mixer.handle_cast_spell()
                        if not cast_info:
                            # Mixer rejected (e.g., race condition or cooldown) -> do not cast
                            return

                        try:
                            dbg_elems = [e.value for e in player.magic_system.selected_elements]
                            if VERBOSE_LOGS:
                                print(f"✨ Casting with core elements: {dbg_elems}")
                        except Exception:
                            pass

                        player.magic_system.cast_magic(caster=player, enemies=enemies_list)
                        return

                    # Fallback path (no ElementMixer available): cast with currently selected elements (no UI cooldown)
                    try:
                        dbg_elems = [e.value for e in player.magic_system.selected_elements]
                        if VERBOSE_LOGS:
                            print(f"✨ Casting with core elements (fallback): {dbg_elems}")
                    except Exception:
                        pass
                    player.magic_system.cast_magic(caster=player, enemies=enemies_list)
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
