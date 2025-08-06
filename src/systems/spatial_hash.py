# -*- coding: utf-8 -*-
"""
Spatial Hash System für optimierte Kollisionserkennung
Reduziert die O(n²) Komplexität auf O(1) für lokale Kollisionen
"""

import pygame
from typing import Set, Dict, Tuple, List, Any, Optional


class SpatialHash:
    """
    Räumliche Hashtabelle für effiziente Kollisionserkennung
    
    Teilt die Spielwelt in ein Raster auf und speichert Objekte nur in den
    Zellen, die sie berühren. Dies reduziert die Anzahl der zu überprüfenden
    Kollisionen erheblich.
    """
    
    def __init__(self, cell_size: int = 128):
        """
        Initialisiert die räumliche Hashtabelle
        
        Args:
            cell_size: Größe einer Zelle in Pixeln (Standard: 128)
                      Sollte etwa 2-4x die Größe der typischen Objekte sein
        """
        self.cell_size = cell_size
        self.cells: Dict[Tuple[int, int], Set[Any]] = {}
        self.object_cells: Dict[Any, Set[Tuple[int, int]]] = {}  # Tracking für Updates
        
    def _get_cell_coords(self, rect: pygame.Rect) -> List[Tuple[int, int]]:
        """
        Gibt alle Zellen-Koordinaten zurück, die das Rechteck berührt
        
        Args:
            rect: Das zu prüfende Rechteck
            
        Returns:
            Liste von Zellen-Koordinaten (x, y)
        """
        left = rect.left // self.cell_size
        right = rect.right // self.cell_size
        top = rect.top // self.cell_size
        bottom = rect.bottom // self.cell_size
        
        cells = []
        for x in range(left, right + 1):
            for y in range(top, bottom + 1):
                cells.append((x, y))
        return cells
    
    def insert(self, obj: Any, rect: pygame.Rect) -> None:
        """
        Fügt ein Objekt in die räumliche Hashtabelle ein
        
        Args:
            obj: Das einzufügende Objekt
            rect: Das Rechteck des Objekts
        """
        # Entferne das Objekt erst, falls es bereits existiert
        self.remove(obj)
        
        # Füge zu neuen Zellen hinzu
        cells = self._get_cell_coords(rect)
        self.object_cells[obj] = set(cells)
        
        for cell in cells:
            if cell not in self.cells:
                self.cells[cell] = set()
            self.cells[cell].add(obj)
    
    def remove(self, obj: Any) -> None:
        """
        Entfernt ein Objekt aus der räumlichen Hashtabelle
        
        Args:
            obj: Das zu entfernende Objekt
        """
        if obj not in self.object_cells:
            return
            
        # Entferne aus allen Zellen
        for cell in self.object_cells[obj]:
            if cell in self.cells:
                self.cells[cell].discard(obj)
                # Entferne leere Zellen
                if not self.cells[cell]:
                    del self.cells[cell]
        
        # Entferne Tracking
        del self.object_cells[obj]
    
    def update(self, obj: Any, rect: pygame.Rect) -> None:
        """
        Aktualisiert die Position eines Objekts in der Hashtabelle
        
        Args:
            obj: Das zu aktualisierende Objekt
            rect: Das neue Rechteck des Objekts
        """
        self.insert(obj, rect)  # insert() behandelt bereits das Entfernen
    
    def get_nearby(self, rect: pygame.Rect) -> Set[Any]:
        """
        Gibt alle Objekte in der Nähe des gegebenen Rechtecks zurück
        
        Args:
            rect: Das Abfrage-Rechteck
            
        Returns:
            Set aller Objekte in den berührten Zellen
        """
        nearby = set()
        for cell in self._get_cell_coords(rect):
            if cell in self.cells:
                nearby.update(self.cells[cell])
        return nearby
    
    def get_potential_collisions(self, obj: Any, rect: pygame.Rect) -> Set[Any]:
        """
        Gibt potentielle Kollisionsobjekte zurück (ohne das Objekt selbst)
        
        Args:
            obj: Das anfragende Objekt
            rect: Das Rechteck des anfragenden Objekts
            
        Returns:
            Set aller anderen Objekte in den berührten Zellen
        """
        nearby = self.get_nearby(rect)
        nearby.discard(obj)  # Entferne das Objekt selbst
        return nearby
    
    def clear(self) -> None:
        """Leert die gesamte Hashtabelle"""
        self.cells.clear()
        self.object_cells.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Gibt Statistiken über die Hashtabelle zurück
        
        Returns:
            Dictionary mit Statistiken
        """
        total_objects = len(self.object_cells)
        total_cells = len(self.cells)
        avg_objects_per_cell = sum(len(cell) for cell in self.cells.values()) / max(total_cells, 1)
        
        return {
            'total_objects': total_objects,
            'total_cells': total_cells,
            'avg_objects_per_cell': avg_objects_per_cell,
            'cell_size': self.cell_size,
            'memory_usage_estimate': total_cells * 64 + total_objects * 32  # Grobe Schätzung in Bytes
        }


class CollisionManager:
    """
    Hochleistungs-Kollisionsmanager mit räumlicher Hashtabelle
    
    Diese Klasse ersetzt das naive O(n²) Kollisionssystem durch ein
    optimiertes System, das nur relevante Objekte überprüft.
    """
    
    def __init__(self, cell_size: int = 128):
        """
        Initialisiert den Kollisionsmanager
        
        Args:
            cell_size: Größe der Hashtabellen-Zellen
        """
        self.spatial_hash = SpatialHash(cell_size)
        self.static_objects: Set[Any] = set()  # Objekte, die sich nicht bewegen
        self.dynamic_objects: Set[Any] = set()  # Objekte, die sich bewegen
        
    def add_static_object(self, obj: Any, rect: pygame.Rect) -> None:
        """
        Fügt ein statisches Objekt hinzu (bewegt sich nicht)
        
        Args:
            obj: Das statische Objekt
            rect: Das Rechteck des Objekts
        """
        self.spatial_hash.insert(obj, rect)
        self.static_objects.add(obj)
    
    def add_dynamic_object(self, obj: Any, rect: pygame.Rect) -> None:
        """
        Fügt ein dynamisches Objekt hinzu (bewegt sich)
        
        Args:
            obj: Das dynamische Objekt
            rect: Das Rechteck des Objekts
        """
        self.spatial_hash.insert(obj, rect)
        self.dynamic_objects.add(obj)
    
    def update_dynamic_object(self, obj: Any, rect: pygame.Rect) -> None:
        """
        Aktualisiert die Position eines dynamischen Objekts
        
        Args:
            obj: Das zu aktualisierende Objekt
            rect: Das neue Rechteck
        """
        if obj in self.dynamic_objects:
            self.spatial_hash.update(obj, rect)
    
    def remove_object(self, obj: Any) -> None:
        """
        Entfernt ein Objekt aus dem System
        
        Args:
            obj: Das zu entfernende Objekt
        """
        self.spatial_hash.remove(obj)
        self.static_objects.discard(obj)
        self.dynamic_objects.discard(obj)
    
    def get_collisions(self, obj: Any, rect: pygame.Rect) -> List[Any]:
        """
        Gibt alle Kollisionen für ein Objekt zurück
        
        Args:
            obj: Das anfragende Objekt
            rect: Das Rechteck des Objekts
            
        Returns:
            Liste aller kollidierenden Objekte
        """
        potential_collisions = self.spatial_hash.get_potential_collisions(obj, rect)
        actual_collisions = []
        
        for other_obj in potential_collisions:
            # Hole das Rechteck des anderen Objekts
            other_rect = self._get_object_rect(other_obj)
            if other_rect and rect.colliderect(other_rect):
                actual_collisions.append(other_obj)
        
        return actual_collisions
    
    def _get_object_rect(self, obj: Any) -> Optional[pygame.Rect]:
        """
        Versucht das Rechteck eines Objekts zu ermitteln
        
        Args:
            obj: Das Objekt
            
        Returns:
            Das Rechteck oder None
        """
        # Verschiedene Attribute versuchen
        for attr in ['hitbox', 'rect', 'collision_rect']:
            if hasattr(obj, attr):
                return getattr(obj, attr)
        
        # Falls es direkt ein Rect ist
        if isinstance(obj, pygame.Rect):
            return obj
            
        return None
    
    def check_point_collision(self, point: Tuple[int, int]) -> List[Any]:
        """
        Überprüft Kollisionen mit einem Punkt
        
        Args:
            point: Der zu überprüfende Punkt (x, y)
            
        Returns:
            Liste aller Objekte, die den Punkt enthalten
        """
        point_rect = pygame.Rect(point[0], point[1], 1, 1)
        nearby = self.spatial_hash.get_nearby(point_rect)
        
        collisions = []
        for obj in nearby:
            obj_rect = self._get_object_rect(obj)
            if obj_rect and obj_rect.collidepoint(point):
                collisions.append(obj)
                
        return collisions
    
    def clear(self) -> None:
        """Leert den gesamten Kollisionsmanager"""
        self.spatial_hash.clear()
        self.static_objects.clear()
        self.dynamic_objects.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Gibt detaillierte Statistiken zurück
        
        Returns:
            Dictionary mit Statistiken
        """
        spatial_stats = self.spatial_hash.get_stats()
        return {
            **spatial_stats,
            'static_objects': len(self.static_objects),
            'dynamic_objects': len(self.dynamic_objects),
            'total_managed_objects': len(self.static_objects) + len(self.dynamic_objects)
        }


# Für backward compatibility
def create_optimized_collision_system(cell_size: int = 128) -> CollisionManager:
    """
    Factory-Funktion für einen optimierten Kollisionsmanager
    
    Args:
        cell_size: Größe der Hashtabellen-Zellen
        
    Returns:
        Neuer CollisionManager
    """
    return CollisionManager(cell_size)
