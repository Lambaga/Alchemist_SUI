# -*- coding: utf-8 -*-
"""
Spell Bar UI Component
Displays 6 spell slots with cooldown animations and key bindings
"""

import pygame
import math
from typing import Optional, List, Tuple
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


class SpellBar:
    """
    UI component that displays the spell bar with 6 slots, cooldown animations, and key bindings
    """
    
    def __init__(self, spell_cooldown_manager):
        """
        Initialize the spell bar UI
        
        Args:
            spell_cooldown_manager: Instance of SpellCooldownManager for cooldown tracking
        """
        self.cooldown_manager = spell_cooldown_manager
        self.spells = config.spells.SPELLS.copy()
        
        # UI Configuration - Dynamisch basierend auf Bildschirmgröße
        bar_config = config.spells.get_bar_config()
        ui_settings = config.ui.get_ui_settings()
        
        self.slot_size = bar_config['SLOT_SIZE']
        self.slot_spacing = bar_config['SLOT_SPACING']
        self.background_padding = bar_config['BACKGROUND_PADDING']
        self.background_alpha = bar_config['BACKGROUND_ALPHA']
        self.ui_scale = ui_settings['UI_SCALE']
        
        # Calculate bar dimensions
        self.bar_width = (6 * self.slot_size) + (5 * self.slot_spacing) + (2 * self.background_padding)
        self.bar_height = self.slot_size + (2 * self.background_padding)
        
        # Load or create spell icons
        self.spell_icons = {}
        self.load_spell_icons()
        
        # Create cooldown overlays (precomputed for performance)
        self.cooldown_overlays = self.create_cooldown_overlays()
        
        # UI surfaces
        self.background_surface = None
        self.create_background_surface()
        
        # Font for countdown and key labels - Angepasst für kleine Bildschirme
        pygame.font.init()
        font_size_normal = ui_settings.get('FONT_SIZE_NORMAL', 20)
        font_size_small = ui_settings.get('FONT_SIZE_SMALL', 16)
        
        self.font = pygame.font.Font(None, font_size_normal)
        self.small_font = pygame.font.Font(None, font_size_small)
        
        # Animation states
        self.slot_animations = [0.0] * 6  # For press feedback animation
        self.selected_spell_index = -1    # Currently selected spell (-1 = none)
        
        display_settings = config.display.get_optimized_settings()
        screen_info = f"({display_settings.get('WINDOW_WIDTH')}x{display_settings.get('WINDOW_HEIGHT')})"
        print(f"✨ SpellBar initialized for {screen_info} with {len(self.spells)} spells")
        print(f"   📊 Slot size: {self.slot_size}px, UI scale: {self.ui_scale}")
    
    def load_spell_icons(self):
        """Load spell icons or create placeholders if not found"""
        assets_dir = Path(config.paths.ASSETS_DIR) / "ui" / "spells"
        # Prepare optional fallback icon loader
        try:
            from .spell_icons import SpellIcons
            icons = SpellIcons(base_size=self.slot_size)
        except Exception:
            icons = None
        
        for i, spell in enumerate(self.spells):
            icon_path = assets_dir / Path(spell["icon_path"]).name
            
            try:
                if icon_path.exists():
                    icon = pygame.image.load(str(icon_path)).convert_alpha()
                    icon = pygame.transform.scale(icon, (self.slot_size, self.slot_size))
                    self.spell_icons[spell["id"]] = icon
                    print("Loaded icon for '{}': {}".format(spell["id"], icon_path.name))
                elif icons is not None:
                    # Try to derive from element/combos assets by combination key if present
                    combo = spell.get("elements") or spell.get("combo")
                    if isinstance(combo, (list, tuple)) and len(combo) == 2:
                        a, b = combo
                        surf = icons.get_combo(a, b, self.slot_size)
                    else:
                        # fall back to display/name as element icon
                        surf = icons.get_element(spell.get("id", "?"), self.slot_size)
                    self.spell_icons[spell["id"]] = surf
                    print("Fallback icon for '{}' from assets/ui/spells".format(spell["id"]))
                else:
                    # Create a simple placeholder
                    self.spell_icons[spell["id"]] = self.create_placeholder_icon(i)
                    print("Created placeholder for '{}'".format(spell["id"]))
            except Exception as e:
                print("Failed to load icon for '{}': {}".format(spell["id"], e))
                self.spell_icons[spell["id"]] = self.create_placeholder_icon(i)
    
    def create_placeholder_icon(self, spell_index: int) -> pygame.Surface:
        """Create a simple placeholder icon for a spell"""
        surface = pygame.Surface((self.slot_size, self.slot_size), pygame.SRCALPHA)
        
        # Colors for different spells
        colors = [
            (220, 50, 50),   # Red
            (50, 220, 50),   # Green
            (50, 150, 220),  # Blue
            (200, 200, 50),  # Yellow
            (150, 50, 220),  # Purple
            (50, 200, 220),  # Cyan
        ]
        
        color = colors[spell_index % len(colors)]
        surface.fill(color)
        
        # Add border
        pygame.draw.rect(surface, (255, 255, 255), surface.get_rect(), 2)
        
        # Add spell number
        text = str(spell_index + 1)
        text_surface = self.font.render(text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(self.slot_size // 2, self.slot_size // 2))
        surface.blit(text_surface, text_rect)
        
        return surface
    
    def create_cooldown_overlays(self) -> List[pygame.Surface]:
        """
        Pre-create cooldown overlay surfaces for smooth animation
        Creates 60 surfaces representing different cooldown progress states
        """
        overlays = []
        steps = 60  # 60 steps for smooth animation
        
        for step in range(steps + 1):
            progress = step / steps  # 0.0 to 1.0
            overlay = self.create_cooldown_overlay(progress)
            overlays.append(overlay)
        
        print("Created {} cooldown overlay surfaces".format(len(overlays)))
        return overlays
    
    def create_cooldown_overlay(self, progress: float) -> pygame.Surface:
        """
        Create a radial cooldown overlay surface
        
        Args:
            progress: Progress from 0.0 (full overlay) to 1.0 (no overlay)
        """
        surface = pygame.Surface((self.slot_size, self.slot_size), pygame.SRCALPHA)
        
        if progress >= 1.0:
            return surface  # Empty surface when ready
        
        center = (self.slot_size // 2, self.slot_size // 2)
        radius = self.slot_size // 2
        
        # Create a semi-transparent overlay
        overlay_color = (0, 0, 0, 128)  # Semi-transparent black
        
        # Calculate the angle for the "pie slice" that should remain covered
        # progress 0.0 = full circle, progress 1.0 = no circle
        remaining_angle = 2 * math.pi * (1.0 - progress)
        
        # Draw the remaining cooldown portion as a pie slice
        if remaining_angle > 0:
            points = [center]  # Start with center point
            
            # Calculate points for the pie slice
            num_points = max(8, int(remaining_angle * 8))  # More points for larger angles
            for i in range(num_points + 1):
                angle = -math.pi / 2 + (i / num_points) * remaining_angle  # Start from top
                x = center[0] + int(radius * math.cos(angle))
                y = center[1] + int(radius * math.sin(angle))
                points.append((x, y))
            
            # Draw the filled polygon
            if len(points) > 2:
                pygame.draw.polygon(surface, overlay_color, points)
        
        return surface
    
    def create_background_surface(self):
        """Create the background surface for the spell bar"""
        self.background_surface = pygame.Surface((self.bar_width, self.bar_height), pygame.SRCALPHA)
        
        # Semi-transparent dark background
        background_color = (*config.colors.UI_BACKGROUND, self.background_alpha)
        self.background_surface.fill(background_color)
        
        # Optional: rounded corners (simple version)
        pygame.draw.rect(self.background_surface, background_color, 
                        self.background_surface.get_rect(), border_radius=8)
    
    def get_position(self, screen_height: int) -> Tuple[int, int]:
        """
        Calculate the position of the spell bar on screen
        
        Args:
            screen_height: Height of the game screen
            
        Returns:
            (x, y) position for the spell bar
        """
        bar_config = config.spells.get_bar_config()
        x = bar_config['BAR_POSITION'][0]  # Variable px from left (10 for 7-inch, 20 for standard)
        y = screen_height + bar_config['BAR_POSITION'][1] - self.bar_height  # Variable px from bottom
        return (x, y)
    
    def handle_spell_selection(self, spell_index: int) -> bool:
        """
        Handle spell selection (not casting) - just visual feedback
        
        Args:
            spell_index: Index of the spell (0-5)
            
        Returns:
            True if spell was successfully selected, False if on cooldown
        """
        if 0 <= spell_index < len(self.spells):
            spell = self.spells[spell_index]
            spell_id = spell["id"]
            
            # Check if spell is ready (not on cooldown)
            if self.cooldown_manager.is_ready(spell_id):
                # Set as selected spell
                self.selected_spell_index = spell_index
                
                # Trigger selection animation
                self.slot_animations[spell_index] = 0.5  # Softer flash for selection
                
                print("Selected spell: {} (slot {}) - Press C to cast!".format(spell["display_name"], spell_index + 1))
                return True
            else:
                # Spell on cooldown - show remaining time
                remaining = self.cooldown_manager.time_remaining(spell_id)
                print("Spell {} on cooldown: {:.1f}s remaining".format(spell["display_name"], remaining))
                return False
        
        return False
    
    def handle_spell_cast(self, spell_id: str) -> bool:
        """
        Handle actual spell casting - starts cooldown
        This should be called when the spell is actually cast (e.g., when pressing C)
        
        Args:
            spell_id: ID of the spell being cast
            
        Returns:
            True if spell was successfully cast, False if on cooldown
        """
        # Find the spell in our list
        spell_data = None
        spell_index = -1
        for i, spell in enumerate(self.spells):
            if spell["id"] == spell_id:
                spell_data = spell
                spell_index = i
                break
        
        if not spell_data:
            print("Warning: Unknown spell ID: {}".format(spell_id))
            return False
            
        if self.cooldown_manager.is_ready(spell_id):
            # Start cooldown
            cooldown_duration = spell_data.get("cooldown", config.spells.DEFAULT_COOLDOWN)
            self.cooldown_manager.start_cooldown(spell_id, cooldown_duration)
            
            # Trigger cast animation (stronger flash)
            if spell_index >= 0:
                self.slot_animations[spell_index] = 1.0
            
            print("✨ Cast spell: {} - cooldown started ({:.1f}s)".format(spell_data["display_name"], cooldown_duration))
            return True
        else:
            # Spell on cooldown
            remaining = self.cooldown_manager.time_remaining(spell_id)
            print("🚫 Spell {} on cooldown: {:.1f}s remaining".format(spell_data["display_name"], remaining))
            return False
    
    def get_selected_spell_id(self) -> str:
        """Get the ID of the currently selected spell"""
        if 0 <= self.selected_spell_index < len(self.spells):
            return self.spells[self.selected_spell_index]["id"]
        return None
    
    def get_selected_spell_name(self) -> str:
        """Get the display name of the currently selected spell"""
        if 0 <= self.selected_spell_index < len(self.spells):
            return self.spells[self.selected_spell_index]["display_name"]
        return None
    
    def clear_selection(self):
        """Clear the current spell selection"""
        self.selected_spell_index = -1
    
    def has_selection(self) -> bool:
        """Check if a spell is currently selected"""
        return self.selected_spell_index >= 0
    
    def update(self, dt: float):
        """
        Update animations and states
        
        Args:
            dt: Delta time in seconds
        """
        # Update press feedback animations
        for i in range(len(self.slot_animations)):
            if self.slot_animations[i] > 0:
                self.slot_animations[i] = max(0, self.slot_animations[i] - dt * 4.0)  # Fade out over 0.25 seconds
    
    def render(self, screen: pygame.Surface, screen_height: int):
        """
        Render the spell bar to the screen
        
        Args:
            screen: Pygame surface to render to
            screen_height: Height of the screen for positioning
        """
        # Get position
        bar_x, bar_y = self.get_position(screen_height)
        
        # Draw background
        screen.blit(self.background_surface, (bar_x, bar_y))
        
        # Draw each spell slot
        for i in range(6):
            slot_x = bar_x + self.background_padding + i * (self.slot_size + self.slot_spacing)
            slot_y = bar_y + self.background_padding
            
            self.render_spell_slot(screen, i, slot_x, slot_y)
    
    def render_spell_slot(self, screen: pygame.Surface, slot_index: int, x: int, y: int):
        """
        Render a single spell slot
        
        Args:
            screen: Surface to render to
            slot_index: Index of the spell slot (0-5)
            x, y: Position to render at
        """
        if slot_index >= len(self.spells):
            return
        
        spell = self.spells[slot_index]
        spell_id = spell["id"]
        
        # Get spell icon
        icon = self.spell_icons.get(spell_id)
        if not icon:
            return
        
        # Check cooldown state
        is_ready = self.cooldown_manager.is_ready(spell_id)
        
        if is_ready:
            # Spell is ready - render normally
            screen.blit(icon, (x, y))
            
            # Add press feedback animation
            if self.slot_animations[slot_index] > 0:
                # Create a bright flash overlay
                flash_alpha = int(self.slot_animations[slot_index] * 100)
                flash_surface = pygame.Surface((self.slot_size, self.slot_size), pygame.SRCALPHA)
                flash_surface.fill((255, 255, 255, flash_alpha))
                screen.blit(flash_surface, (x, y))
        
        else:
            # Spell on cooldown - render dimmed with countdown
            
            # Dim the icon
            dimmed_icon = icon.copy()
            dimmed_overlay = pygame.Surface((self.slot_size, self.slot_size), pygame.SRCALPHA)
            dimmed_overlay.fill((0, 0, 0, 100))  # Dark overlay
            dimmed_icon.blit(dimmed_overlay, (0, 0))
            screen.blit(dimmed_icon, (x, y))
            
            # Get cooldown progress
            cooldown_duration = spell.get("cooldown", config.spells.DEFAULT_COOLDOWN)
            progress = self.cooldown_manager.progress(spell_id, cooldown_duration)
            
            # Draw cooldown overlay (radial wipe)
            overlay_index = min(len(self.cooldown_overlays) - 1, int(progress * (len(self.cooldown_overlays) - 1)))
            cooldown_overlay = self.cooldown_overlays[overlay_index]
            screen.blit(cooldown_overlay, (x, y))
            
            # Draw countdown text
            remaining_time = self.cooldown_manager.time_remaining(spell_id)
            countdown_text = str(max(1, int(remaining_time + 0.5)))  # Round up
            
            text_surface = self.font.render(countdown_text, True, (255, 255, 255))
            text_rect = text_surface.get_rect(center=(x + self.slot_size // 2, y + self.slot_size // 2))
            
            # Add text shadow for readability
            shadow_surface = self.font.render(countdown_text, True, (0, 0, 0))
            shadow_rect = shadow_surface.get_rect(center=(x + self.slot_size // 2 + 1, y + self.slot_size // 2 + 1))
            screen.blit(shadow_surface, shadow_rect)
            screen.blit(text_surface, text_rect)
        
        # Draw key binding label
        key_text = str(slot_index + 1)
        key_surface = self.small_font.render(key_text, True, (255, 255, 255))
        
        # Position in bottom-right corner of slot
        key_rect = key_surface.get_rect()
        key_rect.bottomright = (x + self.slot_size - 2, y + self.slot_size - 2)
        
        # Add small shadow
        shadow_surface = self.small_font.render(key_text, True, (0, 0, 0))
        shadow_rect = shadow_surface.get_rect()
        shadow_rect.bottomright = (key_rect.bottomright[0] + 1, key_rect.bottomright[1] + 1)
        
        screen.blit(shadow_surface, shadow_rect)
        screen.blit(key_surface, key_rect)
        
        # Draw slot border - highlight if selected
        if slot_index == self.selected_spell_index:
            # Selected spell - bright yellow border
            border_color = (255, 255, 100)
            border_width = 2
        elif is_ready:
            # Ready but not selected - normal border
            border_color = (100, 100, 100)
            border_width = 1
        else:
            # On cooldown - dark border
            border_color = (60, 60, 60)
            border_width = 1
            
        pygame.draw.rect(screen, border_color, (x, y, self.slot_size, self.slot_size), border_width)
