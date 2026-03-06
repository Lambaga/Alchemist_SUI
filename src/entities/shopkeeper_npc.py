# -*- coding: utf-8 -*-
"""
Shopkeeper NPC – Händler mit Platzhalter-Sprite.

Erscheint auf Map3.tmx (erste Map) und Map_Town.tmx (vorletzte Map).
Sprite-Ordner: assets/Shopkeeper/  (wird später mit echtem Modell gefüllt).
"""

from __future__ import annotations

import os
import pygame
from typing import Tuple


class ShopkeeperNPC(pygame.sprite.Sprite):
    """Ein Händler-NPC, bei dem der Spieler Upgrades kaufen kann."""

    INTERACTION_RADIUS = 100  # Pixel

    def __init__(self, x: int, y: int):
        super().__init__()

        self.name = "Händler"
        self.pos_x = float(x)
        self.pos_y = float(y)

        # Versuche echtes Asset, sonst Platzhalter
        self._load_sprite()

        self.rect = self.image.get_rect()
        self.rect.midbottom = (int(self.pos_x), int(self.pos_y))

        # Animation
        self.animation_timer = 0.0
        self.animation_speed = 0.6
        self.frame_index = 0

        # Interaktion
        self.can_interact = False

    # ------------------------------------------------------------------
    # Sprite laden
    # ------------------------------------------------------------------
    def _load_sprite(self):
        """Lädt das Shopkeeper-Asset oder erstellt einen Platzhalter."""
        asset_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "assets", "Shopkeeper"
        )

        # Versuche ein Bild zu laden (PNG/JPG im Ordner)
        loaded = False
        if os.path.isdir(asset_dir):
            for fname in sorted(os.listdir(asset_dir)):
                if fname.lower().endswith(('.png', '.jpg', '.jpeg')):
                    try:
                        path = os.path.join(asset_dir, fname)
                        raw = pygame.image.load(path).convert_alpha()
                        # Skaliere auf vernünftige NPC-Größe
                        w, h = raw.get_size()
                        target_h = 80
                        scale = target_h / h if h > 0 else 1
                        self.image = pygame.transform.smoothscale(
                            raw, (max(1, int(w * scale)), target_h)
                        )
                        loaded = True
                        print(f"🏪 Shopkeeper-Sprite geladen: {fname}")
                        break
                    except Exception as e:
                        print(f"⚠️ Shopkeeper-Sprite Fehler: {e}")

        if not loaded:
            self._create_placeholder_sprite()

    def _create_placeholder_sprite(self):
        """Erstellt einen erkennbaren Platzhalter-Sprite."""
        width, height = 48, 72
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)

        # Körper (Robe in Braun/Gold – typisch Händler)
        pygame.draw.ellipse(self.image, (100, 70, 30), (6, 28, 36, 44))
        # Umhang-Rand
        pygame.draw.ellipse(self.image, (140, 100, 40), (6, 28, 36, 44), 2)

        # Kopf
        pygame.draw.circle(self.image, (210, 175, 140), (24, 18), 13)

        # Turban / Mütze
        pygame.draw.ellipse(self.image, (160, 120, 50), (10, 2, 28, 18))
        pygame.draw.ellipse(self.image, (200, 160, 60), (10, 2, 28, 18), 2)
        # Juwel auf der Mütze
        pygame.draw.circle(self.image, (60, 200, 120), (24, 8), 3)

        # Augen
        pygame.draw.circle(self.image, (40, 40, 40), (19, 17), 2)
        pygame.draw.circle(self.image, (40, 40, 40), (29, 17), 2)

        # Lächeln
        pygame.draw.arc(self.image, (40, 40, 40), (17, 18, 14, 8), 3.3, 6.1, 1)

        # Waren-Beutel in der Hand
        pygame.draw.circle(self.image, (180, 140, 60), (38, 46), 8)
        pygame.draw.circle(self.image, (140, 100, 40), (38, 46), 8, 1)
        # Münz-Symbol auf dem Beutel
        pygame.draw.circle(self.image, (255, 215, 0), (38, 46), 3)

    # ------------------------------------------------------------------
    # Update / Interaktion
    # ------------------------------------------------------------------
    def update(self, dt: float = None):
        if dt is None:
            dt = 1 / 60
        self.animation_timer += dt
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0.0
            self.frame_index = (self.frame_index + 1) % 4

    def check_player_nearby(self, player_pos: Tuple[float, float]) -> bool:
        dx = player_pos[0] - self.pos_x
        dy = player_pos[1] - self.pos_y
        distance = (dx * dx + dy * dy) ** 0.5
        self.can_interact = distance <= self.INTERACTION_RADIUS
        return self.can_interact

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------
    def draw(self, screen: pygame.Surface, camera):
        screen_pos = camera.apply(self)
        hover_offset = [0, -2, 0, 2][self.frame_index]
        screen.blit(self.image, (screen_pos.x, screen_pos.y + hover_offset))

    def draw_interaction_prompt(self, screen: pygame.Surface, camera):
        if not self.can_interact:
            return
        screen_pos = camera.apply(self)
        prompt_x = screen_pos.centerx
        prompt_y = screen_pos.top - 25

        try:
            font = pygame.font.Font(None, 20)
            text = font.render("[ C ] Shop", True, (255, 220, 100))
            text_rect = text.get_rect(center=(prompt_x, prompt_y))

            bg_rect = text_rect.inflate(10, 6)
            bg = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
            bg.fill((0, 0, 0, 180))
            screen.blit(bg, bg_rect)
            pygame.draw.rect(screen, (255, 200, 50), bg_rect, 1, border_radius=4)
            screen.blit(text, text_rect)
        except Exception:
            pass
