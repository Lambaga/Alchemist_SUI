# -*- coding: utf-8 -*-
"""
Erweiterte Sprite-Gruppen mit Layer-Support und optimierter Kamera-Integration
"""

import pygame
from typing import Optional, Any, Tuple
from .camera import Camera


class LayeredSpriteGroup(pygame.sprite.LayeredUpdates):
    """
    Erweiterte Sprite-Gruppe mit Layer-Support und Kamera-Integration
    
    Bietet optimiertes Rendering mit Kamera-Transformation und
    Delta-Time basierte Updates für konsistente Performance.
    """
    
    def __init__(self, *sprites, **kwargs):
        """
        Initialisiert die LayeredSpriteGroup
        
        Args:
            *sprites: Sprites, die initial hinzugefügt werden sollen
            **kwargs: Zusätzliche Parameter für pygame.sprite.LayeredUpdates
        """
        super().__init__(*sprites, **kwargs)
        self._visible_sprites_cache = []
        self._cache_dirty = True
        
    def add(self, *sprites, **kwargs):
        """Fügt Sprites hinzu und markiert Cache als dirty"""
        super().add(*sprites, **kwargs)
        self._cache_dirty = True
    
    def remove(self, *sprites):
        """Entfernt Sprites und markiert Cache als dirty"""
        super().remove(*sprites)
        self._cache_dirty = True
    
    def draw_with_camera(self, surface: pygame.Surface, camera: Camera) -> None:
        """
        Zeichnet alle sichtbaren Sprites mit Kamera-Transformation
        
        Args:
            surface: Die Ziel-Surface zum Zeichnen
            camera: Die Kamera für die Transformation
        """
        # Frustum Culling: Nur sichtbare Sprites zeichnen
        camera_rect = camera.get_viewport_rect()
        
        for sprite in self.sprites():
            if not hasattr(sprite, 'image') or not sprite.image:
                continue
                
            # Prüfe ob Sprite im Kamera-Bereich ist
            sprite_rect = getattr(sprite, 'rect', None)
            if sprite_rect and not camera_rect.colliderect(sprite_rect):
                continue
                
            # Transformiere Sprite-Position mit Kamera
            transformed_rect = camera.apply(sprite)
            surface.blit(sprite.image, transformed_rect)
    
    def update_with_dt(self, dt: float, *args, **kwargs) -> None:
        """
        Update mit Delta-Time für alle Sprites
        
        Args:
            dt: Delta-Time in Sekunden
            *args, **kwargs: Zusätzliche Parameter für Sprite.update()
        """
        for sprite in self.sprites():
            if hasattr(sprite, 'update'):
                # Prüfe ob Sprite Delta-Time unterstützt
                sprite_update = getattr(sprite, 'update')
                try:
                    # Versuche Update mit dt
                    sprite_update(dt, *args, **kwargs)
                except TypeError:
                    # Fallback für Sprites ohne dt-Support
                    sprite_update(*args, **kwargs)
    
    def get_sprites_in_area(self, rect: pygame.Rect) -> list:
        """
        Gibt alle Sprites in einem bestimmten Bereich zurück
        
        Args:
            rect: Der zu überprüfende Bereich
            
        Returns:
            Liste der Sprites im Bereich
        """
        sprites_in_area = []
        for sprite in self.sprites():
            sprite_rect = getattr(sprite, 'rect', None)
            if sprite_rect and rect.colliderect(sprite_rect):
                sprites_in_area.append(sprite)
        return sprites_in_area
    
    def get_sprites_by_layer(self, layer: int) -> list:
        """
        Gibt alle Sprites eines bestimmten Layers zurück
        
        Args:
            layer: Der Layer-Index
            
        Returns:
            Liste der Sprites im Layer
        """
        return [sprite for sprite in self.sprites() 
                if self.get_layer_of_sprite(sprite) == layer]
    
    def set_sprite_layer_safe(self, sprite: pygame.sprite.Sprite, layer: int) -> bool:
        """
        Setzt den Layer eines Sprites sicher
        
        Args:
            sprite: Das Sprite
            layer: Der neue Layer
            
        Returns:
            True wenn erfolgreich, False sonst
        """
        try:
            if sprite in self.sprites():
                self.change_layer(sprite, layer)
                self._cache_dirty = True
                return True
        except Exception:
            pass
        return False


class CollisionSpriteGroup(LayeredSpriteGroup):
    """
    Sprite-Gruppe mit integrierter Kollisionserkennung
    
    Kombiniert Layer-Rendering mit optimierter Kollisionserkennung
    für bessere Performance in kollisionsintensiven Szenarien.
    """
    
    def __init__(self, *sprites, **kwargs):
        """
        Initialisiert die CollisionSpriteGroup
        
        Args:
            *sprites: Initial hinzuzufügende Sprites
            **kwargs: Zusätzliche Parameter
        """
        super().__init__(*sprites, **kwargs)
        self._collision_enabled_sprites = set()
    
    def enable_collision(self, sprite: pygame.sprite.Sprite) -> None:
        """
        Aktiviert Kollisionserkennung für ein Sprite
        
        Args:
            sprite: Das Sprite für das Kollisionen aktiviert werden sollen
        """
        if sprite in self.sprites():
            self._collision_enabled_sprites.add(sprite)
    
    def disable_collision(self, sprite: pygame.sprite.Sprite) -> None:
        """
        Deaktiviert Kollisionserkennung für ein Sprite
        
        Args:
            sprite: Das Sprite für das Kollisionen deaktiviert werden sollen
        """
        self._collision_enabled_sprites.discard(sprite)
    
    def check_collisions(self, sprite: pygame.sprite.Sprite) -> list:
        """
        Überprüft Kollisionen für ein bestimmtes Sprite
        
        Args:
            sprite: Das zu überprüfende Sprite
            
        Returns:
            Liste kollidierender Sprites
        """
        if sprite not in self._collision_enabled_sprites:
            return []
            
        collisions = []
        sprite_rect = getattr(sprite, 'rect', None)
        if not sprite_rect:
            return collisions
            
        for other_sprite in self._collision_enabled_sprites:
            if other_sprite == sprite:
                continue
                
            other_rect = getattr(other_sprite, 'rect', None)
            if other_rect and sprite_rect.colliderect(other_rect):
                collisions.append(other_sprite)
                
        return collisions
    
    def update_collisions(self) -> dict:
        """
        Überprüft alle Kollisionen und gibt sie zurück
        
        Returns:
            Dictionary mit Sprite -> Liste kollidierender Sprites
        """
        collision_map = {}
        
        for sprite in self._collision_enabled_sprites:
            collisions = self.check_collisions(sprite)
            if collisions:
                collision_map[sprite] = collisions
                
        return collision_map
    
    def remove(self, *sprites):
        """Überschreibt remove um Collision-Tracking zu bereinigen"""
        for sprite in sprites:
            self._collision_enabled_sprites.discard(sprite)
        super().remove(*sprites)


class AnimatedSpriteGroup(LayeredSpriteGroup):
    """
    Sprite-Gruppe speziell für animierte Sprites
    
    Bietet zusätzliche Funktionen für Animation-Management
    und synchronisierte Animation-Updates.
    """
    
    def __init__(self, *sprites, **kwargs):
        """
        Initialisiert die AnimatedSpriteGroup
        
        Args:
            *sprites: Initial hinzuzufügende Sprites
            **kwargs: Zusätzliche Parameter
        """
        super().__init__(*sprites, **kwargs)
        self._paused_sprites = set()
        self._animation_speed_multiplier = 1.0
    
    def pause_animation(self, sprite: pygame.sprite.Sprite) -> None:
        """
        Pausiert die Animation eines Sprites
        
        Args:
            sprite: Das Sprite dessen Animation pausiert werden soll
        """
        if sprite in self.sprites():
            self._paused_sprites.add(sprite)
    
    def resume_animation(self, sprite: pygame.sprite.Sprite) -> None:
        """
        Setzt die Animation eines Sprites fort
        
        Args:
            sprite: Das Sprite dessen Animation fortgesetzt werden soll
        """
        self._paused_sprites.discard(sprite)
    
    def set_animation_speed(self, multiplier: float) -> None:
        """
        Setzt die globale Animations-Geschwindigkeit
        
        Args:
            multiplier: Geschwindigkeits-Multiplikator (1.0 = normal)
        """
        self._animation_speed_multiplier = max(0.0, multiplier)
    
    def update_with_dt(self, dt: float, *args, **kwargs) -> None:
        """
        Update mit Delta-Time und Animation-Control
        
        Args:
            dt: Delta-Time in Sekunden
            *args, **kwargs: Zusätzliche Parameter
        """
        adjusted_dt = dt * self._animation_speed_multiplier
        
        for sprite in self.sprites():
            if sprite in self._paused_sprites:
                continue
                
            if hasattr(sprite, 'update'):
                sprite_update = getattr(sprite, 'update')
                try:
                    sprite_update(adjusted_dt, *args, **kwargs)
                except TypeError:
                    sprite_update(*args, **kwargs)
    
    def get_animated_sprites(self) -> list:
        """
        Gibt alle Sprites mit Animation-Unterstützung zurück
        
        Returns:
            Liste der animierten Sprites
        """
        animated = []
        for sprite in self.sprites():
            if hasattr(sprite, 'animate') or hasattr(sprite, 'current_frame'):
                animated.append(sprite)
        return animated


# Factory-Funktionen für einfache Erstellung
def create_layered_group(*sprites, **kwargs) -> LayeredSpriteGroup:
    """
    Factory-Funktion für LayeredSpriteGroup
    
    Args:
        *sprites: Initial hinzuzufügende Sprites
        **kwargs: Zusätzliche Parameter
        
    Returns:
        Neue LayeredSpriteGroup Instanz
    """
    return LayeredSpriteGroup(*sprites, **kwargs)


def create_collision_group(*sprites, **kwargs) -> CollisionSpriteGroup:
    """
    Factory-Funktion für CollisionSpriteGroup
    
    Args:
        *sprites: Initial hinzuzufügende Sprites
        **kwargs: Zusätzliche Parameter
        
    Returns:
        Neue CollisionSpriteGroup Instanz
    """
    return CollisionSpriteGroup(*sprites, **kwargs)


def create_animated_group(*sprites, **kwargs) -> AnimatedSpriteGroup:
    """
    Factory-Funktion für AnimatedSpriteGroup
    
    Args:
        *sprites: Initial hinzuzufügende Sprites
        **kwargs: Zusätzliche Parameter
        
    Returns:
        Neue AnimatedSpriteGroup Instanz
    """
    return AnimatedSpriteGroup(*sprites, **kwargs)
