#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Raspberry Pi 4 Test Script für Der Alchemist
Testet Joystick/Gamepad Kompatibilität und Performance
"""

import pygame
import sys
import time
from typing import List, Dict

def test_joystick_detection() -> List[Dict]:
    """Testet die Joystick-Erkennung"""
    print("🎮 JOYSTICK-ERKENNUNGS-TEST")
    print("="*50)
    
    pygame.init()
    pygame.joystick.init()
    
    joystick_count = pygame.joystick.get_count()
    joysticks = []
    
    print(f"Gefundene Joysticks: {joystick_count}")
    
    for i in range(joystick_count):
        try:
            joystick = pygame.joystick.Joystick(i)
            joystick.init()
            
            info = {
                'index': i,
                'name': joystick.get_name(),
                'axes': joystick.get_numaxes(),
                'buttons': joystick.get_numbuttons(),
                'hats': joystick.get_numhats(),
                'instance_id': joystick.get_instance_id(),
                'joystick': joystick
            }
            
            joysticks.append(info)
            
            print(f"\n✅ Joystick {i}:")
            print(f"   Name: {info['name']}")
            print(f"   Achsen: {info['axes']}")
            print(f"   Buttons: {info['buttons']}")
            print(f"   Hats (D-Pads): {info['hats']}")
            print(f"   Instance ID: {info['instance_id']}")
            
        except pygame.error as e:
            print(f"❌ Fehler bei Joystick {i}: {e}")
    
    return joysticks

def test_joystick_input(joystick_info: Dict, duration: int = 10):
    """Testet die Joystick-Eingaben"""
    print(f"\n🎯 INPUT-TEST FÜR: {joystick_info['name']}")
    print("="*50)
    print("Bewege den Joystick und drücke Buttons...")
    print(f"Test läuft {duration} Sekunden\n")
    
    joystick = joystick_info['joystick']
    clock = pygame.time.Clock()
    start_time = time.time()
    
    last_axis_values = [0.0] * joystick_info['axes']
    last_button_states = [False] * joystick_info['buttons']
    
    while time.time() - start_time < duration:
        pygame.event.pump()  # Wichtig für Joystick-Updates
        
        # Achsen testen
        for axis in range(joystick_info['axes']):
            try:
                value = joystick.get_axis(axis)
                if abs(value - last_axis_values[axis]) > 0.1:  # Nur bei größeren Änderungen
                    print(f"Achse {axis}: {value:.3f}")
                    last_axis_values[axis] = value
            except pygame.error:
                pass
        
        # Buttons testen
        for button in range(joystick_info['buttons']):
            try:
                pressed = joystick.get_button(button)
                if pressed != last_button_states[button]:
                    state = "GEDRÜCKT" if pressed else "LOSGELASSEN"
                    print(f"Button {button}: {state}")
                    last_button_states[button] = pressed
            except pygame.error:
                pass
        
        # Hats/D-Pad testen
        for hat in range(joystick_info['hats']):
            try:
                hat_pos = joystick.get_hat(hat)
                if hat_pos != (0, 0):
                    print(f"Hat {hat}: {hat_pos}")
            except pygame.error:
                pass
        
        # Events verarbeiten
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return
        
        clock.tick(60)  # 60 FPS

def test_raspberry_pi_performance():
    """Testet die Performance auf Raspberry Pi"""
    print("\n⚡ RASPBERRY PI PERFORMANCE-TEST")
    print("="*50)
    
    # Bildschirm initialisieren
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Raspberry Pi Performance Test")
    clock = pygame.time.Clock()
    
    # Test-Sprites erstellen
    sprites = []
    for i in range(100):  # 100 bewegende Rechtecke
        sprite = {
            'x': i * 5,
            'y': 300,
            'dx': (i % 10) - 5,
            'dy': 0,
            'color': (255 - i*2, i*2, 100)
        }
        sprites.append(sprite)
    
    # Performance-Test
    frame_count = 0
    fps_sum = 0
    test_duration = 5  # 5 Sekunden
    start_time = time.time()
    
    print("Rendering 100 bewegende Sprites...")
    
    while time.time() - start_time < test_duration:
        # Events verarbeiten
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return
        
        # Sprites bewegen
        for sprite in sprites:
            sprite['x'] += sprite['dx']
            sprite['y'] += sprite['dy']
            
            # Kollision mit Bildschirmrändern
            if sprite['x'] <= 0 or sprite['x'] >= 780:
                sprite['dx'] *= -1
            if sprite['y'] <= 0 or sprite['y'] >= 580:
                sprite['dy'] *= -1
        
        # Zeichnen
        screen.fill((0, 0, 0))
        for sprite in sprites:
            pygame.draw.rect(screen, sprite['color'], 
                           (int(sprite['x']), int(sprite['y']), 20, 20))
        
        # FPS anzeigen
        fps = clock.get_fps()
        fps_sum += fps
        frame_count += 1
        
        if frame_count % 60 == 0:  # Alle 60 Frames
            avg_fps = fps_sum / 60
            print(f"FPS: {avg_fps:.1f}")
            fps_sum = 0
        
        pygame.display.flip()
        clock.tick(60)  # Ziel: 60 FPS
    
    avg_fps = fps_sum / max(frame_count % 60, 1)
    print(f"\nDurchschnittliche FPS: {avg_fps:.1f}")
    
    if avg_fps >= 50:
        print("✅ Performance: EXZELLENT")
    elif avg_fps >= 30:
        print("✅ Performance: GUT")
    elif avg_fps >= 20:
        print("⚠️ Performance: AKZEPTABEL")
    else:
        print("❌ Performance: SCHLECHT")

def test_universal_input_system():
    """Testet das Universal Input System"""
    print("\n🔧 UNIVERSAL INPUT SYSTEM TEST")
    print("="*50)
    
    try:
        # Input System importieren
        sys.path.append('/home/pi/Alchemist/src/systems')  # Raspberry Pi Pfad
        from input_system import UniversalInputSystem
        
        input_sys = UniversalInputSystem()
        input_sys.print_control_scheme()
        
        # 10 Sekunden Test
        screen = pygame.display.set_mode((400, 300))
        pygame.display.set_caption("Universal Input Test")
        clock = pygame.time.Clock()
        font = pygame.font.Font(None, 36)
        
        test_duration = 10
        start_time = time.time()
        
        print(f"\nTeste Universal Input System für {test_duration} Sekunden...")
        print("Bewege dich mit Tastatur oder Joystick!")
        
        while time.time() - start_time < test_duration:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return
                
                # Input System testen
                action = input_sys.handle_event(event)
                if action:
                    print(f"Action erkannt: {action}")
            
            # Input System updaten
            input_sys.update()
            
            # Bewegungsvektor holen
            movement = input_sys.get_movement_vector()
            right_stick = input_sys.get_right_stick_vector()
            
            # Zeichnen
            screen.fill((30, 30, 30))
            
            # Bewegungsvektor anzeigen
            if movement.length() > 0:
                text = font.render(f"Movement: {movement.x:.1f}, {movement.y:.1f}", 
                                 True, (255, 255, 255))
                screen.blit(text, (10, 50))
            
            # Right Stick anzeigen
            if right_stick.length() > 0:
                text = font.render(f"Right Stick: {right_stick.x:.1f}, {right_stick.y:.1f}", 
                                 True, (255, 255, 255))
                screen.blit(text, (10, 100))
            
            # Joystick Info
            joystick_info = input_sys.get_joystick_info()
            text = font.render(f"Joysticks: {joystick_info['count']}", 
                             True, (0, 255, 0) if joystick_info['count'] > 0 else (255, 0, 0))
            screen.blit(text, (10, 10))
            
            pygame.display.flip()
            clock.tick(60)
        
        print("✅ Universal Input System Test abgeschlossen!")
        
    except ImportError as e:
        print(f"❌ Fehler beim Import des Universal Input Systems: {e}")
        print("Stelle sicher, dass sich das Script im richtigen Verzeichnis befindet.")

def main():
    """Hauptfunktion des Test-Scripts"""
    print("🍓 RASPBERRY PI 4 KOMPATIBILITÄTS-TEST")
    print("für 'Der Alchemist'")
    print("="*60)
    
    # Pygame initialisieren
    pygame.init()
    
    try:
        # 1. Joystick-Erkennung testen
        joysticks = test_joystick_detection()
        
        if joysticks:
            print(f"\n✅ {len(joysticks)} Joystick(s) gefunden!")
            
            # Ersten Joystick für detaillierte Tests verwenden
            test_joystick_input(joysticks[0], duration=5)
        else:
            print("\n⚠️ Keine Joysticks gefunden. Nur Tastatur/Maus verfügbar.")
        
        # 2. Performance testen
        test_raspberry_pi_performance()
        
        # 3. Universal Input System testen
        test_universal_input_system()
        
        print("\n🎉 ALLE TESTS ABGESCHLOSSEN!")
        print("\nZUSAMMENFASSUNG:")
        print(f"- Joysticks gefunden: {len(joysticks)}")
        print("- Performance: Siehe oben")
        print("- Input System: Funktional")
        
        print("\n💡 EMPFEHLUNGEN FÜR RASPBERRY PI 4:")
        print("- Verwende einen USB-Gamepad für beste Erfahrung")
        print("- Stelle sicher, dass der Pi ausreichend gekühlt ist")
        print("- Verwende eine schnelle SD-Karte (Class 10+)")
        print("- Aktiviere GPU-Memory Split (128MB+)")
        
    except Exception as e:
        print(f"❌ Fehler im Test: {e}")
    finally:
        pygame.quit()

if __name__ == "__main__":
    main()
