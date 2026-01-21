# -*- coding: utf-8 -*-
# src/config.py
"""
Modernisierte zentrale Konfigurationsdatei für Das Alchemist Spiel
Verwendet Klassen-basierte Organisation für bessere Struktur
"""

import pygame
import os
from os import path

# === PFAD DEFINITIONEN (ROBUST) ===
# Finde den absoluten Pfad zur src-Datei, dann gehe zu root
SRC_DIR = path.dirname(path.dirname(path.abspath(__file__)))  # Geht von core/ zu src/
ROOT_DIR = path.dirname(SRC_DIR)  # Geht von src/ zu root
ASSETS_DIR = path.abspath(path.join(ROOT_DIR, 'assets'))

class DisplayConfig:
    """Display- und Fenster-Konfiguration mit RPi4-Optimierung und 7-Zoll Monitor Support"""
    # Drucke Profil-Hinweise höchstens einmal pro Lauf
    _last_profile_printed = None
    # Standard-Einstellungen (PC)
    SCREEN_WIDTH = 1920
    SCREEN_HEIGHT = 1080
    WINDOW_WIDTH = 1280
    WINDOW_HEIGHT = 720
    FPS = 60
    
    # 7-Zoll Monitor Einstellungen (1024x600)
    SMALL_SCREEN_WIDTH = 1024
    SMALL_SCREEN_HEIGHT = 600
    SMALL_SCREEN_THRESHOLD = 1200  # Auflösungen unter 1200px Breite gelten als "klein"
    
    # 🚀 RPi4-Performance-Profile
    @staticmethod
    def is_raspberry_pi():
        """Erkennt ob das System ein Raspberry Pi ist"""
        try:
            with open('/proc/cpuinfo', 'r') as f:
                cpuinfo = f.read()
                return 'Raspberry Pi' in cpuinfo or 'BCM' in cpuinfo
        except:
            # Windows/andere Systeme - kein RPi
            return False
    
    @staticmethod
    def is_small_screen():
        """Erkennt ob ein kleiner Bildschirm (7-Zoll) verwendet wird"""
        # Allow forcing 7-inch mode via launcher/env var
        try:
            if os.environ.get('ALCHEMIST_SMALL_SCREEN', '0') == '1':
                return True
        except Exception:
            pass

        import pygame
        
        # Versuche die Display-Informationen zu bekommen
        try:
            pygame.display.init()
            display_info = pygame.display.Info()
            return display_info.current_w <= DisplayConfig.SMALL_SCREEN_THRESHOLD
        except:
            return False
    
    @staticmethod
    def get_optimized_settings():
        """Gibt optimierte Einstellungen basierend auf Hardware zurück"""
        is_rpi = DisplayConfig.is_raspberry_pi()
        is_small = DisplayConfig.is_small_screen()
        
        def maybe_print(message: str, profile_id: str):
            try:
                from core.settings import VERBOSE_LOGS
            except Exception:
                VERBOSE_LOGS = False  # type: ignore
            # Unterdrücke Spam: Nur drucken, wenn Profil sich geändert hat und verbose an ist
            if VERBOSE_LOGS and DisplayConfig._last_profile_printed != profile_id:  # type: ignore[name-defined]
                print(message)
                DisplayConfig._last_profile_printed = profile_id
        
        if is_small:
            maybe_print("📱 7-Zoll Monitor (1024x600) erkannt - Anpassungen für kleinen Bildschirm!", "small")
            return {
                'FPS': 45,              # 📱 Moderate FPS für 7-Zoll
                'WINDOW_WIDTH': 1024,   # 📱 Exakte Bildschirmbreite
                'WINDOW_HEIGHT': 600,   # 📱 Exakte Bildschirmhöhe
                'FULLSCREEN': True,     # 📱 Vollbild für 7-Zoll optimal
                'LOW_EFFECTS': False,   # 📱 Effekte können bleiben bei 1024x600
                'AUDIO_QUALITY': 'MEDIUM', # 📱 Mittlere Audio-Qualität
                'VSYNC': True,          # 📱 VSync für flüssigeres Bild
                'TILE_CACHE_SIZE': 75,  # 📱 Optimierter Cache für 7-Zoll
                'AUDIO_FREQUENCY': 44100,# 📱 Standard Audio-Frequenz
                'AUDIO_BUFFER': 512,    # � Optimaler Audio-Buffer
                'UI_SCALE': 0.8,        # 📱 UI etwas kleiner skalieren
                'FONT_SIZE_SMALL': 14,  # 📱 Kleinere Schriftgrößen
                'FONT_SIZE_NORMAL': 18,
                'FONT_SIZE_LARGE': 24,
                'SPELL_BAR_SCALE': 0.9, # 📱 Spell Bar etwas kleiner
                'HOTKEY_DISPLAY_COMPACT': True  # 📱 Kompakte Hotkey-Anzeige
            }
        elif is_rpi:
            maybe_print("🚀 Raspberry Pi erkannt - Performance-Optimierungen aktiviert!", "rpi")
            return {
                'FPS': 30,              # 🚀 Reduzierte FPS für RPi4
                'WINDOW_WIDTH': 1024,   # 🚀 Kleinere Auflösung
                'WINDOW_HEIGHT': 576,   # 🚀 16:9 aber niedriger
                'FULLSCREEN': False,    # 🚀 Fenstermodus für RPi
                'LOW_EFFECTS': True,    # 🚀 Reduzierte Effekte
                'AUDIO_QUALITY': 'LOW', # 🚀 Niedrigere Audio-Qualität
                'VSYNC': False,         # 🚀 VSync aus für RPi4
                'TILE_CACHE_SIZE': 50,  # 🚀 Kleinerer Tile-Cache
                'AUDIO_FREQUENCY': 22050,# 🚀 Niedrigere Audio-Frequenz
                'AUDIO_BUFFER': 1024,   # 🚀 Größerer Audio-Buffer für Stabilität
                'UI_SCALE': 1.0,        # 🚀 Standard UI-Skalierung
                'FONT_SIZE_SMALL': 16,
                'FONT_SIZE_NORMAL': 20,
                'FONT_SIZE_LARGE': 28,
                'SPELL_BAR_SCALE': 1.0,
                'HOTKEY_DISPLAY_COMPACT': False
            }
        else:
            maybe_print("🖥️ Desktop-System erkannt - Standard-Einstellungen", "desktop")
            return {
                'FPS': 60,              # Standard FPS
                'WINDOW_WIDTH': 1280,   # Standard Auflösung
                'WINDOW_HEIGHT': 720,   
                'FULLSCREEN': False,    # Fenstermodus für Desktop
                'LOW_EFFECTS': False,   # Alle Effekte
                'AUDIO_QUALITY': 'HIGH',# Hohe Audio-Qualität
                'VSYNC': True,          # VSync für flüssigeres Gameplay
                'TILE_CACHE_SIZE': 100, # Größerer Cache
                'AUDIO_FREQUENCY': 44100,# Standard Audio-Frequenz
                'AUDIO_BUFFER': 512,    # Optimaler Audio-Buffer für PC
                'UI_SCALE': 1.0,        # Standard UI-Skalierung
                'FONT_SIZE_SMALL': 16,
                'FONT_SIZE_NORMAL': 20,
                'FONT_SIZE_LARGE': 28,
                'SPELL_BAR_SCALE': 1.0,
                'HOTKEY_DISPLAY_COMPACT': False
            }
    
    @staticmethod
    def init_audio_for_hardware():
        """🚀 Task 4: Initialisiert Audio mit hardware-spezifischen Einstellungen"""
        import pygame
        
        # Nur initialisieren wenn noch nicht geschehen
        if pygame.mixer.get_init():
            return
            
        settings = DisplayConfig.get_optimized_settings()
        
        try:
            # Hardware-spezifische Audio-Initialisierung
            pygame.mixer.pre_init(
                frequency=settings['AUDIO_FREQUENCY'],
                size=-16,           # 16-bit signed samples
                channels=2,         # Stereo
                buffer=settings['AUDIO_BUFFER']
            )
            
            # Mixer tatsächlich initialisieren
            pygame.mixer.init()
            
            hardware_type = "RPi4" if DisplayConfig.is_raspberry_pi() else "Desktop"
            print(f"🔊 Audio initialisiert für {hardware_type}:")
            print(f"   Frequenz: {settings['AUDIO_FREQUENCY']}Hz")
            print(f"   Buffer: {settings['AUDIO_BUFFER']} samples")
            
        except pygame.error as e:
            print(f"⚠️ Audio-Initialisierung fehlgeschlagen: {e}")
            # Fallback zu einfacherer Initialisierung
            try:
                pygame.mixer.init()
                print("🔊 Audio-Fallback erfolgreich")
            except:
                print("❌ Audio komplett fehlgeschlagen - Spiel läuft stumm")

class UIConfig:
    """UI-Konfiguration für verschiedene Bildschirmgrößen"""
    
    @staticmethod
    def get_ui_settings():
        """Gibt UI-Einstellungen basierend auf der Bildschirmgröße zurück"""
        display_settings = DisplayConfig.get_optimized_settings()
        
        return {
            # Schriftgrößen
            'FONT_SIZE_SMALL': display_settings.get('FONT_SIZE_SMALL', 16),
            'FONT_SIZE_NORMAL': display_settings.get('FONT_SIZE_NORMAL', 20),
            'FONT_SIZE_LARGE': display_settings.get('FONT_SIZE_LARGE', 28),
            
            # UI-Skalierung
            'UI_SCALE': display_settings.get('UI_SCALE', 1.0),
            'SPELL_BAR_SCALE': display_settings.get('SPELL_BAR_SCALE', 1.0),
            
            # Kompakte Anzeige für kleine Bildschirme
            'HOTKEY_DISPLAY_COMPACT': display_settings.get('HOTKEY_DISPLAY_COMPACT', False),
            
            # Spell Bar Anpassungen für kleine Bildschirme
            'SPELL_SLOT_SIZE': int(56 * display_settings.get('SPELL_BAR_SCALE', 1.0)),
            'SPELL_SLOT_SPACING': int(8 * display_settings.get('UI_SCALE', 1.0)),
            
            # Health Bar Anpassungen
            'HEALTH_BAR_WIDTH': int(100 * display_settings.get('UI_SCALE', 1.0)),
            'HEALTH_BAR_HEIGHT': int(8 * display_settings.get('UI_SCALE', 1.0)),
            
            # FPS Monitor Position (für kleine Bildschirme)
            'FPS_POSITION_X': 10 if display_settings.get('HOTKEY_DISPLAY_COMPACT') else 10,
            'FPS_POSITION_Y': 10,
            
            # Hotkey Display Anpassungen
            'HOTKEY_LINE_HEIGHT': int(20 * display_settings.get('UI_SCALE', 1.0)),
            'HOTKEY_PADDING': int(8 * display_settings.get('UI_SCALE', 1.0)),
        }

class PlayerConfig:
    """Player-spezifische Konfiguration"""
    SPEED = 4
    SIZE = (96, 128)  # (width, height) - 2 Tile-Blöcke
    START_POS = (960, 500)
    SPRITE_WIDTH = 96
    SPRITE_HEIGHT = 128
    ANIMATION_SPEED = 0.15
    ANIMATION_SPEEDS = {
        "idle": 120,
        "run": 80
    }
    
    @property
    def START_X(self):
        """Kompatibilität: Player Start X Position"""
        return self.START_POS[0]
    
    @property
    def START_Y(self):
        """Kompatibilität: Player Start Y Position"""
        return self.START_POS[1]
    
    @property
    def FRAME_WIDTH(self):
        """Kompatibilität: Frame Breite"""
        return self.SPRITE_WIDTH
    
    @property
    def FRAME_HEIGHT(self):
        """Kompatibilität: Frame Höhe"""
        return self.SPRITE_HEIGHT

class Colors:
    """Alle Farbdefinitionen"""
    # UI Farben
    BACKGROUND = (25, 25, 50)
    TEXT = (255, 255, 255)
    UI_BACKGROUND = (50, 50, 80)
    
    # Spielwelt Farben
    PLAYER = (100, 255, 100)
    GROUND = (139, 69, 19)
    SKY = (135, 206, 235)
    TREE = (34, 139, 34)
    
    # Zutaten Farben
    WASSERKRISTALL = (0, 150, 255)
    FEUERESSENZ = (255, 100, 0)
    ERDKRISTALL = (139, 69, 19)
    
    # Standardfarben
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)
    YELLOW = (255, 255, 0)
    MAGENTA = (255, 0, 255)
    CYAN = (0, 255, 255)
    
    # Kompatibilitäts-Aliase
    @property
    def BACKGROUND_BLUE(self):
        return self.BACKGROUND
    
    @property
    def PLAYER_GREEN(self):
        return self.PLAYER
    
    @property
    def PLACEHOLDER_GREEN(self):
        return self.PLAYER

class Paths:
    """Pfad-Konfiguration"""
    def __init__(self):
        self.ROOT_DIR = ROOT_DIR
        self.ASSETS_DIR = ASSETS_DIR
        self.MAPS_DIR = path.join(ASSETS_DIR, 'maps')
        self.SOUNDS_DIR = path.join(ASSETS_DIR, 'sounds')
        self.SPRITES_DIR = path.join(ASSETS_DIR, 'Wizard Pack')
        
        # Kompatibilitäts-Aliase für alte string-basierte Pfade
        self.ASSETS = ASSETS_DIR
        self.SPRITES = self.SPRITES_DIR
        self.MAPS = self.MAPS_DIR
        self.SOUNDS = self.SOUNDS_DIR
        # Legacy alias, now pointing to Mystic Brew for consistency
        self.MUSIC_KOROL = path.join(self.SOUNDS_DIR, "Mystic Brew (Cozy Battle Alchemist Remix).mp3")
    
    @property
    def BACKGROUND_MUSIC(self):
        # Use Mystic Brew as default background music
        return path.join(self.SOUNDS_DIR, "Mystic Brew (Cozy Battle Alchemist Remix).mp3")
    
    @property
    def MENU_MUSIC(self):
        # Use Mystic Brew for menu as well (consistent theme)
        return path.join(self.SOUNDS_DIR, "Mystic Brew (Cozy Battle Alchemist Remix).mp3")
    
    @property
    def DEFAULT_MAP(self):
        return path.join(self.MAPS_DIR, "Map2.tmx")

class InputConfig:
    """Input- und Tastatur-Konfiguration mit Hardware-Support"""
    MOVEMENT_KEYS = {
        'left': [pygame.K_LEFT, pygame.K_a],
        'right': [pygame.K_RIGHT, pygame.K_d],
        'up': [pygame.K_UP, pygame.K_w],
        'down': [pygame.K_DOWN, pygame.K_s]
    }
    
    ACTION_KEYS = {
        'brew': pygame.K_SPACE,
        'remove_ingredient': pygame.K_BACKSPACE,
        'reset': pygame.K_r,
        'music_toggle': pygame.K_m,
        'quit': pygame.K_ESCAPE
    }
    
    # Element mixing keys (for magic system integration)
    ELEMENT_KEYS = {
        'water': pygame.K_1,   # 1 = Water
        'fire': pygame.K_2,    # 2 = Fire  
        'stone': pygame.K_3    # 3 = Stone
    }
    
    # Legacy spell hotkeys (kept for compatibility)
    SPELL_KEYS = [
        pygame.K_1,
        pygame.K_2, 
        pygame.K_3,
        pygame.K_4,
        pygame.K_5,
        pygame.K_6
    ]
    
    # Action System Mappings - Zentraler ACTION Block
    ACTIONS = {
        # Bewegung
        'move_left': {
            'keyboard': [pygame.K_LEFT, pygame.K_a],
            'gamepad': {'dpad': 'left', 'axis': (0, -0.5)},  # Left stick X < -0.5
            'hardware': 'MOVE_LEFT'
        },
        'move_right': {
            'keyboard': [pygame.K_RIGHT, pygame.K_d],
            'gamepad': {'dpad': 'right', 'axis': (0, 0.5)},  # Left stick X > 0.5
            'hardware': 'MOVE_RIGHT'
        },
        'move_up': {
            'keyboard': [pygame.K_UP, pygame.K_w],
            'gamepad': {'dpad': 'up', 'axis': (1, -0.5)},    # Left stick Y < -0.5
            'hardware': 'MOVE_UP'
        },
        'move_down': {
            'keyboard': [pygame.K_DOWN, pygame.K_s],
            'gamepad': {'dpad': 'down', 'axis': (1, 0.5)},   # Left stick Y > 0.5  
            'hardware': 'MOVE_DOWN'
        },
        
        # Magic System - KORREKTE ZUORDNUNG: 1=Water, 2=Fire, 3=Stone
        'magic_fire': {
            'keyboard': [pygame.K_2],           # Taste 2
            'gamepad': {'button': 5},           # R1/RB Button
            'hardware': 'FIRE'                  # Hardware Button "FIRE"
        },
        'magic_water': {
            'keyboard': [pygame.K_1],           # Taste 1  
            'gamepad': {'button': 4},           # L1/LB Button
            'hardware': 'WATER'                 # Hardware Button "WATER"
        },
        'magic_stone': {
            'keyboard': [pygame.K_3],           # Taste 3
            'gamepad': {'button': 6},           # Back/Select Button
            'hardware': 'STONE'                 # Hardware Button "STONE"
        },
        'cast_magic': {
            'keyboard': [pygame.K_c, pygame.K_SPACE],  # C oder Space
            'gamepad': {'button': 0},                  # A/X Button
            'hardware': 'CAST'                         # Hardware Button "CAST"
        },
        'clear_magic': {
            'keyboard': [pygame.K_x, pygame.K_BACKSPACE],  # X oder Backspace
            'gamepad': {'button': 1},                      # B/Circle Button
            'hardware': 'CLEAR'                            # Hardware Button "CLEAR"
        },
        
        # System Actions
        'attack': {
            'keyboard': [pygame.K_SPACE],
            'gamepad': {'button': 0},           # A/X Button
            'hardware': None
        },
        'pause': {
            'keyboard': [pygame.K_ESCAPE],
            'gamepad': {'button': 7},           # Start/Options Button
            'hardware': None
        },
        'music_toggle': {
            'keyboard': [pygame.K_m],
            'gamepad': {'button': 2},           # X/Square Button
            'hardware': None
        },
        'reset_game': {
            'keyboard': [pygame.K_r],
            'gamepad': {'button': 3},           # Y/Triangle Button
            'hardware': None
        },
        
        # Debug
        'toggle_debug': {
            'keyboard': [pygame.K_F1],
            'gamepad': None,
            'hardware': None
        },
        'toggle_fps': {
            'keyboard': [pygame.K_F3],
            'gamepad': None,
            'hardware': None
        }
    }
    
    # Source Priority (höchste zu niedrigste)
    INPUT_SOURCE_PRIORITY = ['hardware', 'gamepad', 'keyboard']
    
    # Hardware-spezifische Einstellungen
    HARDWARE_CONFIG = {
        'port': '/dev/ttyUSB0',              # Standard serieller Port (Linux/Pi)
        'baud_rate': 115200,                 # Baudrate für ESP32
        'mock_mode': True,                   # Entwicklungsmodus ohne echte Hardware
        'heartbeat_timeout': 3.0,            # Sekunden bis Hardware als getrennt gilt
        'joystick_deadzone': 0.1,           # Deadzone für Hardware-Joystick
        'auto_reconnect': True,              # Automatischer Reconnect-Versuch
        'debug_logging': False               # Debug-Ausgaben für Hardware-Events
    }

class GameConfig:
    """Spiel-spezifische Konfiguration"""
    TITLE = "🧙‍♂️ Der Alchemist"
    MAX_INGREDIENTS = 5
    MUSIC_VOLUME = 0.7
    
    # Debug Einstellungen
    DEBUG_MODE = True
    SHOW_FPS = True
    SHOW_COLLISION_BOXES = False
    SHOW_SPAWN_INFO = True
    # Anzeige von Item-Namen über Sammelobjekten
    SHOW_ITEM_NAMES = True
    
    @property
    def GROUND_Y_POSITION(self):
        return 1080 - 200  # SCREEN_HEIGHT - 200

class SpellConfig:
    """Zauberspruch-System Konfiguration basierend auf Element-Mischungen"""
    DEFAULT_COOLDOWN = 3.0  # 3 seconds default cooldown
    
    # UI Configuration for spell bar - Dynamisch basierend auf Bildschirmgröße
    @staticmethod
    def get_bar_config():
        """Gibt Spell Bar Konfiguration basierend auf Bildschirmgröße zurück"""
        ui_settings = UIConfig.get_ui_settings()
        display_settings = DisplayConfig.get_optimized_settings()
        
        # Für 7-Zoll Displays (1024x600) kompaktere Anordnung
        if display_settings.get('WINDOW_HEIGHT', 720) <= 600:
            return {
                'BAR_POSITION': (10, -80),  # Höher positioniert für 7-Zoll
                'SLOT_SIZE': ui_settings['SPELL_SLOT_SIZE'],
                'SLOT_SPACING': ui_settings['SPELL_SLOT_SPACING'], 
                'BACKGROUND_PADDING': ui_settings['HOTKEY_PADDING'],
                'BACKGROUND_ALPHA': 200,  # Etwas undurchsichtiger für bessere Sichtbarkeit
            }
        else:
            return {
                'BAR_POSITION': (20, -120),  # Standard Position
                'SLOT_SIZE': ui_settings['SPELL_SLOT_SIZE'],
                'SLOT_SPACING': ui_settings['SPELL_SLOT_SPACING'],
                'BACKGROUND_PADDING': ui_settings['HOTKEY_PADDING'],
                'BACKGROUND_ALPHA': 180,
            }
    
    # Magic combination definitions (based on existing magic system)
    MAGIC_COMBINATIONS = {
        # Fire + Fire = Fireball
        ('fire', 'fire'): {
            "id": "fireball", 
            "display_name": "Feuerball", 
            "icon_path": "ui/spells/fireball.png", 
            "cooldown": 3.0,
            "elements": ["feuer", "feuer"]
        },
        # Water + Water = Waterbolt
        ('water', 'water'): {
            "id": "waterbolt", 
            "display_name": "Wasserkugel", 
            "icon_path": "ui/spells/waterbolt.png", 
            "cooldown": 3.0,
            "elements": ["wasser", "wasser"],
            "sound": "spells/combos/splash-by-blaukreuz-6261.mp3"
        },
        # Stone + Stone = Shield
        ('stone', 'stone'): {
            "id": "shield", 
            "display_name": "Schutzschild", 
            "icon_path": "ui/spells/shield.png", 
            "cooldown": 3.0,
            "elements": ["stein", "stein"],
            "sound": "spells/combos/block-6839.mp3"
        },
        # Fire + Water = Healing (both orders)
        ('fire', 'water'): {
            "id": "healing", 
            "display_name": "Heilungstrank", 
            "icon_path": "ui/spells/healing.png", 
            "cooldown": 3.0,
            "elements": ["feuer", "wasser"],
            "sound": "spells/combos/healing-magic-1-378665.mp3"
        },
        ('water', 'fire'): {
            "id": "healing", 
            "display_name": "Heilungstrank", 
            "icon_path": "ui/spells/healing.png", 
            "cooldown": 3.0,
            "elements": ["wasser", "feuer"],
            "sound": "spells/combos/healing-magic-1-378665.mp3"
        },
        # Fire + Stone = Whirlwind (both orders)
        ('fire', 'stone'): {
            "id": "whirlwind", 
            "display_name": "Wirbelattacke", 
            "icon_path": "ui/spells/whirlwind.png", 
            "cooldown": 3.0,
            "elements": ["feuer", "stein"],
            "sound": "spells/combos/impact-109588.mp3"
        },
        ('stone', 'fire'): {
            "id": "whirlwind", 
            "display_name": "Wirbelattacke", 
            "icon_path": "ui/spells/whirlwind.png", 
            "cooldown": 3.0,
            "elements": ["stein", "feuer"],
            "sound": "spells/combos/impact-109588.mp3"
        },
        # Water + Stone = Invisibility (both orders)
        ('water', 'stone'): {
            "id": "invisibility", 
            "display_name": "Unsichtbarkeit", 
            "icon_path": "ui/spells/invisibility.png", 
            "cooldown": 3.0,
            "elements": ["wasser", "stein"],
            "sound": "spells/combos/Deep woosh1.wav"
        },
        ('stone', 'water'): {
            "id": "invisibility", 
            "display_name": "Unsichtbarkeit", 
            "icon_path": "ui/spells/invisibility.png", 
            "cooldown": 3.0,
            "elements": ["stein", "wasser"],
            "sound": "spells/combos/Deep woosh1.wav"
        }
    }
    
    # Legacy spell list (for compatibility)
    SPELLS = [
        {"id": "fireball", "display_name": "Feuerball", "icon_path": "ui/spells/fireball.png", "cooldown": 3.0},
        {"id": "healing", "display_name": "Heilung", "icon_path": "ui/spells/healing.png", "cooldown": 3.0},
        {"id": "shield", "display_name": "Schild", "icon_path": "ui/spells/shield.png", "cooldown": 3.0},
        {"id": "whirlwind", "display_name": "Wirbel", "icon_path": "ui/spells/whirlwind.png", "cooldown": 3.0},
        {"id": "invisibility", "display_name": "Unsichtbar", "icon_path": "ui/spells/invisibility.png", "cooldown": 3.0},
        {"id": "waterbolt", "display_name": "Wasserkugel", "icon_path": "ui/spells/waterbolt.png", "cooldown": 3.0}
    ]
    
    # Legacy UI Properties für Kompatibilität
    @property
    def BAR_POSITION(self):
        return self.get_bar_config()['BAR_POSITION']
    
    @property  
    def SLOT_SIZE(self):
        return self.get_bar_config()['SLOT_SIZE']
        
    @property
    def SLOT_SPACING(self):
        return self.get_bar_config()['SLOT_SPACING']
        
    @property
    def BACKGROUND_PADDING(self):
        return self.get_bar_config()['BACKGROUND_PADDING']
        
    @property
    def BACKGROUND_ALPHA(self):
        return self.get_bar_config()['BACKGROUND_ALPHA']

# === SINGLETON PATTERN FÜR GLOBALE KONFIGURATION ===
class Config:
    """Singleton-Klasse für zentrale Konfiguration"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        self.display = DisplayConfig()
        self.ui = UIConfig()
        self.player = PlayerConfig()
        self.colors = Colors()
        self.paths = Paths()
        self.input = InputConfig()
        self.game = GameConfig()
        self.spells = SpellConfig()
        
        # Zutaten und Rezepte
        self.ingredient_colors = {
            "wasserkristall": self.colors.WASSERKRISTALL,
            "feueressenz": self.colors.FEUERESSENZ,
            "erdkristall": self.colors.ERDKRISTALL
        }
        
        self.recipes = {
            ("wasserkristall", "wasserkristall"): "💧 Feuer gelöscht! Ein starker Wasserzauber.",
            ("feueressenz", "wasserkristall"): "❤️ Heiltrank gebraut! Lebenspunkte wiederhergestellt.",
            ("erdkristall", "feueressenz"): "💥 Explosion! Das war die falsche Mischung.",
            ("wasserkristall", "erdkristall"): "🌱 Wachstumstrank! Pflanzen sprießen.",
            ("feueressenz", "feueressenz"): "🔥 Feuerball! Mächtiger Angriffszauber.",
            ("erdkristall", "erdkristall"): "🏔️ Steinwall! Schutz vor Angriffen."
        }
        
        self._initialized = True

# Globale Konfiguration-Instanz
config = Config()

# === KOMPATIBILITÄTS-EXPORTE ===
# Für Rückwärtskompatibilität exportieren wir die wichtigsten Konstanten
SCREEN_WIDTH = config.display.SCREEN_WIDTH
SCREEN_HEIGHT = config.display.SCREEN_HEIGHT
WINDOW_WIDTH = config.display.WINDOW_WIDTH
WINDOW_HEIGHT = config.display.WINDOW_HEIGHT
FPS = config.display.FPS

PLAYER_SPEED = config.player.SPEED
PLAYER_SIZE = config.player.SIZE
PLAYER_START_X = config.player.START_POS[0]
PLAYER_START_Y = config.player.START_POS[1]
PLAYER_SPRITE_WIDTH = config.player.SPRITE_WIDTH
PLAYER_SPRITE_HEIGHT = config.player.SPRITE_HEIGHT
ANIMATION_SPEED = config.player.ANIMATION_SPEED
ANIMATION_SPEEDS = config.player.ANIMATION_SPEEDS

MAX_INGREDIENTS = config.game.MAX_INGREDIENTS
GROUND_Y_POSITION = config.game.GROUND_Y_POSITION
MUSIC_VOLUME = config.game.MUSIC_VOLUME

INGREDIENT_COLORS = config.ingredient_colors
RECIPES = config.recipes

# Neue Spell-Konfiguration Exporte
DEFAULT_COOLDOWN = config.spells.DEFAULT_COOLDOWN
SPELL_KEYS = config.input.SPELL_KEYS

# Alte Klassen für Kompatibilität
Colors = config.colors
Paths = config.paths

# Neue Klassen-Aliase
PlayerConfig = config.player
WindowConfig = config.display
