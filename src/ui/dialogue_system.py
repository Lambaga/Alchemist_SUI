# -*- coding: utf-8 -*-
"""
Modal Dialogue UI for NPC conversations.

Features:
- Blocks gameplay input while active (Level controls this by querying `is_active`).
- Multi-line text with automatic wrapping to screen width.
- Paging support with indicator (» Weiter: C/Space/Enter).
- Advance via keyboard: C, SPACE, ENTER; gamepad: A; hardware: CAST.
- Modern pixel-art styled dialogue box with decorative elements.
"""

from __future__ import annotations

import pygame
import math
from typing import List, Optional, Tuple
from managers.font_manager import get_font_manager


class DialogueBox:
    def __init__(self, screen: pygame.Surface, width_ratio: float = 0.6, height: int = 160, align: str = 'right'):
        self.screen = screen
        self.width_ratio = max(0.5, min(1.0, width_ratio))
        self.height = height
        self.margin = 20
        self.padding = 18
        
        # Moderne Pixel-Art Farbpalette
        self.bg_color_top = (15, 20, 45)      # Dunkelblau oben
        self.bg_color_bottom = (8, 12, 28)    # Noch dunkler unten
        self.border_outer = (45, 55, 90)      # Äußerer Rahmen
        self.border_middle = (70, 90, 140)    # Mittlerer Rahmen
        self.border_inner = (100, 130, 200)   # Innerer leuchtender Rahmen
        self.border_glow = (120, 160, 255)    # Glüh-Effekt
        self.corner_accent = (180, 140, 80)   # Gold-Akzent für Ecken
        
        self.text_color = (230, 235, 245)
        self.hint_color = (140, 170, 220)
        self.name_color = (255, 200, 100)     # Warmes Gold für Namen
        self.name_glow = (255, 180, 60)       # Name-Glühen
        
        self.align = align if align in ('left', 'center', 'right') else 'right'

        # 🚀 RPi-Optimierung: FontManager für gecachte Fonts
        self._font_manager = get_font_manager()
        self.title_font = self._font_manager.get_font(28)
        self.text_font = self._font_manager.get_font(22)
        self.hint_font = self._font_manager.get_font(18)

        # Animation State
        self.is_active: bool = False
        self.pages: List[Tuple[Optional[str], List[str]]] = []
        self.page_index: int = 0
        self.open_time: int = 0  # Für Animationen

    def open(self, text: str, speaker: Optional[str] = None, wrap_at: Optional[int] = None):
        self.pages = self._paginate(text, speaker, wrap_at)
        self.page_index = 0
        self.is_active = True
        self.open_time = pygame.time.get_ticks()

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
        
        # Horizontal alignment
        if self.align == 'right':
            dialog_x = screen_w - dialog_w - self.margin
        elif self.align == 'left':
            dialog_x = self.margin
        else:
            dialog_x = (screen_w - dialog_w) // 2
        dialog_y = screen_h - dialog_h - self.margin

        # Animation Zeit
        anim_time = pygame.time.get_ticks() - self.open_time
        
        # === HINTERGRUND MIT GRADIENT ===
        self._draw_gradient_background(dialog_x, dialog_y, dialog_w, dialog_h)
        
        # === MEHRSTUFIGER RAHMEN (Pixel-Art Style) ===
        self._draw_pixel_border(dialog_x, dialog_y, dialog_w, dialog_h, anim_time)
        
        # === DEKORATIVE ECKEN ===
        self._draw_corner_decorations(dialog_x, dialog_y, dialog_w, dialog_h)
        
        # Content rect
        content_x = dialog_x + self.padding + 8
        content_y = dialog_y + self.padding
        
        speaker, lines = self.pages[self.page_index]

        # === SPEAKER NAME MIT GLOW ===
        y = content_y
        if speaker:
            self._draw_speaker_name(speaker, content_x, y, anim_time)
            y += self.title_font.get_height() + 10
            
            # Trennlinie unter dem Namen
            line_y = y - 4
            pygame.draw.line(self.screen, self.border_middle, 
                           (content_x, line_y), 
                           (dialog_x + dialog_w - self.padding - 8, line_y), 1)

        # === TEXT ZEILEN ===
        for line in lines:
            txt = self.text_font.render(line, True, self.text_color)
            self.screen.blit(txt, (content_x, y))
            y += txt.get_height() + 3

        # === BLINKENDER WEITER-HINWEIS ===
        self._draw_hint(dialog_x, dialog_y, dialog_w, dialog_h, anim_time)
        
        # === SEITEN-ANZEIGE ===
        self._draw_page_counter(dialog_x, dialog_y, dialog_h)

    def _draw_gradient_background(self, x: int, y: int, w: int, h: int):
        """Zeichnet einen vertikalen Farbverlauf-Hintergrund."""
        bg = pygame.Surface((w, h), pygame.SRCALPHA)
        
        for row in range(h):
            # Interpoliere zwischen oben und unten
            ratio = row / h
            r = int(self.bg_color_top[0] * (1 - ratio) + self.bg_color_bottom[0] * ratio)
            g = int(self.bg_color_top[1] * (1 - ratio) + self.bg_color_bottom[1] * ratio)
            b = int(self.bg_color_top[2] * (1 - ratio) + self.bg_color_bottom[2] * ratio)
            pygame.draw.line(bg, (r, g, b, 235), (0, row), (w, row))
        
        self.screen.blit(bg, (x, y))

    def _draw_pixel_border(self, x: int, y: int, w: int, h: int, anim_time: int):
        """Zeichnet einen mehrstufigen Pixel-Art Rahmen."""
        # Äußerer Rahmen (dunkel)
        pygame.draw.rect(self.screen, self.border_outer, (x-2, y-2, w+4, h+4), 2)
        
        # Mittlerer Rahmen
        pygame.draw.rect(self.screen, self.border_middle, (x, y, w, h), 2)
        
        # Innerer leuchtender Rahmen
        pygame.draw.rect(self.screen, self.border_inner, (x+2, y+2, w-4, h-4), 1)
        
        # Animierter Glüh-Effekt (pulsiert)
        glow_alpha = int(80 + 40 * math.sin(anim_time / 300))
        glow_surf = pygame.Surface((w-6, h-6), pygame.SRCALPHA)
        pygame.draw.rect(glow_surf, (*self.border_glow, glow_alpha), (0, 0, w-6, h-6), 1)
        self.screen.blit(glow_surf, (x+3, y+3))

    def _draw_corner_decorations(self, x: int, y: int, w: int, h: int):
        """Zeichnet dekorative Pixel-Ecken."""
        corner_size = 6
        
        # Goldene Eck-Akzente
        corners = [
            (x, y),                     # Oben links
            (x + w - corner_size, y),   # Oben rechts
            (x, y + h - corner_size),   # Unten links
            (x + w - corner_size, y + h - corner_size)  # Unten rechts
        ]
        
        for cx, cy in corners:
            # Kleines Quadrat in jeder Ecke
            pygame.draw.rect(self.screen, self.corner_accent, (cx, cy, corner_size, corner_size))
            # Innerer Punkt
            pygame.draw.rect(self.screen, (255, 220, 140), (cx+2, cy+2, 2, 2))

    def _draw_speaker_name(self, speaker: str, x: int, y: int, anim_time: int):
        """Zeichnet den Sprecher-Namen mit Glow-Effekt."""
        # Subtiler Glow hinter dem Namen (pulsiert leicht)
        glow_intensity = int(100 + 30 * math.sin(anim_time / 400))
        glow_surf = self.title_font.render(speaker, True, (*self.name_glow[:3], glow_intensity))
        glow_pos = (x - 1, y - 1)
        
        # Glow als halbtransparentes Overlay
        glow_bg = pygame.Surface(glow_surf.get_size(), pygame.SRCALPHA)
        glow_bg.blit(glow_surf, (0, 0))
        glow_bg.set_alpha(80)
        self.screen.blit(glow_bg, glow_pos)
        
        # Haupt-Name
        name_surf = self.title_font.render(speaker, True, self.name_color)
        self.screen.blit(name_surf, (x, y))
        
        # Kleines Dekorsymbol vor dem Namen
        deco_x = x - 12
        deco_y = y + name_surf.get_height() // 2
        pygame.draw.polygon(self.screen, self.corner_accent, [
            (deco_x, deco_y),
            (deco_x + 6, deco_y - 4),
            (deco_x + 6, deco_y + 4)
        ])

    def _draw_hint(self, dialog_x: int, dialog_y: int, dialog_w: int, dialog_h: int, anim_time: int):
        """Zeichnet den blinkenden Weiter-Hinweis."""
        # Blinken: Ein/Aus alle 600ms
        blink = (anim_time // 600) % 2 == 0
        
        if self.page_index + 1 == len(self.pages):
            hint = "Schliessen"
        else:
            hint = "Weiter"
        
        # Basis-Farbe mit Blink-Effekt
        if blink:
            hint_color = (200, 220, 255)
        else:
            hint_color = self.hint_color
        
        hint_surf = self.hint_font.render(hint, True, hint_color)
        hint_rect = hint_surf.get_rect()
        hint_rect.bottomright = (dialog_x + dialog_w - self.padding - 4, 
                                  dialog_y + dialog_h - self.padding + 2)
        
        # Kleiner Hintergrund für den Hinweis
        bg_rect = hint_rect.inflate(12, 6)
        bg_surf = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        bg_surf.fill((20, 30, 50, 150))
        self.screen.blit(bg_surf, bg_rect)
        
        # Rahmen um Hinweis
        pygame.draw.rect(self.screen, self.border_middle, bg_rect, 1)
        
        self.screen.blit(hint_surf, hint_rect)

    def _draw_page_counter(self, dialog_x: int, dialog_y: int, dialog_h: int):
        """Zeichnet die Seiten-Anzeige."""
        counter = f"{self.page_index + 1}/{len(self.pages)}"
        cnt_surf = self.hint_font.render(counter, True, (120, 130, 160))
        self.screen.blit(cnt_surf, (dialog_x + self.padding + 4, 
                                     dialog_y + dialog_h - self.padding - cnt_surf.get_height() + 2))

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
