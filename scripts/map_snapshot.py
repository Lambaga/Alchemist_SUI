# -*- coding: utf-8 -*-
"""
Render a TMX map snapshot to a PNG using the project's MapLoader.
Useful to validate tileset slicing and visibility without running the full game.

Usage (PowerShell):
  # Optional debug flags
  $env:ALCHEMIST_MAP_DEBUG="1"; $env:ALCHEMIST_TILE_DEBUG_SOLID="1"; $env:ALCHEMIST_TILE_GRID="1"; \
  $env:ALCHEMIST_DISABLE_FOREGROUND="1"; $env:ALCHEMIST_SLICE_PREFERRED="1"; \
  python scripts/map_snapshot.py --map assets/maps/Map_Town.tmx --out snapshot.png --w 1280 --h 720

Notes:
- If content bounds are available, the camera snaps to the first non-zero tile area.
- Use --x/--y to override the camera position in world pixels.
"""
import os
import sys
import argparse
import pygame

# Ensure src is on path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src')
if SRC not in sys.path:
    sys.path.insert(0, SRC)
    sys.path.insert(0, os.path.join(SRC, 'world'))
    sys.path.insert(0, os.path.join(SRC, 'managers'))

from world.map_loader import MapLoader  # type: ignore

class FakeCamera:
    def __init__(self, x: int, y: int, w: int, h: int):
        self.camera_rect = pygame.Rect(x, y, w, h)
        self.zoom_factor = 1.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--map', default=os.path.join(ROOT, 'assets', 'maps', 'Map2.tmx'), help='Path to TMX map')  # Geändert
    ap.add_argument('--out', default='debug_map_snapshot.png', help='Output PNG file')
    ap.add_argument('--w', type=int, default=1280, help='Viewport width')
    ap.add_argument('--h', type=int, default=720, help='Viewport height')
    ap.add_argument('--x', type=int, default=None, help='Camera X in world pixels (overrides content snap)')
    ap.add_argument('--y', type=int, default=None, help='Camera Y in world pixels (overrides content snap)')
    args = ap.parse_args()

    pygame.init()
    try:
        # Minimal display for convert/convert_alpha
        pygame.display.set_mode((1, 1))
    except Exception:
        pass
    try:
        surface = pygame.Surface((args.w, args.h), pygame.SRCALPHA)
    except Exception:
        surface = pygame.Surface((args.w, args.h))

    # Load map
    ml = MapLoader(args.map)
    if not ml or not getattr(ml, 'tmx_data', None):
        print(f"❌ Failed to load TMX: {args.map}")
        sys.exit(2)

    # Determine camera start
    cx, cy = 0, 0
    if args.x is not None and args.y is not None:
        cx, cy = int(args.x), int(args.y)
    else:
        cb = getattr(ml, 'content_bounds', None)
        if cb:
            cx = int(cb['min_x'] * cb['tw'])
            cy = int(cb['min_y'] * cb['th'])
            print(f"[Snapshot] Snapping camera to content bounds at ({cx},{cy})")
        else:
            print("[Snapshot] No content bounds computed; using (0,0)")

    cam = FakeCamera(cx, cy, args.w, args.h)

    # Optional background fill
    surface.fill((0, 0, 0, 255))

    # Render background layers
    ml.render(surface, cam)

    # Optionally render foreground unless disabled by env var
    if not os.environ.get('ALCHEMIST_DISABLE_FOREGROUND'):
        ml.render_foreground(surface, cam)

    # Save PNG
    out_path = args.out
    pygame.image.save(surface, out_path)
    print(f"✅ Wrote snapshot: {out_path} ({args.w}x{args.h}) @ cam=({cx},{cy})")

if __name__ == '__main__':
    main()
