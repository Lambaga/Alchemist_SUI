# -*- coding: utf-8 -*-
"""
Soldier NPC – Ritter auf der vorletzten Map (Map_Town).

Warnt den Spieler vor dem Dragon Lord und gibt Trainings-Tipps.
Sprite-Ordner: assets/Knight/  (Sprite-Sheets, 120×80 px pro Frame).
"""

import os
import pygame
import math
from typing import List, Tuple


class SoldierNPC(pygame.sprite.Sprite):
    """Ritter-NPC der den Spieler warnt und den Fortschritt gated."""

    INTERACTION_RADIUS = 100
    FRAME_W = 120   # Breite eines einzelnen Frames im Sheet
    FRAME_H = 80    # Höhe eines einzelnen Frames im Sheet
    TARGET_H = 80   # Anzeigegröße (Höhe in Pixel)

    def __init__(self, x: int, y: int):
        super().__init__()

        self.name = "Ritter Konrad"
        self.pos_x = float(x)
        self.pos_y = float(y)

        # Animations-Daten
        self.idle_frames: List[pygame.Surface] = []
        self.run_frames: List[pygame.Surface] = []

        # Lade echte Sprites oder Platzhalter
        self._load_sprites()

        # Aktuelles Bild
        self.image = self.idle_frames[0] if self.idle_frames else self._make_placeholder()
        self.rect = self.image.get_rect()
        self.rect.midbottom = (int(self.pos_x), int(self.pos_y))

        # Animation
        self.animation_timer = 0.0
        self.animation_speed = 0.1  # Sekunden pro Frame
        self.frame_index = 0

        # Interaktion
        self.can_interact = False

    # ------------------------------------------------------------------
    # Sprite-Sheet laden
    # ------------------------------------------------------------------
    def _get_asset_dir(self) -> str:
        """Gibt den Pfad zum Knight-Asset-Ordner zurück."""
        return os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "assets", "Knight",
        )

    def _load_sheet(self, path: str) -> List[pygame.Surface]:
        """Zerlegt ein horizontales Sprite-Sheet in einzelne Frames."""
        try:
            sheet = pygame.image.load(path).convert_alpha()
        except Exception as e:
            print(f"⚠️ Knight-Sheet Fehler ({path}): {e}")
            return []

        sw, sh = sheet.get_size()
        frame_count = max(1, sw // self.FRAME_W)
        scale = self.TARGET_H / self.FRAME_H
        target_w = max(1, int(self.FRAME_W * scale))

        frames: List[pygame.Surface] = []
        for i in range(frame_count):
            sub = sheet.subsurface(pygame.Rect(i * self.FRAME_W, 0, self.FRAME_W, self.FRAME_H))
            if scale != 1.0:
                sub = pygame.transform.smoothscale(sub, (target_w, self.TARGET_H))
            frames.append(sub)
        return frames

    def _load_sprites(self):
        """Lädt die Knight Sprite-Sheets (Idle + Run)."""
        asset_dir = self._get_asset_dir()

        if not os.path.isdir(asset_dir):
            print("⚠️ Knight-Ordner nicht gefunden – verwende Platzhalter")
            self.idle_frames = [self._make_placeholder()]
            self.run_frames = self.idle_frames
            return

        # Idle-Animation laden
        idle_path = os.path.join(asset_dir, "_Idle.png")
        if os.path.isfile(idle_path):
            self.idle_frames = self._load_sheet(idle_path)
            print(f"⚔️  Knight _Idle geladen: {len(self.idle_frames)} Frames")

        # Run-Animation als Fallback (optional)
        run_path = os.path.join(asset_dir, "_Run.png")
        if os.path.isfile(run_path):
            self.run_frames = self._load_sheet(run_path)

        # Fallback
        if not self.idle_frames:
            self.idle_frames = [self._make_placeholder()]
        if not self.run_frames:
            self.run_frames = self.idle_frames

    def _make_placeholder(self) -> pygame.Surface:
        """Erstellt einen einfachen Platzhalter falls keine Sprites vorhanden."""
        w, h = 48, 72
        surf = pygame.Surface((w, h), pygame.SRCALPHA)

        # Körper
        pygame.draw.rect(surf, (150, 150, 160), (10, 28, 28, 26))
        pygame.draw.rect(surf, (160, 30, 30), (14, 30, 20, 22))
        pygame.draw.rect(surf, (220, 200, 60), (22, 32, 4, 16))
        pygame.draw.rect(surf, (220, 200, 60), (16, 38, 16, 4))

        # Beine
        pygame.draw.rect(surf, (120, 120, 130), (14, 52, 8, 18))
        pygame.draw.rect(surf, (120, 120, 130), (26, 52, 8, 18))
        pygame.draw.rect(surf, (50, 35, 25), (13, 66, 10, 6))
        pygame.draw.rect(surf, (50, 35, 25), (25, 66, 10, 6))

        # Kopf + Helm
        pygame.draw.circle(surf, (210, 175, 145), (24, 18), 11)
        pygame.draw.arc(surf, (140, 140, 150), (13, 6, 22, 20), 0, math.pi, 4)
        pygame.draw.rect(surf, (140, 140, 150), (13, 8, 22, 6))
        pygame.draw.rect(surf, (130, 130, 140), (22, 12, 4, 12))
        pygame.draw.circle(surf, (40, 60, 90), (19, 18), 2)
        pygame.draw.circle(surf, (40, 60, 90), (29, 18), 2)

        # Schwert + Schild
        pygame.draw.rect(surf, (180, 180, 200), (38, 14, 3, 12))
        pygame.draw.rect(surf, (90, 80, 70), (38, 24, 3, 6))
        pygame.draw.rect(surf, (160, 140, 60), (35, 30, 9, 3))
        pygame.draw.ellipse(surf, (100, 30, 30), (0, 30, 14, 20))
        pygame.draw.circle(surf, (220, 200, 60), (7, 40), 3)
        return surf

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------
    def update(self, dt: float = None):
        if dt is None:
            dt = 1 / 60

        frames = self.idle_frames
        self.animation_timer += dt
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0.0
            self.frame_index = (self.frame_index + 1) % len(frames)
            self.image = frames[self.frame_index]
            # rect-Größe aktualisieren, Position beibehalten
            old_midbottom = self.rect.midbottom
            self.rect = self.image.get_rect()
            self.rect.midbottom = old_midbottom

    def check_player_nearby(self, player_pos: Tuple[float, float]) -> bool:
        dx = player_pos[0] - self.pos_x
        dy = player_pos[1] - self.pos_y
        dist = (dx * dx + dy * dy) ** 0.5
        self.can_interact = dist <= self.INTERACTION_RADIUS
        return self.can_interact

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------
    def draw(self, screen: pygame.Surface, camera):
        screen_pos = camera.apply(self)
        screen.blit(self.image, (screen_pos.x, screen_pos.y))

    def draw_interaction_prompt(self, screen: pygame.Surface, camera):
        if not self.can_interact:
            return
        screen_pos = camera.apply(self)
        px = screen_pos.centerx
        py = screen_pos.top - 25

        try:
            font = pygame.font.Font(None, 20)
            text = font.render("[ C ] Ritter ansprechen", True, (255, 220, 100))
            text_rect = text.get_rect(center=(px, py))
            bg = text_rect.inflate(10, 6)
            pygame.draw.rect(screen, (0, 0, 0, 180), bg, border_radius=4)
            pygame.draw.rect(screen, (200, 180, 60), bg, 1, border_radius=4)
            screen.blit(text, text_rect)
        except Exception:
            pass
