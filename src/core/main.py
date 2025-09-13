# -*- coding: utf-8 -*-
"""
M# Action System Integration
try:
    from systems.action_system import init_action_system, get_action_system, MagicSystemAdapter
    from systems.hardware_input_adapter import create_hardware_input_adapter
    ACTION_SYSTEM_AVAILABLE = True
    print("✅ Action System verfügbar")
except ImportError as e:
    ACTION_SYSTEM_AVAILABLE = False
    print("⚠️ Action System nicht verfügbar: {}".format(e)) File - Enhanced with FPS Monitoring and Menu System

Hauptspiel-Datei mit erweitertem FPS-Tracking und vollständigem Menu-System.
"""

import pygame
import sys
import os

# Add src subdirectories to Python path for imports
src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, src_dir)
sys.path.insert(0, os.path.join(src_dir, 'core'))
sys.path.insert(0, os.path.join(src_dir, 'managers'))
sys.path.insert(0, os.path.join(src_dir, 'ui'))
sys.path.insert(0, os.path.join(src_dir, 'entities'))
sys.path.insert(0, os.path.join(src_dir, 'world'))
sys.path.insert(0, os.path.join(src_dir, 'systems'))

from typing import Optional
from settings import *
from level import Level
from asset_manager import AssetManager
from fps_monitor import FPSMonitor, create_detailed_fps_display
from menu_system import MenuSystem, GameState
from save_system import save_manager
from hotkey_display import HotkeyDisplay
from input_system import init_universal_input

# Action System Integration (Auskommentiert wegen Unicode-Problemen)
# try:
#     from systems.action_system import init_action_system, get_action_system, MagicSystemAdapter
#     from systems.hardware_input_adapter import create_hardware_input_adapter
#     ACTION_SYSTEM_AVAILABLE = True
# except ImportError as e:
#     ACTION_SYSTEM_AVAILABLE = False
#     print("Action System nicht verfuegbar: {}".format(e))

# Temporär deaktiviert
ACTION_SYSTEM_AVAILABLE = False

import os

class Game:
    """
    Hauptspiel-Klasse mit erweiterten Performance-Monitoring und Menu-System.
    
    Features:
    - Vollständiges Menu-System (New Game, Load Game, Settings, Credits)
    - FPS-Anzeige in Echtzeit
    - Frame-Drop Detektion
    - Performance-Metriken
    - Detaillierte Debug-Informationen
    - State Management
    """
    
    def __init__(self):
        pygame.init()
        pygame.font.init()  # Explizit font system initialisieren
        
        # 🚀 Task 4: Hardware-spezifische Audio-Initialisierung
        from config import DisplayConfig
        DisplayConfig.init_audio_for_hardware()
        
        # 🚀 Task 4: Hardware-optimierte Display-Einstellungen
        self.optimized_settings = DisplayConfig.get_optimized_settings()
        
        # Universal Input System initialisieren
        self.input_system = init_universal_input(use_action_system=ACTION_SYSTEM_AVAILABLE)
        self.input_system.print_control_scheme()
        
        # Action System initialisieren (falls verfügbar)
        self.action_system = None
        self.hardware_adapter = None
        if ACTION_SYSTEM_AVAILABLE:
            self.action_system = init_action_system()
            
            # Versuche Hardware Input Adapter zu erstellen
            try:
                from core.config import config
                hardware_config = config.input.HARDWARE_CONFIG
                self.hardware_adapter = create_hardware_input_adapter(
                    port=hardware_config['port'],
                    mock_mode=hardware_config['mock_mode']
                )
                if self.hardware_adapter:
                    print("✅ Hardware Input Adapter aktiviert")
                else:
                    print("⚠️ Hardware Input Adapter nicht verfügbar - Fallback auf Tastatur/Gamepad")
            except Exception as e:
                print("Hardware Input Adapter Fehler: {}".format(e))
                self.hardware_adapter = None
        
        # Initialize AssetManager
        self.asset_manager = AssetManager()
        
        # 🚀 Nutze optimierte Auflösung basierend auf Hardware
        window_width = self.optimized_settings['WINDOW_WIDTH']
        window_height = self.optimized_settings['WINDOW_HEIGHT']
        use_fullscreen = self.optimized_settings.get('FULLSCREEN', False)
        
        print("🚀 Display: {}x{} @ {} FPS{}".format(
            window_width, window_height, 
            self.optimized_settings['FPS'],
            " (Vollbild)" if use_fullscreen else ""
        ))
        
        # Display-Modus basierend auf Hardware-Einstellungen
        display_flags = pygame.FULLSCREEN if use_fullscreen else 0
        self.game_surface = pygame.display.set_mode((window_width, window_height), display_flags)
        pygame.display.set_caption(GAME_TITLE)
        
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Game State Management
        self.game_state = GameState.MAIN_MENU
        self.previous_state = GameState.MAIN_MENU  # For pause/resume
        self.menu_system = MenuSystem(self.game_surface)
        self.level = None
        
        # Message system for feedback
        self.message_text = ""
        self.message_timer = 0
        self.message_duration = 2000  # 2 seconds in milliseconds
        self.message_font = pygame.font.Font(None, 36)
        
        # Hotkey display system
        self.hotkey_display = HotkeyDisplay(self.game_surface)
        
        # FPS-Monitoring System
        self.fps_monitor = create_detailed_fps_display(position=(10, 10))
        self.fps_monitor.set_target_fps(FPS)
        self.show_fps = True  # Toggle für FPS-Anzeige
        
        # Performance-Tracking
        self.frame_count = 0
        self.total_time = 0.0
        
        # 🚀 Element Mixing System Integration
        from systems.spell_cooldown_manager import SpellCooldownManager
        from ui.element_mixer import ElementMixer
        self.spell_cooldown_manager = SpellCooldownManager()
        self.element_mixer = ElementMixer(self.spell_cooldown_manager)
        print("✨ Element mixing system initialized with 3 elements (Fire/Water/Stone)")
        
        # 🔌 Action System & Hardware Integration (Temporär deaktiviert)
        # if ACTION_SYSTEM_AVAILABLE:
        #     self.action_system = init_action_system()
        #     self.hardware_adapter = None
        #     
        #     # Try to initialize hardware adapter
        #     import os
        #     enable_hardware = os.environ.get('ALCHEMIST_HW', '0') == '1'
        #     
        #     if enable_hardware:
        #         print("🔌 Hardware-Modus aktiviert - versuche Hardware-Verbindung...")
        #         self.hardware_adapter = create_hardware_input_adapter(
        #             port='/dev/ttyUSB0', 
        #             mock_mode=True  # Erstmal Mock-Mode für Tests
        #         )
        #         
        #         if self.hardware_adapter:
        #             print("✅ Hardware Input Adapter erfolgreich initialisiert")
        #         else:
        #             print("⚠️ Hardware Input Adapter konnte nicht initialisiert werden - Fallback zu Standard-Input")
        #     else:
        #         print("💡 Hardware-Modus deaktiviert (ALCHEMIST_HW=1 zum Aktivieren)")
        #         
        #     self.action_system.debug_enabled = False  # Debug-Ausgaben standardmäßig aus
        # else:
        self.action_system = None
        self.hardware_adapter = None
        
        # Magic System Adapter für Action System (falls verfügbar)
        self.magic_adapter = None
        if ACTION_SYSTEM_AVAILABLE and self.action_system:
            # Magic Adapter wird erst nach Level-Erstellung gesetzt
            pass
        
        self.load_background_music()
        
        print("Game started with Menu System!")
        print("Architecture: Central Game class with Menu System and Level system")
        print(f"🎯 Target FPS: {FPS}")
        print("💡 Drücke F3 um FPS-Anzeige ein/auszuschalten")
        print("💡 Drücke F4 um zwischen einfacher/detaillierter Anzeige zu wechseln")
        print("🎮 Verwende das Menu-System zum Navigieren!")
    
    def load_background_music(self):
        """Lädt und startet die Hintergrundmusik."""
        try:
            pygame.mixer.music.load(BACKGROUND_MUSIC)
            pygame.mixer.music.set_volume(MUSIC_VOLUME)
            pygame.mixer.music.play(-1)
            print("Music started:", BACKGROUND_MUSIC)
        except Exception as e:
            print("Music error:", e)
    
    def handle_events(self):
        """Behandelt alle Pygame-Events inklusive Menu-System und FPS-Display Steuerung."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            # Pass all keyboard events to the current state
            if event.type in [pygame.KEYDOWN, pygame.KEYUP]:
                if event.type == pygame.KEYDOWN:
                    # ESC zum Beenden (nur im Gameplay)
                    if event.key == pygame.K_ESCAPE:
                        if self.game_state == GameState.GAMEPLAY:
                            self.pause_game()
                        elif self.game_state == GameState.PAUSE:
                            self.resume_game()
                        elif self.game_state == GameState.MAIN_MENU:
                            self.running = False
                    
                    # F3: FPS-Anzeige ein/ausschalten (nur im Gameplay)
                    elif event.key == pygame.K_F3 and self.game_state == GameState.GAMEPLAY:
                        self.show_fps = not self.show_fps
                        print(f"🔧 FPS-Anzeige: {'Ein' if self.show_fps else 'Aus'}")
                    
                    # F4: Detaillierte/Einfache FPS-Anzeige wechseln (nur im Gameplay)
                    elif event.key == pygame.K_F4 and self.game_state == GameState.GAMEPLAY:
                        self.fps_monitor.toggle_detailed()
                        mode = "Detailliert" if self.fps_monitor.show_detailed else "Einfach"
                        print(f"🔧 FPS-Modus: {mode}")
                    
                    # F5: FPS-Statistiken zurücksetzen (nur im Gameplay)
                    elif event.key == pygame.K_F5 and self.game_state == GameState.GAMEPLAY:
                        self.fps_monitor.reset_stats()
                        print("🔧 FPS-Statistiken zurückgesetzt")
                    
                    # F6: Performance-Zusammenfassung ausgeben (nur im Gameplay)
                    elif event.key == pygame.K_F6 and self.game_state == GameState.GAMEPLAY:
                        self._print_performance_summary()
                    
                    # H: Hotkey-Anzeige ein/ausschalten (nur im Gameplay)
                    elif event.key == pygame.K_h and self.game_state == GameState.GAMEPLAY:
                        self.hotkey_display.toggle_visibility()
                        status = "Ein" if self.hotkey_display.visible else "Aus"
                        print(f"🔧 Hotkey-Anzeige: {status}")
                    
                    # 🚀 GLOBAL MAGIC TEST HOTKEYS (F7-F8 statt F10-F12 - kein Konflikt mit Speicher-Slots!)
                    elif event.key == pygame.K_F7:  # F7 für direkten Magie-Test (war F10)
                        print("🧪 GLOBAL MAGIC TEST: F7 gedrückt!")
                        self._test_magic_system_global()
                    elif event.key == pygame.K_F8:  # F8 für Feuer + Heilung kombiniert (war F11+F12)
                        print("🔥💚 GLOBAL MAGIC: Feuer + Heilung kombiniert!")  
                        self._add_magic_element_global("fire")
                        self._cast_heal_global()
                    
                    # ✨ ELEMENT MIXING: Handle element keys 1-3 (nur im Gameplay)
                    elif self.game_state == GameState.GAMEPLAY:
                        # Element selection: 1=Water, 2=Fire, 3=Stone
                        element_handled = False
                        if event.key == pygame.K_1:
                            self.element_mixer.handle_element_press("water")
                            element_handled = True
                        elif event.key == pygame.K_2:
                            self.element_mixer.handle_element_press("fire")
                            element_handled = True
                        elif event.key == pygame.K_3:
                            self.element_mixer.handle_element_press("stone")
                            element_handled = True
                        
                        # Wenn Element-Event behandelt wurde, nicht weiterleiten
                        if element_handled:
                            continue  # Skip weitere Event-Verarbeitung
            
            # Handle events based on current game state
            if self.game_state == GameState.MAIN_MENU or self.game_state in [GameState.SETTINGS, GameState.CREDITS, GameState.LOAD_GAME, GameState.PAUSE, GameState.GAME_OVER]:
                # Menu system handles these states
                result = self.menu_system.handle_event(event)
                if result:
                    if result == GameState.GAMEPLAY:
                        self.start_new_game()
                    elif isinstance(result, tuple) and result[0] == "load_game":
                        self.load_game(result[1])
                    elif isinstance(result, tuple) and result[0] == "save_to_slot":
                        self.save_to_slot(result[1])
                    elif result == "save_game":
                        self.save_from_menu()
                    elif result == "resume":
                        self.resume_game()
                    elif result == "save":
                        self.quick_save()
                    elif result == GameState.MAIN_MENU:
                        self.return_to_menu()
                    elif result == GameState.QUIT:
                        self.running = False
                    elif result == "restart_game":
                        self.restart_current_game()
                    # Other state changes are handled by menu_system internally
            
            elif self.game_state == GameState.GAMEPLAY:
                # Skip level handling ONLY for element keys 1-3 to prevent double processing
                skip_level = False
                if (event.type == pygame.KEYDOWN and 
                    event.key in [pygame.K_1, pygame.K_2, pygame.K_3]):
                    skip_level = True
                    print(f"🚫 Skipping level handling for element key: {event.key}")
                
                # Pass events to level if in gameplay (except element keys 1-3)
                if not skip_level and self.level and hasattr(self.level, 'handle_event'):
                    self.level.handle_event(event)
    
    
    def start_new_game(self):
        """Startet ein neues Spiel"""
        print("🎮 Neues Spiel wird gestartet...")
        self.game_state = GameState.GAMEPLAY
        self.level = Level(self.game_surface, main_game=self)
        
        # Set save callback for the level
        self.level.set_save_callback(self.save_current_game)
        
        # Magic System Adapter für Action System (falls verfügbar)
        # if ACTION_SYSTEM_AVAILABLE and self.action_system and self.level:
        #     self.magic_adapter = MagicSystemAdapter(self.level)
        #     self.action_system.set_magic_handler(self.magic_adapter)
        #     print("✅ Magic System Adapter für Action System konfiguriert")
        
        print("✅ Level geladen, Spiel bereit!")
    
    def restart_current_game(self):
        """Startet das aktuelle Level neu"""
        print("🔄 Spiel wird neu gestartet...")
        if self.level:
            self.level.restart_level()
        else:
            # Fallback: Erstelle ein neues Level
            self.level = Level(self.game_surface, main_game=self)
            self.level.set_save_callback(self.save_current_game)
        
        self.game_state = GameState.GAMEPLAY
        print("✅ Spiel neu gestartet!")
    
    def load_game(self, slot_number):
        """Lädt ein gespeichertes Spiel"""
        print(f"📂 Lade Spielstand aus Slot {slot_number}...")
        
        # Load save data
        save_data = save_manager.load_game(slot_number)
        if save_data:
            # Create new level first
            self.game_state = GameState.GAMEPLAY
            self.level = Level(self.game_surface, main_game=self)
            
            # Set save callback for the level
            self.level.set_save_callback(self.save_current_game)
            
            # Magic System Adapter für Action System (falls verfügbar)
            # if ACTION_SYSTEM_AVAILABLE and self.action_system and self.level:
            #     self.magic_adapter = MagicSystemAdapter(self.level)
            #     self.action_system.set_magic_handler(self.magic_adapter)
            #     print("✅ Magic System Adapter für Action System konfiguriert")
            
            # Apply save data to game logic
            if save_manager.apply_save_data(self.level.game_logic, save_data):
                print("✅ Spielstand erfolgreich geladen!")
            else:
                print("⚠️ Spielstand geladen, aber einige Daten konnten nicht wiederhergestellt werden")
        else:
            print("❌ Fehler beim Laden des Spielstands")
            # Fall back to new game
            self.start_new_game()
    
    def save_current_game(self, slot_number):
        """Speichert das aktuelle Spiel"""
        if self.level and self.level.game_logic:
            save_data = save_manager.export_save_data(self.level.game_logic)
            return save_manager.save_game(slot_number, save_data)
        return False
    
    def quick_save(self):
        """Schnelles Speichern in Slot 1"""
        if self.save_current_game(1):
            print("💾 Spiel gespeichert!")
            self.show_message("💾 Schnell gespeichert (Slot 1)!")
        else:
            print("❌ Fehler beim Speichern!")
            self.show_message("❌ Speichern fehlgeschlagen!")
    
    def save_to_slot(self, slot_number: int):
        """Speichert das Spiel in einen bestimmten Slot"""
        if self.save_current_game(slot_number):
            print(f"💾 Spiel in Slot {slot_number} gespeichert!")
            self.show_message(f"💾 Gespeichert in Slot {slot_number}!")
            return True
        else:
            print(f"❌ Fehler beim Speichern in Slot {slot_number}!")
            self.show_message(f"❌ Speichern fehlgeschlagen!")
            return False
    
    def save_from_menu(self):
        """Speichert das Spiel vom Hauptmenü aus"""
        if self.level and self.level.game_logic:
            if self.save_current_game(1):  # Save to slot 1
                print("💾 Spiel vom Hauptmenü gespeichert!")
                self.menu_system.show_save_confirmation()
                return True
            else:
                print("❌ Fehler beim Speichern vom Hauptmenü!")
                return False
        else:
            print("⚠️ Kein aktives Spiel zum Speichern!")
            self.menu_system.show_no_game_message()
            return False
    
    def show_message(self, text: str):
        """Zeigt eine temporäre Nachricht an"""
        self.message_text = text
        self.message_timer = pygame.time.get_ticks()
    
    def update_message_system(self):
        """Aktualisiert das Nachrichtensystem"""
        if self.message_text and pygame.time.get_ticks() - self.message_timer > self.message_duration:
            self.message_text = ""
    
    def draw_message(self):
        """Zeichnet die aktuelle Nachricht"""
        if self.message_text:
            # Create message surface with background
            text_surface = self.message_font.render(self.message_text, True, (255, 255, 255))
            text_rect = text_surface.get_rect()
            
            # Position at top-center of screen
            padding = 20
            bg_rect = pygame.Rect(
                WINDOW_WIDTH // 2 - text_rect.width // 2 - padding,
                50,
                text_rect.width + padding * 2,
                text_rect.height + padding
            )
            
            # Draw background
            pygame.draw.rect(self.game_surface, (0, 0, 0, 180), bg_rect)
            pygame.draw.rect(self.game_surface, (100, 100, 150), bg_rect, 2)
            
            # Draw text
            text_pos = (bg_rect.x + padding, bg_rect.y + padding // 2)
            self.game_surface.blit(text_surface, text_pos)
    
    def pause_game(self):
        """Pausiert das Spiel ohne automatisches Speichern"""
        if self.game_state == GameState.GAMEPLAY:
            print("⏸️ Spiel pausiert...")
            
            # Input-Status leeren um Bug zu vermeiden
            if self.level:
                self.level.clear_input_state()
            
            self.previous_state = self.game_state
            self.game_state = GameState.PAUSE
            self.menu_system.change_state(GameState.PAUSE)
    
    def resume_game(self):
        """Setzt das Spiel fort"""
        if self.game_state == GameState.PAUSE:
            print("▶️ Spiel fortgesetzt")
            
            # Input-Status leeren um sicherzustellen, dass keine Tasten "hängen"
            if self.level:
                self.level.clear_input_state()
            
            self.game_state = self.previous_state
    
    def return_to_menu(self):
        """Kehrt zum Hauptmenü zurück"""
        print("📋 Zurück zum Hauptmenü...")
        
        # Input-Status leeren bevor wir zum Menü wechseln
        if self.level:
            self.level.clear_input_state()
        
        self.game_state = GameState.MAIN_MENU
        if self.level:
            # Clean up level resources if needed
            self.level = None
        print("✅ Im Hauptmenü")
    
    def _print_performance_summary(self):
        """Gibt eine detaillierte Performance-Zusammenfassung aus."""
        summary = self.fps_monitor.get_performance_summary()
        
        print("\n📊 PERFORMANCE SUMMARY 📊")
        print("=" * 40)
        print(f"Aktuelle FPS: {summary['current_fps']:.1f}")
        print(f"Durchschnitt: {summary['average_fps']:.1f}")
        print(f"Min/Max: {summary['min_fps']:.0f}/{summary['max_fps']:.0f}")
        print(f"Frame-Zeit: {summary['frame_time_ms']:.1f}ms")
        print(f"Frame-Drops: {summary['consecutive_drops']}")
        print(f"Bewertung: {summary['performance_rating']}")
        print(f"Gesamt-Frames: {self.frame_count}")
        print(f"Laufzeit: {self.total_time:.1f}s")
        print("=" * 40)
    
    def update(self):
        """Aktualisiert das Spiel und die Performance-Metriken."""
        # 🚀 Task 4: Hardware-optimierte FPS verwenden
        target_fps = self.optimized_settings['FPS']
        dt = self.clock.tick(target_fps) / 1000.0
        current_fps = self.clock.get_fps()
        
        # Performance-Tracking
        self.frame_count += 1
        self.total_time += dt
        
        # FPS-Monitor aktualisieren
        self.fps_monitor.update(current_fps, dt)
        
        # Hardware Input Adapter Update (non-blocking)
        if self.hardware_adapter:
            self.hardware_adapter.update()
        
        # Input System Update
        self.input_system.update()
        
        # Element Mixer Update (für Animationen)
        self.element_mixer.update(dt)
        if self.input_system:
            self.input_system.update()
        
        # Update message system
        self.update_message_system()
        
        # Update based on current game state
        if self.game_state == GameState.MAIN_MENU or self.game_state in [GameState.SETTINGS, GameState.CREDITS, GameState.LOAD_GAME, GameState.PAUSE]:
            # Update menu system
            self.menu_system.update(dt)
        elif self.game_state == GameState.GAMEPLAY:
            # Update hardware input adapter (falls verfügbar)
            if self.hardware_adapter:
                self.hardware_adapter.update()
            
            # Update gameplay level
            if self.level:
                result = self.level.update(dt)
                # Prüfe auf Game Over Signal
                if result == "game_over":
                    print("💀 GAME OVER detected - switching to Game Over menu")
                    self.game_state = GameState.GAME_OVER
                    self.menu_system.show_game_over()
            
            # ✨ Update element mixing system
            self.spell_cooldown_manager.update()
            self.element_mixer.update(dt)
        elif self.game_state == GameState.GAME_OVER:
            # Update menu system for Game Over state
            self.menu_system.update(dt)
    
    def draw(self) -> None:
        """Rendert das Spiel und das FPS-Display."""
        # Render based on current game state
        if self.game_state == GameState.MAIN_MENU or self.game_state in [GameState.SETTINGS, GameState.CREDITS, GameState.LOAD_GAME]:
            # Draw menu system
            self.menu_system.draw()
        elif self.game_state == GameState.GAMEPLAY:
            # Draw gameplay level
            if self.level:
                self.level.render()
            
            # ✨ Draw element mixer
            screen_height = self.game_surface.get_height()
            self.element_mixer.render(self.game_surface, screen_height)
            
            # FPS-Display zeichnen (falls aktiviert und im Gameplay)
            if self.show_fps:
                self.fps_monitor.draw(self.game_surface)
            
            # Hotkey-Display zeichnen (falls aktiviert und im Gameplay)
            self.hotkey_display.draw()
        elif self.game_state == GameState.PAUSE:
            # Draw gameplay in background, then pause menu on top
            if self.level:
                self.level.render()
            
            # ✨ Draw element mixer (visible during pause for reference)
            screen_height = self.game_surface.get_height()
            self.element_mixer.render(self.game_surface, screen_height)
            
            # Draw hotkey display even when paused (useful for reference)
            self.hotkey_display.draw()
            
            # Draw pause menu overlay
            self.menu_system.draw()
        elif self.game_state == GameState.GAME_OVER:
            # Fill screen with black background first
            self.game_surface.fill((0, 0, 0))
            
            # Draw Game Over menu overlay
            self.menu_system.draw()
        
        # Draw messages on top of everything
        self.draw_message()
        
        # Bildschirm aktualisieren
        pygame.display.flip()
    
    
    def run(self) -> None:
        """Hauptspielschleife mit Performance-Tracking und Menu-System."""
        print("Main loop started with Menu System!")
        print("🎮 Navigation:")
        print("   🖱️ Maus: Menu-Navigation")
        print("   ESC: Zurück zum Menu / Beenden")
        print("   Im Spiel:")
        print("     W A S D: Spieler bewegen")
        print("     Maus: Blickrichtung")
        print("     Linksklick: Feuerball schießen")
        print("     1-6: Zauberspruch auswählen (keine Cooldown)")
        print("     C: Ausgewählten Zauber wirken (startet Cooldown)")
        print("     F3: FPS-Anzeige ein/aus")
        print("     F4: Detaillierte/Einfache Anzeige")
        print("     F5: Statistiken zurücksetzen")
        print("     F6: Performance-Zusammenfassung")
        print("     F7: Global Magic Test")  # 🚀 Verschoben von F10
        print("     F8: Feuer + Heilung")   # 🚀 Kombiniert F11+F12
        print("     F9-F12: Speichern in Slot 1-4")  # 🚀 Jetzt konfliktfrei!
        print("     H: Hotkey-Anzeige ein/aus")
        
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
        
        # Finale Performance-Zusammenfassung
        if self.game_state == GameState.GAMEPLAY:
            print("\n🏁 FINALE PERFORMANCE-STATISTIKEN:")
            self._print_performance_summary()
        
        print("Game is shutting down...")
        pygame.quit()
        sys.exit()
    
    def _test_magic_system_global(self):
        """Globaler Magie-System Test"""
        print("🧪 === GLOBAL MAGIC SYSTEM TEST ===")
        if self.level and self.level.game_logic and self.level.game_logic.player:
            player = self.level.game_logic.player
            print(f"🔍 Player gefunden: {player.__class__.__name__}")
            print(f"🔍 Player HP: {player.current_health}/{player.max_health}")
            
            # Test Magie-System direkt
            magic_system = player.magic_system
            print(f"🔍 Magic System: {magic_system}")
            print(f"🔍 Ausgewählte Elemente: {magic_system.selected_elements}")
            
        else:
            print("❌ Kein Level/Player für Magie-Test gefunden!")
            print(f"🔍 Game State: {self.game_state}")
            print(f"🔍 Level: {self.level}")
    
    def _add_magic_element_global(self, element_name: str):
        """Fügt global ein Magie-Element hinzu"""
        if self.level and self.level.game_logic and self.level.game_logic.player:
            from systems.magic_system import ElementType
            
            element_map = {
                'fire': ElementType.FEUER,
                'water': ElementType.WASSER, 
                'stone': ElementType.STEIN
            }
            
            element = element_map.get(element_name)
            if element:
                success = self.level.game_logic.player.magic_system.add_element(element)
                print(f"🔥 Element {element_name} hinzugefügt: {success}")
            else:
                print(f"❌ Unbekanntes Element: {element_name}")
        else:
            print("❌ Kein Player für Element-Hinzufügung!")
    
    def _cast_heal_global(self):
        """Wirkt global einen Heilungszauber"""
        if self.level and self.level.game_logic and self.level.game_logic.player:
            from systems.magic_system import ElementType
            
            player = self.level.game_logic.player
            magic_system = player.magic_system
            
            # Elemente löschen und Feuer + Wasser hinzufügen
            magic_system.clear_elements()
            magic_system.add_element(ElementType.FEUER)
            magic_system.add_element(ElementType.WASSER)
            
            # Schaden zufügen für Test
            old_hp = player.current_health
            player.current_health = max(1, player.current_health - 30)
            print(f"🩸 Test-Schaden: {old_hp} -> {player.current_health} HP")
            
            # Heilung wirken
            result = magic_system.cast_magic(caster=player)
            print(f"💚 Heilung Ergebnis: {result}")
            print(f"💚 HP nach Heilung: {player.current_health}/{player.max_health}")
        else:
            print("❌ Kein Player für Heilung!")


def main() -> None:
    """Hauptfunktion zum Starten des Spiels mit Menu-System."""
    print("The Alchemist - Enhanced Version with Menu System & FPS Monitoring!")
    print("🔍 Performance-Tracking aktiviert")
    print("🎮 Vollständiges Menu-System implementiert")
    
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
