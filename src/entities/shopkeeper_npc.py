# -*- coding: utf-8 -*-
"""
Shopkeeper NPC – Animated Merchant with full sprite-sheet animations.

Sprite-Ordner: assets/Merchant/  (64×64 px Frames).

Animation states (from framerate chart):
  01_[Idle]              – 12 frames, Slow (200ms)
  02_[Idle]to[Work]      –  3 frames, Normal (100ms)
  03_[Work_Loop]         – 10 frames, mixed speeds
  04_[Work]to[Idle]      –  3 frames, Normal (100ms)
  10_[Idle]to[Dialog_I]  –  3 frames, Normal (100ms)
  11_[Dialog_I[Stand]]   –  1 frame,  static
  12_[Dialog_I[Nods]]    –  5 frames, mixed speeds
  13_[Dialog_I]to[Dialog_II] – 4 frames, Normal (100ms)
  14_[Dialog_II[Stand]]  –  1 frame,  static
  15_[Dialog_II[Nods]]   –  5 frames, mixed speeds
  16_[Dialog_II]to[Dialog_I] – 4 frames, Normal (100ms)
  20_[Dialog_I]to[Idle]  –  3 frames, Normal (100ms)
"""

from __future__ import annotations

import os
import pygame
from typing import Dict, List, Optional, Tuple


class ShopkeeperNPC(pygame.sprite.Sprite):
    """Animated Merchant NPC with dialog and work animations."""

    INTERACTION_RADIUS = 100  # Pixel
    FRAME_SIZE = 64           # Each frame is 64×64

    # Display scale: how tall the NPC appears in-game
    TARGET_H = 96             # Scaled up from 64 for visibility

    # Animation speed tiers (seconds per frame)
    SLOW = 0.200     # 200ms
    NORMAL = 0.100   # 100ms
    FAST = 0.050     # 50ms

    # State machine states
    STATE_IDLE = "idle"
    STATE_IDLE_TO_WORK = "idle_to_work"
    STATE_WORK_LOOP = "work_loop"
    STATE_WORK_TO_IDLE = "work_to_idle"
    STATE_IDLE_TO_DIALOG_I = "idle_to_dialog_i"
    STATE_DIALOG_I_STAND = "dialog_i_stand"
    STATE_DIALOG_I_NODS = "dialog_i_nods"
    STATE_DIALOG_I_TO_II = "dialog_i_to_ii"
    STATE_DIALOG_II_STAND = "dialog_ii_stand"
    STATE_DIALOG_II_NODS = "dialog_ii_nods"
    STATE_DIALOG_II_TO_I = "dialog_ii_to_i"
    STATE_DIALOG_I_TO_IDLE = "dialog_i_to_idle"

    def __init__(self, x: int, y: int):
        super().__init__()

        self.name = "Händler"
        self.pos_x = float(x)
        self.pos_y = float(y)

        # Animation storage: state_name → list of (surface, duration_sec)
        self.animations: Dict[str, List[Tuple[pygame.Surface, float]]] = {}

        # Load assets
        self._load_all_sprites()

        # State machine
        self.state = self.STATE_IDLE
        self.frame_index = 0
        self.animation_timer = 0.0
        self._in_dialog = False         # True while dialog/shop is open
        self._dialog_nod_timer = 0.0    # Timer to switch between stand/nods
        self._dialog_nod_interval = 2.0 # Seconds between nod cycles
        self._dialog_pose = 1           # 1 or 2 (Dialog_I or Dialog_II)

        # Current image
        self.image = self._get_frame(0)
        self.rect = self.image.get_rect()
        self.rect.midbottom = (int(self.pos_x), int(self.pos_y))

        # Interaction
        self.can_interact = False

        # Work cycle timer (idle → work → idle periodically when not talking)
        self._work_timer = 0.0
        self._work_interval = 6.0   # seconds between work cycles

    # ==================================================================
    # Sprite Loading
    # ==================================================================
    def _get_asset_dir(self) -> str:
        return os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "assets", "Merchant",
        )

    def _load_sheet(self, filename: str, per_frame_speeds: Optional[List[float]] = None
                    ) -> List[Tuple[pygame.Surface, float]]:
        """Load a horizontal sprite sheet and split into (surface, duration) tuples."""
        path = os.path.join(self._get_asset_dir(), filename)
        if not os.path.isfile(path):
            return []

        try:
            sheet = pygame.image.load(path).convert_alpha()
        except Exception as e:
            print(f"⚠️ Merchant Sheet Fehler ({filename}): {e}")
            return []

        sw, sh = sheet.get_size()
        n = max(1, sw // self.FRAME_SIZE)
        scale = self.TARGET_H / self.FRAME_SIZE
        tw = max(1, int(self.FRAME_SIZE * scale))

        frames: List[Tuple[pygame.Surface, float]] = []
        for i in range(n):
            sub = sheet.subsurface(pygame.Rect(
                i * self.FRAME_SIZE, 0, self.FRAME_SIZE, self.FRAME_SIZE
            ))
            if scale != 1.0:
                sub = pygame.transform.smoothscale(sub, (tw, self.TARGET_H))

            # Determine speed for this frame
            if per_frame_speeds and i < len(per_frame_speeds):
                spd = per_frame_speeds[i]
            else:
                spd = self.NORMAL  # fallback
            frames.append((sub, spd))

        return frames

    def _load_all_sprites(self):
        """Load all Merchant animation sheets with per-frame timing from the chart."""
        ad = self._get_asset_dir()
        if not os.path.isdir(ad):
            print("⚠️ Merchant-Ordner nicht gefunden – verwende Platzhalter")
            ph = self._make_placeholder()
            self.animations[self.STATE_IDLE] = [(ph, self.SLOW)]
            return

        S, N, F = self.SLOW, self.NORMAL, self.FAST

        # 01_Idle: 12 frames, all Slow (green in chart)
        self.animations[self.STATE_IDLE] = self._load_sheet(
            "01_[Idle].png", [S] * 12)

        # 02_Idle→Work: 3 frames, all Normal
        self.animations[self.STATE_IDLE_TO_WORK] = self._load_sheet(
            "02_[Idle]to[Work].png", [N] * 3)

        # 03_Work_Loop: 10 frames (from chart: 6 green=Slow, 2 red=Fast, 2 green=Slow)
        self.animations[self.STATE_WORK_LOOP] = self._load_sheet(
            "03_[Work_Loop].png", [S, S, S, S, S, S, F, F, S, S])

        # 04_Work→Idle: 3 frames, Normal
        self.animations[self.STATE_WORK_TO_IDLE] = self._load_sheet(
            "04_[Work]to[Idle].png", [N] * 3)

        # 10_Idle→Dialog_I: 3 frames, Normal
        self.animations[self.STATE_IDLE_TO_DIALOG_I] = self._load_sheet(
            "10_[Idle]to[Dialog_I].png", [N] * 3)

        # 11_Dialog_I Stand: 1 frame, static
        self.animations[self.STATE_DIALOG_I_STAND] = self._load_sheet(
            "11_[Dialog_I[Stand]].png", [S])

        # 12_Dialog_I Nods: 5 frames (from chart: 3 green=Slow, 2 red=Fast)
        self.animations[self.STATE_DIALOG_I_NODS] = self._load_sheet(
            "12_[Dialog_I[Nods]].png", [S, S, S, F, F])

        # 13_Dialog_I→Dialog_II: 4 frames, Normal
        self.animations[self.STATE_DIALOG_I_TO_II] = self._load_sheet(
            "13_[Dialog_I]to[Dialog_II].png", [N] * 4)

        # 14_Dialog_II Stand: 1 frame, static
        self.animations[self.STATE_DIALOG_II_STAND] = self._load_sheet(
            "14_[Dialog_II[Stand]].png", [S])

        # 15_Dialog_II Nods: 5 frames (3 green=Slow, 2 red=Fast)
        self.animations[self.STATE_DIALOG_II_NODS] = self._load_sheet(
            "15_[Dialog_II[Nods]].png", [S, S, S, F, F])

        # 16_Dialog_II→Dialog_I: 4 frames, Normal
        self.animations[self.STATE_DIALOG_II_TO_I] = self._load_sheet(
            "16_[Dialog_II]to[Dialog_I].png", [N] * 4)

        # 20_Dialog_I→Idle: 3 frames, Normal
        self.animations[self.STATE_DIALOG_I_TO_IDLE] = self._load_sheet(
            "20_[Dialog_I]to[Idle].png", [N] * 3)

        loaded = sum(len(v) for v in self.animations.values())
        states = sum(1 for v in self.animations.values() if v)
        print(f"🏪 Merchant Sprites geladen: {states} Animationen, {loaded} Frames total")

        # Fallback if idle was empty
        if not self.animations.get(self.STATE_IDLE):
            self.animations[self.STATE_IDLE] = [(self._make_placeholder(), S)]

    def _make_placeholder(self) -> pygame.Surface:
        """Simple placeholder if no assets found."""
        w, h = 48, 72
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.ellipse(s, (100, 70, 30), (6, 28, 36, 44))
        pygame.draw.circle(s, (210, 175, 140), (24, 18), 13)
        pygame.draw.ellipse(s, (160, 120, 50), (10, 2, 28, 18))
        pygame.draw.circle(s, (60, 200, 120), (24, 8), 3)
        pygame.draw.circle(s, (40, 40, 40), (19, 17), 2)
        pygame.draw.circle(s, (40, 40, 40), (29, 17), 2)
        pygame.draw.circle(s, (180, 140, 60), (38, 46), 8)
        pygame.draw.circle(s, (255, 215, 0), (38, 46), 3)
        return s

    # ==================================================================
    # Helpers
    # ==================================================================
    def _get_frame(self, idx: int) -> pygame.Surface:
        """Get the surface for the current frame in the current state."""
        frames = self.animations.get(self.state)
        if not frames:
            frames = self.animations.get(self.STATE_IDLE, [])
        if not frames:
            return self._make_placeholder()
        return frames[idx % len(frames)][0]

    def _get_speed(self, idx: int) -> float:
        """Get the duration for the current frame."""
        frames = self.animations.get(self.state)
        if not frames:
            return self.SLOW
        return frames[idx % len(frames)][1]

    def _frame_count(self, state: Optional[str] = None) -> int:
        st = state or self.state
        frames = self.animations.get(st)
        return len(frames) if frames else 1

    def _change_state(self, new_state: str):
        """Transition to a new animation state."""
        if new_state == self.state:
            return
        self.state = new_state
        self.frame_index = 0
        self.animation_timer = 0.0

    # ==================================================================
    # Public interface — called by Level
    # ==================================================================
    def start_dialog(self):
        """Called when the player opens the shop / talks to the merchant."""
        if self._in_dialog:
            return
        self._in_dialog = True
        self._dialog_pose = 1
        self._dialog_nod_timer = 0.0
        # Transition: idle/work → dialog_I
        self._change_state(self.STATE_IDLE_TO_DIALOG_I)

    def end_dialog(self):
        """Called when the shop / dialog closes."""
        if not self._in_dialog:
            return
        self._in_dialog = False
        # Transition back to idle
        if self._dialog_pose == 2:
            self._change_state(self.STATE_DIALOG_II_TO_I)
        else:
            self._change_state(self.STATE_DIALOG_I_TO_IDLE)

    # ==================================================================
    # Update (state machine)
    # ==================================================================
    def update(self, dt: float = None):
        if dt is None:
            dt = 1 / 60

        self.animation_timer += dt
        speed = self._get_speed(self.frame_index)
        n = self._frame_count()

        if self.animation_timer >= speed:
            self.animation_timer -= speed
            self.frame_index += 1

        # ---- State machine transitions ----

        # --- IDLE ---
        if self.state == self.STATE_IDLE:
            self.frame_index %= n  # loop
            if not self._in_dialog:
                self._work_timer += dt
                if self._work_timer >= self._work_interval:
                    self._work_timer = 0.0
                    self._change_state(self.STATE_IDLE_TO_WORK)

        # --- IDLE → WORK (transition, play once) ---
        elif self.state == self.STATE_IDLE_TO_WORK:
            if self.frame_index >= n:
                self._change_state(self.STATE_WORK_LOOP)

        # --- WORK LOOP (play twice then go back) ---
        elif self.state == self.STATE_WORK_LOOP:
            if self.frame_index >= n * 2:
                self._change_state(self.STATE_WORK_TO_IDLE)
            else:
                self.frame_index %= n

        # --- WORK → IDLE (transition, play once) ---
        elif self.state == self.STATE_WORK_TO_IDLE:
            if self.frame_index >= n:
                self._change_state(self.STATE_IDLE)

        # --- IDLE → DIALOG_I (transition, play once) ---
        elif self.state == self.STATE_IDLE_TO_DIALOG_I:
            if self.frame_index >= n:
                self._dialog_pose = 1
                self._dialog_nod_timer = 0.0
                self._change_state(self.STATE_DIALOG_I_STAND)

        # --- DIALOG_I STAND (static, periodically nod) ---
        elif self.state == self.STATE_DIALOG_I_STAND:
            self.frame_index = 0
            if self._in_dialog:
                self._dialog_nod_timer += dt
                if self._dialog_nod_timer >= self._dialog_nod_interval:
                    self._dialog_nod_timer = 0.0
                    self._change_state(self.STATE_DIALOG_I_NODS)

        # --- DIALOG_I NODS (play once, then switch pose) ---
        elif self.state == self.STATE_DIALOG_I_NODS:
            if self.frame_index >= n:
                # Alternate to Dialog_II
                self._dialog_pose = 2
                self._change_state(self.STATE_DIALOG_I_TO_II)

        # --- DIALOG_I → DIALOG_II (transition) ---
        elif self.state == self.STATE_DIALOG_I_TO_II:
            if self.frame_index >= n:
                self._dialog_pose = 2
                self._dialog_nod_timer = 0.0
                self._change_state(self.STATE_DIALOG_II_STAND)

        # --- DIALOG_II STAND ---
        elif self.state == self.STATE_DIALOG_II_STAND:
            self.frame_index = 0
            if self._in_dialog:
                self._dialog_nod_timer += dt
                if self._dialog_nod_timer >= self._dialog_nod_interval:
                    self._dialog_nod_timer = 0.0
                    self._change_state(self.STATE_DIALOG_II_NODS)

        # --- DIALOG_II NODS ---
        elif self.state == self.STATE_DIALOG_II_NODS:
            if self.frame_index >= n:
                # Switch back to Dialog_I
                self._dialog_pose = 1
                self._change_state(self.STATE_DIALOG_II_TO_I)

        # --- DIALOG_II → DIALOG_I ---
        elif self.state == self.STATE_DIALOG_II_TO_I:
            if self.frame_index >= n:
                if not self._in_dialog:
                    self._change_state(self.STATE_DIALOG_I_TO_IDLE)
                else:
                    self._dialog_pose = 1
                    self._dialog_nod_timer = 0.0
                    self._change_state(self.STATE_DIALOG_I_STAND)

        # --- DIALOG_I → IDLE (exit transition) ---
        elif self.state == self.STATE_DIALOG_I_TO_IDLE:
            if self.frame_index >= n:
                self._change_state(self.STATE_IDLE)
                self._work_timer = 0.0

        # Update current image
        actual_idx = self.frame_index % self._frame_count()
        self.image = self._get_frame(actual_idx)

        # Keep rect anchored
        old_mb = self.rect.midbottom
        self.rect = self.image.get_rect()
        self.rect.midbottom = old_mb

    # ==================================================================
    # Interaction
    # ==================================================================
    def check_player_nearby(self, player_pos: Tuple[float, float]) -> bool:
        dx = player_pos[0] - self.pos_x
        dy = player_pos[1] - self.pos_y
        distance = (dx * dx + dy * dy) ** 0.5
        self.can_interact = distance <= self.INTERACTION_RADIUS
        return self.can_interact

    # ==================================================================
    # Rendering
    # ==================================================================
    def draw(self, screen: pygame.Surface, camera):
        screen_pos = camera.apply(self)
        screen.blit(self.image, (screen_pos.x, screen_pos.y))

    def draw_interaction_prompt(self, screen: pygame.Surface, camera):
        if not self.can_interact or self._in_dialog:
            return
        screen_pos = camera.apply(self)
        prompt_x = screen_pos.centerx
        prompt_y = screen_pos.top + 20

        try:
            font = pygame.font.Font(None, 20)
            text = font.render("[ i ] Shop", True, (255, 220, 100))
            text_rect = text.get_rect(center=(prompt_x, prompt_y))

            bg_rect = text_rect.inflate(10, 6)
            bg = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
            bg.fill((0, 0, 0, 180))
            screen.blit(bg, bg_rect)
            pygame.draw.rect(screen, (255, 200, 50), bg_rect, 1, border_radius=4)
            screen.blit(text, text_rect)
        except Exception:
            pass
