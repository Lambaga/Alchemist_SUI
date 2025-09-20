# -*- coding: utf-8 -*-
"""
Spell System Demo - Quick test of the 6-spell bar functionality
Shows all spell icons and tests cooldown animations
"""

import pygame
import sys
import os
import time

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'core'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'ui'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'systems'))

from systems.spell_cooldown_manager import SpellCooldownManager
from ui.spell_bar import SpellBar

def main():
    """Simple demonstration of the spell bar system"""
    print("🧙‍♂️ Spell System Demo")
    print("Controls:")
    print("  1-6: Cast spells (with 3-second cooldown)")
    print("  ESC: Exit")
    print("  Watch the cooldown animations!")
    
    pygame.init()
    
    # Create a simple test window
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Spell Bar Demo")
    clock = pygame.time.Clock()
    
    # Initialize spell system
    cooldown_manager = SpellCooldownManager()
    spell_bar = SpellBar(cooldown_manager)
    
    # Background color
    background_color = (30, 30, 50)
    
    running = True
    while running:
        dt = clock.tick(60) / 1000.0  # 60 FPS, delta time in seconds
        
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                # Test spell keys 1-6
                elif event.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6]:
                    spell_index = event.key - pygame.K_1  # Convert to 0-5 index
                    success = spell_bar.handle_spell_cast(spell_index)
                    if success:
                        print("✨ Spell {} cast successfully!".format(spell_index + 1))
                    else:
                        print("🚫 Spell {} on cooldown!".format(spell_index + 1))
        
        # Update
        cooldown_manager.update()
        spell_bar.update(dt)
        
        # Draw
        screen.fill(background_color)
        
        # Draw title
        font = pygame.font.Font(None, 48)
        title = font.render("Spell Bar Demo", True, (255, 255, 255))
        screen.blit(title, (screen.get_width() // 2 - title.get_width() // 2, 50))
        
        # Draw instructions
        small_font = pygame.font.Font(None, 24)
        instructions = [
            "Press keys 1-6 to cast spells",
            "Each spell has a 3-second cooldown",
            "Watch the radial countdown animation",
            "ESC to exit"
        ]
        
        for i, instruction in enumerate(instructions):
            text = small_font.render(instruction, True, (200, 200, 200))
            screen.blit(text, (50, 120 + i * 30))
        
        # Draw spell bar (centered)
        spell_bar.render(screen, screen.get_height())
        
        # Show active cooldowns
        active_cooldowns = cooldown_manager.get_all_cooldowns()
        if active_cooldowns:
            cooldown_text = "Active cooldowns: " + ", ".join(
                "{}({:.1f}s)".format(spell_id, remaining) 
                for spell_id, remaining in active_cooldowns.items()
            )
            text = small_font.render(cooldown_text, True, (255, 255, 100))
            screen.blit(text, (50, screen.get_height() - 50))
        
        pygame.display.flip()
    
    pygame.quit()
    print("🧙‍♂️ Spell system demo completed!")

if __name__ == "__main__":
    main()
