# src/settings.py
# Zentrale Einstellungen für das gesamte Spiel
import pygame
from os import path

# === PFAD DEFINITIONEN (ROBUST) ===
# __file__ ist der Pfad zur aktuellen Datei (settings.py)
# path.dirname() holt das Verzeichnis davon (der 'src' Ordner)
# path.join() fügt Verzeichnisse plattformunabhängig zusammen
SRC_DIR = path.dirname(__file__)
ROOT_DIR = path.join(SRC_DIR, '..') # Geht ein Verzeichnis hoch zum Projekt-Root
ASSETS_DIR = path.join(ROOT_DIR, 'assets')
MAP_DIR = path.join(ASSETS_DIR, 'maps')
SOUND_DIR = path.join(ASSETS_DIR, 'sounds')
SPRITES_DIR = path.join(ASSETS_DIR, 'Wizard Pack')

# === BILDSCHIRM EINSTELLUNGEN ===
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
WINDOW_WIDTH = 1280   
WINDOW_HEIGHT = 720   
FPS = 60

# === SPIEL EINSTELLUNGEN ===
GAME_TITLE = "🧙‍♂️ Der Alchemist"

# === PFADE (veraltet, jetzt oben definiert) ===
# ASSETS_PATH = "assets"
# MAPS_PATH = "assets/maps"
# SOUNDS_PATH = "assets/sounds"
# SPRITES_PATH = "assets/Wizard Pack"

# === MUSIK ===
BACKGROUND_MUSIC = path.join(SOUND_DIR, "korol.mp3")
MUSIC_VOLUME = 0.7

# === FARBEN ===
BACKGROUND_COLOR = (25, 25, 50)
TEXT_COLOR = (255, 255, 255)
UI_BACKGROUND = (50, 50, 80)

# === PLAYER EINSTELLUNGEN ===
PLAYER_SPEED = 4
PLAYER_SIZE = (96, 128)  # 2 Tile-Blöcke
PLAYER_START_POS = (960, 500)

# === KAMERA EINSTELLUNGEN ===
DEFAULT_ZOOM = 2.0
MIN_ZOOM = 1.0
MAX_ZOOM = 4.0
ZOOM_STEP = 0.2

# === INPUT EINSTELLUNGEN ===
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
    'zoom_in': [pygame.K_PLUS, pygame.K_EQUALS],
    'zoom_out': pygame.K_MINUS,
    'quit': pygame.K_ESCAPE
}

# === DEBUG EINSTELLUNGEN ===
DEBUG_MODE = True
SHOW_FPS = True
SHOW_COLLISION_BOXES = False
SHOW_SPAWN_INFO = True  # Zeigt Spawn-Informationen
