"""
fov.py — Recursive shadowcasting FOV
"""
from __future__ import annotations
from tiles import DungeonMap

MULTIPLIERS = [
    [1,  0,  0, -1, -1,  0,  0,  1],
    [0,  1, -1,  0,  0, -1,  1,  0],
    [0,  1,  1,  0,  0, -1, -1,  0],
    [1,  0,  0,  1, -1,  0,  0, -1],
]


def compute_fov(dmap: DungeonMap, ox: int, oy: int, radius: int):
    dmap.reset_visibility()
    if dmap.in_bounds(ox, oy):
        dmap.tiles[ox][oy].visible = True
        dmap.tiles[ox][oy].visited = True

    for octant in range(8):
        _cast_light(
            dmap, ox, oy, radius, 1, 1.0, 0.0,
            MULTIPLIERS[0][octant], MULTIPLIERS[1][octant],
            MULTIPLIERS[2][octant], MULTIPLIERS[3][octant],
        )


def _cast_light(dmap, cx, cy, radius, row,
                start_slope, end_slope, xx, xy, yx, yy):
    if start_slope < end_slope:
        return
    radius_sq = radius * radius
    next_start = start_slope

    for j in range(row, radius + 1):
        dx = -j - 1
        blocked = False
        dy = -j

        while dx <= 0:
            dx += 1
            mx = cx + dx * xx + dy * xy
            my = cy + dx * yx + dy * yy

            l_slope = (dx - 0.5) / (dy + 0.5)
            r_slope = (dx + 0.5) / (dy - 0.5)

            if start_slope < r_slope:
                continue
            if end_slope > l_slope:
                break

            if dx * dx + dy * dy <= radius_sq and dmap.in_bounds(mx, my):
                dmap.tiles[mx][my].visible = True
                dmap.tiles[mx][my].visited = True

            if blocked:
                if not dmap.transparent(mx, my):
                    next_start = r_slope
                    continue
                else:
                    blocked = False
                    start_slope = next_start
            else:
                if not dmap.transparent(mx, my) and j < radius:
                    blocked = True
                    _cast_light(dmap, cx, cy, radius, j + 1,
                                start_slope, l_slope, xx, xy, yx, yy)
                    next_start = r_slope

        if blocked:
            break
