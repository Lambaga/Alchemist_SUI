# -*- coding: utf-8 -*-
"""
Knight Companion – Ritter Konrad als Begleiter.

Folgt dem Spieler, greift nahe Gegner an (10 Schaden) und hat 500 HP.
Wird aktiviert wenn der Spieler den Ritter auf Map_Town für 100 Gold anheuert.
Sprite-Ordner: assets/Knight/ (120×80 px pro Frame).
"""

from __future__ import annotations

import os
import math
import pygame
from typing import List, Optional, Tuple, Any


class KnightCompanion(pygame.sprite.Sprite):
    """Begleiter-Ritter der dem Spieler folgt und Gegner angreift."""

    # --- Sprite-Sheet Konfiguration ---
    FRAME_W = 120
    FRAME_H = 80
    TARGET_H = 80

    # --- Kampfwerte ---
    MAX_HEALTH = 500
    ATTACK_DAMAGE = 10
    ATTACK_RANGE = 90          # Pixel – Nahkampf-Reichweite
    ATTACK_COOLDOWN = 1200     # ms zwischen Angriffen
    DETECTION_RANGE = 250      # Pixel – ab wann er Gegner verfolgt

    # --- Bewegung ---
    MOVE_SPEED = 160           # Pixel/s
    FOLLOW_DISTANCE = 90       # Pixel – gewünschter Abstand zum Spieler
    FOLLOW_CLOSE = 60          # Pixel – stehenbleiben wenn näher

    def __init__(self, x: int, y: int):
        super().__init__()

        self.name = "Ritter Konrad"
        self.pos_x = float(x)
        self.pos_y = float(y)

        # HP
        self.current_health = self.MAX_HEALTH
        self.max_health = self.MAX_HEALTH
        self.alive_status = True

        # Animations-Daten
        self.idle_frames: List[pygame.Surface] = []
        self.idle_frames_left: List[pygame.Surface] = []
        self.run_frames: List[pygame.Surface] = []
        self.run_frames_left: List[pygame.Surface] = []
        self.attack_frames: List[pygame.Surface] = []
        self.attack_frames_left: List[pygame.Surface] = []

        self._load_sprites()

        # Aktuelles Bild
        self.image = self.idle_frames[0] if self.idle_frames else self._make_placeholder()
        self.rect = self.image.get_rect()
        self.rect.midbottom = (int(self.pos_x), int(self.pos_y))
        self.hitbox = self.rect.inflate(-60, -30)

        # State
        self.state = "idle"          # idle | follow | attack
        self.facing_right = True
        self.frame_index = 0
        self.animation_timer = 0.0
        self.animation_speed = 0.1   # Sekunden/Frame

        # Kampf
        self.last_attack_time = 0
        self._attack_target: Optional[Any] = None
        self._attack_frame_total = 0  # Gesamtframes der Attack-Anim

        # Obstacle-Awareness (optional)
        self.obstacle_sprites: Optional[pygame.sprite.Group] = None

    # ==================================================================
    # Sprite Loading (wiederverwendet Knight-Assets)
    # ==================================================================
    @staticmethod
    def _get_asset_dir() -> str:
        return os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "assets", "Knight",
        )

    def _load_sheet(self, path: str) -> List[pygame.Surface]:
        """Zerlegt ein horizontales Sprite-Sheet in Frames."""
        try:
            sheet = pygame.image.load(path).convert_alpha()
        except Exception as e:
            print(f"⚠️ KnightComp Sheet Fehler ({os.path.basename(path)}): {e}")
            return []

        sw, sh = sheet.get_size()
        n = max(1, sw // self.FRAME_W)
        scale = self.TARGET_H / self.FRAME_H
        tw = max(1, int(self.FRAME_W * scale))

        frames: List[pygame.Surface] = []
        for i in range(n):
            sub = sheet.subsurface(pygame.Rect(i * self.FRAME_W, 0, self.FRAME_W, self.FRAME_H))
            if scale != 1.0:
                sub = pygame.transform.smoothscale(sub, (tw, self.TARGET_H))
            frames.append(sub)
        return frames

    @staticmethod
    def _flip_frames(frames: List[pygame.Surface]) -> List[pygame.Surface]:
        return [pygame.transform.flip(f, True, False) for f in frames]

    def _load_sprites(self):
        ad = self._get_asset_dir()
        if not os.path.isdir(ad):
            ph = self._make_placeholder()
            self.idle_frames = [ph]
            self.idle_frames_left = [pygame.transform.flip(ph, True, False)]
            self.run_frames = self.idle_frames
            self.run_frames_left = self.idle_frames_left
            self.attack_frames = self.idle_frames
            self.attack_frames_left = self.idle_frames_left
            return

        # Idle
        p = os.path.join(ad, "_Idle.png")
        if os.path.isfile(p):
            self.idle_frames = self._load_sheet(p)
        # Run
        p = os.path.join(ad, "_Run.png")
        if os.path.isfile(p):
            self.run_frames = self._load_sheet(p)
        # Attack
        p = os.path.join(ad, "_Attack.png")
        if os.path.isfile(p):
            self.attack_frames = self._load_sheet(p)

        # Fallbacks
        if not self.idle_frames:
            self.idle_frames = [self._make_placeholder()]
        if not self.run_frames:
            self.run_frames = self.idle_frames
        if not self.attack_frames:
            self.attack_frames = self.idle_frames

        # Gespiegelte (links) Varianten
        self.idle_frames_left = self._flip_frames(self.idle_frames)
        self.run_frames_left = self._flip_frames(self.run_frames)
        self.attack_frames_left = self._flip_frames(self.attack_frames)
        self._attack_frame_total = len(self.attack_frames)

        print(f"⚔️  KnightCompanion Sprites: idle={len(self.idle_frames)}, "
              f"run={len(self.run_frames)}, attack={len(self.attack_frames)}")

    def _make_placeholder(self) -> pygame.Surface:
        w, h = 48, 72
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(s, (150, 150, 160), (10, 28, 28, 26))
        pygame.draw.rect(s, (160, 30, 30), (14, 30, 20, 22))
        pygame.draw.circle(s, (210, 175, 145), (24, 18), 11)
        pygame.draw.arc(s, (140, 140, 150), (13, 6, 22, 20), 0, math.pi, 4)
        pygame.draw.rect(s, (180, 180, 200), (38, 14, 3, 12))
        return s

    # ==================================================================
    # Hilfsfunktionen
    # ==================================================================
    def set_obstacles(self, group: pygame.sprite.Group):
        self.obstacle_sprites = group

    def take_damage(self, amount: int) -> bool:
        """Ritter nimmt Schaden. Gibt True zurück wenn noch am Leben."""
        if not self.alive_status:
            return False
        self.current_health = max(0, self.current_health - amount)
        if self.current_health <= 0:
            self.alive_status = False
            self.state = "idle"
            print(f"💀 {self.name} ist gefallen!")
        return self.alive_status

    def is_alive(self) -> bool:
        return self.alive_status

    def get_health(self) -> int:
        return self.current_health

    # ==================================================================
    # AI – Update
    # ==================================================================
    def update(self, dt: float, player, enemies=None):
        """Hauptupdate: Gegner suchen → angreifen ODER Spieler folgen."""
        if not self.alive_status:
            return

        if dt is None or dt <= 0:
            dt = 1 / 60

        current_time = pygame.time.get_ticks()
        player_cx = player.rect.centerx
        player_cy = player.rect.centery
        dx_p = player_cx - self.pos_x
        dy_p = player_cy - self.pos_y
        dist_player = math.hypot(dx_p, dy_p)

        # --- 1. Nächsten lebenden Gegner in Reichweite finden ---
        target = None
        target_dist = float('inf')
        if enemies:
            for e in enemies:
                if not getattr(e, 'alive_status', False):
                    continue
                ex = e.rect.centerx
                ey = e.rect.centery
                d = math.hypot(ex - self.pos_x, ey - self.pos_y)
                if d < self.DETECTION_RANGE and d < target_dist:
                    target = e
                    target_dist = d

        # --- 2. Angreifen wenn Gegner in Nahkampf-Reichweite ---
        if target and target_dist <= self.ATTACK_RANGE:
            self.state = "attack"
            self.facing_right = (target.rect.centerx >= self.pos_x)
            self._attack_target = target

            if current_time - self.last_attack_time >= self.ATTACK_COOLDOWN:
                self.last_attack_time = current_time
                self.frame_index = 0  # Attack-Anim neustarten
                # Schaden zufügen
                if hasattr(target, 'take_damage'):
                    target.take_damage(self.ATTACK_DAMAGE)
                    # print(f"⚔️ {self.name} trifft {getattr(target, 'name', 'Gegner')} für {self.ATTACK_DAMAGE}!")

        # --- 3. Gegner verfolgen wenn in Sichtweite ---
        elif target and target_dist > self.ATTACK_RANGE:
            self.state = "follow"
            self._move_toward(target.rect.centerx, target.rect.centery, dt)

        # --- 4. Spieler folgen wenn zu weit weg ---
        elif dist_player > self.FOLLOW_DISTANCE:
            self.state = "follow"
            self._move_toward(player_cx, player_cy, dt, stop_distance=self.FOLLOW_CLOSE)

        # --- 5. Idle ---
        else:
            self.state = "idle"
            # Richtung zum Spieler beibehalten
            if abs(dx_p) > 5:
                self.facing_right = dx_p > 0

        # Animation aktualisieren
        self._animate(dt)

        # Rect synchronisieren
        self.rect.midbottom = (int(self.pos_x), int(self.pos_y))
        self.hitbox = self.rect.inflate(-60, -30)

    def _move_toward(self, tx: float, ty: float, dt: float, stop_distance: float = 0):
        """Bewegt sich Richtung Ziel."""
        dx = tx - self.pos_x
        dy = ty - self.pos_y
        dist = math.hypot(dx, dy)
        if dist <= stop_distance or dist < 1:
            return
        # Normalisieren
        nx = dx / dist
        ny = dy / dist

        move_x = nx * self.MOVE_SPEED * dt
        move_y = ny * self.MOVE_SPEED * dt

        new_x = self.pos_x + move_x
        new_y = self.pos_y + move_y

        # Einfache Kollisionsprüfung mit Hindernissen
        if self.obstacle_sprites:
            test_rect = self.rect.copy()
            test_rect.midbottom = (int(new_x), int(new_y))
            test_hitbox = test_rect.inflate(-60, -30)
            blocked = False
            for obs in self.obstacle_sprites:
                if test_hitbox.colliderect(obs.rect):
                    blocked = True
                    break
            if blocked:
                # Versuche nur horizontale oder vertikale Bewegung
                test_rect.midbottom = (int(new_x), int(self.pos_y))
                test_hitbox = test_rect.inflate(-60, -30)
                h_ok = not any(test_hitbox.colliderect(o.rect) for o in self.obstacle_sprites)
                test_rect.midbottom = (int(self.pos_x), int(new_y))
                test_hitbox = test_rect.inflate(-60, -30)
                v_ok = not any(test_hitbox.colliderect(o.rect) for o in self.obstacle_sprites)
                if h_ok:
                    new_y = self.pos_y
                elif v_ok:
                    new_x = self.pos_x
                else:
                    return  # Komplett blockiert

        self.pos_x = new_x
        self.pos_y = new_y
        self.facing_right = (dx > 0)

    # ==================================================================
    # Animation
    # ==================================================================
    def _get_current_frames(self) -> List[pygame.Surface]:
        if self.state == "attack":
            return self.attack_frames if self.facing_right else self.attack_frames_left
        elif self.state == "follow":
            return self.run_frames if self.facing_right else self.run_frames_left
        else:
            return self.idle_frames if self.facing_right else self.idle_frames_left

    def _animate(self, dt: float):
        frames = self._get_current_frames()
        if not frames:
            return
        speed = 0.06 if self.state == "attack" else (0.08 if self.state == "follow" else 0.1)
        self.animation_timer += dt
        if self.animation_timer >= speed:
            self.animation_timer = 0.0
            self.frame_index = (self.frame_index + 1) % len(frames)
        self.image = frames[self.frame_index % len(frames)]

    # ==================================================================
    # Rendering
    # ==================================================================
    def draw(self, screen: pygame.Surface, camera):
        """Zeichnet den Ritter-Begleiter."""
        if not self.alive_status:
            return
        screen_pos = camera.apply(self)
        screen.blit(self.image, (screen_pos.x, screen_pos.y))

        # Mini-Healthbar über dem Kopf
        self._draw_health_bar(screen, screen_pos)

    def _draw_health_bar(self, screen: pygame.Surface, screen_pos: pygame.Rect):
        """Zeichnet eine kleine HP-Leiste über dem Ritter."""
        bar_w = 50
        bar_h = 5
        bx = screen_pos.centerx - bar_w // 2
        by = screen_pos.top - 8

        ratio = max(0, self.current_health / self.max_health)

        # Hintergrund
        pygame.draw.rect(screen, (40, 40, 40), (bx - 1, by - 1, bar_w + 2, bar_h + 2))
        # HP-Füllstand (grün → gelb → rot)
        if ratio > 0.5:
            color = (60, 200, 80)
        elif ratio > 0.25:
            color = (220, 200, 40)
        else:
            color = (220, 50, 40)
        pygame.draw.rect(screen, color, (bx, by, int(bar_w * ratio), bar_h))
        # Rahmen
        pygame.draw.rect(screen, (180, 180, 180), (bx - 1, by - 1, bar_w + 2, bar_h + 2), 1)

    def draw_name(self, screen: pygame.Surface, camera):
        """Zeichnet den Namen über dem Ritter (optional)."""
        if not self.alive_status:
            return
        screen_pos = camera.apply(self)
        try:
            font = pygame.font.Font(None, 18)
            text = font.render(self.name, True, (255, 220, 100))
            tr = text.get_rect(center=(screen_pos.centerx, screen_pos.top - 16))
            screen.blit(text, tr)
        except Exception:
            pass
