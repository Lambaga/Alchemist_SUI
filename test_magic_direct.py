# -*- coding: utf-8 -*-
"""
Direkter Test des Magie-Systems
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Pygame initialisieren (Minimal)
import pygame
pygame.init()

# Mock Player Klasse für Test
class MockPlayer:
    def __init__(self):
        self.max_health = 100
        self.current_health = 50  # Halb Gesundheit für Heilung-Test
        self.rect = pygame.Rect(400, 300, 64, 64)
        self.facing_right = True
    
    def __str__(self):
        return f"MockPlayer(HP: {self.current_health}/{self.max_health})"

# Magie-System importieren
from systems.magic_system import MagicSystem, ElementType

def test_magic_system():
    print("=== MAGIE-SYSTEM TEST ===")
    
    # System initialisieren
    magic = MagicSystem()
    player = MockPlayer()
    
    print(f"Spieler zu Beginn: {player}")
    
    # Test 1: Element hinzufügen
    print("\n--- Test 1: Element hinzufügen ---")
    success1 = magic.add_element(ElementType.FEUER)
    success2 = magic.add_element(ElementType.WASSER)
    
    print(f"Feuer hinzugefügt: {success1}")
    print(f"Wasser hinzugefügt: {success2}")
    print(f"Ausgewählte Elemente: {magic.get_selected_elements_str()}")
    
    # Test 2: Heilungstrank wirken
    print("\n--- Test 2: Heilungstrank wirken ---")
    print(f"Vor Heilung: {player}")
    
    result = magic.cast_magic(caster=player, target_pos=None, enemies=[])
    
    print(f"Magie-Ergebnis: {result}")
    print(f"Nach Heilung: {player}")
    
    # Test 3: Verfügbare Kombinationen anzeigen
    print("\n--- Test 3: Verfügbare Kombinationen ---")
    combinations = magic.get_available_combinations()
    for combo in combinations:
        print(f"  {combo}")

if __name__ == "__main__":
    test_magic_system()
