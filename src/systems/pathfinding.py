# -*- coding: utf-8 -*-
"""
Lightweight grid-based A* pathfinding for enemies.

Builds a blocked grid from TMX collision rectangles and finds a 4-dir path
from A (px) to B (px). Returns waypoints in pixel centers.
"""
from __future__ import annotations

from typing import List, Tuple, Optional
import heapq


class GridPathfinder:
    def __init__(self, map_width_tiles: int, map_height_tiles: int, tile_w: int, tile_h: int):
        self.w = map_width_tiles
        self.h = map_height_tiles
        self.tw = tile_w
        self.th = tile_h
        self.blocked = [[False for _ in range(self.w)] for _ in range(self.h)]

    def clear(self):
        for y in range(self.h):
            row = self.blocked[y]
            for x in range(self.w):
                row[x] = False

    def build_from_collision_rects(self, collision_rects: List[Tuple[int, int, int, int]]):
        # Mark tiles covered by collision rectangles as blocked
        self.clear()
        tw, th = self.tw, self.th
        for r in collision_rects:
            # Accept either pygame.Rect or tuple-like
            try:
                x0 = getattr(r, 'x', None)
                y0 = getattr(r, 'y', None)
                w = getattr(r, 'width', None)
                h = getattr(r, 'height', None)
                if x0 is None:
                    x0, y0, w, h = r
            except Exception:
                x0, y0, w, h = r

            tx0 = max(0, x0 // tw)
            ty0 = max(0, y0 // th)
            tx1 = min(self.w - 1, (x0 + w - 1) // tw)
            ty1 = min(self.h - 1, (y0 + h - 1) // th)
            for ty in range(ty0, ty1 + 1):
                for tx in range(tx0, tx1 + 1):
                    self.blocked[ty][tx] = True

    def _heuristic(self, a: Tuple[int, int], b: Tuple[int, int]) -> int:
        # Manhattan distance
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def _neighbors(self, x: int, y: int):
        if x > 0:
            yield (x - 1, y)
        if x < self.w - 1:
            yield (x + 1, y)
        if y > 0:
            yield (x, y - 1)
        if y < self.h - 1:
            yield (x, y + 1)

    def _in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.w and 0 <= y < self.h

    def _is_free(self, x: int, y: int) -> bool:
        return self._in_bounds(x, y) and not self.blocked[y][x]

    def world_to_grid(self, px: float, py: float) -> Tuple[int, int]:
        return int(px // self.tw), int(py // self.th)

    def grid_to_world_center(self, gx: int, gy: int) -> Tuple[int, int]:
        return gx * self.tw + self.tw // 2, gy * self.th + self.th // 2

    def find_path(self, start_px: Tuple[float, float], goal_px: Tuple[float, float], max_closed: int = 5000) -> List[Tuple[int, int]]:
        sx, sy = self.world_to_grid(start_px[0], start_px[1])
        gx, gy = self.world_to_grid(goal_px[0], goal_px[1])
        if not self._is_free(sx, sy):
            # Try to nudge start around if inside wall
            for nx, ny in self._neighbors(sx, sy):
                if self._is_free(nx, ny):
                    sx, sy = nx, ny
                    break
        if not self._is_free(gx, gy):
            # Early exit if goal is inside wall; try neighbors
            found = False
            for nx, ny in self._neighbors(gx, gy):
                if self._is_free(nx, ny):
                    gx, gy = nx, ny
                    found = True
                    break
            if not found:
                return []

        open_heap: List[Tuple[int, Tuple[int, int]]] = []
        heapq.heappush(open_heap, (0, (sx, sy)))
        came_from: dict[Tuple[int, int], Optional[Tuple[int, int]]] = {(sx, sy): None}
        g_score: dict[Tuple[int, int], int] = {(sx, sy): 0}

        closed = 0
        while open_heap and closed < max_closed:
            _, current = heapq.heappop(open_heap)
            cx, cy = current
            closed += 1
            if current == (gx, gy):
                break
            for nx, ny in self._neighbors(cx, cy):
                if not self._is_free(nx, ny):
                    continue
                tentative = g_score[current] + 1
                if tentative < g_score.get((nx, ny), 1_000_000_000):
                    came_from[(nx, ny)] = current
                    g_score[(nx, ny)] = tentative
                    f = tentative + self._heuristic((nx, ny), (gx, gy))
                    heapq.heappush(open_heap, (f, (nx, ny)))

        # Reconstruct
        if (gx, gy) not in came_from:
            return []
        path_cells = []
        cur = (gx, gy)
        while cur is not None:
            path_cells.append(cur)
            cur = came_from.get(cur)
        path_cells.reverse()

        # Convert to world pixel centers
        return [self.grid_to_world_center(x, y) for (x, y) in path_cells]
