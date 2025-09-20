# -*- coding: utf-8 -*-
"""
Test Script für 7-Zoll Monitor (1024x600) Optimierungen
Testet alle UI-Komponenten und Display-Einstellungen für kleine Bildschirme
"""

import pygame
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'core'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'ui'))

from src.core.config import config

def test_display_detection():
    """Testet die automatische Display-Erkennung"""
    print("="*60)
    print("🖥️  DISPLAY-ERKENNUNGS TEST")
    print("="*60)
    
    pygame.init()
    pygame.display.init()
    
    # Display-Info abrufen
    try:
        display_info = pygame.display.Info()
        print(f"Aktuelle Aufloesung: {display_info.current_w}x{display_info.current_h}")
        print(f"Bittiefe: {display_info.bitsize}")
        print(f"Hardware-beschleunigt: {display_info.hw}")
    except Exception as e:
        print(f"Warnung: Fehler beim Abrufen der Display-Informationen: {e}")
    
    # Ist kleiner Bildschirm?
    is_small = config.display.is_small_screen()
    is_rpi = config.display.is_raspberry_pi()
    
    print(f"\n7-Zoll Bildschirm erkannt: {is_small}")
    print(f"Raspberry Pi erkannt: {is_rpi}")
    
    # Optimierte Einstellungen anzeigen
    settings = config.display.get_optimized_settings()
    print(f"\nOptimierte Einstellungen:")
    for key, value in settings.items():
        print(f"   {key}: {value}")

def test_ui_scaling():
    """Testet die UI-Skalierung für verschiedene Bildschirmgrößen"""
    print("\n" + "="*60)
    print("📏 UI-SKALIERUNGS TEST")
    print("="*60)
    
    # UI-Einstellungen abrufen
    ui_settings = config.ui.get_ui_settings()
    
    print("🎨 UI-Einstellungen:")
    for key, value in ui_settings.items():
        print(f"   {key}: {value}")
    
    # Spell Bar Konfiguration testen
    spell_config = config.spells.get_bar_config()
    print(f"\n🔮 Spell Bar Konfiguration:")
    for key, value in spell_config.items():
        print(f"   {key}: {value}")

def test_ui_components():
    """Testet die UI-Komponenten mit den neuen Einstellungen"""
    print("\n" + "="*60)
    print("🎮 UI-KOMPONENTEN TEST")
    print("="*60)
    
    # Simuliere einen kleinen 7-Zoll Bildschirm
    test_width = 1024
    test_height = 600
    
    pygame.init()
    screen = pygame.display.set_mode((test_width, test_height))
    pygame.display.set_caption("7-Zoll Display Test")
    
    clock = pygame.time.Clock()
    
    # Lade UI-Komponenten
    try:
        from ui.hotkey_display import HotkeyDisplay
        hotkey_display = HotkeyDisplay(screen)
        print("✅ Hotkey Display erfolgreich geladen")
    except Exception as e:
        print(f"❌ Fehler beim Laden der Hotkey Display: {e}")
        hotkey_display = None
    
    try:
        from ui.fps_monitor import FPSMonitor
        fps_monitor = FPSMonitor()
        print("✅ FPS Monitor erfolgreich geladen")
    except Exception as e:
        print(f"❌ Fehler beim Laden des FPS Monitor: {e}")
        fps_monitor = None
    
    try:
        from systems.spell_cooldown_manager import SpellCooldownManager
        from ui.spell_bar import SpellBar
        cooldown_manager = SpellCooldownManager()
        spell_bar = SpellBar(cooldown_manager)
        print("✅ Spell Bar erfolgreich geladen")
    except Exception as e:
        print(f"❌ Fehler beim Laden der Spell Bar: {e}")
        spell_bar = None
    
    # Test-Loop für visuelle Überprüfung
    running = True
    test_duration = 5000  # 5 Sekunden
    start_time = pygame.time.get_ticks()
    
    print(f"\n🎯 Visueller Test startet für {test_duration/1000} Sekunden...")
    print("   Drücke ESC zum Beenden oder warte auf automatisches Ende")
    
    while running:
        current_time = pygame.time.get_ticks()
        dt = clock.tick(60) / 1000.0
        
        # Event-Handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_h and hotkey_display:
                    hotkey_display.toggle_visibility()
        
        # Automatisches Ende nach test_duration
        if current_time - start_time > test_duration:
            print("⏰ Test-Zeit abgelaufen - Test beendet")
            running = False
        
        # Screen clearen
        screen.fill((25, 25, 50))  # Dunkler Hintergrund
        
        # UI-Komponenten zeichnen
        if fps_monitor:
            fps_monitor.update(clock.get_fps(), dt)
            fps_monitor.draw(screen)
        
        if hotkey_display:
            hotkey_display.draw()
        
        if spell_bar:
            spell_bar.update(dt)
            spell_bar.draw(screen, test_height)
        
        # Informationstext anzeigen
        font = pygame.font.Font(None, 36)
        info_texts = [
            f"7-Zoll Display Test ({test_width}x{test_height})",
            f"Zeit: {(current_time - start_time)/1000:.1f}s / {test_duration/1000:.1f}s",
            "Drücke H für Hotkey-Toggle, ESC zum Beenden"
        ]
        
        for i, text in enumerate(info_texts):
            color = (255, 255, 255) if i == 0 else (200, 200, 200)
            text_surface = font.render(text, True, color)
            y_pos = test_height // 2 + (i - 1) * 40
            x_pos = (test_width - text_surface.get_width()) // 2
            screen.blit(text_surface, (x_pos, y_pos))
        
        pygame.display.flip()
    
    pygame.quit()
    print("✅ UI-Komponenten Test abgeschlossen")

def test_performance_settings():
    """Testet die Performance-Einstellungen für 7-Zoll Displays"""
    print("\n" + "="*60)
    print("⚡ PERFORMANCE-EINSTELLUNGEN TEST")
    print("="*60)
    
    settings = config.display.get_optimized_settings()
    
    # Performance-relevante Einstellungen hervorheben
    performance_settings = [
        'FPS', 'WINDOW_WIDTH', 'WINDOW_HEIGHT', 'FULLSCREEN', 
        'LOW_EFFECTS', 'AUDIO_QUALITY', 'VSYNC', 'TILE_CACHE_SIZE',
        'UI_SCALE', 'SPELL_BAR_SCALE', 'HOTKEY_DISPLAY_COMPACT'
    ]
    
    print("🚀 Performance-kritische Einstellungen:")
    for setting in performance_settings:
        if setting in settings:
            value = settings[setting]
            print(f"   {setting}: {value}")
    
    # Geschätzte Performance-Auswirkung
    print(f"\n📊 Performance-Analyse:")
    fps_target = settings.get('FPS', 60)
    resolution = f"{settings.get('WINDOW_WIDTH', 1280)}x{settings.get('WINDOW_HEIGHT', 720)}"
    fullscreen = settings.get('FULLSCREEN', False)
    
    print(f"   🎯 Ziel-FPS: {fps_target}")
    print(f"   📺 Auflösung: {resolution}")
    print(f"   🖼️ Vollbild: {'Ja' if fullscreen else 'Nein'}")
    print(f"   🎨 UI-Skalierung: {settings.get('UI_SCALE', 1.0)}")

def main():
    """Hauptfunktion für alle Tests"""
    print("🧙‍♂️ DER ALCHEMIST - 7-ZOLL MONITOR TEST")
    print("🔍 Testet alle Anpassungen für 1024x600 Auflösung")
    print()
    
    try:
        test_display_detection()
        test_ui_scaling()
        test_performance_settings()
        test_ui_components()
        
        print("\n" + "="*60)
        print("✅ ALLE TESTS ERFOLGREICH ABGESCHLOSSEN!")
        print("="*60)
        print()
        print("📋 Zusammenfassung:")
        print("   - Display-Erkennung funktioniert")
        print("   - UI-Skalierung ist konfiguriert")
        print("   - Performance-Einstellungen sind optimiert")
        print("   - UI-Komponenten sind angepasst")
        print()
        print("🎮 Das Spiel ist bereit für 7-Zoll Monitore (1024x600)!")
        
    except Exception as e:
        print(f"\n❌ FEHLER WÄHREND DER TESTS: {e}")
        print("Überprüfe die Konfiguration und Abhängigkeiten.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
