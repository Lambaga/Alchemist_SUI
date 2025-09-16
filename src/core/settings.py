# -*- coding: utf-8 -*-
# src/settings.py
"""
Kompatibilitäts-Wrapper für die modernisierte Konfiguration
Importiert alle Werte aus der neuen config.py für Rückwärtskompatibilität
"""

import pygame
from os import path

# Importiere die neue modernisierte Konfiguration
from config import config

# === PFAD DEFINITIONEN (aus der neuen config.py) ===
SRC_DIR = config.paths.ROOT_DIR + '/src'
ROOT_DIR = config.paths.ROOT_DIR
ASSETS_DIR = config.paths.ASSETS_DIR
MAP_DIR = config.paths.MAPS_DIR
SOUND_DIR = config.paths.SOUNDS_DIR
SPRITES_DIR = config.paths.SPRITES_DIR

# === BILDSCHIRM EINSTELLUNGEN ===
SCREEN_WIDTH = config.display.SCREEN_WIDTH
SCREEN_HEIGHT = config.display.SCREEN_HEIGHT
WINDOW_WIDTH = config.display.WINDOW_WIDTH
WINDOW_HEIGHT = config.display.WINDOW_HEIGHT
FPS = config.display.FPS

# === SPIEL EINSTELLUNGEN ===
GAME_TITLE = config.game.TITLE

# === MUSIK ===
BACKGROUND_MUSIC = config.paths.BACKGROUND_MUSIC
MUSIC_VOLUME = config.game.MUSIC_VOLUME

# === FARBEN ===
BACKGROUND_COLOR = config.colors.BACKGROUND
TEXT_COLOR = config.colors.TEXT
UI_BACKGROUND = config.colors.UI_BACKGROUND

# === PLAYER EINSTELLUNGEN ===
PLAYER_SPEED = config.player.SPEED
PLAYER_SIZE = config.player.SIZE
PLAYER_START_POS = config.player.START_POS

# === INPUT EINSTELLUNGEN ===
MOVEMENT_KEYS = config.input.MOVEMENT_KEYS
ACTION_KEYS = config.input.ACTION_KEYS

# === DEBUG EINSTELLUNGEN ===
DEBUG_MODE = config.game.DEBUG_MODE
SHOW_FPS = config.game.SHOW_FPS
SHOW_COLLISION_BOXES = config.game.SHOW_COLLISION_BOXES
SHOW_SPAWN_INFO = config.game.SHOW_SPAWN_INFO
SHOW_ITEM_NAMES = config.game.SHOW_ITEM_NAMES

# === MANA SYSTEM EINSTELLUNGEN ===
MANA_MAX = 100
MANA_REGEN_PER_SEC = 3
MANA_SPELL_COST = 10

# === SPELL SYSTEM EINSTELLUNGEN ===
DEFAULT_COOLDOWN = config.spells.DEFAULT_COOLDOWN
SPELL_KEYS = config.input.SPELL_KEYS

# === ZUGRIFF AUF DIE NEUE KONFIGURATION ===
# Für moderneren Code kann direkt die config-Instanz verwendet werden:
# from settings import config
# config.display.SCREEN_WIDTH
# config.player.SPEED
# config.colors.BACKGROUND
# etc.
