# -*- coding: utf-8 -*-
"""
Spell icon loader with simple caching.

Looks for PNGs in:
- assets/ui/spells/elements/<name>.png
- assets/ui/spells/combos/<a>_<b>.png (both orders tried)

Supports DE/EN naming fallbacks (wasser/water, feuer/fire, stein/stone).
Scales icons to requested size and caches per (key,size).
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Tuple, Optional
import pygame

try:
    from core.config import config
except ImportError:
    try:
        from ..core.config import config
    except Exception:
        import sys, os
        sys.path.append(os.path.dirname(os.path.dirname(__file__)))
        from core.config import config


# map ids used in code to possible file basenames
_NAME_MAP = {
    "water": ["water", "wasser", "w"],
    "fire": ["fire", "feuer", "f"],
    "stone": ["stone", "stein", "s"],
}


class SpellIcons:
    def __init__(self, base_size: int = 64, assets_dir: Optional[Path] = None) -> None:
        self.base_size = base_size
        base_assets = Path(assets_dir or config.paths.ASSETS_DIR)
        self.elements_dir = base_assets / "ui" / "spells" / "elements"
        self.combos_dir = base_assets / "ui" / "spells" / "combos"
        self._cache: Dict[Tuple[str, int], pygame.Surface] = {}

    def _load_png(self, path: Path, size: int) -> Optional[pygame.Surface]:
        if not path.exists():
            return None
        try:
            surf = pygame.image.load(str(path))
            # Only convert if a display surface exists
            if pygame.display.get_surface() is not None:
                surf = surf.convert_alpha()
        except Exception:
            return None
        if surf.get_width() != size or surf.get_height() != size:
            surf = pygame.transform.smoothscale(surf, (size, size))
        return surf

    def _placeholder(self, label: str, size: int) -> pygame.Surface:
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        surf.fill((40, 40, 40, 180))
        pygame.draw.rect(surf, (255, 255, 255), surf.get_rect(), 2)
        pygame.font.init()
        font = pygame.font.Font(None, max(16, int(size * 0.5)))
        txt = font.render(label, True, (255, 255, 255))
        surf.blit(txt, txt.get_rect(center=surf.get_rect().center))
        return surf

    def _find_png_fuzzy(self, directory: Path, names: list[str]) -> Optional[Path]:
        # exact names first
        for n in names:
            p = directory / f"{n}.png"
            if p.exists():
                return p
        # fuzzy: any file containing one of the names
        try:
            for file in directory.glob("*.png"):
                stem = file.stem.lower()
                if any(n in stem for n in names):
                    return file
        except FileNotFoundError:
            return None
        return None

    def get_element(self, name: str, size: Optional[int] = None) -> pygame.Surface:
        size = size or self.base_size
        key = (f"elem:{name.lower()}", size)
        if key in self._cache:
            return self._cache[key]

        name_list = _NAME_MAP.get(name.lower(), [name.lower()])
        path = self._find_png_fuzzy(self.elements_dir, name_list)
        surf: Optional[pygame.Surface] = self._load_png(path, size) if path else None
        if not surf:
            label = (name[:2] or "?").upper()
            surf = self._placeholder(label, size)

        self._cache[key] = surf
        return surf

    def get_combo(self, a: str, b: str, size: Optional[int] = None) -> pygame.Surface:
        size = size or self.base_size
        a_l, b_l = a.lower(), b.lower()
        key = (f"combo:{a_l}+{b_l}", size)
        if key in self._cache:
            return self._cache[key]

        names_a = _NAME_MAP.get(a_l, [a_l])
        names_b = _NAME_MAP.get(b_l, [b_l])

        # try structured names first
        path = None
        for x in names_a:
            for y in names_b:
                p1 = self.combos_dir / f"{x}_{y}.png"
                p2 = self.combos_dir / f"{y}_{x}.png"
                if p1.exists():
                    path = p1; break
                if p2.exists():
                    path = p2; break
            if path:
                break
        # fuzzy fallback using either a or b keywords
        if path is None:
            keywords = list(dict.fromkeys(names_a + names_b))
            path = self._find_png_fuzzy(self.combos_dir, keywords)

        surf: Optional[pygame.Surface] = self._load_png(path, size) if path else None
        if not surf:
            label = (a_l[:1] + b_l[:1]).upper()
            surf = self._placeholder(label, size)

        self._cache[key] = surf
        return surf
