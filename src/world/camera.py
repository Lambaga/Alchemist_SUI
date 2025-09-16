# -*- coding: utf-8 -*-
# src/camera.py
import pygame
from settings import *

class Camera:
    """
    Eine Kamera mit Zoom-Funktionalität, die einem Ziel-Sprite folgt.
    Sie verschiebt und skaliert die gesamte Szene.
    """
    def __init__(self, screen_width, screen_height, zoom_factor=1.0):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.zoom_factor = 1.0  # Fester Zoom-Faktor (maximal herausgezoomt)
        
        # Effektive Kamera-Größe mit Zoom
        self.update_zoom_dimensions()
        
        # Das Kamera-Rechteck repräsentiert den sichtbaren Bereich.
        self.camera_rect = pygame.Rect(0, 0, self.camera_width, self.camera_height)
        
    def update_zoom_dimensions(self):
        """Aktualisiert die Kamera-Dimensionen basierend auf dem Zoom-Faktor"""
        self.camera_width = self.screen_width / self.zoom_factor
        self.camera_height = self.screen_height / self.zoom_factor

    def apply(self, entity):
        """
        Wendet den Kamera-Offset und Zoom auf ein Sprite an.
        """
        # Berechne Position relativ zur Kamera
        x = (entity.rect.x - self.camera_rect.x) * self.zoom_factor
        y = (entity.rect.y - self.camera_rect.y) * self.zoom_factor
        return pygame.Rect(x, y, entity.rect.width * self.zoom_factor, entity.rect.height * self.zoom_factor)

    def apply_rect(self, rect):
        """
        Wendet den Kamera-Offset und Zoom auf ein beliebiges Rechteck an.
        """
        x = (rect.x - self.camera_rect.x) * self.zoom_factor
        y = (rect.y - self.camera_rect.y) * self.zoom_factor
        return pygame.Rect(x, y, rect.width * self.zoom_factor, rect.height * self.zoom_factor)
    
    def reverse_apply_pos(self, screen_pos):
        """
        Konvertiert eine Bildschirm-Position zurück zur Welt-Position.
        """
        world_x = screen_pos[0] / self.zoom_factor + self.camera_rect.x
        world_y = screen_pos[1] / self.zoom_factor + self.camera_rect.y
        return (world_x, world_y)

    def update(self, target):
        """
        Aktualisiert die Kameraposition, um das Ziel in der Mitte zu halten.
        """
        # Zentriere das Ziel in der Kamera (mit Zoom berücksichtigt)
        x = target.rect.centerx - self.camera_width / 2
        y = target.rect.centery - self.camera_height / 2

        self.camera_rect = pygame.Rect(x, y, self.camera_width, self.camera_height)
    
    def center_on_target(self, target):
        """Kompatibilitäts-Methode: zentriert die Kamera auf das Ziel.
        Alias für `update(target)`.
        """
        self.update(target)
    
    def get_viewport_rect(self):
        """
        Gibt das Sichtfeld der Kamera zurück (für Frustum Culling)
        
        Returns:
            pygame.Rect: Das sichtbare Rechteck der Kamera
        """
        return self.camera_rect.copy()

