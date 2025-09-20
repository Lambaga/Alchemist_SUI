# -*- coding: utf-8 -*-
"""
Test des Input-Systems mit Magie
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

import pygame
pygame.init()

# Test Input Event
def test_input_events():
    print("=== INPUT-SYSTEM TEST ===")
    
    from systems.input_system import UniversalInputSystem
    
    input_system = UniversalInputSystem()
    
    # Simuliere F-Taste für Feuer
    print("\n--- Test F-Taste (Feuer) ---")
    f_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_f)
    action = input_system.handle_event(f_event)
    print(f"F-Taste gedrückt -> Action: {action}")
    
    # Simuliere W-Taste für Wasser  
    print("\n--- Test W-Taste (Wasser) ---")
    w_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_w)
    action = input_system.handle_event(w_event)
    print(f"W-Taste gedrückt -> Action: {action}")
    
    # Simuliere C-Taste für Zaubern
    print("\n--- Test C-Taste (Zaubern) ---")
    c_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_c)
    action = input_system.handle_event(c_event)
    print(f"C-Taste gedrückt -> Action: {action}")
    
    print("\n--- Action-Mapping überprüfen ---")
    keyboard_mapping = input_system.action_mapping[input_system.InputDevice.KEYBOARD]
    print("Verfügbare Keyboard-Actions:")
    for action_name, key in keyboard_mapping.items():
        if 'magic' in action_name or action_name == 'cast_magic':
            key_name = pygame.key.name(key)
            print(f"  {action_name}: {key_name}")

if __name__ == "__main__":
    test_input_events()
