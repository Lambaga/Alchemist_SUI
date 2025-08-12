# -*- coding: utf-8 -*-
"""
Generates placeholder spell icons for the spell bar system.
Creates simple colored 64x64 PNG files with spell names.
"""

import pygame
import os
from pathlib import Path

# Initialize pygame for surface creation
pygame.init()

# Configuration
ICON_SIZE = 64
FONT_SIZE = 16
BACKGROUND_COLORS = [
    (220, 50, 50),   # Red - Fireball
    (50, 220, 50),   # Green - Healing  
    (50, 150, 220),  # Blue - Shield
    (200, 200, 50),  # Yellow - Whirlwind
    (150, 50, 220),  # Purple - Invisibility
    (50, 200, 220),  # Cyan - Waterbolt
]

SPELL_NAMES = [
    "FB",  # Fireball
    "HL",  # Healing
    "SH",  # Shield
    "WW",  # Whirlwind
    "IN",  # Invisibility
    "WB",  # Waterbolt
]

SPELL_FILES = [
    "fireball.png",
    "healing.png", 
    "shield.png",
    "whirlwind.png",
    "invisibility.png",
    "waterbolt.png"
]

def create_placeholder_icon(color, text, filepath):
    """Create a simple placeholder icon with colored background and text"""
    # Create surface
    surface = pygame.Surface((ICON_SIZE, ICON_SIZE))
    surface.fill(color)
    
    # Add border
    pygame.draw.rect(surface, (255, 255, 255), surface.get_rect(), 2)
    
    # Add text
    font = pygame.font.Font(None, FONT_SIZE)
    text_surface = font.render(text, True, (255, 255, 255))
    text_rect = text_surface.get_rect(center=(ICON_SIZE//2, ICON_SIZE//2))
    surface.blit(text_surface, text_rect)
    
    # Save as PNG
    pygame.image.save(surface, filepath)
    print("Created: {}".format(filepath))

def main():
    """Generate all placeholder spell icons"""
    # Get the assets directory
    script_dir = Path(__file__).parent
    assets_dir = script_dir.parent / "assets" / "ui" / "spells"
    
    # Create directory if it doesn't exist
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    print("Generating placeholder spell icons...")
    
    # Generate each icon
    for i, (color, name, filename) in enumerate(zip(BACKGROUND_COLORS, SPELL_NAMES, SPELL_FILES)):
        filepath = assets_dir / filename
        create_placeholder_icon(color, name, str(filepath))
    
    print("All placeholder icons generated successfully!")
    print("Icons saved to: {}".format(assets_dir))

if __name__ == "__main__":
    main()
