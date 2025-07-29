# src/config.py
"""
Zentrale Konfigurationsdatei für Das Alchemist Spiel
"""

# === DISPLAY EINSTELLUNGEN ===
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
FPS = 60

# === SPIELER EINSTELLUNGEN ===
PLAYER_SPEED = 4
PLAYER_SIZE = (48, 64)  # (width, height)
PLAYER_START_X = 960
PLAYER_START_Y = 500

# === ANIMATION EINSTELLUNGEN ===
# Player-Konfiguration
PLAYER_SPEED = 4
PLAYER_SPRITE_WIDTH = 48
PLAYER_SPRITE_HEIGHT = 64
ANIMATION_SPEED = 0.15
ANIMATION_SPEEDS = {
    "idle": 120,
    "run": 80
}

# === FARBEN ===
class Colors:
    # UI Farben
    BACKGROUND = (25, 25, 50)
    BACKGROUND_BLUE = (25, 25, 50)  # Alias
    TEXT = (255, 255, 255)
    WHITE = (255, 255, 255)  # Alias
    UI_BACKGROUND = (50, 50, 80)
    
    # Spielwelt Farben
    PLAYER = (100, 255, 100)
    PLAYER_GREEN = (100, 255, 100)  # Alias
    PLACEHOLDER_GREEN = (100, 255, 100)  # Alias
    GROUND = (139, 69, 19)
    SKY = (135, 206, 235)
    TREE = (34, 139, 34)
    
    # Zutaten Farben
    WASSERKRISTALL = (0, 150, 255)
    FEUERESSENZ = (255, 100, 0)
    ERDKRISTALL = (139, 69, 19)
    
    # Standardfarben
    BLACK = (0, 0, 0)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)
    YELLOW = (255, 255, 0)
    MAGENTA = (255, 0, 255)
    CYAN = (0, 255, 255)

# === KLASSEN FÜR ORGANISIERTE KONFIGURATION ===

class PlayerConfig:
    """Player-spezifische Konfiguration"""
    SPEED = PLAYER_SPEED
    SPRITE_WIDTH = PLAYER_SPRITE_WIDTH
    SPRITE_HEIGHT = PLAYER_SPRITE_HEIGHT
    FRAME_WIDTH = PLAYER_SPRITE_WIDTH
    FRAME_HEIGHT = PLAYER_SPRITE_HEIGHT
    ANIMATION_SPEED = ANIMATION_SPEED
    ANIMATION_SPEED_MS = ANIMATION_SPEEDS

class WindowConfig:
    """Fenster- und Bildschirm-Konfiguration"""
    SCREEN_WIDTH = SCREEN_WIDTH
    SCREEN_HEIGHT = SCREEN_HEIGHT
    WINDOW_WIDTH = WINDOW_WIDTH
    WINDOW_HEIGHT = WINDOW_HEIGHT
    FPS = FPS

# === PFADE ===
class Paths:
    ASSETS = "assets"
    SPRITES = "assets/Wizard Pack"
    MAPS = "assets/maps"
    SOUNDS = "assets/sounds"
    
    # Spezifische Dateien
    BACKGROUND_MUSIC = "assets/sounds/korol.mp3"
    MUSIC_KOROL = "assets/sounds/korol.mp3"  # Alias für Kompatibilität
    DEFAULT_MAP = "assets/maps/Map1.tmx"

# === SPIEL EINSTELLUNGEN ===
MAX_INGREDIENTS = 5
GROUND_Y_POSITION = SCREEN_HEIGHT - 200
MUSIC_VOLUME = 0.7

# === ZUTATEN ===
INGREDIENT_COLORS = {
    "wasserkristall": Colors.WASSERKRISTALL,
    "feueressenz": Colors.FEUERESSENZ,
    "erdkristall": Colors.ERDKRISTALL
}

# === REZEPTE ===
RECIPES = {
    ("wasserkristall", "wasserkristall"): "💧 Feuer gelöscht! Ein starker Wasserzauber.",
    ("feueressenz", "wasserkristall"): "❤️ Heiltrank gebraut! Lebenspunkte wiederhergestellt.",
    ("erdkristall", "feueressenz"): "💥 Explosion! Das war die falsche Mischung.",
    ("wasserkristall", "erdkristall"): "🌱 Wachstumstrank! Pflanzen sprießen.",
    ("feueressenz", "feueressenz"): "🔥 Feuerball! Mächtiger Angriffszauber.",
    ("erdkristall", "erdkristall"): "🏔️ Steinwall! Schutz vor Angriffen."
}
