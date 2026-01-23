# -*- coding: utf-8 -*-
"""
Element Mixer UI Component
Shows the 3 elements (Fire, Water, Stone) and current combination with cooldowns
"""

import pygame
import math
from typing import Optional, List, Tuple, Dict, Any
from pathlib import Path

# Import configuration
try:
    from core.config import config
except ImportError:
    try:
        from ..core.config import config
    except ImportError:
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(__file__)))
        from core.config import config

# Verbose logging toggle
try:
    from core.settings import VERBOSE_LOGS
except Exception:
    VERBOSE_LOGS = False  # type: ignore

# Easter Egg System
try:
    from ui.gif_overlay import EasterEggSequence
except ImportError:
    try:
        from .gif_overlay import EasterEggSequence
    except ImportError:
        EasterEggSequence = None  # type: ignore


class ElementMixer:
    """
    UI component that displays the element mixing system
    Shows 3 elements + current combination + cooldown tracking
    """
    
    def __init__(self, spell_cooldown_manager):
        """
        Initialize the element mixer UI
        
        Args:
            spell_cooldown_manager: Instance of SpellCooldownManager for cooldown tracking
        """
        self.cooldown_manager = spell_cooldown_manager
        
        # Element configuration - CORRECT MAPPING: 1=Water, 2=Fire, 3=Stone
        self.elements = [
            {"id": "water", "name": "Wasser", "color": (80, 150, 255), "key": "1"},
            {"id": "fire", "name": "Feuer", "color": (255, 80, 80), "key": "2"},
            {"id": "stone", "name": "Stein", "color": (150, 150, 100), "key": "3"}
        ]
        
        # Current element selection
        self.selected_elements = []  # List of selected element IDs
        self.current_combination = None  # Current spell combination
        
        # Debounce protection against double event handling
        self.last_element_press = {"element": None, "time": 0}
        self.debounce_time = 0.1  # 100ms debounce
        
        # 🥚 Easter Egg Sequenz-Erkennung
        self.easter_egg_detector = EasterEggSequence() if EasterEggSequence else None
        self.pending_easter_egg: str = None  # Ausgelöstes Easter Egg
                # UI Configuration
        self.element_size = 48  # 48x48 pixel elements
        self.element_spacing = 8
        self.combination_size = 64  # Larger size for the result spell
        self.background_padding = 10
        self.background_alpha = 180
        
        # Fonts (initialize first before creating icons)
        pygame.font.init()
        self.font = pygame.font.Font(None, 20)
        self.small_font = pygame.font.Font(None, 16)
        self.label_font = pygame.font.Font(None, 22)
        
        # Load element + combo icons
        try:
            from .spell_icons import SpellIcons
        except ImportError:
            from ui.spell_icons import SpellIcons  # fallback when run from different cwd
        self.icons = SpellIcons(base_size=self.combination_size)
        self.element_icons: Dict[str, pygame.Surface] = {}
        self.combination_icons: Dict[str, pygame.Surface] = {}
        self.load_icons()

        # Create cooldown overlays
        self.cooldown_overlays: List[pygame.Surface] = self.create_cooldown_overlays()

        # UI surfaces
        self.background_surface: Optional[pygame.Surface] = None
        self.create_background_surface()

        # Cached element name lookup for display
        self.element_name_map = {e["id"]: e["name"] for e in self.elements}
        # Bottom label styling
        self.label_margin_top = 6
        self.label_padding = 6
        self.label_bg_alpha = 160

        # Performance caches (RPi/7-inch): avoid per-frame font/surface work
        self._chip_font: Optional[pygame.font.Font] = None
        self._chip_surfaces: Dict[Tuple[str, int], pygame.Surface] = {}
        self._key_label_cache: Dict[Tuple[str, int, Tuple[int, int, int]], pygame.Surface] = {}
        self._flash_surface_cache: Dict[Tuple[int, int, int], pygame.Surface] = {}
        self._combo_dimmed_cache: Dict[str, pygame.Surface] = {}
        self._combo_key_c_cache: Optional[Tuple[pygame.Surface, pygame.Surface]] = None
        self._combo_qmark_cache: Dict[Tuple[int, int], pygame.Surface] = {}
        self._countdown_cache: Dict[Tuple[int, int], Tuple[pygame.Surface, pygame.Surface]] = {}
        
        # Animation states
        self.element_animations = [0.0] * 3  # For element press feedback
        self.combination_animation = 0.0     # For combination ready/cast animation
        
        if VERBOSE_LOGS:
            print("✨ ElementMixer initialized with 3 elements")

    def _get_chip_surface(self, txt: str, size: int) -> pygame.Surface:
        """Return cached '+'/'=' chip surface with proper vertical centering."""
        key = (txt, size)
        cached = self._chip_surfaces.get(key)
        if cached is not None:
            return cached
        if self._chip_font is None:
            self._chip_font = pygame.font.Font(None, max(24, size // 2))
        # Groessere Surface fuer bessere Zentrierung
        chip_size = size
        surf = pygame.Surface((chip_size // 2, chip_size), pygame.SRCALPHA)
        t = self._chip_font.render(txt, True, (180, 200, 230))
        # Zentriere horizontal und vertikal
        tx = (surf.get_width() - t.get_width()) // 2
        ty = (surf.get_height() - t.get_height()) // 2
        surf.blit(t, (tx, ty))
        self._chip_surfaces[key] = surf
        return surf

    def _get_key_label(self, txt: str, font: pygame.font.Font, color: Tuple[int, int, int]) -> pygame.Surface:
        """Cache label surfaces (e.g., '1','2','3','C') to avoid per-frame font.render."""
        key = (txt, id(font), color)
        cached = self._key_label_cache.get(key)
        if cached is not None:
            return cached
        surf = font.render(txt, True, color)
        self._key_label_cache[key] = surf
        return surf

    def _get_flash_surface(self, size: int, alpha: int) -> pygame.Surface:
        """Cache flash overlay surfaces by size + alpha bucket."""
        a = max(0, min(255, int(alpha)))
        bucket = int(a / 10) * 10
        key = (size, size, bucket)
        cached = self._flash_surface_cache.get(key)
        if cached is not None:
            return cached
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        surf.fill((255, 255, 255, bucket))
        self._flash_surface_cache[key] = surf
        return surf

    def _get_dimmed_combo_icon(self, spell_id: str) -> Optional[pygame.Surface]:
        """Cache dimmed combo icon for cooldown state."""
        if spell_id in self._combo_dimmed_cache:
            return self._combo_dimmed_cache[spell_id]
        icon = self.combination_icons.get(spell_id)
        if not icon:
            return None
        dimmed = icon.copy()
        dimmed_overlay = pygame.Surface((self.combination_size, self.combination_size), pygame.SRCALPHA)
        dimmed_overlay.fill((0, 0, 0, 100))
        dimmed.blit(dimmed_overlay, (0, 0))
        self._combo_dimmed_cache[spell_id] = dimmed
        return dimmed

    def _get_countdown_surfaces(self, number: int) -> Tuple[pygame.Surface, pygame.Surface]:
        """Cache countdown text surface + shadow."""
        key = (number, self.combination_size)
        cached = self._countdown_cache.get(key)
        if cached is not None:
            return cached
        txt = str(max(1, int(number)))
        main = self.font.render(txt, True, (255, 255, 255))
        shadow = self.font.render(txt, True, (0, 0, 0))
        self._countdown_cache[key] = (main, shadow)
        return main, shadow
    
    def load_icons(self):
        """Load element icons and combination spell icons"""
        # Element icons from assets/ui/spells/elements
        for element in self.elements:
            elem_id = element["id"]
            size = self.element_size
            self.element_icons[elem_id] = self.icons.get_element(elem_id, size)

        # Combination icons from assets/ui/spells/combos
        for combination_key, spell_data in config.spells.MAGIC_COMBINATIONS.items():
            a, b = combination_key
            self.combination_icons[spell_data["id"]] = self.icons.get_combo(a, b, self.combination_size)
    
    def create_element_icon(self, element: Dict) -> pygame.Surface:
        """Deprecated: kept for compatibility, now uses SpellIcons"""
        return self.icons.get_element(element["id"], self.element_size)
    
    def create_combination_placeholder(self, spell_data: Dict) -> pygame.Surface:
        return self.icons.get_combo("?", "?", self.combination_size)
    
    def create_cooldown_overlays(self) -> List[pygame.Surface]:
        """Create cooldown overlay surfaces for smooth animation"""
        overlays = []
        steps = 60
        
        for step in range(steps + 1):
            progress = step / steps
            overlay = self.create_cooldown_overlay(progress, self.combination_size)
            overlays.append(overlay)
        
        try:
            from core.settings import VERBOSE_LOGS  # type: ignore
        except Exception:
            VERBOSE_LOGS = False  # type: ignore
        if VERBOSE_LOGS:  # type: ignore[name-defined]
            print("Created {} cooldown overlays for combinations".format(len(overlays)))
        return overlays
    
    def create_cooldown_overlay(self, progress: float, size: int) -> pygame.Surface:
        """Create a radial cooldown overlay surface"""
        surface = pygame.Surface((size, size), pygame.SRCALPHA)
        
        if progress >= 1.0:
            return surface
        
        center = (size // 2, size // 2)
        radius = size // 2
        overlay_color = (0, 0, 0, 128)
        remaining_angle = 2 * math.pi * (1.0 - progress)
        
        if remaining_angle > 0:
            points = [center]
            num_points = max(8, int(remaining_angle * 8))
            for i in range(num_points + 1):
                angle = -math.pi / 2 + (i / num_points) * remaining_angle
                x = center[0] + int(radius * math.cos(angle))
                y = center[1] + int(radius * math.sin(angle))
                points.append((x, y))
            
            if len(points) > 2:
                pygame.draw.polygon(surface, overlay_color, points)
        
        return surface
    
    def create_background_surface(self):
        """Create the background surface for the element mixer with modern pixel-art style"""
        # Calculate total width: 3 elements + spacing + combination slot + padding
        elements_width = 3 * self.element_size + 2 * self.element_spacing
        total_width = elements_width + self.element_spacing * 2 + self.combination_size + 2 * self.background_padding
        total_height = max(self.element_size, self.combination_size) + 2 * self.background_padding

        self.background_surface = pygame.Surface((total_width, total_height), pygame.SRCALPHA)
        
        # Moderner Gradient-Hintergrund (dunkel nach noch dunkler)
        for row in range(total_height):
            ratio = row / total_height
            r = int(20 * (1 - ratio) + 10 * ratio)
            g = int(25 * (1 - ratio) + 15 * ratio)
            b = int(45 * (1 - ratio) + 30 * ratio)
            pygame.draw.line(self.background_surface, (r, g, b, self.background_alpha), 
                           (0, row), (total_width, row))
        
        # Mehrstufiger Rahmen (Pixel-Art Style)
        # Aeusserer dunkler Rahmen
        pygame.draw.rect(self.background_surface, (30, 35, 55, 255), 
                        (0, 0, total_width, total_height), 3)
        # Mittlerer Rahmen
        pygame.draw.rect(self.background_surface, (50, 60, 90, 255), 
                        (2, 2, total_width - 4, total_height - 4), 2)
        # Innerer leuchtender Rahmen
        pygame.draw.rect(self.background_surface, (70, 90, 140, 255), 
                        (4, 4, total_width - 8, total_height - 8), 1)
        
        # Dekorative Ecken (Gold-Akzent)
        corner_size = 5
        corner_color = (140, 110, 60, 255)
        corners = [(0, 0), (total_width - corner_size, 0), 
                   (0, total_height - corner_size), (total_width - corner_size, total_height - corner_size)]
        for cx, cy in corners:
            pygame.draw.rect(self.background_surface, corner_color, (cx, cy, corner_size, corner_size))
            pygame.draw.rect(self.background_surface, (180, 150, 90, 255), (cx + 1, cy + 1, 3, 3))
        
        # Obere Highlight-Linie
        pygame.draw.line(self.background_surface, (80, 100, 150, 100),
                        (corner_size + 2, 1), (total_width - corner_size - 2, 1))
    
    def handle_element_press(self, element_id: str) -> bool:
        """
        Handle element button press - adds element to combination
        
        Args:
            element_id: ID of the element pressed ('fire', 'water', 'stone')
            
        Returns:
            True if element was added successfully
        """
        # Get current time for debounce check
        current_time = pygame.time.get_ticks() / 1000.0  # Convert to seconds
        
        # Check for debounce: same element pressed within debounce_time
        if (self.last_element_press["element"] == element_id and 
            current_time - self.last_element_press["time"] < self.debounce_time):
            if VERBOSE_LOGS:
                print(f"🚫 DEBOUNCE: Ignoring duplicate press of '{element_id}' within {self.debounce_time}s")
            return False
        
        # Update debounce tracking
        self.last_element_press = {"element": element_id, "time": current_time}
        
        if VERBOSE_LOGS:
            print(f"🔍 DEBUG: handle_element_press called with '{element_id}'")
            print(f"🔍 DEBUG: Current selected_elements: {self.selected_elements}")
            print(f"🔍 DEBUG: Length before: {len(self.selected_elements)}")
        
        # Find element index for animation
        element_index = -1
        for i, element in enumerate(self.elements):
            if element["id"] == element_id:
                element_index = i
                break
        
        if element_index >= 0:
            # 🥚 Easter Egg Sequenz prüfen
            if self.easter_egg_detector:
                easter_egg = self.easter_egg_detector.add_input(element_id)
                if easter_egg:
                    self.pending_easter_egg = easter_egg
                    # Reset selection damit kein Zauber ausgelöst wird
                    self.reset_combination()
                    return True
            
            # If we already have 2 elements, reset first
            if len(self.selected_elements) >= 2:
                if VERBOSE_LOGS:
                    print("🔍 DEBUG: Resetting because we already have 2 elements")
                self.reset_combination()
                if VERBOSE_LOGS:
                    print(f"� DEBUG: After reset, selected_elements: {self.selected_elements}")
            
            # Add element to selection (max 2)
            if len(self.selected_elements) < 2:
                if VERBOSE_LOGS:
                    print(f"🔍 DEBUG: Adding element '{element_id}' to selection")
                self.selected_elements.append(element_id)
                if VERBOSE_LOGS:
                    print(f"🔍 DEBUG: After adding, selected_elements: {self.selected_elements}")
                self.element_animations[element_index] = 1.0
                
                # Check if we have a valid combination (only when we have exactly 2)
                if len(self.selected_elements) == 2:
                    if VERBOSE_LOGS:
                        print(f"🔍 DEBUG: Have 2 elements, checking combination")
                    combination_key = tuple(self.selected_elements)
                    if VERBOSE_LOGS:
                        print(f"🔍 DEBUG: Combination key: {combination_key}")
                    if combination_key in config.spells.MAGIC_COMBINATIONS:
                        self.current_combination = config.spells.MAGIC_COMBINATIONS[combination_key]
                        self.combination_animation = 1.0
                        if VERBOSE_LOGS:
                            print("✨ Combination ready: {} ({} + {})".format(
                                self.current_combination["display_name"],
                                self.selected_elements[0], self.selected_elements[1]
                            ))
                        return True
                    else:
                        # Invalid combination - reset and wait for new selection
                        if VERBOSE_LOGS:
                            print("❌ Invalid combination: {} + {} - try again".format(
                                self.selected_elements[0], self.selected_elements[1]
                            ))
                        self.reset_combination()
                        return False
                
                if VERBOSE_LOGS:
                    print("📝 Selected element: {} (need {} more)".format(
                        element_id, 2 - len(self.selected_elements)
                    ))
                return True
        
        if VERBOSE_LOGS:
            print(f"🔍 DEBUG: Element index not found for '{element_id}'")
        return False
    
    def handle_cast_spell(self) -> Optional[Dict[str, Any]]:
        """
        Handle spell casting - starts cooldown if combination is ready
        
        Returns:
            Dict with spell data if successful, None if failed
        """
        if not self.current_combination:
            if VERBOSE_LOGS:
                print("🚫 No spell combination ready")
            return None
        
        spell_id = self.current_combination["id"]
        
        if self.cooldown_manager.is_ready(spell_id):
            # Start cooldown
            cooldown_duration = self.current_combination.get("cooldown", config.spells.DEFAULT_COOLDOWN)
            self.cooldown_manager.start_cooldown(spell_id, cooldown_duration)
            
            if VERBOSE_LOGS:
                print("✨ Cast spell: {} - cooldown started ({:.1f}s)".format(
                    self.current_combination["display_name"], cooldown_duration
                ))

            # Play combo sound if available
            try:
                from managers.asset_manager import AssetManager
                assets = AssetManager()
                sounds_dir = Path(config.paths.SOUNDS_DIR)
                # Prefer specific combo file naming; fuzzy match allowed
                a, b = tuple(self.current_combination.get("elements", []))[:2] if self.current_combination.get("elements") else (None, None)
                combo_dir = sounds_dir / "spells" / "combos"
                sound_path = None
                # Explicit sound on combination config takes priority
                explicit = self.current_combination.get("sound")
                if explicit:
                    p = sounds_dir / explicit
                    if p.exists():
                        sound_path = str(p)
                # Try fireball first if spell_id matches
                if spell_id == "fireball":
                    # common names: fireball.wav/mp3/ogg
                    for ext in (".wav", ".ogg", ".mp3"):
                        p = combo_dir / ("fireball" + ext)
                        if p.exists():
                            sound_path = str(p); break
                    if sound_path is None:
                        # fuzzy: any file containing "fireball"
                        for f in combo_dir.iterdir():
                            if f.is_file() and "fireball" in f.stem.lower() and f.suffix.lower() in (".wav", ".ogg", ".mp3"):
                                sound_path = str(f); break
                # fallback: use element pair keywords
                if sound_path is None and a and b:
                    keyparts = [a, b]
                    for f in combo_dir.glob("*.*"):
                        if f.suffix.lower() not in (".wav", ".ogg", ".mp3"):
                            continue
                        stem = f.stem.lower()
                        if all(part in stem for part in keyparts):
                            sound_path = str(f); break

                if sound_path:
                    snd = assets.load_sound(sound_path)
                    if snd:
                        try:
                            from managers.settings_manager import SettingsManager
                            sm = SettingsManager()
                            if sm.master_mute:
                                vol = 0.0
                            else:
                                vol = max(0.0, min(1.0, float(sm.sound_volume) * float(sm.master_volume)))
                            snd.set_volume(vol)
                        except Exception:
                            pass
                        snd.play()
            except Exception as _e:
                # Non-fatal; continue silently
                pass
            
            # Erstelle Spell-Daten bevor Reset
            spell_data = {
                "combination": self.current_combination.copy(),
                "elements": self.selected_elements.copy(),
                "success": True
            }
            
            # Reset combination after casting
            self.reset_combination()
            
            return spell_data
        else:
            remaining = self.cooldown_manager.time_remaining(spell_id)
            if VERBOSE_LOGS:
                print("🚫 Spell {} on cooldown: {:.1f}s remaining".format(
                    self.current_combination["display_name"], remaining
                ))
            return None
    
    def reset_combination(self):
        """Reset the current element combination"""
        self.selected_elements = []
        self.current_combination = None
    
    def get_current_spell_id(self) -> Optional[str]:
        """Get the ID of the current ready combination"""
        return self.current_combination["id"] if self.current_combination else None
    
    def get_current_spell_elements(self) -> Optional[List[str]]:
        """Get the magic system elements for the current combination"""
        return self.current_combination["elements"] if self.current_combination else None
    
    def update(self, dt: float):
        """Update animations"""
        # Update element animations
        for i in range(len(self.element_animations)):
            if self.element_animations[i] > 0:
                self.element_animations[i] = max(0, self.element_animations[i] - dt * 4.0)
        
        # Update combination animation
        if self.combination_animation > 0:
            self.combination_animation = max(0, self.combination_animation - dt * 2.0)
    
    def get_position(self, screen_height: int) -> Tuple[int, int]:
        """Calculate position on screen"""
        x = 20  # Left margin
        bg = self.background_surface
        if bg is None:
            self.create_background_surface()
            bg = self.background_surface
        y = screen_height - 120 - (bg.get_height() if bg else 0)
        return (x, y)
    
    def render(self, screen: pygame.Surface, screen_height: int):
        """Render the element mixer to screen"""
        x, y = self.get_position(screen_height)
        
        # Draw background
        bg = self.background_surface
        if bg is None:
            self.create_background_surface()
            bg = self.background_surface
        if bg is not None:
            screen.blit(bg, (x, y))
        
        # Draw elements
        element_y = y + self.background_padding
        element_x = x + self.background_padding
        
        for i, element in enumerate(self.elements):
            self.render_element(screen, i, element, element_x, element_y)
            element_x += self.element_size + self.element_spacing
        
        # Draw combination slot
        combination_x = element_x + self.element_spacing
        combination_y = y + self.background_padding
        self.render_combination(screen, combination_x, combination_y)

        # Draw selected elements icons row under the bar
        self.render_selected_icons(screen, x, y)

    def render_selected_icons(self, screen: pygame.Surface, x: int, y: int):
        """Render the selected elements as icons with + and = visuals."""
        bg = self.background_surface
        if bg is None:
            self.create_background_surface()
            bg = self.background_surface
        bg_width = bg.get_width() if bg else 0
        label_y = y + (bg.get_height() if bg else 0) + self.label_margin_top

        size = int(self.element_size * 0.9)
        spacing = 8
        parts: List[pygame.Surface] = []

        if len(self.selected_elements) >= 1:
            parts.append(self.icons.get_element(self.selected_elements[0], size))
        if len(self.selected_elements) >= 2:
            parts.append(self._get_chip_surface("+", size))
            parts.append(self.icons.get_element(self.selected_elements[1], size))

        # If a valid combination exists, show = and result icon
        if len(self.selected_elements) == 2:
            key = tuple(self.selected_elements)
            if key in config.spells.MAGIC_COMBINATIONS:
                parts.append(self._get_chip_surface("=", size))
                a, b = key
                parts.append(self.icons.get_combo(a, b, size))

        if not parts:
            # Draw neutral label pill "Ausgewaehlt: -" mit modernem Style
            text_surface = self.label_font.render("Ausgewaehlt: -", True, (180, 190, 210))
            pill_w = text_surface.get_width() + 2 * self.label_padding + 8
            pill_h = text_surface.get_height() + 2 * self.label_padding
            pill = pygame.Surface((pill_w, pill_h), pygame.SRCALPHA)
            
            # Gradient-Hintergrund
            for row in range(pill_h):
                ratio = row / pill_h
                r = int(20 * (1 - ratio) + 12 * ratio)
                g = int(25 * (1 - ratio) + 16 * ratio)
                b = int(45 * (1 - ratio) + 32 * ratio)
                pygame.draw.line(pill, (r, g, b, self.label_bg_alpha), (0, row), (pill_w, row))
            
            # Rahmen
            pygame.draw.rect(pill, (50, 60, 90), (0, 0, pill_w, pill_h), 2)
            pygame.draw.rect(pill, (70, 85, 120), (1, 1, pill_w - 2, pill_h - 2), 1)
            
            label_x = x + (bg_width - pill_w) // 2
            screen.blit(pill, (label_x, label_y))
            screen.blit(text_surface, (label_x + self.label_padding + 4, label_y + self.label_padding))
            return

        total_w = sum(p.get_width() for p in parts) + spacing * (len(parts) - 1)
        total_h = max(p.get_height() for p in parts)
        label_x = x + (bg_width - total_w) // 2

        # Background pill mit modernem Style
        pill_w = total_w + 2 * self.label_padding + 4
        pill_h = total_h + 2 * self.label_padding
        pill = pygame.Surface((pill_w, pill_h), pygame.SRCALPHA)
        
        # Gradient-Hintergrund
        for row in range(pill_h):
            ratio = row / pill_h
            r = int(22 * (1 - ratio) + 14 * ratio)
            g = int(28 * (1 - ratio) + 18 * ratio)
            b = int(50 * (1 - ratio) + 35 * ratio)
            pygame.draw.line(pill, (r, g, b, self.label_bg_alpha + 20), (0, row), (pill_w, row))
        
        # Rahmen
        pygame.draw.rect(pill, (55, 65, 95), (0, 0, pill_w, pill_h), 2)
        pygame.draw.rect(pill, (75, 90, 130), (1, 1, pill_w - 2, pill_h - 2), 1)
        
        screen.blit(pill, (label_x - self.label_padding - 2, label_y - self.label_padding))

        # Zeichne alle Teile mit vertikaler Zentrierung
        cx = label_x
        for idx, part in enumerate(parts):
            # Zentriere vertikal basierend auf maximaler Hoehe
            part_y = label_y + (total_h - part.get_height()) // 2
            screen.blit(part, (cx, part_y))
            cx += part.get_width()
            if idx < len(parts) - 1:
                cx += spacing
    
    def render_element(self, screen: pygame.Surface, index: int, element: Dict, x: int, y: int):
        """Render a single element with modern styling"""
        size = self.element_size
        
        # Element-Hintergrund mit Gradient
        elem_bg = pygame.Surface((size, size), pygame.SRCALPHA)
        for row in range(size):
            ratio = row / size
            r = int(25 * (1 - ratio) + 15 * ratio)
            g = int(30 * (1 - ratio) + 20 * ratio)
            b = int(50 * (1 - ratio) + 35 * ratio)
            pygame.draw.line(elem_bg, (r, g, b, 200), (0, row), (size, row))
        
        # Rahmen um Element
        pygame.draw.rect(elem_bg, (50, 60, 85), (0, 0, size, size), 2)
        pygame.draw.rect(elem_bg, (70, 85, 120), (1, 1, size - 2, size - 2), 1)
        
        screen.blit(elem_bg, (x, y))
        
        # Draw element icon (zentriert)
        icon = self.element_icons[element["id"]]
        icon_x = x + (size - icon.get_width()) // 2
        icon_y = y + (size - icon.get_height()) // 2
        screen.blit(icon, (icon_x, icon_y))
        
        # Add press feedback animation (Glow-Effekt)
        if self.element_animations[index] > 0:
            flash_alpha = int(self.element_animations[index] * 80)
            glow = pygame.Surface((size, size), pygame.SRCALPHA)
            glow.fill((255, 255, 200, flash_alpha))
            screen.blit(glow, (x, y))
        
        # Draw key label mit Hintergrund
        key_text = element["key"]
        key_surface = self._get_key_label(key_text, self.small_font, (220, 230, 255))
        
        # Kleiner Hintergrund fuer die Taste
        key_bg = pygame.Surface((14, 14), pygame.SRCALPHA)
        key_bg.fill((20, 25, 40, 180))
        pygame.draw.rect(key_bg, (60, 80, 120), (0, 0, 14, 14), 1)
        
        key_x = x + size - 16
        key_y = y + size - 16
        screen.blit(key_bg, (key_x, key_y))
        
        key_rect = key_surface.get_rect(center=(key_x + 7, key_y + 7))
        screen.blit(key_surface, key_rect)
        
        # Highlight if selected (leuchtender Rahmen)
        if element["id"] in self.selected_elements:
            # Aeusserer Glow
            glow_rect = pygame.Surface((size + 4, size + 4), pygame.SRCALPHA)
            pygame.draw.rect(glow_rect, (255, 220, 100, 60), (0, 0, size + 4, size + 4), 3)
            screen.blit(glow_rect, (x - 2, y - 2))
            # Innerer heller Rahmen
            pygame.draw.rect(screen, (255, 230, 120), (x, y, size, size), 2)
    
    def render_combination(self, screen: pygame.Surface, x: int, y: int):
        """Render the combination slot with modern styling"""
        size = self.combination_size
        
        # Kombinations-Hintergrund mit Gradient
        combo_bg = pygame.Surface((size, size), pygame.SRCALPHA)
        for row in range(size):
            ratio = row / size
            r = int(18 * (1 - ratio) + 10 * ratio)
            g = int(22 * (1 - ratio) + 14 * ratio)
            b = int(40 * (1 - ratio) + 28 * ratio)
            pygame.draw.line(combo_bg, (r, g, b, 220), (0, row), (size, row))
        
        # Mehrstufiger Rahmen
        pygame.draw.rect(combo_bg, (40, 50, 75), (0, 0, size, size), 2)
        pygame.draw.rect(combo_bg, (60, 75, 110), (2, 2, size - 4, size - 4), 1)
        
        screen.blit(combo_bg, (x, y))
        
        if not self.current_combination:
            # Empty combination slot - "?" Platzhalter
            q_key = (id(self.font), size)
            text_surface = self._combo_qmark_cache.get(q_key)
            if text_surface is None:
                text_surface = self.font.render("?", True, (100, 110, 140))
                self._combo_qmark_cache[q_key] = text_surface
            text_rect = text_surface.get_rect(center=(x + self.combination_size // 2, y + self.combination_size // 2))
            screen.blit(text_surface, text_rect)
            return
        
        spell_id = self.current_combination["id"]
        is_ready = self.cooldown_manager.is_ready(spell_id)
        
        # Draw combination icon
        if spell_id in self.combination_icons:
            icon = self.combination_icons[spell_id]
            
            if not is_ready:
                # Dimmed version during cooldown (cached)
                dimmed_icon = self._get_dimmed_combo_icon(spell_id)
                if dimmed_icon is not None:
                    screen.blit(dimmed_icon, (x, y))
                else:
                    screen.blit(icon, (x, y))
                
                # Draw cooldown overlay
                cooldown_duration = self.current_combination.get("cooldown", config.spells.DEFAULT_COOLDOWN)
                progress = self.cooldown_manager.progress(spell_id, cooldown_duration)
                overlay_index = min(len(self.cooldown_overlays) - 1, int(progress * (len(self.cooldown_overlays) - 1)))
                cooldown_overlay = self.cooldown_overlays[overlay_index]
                screen.blit(cooldown_overlay, (x, y))
                
                # Draw countdown text
                remaining_time = self.cooldown_manager.time_remaining(spell_id)
                countdown_text = str(max(1, int(remaining_time + 0.5)))
                try:
                    number = int(countdown_text)
                except Exception:
                    number = 1
                text_surface, shadow_surface = self._get_countdown_surfaces(number)
                text_rect = text_surface.get_rect(center=(x + self.combination_size // 2, y + self.combination_size // 2))
                shadow_rect = shadow_surface.get_rect(center=(x + self.combination_size // 2 + 1, y + self.combination_size // 2 + 1))
                screen.blit(shadow_surface, shadow_rect)
                screen.blit(text_surface, text_rect)
            else:
                # Ready state
                screen.blit(icon, (x, y))
                
                # Add ready animation
                if self.combination_animation > 0:
                    flash_alpha = int(self.combination_animation * 100)
                    screen.blit(self._get_flash_surface(self.combination_size, flash_alpha), (x, y))
        
        # Draw border
        border_color = (100, 255, 100) if is_ready else (100, 100, 100)
        border_width = 2 if is_ready else 1
        pygame.draw.rect(screen, border_color, (x, y, self.combination_size, self.combination_size), border_width)
        
        # Draw "C" key label
        if self._combo_key_c_cache is None:
            key_surface = self._get_key_label("C", self.small_font, (255, 255, 255))
            shadow_surface = self._get_key_label("C", self.small_font, (0, 0, 0))
            self._combo_key_c_cache = (key_surface, shadow_surface)
        else:
            key_surface, shadow_surface = self._combo_key_c_cache
        key_rect = key_surface.get_rect()
        key_rect.bottomright = (x + self.combination_size - 2, y + self.combination_size - 2)
        shadow_rect = shadow_surface.get_rect()
        shadow_rect.bottomright = (key_rect.bottomright[0] + 1, key_rect.bottomright[1] + 1)
        
        screen.blit(shadow_surface, shadow_rect)
        screen.blit(key_surface, key_rect)
