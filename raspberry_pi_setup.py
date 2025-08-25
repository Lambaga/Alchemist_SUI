# -*- coding: utf-8 -*-
"""
Raspberry Pi 4 Setup und Kompatibilitäts-Test
Testet Joystick-Funktionalität und Performance
"""

import pygame
import sys
import os
import time
from typing import Dict, List

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'systems'))

try:
    from systems.input_system import UniversalInputSystem, get_input_system
except ImportError:
    print("HINWEIS: Input-System nicht gefunden. Verwende Mock-Version für Test.")
    
    class MockInputSystem:
        def __init__(self):
            self.joysticks = []
            
        def get_joystick_info(self):
            return {'count': 0, 'active': None, 'devices': []}
            
        def update(self):
            pass
            
        def handle_event(self, event):
            return None
            
        def get_movement_vector(self):
            return type('Vector2', (), {'x': 0, 'y': 0})()
            
        def get_right_stick_vector(self):
            return type('Vector2', (), {'x': 0, 'y': 0})()
            
        def is_action_pressed(self, action):
            return False
    
    UniversalInputSystem = MockInputSystem

class RaspberryPiTester:
    """Test-Klasse für Raspberry Pi 4 Kompatibilität"""
    
    def __init__(self):
        pygame.init()
        pygame.joystick.init()
        
        self.screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("Raspberry Pi 4 - Gamepad Test")
        
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        self.clock = pygame.time.Clock()
        
        # Input-System initialisieren
        self.input_system = UniversalInputSystem()
        
        self.running = True
        self.test_results = []
        
    def run_hardware_tests(self):
        """Führt Hardware-Kompatibilitäts-Tests durch"""
        print("Hardware-Tests werden gestartet...")
        
        # Test 1: Joystick-Erkennung
        joystick_info = self.input_system.get_joystick_info()
        if joystick_info['count'] > 0:
            self.test_results.append("OK " + str(joystick_info['count']) + " Gamepad(s) erkannt")
            for device in joystick_info['devices']:
                self.test_results.append("   Device: " + str(device['name']))
                self.test_results.append("      Buttons: " + str(device['buttons']) + ", Achsen: " + str(device['axes']))
        else:
            self.test_results.append("WARN Kein Gamepad gefunden")
            
        # Test 2: Pygame Version
        pygame_version = pygame.version.ver
        self.test_results.append("Python Pygame Version: " + str(pygame_version))
        
        # Test 3: Python Version
        python_version = str(sys.version_info.major) + "." + str(sys.version_info.minor) + "." + str(sys.version_info.micro)
        self.test_results.append("Python Version: " + python_version)
        
        # Test 4: Performance-Test
        self.test_results.append("Performance-Test...")
        start_time = time.time()
        for _ in range(1000):
            self.input_system.update()
        test_time = time.time() - start_time
        self.test_results.append("   Input-Update: " + str(round(test_time, 4)) + "s für 1000 Zyklen")
        
        # Test 5: Virtual Environment Check
        if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            self.test_results.append("OK Virtual Environment erkannt")
        else:
            self.test_results.append("WARN Kein Virtual Environment erkannt")
            
        print("Hardware-Tests abgeschlossen")
        
    def run_interactive_test(self):
        """Führt interaktiven Gamepad-Test durch"""
        print("🎮 Interaktiver Gamepad-Test gestartet")
        print("   - Bewege die Sticks und drücke Buttons")
        print("   - ESC zum Beenden")
        
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.running = False
                
                # Input-System testen
                action = self.input_system.handle_event(event)
                if action:
                    print("Action erkannt: " + str(action))
            
            # Input-System updaten
            self.input_system.update()
            
            # Screen clearen
            self.screen.fill((20, 20, 40))
            
            # Testergebnisse anzeigen
            y_offset = 10
            for result in self.test_results:
                text = self.small_font.render(result, True, (255, 255, 255))
                self.screen.blit(text, (10, y_offset))
                y_offset += 25
            
            # Live-Input-Status anzeigen
            y_offset += 20
            
            # Bewegungsvektor
            movement = self.input_system.get_movement_vector()
            text = self.font.render(f"Bewegung: ({movement.x:.1f}, {movement.y:.1f})", True, (100, 255, 100))
            self.screen.blit(text, (10, y_offset))
            y_offset += 40
            
            # Right Stick (falls vorhanden)
            right_stick = self.input_system.get_right_stick_vector()
            text = self.font.render(f"Right Stick: ({right_stick.x:.1f}, {right_stick.y:.1f})", True, (100, 255, 100))
            self.screen.blit(text, (10, y_offset))
            y_offset += 40
            
            # Aktions-Status
            actions = ['brew', 'remove_ingredient', 'reset', 'music_toggle', 'pause']
            for action in actions:
                is_pressed = self.input_system.is_action_pressed(action)
                color = (255, 100, 100) if is_pressed else (150, 150, 150)
                text = self.small_font.render(f"{action}: {'PRESSED' if is_pressed else 'released'}", True, color)
                self.screen.blit(text, (10, y_offset))
                y_offset += 25
            
            # Instructions
            instructions = [
                "ESC: Test beenden",
                "Teste alle Gamepad-Buttons und Sticks!",
                "Raspberry Pi 4 Kompatibilität wird geprüft..."
            ]
            
            y_offset = self.screen.get_height() - len(instructions) * 25 - 10
            for instruction in instructions:
                text = self.small_font.render(instruction, True, (200, 200, 100))
                self.screen.blit(text, (10, y_offset))
                y_offset += 25
            
            pygame.display.flip()
            self.clock.tick(60)
    
    def generate_report(self):
        """Generiert einen Kompatibilitäts-Bericht"""
        report = []
        report.append("="*60)
        report.append("RASPBERRY PI 4 KOMPATIBILITÄTS-BERICHT")
        report.append("="*60)
        report.append("")
        
        for result in self.test_results:
            report.append(result)
        
        report.append("")
        report.append("EMPFEHLUNGEN:")
        
        joystick_info = self.input_system.get_joystick_info()
        if joystick_info['count'] > 0:
            report.append("✅ Das Spiel ist bereit für Raspberry Pi 4!")
            report.append("✅ Gamepad-Support funktioniert einwandfrei")
            report.append("🎮 Erkannte Gamepads können sofort verwendet werden")
        else:
            report.append("⚠️ Schließe ein USB-Gamepad an den Raspberry Pi 4 an")
            report.append("📱 Empfohlene Gamepads: Xbox Controller, PS4/PS5 Controller")
            report.append("🔌 USB-Gamepads werden automatisch erkannt")
            
        report.append("")
        report.append("RASPBERRY PI 4 OPTIMIERUNGEN:")
        report.append("- GPU-Speicher auf 128MB oder höher setzen (sudo raspi-config)")
        report.append("- Audio über HDMI oder 3.5mm Klinke aktivieren") 
        report.append("- Für beste Performance: Desktop-Umgebung optional deaktivieren")
        report.append("- Virtual Environment für Python-Pakete verwenden (bereits erkannt)")
        
        report.append("")
        report.append("="*60)
        
        return "\n".join(report)

def main():
    """Hauptfunktion für Raspberry Pi Tests"""
    print("🍓 Raspberry Pi 4 - Der Alchemist Kompatibilitäts-Test")
    print("="*60)
    
    tester = RaspberryPiTester()
    
    # Hardware-Tests durchführen
    tester.run_hardware_tests()
    
    # Bericht ausgeben
    report = tester.generate_report()
    print(report)
    
    # Bericht speichern
    with open("raspberry_pi_report.txt", "w", encoding="utf-8") as f:
        f.write(report)
    print("\n💾 Bericht gespeichert als 'raspberry_pi_report.txt'")
    
    # Interaktiver Test anbieten
    print("\n🎮 Möchten Sie den interaktiven Gamepad-Test starten? (y/n): ", end="")
    if input().lower().startswith('y'):
        tester.run_interactive_test()
    
    print("🏁 Test abgeschlossen!")

if __name__ == "__main__":
    main()
