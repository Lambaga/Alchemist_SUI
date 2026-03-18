# -*- coding: utf-8 -*-
"""
Gambler NPC – Animated character with full sprite-sheet animations.

Sprite-Ordner: assets/Gambler/  (64×64 px Frames).

Animation states (from framerate chart):
  01_[Idle_I]          –  6 frames, Slow (200ms)
  02_[Idle_II]         –  9 frames, mixed (Slow/Normal/Slow)
  03_[Idle]to[Work]    –  3 frames, Normal (100ms)
  04_[Work_I_Loop]     – 10 frames, mixed (Normal/Fast/Normal)
  04_[Work_II_Loop]    – 14 frames, mixed (Normal/Fast/Normal)
  06_[Work]to[Idle]    –  3 frames, Normal (100ms)
  10_[Idle]to[Dialog]  –  3 frames, Normal (100ms)
  11_[Dialog]          – 10 frames, mixed
  12_[Dialog]to[Idle]  –  3 frames, Normal (100ms)
"""

from __future__ import annotations

import os
import pygame
from typing import Dict, List, Optional, Tuple


class GamblerNPC(pygame.sprite.Sprite):
    """Animated Gambler NPC with dialog and work animations."""

    INTERACTION_RADIUS = 100  # Pixel
    FRAME_SIZE = 64           # Each frame is 64×64

    # Display scale
    TARGET_H = 96             # Scaled up from 64 for visibility

    # Animation speed tiers (seconds per frame)
    SLOW = 0.200     # 200ms
    NORMAL = 0.100   # 100ms
    FAST = 0.050     # 50ms

    # State machine states
    STATE_IDLE_I = "idle_i"
    STATE_IDLE_II = "idle_ii"
    STATE_IDLE_TO_WORK = "idle_to_work"
    STATE_WORK_I_LOOP = "work_i_loop"
    STATE_WORK_II_LOOP = "work_ii_loop"
    STATE_WORK_TO_IDLE = "work_to_idle"
    STATE_IDLE_TO_DIALOG = "idle_to_dialog"
    STATE_DIALOG = "dialog"
    STATE_DIALOG_TO_IDLE = "dialog_to_idle"

    def __init__(self, x: int, y: int):
        super().__init__()

        self.name = "Die Kartenlegerin"
        self.pos_x = float(x)
        self.pos_y = float(y)

        # Animation storage: state_name → list of (surface, duration_sec)
        self.animations: Dict[str, List[Tuple[pygame.Surface, float]]] = {}

        # Load assets
        self._load_all_sprites()

        # State machine
        self.state = self.STATE_IDLE_I
        self.frame_index = 0
        self.animation_timer = 0.0
        self._in_dialog = False

        # Current image
        self.image = self._get_frame(0)
        self.rect = self.image.get_rect()
        self.rect.midbottom = (int(self.pos_x), int(self.pos_y))

        # Interaction
        self.can_interact = False
        self.interaction_radius = self.INTERACTION_RADIUS

        # Idle variation timer (alternate between Idle_I and Idle_II)
        self._idle_timer = 0.0
        self._idle_switch_interval = 4.0  # seconds between idle switches
        self._current_idle = 1  # 1 or 2

        # Work cycle timer
        self._work_timer = 0.0
        self._work_interval = 8.0   # seconds between work cycles
        self._work_loop_count = 0   # alternates Work_I and Work_II

        # Dialog loop counter
        self._dialog_loops = 0

    # ==================================================================
    # Sprite Loading
    # ==================================================================
    def _get_asset_dir(self) -> str:
        return os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "assets", "Gambler",
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
            print(f"⚠️ Gambler Sheet Fehler ({filename}): {e}")
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

            if per_frame_speeds and i < len(per_frame_speeds):
                spd = per_frame_speeds[i]
            else:
                spd = self.NORMAL
            frames.append((sub, spd))

        return frames

    def _load_all_sprites(self):
        """Load all Gambler animation sheets with per-frame timing from the chart."""
        ad = self._get_asset_dir()
        if not os.path.isdir(ad):
            print("⚠️ Gambler-Ordner nicht gefunden – verwende Platzhalter")
            ph = self._make_placeholder()
            self.animations[self.STATE_IDLE_I] = [(ph, self.SLOW)]
            return

        S, N, F = self.SLOW, self.NORMAL, self.FAST

        # 01_Idle_I: 6 frames, all Slow (light blue in chart)
        self.animations[self.STATE_IDLE_I] = self._load_sheet(
            "01_[Idle_I].png", [S] * 6)

        # 02_Idle_II: 9 frames (blue=Slow 3, green=Normal 3, blue=Slow 3)
        self.animations[self.STATE_IDLE_II] = self._load_sheet(
            "02_[Idle_II].png", [S, S, S, N, N, N, S, S, S])

        # 03_Idle→Work: 3 frames, all Normal
        self.animations[self.STATE_IDLE_TO_WORK] = self._load_sheet(
            "03_[Idle]to[Work].png", [N] * 3)

        # 04_Work_I_Loop: 10 frames (green=Normal 6, red=Fast 2, green=Normal 2)
        self.animations[self.STATE_WORK_I_LOOP] = self._load_sheet(
            "04_[Work_I_Loop].png", [N, N, N, N, N, N, F, F, N, N])

        # 04_Work_II_Loop: 14 frames (green=Normal 8, red=Fast 2, green=Normal 4)
        self.animations[self.STATE_WORK_II_LOOP] = self._load_sheet(
            "04_[Work_II_Loop].png", [N, N, N, N, N, N, N, N, F, F, N, N, N, N])

        # 06_Work→Idle: 3 frames, Normal
        self.animations[self.STATE_WORK_TO_IDLE] = self._load_sheet(
            "06_[Work]to[Idle].png", [N] * 3)

        # 10_Idle→Dialog: 3 frames, Normal
        self.animations[self.STATE_IDLE_TO_DIALOG] = self._load_sheet(
            "10_[Idle]to[Dialog].png", [N] * 3)

        # 11_Dialog: 10 frames (mixed: Slow start, Normal/Fast middle)
        self.animations[self.STATE_DIALOG] = self._load_sheet(
            "11_[Dialog].png", [S, S, N, N, N, N, F, F, N, N])

        # 12_Dialog→Idle: 3 frames, Normal
        self.animations[self.STATE_DIALOG_TO_IDLE] = self._load_sheet(
            "12_[Dialog]to[Idle].png", [N] * 3)

        loaded = sum(len(v) for v in self.animations.values())
        states = sum(1 for v in self.animations.values() if v)
        print(f"🎰 Gambler Sprites geladen: {states} Animationen, {loaded} Frames total")

        # Fallback
        if not self.animations.get(self.STATE_IDLE_I):
            self.animations[self.STATE_IDLE_I] = [(self._make_placeholder(), S)]

    def _make_placeholder(self) -> pygame.Surface:
        """Simple placeholder if no assets found."""
        w, h = 48, 64
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.ellipse(s, (30, 30, 40), (8, 24, 32, 40))
        pygame.draw.circle(s, (200, 160, 130), (24, 16), 12)
        pygame.draw.rect(s, (20, 20, 25), (12, 0, 24, 12))
        pygame.draw.rect(s, (20, 20, 25), (8, 10, 32, 4))
        pygame.draw.circle(s, (200, 50, 50), (20, 14), 2)
        pygame.draw.circle(s, (200, 50, 50), (28, 14), 2)
        pygame.draw.rect(s, (255, 255, 255), (34, 32, 10, 14))
        return s

    # ==================================================================
    # Helpers
    # ==================================================================
    def _get_frame(self, idx: int) -> pygame.Surface:
        frames = self.animations.get(self.state)
        if not frames:
            frames = self.animations.get(self.STATE_IDLE_I, [])
        if not frames:
            return self._make_placeholder()
        return frames[idx % len(frames)][0]

    def _get_speed(self, idx: int) -> float:
        frames = self.animations.get(self.state)
        if not frames:
            return self.SLOW
        return frames[idx % len(frames)][1]

    def _frame_count(self, state: Optional[str] = None) -> int:
        st = state or self.state
        frames = self.animations.get(st)
        return len(frames) if frames else 1

    def _change_state(self, new_state: str):
        if new_state == self.state:
            return
        self.state = new_state
        self.frame_index = 0
        self.animation_timer = 0.0

    # ==================================================================
    # Public interface — called by Level
    # ==================================================================
    def start_dialog(self):
        """Called when the player talks to the gambler."""
        if self._in_dialog:
            return
        self._in_dialog = True
        self._dialog_loops = 0
        self._change_state(self.STATE_IDLE_TO_DIALOG)

    def end_dialog(self):
        """Called when blackjack / dialog closes."""
        if not self._in_dialog:
            return
        self._in_dialog = False
        self._change_state(self.STATE_DIALOG_TO_IDLE)

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

        # --- IDLE I ---
        if self.state == self.STATE_IDLE_I:
            self.frame_index %= n  # loop
            if not self._in_dialog:
                self._idle_timer += dt
                self._work_timer += dt
                # Switch to Idle_II after interval
                if self._idle_timer >= self._idle_switch_interval:
                    self._idle_timer = 0.0
                    self._change_state(self.STATE_IDLE_II)
                # Start work cycle
                elif self._work_timer >= self._work_interval:
                    self._work_timer = 0.0
                    self._change_state(self.STATE_IDLE_TO_WORK)

        # --- IDLE II ---
        elif self.state == self.STATE_IDLE_II:
            self.frame_index %= n  # loop
            if not self._in_dialog:
                self._idle_timer += dt
                self._work_timer += dt
                # Switch back to Idle_I after interval
                if self._idle_timer >= self._idle_switch_interval:
                    self._idle_timer = 0.0
                    self._change_state(self.STATE_IDLE_I)
                # Start work cycle
                elif self._work_timer >= self._work_interval:
                    self._work_timer = 0.0
                    self._change_state(self.STATE_IDLE_TO_WORK)

        # --- IDLE → WORK (transition, play once) ---
        elif self.state == self.STATE_IDLE_TO_WORK:
            if self.frame_index >= n:
                # Alternate between Work_I and Work_II
                self._work_loop_count += 1
                if self._work_loop_count % 2 == 1:
                    self._change_state(self.STATE_WORK_I_LOOP)
                else:
                    self._change_state(self.STATE_WORK_II_LOOP)

        # --- WORK I LOOP (play twice then go back) ---
        elif self.state == self.STATE_WORK_I_LOOP:
            if self.frame_index >= n * 2:
                self._change_state(self.STATE_WORK_TO_IDLE)
            else:
                self.frame_index %= n

        # --- WORK II LOOP (play twice then go back) ---
        elif self.state == self.STATE_WORK_II_LOOP:
            if self.frame_index >= n * 2:
                self._change_state(self.STATE_WORK_TO_IDLE)
            else:
                self.frame_index %= n

        # --- WORK → IDLE (transition, play once) ---
        elif self.state == self.STATE_WORK_TO_IDLE:
            if self.frame_index >= n:
                self._change_state(self.STATE_IDLE_I)
                self._idle_timer = 0.0

        # --- IDLE → DIALOG (transition, play once) ---
        elif self.state == self.STATE_IDLE_TO_DIALOG:
            if self.frame_index >= n:
                self._dialog_loops = 0
                self._change_state(self.STATE_DIALOG)

        # --- DIALOG (loop while in dialog) ---
        elif self.state == self.STATE_DIALOG:
            if self.frame_index >= n:
                self._dialog_loops += 1
                self.frame_index = 0  # loop
            if not self._in_dialog:
                self._change_state(self.STATE_DIALOG_TO_IDLE)

        # --- DIALOG → IDLE (exit transition) ---
        elif self.state == self.STATE_DIALOG_TO_IDLE:
            if self.frame_index >= n:
                self._change_state(self.STATE_IDLE_I)
                self._work_timer = 0.0
                self._idle_timer = 0.0

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

    def get_interaction_prompt(self) -> str:
        return "[ I ] Sprechen"

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
        prompt_y = screen_pos.top - 25

        try:
            font = pygame.font.Font(None, 20)
            text = font.render(self.get_interaction_prompt(), True, (255, 220, 100))
            text_rect = text.get_rect(center=(prompt_x, prompt_y))

            bg_rect = text_rect.inflate(10, 6)
            bg = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
            bg.fill((0, 0, 0, 180))
            screen.blit(bg, bg_rect)
            pygame.draw.rect(screen, (255, 200, 50), bg_rect, 1, border_radius=4)
            screen.blit(text, text_rect)
        except Exception:
            pass
