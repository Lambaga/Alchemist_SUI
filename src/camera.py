# src/camera.py
import pygame
from settings import *

class Camera:
    """
    Eine Kamera mit Zoom-Funktionalität, die einem Ziel-Sprite folgt.
    Sie verschiebt und skaliert die gesamte Szene.
    """
    def __init__(self, screen_width, screen_height, zoom_factor=2.0):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.zoom_factor = zoom_factor  # 2.0 = 200% Zoom für bessere Sicht
        self.min_zoom = 1.0  # Minimaler Zoom
        self.max_zoom = 4.0  # Maximaler Zoom
        
        # Effektive Kamera-Größe mit Zoom
        self.update_zoom_dimensions()
        
        # Das Kamera-Rechteck repräsentiert den sichtbaren Bereich.
        self.camera_rect = pygame.Rect(0, 0, self.camera_width, self.camera_height)
        
    def update_zoom_dimensions(self):
        """Aktualisiert die Kamera-Dimensionen basierend auf dem Zoom-Faktor"""
        self.camera_width = self.screen_width / self.zoom_factor
        self.camera_height = self.screen_height / self.zoom_factor
        
    def zoom_in(self, factor=0.2):
        """Vergrößert den Zoom"""
        self.zoom_factor = min(self.max_zoom, self.zoom_factor + factor)
        self.update_zoom_dimensions()
        
    def zoom_out(self, factor=0.2):
        """Verkleinert den Zoom"""
        self.zoom_factor = max(self.min_zoom, self.zoom_factor - factor)
        self.update_zoom_dimensions()

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

    def update(self, target):
        """
        Aktualisiert die Kameraposition, um das Ziel in der Mitte zu halten.
        """
        # Zentriere das Ziel in der Kamera (mit Zoom berücksichtigt)
        x = target.rect.centerx - self.camera_width / 2
        y = target.rect.centery - self.camera_height / 2

        self.camera_rect = pygame.Rect(x, y, self.camera_width, self.camera_height)

