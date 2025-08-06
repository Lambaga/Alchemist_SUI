# -*- coding: utf-8 -*-
"""
Optimierte Kollisionserkennung für das Alchemist-Spiel
Ersetzt die naive O(n²) Kollisionsprüfung durch ein räumliches Hash-System
"""

import pygame
from typing import List, Optional, Any, Dict
from spatial_hash import CollisionManager


class OptimizedCollisionSystem:
    """
    Optimiertes Kollisionssystem für das Alchemist-Spiel
    
    Verwendet räumliche Hashtabellen für effiziente Kollisionserkennung
    und ist kompatibel mit dem bestehenden Spielsystem.
    """
    
    def __init__(self, cell_size: int = 128):
        """
        Initialisiert das optimierte Kollisionssystem
        
        Args:
            cell_size: Größe der Hashtabellen-Zellen (sollte ~2-4x Objektgröße sein)
        """
        self.collision_manager = CollisionManager(cell_size)
        self.initialized = False
        
        # Performance-Tracking
        self.collision_checks = 0
        self.collision_hits = 0
        
    def initialize_static_objects(self, collision_objects: List[Any]) -> None:
        """
        Initialisiert statische Kollisionsobjekte (Wände, Hindernisse)
        
        Args:
            collision_objects: Liste der statischen Kollisionsobjekte
        """
        self.collision_manager.clear()
        
        for obj in collision_objects:
            rect = self._get_rect_from_object(obj)
            if rect:
                self.collision_manager.add_static_object(obj, rect)
        
        self.initialized = True
        print(f"✅ Spatial Hash initialisiert mit {len(collision_objects)} statischen Objekten")
    
    def add_dynamic_object(self, obj: Any) -> None:
        """
        Fügt ein dynamisches Objekt hinzu (Spieler, Feinde, Projektile)
        
        Args:
            obj: Das dynamische Objekt
        """
        rect = self._get_rect_from_object(obj)
        if rect:
            self.collision_manager.add_dynamic_object(obj, rect)
    
    def update_dynamic_object(self, obj: Any) -> None:
        """
        Aktualisiert die Position eines dynamischen Objekts
        
        Args:
            obj: Das zu aktualisierende Objekt
        """
        rect = self._get_rect_from_object(obj)
        if rect:
            self.collision_manager.update_dynamic_object(obj, rect)
    
    def check_collisions(self, obj: Any, test_rect: Optional[pygame.Rect] = None) -> List[Any]:
        """
        Überprüft Kollisionen für ein Objekt (optimiert)
        
        Args:
            obj: Das zu prüfende Objekt
            test_rect: Optionales Test-Rechteck (für Bewegungsvorhersage)
            
        Returns:
            Liste aller kollidierenden Objekte
        """
        if not self.initialized:
            return []
        
        # Performance-Tracking
        self.collision_checks += 1
        
        # Verwende Test-Rechteck oder aktuelles Rechteck des Objekts
        rect = test_rect or self._get_rect_from_object(obj)
        if not rect:
            return []
        
        collisions = self.collision_manager.get_collisions(obj, rect)
        
        if collisions:
            self.collision_hits += 1
            
        return collisions
    
    def check_horizontal_collision(self, obj: Any, direction: float) -> List[Any]:
        """
        Spezialisierte horizontale Kollisionsprüfung
        
        Args:
            obj: Das zu prüfende Objekt
            direction: Bewegungsrichtung (-1 = links, +1 = rechts)
            
        Returns:
            Liste kollidierender Objekte
        """
        rect = self._get_rect_from_object(obj)
        if not rect:
            return []
        
        # Erstelle Test-Rechteck für horizontale Bewegung
        test_rect = rect.copy()
        if direction > 0:  # Nach rechts
            test_rect.x += 1
        else:  # Nach links
            test_rect.x -= 1
            
        return self.check_collisions(obj, test_rect)
    
    def check_vertical_collision(self, obj: Any, direction: float) -> List[Any]:
        """
        Spezialisierte vertikale Kollisionsprüfung
        
        Args:
            obj: Das zu prüfende Objekt
            direction: Bewegungsrichtung (-1 = oben, +1 = unten)
            
        Returns:
            Liste kollidierender Objekte
        """
        rect = self._get_rect_from_object(obj)
        if not rect:
            return []
        
        # Erstelle Test-Rechteck für vertikale Bewegung
        test_rect = rect.copy()
        if direction > 0:  # Nach unten
            test_rect.y += 1
        else:  # Nach oben
            test_rect.y -= 1
            
        return self.check_collisions(obj, test_rect)
    
    def _get_rect_from_object(self, obj: Any) -> Optional[pygame.Rect]:
        """
        Ermittelt das Rechteck eines Objekts
        
        Args:
            obj: Das Objekt
            
        Returns:
            Das Rechteck oder None
        """
        # Priorität: hitbox > rect > collision_rect
        for attr in ['hitbox', 'rect', 'collision_rect']:
            if hasattr(obj, attr):
                rect = getattr(obj, attr)
                if isinstance(rect, pygame.Rect):
                    return rect
        
        # Falls es direkt ein Rect ist
        if isinstance(obj, pygame.Rect):
            return obj
            
        return None
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Gibt Performance-Statistiken zurück
        
        Returns:
            Dictionary mit Performance-Daten
        """
        spatial_stats = self.collision_manager.get_stats()
        
        hit_ratio = (self.collision_hits / max(self.collision_checks, 1)) * 100
        
        return {
            **spatial_stats,
            'collision_checks': self.collision_checks,
            'collision_hits': self.collision_hits,
            'hit_ratio_percent': hit_ratio,
            'efficiency': f"{hit_ratio:.1f}% hit ratio"
        }
    
    def reset_performance_counters(self) -> None:
        """Setzt die Performance-Zähler zurück"""
        self.collision_checks = 0
        self.collision_hits = 0


class PlayerCollisionMixin:
    """
    Mixin-Klasse für optimierte Player-Kollisionen
    
    Kann in die bestehende Player-Klasse integriert werden,
    um die Kollisionserkennung zu optimieren.
    """
    
    def __init_collision_system__(self, cell_size: int = 128):
        """Initialisiert das optimierte Kollisionssystem"""
        self.collision_system = OptimizedCollisionSystem(cell_size)
        self._old_obstacle_sprites = None
    
    def set_obstacle_sprites_optimized(self, obstacle_sprites) -> None:
        """
        Ersetzt set_obstacle_sprites mit optimierter Version
        
        Args:
            obstacle_sprites: Sprite-Gruppe oder Liste der Hindernis-Sprites
        """
        # Konvertiere zu Liste falls nötig
        if hasattr(obstacle_sprites, 'sprites'):
            obstacles = obstacle_sprites.sprites()
        else:
            obstacles = list(obstacle_sprites)
        
        # Initialisiere das räumliche Hash-System
        self.collision_system.initialize_static_objects(obstacles)
        
        # Speichere für Backward-Compatibility
        self._old_obstacle_sprites = obstacle_sprites
        
        # Füge sich selbst als dynamisches Objekt hinzu
        self.collision_system.add_dynamic_object(self)
    
    def collision_optimized(self, direction: str) -> None:
        """
        Optimierte Kollisionserkennung
        
        Args:
            direction: 'horizontal' oder 'vertical'
        """
        if not hasattr(self, 'collision_system'):
            # Fallback zur alten Methode
            return self.collision_original(direction)
        
        # Aktualisiere Position im räumlichen Hash
        self.collision_system.update_dynamic_object(self)
        
        if direction == 'horizontal':
            collisions = self.collision_system.check_horizontal_collision(
                self, self.direction.x if hasattr(self, 'direction') else 0
            )
            
            for collision_obj in collisions:
                collision_rect = self.collision_system._get_rect_from_object(collision_obj)
                if collision_rect and collision_rect.colliderect(self.hitbox):
                    if hasattr(self, 'direction') and self.direction.x > 0:  # Bewegung nach rechts
                        self.hitbox.right = collision_rect.left
                    elif hasattr(self, 'direction') and self.direction.x < 0:  # Bewegung nach links
                        self.hitbox.left = collision_rect.right
                    
                    # Float-Position synchronisieren
                    if hasattr(self, 'position'):
                        self.position.x = self.hitbox.centerx
                    break  # Erste Kollision reicht
                        
        elif direction == 'vertical':
            collisions = self.collision_system.check_vertical_collision(
                self, self.direction.y if hasattr(self, 'direction') else 0
            )
            
            for collision_obj in collisions:
                collision_rect = self.collision_system._get_rect_from_object(collision_obj)
                if collision_rect and collision_rect.colliderect(self.hitbox):
                    if hasattr(self, 'direction') and self.direction.y > 0:  # Bewegung nach unten
                        self.hitbox.bottom = collision_rect.top
                    elif hasattr(self, 'direction') and self.direction.y < 0:  # Bewegung nach oben
                        self.hitbox.top = collision_rect.bottom
                    
                    # Float-Position synchronisieren
                    if hasattr(self, 'position'):
                        self.position.y = self.hitbox.centery
                    break  # Erste Kollision reicht


def integrate_spatial_hash_into_player(player_class):
    """
    Integriert das räumliche Hash-System in eine bestehende Player-Klasse
    
    Args:
        player_class: Die Player-Klasse, die erweitert werden soll
        
    Returns:
        Die erweiterte Player-Klasse
    """
    # Sichere die ursprüngliche collision-Methode
    if not hasattr(player_class, 'collision_original'):
        player_class.collision_original = player_class.collision
    
    # Füge Mixin-Methoden hinzu
    for method_name in dir(PlayerCollisionMixin):
        if not method_name.startswith('_') or method_name == '__init_collision_system__':
            method = getattr(PlayerCollisionMixin, method_name)
            setattr(player_class, method_name, method)
    
    # Ersetze die collision-Methode
    player_class.collision = PlayerCollisionMixin.collision_optimized
    
    return player_class
