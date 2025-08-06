# -*- coding: utf-8 -*-
"""
Hotkey Display System for Der Alchemist
Shows all available hotkeys in the top-left corner of the game
"""

import pygame
from typing import List, Tuple

class HotkeyDisplay:
    """Display system for showing game hotkeys"""
    
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.visible = True
        self.font_title = pygame.font.Font(None, 28)
        self.font_hotkey = pygame.font.Font(None, 24)
        self.font_small = pygame.font.Font(None, 20)
        
        # Position and styling - Rechte Seite des Bildschirms
        self.x = 0  # Wird in calculate_dimensions gesetzt
        self.y = 10
        self.line_height = 20
        self.padding = 8
        self.bg_alpha = 180
        
        # Colors
        self.bg_color = (0, 0, 0)
        self.border_color = (100, 100, 150)
        self.title_color = (255, 215, 0)
        self.hotkey_color = (100, 255, 100)
        self.desc_color = (200, 200, 200)
        self.separator_color = (80, 80, 120)
        
        # Hotkey data
        self.hotkeys = self.get_hotkey_data()
        
        # Calculate dimensions
        self.calculate_dimensions()
    
    def get_hotkey_data(self) -> List[Tuple[str, str, str]]:
        """Get all hotkey data organized by category"""
        return [
            # Category, Key, Description
            ("STEUERUNG", "", ""),
            ("", "W A S D", "Bewegung"),
            ("", "Maus", "Blickrichtung"),
            ("", "Linksklick", "Feuerball"),
            ("", "Leertaste", "Angriff"),
            ("", "", ""),
            
            ("INTERFACE", "", ""),
            ("", "ESC", "Pause-Menü"),
            ("", "Tab", "Inventar"),
            ("", "H", "Hotkeys ein/aus"),
            ("", "", ""),
            
            ("SPEICHERN", "", ""),
            ("", "F9-F12", "Slots 1-4"),
            ("", "", ""),
            
            ("DEBUG", "", ""),
            ("", "F3", "FPS ein/aus"),
            ("", "F4", "FPS-Details"),
            ("", "F5", "Reset Stats"),
            ("", "F6", "Performance"),
        ]
    
    def calculate_dimensions(self):
        """Calculate the display dimensions based on content"""
        max_width = 0
        line_count = 0
        
        for category, key, desc in self.hotkeys:
            if category:  # Category header
                text = f"═══ {category} ═══"
                width = self.font_title.size(text)[0]
            elif key and desc:  # Hotkey entry
                text = f"{key}: {desc}"
                width = self.font_hotkey.size(text)[0]
            else:  # Empty line
                width = 0
            
            max_width = max(max_width, width)
            line_count += 1
        
        self.width = max_width + self.padding * 2
        self.height = line_count * self.line_height + self.padding * 2
        
        # Update x position to align to right edge
        self.x = self.screen.get_width() - self.width - 10  # 10 Pixel Abstand vom Rand
    
    def toggle_visibility(self):
        """Toggle hotkey display visibility"""
        self.visible = not self.visible
    
    def draw(self):
        """Draw the hotkey display"""
        if not self.visible:
            return
        
        # Create background surface with transparency
        bg_surface = pygame.Surface((self.width, self.height))
        bg_surface.set_alpha(self.bg_alpha)
        bg_surface.fill(self.bg_color)
        
        # Draw background
        self.screen.blit(bg_surface, (self.x, self.y))
        
        # Draw border
        border_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(self.screen, self.border_color, border_rect, 2)
        
        # Draw hotkey entries
        current_y = self.y + self.padding
        
        for category, key, desc in self.hotkeys:
            if category:  # Category header
                text = f"═══ {category} ═══"
                text_surface = self.font_title.render(text, True, self.title_color)
                self.screen.blit(text_surface, (self.x + self.padding, current_y))
                
            elif key and desc:  # Hotkey entry
                # Draw key in green
                key_surface = self.font_hotkey.render(f"{key}:", True, self.hotkey_color)
                self.screen.blit(key_surface, (self.x + self.padding, current_y))
                
                # Draw description in white
                key_width = self.font_hotkey.size(f"{key}: ")[0]
                desc_surface = self.font_hotkey.render(desc, True, self.desc_color)
                self.screen.blit(desc_surface, (self.x + self.padding + key_width, current_y))
            
            # Empty lines just add spacing
            current_y += self.line_height
        
        # Draw toggle hint at bottom
        hint_text = "H: Hotkeys ein/aus"
        hint_surface = self.font_small.render(hint_text, True, (150, 150, 150))
        hint_y = self.y + self.height - 25
        self.screen.blit(hint_surface, (self.x + self.padding, hint_y))
