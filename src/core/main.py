# -*- coding: utf-8 -*-
"""
Hauptspiel-Datei mit erweitertem FPS-Tracking, Menu-System und optionaler
Action-System/Hardware-Integration (ESP32 über Serial).
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

from typing import Optional, Any, Callable
from settings import *
from level import Level
from asset_manager import AssetManager
from font_manager import get_font_manager
from memory_monitor import get_memory_monitor
from fps_monitor import FPSMonitor, create_detailed_fps_display
from menu_system import MenuSystem, GameState
from save_system import save_manager
from hotkey_display import HotkeyDisplay
from systems.input_system import init_universal_input
from managers.settings_manager import SettingsManager

"""
Optionale Action-System-Importe: Definiere Platzhalter, damit Pylance keine
"possibly unbound"-Warnungen meldet, falls die Imports zur Laufzeit fehlen.
"""
init_action_system: Optional[Callable[..., Any]] = None
get_action_system: Optional[Callable[..., Any]] = None
MagicSystemAdapter: Optional[Any] = None
create_hardware_input_adapter: Optional[Callable[..., Any]] = None

# Action System Integration (aktiviert, wenn verfügbar)
try:
    from systems.action_system import init_action_system as _init_action_system, get_action_system as _get_action_system, MagicSystemAdapter as _MagicSystemAdapter
    from systems.hardware_input_adapter import create_hardware_input_adapter as _create_hardware_input_adapter
    init_action_system = _init_action_system
    get_action_system = _get_action_system
    MagicSystemAdapter = _MagicSystemAdapter
    create_hardware_input_adapter = _create_hardware_input_adapter
    ACTION_SYSTEM_AVAILABLE = True
    if VERBOSE_LOGS:
        print("✅ Action System verfügbar")
except ImportError as e:
    ACTION_SYSTEM_AVAILABLE = False
    if VERBOSE_LOGS:
        print("⚠️ Action System nicht verfügbar: {}".format(e))

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
        if ACTION_SYSTEM_AVAILABLE and init_action_system is not None:
            self.action_system = init_action_system()
            
            # Versuche Hardware Input Adapter zu erstellen
            try:
                from core.config import config
                hardware_config = config.input.HARDWARE_CONFIG
                # Umgebung erlaubt Override: ALCHEMIST_HW=1 aktiviert echte Hardware
                enable_hw_env = os.environ.get('ALCHEMIST_HW', '0') == '1'
                hw_port_env = os.environ.get('ALCHEMIST_HW_PORT')
                if enable_hw_env:
                    # Erzwinge echten Hardware-Modus ohne Mock
                    hardware_config = dict(hardware_config)
                    hardware_config['mock_mode'] = False
                    if hw_port_env:
                        hardware_config['port'] = hw_port_env

                # Einfache Port-Auflösung für gängige RPi-Gerätenamen
                def _resolve_serial_port(default_port: str) -> str:
                    candidates = []
                    if hw_port_env:
                        candidates.append(hw_port_env)
                    if default_port:
                        candidates.append(default_port)
                    # Häufige Standardgeräte
                    candidates.extend(['/dev/ttyACM0', '/dev/ttyUSB0'])
                    for p in candidates:
                        try:
                            if p and os.path.exists(p):
                                return p
                        except Exception:
                            pass
                    return default_port

                resolved_port = _resolve_serial_port(hardware_config.get('port', '/dev/ttyUSB0'))
                # create_hardware_input_adapter sollte vorhanden sein, wenn ACTION_SYSTEM_AVAILABLE True ist
                if create_hardware_input_adapter is not None:
                    self.hardware_adapter = create_hardware_input_adapter(
                        port=resolved_port,
                        mock_mode=hardware_config.get('mock_mode', True)
                    )
                else:
                    self.hardware_adapter = None
                if self.hardware_adapter and VERBOSE_LOGS:
                    print(f"✅ Hardware Input Adapter aktiviert (Port: {resolved_port}, Mock: {hardware_config.get('mock_mode', True)})")
                elif not self.hardware_adapter and VERBOSE_LOGS:
                    print("⚠️ Hardware Input Adapter nicht verfügbar - Fallback auf Tastatur/Gamepad")
            except Exception as e:
                if VERBOSE_LOGS:
                    print("Hardware Input Adapter Fehler: {}".format(e))
                self.hardware_adapter = None
        
        # Initialize AssetManager
        self.asset_manager = AssetManager()
        
        # 🚀 Nutze optimierte Auflösung basierend auf Hardware
        window_width = self.optimized_settings['WINDOW_WIDTH']
        window_height = self.optimized_settings['WINDOW_HEIGHT']
        use_fullscreen = self.optimized_settings.get('FULLSCREEN', False)
        
        if VERBOSE_LOGS:
            print("🚀 Display: {}x{} @ {} FPS{}".format(
            window_width, window_height, 
            self.optimized_settings['FPS'],
            " (Vollbild)" if use_fullscreen else ""
        ))
        
        # Display-Modus basierend auf Hardware-Einstellungen
        display_flags = 0
        if use_fullscreen:
            display_flags |= pygame.FULLSCREEN
        # Performance: double buffering can reduce tearing/overhead on some drivers
        display_flags |= pygame.DOUBLEBUF
# HWSURFACE auf Raspberry Pi NICHT verwenden – sperrt die Surface und
# verursacht "Surfaces must be not locked during blit" bei allen Blits
# (set_alpha, SRCALPHA-Surfaces, draw.line-Schleifen etc.)

        # VSYNC (pygame2 keyword; safe fallback)
        vsync_enabled = bool(self.optimized_settings.get('VSYNC', False))
        try:
            self.game_surface = pygame.display.set_mode(
                (window_width, window_height),
                display_flags,
                vsync=1 if vsync_enabled else 0
            )
        except TypeError:
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
        # 🚀 RPi-Optimierung: FontManager für gecachte Fonts
        self._font_manager = get_font_manager()
        self.message_font = self._font_manager.get_font(36)
        
        # Hotkey display system
        self.hotkey_display = HotkeyDisplay(self.game_surface)
        # Start hidden by default; toggle with H
        self.hotkey_display.visible = False
        
        # FPS-Monitoring System
        self.fps_monitor = create_detailed_fps_display(position=(10, 10))
        self.fps_monitor.set_target_fps(FPS)
        # FPS-Overlay standardmäßig ausgeblendet (toggle mit F3)
        self.show_fps = False
        
        # 🚀 Memory-Monitoring System für RPi Tests (F9 zum Umschalten)
        self.memory_monitor = get_memory_monitor()
        
        # Performance-Tracking
        self.frame_count = 0
        self.total_time = 0.0
        
        # 🚀 Element Mixing System Integration
        from systems.spell_cooldown_manager import SpellCooldownManager
        from ui.element_mixer import ElementMixer
        self.spell_cooldown_manager = SpellCooldownManager()
        self.element_mixer = ElementMixer(self.spell_cooldown_manager)
        if VERBOSE_LOGS:
            print("✨ Element mixing system initialized with 3 elements (Fire/Water/Stone)")
        
        # 🥚 Easter Egg GIF Overlay
        from ui.gif_overlay import GifOverlay
        self.gif_overlay = GifOverlay((SCREEN_WIDTH, SCREEN_HEIGHT))
        self._load_easter_egg_gifs()
        
        # 🎬 Intro Cinematic System
        from ui.video_player import IntroCinematic
        self.intro_cinematic = IntroCinematic((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.intro_cinematic.load()  # Lädt Video falls vorhanden
        self._intro_pending = False  # Flag für ausstehende Intro-Wiedergabe
        
        # Falls ACTION_SYSTEM nicht verfügbar, bleibt nur Keyboard/Gamepad
        if not ACTION_SYSTEM_AVAILABLE:
            self.action_system = None
            self.hardware_adapter = None
        
        # Magic System Adapter für Action System (falls verfügbar)
        self.magic_adapter = None
        if ACTION_SYSTEM_AVAILABLE and self.action_system:
            # Magic Adapter wird erst nach Level-Erstellung gesetzt
            pass
        
        # NFC/Hardware Interface für NFC-Login
        # Hinweis: Wird nach hardware_adapter Initialisierung konfiguriert
        self.hardware_interface = None
        self.player_name = None  # Spielername vom NFC-Tag
        self.player_uid = None  # NFC Tag UID für Highscore
        self._setup_nfc_callbacks()  # Register NFC callbacks AFTER hardware_adapter is created
        
        # Start with menu music on initial MAIN_MENU
        self._current_music_path = None
        self.settings = SettingsManager()
        self._last_nonzero_music_vol = float(self.settings.music_volume) or 0.7
        self._apply_music_for_state(GameState.MAIN_MENU)
        
        if VERBOSE_LOGS:
            print("Game started with Menu System!")
            print("Architecture: Central Game class with Menu System and Level system")
            if VERBOSE_LOGS:
                print(f"🎯 Target FPS: {FPS}")
            print("💡 Drücke F3 um FPS-Anzeige ein/auszuschalten")
            print("💡 Drücke F4 um zwischen einfacher/detaillierter Anzeige zu wechseln")
            print("🎮 Verwende das Menu-System zum Navigieren!")
    
    def _setup_nfc_callbacks(self):
        """Setup NFC callbacks using existing hardware_adapter (action system)"""
        try:
            # Use existing hardware_adapter from action system (already connected to COM port)
            if self.hardware_adapter and hasattr(self.hardware_adapter, 'hardware'):
                hw_interface = self.hardware_adapter.hardware
                self.hardware_interface = hw_interface
                
                # Register NFC callback with existing hardware interface
                hw_interface.register_callback(
                    'nfc_read',
                    self._on_nfc_tag_detected
                )
                
                if VERBOSE_LOGS:
                    print("✅ NFC-Callback registriert (nutzt bestehenden Hardware-Adapter)")
            else:
                if VERBOSE_LOGS:
                    print("⚠️ Hardware-Adapter nicht verfügbar - NFC-Login deaktiviert")
                    
        except Exception as e:
            if VERBOSE_LOGS:
                print(f"⚠️ NFC Callback Setup Error: {e}")
    
    def _on_nfc_tag_detected(self, uid: str):
        """Handle NFC tag detection from hardware interface"""
        if VERBOSE_LOGS:
            print(f"🎫 NFC-Tag in Game detected: {uid}")
        
        # Post pygame event for the menu system to handle
        try:
            nfc_event = pygame.event.Event(
                pygame.USEREVENT,
                {'nfc_uid': uid}
            )
            pygame.event.post(nfc_event)
        except Exception as e:
            if VERBOSE_LOGS:
                print(f"⚠️ Error posting NFC event: {e}")
    
    def load_background_music(self):
        """Legacy helper: plays gameplay background music."""
        self._play_music(BACKGROUND_MUSIC)

    def _play_music(self, music_path: str):
        """Load and loop music if path changed; respect volume."""
        try:
            if self._current_music_path != music_path:
                pygame.mixer.music.stop()
                pygame.mixer.music.load(music_path)
                vol = 0.7
                try:
                    base = float(self.settings.music_volume)
                except Exception:
                    base = MUSIC_VOLUME
                # Apply master volume/mute
                try:
                    from managers.settings_manager import SettingsManager
                    sm = SettingsManager()
                    if sm.master_mute:
                        vol = 0.0
                    else:
                        vol = max(0.0, min(1.0, base * float(sm.master_volume)))
                except Exception:
                    vol = base
                pygame.mixer.music.set_volume(vol)
                pygame.mixer.music.play(-1)
                self._current_music_path = music_path
                if VERBOSE_LOGS:
                    print("Music started:", music_path)
                if VERBOSE_LOGS:
                    try:
                        print(f"🎵 Music volume: {pygame.mixer.music.get_volume():.2f}")
                    except Exception:
                        pass
        except Exception as e:
            if VERBOSE_LOGS:
                print("Music error:", e)

    def apply_current_music_volume(self):
        """Reapply the current music volume from settings without restarting track."""
        try:
            base = float(self.settings.music_volume)
            # Apply master volume/mute
            try:
                from managers.settings_manager import SettingsManager
                sm = SettingsManager()
                if sm.master_mute:
                    vol = 0.0
                else:
                    vol = max(0.0, min(1.0, base * float(sm.master_volume)))
            except Exception:
                vol = base
            pygame.mixer.music.set_volume(vol)
            if VERBOSE_LOGS:
                try:
                    if VERBOSE_LOGS:
                        print(f"🎵 Music volume applied: {pygame.mixer.music.get_volume():.2f}")
                except Exception:
                    pass
        except Exception:
            pass

    def _load_easter_egg_gifs(self):
        """Lädt Easter Egg GIFs vor."""
        import os
        assets_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "assets")
        ishowspeed_gif = os.path.join(assets_path, "ishowspeed", "giphy.gif")
        
        if os.path.exists(ishowspeed_gif):
            self.gif_overlay.load_gif(ishowspeed_gif, scale_to_fit=True)
            print("🥚 Easter Egg GIF geladen: ishowspeed")
        else:
            print(f"⚠️ Easter Egg GIF nicht gefunden: {ishowspeed_gif}")

    def _check_easter_eggs(self):
        """Prüft ob ein Easter Egg ausgelöst wurde."""
        if hasattr(self, 'element_mixer') and self.element_mixer.pending_easter_egg:
            easter_egg = self.element_mixer.pending_easter_egg
            self.element_mixer.pending_easter_egg = None
            
            if easter_egg == "ishowspeed":
                print("🚀 IShowSpeed Easter Egg aktiviert!")
                if self.gif_overlay.gif_loaded:
                    self.gif_overlay.play(loop=False)

    def _apply_music_for_state(self, state: 'GameState'):
        """Switches music based on current high-level state."""
        is_menu = state in [GameState.MAIN_MENU, GameState.SETTINGS, GameState.CREDITS, GameState.LOAD_GAME]
        if is_menu:
            # Fallback to BACKGROUND_MUSIC if menu track missing
            music_path = MENU_MUSIC if os.path.exists(MENU_MUSIC) else BACKGROUND_MUSIC
            self._play_music(music_path)
        elif state in [GameState.GAMEPLAY, GameState.PAUSE, GameState.GAME_OVER]:
            # Use gameplay music for gameplay, pause and game over
            self._play_music(BACKGROUND_MUSIC)
    
    def handle_events(self):
        """Behandelt alle Pygame-Events inklusive Menu-System und FPS-Display Steuerung."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            # 🎬 Intro-Cinematic Event-Handling (blockiert alles während Wiedergabe)
            if self.intro_cinematic.is_playing:
                self.intro_cinematic.handle_event(event)
                continue  # Alle anderen Events werden während Intro ignoriert
            
            # 🥚 Easter Egg GIF-Overlay Event-Handling (blockiert andere Events während Wiedergabe)
            if self.gif_overlay.is_playing:
                if self.gif_overlay.handle_event(event):
                    continue  # Event wurde konsumiert
            
            # Apply music volume on settings change
            if event.type == pygame.USEREVENT and getattr(event, 'name', '') == 'APPLY_MUSIC_VOLUME':
                self.apply_current_music_volume()
            elif event.type == pygame.USEREVENT and getattr(event, 'nfc_login_complete', False):
                # NFC login completed - transition to gameplay
                self.start_nfc_login_or_gameplay()
            elif event.type == pygame.USEREVENT and getattr(event, 'name', '') == 'APPLY_DIFFICULTY':
                try:
                    if self.level and getattr(self.level, 'enemy_manager', None):
                        self.level.enemy_manager.apply_difficulty_to_all()
                        if VERBOSE_LOGS:
                            print("⚔️ Difficulty reapplied to all enemies")
                except Exception as _e:
                    if VERBOSE_LOGS:
                        print(f"⚠️ Failed to apply difficulty: {_e}")
            
            # Pass all keyboard events to the current state
            if event.type in [pygame.KEYDOWN, pygame.KEYUP]:
                if event.type == pygame.KEYDOWN:
                    # Global runtime music controls
                    if event.key == pygame.K_PAGEDOWN:
                        new_vol = max(0.0, min(1.0, float(self.settings.music_volume) - 0.05))
                        self.settings.music_volume = new_vol
                        try:
                            from managers.settings_manager import SettingsManager
                            SettingsManager().save()
                        except Exception:
                            pass
                        if new_vol > 0:
                            self._last_nonzero_music_vol = new_vol
                        self.apply_current_music_volume()
                    elif event.key == pygame.K_PAGEUP:
                        new_vol = max(0.0, min(1.0, float(self.settings.music_volume) + 0.05))
                        self.settings.music_volume = new_vol
                        try:
                            from managers.settings_manager import SettingsManager
                            SettingsManager().save()
                        except Exception:
                            pass
                        if new_vol > 0:
                            self._last_nonzero_music_vol = new_vol
                        self.apply_current_music_volume()
                    elif event.key == pygame.K_m:
                        # Toggle mute/unmute
                        cur = float(self.settings.music_volume)
                        if cur > 0.0:
                            self._last_nonzero_music_vol = cur
                            self.settings.music_volume = 0.0
                        else:
                            self.settings.music_volume = max(0.05, self._last_nonzero_music_vol)
                        try:
                            from managers.settings_manager import SettingsManager
                            SettingsManager().save()
                        except Exception:
                            pass
                        self.apply_current_music_volume()
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
                        if VERBOSE_LOGS:
                            print(f"🔧 FPS-Anzeige: {'Ein' if self.show_fps else 'Aus'}")
                    
                    # F4: Detaillierte/Einfache FPS-Anzeige wechseln (nur im Gameplay)
                    elif event.key == pygame.K_F4 and self.game_state == GameState.GAMEPLAY:
                        self.fps_monitor.toggle_detailed()
                        mode = "Detailliert" if self.fps_monitor.show_detailed else "Einfach"
                        if VERBOSE_LOGS:
                            print(f"🔧 FPS-Modus: {mode}")
                    
                    # F5: FPS-Statistiken zurücksetzen (nur im Gameplay)
                    elif event.key == pygame.K_F5 and self.game_state == GameState.GAMEPLAY:
                        self.fps_monitor.reset_stats()
                        if VERBOSE_LOGS:
                            print("🔧 FPS-Statistiken zurückgesetzt")
                    
                    # F6: Performance-Zusammenfassung ausgeben (nur im Gameplay)
                    elif event.key == pygame.K_F6 and self.game_state == GameState.GAMEPLAY:
                        if VERBOSE_LOGS:
                            self._print_performance_summary()
                    
                    # F9: Memory Monitor Overlay ein/ausschalten (nur im Gameplay)
                    elif event.key == pygame.K_F9 and self.game_state == GameState.GAMEPLAY:
                        self.memory_monitor.toggle_overlay()
                        if VERBOSE_LOGS:
                            self.memory_monitor.log_snapshot("F9 Toggle")
                    
                    # H: Hotkey-Anzeige ein/ausschalten (nur im Gameplay)
                    elif event.key == pygame.K_h and self.game_state == GameState.GAMEPLAY:
                        self.hotkey_display.toggle_visibility()
                        if VERBOSE_LOGS:
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
                    # 🎰 NICHT während Blackjack!
                    elif self.game_state == GameState.GAMEPLAY:
                        # Prüfe ob Blackjack aktiv ist
                        blackjack_active = False
                        if self.level and hasattr(self.level, 'blackjack_game') and self.level.blackjack_game:
                            blackjack_active = self.level.blackjack_game.is_active
                        
                        # Element selection: 1=Water, 2=Fire, 3=Stone (nur wenn Blackjack NICHT aktiv)
                        if not blackjack_active:
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
            if self.game_state == GameState.MAIN_MENU or self.game_state in [GameState.SETTINGS, GameState.CREDITS, GameState.LOAD_GAME, GameState.PAUSE, GameState.GAME_OVER, GameState.NFC_LOGIN]:
                # Menu system handles these states
                result = self.menu_system.handle_event(event)
                if result:
                    if result == GameState.GAMEPLAY:
                        self.start_nfc_login_or_gameplay()
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
                        self.start_new_game()
                    elif result == "retry_game":
                        self.restart_current_game()
                    # Other state changes are handled by menu_system internally
            
            elif self.game_state == GameState.GAMEPLAY:
                # Skip level handling ONLY for element keys 1-3 to prevent double processing
                # ABER: Nicht überspringen wenn Blackjack aktiv ist!
                skip_level = False
                blackjack_active = False
                if self.level and hasattr(self.level, 'blackjack_game') and self.level.blackjack_game:
                    blackjack_active = self.level.blackjack_game.is_active
                
                if (event.type == pygame.KEYDOWN and 
                    event.key in [pygame.K_1, pygame.K_2, pygame.K_3] and
                    not blackjack_active):  # Nur überspringen wenn Blackjack NICHT aktiv
                    skip_level = True
                    if VERBOSE_LOGS:
                        print(f"🚫 Skipping level handling for element key: {event.key}")
                
                # Pass events to level if in gameplay (except element keys 1-3)
                if not skip_level and self.level and hasattr(self.level, 'handle_event'):
                    self.level.handle_event(event)
    
    
    def start_nfc_login_or_gameplay(self):
        """
        Transition from NFC_LOGIN to actual gameplay.
        Called when NFC_LOGIN state completes (auto-transition after tag detected).
        """
        # Get player name and UID from NFC login screen
        nfc_login_state = self.menu_system.states.get(GameState.NFC_LOGIN)
        if nfc_login_state:
            if hasattr(nfc_login_state, 'player_name'):
                self.player_name = nfc_login_state.player_name
                if VERBOSE_LOGS:
                    print(f"👤 Spielername gespeichert: {self.player_name}")
            if hasattr(nfc_login_state, 'detected_uid'):
                self.player_uid = nfc_login_state.detected_uid
                if VERBOSE_LOGS:
                    print(f"🏷️ NFC UID gespeichert: {self.player_uid}")
        
        # Start gameplay
        self.start_new_game()
    
    def start_new_game(self):
        """Startet ein neues Spiel - optional mit Intro-Cinematic"""
        if VERBOSE_LOGS:
            print("🎮 Neues Spiel wird gestartet...")
            if self.player_name:
                print(f"👤 Mit Spieler: {self.player_name}")
        
        # 🎬 Intro-Cinematic abspielen (falls vorhanden)
        if self.intro_cinematic.video_player.video_loaded:
            self._intro_pending = True
            self.intro_cinematic.play(on_complete=self._on_intro_complete)
            print("🎬 Intro-Cinematic wird abgespielt...")
        else:
            # Kein Intro - direkt zum Spiel
            self._actually_start_game()
    
    def _on_intro_complete(self):
        """Wird aufgerufen wenn das Intro beendet ist."""
        self._intro_pending = False
        self._actually_start_game()
    
    def _actually_start_game(self):
        """Startet das eigentliche Gameplay nach dem Intro."""
        self.game_state = GameState.GAMEPLAY
        self.level = Level(self.game_surface, main_game=self)
        self._apply_music_for_state(self.game_state)
        
        # Set save callback for the level
        self.level.set_save_callback(self.save_current_game)
        
        # Magic System Adapter für Action System (falls verfügbar)
        # if ACTION_SYSTEM_AVAILABLE and self.action_system and self.level:
        #     self.magic_adapter = MagicSystemAdapter(self.level)
        #     self.action_system.set_magic_handler(self.magic_adapter)
        #     print("✅ Magic System Adapter für Action System konfiguriert")
        
        if VERBOSE_LOGS:
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
        self._apply_music_for_state(self.game_state)
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
            self._apply_music_for_state(self.game_state)
            
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
        """Schnelles Speichern: wählt automatisch einen freien Slot (1-5) oder überschreibt den ältesten."""
        if self.level and self.level.game_logic:
            data = save_manager.export_save_data(self.level.game_logic)
            used_slot = save_manager.save_auto(data)
            if used_slot:
                print(f"💾 Schnell gespeichert in Slot {used_slot}!")
                self.show_message(f"💾 Schnell gespeichert (Slot {used_slot})!")
            else:
                print("❌ Fehler beim Speichern!")
                self.show_message("❌ Speichern fehlgeschlagen!")
        else:
            print("⚠️ Kein aktives Spiel zum Speichern!")
            self.show_message("⚠️ Kein aktives Spiel!")
    
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
            data = save_manager.export_save_data(self.level.game_logic)
            used_slot = save_manager.save_auto(data)
            if used_slot:
                print(f"💾 Spiel vom Hauptmenü gespeichert (Slot {used_slot})!")
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
            if VERBOSE_LOGS:
                print("⏸️ Spiel pausiert...")
            
            # Input-Status leeren um Bug zu vermeiden
            if self.level:
                self.level.clear_input_state()
            
            self.previous_state = self.game_state
            self.game_state = GameState.PAUSE
            self.menu_system.change_state(GameState.PAUSE)
            self._apply_music_for_state(self.game_state)
    
    def resume_game(self):
        """Setzt das Spiel fort"""
        if self.game_state == GameState.PAUSE:
            if VERBOSE_LOGS:
                print("▶️ Spiel fortgesetzt")
            
            # Input-Status leeren um sicherzustellen, dass keine Tasten "hängen"
            if self.level:
                self.level.clear_input_state()
            
            self.game_state = self.previous_state
            self._apply_music_for_state(self.game_state)
    
    def return_to_menu(self):
        """Kehrt zum Hauptmenü zurück"""
        print("📋 Zurück zum Hauptmenü...")
        
        # Speichere High-Score vor dem Cleanup
        if self.level and self.player_uid:
            from managers.highscore_manager import get_highscore_manager
            try:
                # Get score from level if available
                if hasattr(self.level, '_score_data') and self.level._score_data:
                    final_score = self.level._score_data.final_score
                    if final_score and final_score > 0:
                        highscore_mgr = get_highscore_manager()
                        is_new_high = highscore_mgr.set_highscore(self.player_uid, final_score)
                        player_display = self.player_name if self.player_name else "Unbekannt"
                        if is_new_high:
                            print(f"🏆 Neuer High-Score für {player_display}: {final_score}")
                        else:
                            print(f"📊 Score für {player_display}: {final_score}")
            except Exception as e:
                if VERBOSE_LOGS:
                    print(f"⚠️ High-Score Save Error: {e}")
        
        # Input-Status leeren bevor wir zum Menü wechseln
        if self.level:
            self.level.clear_input_state()
        
        self.game_state = GameState.MAIN_MENU
        if self.level:
            # Clean up level resources if needed
            self.level = None
        print("✅ Im Hauptmenü")
        self._apply_music_for_state(self.game_state)
    
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
        
        # 🥚 Easter Egg System prüfen und GIF-Overlay updaten
        self._check_easter_eggs()
        if self.gif_overlay.is_playing:
            self.gif_overlay.update(dt)
        
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
                    self._apply_music_for_state(self.game_state)
                    self.menu_system.show_game_over()
            
            # ✨ Update element mixing system
            self.spell_cooldown_manager.update()
            self.element_mixer.update(dt)
        elif self.game_state == GameState.GAME_OVER:
            # Update menu system for Game Over state
            self.menu_system.update(dt)
    
    def draw(self) -> None:
        """Rendert das Spiel und das FPS-Display."""
        # 🎬 Intro-Cinematic Rendering (überlagert alles)
        if self.intro_cinematic.is_playing:
            self.intro_cinematic.update()
            self.intro_cinematic.render(self.game_surface)
            pygame.display.flip()
            return
        
        # Render based on current game state
        if self.game_state == GameState.MAIN_MENU or self.game_state in [GameState.SETTINGS, GameState.CREDITS, GameState.LOAD_GAME]:
            # Draw menu system
            self.menu_system.draw()
        elif self.game_state == GameState.GAMEPLAY:
            # Draw gameplay level
            if self.level:
                self.level.render()
            
            # 🏆 Während Finale kein HUD anzeigen
            finale_active = self.level and hasattr(self.level, '_finale_active') and self.level._finale_active
            if not finale_active:
                # ✨ Draw element mixer
                screen_height = self.game_surface.get_height()
                self.element_mixer.render(self.game_surface, screen_height)

                # Mana bar above the element mixer with modern pixel-art style
                try:
                    player = self.level.game_logic.player if self.level and self.level.game_logic else None
                    if player:
                        mix_x, mix_y = self.element_mixer.get_position(screen_height)
                        bar_width, bar_height = 180, 14
                        bar_x = mix_x
                        bar_y = max(0, mix_y - 20)
                        
                        # Aeusserer Rahmen (dunkel)
                        pygame.draw.rect(self.game_surface, (25, 30, 50), (bar_x - 2, bar_y - 2, bar_width + 4, bar_height + 4))
                        # Hintergrund mit Gradient-Effekt
                        for row in range(bar_height):
                            ratio = row / bar_height
                            r = int(15 * (1 - ratio) + 8 * ratio)
                            g = int(20 * (1 - ratio) + 12 * ratio)
                            b = int(35 * (1 - ratio) + 25 * ratio)
                            pygame.draw.line(self.game_surface, (r, g, b), (bar_x, bar_y + row), (bar_x + bar_width, bar_y + row))
                        
                        # Mana-Fuellung mit Gradient
                        fill_w = int(bar_width * player.get_mana_percentage())
                        if fill_w > 0:
                            for row in range(bar_height):
                                ratio = row / bar_height
                                r = int(60 * (1 - ratio) + 30 * ratio)
                                g = int(140 * (1 - ratio) + 100 * ratio)
                                b = int(255 * (1 - ratio) + 200 * ratio)
                                pygame.draw.line(self.game_surface, (r, g, b), (bar_x, bar_y + row), (bar_x + fill_w, bar_y + row))
                            # Highlight oben
                            pygame.draw.line(self.game_surface, (120, 180, 255), (bar_x, bar_y), (bar_x + fill_w, bar_y))
                        
                        # Innerer Rahmen
                        pygame.draw.rect(self.game_surface, (50, 60, 90), (bar_x, bar_y, bar_width, bar_height), 1)
                        # Leuchtender Rahmen
                        pygame.draw.rect(self.game_surface, (70, 90, 140), (bar_x - 1, bar_y - 1, bar_width + 2, bar_height + 2), 1)
                except Exception:
                    pass
                
                # FPS-Display zeichnen (falls aktiviert und im Gameplay)
                if self.show_fps:
                    self.fps_monitor.draw(self.game_surface)
                
                # 🚀 Memory Monitor Overlay (F9 zum Umschalten)
                self.memory_monitor.update()
                self.memory_monitor.render(self.game_surface)
                
                # Hotkey-Display zeichnen (falls aktiviert und im Gameplay)
                self.hotkey_display.draw()
            
                # 💬 Dialog-Box ganz am Ende rendern (über allem anderen)
                if self.level and self.level.dialogue_box:
                    self.level.dialogue_box.render()
                
                # 🥚 Easter Egg GIF-Overlay ganz oben (über allem)
                if self.gif_overlay.is_playing:
                    self.gif_overlay.render(self.game_surface)
                
        elif self.game_state == GameState.PAUSE:
            # Draw gameplay in background, then pause menu on top
            if self.level:
                self.level.render()
            
            # ✨ Draw element mixer (visible during pause for reference)
            screen_height = self.game_surface.get_height()
            self.element_mixer.render(self.game_surface, screen_height)

            # Mana bar above the element mixer in pause (same style as gameplay)
            try:
                player = self.level.game_logic.player if self.level and self.level.game_logic else None
                if player:
                    mix_x, mix_y = self.element_mixer.get_position(screen_height)
                    bar_width, bar_height = 180, 14
                    bar_x = mix_x
                    bar_y = max(0, mix_y - 20)
                    
                    # Aeusserer Rahmen
                    pygame.draw.rect(self.game_surface, (25, 30, 50), (bar_x - 2, bar_y - 2, bar_width + 4, bar_height + 4))
                    # Hintergrund
                    for row in range(bar_height):
                        ratio = row / bar_height
                        r = int(15 * (1 - ratio) + 8 * ratio)
                        g = int(20 * (1 - ratio) + 12 * ratio)
                        b = int(35 * (1 - ratio) + 25 * ratio)
                        pygame.draw.line(self.game_surface, (r, g, b), (bar_x, bar_y + row), (bar_x + bar_width, bar_y + row))
                    
                    # Mana-Fuellung
                    fill_w = int(bar_width * player.get_mana_percentage())
                    if fill_w > 0:
                        for row in range(bar_height):
                            ratio = row / bar_height
                            r = int(60 * (1 - ratio) + 30 * ratio)
                            g = int(140 * (1 - ratio) + 100 * ratio)
                            b = int(255 * (1 - ratio) + 200 * ratio)
                            pygame.draw.line(self.game_surface, (r, g, b), (bar_x, bar_y + row), (bar_x + fill_w, bar_y + row))
                        pygame.draw.line(self.game_surface, (120, 180, 255), (bar_x, bar_y), (bar_x + fill_w, bar_y))
                    
                    pygame.draw.rect(self.game_surface, (50, 60, 90), (bar_x, bar_y, bar_width, bar_height), 1)
                    pygame.draw.rect(self.game_surface, (70, 90, 140), (bar_x - 1, bar_y - 1, bar_width + 2, bar_height + 2), 1)
            except Exception:
                pass
            
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
        if VERBOSE_LOGS:
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
        if self.game_state == GameState.GAMEPLAY and VERBOSE_LOGS:
            print("\n🏁 FINALE PERFORMANCE-STATISTIKEN:")
            self._print_performance_summary()
        
        if VERBOSE_LOGS:
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
    if VERBOSE_LOGS:
        print("The Alchemist - Enhanced Version with Menu System & FPS Monitoring!")
        print("🔍 Performance-Tracking aktiviert")
        print("🎮 Vollständiges Menu-System implementiert")
    
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
