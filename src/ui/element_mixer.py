# -*- coding: utf-8 -*-
"""
Element Mixer UI Component
Shows the 3 elements (Fire, Water, Stone) and current combination with cooldowns
"""

import pygame
import math
from typing import Optional, List, Tuple, Dict
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
        
        # Load element icons (or create placeholders)
        self.element_icons = {}
        self.combination_icons = {}
        self.load_icons()
        
        # Create cooldown overlays
        self.cooldown_overlays = self.create_cooldown_overlays()
        
        # UI surfaces
        self.background_surface = None
        self.create_background_surface()

        # Cached element name lookup for display
        self.element_name_map = {e["id"]: e["name"] for e in self.elements}
        # Bottom label styling
        self.label_margin_top = 6
        self.label_padding = 6
        self.label_bg_alpha = 160
        
        # Animation states
        self.element_animations = [0.0] * 3  # For element press feedback
        self.combination_animation = 0.0     # For combination ready/cast animation
        
        print("✨ ElementMixer initialized with 3 elements")
    
    def load_icons(self):
        """Load element icons and combination spell icons"""
        # Load element icons (or create simple placeholders)
        for element in self.elements:
            self.element_icons[element["id"]] = self.create_element_icon(element)
        
        # Load combination spell icons
        for combination_key, spell_data in config.spells.MAGIC_COMBINATIONS.items():
            icon_path = Path(config.paths.ASSETS_DIR) / "ui" / "spells" / Path(spell_data["icon_path"]).name
            
            try:
                if icon_path.exists():
                    icon = pygame.image.load(str(icon_path)).convert_alpha()
                    icon = pygame.transform.scale(icon, (self.combination_size, self.combination_size))
                    self.combination_icons[spell_data["id"]] = icon
                    print("Loaded combination icon: {}".format(spell_data["id"]))
                else:
                    self.combination_icons[spell_data["id"]] = self.create_combination_placeholder(spell_data)
                    print("Created placeholder for combination: {}".format(spell_data["id"]))
            except Exception as e:
                print("Error loading icon for {}: {}".format(spell_data["id"], e))
                self.combination_icons[spell_data["id"]] = self.create_combination_placeholder(spell_data)
    
    def create_element_icon(self, element: Dict) -> pygame.Surface:
        """Create a simple element icon"""
        surface = pygame.Surface((self.element_size, self.element_size), pygame.SRCALPHA)
        surface.fill(element["color"])
        
        # Add border
        pygame.draw.rect(surface, (255, 255, 255), surface.get_rect(), 2)
        
        # Add element symbol
        text = element["name"][0]  # First letter
        text_surface = self.font.render(text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(self.element_size // 2, self.element_size // 2))
        surface.blit(text_surface, text_rect)
        
        return surface
    
    def create_combination_placeholder(self, spell_data: Dict) -> pygame.Surface:
        """Create a placeholder for spell combinations"""
        surface = pygame.Surface((self.combination_size, self.combination_size), pygame.SRCALPHA)
        
        # Use a different color based on spell type
        color_map = {
            "fireball": (255, 100, 50),
            "waterbolt": (50, 150, 255), 
            "shield": (200, 200, 100),
            "healing": (100, 255, 100),
            "whirlwind": (255, 150, 50),
            "invisibility": (150, 100, 255)
        }
        
        color = color_map.get(spell_data["id"], (150, 150, 150))
        surface.fill(color)
        
        # Add border
        pygame.draw.rect(surface, (255, 255, 255), surface.get_rect(), 2)
        
        # Add spell initial
        text = spell_data["display_name"][0]
        text_surface = pygame.font.Font(None, 24).render(text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(self.combination_size // 2, self.combination_size // 2))
        surface.blit(text_surface, text_rect)
        
        return surface
    
    def create_cooldown_overlays(self) -> List[pygame.Surface]:
        """Create cooldown overlay surfaces for smooth animation"""
        overlays = []
        steps = 60
        
        for step in range(steps + 1):
            progress = step / steps
            overlay = self.create_cooldown_overlay(progress, self.combination_size)
            overlays.append(overlay)
        
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
        """Create the background surface for the element mixer"""
        # Calculate total width: 3 elements + spacing + combination slot + padding
        elements_width = 3 * self.element_size + 2 * self.element_spacing
        total_width = elements_width + self.element_spacing * 2 + self.combination_size + 2 * self.background_padding
        total_height = max(self.element_size, self.combination_size) + 2 * self.background_padding
        
        self.background_surface = pygame.Surface((total_width, total_height), pygame.SRCALPHA)
        background_color = (*config.colors.UI_BACKGROUND, self.background_alpha)
        self.background_surface.fill(background_color)
        
        # Add rounded corners effect
        pygame.draw.rect(self.background_surface, background_color, 
                        self.background_surface.get_rect(), border_radius=8)
    
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
            print(f"🚫 DEBOUNCE: Ignoring duplicate press of '{element_id}' within {self.debounce_time}s")
            return False
        
        # Update debounce tracking
        self.last_element_press = {"element": element_id, "time": current_time}
        
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
            # If we already have 2 elements, reset first
            if len(self.selected_elements) >= 2:
                print("🔍 DEBUG: Resetting because we already have 2 elements")
                self.reset_combination()
                print(f"� DEBUG: After reset, selected_elements: {self.selected_elements}")
            
            # Add element to selection (max 2)
            if len(self.selected_elements) < 2:
                print(f"🔍 DEBUG: Adding element '{element_id}' to selection")
                self.selected_elements.append(element_id)
                print(f"🔍 DEBUG: After adding, selected_elements: {self.selected_elements}")
                self.element_animations[element_index] = 1.0
                
                # Check if we have a valid combination (only when we have exactly 2)
                if len(self.selected_elements) == 2:
                    print(f"🔍 DEBUG: Have 2 elements, checking combination")
                    combination_key = tuple(self.selected_elements)
                    print(f"🔍 DEBUG: Combination key: {combination_key}")
                    if combination_key in config.spells.MAGIC_COMBINATIONS:
                        self.current_combination = config.spells.MAGIC_COMBINATIONS[combination_key]
                        self.combination_animation = 1.0
                        print("✨ Combination ready: {} ({} + {})".format(
                            self.current_combination["display_name"],
                            self.selected_elements[0], self.selected_elements[1]
                        ))
                        return True
                    else:
                        # Invalid combination - reset and wait for new selection
                        print("❌ Invalid combination: {} + {} - try again".format(
                            self.selected_elements[0], self.selected_elements[1]
                        ))
                        self.reset_combination()
                        return False
                
                print("📝 Selected element: {} (need {} more)".format(
                    element_id, 2 - len(self.selected_elements)
                ))
                return True
        
        print(f"🔍 DEBUG: Element index not found for '{element_id}'")
        return False
    
    def handle_cast_spell(self) -> dict:
        """
        Handle spell casting - starts cooldown if combination is ready
        
        Returns:
            Dict with spell data if successful, None if failed
        """
        if not self.current_combination:
            print("🚫 No spell combination ready")
            return None
        
        spell_id = self.current_combination["id"]
        
        if self.cooldown_manager.is_ready(spell_id):
            # Start cooldown
            cooldown_duration = self.current_combination.get("cooldown", config.spells.DEFAULT_COOLDOWN)
            self.cooldown_manager.start_cooldown(spell_id, cooldown_duration)
            
            print("✨ Cast spell: {} - cooldown started ({:.1f}s)".format(
                self.current_combination["display_name"], cooldown_duration
            ))
            
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
        y = screen_height - 120 - self.background_surface.get_height()
        return (x, y)
    
    def render(self, screen: pygame.Surface, screen_height: int):
        """Render the element mixer to screen"""
        x, y = self.get_position(screen_height)
        
        # Draw background
        screen.blit(self.background_surface, (x, y))
        
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

        # Draw selected elements label under the bar
        self.render_selected_label(screen, x, y)

    def get_selected_elements_text(self) -> str:
        """Return human-readable text of currently selected elements"""
        if not self.selected_elements:
            return "Ausgewählt: —"
        names = [self.element_name_map.get(eid, eid) for eid in self.selected_elements]
        return "Ausgewählt: " + " + ".join(names)

    def render_selected_label(self, screen: pygame.Surface, x: int, y: int):
        """Render a compact label below the element bar indicating selection"""
        text = self.get_selected_elements_text()
        text_surface = self.label_font.render(text, True, (255, 255, 255))

        # Center the label under the mixer background
        bg_width = self.background_surface.get_width()
        label_y = y + self.background_surface.get_height() + self.label_margin_top
        label_x = x + (bg_width - text_surface.get_width()) // 2

        # Background pill for readability
        pill_surf = pygame.Surface(
            (text_surface.get_width() + 2 * self.label_padding,
             text_surface.get_height() + 2 * self.label_padding),
            pygame.SRCALPHA,
        )
        bg_color = (*config.colors.UI_BACKGROUND, self.label_bg_alpha)
        pill_surf.fill(bg_color)
        pygame.draw.rect(pill_surf, bg_color, pill_surf.get_rect(), border_radius=8)

        screen.blit(pill_surf, (label_x - self.label_padding, label_y - self.label_padding))
        screen.blit(text_surface, (label_x, label_y))
    
    def render_element(self, screen: pygame.Surface, index: int, element: Dict, x: int, y: int):
        """Render a single element"""
        # Draw element icon
        icon = self.element_icons[element["id"]]
        screen.blit(icon, (x, y))
        
        # Add press feedback animation
        if self.element_animations[index] > 0:
            flash_alpha = int(self.element_animations[index] * 100)
            flash_surface = pygame.Surface((self.element_size, self.element_size), pygame.SRCALPHA)
            flash_surface.fill((255, 255, 255, flash_alpha))
            screen.blit(flash_surface, (x, y))
        
        # Draw key label
        key_surface = self.small_font.render(element["key"], True, (255, 255, 255))
        key_rect = key_surface.get_rect()
        key_rect.bottomright = (x + self.element_size - 2, y + self.element_size - 2)
        
        # Add shadow
        shadow_surface = self.small_font.render(element["key"], True, (0, 0, 0))
        shadow_rect = shadow_surface.get_rect()
        shadow_rect.bottomright = (key_rect.bottomright[0] + 1, key_rect.bottomright[1] + 1)
        
        screen.blit(shadow_surface, shadow_rect)
        screen.blit(key_surface, key_rect)
        
        # Highlight if selected
        if element["id"] in self.selected_elements:
            pygame.draw.rect(screen, (255, 255, 100), (x, y, self.element_size, self.element_size), 2)
    
    def render_combination(self, screen: pygame.Surface, x: int, y: int):
        """Render the combination slot"""
        if not self.current_combination:
            # Empty combination slot
            pygame.draw.rect(screen, (100, 100, 100), (x, y, self.combination_size, self.combination_size), 2)
            # Draw "?" placeholder
            text_surface = self.font.render("?", True, (150, 150, 150))
            text_rect = text_surface.get_rect(center=(x + self.combination_size // 2, y + self.combination_size // 2))
            screen.blit(text_surface, text_rect)
            return
        
        spell_id = self.current_combination["id"]
        is_ready = self.cooldown_manager.is_ready(spell_id)
        
        # Draw combination icon
        if spell_id in self.combination_icons:
            icon = self.combination_icons[spell_id]
            
            if not is_ready:
                # Dimmed version during cooldown
                dimmed_icon = icon.copy()
                dimmed_overlay = pygame.Surface((self.combination_size, self.combination_size), pygame.SRCALPHA)
                dimmed_overlay.fill((0, 0, 0, 100))
                dimmed_icon.blit(dimmed_overlay, (0, 0))
                screen.blit(dimmed_icon, (x, y))
                
                # Draw cooldown overlay
                cooldown_duration = self.current_combination.get("cooldown", config.spells.DEFAULT_COOLDOWN)
                progress = self.cooldown_manager.progress(spell_id, cooldown_duration)
                overlay_index = min(len(self.cooldown_overlays) - 1, int(progress * (len(self.cooldown_overlays) - 1)))
                cooldown_overlay = self.cooldown_overlays[overlay_index]
                screen.blit(cooldown_overlay, (x, y))
                
                # Draw countdown text
                remaining_time = self.cooldown_manager.time_remaining(spell_id)
                countdown_text = str(max(1, int(remaining_time + 0.5)))
                
                text_surface = self.font.render(countdown_text, True, (255, 255, 255))
                text_rect = text_surface.get_rect(center=(x + self.combination_size // 2, y + self.combination_size // 2))
                
                # Text shadow
                shadow_surface = self.font.render(countdown_text, True, (0, 0, 0))
                shadow_rect = shadow_surface.get_rect(center=(x + self.combination_size // 2 + 1, y + self.combination_size // 2 + 1))
                screen.blit(shadow_surface, shadow_rect)
                screen.blit(text_surface, text_rect)
            else:
                # Ready state
                screen.blit(icon, (x, y))
                
                # Add ready animation
                if self.combination_animation > 0:
                    flash_alpha = int(self.combination_animation * 100)
                    flash_surface = pygame.Surface((self.combination_size, self.combination_size), pygame.SRCALPHA)
                    flash_surface.fill((255, 255, 255, flash_alpha))
                    screen.blit(flash_surface, (x, y))
        
        # Draw border
        border_color = (100, 255, 100) if is_ready else (100, 100, 100)
        border_width = 2 if is_ready else 1
        pygame.draw.rect(screen, border_color, (x, y, self.combination_size, self.combination_size), border_width)
        
        # Draw "C" key label
        key_surface = self.small_font.render("C", True, (255, 255, 255))
        key_rect = key_surface.get_rect()
        key_rect.bottomright = (x + self.combination_size - 2, y + self.combination_size - 2)
        
        shadow_surface = self.small_font.render("C", True, (0, 0, 0))
        shadow_rect = shadow_surface.get_rect()
        shadow_rect.bottomright = (key_rect.bottomright[0] + 1, key_rect.bottomright[1] + 1)
        
        screen.blit(shadow_surface, shadow_rect)
        screen.blit(key_surface, key_rect)
