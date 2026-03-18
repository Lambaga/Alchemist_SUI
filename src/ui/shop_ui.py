# -*- coding: utf-8 -*-
"""
Shop UI – Vollbild-Overlay zum Kaufen von Upgrades.

Gesteuert per ↑/↓ Navigation, C/Enter zum Kaufen, Escape zum Schließen.
Pixel-Art-Stil passend zum restlichen UI.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Optional

import pygame

from managers.font_manager import get_font_manager

if TYPE_CHECKING:
    from systems.shop_system import ShopManager


class ShopUI:
    """Modales Shop-Menü-Overlay."""

    # Layout
    PANEL_WIDTH_RATIO = 0.55
    PANEL_MAX_WIDTH = 520
    ROW_HEIGHT = 56
    PADDING = 18
    HEADER_HEIGHT = 50

    # Farben
    BG_DIM = (0, 0, 0, 160)
    PANEL_TOP = (22, 28, 55)
    PANEL_BOT = (12, 16, 35)
    BORDER_OUTER = (55, 75, 140)
    BORDER_INNER = (85, 115, 190)
    GOLD = (255, 215, 0)
    TITLE_COLOR = (255, 220, 80)
    COIN_COLOR = (255, 215, 0)
    TEXT_COLOR = (220, 225, 240)
    DESC_COLOR = (150, 165, 200)
    LOCKED_COLOR = (90, 90, 100)
    MAXED_COLOR = (80, 200, 100)
    PRICE_AFFORD = (100, 255, 100)
    PRICE_CANT = (255, 80, 80)
    HIGHLIGHT_BG = (40, 50, 90, 200)
    CORNER_ACCENT = (180, 140, 80)

    def __init__(self):
        fm = get_font_manager()
        self._font_title = fm.get_font(28)
        self._font_name = fm.get_font(22)
        self._font_desc = fm.get_font(16)
        self._font_price = fm.get_font(20)
        self._font_hint = fm.get_font(16)
        self._font_coins = fm.get_font(24)

        self.is_active = False
        self._selected_index = 0
        self._player = None  # Referenz zum Spieler
        self._shop_manager: Optional['ShopManager'] = None
        self._purchase_message = ""
        self._purchase_msg_timer = 0

    # ------------------------------------------------------------------
    # Öffnen / Schließen
    # ------------------------------------------------------------------
    def open(self, shop_manager: 'ShopManager', player) -> None:
        self.is_active = True
        self._shop_manager = shop_manager
        self._player = player
        self._selected_index = 0
        self._purchase_message = ""
        print("🏪 Shop geöffnet!")

    def close(self) -> None:
        self.is_active = False
        self._player = None
        print("🏪 Shop geschlossen")

    # ------------------------------------------------------------------
    # Event-Handling
    # ------------------------------------------------------------------
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Verarbeitet Events. Gibt True zurück wenn konsumiert."""
        if not self.is_active:
            return False

        if event.type == pygame.KEYDOWN:
            upgrades = self._shop_manager.get_upgrade_defs() if self._shop_manager else []
            count = len(upgrades)

            if event.key in (pygame.K_i, pygame.K_q):
                self.close()
                return True
            elif event.key in (pygame.K_UP, pygame.K_w):
                self._selected_index = (self._selected_index - 1) % count if count else 0
                return True
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self._selected_index = (self._selected_index + 1) % count if count else 0
                return True
            elif event.key in (pygame.K_z, pygame.K_RETURN, pygame.K_SPACE):
                self._try_buy()
                return True

        elif event.type == pygame.JOYBUTTONDOWN:
            if event.button == 1:  # B = close
                self.close()
                return True
            elif event.button == 0:  # A = buy
                self._try_buy()
                return True

        elif event.type == pygame.JOYHATMOTION:
            _, hat_y = event.value
            upgrades = self._shop_manager.get_upgrade_defs() if self._shop_manager else []
            count = len(upgrades)
            if hat_y == 1:
                self._selected_index = (self._selected_index - 1) % count if count else 0
                return True
            elif hat_y == -1:
                self._selected_index = (self._selected_index + 1) % count if count else 0
                return True

        return True  # Konsumiere alles wenn Shop offen ist

    def _try_buy(self):
        if not self._shop_manager or not self._player:
            return
        upgrades = self._shop_manager.get_upgrade_defs()
        if not upgrades or self._selected_index >= len(upgrades):
            return

        upgrade = upgrades[self._selected_index]
        success, msg = self._shop_manager.try_purchase(upgrade.id, self._player)
        self._purchase_message = msg
        self._purchase_msg_timer = pygame.time.get_ticks() + 2000

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------
    def update(self, dt: float = None):
        if self._purchase_msg_timer and pygame.time.get_ticks() > self._purchase_msg_timer:
            self._purchase_message = ""
            self._purchase_msg_timer = 0

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------
    def render(self, surface: pygame.Surface) -> None:
        if not self.is_active or not self._shop_manager:
            return

        sw, sh = surface.get_size()
        anim_time = pygame.time.get_ticks()

        # Hintergrund abdunkeln
        dim = pygame.Surface((sw, sh), pygame.SRCALPHA)
        dim.fill(self.BG_DIM)
        surface.blit(dim, (0, 0))

        upgrades = self._shop_manager.get_upgrade_defs()
        player = self._player

        # Panel-Größe
        panel_w = min(int(sw * self.PANEL_WIDTH_RATIO), self.PANEL_MAX_WIDTH)
        content_h = self.HEADER_HEIGHT + len(upgrades) * self.ROW_HEIGHT + 60  # +60 für Hints
        panel_h = min(content_h + self.PADDING * 2, sh - 60)
        px = (sw - panel_w) // 2
        py = (sh - panel_h) // 2

        # Panel-Hintergrund (Gradient)
        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        for row in range(panel_h):
            ratio = row / max(panel_h, 1)
            r = int(self.PANEL_TOP[0] * (1 - ratio) + self.PANEL_BOT[0] * ratio)
            g = int(self.PANEL_TOP[1] * (1 - ratio) + self.PANEL_BOT[1] * ratio)
            b = int(self.PANEL_TOP[2] * (1 - ratio) + self.PANEL_BOT[2] * ratio)
            pygame.draw.line(panel, (r, g, b, 235), (0, row), (panel_w, row))
        surface.blit(panel, (px, py))

        # Rahmen
        pygame.draw.rect(surface, self.BORDER_OUTER, (px - 2, py - 2, panel_w + 4, panel_h + 4), 2)
        pygame.draw.rect(surface, self.BORDER_INNER, (px, py, panel_w, panel_h), 2)

        # Gold-Ecken
        corner_len = 10
        for cx, cy, dx, dy in [
            (px + 3, py + 3, 1, 1), (px + panel_w - 4, py + 3, -1, 1),
            (px + 3, py + panel_h - 4, 1, -1), (px + panel_w - 4, py + panel_h - 4, -1, -1),
        ]:
            pygame.draw.line(surface, self.CORNER_ACCENT, (cx, cy), (cx + corner_len * dx, cy), 2)
            pygame.draw.line(surface, self.CORNER_ACCENT, (cx, cy), (cx, cy + corner_len * dy), 2)

        # ---- Header ----
        header_y = py + self.PADDING
        title_surf = self._font_title.render("🏪 Händler-Shop", True, self.TITLE_COLOR)
        surface.blit(title_surf, (px + self.PADDING, header_y))

        # Münzen-Anzeige rechts
        if player:
            coin_text = f"💰 {player.coins}"
            coin_surf = self._font_coins.render(coin_text, True, self.COIN_COLOR)
            surface.blit(coin_surf, (px + panel_w - self.PADDING - coin_surf.get_width(), header_y + 4))

        # Trennlinie
        line_y = header_y + title_surf.get_height() + 8
        pygame.draw.line(surface, self.BORDER_OUTER,
                         (px + self.PADDING, line_y),
                         (px + panel_w - self.PADDING, line_y), 1)

        # ---- Upgrade-Zeilen ----
        row_y = line_y + 10
        for i, upgrade in enumerate(upgrades):
            is_selected = (i == self._selected_index)
            is_maxed = self._shop_manager.is_maxed(upgrade.id)
            tier = self._shop_manager.get_next_tier(upgrade.id)
            current_tier_num = self._shop_manager.get_current_tier(upgrade.id)
            max_tiers = len(upgrade.tiers)

            # Highlight-Hintergrund
            row_rect = pygame.Rect(px + 6, row_y, panel_w - 12, self.ROW_HEIGHT - 4)
            if is_selected:
                hl = pygame.Surface((row_rect.width, row_rect.height), pygame.SRCALPHA)
                hl.fill(self.HIGHLIGHT_BG)
                surface.blit(hl, row_rect)
                # Animierter Rahmen
                glow = int(120 + 40 * math.sin(anim_time / 250))
                pygame.draw.rect(surface, (glow, glow, 200, 180), row_rect, 1, border_radius=3)

            # Icon + Name
            name_text = f"{upgrade.icon_char} {upgrade.name}"
            name_color = self.MAXED_COLOR if is_maxed else self.TEXT_COLOR
            name_surf = self._font_name.render(name_text, True, name_color)
            surface.blit(name_surf, (px + self.PADDING + 8, row_y + 4))

            # Stufen-Anzeige
            tier_text = f"Stufe {current_tier_num}/{max_tiers}"
            if is_maxed:
                tier_text = "MAX"
            tier_surf = self._font_desc.render(tier_text, True,
                                                self.MAXED_COLOR if is_maxed else self.DESC_COLOR)
            surface.blit(tier_surf, (px + self.PADDING + 8, row_y + 28))

            # Beschreibung / nächstes Upgrade
            if tier and not is_maxed:
                desc_surf = self._font_desc.render(tier.label, True, self.DESC_COLOR)
                mid_x = px + panel_w // 2 + 10
                surface.blit(desc_surf, (mid_x, row_y + 6))

                # Preis
                can_afford = player and player.coins >= tier.cost
                price_color = self.PRICE_AFFORD if can_afford else self.PRICE_CANT
                price_surf = self._font_price.render(f"💰 {tier.cost}", True, price_color)
                surface.blit(price_surf, (px + panel_w - self.PADDING - price_surf.get_width() - 4, row_y + 4))

            row_y += self.ROW_HEIGHT

        # ---- Kauf-Nachricht ----
        if self._purchase_message:
            msg_surf = self._font_name.render(self._purchase_message, True, self.GOLD)
            msg_rect = msg_surf.get_rect(center=(px + panel_w // 2, row_y + 8))
            # Hintergrund
            bg = msg_rect.inflate(16, 8)
            bg_s = pygame.Surface((bg.width, bg.height), pygame.SRCALPHA)
            bg_s.fill((0, 0, 0, 180))
            surface.blit(bg_s, bg)
            surface.blit(msg_surf, msg_rect)
            row_y += 30

        # ---- Hinweis-Zeile ----
        hints_y = py + panel_h - self.PADDING - 18
        hint_text = "↑↓ Auswahl  ·  1 Kaufen  ·  i Schließen"
        hint_surf = self._font_hint.render(hint_text, True, self.DESC_COLOR)
        hint_rect = hint_surf.get_rect(center=(px + panel_w // 2, hints_y))
        surface.blit(hint_surf, hint_rect)
