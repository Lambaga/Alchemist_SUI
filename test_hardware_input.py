# -*- coding: utf-8 -*-
"""
Test Script für Hardware-Steuerung - Der Alchemist
Testet das komplette Action System mit Hardware Integration
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

import pygame
import time

def test_hardware_input_system():
    """Test der Hardware Input Implementierung"""
    print("🧪 HARDWARE INPUT SYSTEM TEST")
    print("=" * 50)
    
    # Initialize pygame
    pygame.init()
    
    try:
        # Import Action System
        from systems.action_system import init_action_system, ActionType
        from systems.hardware_input_adapter import create_hardware_input_adapter
        from systems.input_system import init_universal_input
        
        print("✅ Alle Imports erfolgreich")
        
        # Initialize Action System
        action_system = init_action_system()
        action_system.debug_enabled = True
        
        # Initialize Universal Input System  
        input_system = init_universal_input(use_action_system=True)
        
        # Create Hardware Input Adapter (Mock Mode)
        print("\n🔌 Hardware Input Adapter erstellen...")
        hardware_adapter = create_hardware_input_adapter(mock_mode=True)
        
        if not hardware_adapter:
            print("❌ Hardware Adapter konnte nicht erstellt werden")
            return False
        
        print("✅ Hardware Adapter erfolgreich erstellt")
        
        # Test 1: Button Tests
        print("\n🔘 Test 1: Hardware Buttons")
        print("-" * 30)
        
        hardware_adapter.test_all_buttons()
        time.sleep(1)
        
        # Test 2: Joystick Tests  
        print("\n🕹️ Test 2: Hardware Joystick")
        print("-" * 30)
        
        hardware_adapter.test_joystick()
        time.sleep(1)
        
        # Test 3: Action System Status
        print("\n🎯 Test 3: Action System Status")
        print("-" * 30)
        
        action_system.print_debug_info()
        
        # Test 4: Individual Hardware Button Simulation
        print("\n🧪 Test 4: Einzelne Button Tests")
        print("-" * 30)
        
        buttons = [
            ("FIRE", "Feuer-Element hinzufügen"),
            ("WATER", "Wasser-Element hinzufügen"), 
            ("STONE", "Stein-Element hinzufügen"),
            ("CAST", "Zauber wirken"),
            ("CLEAR", "Elemente löschen")
        ]
        
        for button_id, description in buttons:
            print("  Button {}: {}".format(button_id, description))
            hardware_adapter.hardware.simulate_button_press(button_id)
            time.sleep(0.3)
        
        # Test 5: Joystick Movement Simulation
        print("\n🕹️ Test 5: Joystick Bewegung")
        print("-" * 30)
        
        movements = [
            (0.0, -1.0, "OBEN"),
            (1.0, 0.0, "RECHTS"),
            (0.0, 1.0, "UNTEN"), 
            (-1.0, 0.0, "LINKS"),
            (0.0, 0.0, "ZENTRUM")
        ]
        
        for x, y, direction in movements:
            print("  Joystick {}: ({}, {})".format(direction, x, y))
            hardware_adapter.hardware.simulate_joystick_move(x, y)
            time.sleep(0.3)
        
        print("\n✅ Alle Hardware Tests erfolgreich abgeschlossen!")
        return True
        
    except ImportError as e:
        print(f"❌ Import-Fehler: {e}")
        return False
    except Exception as e:
        print(f"❌ Fehler beim Test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_action_system_integration():
    """Test der Action System Integration mit Magic System"""
    print("\n🧙‍♂️ MAGIC SYSTEM INTEGRATION TEST")
    print("=" * 50)
    
    try:
        from systems.action_system import get_action_system, ActionType, MagicSystemAdapter
        
        action_system = get_action_system()
        
        # Mock Level für Magic System Adapter
        class MockLevel:
            def __init__(self):
                self.main_game = MockMainGame()
                
            def handle_cast_magic(self):
                print("handle_cast_magic() aufgerufen")
                
        class MockMainGame:
            def __init__(self):
                self.element_mixer = MockElementMixer()
                
        class MockElementMixer:
            def handle_element_press(self, element):
                print("Element hinzugefuegt: {}".format(element))
                return True
                
            def reset_combination(self):
                print("Elemente zurueckgesetzt")
                return True
        
        # Magic System Adapter erstellen
        mock_level = MockLevel()
        magic_adapter = MagicSystemAdapter(mock_level)
        action_system.set_magic_handler(magic_adapter)
        
        # Magic Actions testen
        print("\n🧪 Magic Actions testen...")
        magic_actions = [
            (ActionType.MAGIC_FIRE, "Feuer hinzufügen"),
            (ActionType.MAGIC_WATER, "Wasser hinzufügen"),
            (ActionType.MAGIC_STONE, "Stein hinzufügen"),
            (ActionType.CAST_MAGIC, "Zauber wirken"),
            (ActionType.CLEAR_MAGIC, "Elemente löschen")
        ]
        
        for action, description in magic_actions:
            print("  Action: {}".format(description))
            action_system.handle_magic_action(action, True, "test")
            time.sleep(0.2)
        
        print("\n✅ Magic System Integration Test erfolgreich!")
        return True
        
    except Exception as e:
        print(f"❌ Magic Integration Test Fehler: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_input_priority_system():
    """Test des Input Priority Systems"""
    print("\n🎯 INPUT PRIORITY SYSTEM TEST")
    print("=" * 50)
    
    try:
        from systems.action_system import get_action_system, ActionType
        
        action_system = get_action_system()
        action_system.debug_enabled = True
        
        # Test unterschiedliche Input-Quellen für gleiche Action
        print("\n📱 Priority Test: MAGIC_FIRE von verschiedenen Quellen")
        
        # Keyboard input zuerst
        action_system.dispatch_action(ActionType.MAGIC_FIRE, True, "keyboard")
        
        # Gamepad sollte Keyboard überschreiben
        action_system.dispatch_action(ActionType.MAGIC_FIRE, True, "gamepad") 
        
        # Hardware sollte Gamepad überschreiben
        action_system.dispatch_action(ActionType.MAGIC_FIRE, True, "hardware")
        
        # Keyboard sollte ignoriert werden (niedrigere Priorität)
        action_system.dispatch_action(ActionType.MAGIC_FIRE, True, "keyboard")
        
        time.sleep(0.5)
        
        # Status ausgeben
        action_system.print_debug_info()
        
        print("\n✅ Priority System Test erfolgreich!")
        return True
        
    except Exception as e:
        print(f"❌ Priority Test Fehler: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Haupttest-Funktion"""
    print("🧙‍♂️ DER ALCHEMIST - HARDWARE INPUT SYSTEM TEST")
    print("=" * 60)
    
    results = []
    
    # Test 1: Hardware Input System
    results.append(("Hardware Input System", test_hardware_input_system()))
    
    # Test 2: Action System Integration
    results.append(("Action System Integration", test_action_system_integration()))
    
    # Test 3: Input Priority System
    results.append(("Input Priority System", test_input_priority_system()))
    
    # Ergebnisse zusammenfassen
    print("\n📊 TEST ERGEBNISSE")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ BESTANDEN" if passed else "❌ FEHLGESCHLAGEN"
        print(f"{test_name:<30} {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALLE TESTS BESTANDEN!")
        print("✅ Hardware-Steuerung ist bereit für den Einsatz!")
        
        print("\n📋 NÄCHSTE SCHRITTE:")
        print("1. ESP32 Hardware anschließen und firmware flashen")
        print("2. Mock-Mode in config.py auf False setzen") 
        print("3. Seriellen Port in config.py anpassen")
        print("4. Spiel mit ./run_game.sh starten")
        print("5. Hardware-Buttons testen!")
        
    else:
        print("❌ EINIGE TESTS FEHLGESCHLAGEN!")
        print("🔧 Bitte Fehler beheben vor Hardware-Integration")
    
    # Cleanup
    pygame.quit()
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
