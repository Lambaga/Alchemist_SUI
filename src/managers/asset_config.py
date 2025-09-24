# -*- coding: utf-8 -*-
# src/asset_config.py
"""
Asset-Konfiguration für Das Alchemist Spiel
Definiert standardisierte Asset-Loading-Parameter
"""

from config import config

# Asset-Pfade
ASSET_PATHS = {
    'player': config.paths.SPRITES_DIR,
    'demon': config.paths.ASSETS_DIR + '/Demon Pack',
    'fireworm': config.paths.ASSETS_DIR + '/fireWorm',
    'maps': config.paths.MAPS_DIR,
    'sounds': config.paths.SOUNDS_DIR,
}

# Animation-Konfigurationen
ANIMATION_CONFIGS = {
    'player': {
        'idle': {
            'file': 'Idle.png',
            'frames': 6,
            'frame_width': None,  # Auto-detect
            'frame_height': None,  # Auto-detect
            'scale_to': config.player.SIZE
        },
        'run': {
            'file': 'Run.png',
            'frames': 8,
            'frame_width': None,  # Auto-detect
            'frame_height': None,  # Auto-detect
            'scale_to': config.player.SIZE
        }
    },
    
    'demon': {
        'idle': {
            'type': 'individual',  # Einzelne Dateien statt Spritesheet
            'files': ['Idle1.png', 'Idle2.png', 'Idle3.png', 'Idle4.png'],
            'scale_factor': 1.0  # Wird von Enemy-Instanz überschrieben
        },
        'run': {
            'type': 'individual',
            'files': ['big_demon_run_anim_f0.png', 'big_demon_run_anim_f1.png', 
                     'big_demon_run_anim_f2.png', 'big_demon_run_anim_f3.png'],
            'scale_factor': 1.0
        }
    },
    
    'fireworm': {
        'idle': {
            'file': 'Idle.png',
            'frames': 9,
            'frame_width': 90,
            'frame_height': 90,
            'scale_factor': 1.0
        },
        'walk': {
            'file': 'Walk.png',
            'frames': 9,
            'frame_width': 90,
            'frame_height': 90,
            'scale_factor': 1.0
        },
        'attack': {
            'file': 'Attack.png',
            'frames': 16,
            'frame_width': 90,
            'frame_height': 90,
            'scale_factor': 1.0
        },
        'death': {
            'file': 'Death.png',
            'frames': 8,
            'frame_width': 90,
            'frame_height': 90,
            'scale_factor': 1.0
        }
    },
    
    'fireball': {
        'move': {
            'file': 'Move.png',
            'frames': 5,
            'frame_width': None,  # Auto-detect
            'frame_height': None,  # Auto-detect
            'scale_factor': 1.0
        },
        'explosion': {
            'file': 'Explosion.png',
            'frames': 1,  # Single frame
            'scale_factor': 1.0
        }
    }
}

# Sound-Konfigurationen
SOUND_CONFIGS = {
    'background_music': {
        'file': 'Mystic Brew (Cozy Battle Alchemist Remix).mp3',
        'volume': config.game.MUSIC_VOLUME,
        'loop': True
    }
}

def get_asset_path(entity_type: str) -> str:
    """Gibt den Asset-Pfad für einen Entity-Typ zurück"""
    return ASSET_PATHS.get(entity_type, '')

def get_animation_config(entity_type: str, animation_name: str) -> dict:
    """Gibt die Animation-Konfiguration für einen Entity-Typ und Animation zurück"""
    entity_config = ANIMATION_CONFIGS.get(entity_type, {})
    return entity_config.get(animation_name, {})

def get_sound_config(sound_name: str) -> dict:
    """Gibt die Sound-Konfiguration für einen Sound-Namen zurück"""
    return SOUND_CONFIGS.get(sound_name, {})
