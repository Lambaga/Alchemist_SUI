# -*- coding: utf-8 -*-
# src/asset_manager.py
"""
Zentrales Asset-Management für bessere Performance
"""

import pygame
import os
from typing import Dict, List, Tuple
import json

class ScaledSpriteCache:
    """LRU Cache für skalierte Sprites um teure transform.scale() Operationen zu vermeiden"""
    
    def __init__(self, max_cache_size: int = 100):
        self.cache = {}
        self.access_order = []  # Für LRU tracking
        self.max_size = max_cache_size
    
    def get_scaled(self, original: pygame.Surface, size: Tuple[int, int]) -> pygame.Surface:
        """
        Gibt skalierte Version zurück - cached für Performance
        :param original: Original Surface
        :param size: Zielgröße (width, height)
        :return: Skalierte Surface
        """
        cache_key = (id(original), size)
        
        if cache_key in self.cache:
            # Move to end (most recently used)
            self.access_order.remove(cache_key)
            self.access_order.append(cache_key)
            return self.cache[cache_key]
        
        # Nicht im Cache - skaliere und cache
        if len(self.cache) >= self.max_size:
            # LRU: Entferne ältesten Eintrag
            oldest_key = self.access_order.pop(0)
            del self.cache[oldest_key]
        
        # Erstelle skalierte Version
        scaled_surface = pygame.transform.scale(original, size)
        self.cache[cache_key] = scaled_surface
        self.access_order.append(cache_key)
        
        return scaled_surface
    
    def clear(self):
        """Leert den gesamten Cache"""
        self.cache.clear()
        self.access_order.clear()
    
    def get_cache_info(self) -> Dict[str, int]:
        """Cache-Statistiken für Debugging"""
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'hit_ratio': 0  # TODO: Implementiere hit/miss tracking wenn benötigt
        }

class AssetManager:
    """Zentrales Asset-Management für bessere Performance"""
    
    _instance = None
    # 🚀 RPi-Optimierung: LRU-Limits für Memory-Management
    MAX_IMAGES_CACHE = 200
    MAX_ANIMATIONS_CACHE = 50
    MAX_SOUNDS_CACHE = 30
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._images = {}
            cls._instance._images_lru = []  # LRU tracking für images
            cls._instance._sounds = {}
            cls._instance._sounds_lru = []  # LRU tracking für sounds
            cls._instance._animations = {}
            cls._instance._animations_lru = []  # LRU tracking für animations
            cls._instance._sprite_cache = ScaledSpriteCache(max_cache_size=150)
        return cls._instance
    
    def load_image(self, path: str, cache_key: str = None) -> pygame.Surface:
        """Lädt ein Bild und cached es mit LRU-Eviction"""
        key = cache_key or path
        
        if key in self._images:
            # LRU: Move to end (most recently used)
            if key in self._images_lru:
                self._images_lru.remove(key)
            self._images_lru.append(key)
            return self._images[key]
        
        # 🚀 RPi-Optimierung: LRU-Eviction wenn Cache voll
        while len(self._images) >= self.MAX_IMAGES_CACHE and self._images_lru:
            oldest_key = self._images_lru.pop(0)
            if oldest_key in self._images:
                del self._images[oldest_key]
        
        try:
            self._images[key] = pygame.image.load(path).convert_alpha()
        except pygame.error as e:
            print(f"Fehler beim Laden von {path}: {e}")
            # Erstelle Placeholder
            self._images[key] = self._create_placeholder()
        
        self._images_lru.append(key)
        return self._images[key]
    
    def load_animation_set(self, config_file: str) -> Dict[str, List[pygame.Surface]]:
        """Lädt Animationen basierend auf JSON-Konfiguration mit LRU-Eviction"""
        if config_file in self._animations:
            # LRU: Move to end (most recently used)
            if config_file in self._animations_lru:
                self._animations_lru.remove(config_file)
            self._animations_lru.append(config_file)
            return self._animations[config_file]
        
        # 🚀 RPi-Optimierung: LRU-Eviction wenn Cache voll
        while len(self._animations) >= self.MAX_ANIMATIONS_CACHE and self._animations_lru:
            oldest_key = self._animations_lru.pop(0)
            if oldest_key in self._animations:
                del self._animations[oldest_key]
        
        with open(config_file, 'r') as f:
            anim_config = json.load(f)
        
        animations = {}
        for anim_name, anim_data in anim_config.items():
            frames = []
            spritesheet = self.load_image(anim_data['path'])
            
            for frame_idx in range(anim_data['frame_count']):
                x = frame_idx * anim_data['frame_width']
                frame = spritesheet.subsurface(
                    x, 0, anim_data['frame_width'], anim_data['frame_height']
                )
                frames.append(frame)
            
            animations[anim_name] = frames
        
        self._animations[config_file] = animations
        self._animations_lru.append(config_file)
        return animations
    
    def load_sound(self, path: str, cache_key: str = None) -> pygame.mixer.Sound:
        """Lädt einen Sound und cached ihn mit LRU-Eviction"""
        key = cache_key or path
        
        if key in self._sounds:
            # LRU: Move to end (most recently used)
            if key in self._sounds_lru:
                self._sounds_lru.remove(key)
            self._sounds_lru.append(key)
            return self._sounds[key]
        
        # 🚀 RPi-Optimierung: LRU-Eviction wenn Cache voll
        while len(self._sounds) >= self.MAX_SOUNDS_CACHE and self._sounds_lru:
            oldest_key = self._sounds_lru.pop(0)
            if oldest_key in self._sounds:
                del self._sounds[oldest_key]
        
        try:
            self._sounds[key] = pygame.mixer.Sound(path)
        except pygame.error as e:
            print(f"Fehler beim Laden von Sound {path}: {e}")
            return None
        
        self._sounds_lru.append(key)
        return self._sounds[key]
    
    def _create_placeholder(self, width: int = 32, height: int = 32) -> pygame.Surface:
        """Erstellt ein Placeholder-Bild wenn das Original nicht geladen werden kann"""
        surface = pygame.Surface((width, height))
        surface.fill((255, 0, 255))  # Magenta als Placeholder-Farbe
        return surface
    
    def get_cached_image(self, cache_key: str) -> pygame.Surface:
        """Gibt ein bereits gecachtes Bild zurück"""
        return self._images.get(cache_key)
    
    def get_cached_sound(self, cache_key: str) -> pygame.mixer.Sound:
        """Gibt einen bereits gecachten Sound zurück"""
        return self._sounds.get(cache_key)
    
    def clear_cache(self):
        """Leert den gesamten Cache inkl. LRU-Tracking"""
        self._images.clear()
        self._images_lru.clear()
        self._sounds.clear()
        self._sounds_lru.clear()
        self._animations.clear()
        self._animations_lru.clear()
        self._sprite_cache.clear()
    
    def get_memory_usage(self) -> Dict[str, int]:
        """Gibt Informationen über die Cache-Nutzung zurück"""
        return {
            'images': len(self._images),
            'sounds': len(self._sounds),
            'animations': len(self._animations),
            'scaled_sprites': len(self._sprite_cache.cache)
        }
    
    def get_scaled_sprite(self, original: pygame.Surface, size: Tuple[int, int]) -> pygame.Surface:
        """
        Performance-optimierte Sprite-Skalierung mit Caching
        Verhindert teure pygame.transform.scale() Operationen pro Frame
        
        :param original: Original Surface
        :param size: Zielgröße (width, height)
        :return: Skalierte und gecachte Surface
        """
        return self._sprite_cache.get_scaled(original, size)
    
    def clear_sprite_cache(self):
        """Leert nur den Sprite-Skalierungs-Cache"""
        self._sprite_cache.clear()
    
    def get_sprite_cache_info(self) -> Dict[str, int]:
        """Sprite-Cache Statistiken für Performance-Monitoring"""
        return self._sprite_cache.get_cache_info()
    
    def load_spritesheet_frames(self, spritesheet_path: str, num_frames: int, 
                               frame_width: int = None, frame_height: int = None,
                               scale_to: tuple = None) -> List[pygame.Surface]:
        """
        Lädt Frames aus einem Spritesheet und cached sie
        :param spritesheet_path: Pfad zum Spritesheet
        :param num_frames: Anzahl der Frames
        :param frame_width: Breite eines Frames (auto-detect wenn None)
        :param frame_height: Höhe eines Frames (auto-detect wenn None)
        :param scale_to: Zielgröße (width, height) für Skalierung
        """
        cache_key = f"{spritesheet_path}_frames_{num_frames}_{frame_width}_{frame_height}_{scale_to}"
        
        if cache_key in self._animations:
            return self._animations[cache_key]
        
        frames = []
        try:
            spritesheet = self.load_image(spritesheet_path)
            
            # Auto-detect frame dimensions if not provided
            if frame_width is None:
                frame_width = spritesheet.get_width() // num_frames
            if frame_height is None:
                frame_height = spritesheet.get_height()
            
            for i in range(num_frames):
                x = i * frame_width
                frame_surface = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
                frame_surface.blit(spritesheet, (0, 0), (x, 0, frame_width, frame_height))
                
                # Scale if requested
                if scale_to:
                    frame_surface = pygame.transform.scale(frame_surface, scale_to)
                
                frames.append(frame_surface)
        
        except Exception as e:
            print(f"Fehler beim Laden der Spritesheet-Frames von {spritesheet_path}: {e}")
            # Create placeholder frames
            placeholder_size = scale_to or (32, 32)
            for _ in range(num_frames):
                frames.append(self._create_placeholder(placeholder_size[0], placeholder_size[1]))
        
        self._animations[cache_key] = frames
        return frames
    
    def load_individual_frames(self, frame_paths: List[str], scale_to: tuple = None) -> List[pygame.Surface]:
        """
        Lädt individuelle Frame-Dateien und cached sie
        :param frame_paths: Liste von Pfaden zu einzelnen Frame-Dateien
        :param scale_to: Zielgröße (width, height) für Skalierung
        """
        cache_key = f"individual_{hash(tuple(frame_paths))}_{scale_to}"
        
        if cache_key in self._animations:
            return self._animations[cache_key]
        
        frames = []
        for frame_path in frame_paths:
            try:
                frame = self.load_image(frame_path)
                if scale_to:
                    frame = pygame.transform.scale(frame, scale_to)
                frames.append(frame)
            except Exception as e:
                print(f"Fehler beim Laden von Frame {frame_path}: {e}")
                placeholder_size = scale_to or (32, 32)
                frames.append(self._create_placeholder(placeholder_size[0], placeholder_size[1]))
        
        self._animations[cache_key] = frames
        return frames
    
    def load_entity_animation(self, entity_type: str, animation_name: str, 
                             asset_path: str, scale_factor: float = 1.0) -> List[pygame.Surface]:
        """
        Lädt Animation basierend auf vordefinierter Konfiguration
        :param entity_type: Typ der Entity (z.B. 'player', 'demon', 'fireworm')
        :param animation_name: Name der Animation (z.B. 'idle', 'run', 'attack')
        :param asset_path: Basis-Pfad zu den Assets
        :param scale_factor: Skalierungsfaktor für die Sprites
        """
        try:
            from asset_config import get_animation_config
            import os
            
            config = get_animation_config(entity_type, animation_name)
            if not config:
                print(f"⚠️ Keine Animation-Konfiguration für {entity_type}.{animation_name}")
                return [self._create_placeholder()]
            
            # Individuelle Dateien (z.B. Demon Idle1.png, Idle2.png, etc.)
            if config.get('type') == 'individual':
                frame_paths = [os.path.join(asset_path, filename) for filename in config['files']]
                target_size = None
                if scale_factor != 1.0:
                    # Berechne Zielgröße vom ersten verfügbaren Frame
                    for frame_path in frame_paths:
                        if os.path.exists(frame_path):
                            first_frame = self.load_image(frame_path)
                            target_size = (int(first_frame.get_width() * scale_factor),
                                         int(first_frame.get_height() * scale_factor))
                            break
                
                return self.load_individual_frames(frame_paths, target_size)
            
            # Spritesheet-Dateien (z.B. Player Idle.png mit mehreren Frames)
            else:
                frame_path = os.path.join(asset_path, config['file'])
                num_frames = config['frames']
                frame_width = config.get('frame_width')
                frame_height = config.get('frame_height')
                
                target_size = config.get('scale_to')
                if not target_size and scale_factor != 1.0:
                    # Auto-berechne Zielgröße basierend auf Original und Skalierungsfaktor
                    if os.path.exists(frame_path):
                        temp_sheet = self.load_image(frame_path)
                        orig_width = frame_width or temp_sheet.get_width() // num_frames
                        orig_height = frame_height or temp_sheet.get_height()
                        target_size = (int(orig_width * scale_factor), int(orig_height * scale_factor))
                
                return self.load_spritesheet_frames(
                    frame_path, num_frames, frame_width, frame_height, target_size
                )
                
        except ImportError:
            print("⚠️ asset_config.py nicht verfügbar, verwende Fallback-Methode")
            return [self._create_placeholder()]
        except Exception as e:
            print(f"❌ Fehler beim Laden der Entity-Animation {entity_type}.{animation_name}: {e}")
            return [self._create_placeholder()]
