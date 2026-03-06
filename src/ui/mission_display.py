# -*- coding: utf-8 -*-
"""
Mission Display – HUD-Overlay oben rechts.

Zeigt die aktive Mission (Quest) mit Titel, Auftraggeber und
einer Checkliste der Ziele an.  Passt sich visuell dem
Pixel-Art-Stil des restlichen UI an (Gradient-BG, Glow-Border).
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Optional

import pygame

from managers.font_manager import get_font_manager

if TYPE_CHECKING:
    from systems.quest_manager import QuestManager


class MissionDisplay:
    """Zeichnet die aktive Missions-Anzeige in der oberen rechten Ecke."""

    # Layout-Konstanten
    MARGIN_RIGHT = 14         # Abstand zum rechten Rand
    MARGIN_TOP = 14           # Abstand zum oberen Rand
    PADDING_X = 14            # Innenabstand horizontal
    PADDING_Y = 10            # Innenabstand vertikal
    LINE_GAP = 4              # Abstand zwischen Zeilen
    MIN_WIDTH = 230           # Mindestbreite des Panels
    ICON_SIZE = 14            # Checkbox-Größe

    # Farben (passend zum restlichen UI)
    BG_TOP = (20, 25, 50)
    BG_BOT = (10, 14, 30)
    BORDER_OUTER = (60, 90, 160)
    BORDER_INNER = (90, 130, 200)
    TITLE_COLOR = (255, 220, 80)      # Gold
    NPC_COLOR = (160, 180, 220)       # Helles Blau-Grau
    OBJ_COLOR = (220, 220, 230)       # Fast weiß
    OBJ_DONE_COLOR = (100, 200, 100)  # Grün
    CHECK_COLOR = (80, 220, 80)       # Grünes Häkchen
    BOX_COLOR = (100, 110, 140)       # Leere Checkbox

    def __init__(self):
        fm = get_font_manager()
        self._font_title = fm.get_font(20)
        self._font_npc = fm.get_font(16)
        self._font_obj = fm.get_font(16)

        # Einblend-Animation
        self._show_alpha = 0          # 0..255
        self._target_alpha = 0
        self._fade_speed = 8          # Pro Frame

        # Kill-Counter (von Level gesetzt)
        self._kill_current = 0
        self._kill_total = 0
        self._kill_active = False

        # Cache
        self._cached_surface: Optional[pygame.Surface] = None
        self._cache_key = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def set_kill_counter(self, current: int, total: int) -> None:
        """Setzt den Kill-Counter (z.B. für Map_Town)."""
        self._kill_current = current
        self._kill_total = total
        self._kill_active = True

    def clear_kill_counter(self) -> None:
        """Deaktiviert den Kill-Counter."""
        self._kill_active = False
        self._kill_current = 0
        self._kill_total = 0

    def update(self, quest_manager: 'QuestManager') -> None:
        """Muss einmal pro Frame aufgerufen werden (für Fade-Animation)."""
        active = quest_manager.get_active_quests()
        self._target_alpha = 230 if (active or self._kill_active) else 0

        # Sanftes Ein-/Ausblenden
        if self._show_alpha < self._target_alpha:
            self._show_alpha = min(self._show_alpha + self._fade_speed, self._target_alpha)
        elif self._show_alpha > self._target_alpha:
            self._show_alpha = max(self._show_alpha - self._fade_speed, self._target_alpha)

    def render(self, surface: pygame.Surface, quest_manager: 'QuestManager') -> None:
        """Zeichnet das Missions-Panel oben rechts."""
        if self._show_alpha <= 0:
            return

        active_quests = quest_manager.get_active_quests()
        quest = active_quests[0] if active_quests else None

        # Nichts zu zeigen?
        if not quest and not self._kill_active:
            return

        # Cache-Key
        if quest:
            done_tuple = tuple(o.done for o in quest.objectives)
            ready = getattr(quest, 'ready_to_turn_in', False)
            pulse_key = (pygame.time.get_ticks() // 100) if ready else 0
        else:
            done_tuple = ()
            ready = False
            pulse_key = 0
        kill_key = (self._kill_active, self._kill_current, self._kill_total)
        quest_id = quest.id if quest else None
        cache_key = (quest_id, done_tuple, ready, self._show_alpha, pulse_key, kill_key)

        if self._cache_key != cache_key:
            self._cached_surface = self._build_panel(quest)
            self._cache_key = cache_key

        if self._cached_surface is None:
            return

        # Position: oben rechts
        sw = surface.get_width()
        x = sw - self._cached_surface.get_width() - self.MARGIN_RIGHT
        y = self.MARGIN_TOP

        # Alpha anwenden
        if self._show_alpha < 255:
            temp = self._cached_surface.copy()
            temp.set_alpha(self._show_alpha)
            surface.blit(temp, (x, y))
        else:
            surface.blit(self._cached_surface, (x, y))

    # ------------------------------------------------------------------
    # Internes Rendering
    # ------------------------------------------------------------------
    def _build_panel(self, quest) -> pygame.Surface:
        """Erstellt die Panel-Surface für eine Quest und/oder Kill-Counter."""
        KILL_COLOR = (255, 140, 60)       # Orange für Kill-Counter
        KILL_DONE_COLOR = (80, 220, 80)   # Grün wenn Ziel erreicht

        # ---- Quest-Elemente vorbereiten (falls vorhanden) ----
        header_surf = None
        npc_surf = None
        obj_surfs = []
        return_surf = None
        show_return_hint = False

        if quest:
            header_surf = self._font_title.render(f"📜 {quest.title}", True, self.TITLE_COLOR)
            npc_surf = self._font_npc.render(f"Von: {quest.npc_name}", True, self.NPC_COLOR)

            for obj in quest.objectives:
                color = self.OBJ_DONE_COLOR if obj.done else self.OBJ_COLOR
                label_surf = self._font_obj.render(obj.label, True, color)
                obj_surfs.append((obj.done, label_surf))

            show_return_hint = getattr(quest, 'ready_to_turn_in', False)
            if show_return_hint:
                return_surf = self._font_obj.render(
                    f"→ Kehre zurück zu {quest.npc_name}", True, self.TITLE_COLOR
                )

        # ---- Kill-Counter vorbereiten ----
        kill_surf = None
        kill_done = False
        if self._kill_active:
            kill_done = self._kill_current >= self._kill_total
            kc = KILL_DONE_COLOR if kill_done else KILL_COLOR
            kill_text = f"⚔ Besiegte Gegner: {self._kill_current}/{self._kill_total}"
            kill_surf = self._font_obj.render(kill_text, True, kc)

        # ---- Größe berechnen ----
        width_candidates = []
        if header_surf:
            width_candidates.append(header_surf.get_width())
        if npc_surf:
            width_candidates.append(npc_surf.get_width())
        width_candidates.extend(s.get_width() + self.ICON_SIZE + 8 for _, s in obj_surfs)
        if return_surf:
            width_candidates.append(return_surf.get_width() + 4)
        if kill_surf:
            width_candidates.append(kill_surf.get_width() + 8)
        if not width_candidates:
            width_candidates.append(self.MIN_WIDTH)
        content_w = max(width_candidates)
        panel_w = max(self.MIN_WIDTH, content_w + self.PADDING_X * 2)

        # Höhe berechnen
        line_h = max(header_surf.get_height(), 18) if header_surf else 18
        return_hint_h = (return_surf.get_height() + self.LINE_GAP + 4) if return_surf else 0
        kill_h = 0
        if kill_surf:
            # Trenner + Kill-Zeile
            kill_h = 3 + self.LINE_GAP + kill_surf.get_height() + self.LINE_GAP
            if not quest:
                # Standalone: Titel-Zeile statt Quest-Header
                kill_h = 0  # wird unten separat kalkuliert

        if quest:
            panel_h = (
                self.PADDING_Y
                + line_h                     # Titel
                + self.LINE_GAP
                + npc_surf.get_height()      # Auftraggeber
                + self.LINE_GAP + 3          # Trenner
                + sum(max(s.get_height(), self.ICON_SIZE) + self.LINE_GAP for _, s in obj_surfs)
                + return_hint_h              # Rückkehr-Hinweis
                + (kill_h if kill_surf else 0)
                + self.PADDING_Y
            )
        else:
            # Standalone Kill-Counter-Panel
            standalone_title = self._font_title.render("⚔ Auftrag", True, self.TITLE_COLOR)
            panel_h = (
                self.PADDING_Y
                + standalone_title.get_height()  # Titel
                + self.LINE_GAP + 3              # Trenner
                + kill_surf.get_height() + self.LINE_GAP
                + self.PADDING_Y
            )
            width_candidates.append(standalone_title.get_width())
            content_w = max(width_candidates)
            panel_w = max(self.MIN_WIDTH, content_w + self.PADDING_X * 2)

        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)

        # ---- Hintergrund-Gradient ----
        for row in range(panel_h):
            ratio = row / max(panel_h, 1)
            r = int(self.BG_TOP[0] * (1 - ratio) + self.BG_BOT[0] * ratio)
            g = int(self.BG_TOP[1] * (1 - ratio) + self.BG_BOT[1] * ratio)
            b = int(self.BG_TOP[2] * (1 - ratio) + self.BG_BOT[2] * ratio)
            pygame.draw.line(panel, (r, g, b, 220), (0, row), (panel_w, row))

        # ---- Rahmen (doppelt, Glow) ----
        pygame.draw.rect(panel, self.BORDER_OUTER, (0, 0, panel_w, panel_h), 2)
        pygame.draw.rect(panel, self.BORDER_INNER, (2, 2, panel_w - 4, panel_h - 4), 1)

        # ---- Ecken-Akzente (wie DialogueBox) ----
        corner_len = 8
        for cx, cy, dx, dy in [
            (3, 3, 1, 1), (panel_w - 4, 3, -1, 1),
            (3, panel_h - 4, 1, -1), (panel_w - 4, panel_h - 4, -1, -1),
        ]:
            pygame.draw.line(panel, self.TITLE_COLOR, (cx, cy), (cx + corner_len * dx, cy), 1)
            pygame.draw.line(panel, self.TITLE_COLOR, (cx, cy), (cx, cy + corner_len * dy), 1)

        # ---- Inhalt zeichnen ----
        cur_y = self.PADDING_Y

        if quest:
            # Titel
            panel.blit(header_surf, (self.PADDING_X, cur_y))
            cur_y += header_surf.get_height() + self.LINE_GAP

            # Auftraggeber
            panel.blit(npc_surf, (self.PADDING_X, cur_y))
            cur_y += npc_surf.get_height() + self.LINE_GAP

            # Trenner-Linie
            pygame.draw.line(
                panel, (60, 70, 100, 150),
                (self.PADDING_X, cur_y), (panel_w - self.PADDING_X, cur_y), 1
            )
            cur_y += 3 + self.LINE_GAP

            # Objectives
            for done, label_surf in obj_surfs:
                icon_y = cur_y + (label_surf.get_height() - self.ICON_SIZE) // 2
                icon_x = self.PADDING_X

                if done:
                    # ✓ Häkchen
                    pygame.draw.rect(panel, self.CHECK_COLOR, (icon_x, icon_y, self.ICON_SIZE, self.ICON_SIZE), 0, 2)
                    cx2, cy2 = icon_x + 3, icon_y + self.ICON_SIZE // 2 + 1
                    pygame.draw.line(panel, (255, 255, 255), (cx2, cy2), (cx2 + 3, cy2 + 3), 2)
                    pygame.draw.line(panel, (255, 255, 255), (cx2 + 3, cy2 + 3), (cx2 + 9, cy2 - 4), 2)
                else:
                    # Leere Checkbox
                    pygame.draw.rect(panel, self.BOX_COLOR, (icon_x, icon_y, self.ICON_SIZE, self.ICON_SIZE), 2, 2)

                panel.blit(label_surf, (icon_x + self.ICON_SIZE + 6, cur_y))
                cur_y += max(label_surf.get_height(), self.ICON_SIZE) + self.LINE_GAP

            # Rückkehr-Hinweis
            if return_surf:
                cur_y += 2
                import math as _math
                pulse = int(180 + 60 * _math.sin(pygame.time.get_ticks() / 400))
                glow_color = (pulse, pulse // 2, 0, 60)
                glow_rect = pygame.Rect(self.PADDING_X - 2, cur_y - 2,
                                         return_surf.get_width() + 8, return_surf.get_height() + 4)
                pygame.draw.rect(panel, glow_color, glow_rect, 0, 3)
                panel.blit(return_surf, (self.PADDING_X + 2, cur_y))
                cur_y += return_surf.get_height() + self.LINE_GAP

        else:
            # Standalone Kill-Counter: eigener Titel
            st = self._font_title.render("⚔ Auftrag", True, self.TITLE_COLOR)
            panel.blit(st, (self.PADDING_X, cur_y))
            cur_y += st.get_height() + self.LINE_GAP
            pygame.draw.line(
                panel, (60, 70, 100, 150),
                (self.PADDING_X, cur_y), (panel_w - self.PADDING_X, cur_y), 1
            )
            cur_y += 3 + self.LINE_GAP

        # ---- Kill-Counter (am Ende, immer wenn aktiv) ----
        if kill_surf:
            if quest:
                # Trenner vor Kill-Counter
                pygame.draw.line(
                    panel, (60, 70, 100, 150),
                    (self.PADDING_X, cur_y), (panel_w - self.PADDING_X, cur_y), 1
                )
                cur_y += 3 + self.LINE_GAP

            # Fortschrittsbalken
            bar_x = self.PADDING_X
            bar_w = panel_w - self.PADDING_X * 2
            bar_h = 6
            progress = min(self._kill_current / max(self._kill_total, 1), 1.0)
            # Hintergrund
            pygame.draw.rect(panel, (40, 45, 60, 180), (bar_x, cur_y, bar_w, bar_h), 0, 3)
            # Füllung
            fill_color = (80, 220, 80) if kill_done else (255, 140, 60)
            if progress > 0:
                pygame.draw.rect(panel, fill_color, (bar_x, cur_y, int(bar_w * progress), bar_h), 0, 3)
            pygame.draw.rect(panel, (100, 110, 140), (bar_x, cur_y, bar_w, bar_h), 1, 3)
            cur_y += bar_h + 3

            # Text
            panel.blit(kill_surf, (self.PADDING_X, cur_y))

        return panel
