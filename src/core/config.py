# -*- coding: utf-8 -*-
# src/config.py
"""
Modernisierte zentrale Konfigurationsdatei für Das Alchemist Spiel
Verwendet Klassen-basierte Organisation für bessere Struktur
"""

import pygame
from os import path

# === PFAD DEFINITIONEN (ROBUST) ===
SRC_DIR = path.dirname(path.dirname(__file__))  # Go up one more level since we're in core/
ROOT_DIR = path.join(SRC_DIR, '..')
ASSETS_DIR = path.join(ROOT_DIR, 'assets')

class DisplayConfig:
    """Display- und Fenster-Konfiguration"""
    SCREEN_WIDTH = 1920
    SCREEN_HEIGHT = 1080
    WINDOW_WIDTH = 1280
    WINDOW_HEIGHT = 720
    FPS = 60

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
        self.ASSETS = "assets"
        self.SPRITES = "assets/Wizard Pack"
        self.MAPS = "assets/maps"
        self.SOUNDS = "assets/sounds"
        self.MUSIC_KOROL = "assets/sounds/korol.mp3"
    
    @property
    def BACKGROUND_MUSIC(self):
        return path.join(self.SOUNDS_DIR, "korol.mp3")
    
    @property
    def DEFAULT_MAP(self):
        return path.join(self.MAPS_DIR, "Map2.tmx")

class InputConfig:
    """Input-Konfiguration"""
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
    
    @property
    def GROUND_Y_POSITION(self):
        return 1080 - 200  # SCREEN_HEIGHT - 200

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
        self.player = PlayerConfig()
        self.colors = Colors()
        self.paths = Paths()
        self.input = InputConfig()
        self.game = GameConfig()
        
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

# Alte Klassen für Kompatibilität
Colors = config.colors
Paths = config.paths

# Neue Klassen-Aliase
PlayerConfig = config.player
WindowConfig = config.display
