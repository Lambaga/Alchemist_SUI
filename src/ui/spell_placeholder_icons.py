# -*- coding: utf-8 -*-
"""
Spell Placeholder Icon Generator
Generates temporary colored placeholder icons for the spell system
"""

import pygame
from typing import Dict, Tuple, List


def create_placeholder_icons(size: Tuple[int, int] = (64, 64)) -> Dict[str, pygame.Surface]:
    """
    Creates placeholder icons for all spells
    
    Args:
        size: Tuple of (width, height) for icon size
        
    Returns:
        Dictionary mapping spell IDs to pygame.Surface icons
    """
    icons = {}
    
    # Spell colors and labels
    spell_data = {
        "fireball": {"color": (255, 100, 50), "label": "S1"},
        "healing": {"color": (100, 255, 100), "label": "S2"},
        "shield": {"color": (200, 200, 255), "label": "S3"},
        "whirlwind": {"color": (255, 200, 100), "label": "S4"},
        "invisibility": {"color": (200, 150, 255), "label": "S5"},
        "waterbolt": {"color": (100, 150, 255), "label": "S6"}
    }
    
    font = pygame.font.Font(None, 24)
    
    for spell_id, data in spell_data.items():
        # Create surface with alpha channel
        icon = pygame.Surface(size, pygame.SRCALPHA)
        
        # Fill with spell color
        icon.fill(data["color"])
        
        # Add a border
        pygame.draw.rect(icon, (0, 0, 0), icon.get_rect(), 3)
        
        # Add label text
        text_surface = font.render(data["label"], True, (0, 0, 0))
        text_rect = text_surface.get_rect(center=(size[0] // 2, size[1] // 2))
        icon.blit(text_surface, text_rect)
        
        icons[spell_id] = icon
    
    return icons


def create_cooldown_overlay_surfaces(size: Tuple[int, int] = (64, 64), segments: int = 60) -> List[pygame.Surface]:
    """
    Pre-generates cooldown overlay surfaces for radial wipe animation
    
    Args:
        size: Icon size
        segments: Number of segments for smooth animation (60 = 1 per degree * 60 = smooth)
        
    Returns:
        List of surfaces with progressively more area covered (0% to 100%)
    """
    overlays = []
    
    for i in range(segments + 1):
        # Create surface with alpha
        overlay = pygame.Surface(size, pygame.SRCALPHA)
        
        progress = i / segments  # 0.0 to 1.0
        
        if progress > 0:
            # Calculate angle (0 to 360 degrees)
            angle = progress * 360
            
            # Create a pie slice mask
            center = (size[0] // 2, size[1] // 2)
            radius = min(size) // 2
            
            # Points for the pie slice
            points = [center]
            
            # Add arc points
            for a in range(0, int(angle) + 1, 2):  # Every 2 degrees for performance
                x = center[0] + int(radius * pygame.math.Vector2(1, 0).rotate(a - 90).x)
                y = center[1] + int(radius * pygame.math.Vector2(1, 0).rotate(a - 90).y)
                points.append((x, y))
            
            if len(points) > 2:
                # Draw filled polygon for the cooldown area
                pygame.draw.polygon(overlay, (0, 0, 0, 128), points)
        
        overlays.append(overlay)
    
    return overlays
