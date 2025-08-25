# -*- coding: utf-8 -*-
"""
Einfacher Raspberry Pi 4 Kompatibilitäts-Test
Ohne GUI - nur Konsolen-Output
"""

import pygame
import sys
import os
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'systems'))

def test_pygame_init():
    """Test Pygame Initialisierung"""
    try:
        pygame.init()
        pygame.joystick.init()
        print("✅ Pygame erfolgreich initialisiert")
        return True
    except Exception as e:
        print("❌ Pygame Initialisierung fehlgeschlagen: " + str(e))
        return False

def test_input_system():
    """Test Input-System Import"""
    try:
        from input_system import UniversalInputSystem
        input_system = UniversalInputSystem()
        print("✅ Input-System erfolgreich importiert und initialisiert")
        return input_system
    except Exception as e:
        print("❌ Input-System Import fehlgeschlagen: " + str(e))
        return None

def test_joystick_detection():
    """Test Joystick-Erkennung"""
    pygame.joystick.init()
    joystick_count = pygame.joystick.get_count()
    
    print("🎮 Erkannte Joysticks: " + str(joystick_count))
    
    for i in range(joystick_count):
        try:
            joystick = pygame.joystick.Joystick(i)
            joystick.init()
            print("   Joystick " + str(i) + ": " + joystick.get_name())
            print("      Achsen: " + str(joystick.get_numaxes()))
            print("      Buttons: " + str(joystick.get_numbuttons()))
            print("      Hats: " + str(joystick.get_numhats()))
        except Exception as e:
            print("   ❌ Fehler bei Joystick " + str(i) + ": " + str(e))
    
    return joystick_count > 0

def test_system_info():
    """System-Informationen sammeln"""
    print("🐍 Python Version: " + sys.version)
    print("🎮 Pygame Version: " + pygame.version.ver)
    print("💻 Platform: " + sys.platform)
    
    # Virtual Environment Check
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Virtual Environment erkannt")
    else:
        print("⚠️ Kein Virtual Environment erkannt")

def performance_test(input_system):
    """Performance-Test"""
    if not input_system:
        print("⚠️ Performance-Test übersprungen (Input-System nicht verfügbar)")
        return
    
    print("🚀 Performance-Test wird ausgeführt...")
    start_time = time.time()
    for _ in range(1000):
        input_system.update()
    test_time = time.time() - start_time
    print("   Input-Update: " + "{:.4f}".format(test_time) + "s für 1000 Zyklen")
    
    if test_time < 0.1:
        print("✅ Performance: Ausgezeichnet")
    elif test_time < 0.5:
        print("✅ Performance: Gut")
    else:
        print("⚠️ Performance: Könnte besser sein")

def generate_compatibility_report(pygame_ok, input_system_ok, joystick_found):
    """Generiert Kompatibilitätsbericht"""
    print("\n" + "="*60)
    print("RASPBERRY PI 4 KOMPATIBILITÄTS-BERICHT")
    print("="*60)
    
    if pygame_ok and input_system_ok:
        print("✅ GRUNDLEGENDE KOMPATIBILITÄT: JA")
        print("✅ Das Spiel kann auf Raspberry Pi 4 ausgeführt werden")
    else:
        print("❌ GRUNDLEGENDE KOMPATIBILITÄT: PROBLEME GEFUNDEN")
        print("❌ Bitte beheben Sie die oben genannten Fehler")
        return False
    
    if joystick_found:
        print("✅ GAMEPAD-SUPPORT: VERFÜGBAR")
        print("🎮 Gamepads wurden erkannt und können verwendet werden")
    else:
        print("⚠️ GAMEPAD-SUPPORT: KEIN GAMEPAD GEFUNDEN")
        print("📱 Schließen Sie ein USB-Gamepad an für die beste Erfahrung")
    
    print("\nEMPFEHLUNGEN FÜR RASPBERRY PI 4:")
    print("- GPU-Speicher auf mindestens 128MB setzen: sudo raspi-config")
    print("- Audio konfigurieren (HDMI oder 3.5mm Klinke)")
    print("- Für beste Performance: Desktop optional deaktivieren")
    print("- Empfohlene Gamepads: Xbox Controller, PS4/PS5 Controller")
    print("- USB-Hub verwenden falls mehrere USB-Geräte angeschlossen werden")
    
    print("\n" + "="*60)
    return True

def main():
    """Hauptfunktion"""
    print("🍓 Raspberry Pi 4 - Der Alchemist Kompatibilitäts-Test")
    print("="*60)
    
    # Tests durchführen
    pygame_ok = test_pygame_init()
    input_system = test_input_system()
    input_system_ok = input_system is not None
    joystick_found = test_joystick_detection()
    
    test_system_info()
    performance_test(input_system)
    
    # Bericht generieren
    is_compatible = generate_compatibility_report(pygame_ok, input_system_ok, joystick_found)
    
    if is_compatible:
        print("\n🎉 IHR SPIEL IST RASPBERRY PI 4 KOMPATIBEL!")
        print("🚀 Sie können das Spiel jetzt auf dem Raspberry Pi 4 spielen")
    else:
        print("\n⚠️ Bitte beheben Sie die Probleme vor dem Einsatz auf Raspberry Pi 4")
    
    print("\n🏁 Test abgeschlossen!")

if __name__ == "__main__":
    main()
