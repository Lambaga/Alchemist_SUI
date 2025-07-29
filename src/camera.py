# src/camera.py
import pygame
from config import WindowConfig

class Camera:
    """
    Eine einfache Kamera, die einem Ziel-Sprite folgt.
    Sie verschiebt die gesamte Szene, um den Eindruck zu erwecken,
    dass die Kamera dem Spieler folgt.
    """
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        # Das Kamera-Rechteck repräsentiert den sichtbaren Bereich.
        # Wir starten es bei (0,0) mit der Größe des Bildschirms.
        self.camera_rect = pygame.Rect(0, 0, screen_width, screen_height)

    def apply(self, entity):
        """
        Wendet den Kamera-Offset auf ein Sprite an.
        Verschiebt das Rechteck des Sprites basierend auf der Kameraposition.
        """
        return entity.rect.move(self.camera_rect.topleft)

    def apply_rect(self, rect):
        """
        Wendet den Kamera-Offset auf ein beliebiges Rechteck an.
        Nützlich für statische Objekte wie Steine.
        """
        return rect.move(self.camera_rect.topleft)

    def update(self, target):
        """
        Aktualisiert die Kameraposition, um das Ziel (den Spieler)
        in der Mitte des Bildschirms zu halten.
        """
        # Wir wollen, dass das Ziel in der Mitte ist, also berechnen wir die
        # linke obere Ecke der Kamera so, dass das Ziel zentriert ist.
        x = -target.rect.centerx + int(self.screen_width / 2)
        y = -target.rect.centery + int(self.screen_height / 2)

        # Hier könnten wir später Grenzen für die Kamera hinzufügen,
        # damit sie nicht über die Levelgrenzen hinaus scrollt.

        self.camera_rect = pygame.Rect(x, y, self.camera_rect.width, self.camera_rect.height)

