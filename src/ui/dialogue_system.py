# -*- coding: utf-8 -*-
"""
Modal Dialogue UI for NPC conversations.

Features:
- Blocks gameplay input while active (Level controls this by querying `is_active`).
- Multi-line text with automatic wrapping to screen width.
- Paging support with indicator (» Weiter: C/Space/Enter).
- Advance via keyboard: C, SPACE, ENTER; gamepad: A; hardware: CAST.
"""

from __future__ import annotations

import pygame
from typing import List, Optional, Tuple


class DialogueBox:
    def __init__(self, screen: pygame.Surface, width_ratio: float = 0.6, height: int = 160, align: str = 'right'):
        self.screen = screen
        self.width_ratio = max(0.5, min(1.0, width_ratio))
        self.height = height
        self.margin = 20
        self.padding = 16
        self.bg_color = (10, 12, 26)
        self.border_color = (80, 120, 220)
        self.border_thickness = 3
        self.text_color = (240, 240, 240)
        self.hint_color = (180, 200, 255)
        self.name_color = (255, 215, 120)
        self.align = align if align in ('left', 'center', 'right') else 'right'

        # Fonts
        self.title_font = pygame.font.Font(None, 40)
        self.text_font = pygame.font.Font(None, 32)
        self.hint_font = pygame.font.Font(None, 26)

        # State
        self.is_active: bool = False
        self.pages: List[Tuple[Optional[str], List[str]]] = []  # (speaker, lines)
        self.page_index: int = 0

    def open(self, text: str, speaker: Optional[str] = None, wrap_at: Optional[int] = None):
        self.pages = self._paginate(text, speaker, wrap_at)
        self.page_index = 0
        self.is_active = True

    def close(self):
        self.is_active = False
        self.pages = []
        self.page_index = 0

    def advance(self):
        if not self.is_active:
            return
        if self.page_index + 1 < len(self.pages):
            self.page_index += 1
        else:
            self.close()

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Returns True if the event was consumed by the dialogue."""
        if not self.is_active:
            return False

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_c, pygame.K_SPACE, pygame.K_RETURN):
                self.advance()
                return True
        elif event.type == pygame.JOYBUTTONDOWN:
            if event.button == 0:  # A / Bottom button
                self.advance()
                return True
        return False

    def render(self):
        if not self.is_active or not self.pages:
            return

        screen_w, screen_h = self.screen.get_size()
        dialog_w = int(screen_w * self.width_ratio)
        dialog_h = self.height
        # Horizontal alignment (default: right-aligned to avoid spell UI)
        if self.align == 'right':
            dialog_x = screen_w - dialog_w - self.margin
        elif self.align == 'left':
            dialog_x = self.margin
        else:
            dialog_x = (screen_w - dialog_w) // 2
        dialog_y = screen_h - dialog_h - self.margin

        # Background with slight transparency
        bg = pygame.Surface((dialog_w, dialog_h), pygame.SRCALPHA)
        bg.fill((*self.bg_color, 210))
        self.screen.blit(bg, (dialog_x, dialog_y))
        pygame.draw.rect(self.screen, self.border_color, (dialog_x, dialog_y, dialog_w, dialog_h), self.border_thickness)

        # Content rect
        content_x = dialog_x + self.padding
        content_y = dialog_y + self.padding
        content_w = dialog_w - 2 * self.padding

        speaker, lines = self.pages[self.page_index]

        # Draw speaker name if present
        y = content_y
        if speaker:
            name_surf = self.title_font.render(speaker, True, self.name_color)
            self.screen.blit(name_surf, (content_x, y))
            y += name_surf.get_height() + 6

        # Draw text lines
        for line in lines:
            txt = self.text_font.render(line, True, self.text_color)
            self.screen.blit(txt, (content_x, y))
            y += txt.get_height() + 4

        # Draw page hint
        hint = "» Weiter: C/Leertaste/Enter"
        if self.page_index + 1 == len(self.pages):
            hint = "» Schließen: C/Leertaste/Enter"
        hint_surf = self.hint_font.render(hint, True, self.hint_color)
        hint_rect = hint_surf.get_rect()
        hint_rect.bottomright = (dialog_x + dialog_w - self.padding, dialog_y + dialog_h - self.padding)
        self.screen.blit(hint_surf, hint_rect)

        # Page counter
        counter = f"{self.page_index + 1}/{len(self.pages)}"
        cnt_surf = self.hint_font.render(counter, True, (160, 160, 180))
        self.screen.blit(cnt_surf, (dialog_x + self.padding, dialog_y + dialog_h - self.padding - cnt_surf.get_height()))

    # --- Helpers ---
    def _paginate(self, full_text: str, speaker: Optional[str], wrap_at: Optional[int]) -> List[Tuple[Optional[str], List[str]]]:
        """Splits text into pages by wrapping to content width. Supports optional speaker prefix in the text.

        Convention: If `full_text` contains lines like 'Name:' at the top, we extract it automatically unless `speaker` is already given.
        """
        # Extract speaker from text like "Elara (Nachbarin):\n..." if not provided
        spk = speaker
        text = full_text
        if not spk:
            parts = full_text.split("\n", 1)
            if parts and ':' in parts[0]:
                spk = parts[0].rstrip(':')
                text = parts[1] if len(parts) > 1 else ''

        # Wrap by measuring font width
        screen_w, _ = self.screen.get_size()
        dialog_w = int(screen_w * self.width_ratio) - 2 * self.padding
        max_width = dialog_w

        paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
        wrapped_lines: List[str] = []
        for para in paragraphs:
            wrapped_lines.extend(self._wrap_text(para, self.text_font, max_width))

        # Split into pages based on height
        lines_per_page: List[List[str]] = []
        cur: List[str] = []
        cur_h = 0
        line_h = self.text_font.get_height() + 4
        available_h = self.height - 2 * self.padding
        if spk:
            available_h -= (self.title_font.get_height() + 6)

        for ln in wrapped_lines:
            if cur_h + line_h > available_h and cur:
                lines_per_page.append(cur)
                cur = []
                cur_h = 0
            cur.append(ln)
            cur_h += line_h
        if cur:
            lines_per_page.append(cur)

        if not lines_per_page:
            lines_per_page = [[""]]

        return [(spk, lines) for lines in lines_per_page]

    def _wrap_text(self, text: str, font: pygame.font.Font, max_width: int) -> List[str]:
        words = text.split()
        lines: List[str] = []
        current = ""
        for w in words:
            test = f"{current} {w}".strip()
            if font.size(test)[0] <= max_width:
                current = test
            else:
                if current:
                    lines.append(current)
                current = w
        if current:
            lines.append(current)
        return lines
