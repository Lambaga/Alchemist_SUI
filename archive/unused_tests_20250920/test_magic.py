#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Direkter Magie-System Test
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'src', 'systems'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'src', 'entities'))

# Pygame initialisieren
import pygame
pygame.init()

try:
    from systems.magic_system import MagicSystem, ElementType
    print("✅ Magic System erfolgreich importiert")
except Exception as e:
    print(f"❌ Fehler beim Import: {e}")
    sys.exit(1)

# Mock Player für Test
class MockPlayer:
    def __init__(self):
        self.current_health = 50
        self.max_health = 100
        self.rect = pygame.Rect(100, 100, 32, 32)
        self.facing_right = True
        
    def take_damage(self, damage):
        self.current_health = max(0, self.current_health - damage)
        
print("🧪 Starte Magie-System Test...")

# Mock Player erstellen
player = MockPlayer()
print(f"Player HP: {player.current_health}/{player.max_health}")

# Magic System erstellen
magic_system = MagicSystem()
print("Magic System erstellt")

# Test: Heilungstrank
print("\n🔥💧 Teste Heilungstrank (Feuer + Wasser)...")
magic_system.add_element(ElementType.FEUER)
magic_system.add_element(ElementType.WASSER)
print(f"Elemente hinzugefügt: {magic_system.get_selected_elements_str()}")

# Zauber wirken
result = magic_system.cast_magic(player)
print(f"Player HP nach Heilung: {player.current_health}/{player.max_health}")

print("\n✅ Test abgeschlossen!")
