"""
tiles.py — Tile definitions and the DungeonMap class
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List
from constants import MAP_W, MAP_H


@dataclass
class Tile:
    walkable:  bool = False
    transparent: bool = False
    visited:   bool = False   # ever seen?
    visible:   bool = False   # currently in FOV?
    glyph:     str  = "#"
    # 0=wall, 1=floor, 2=stairs_down, 3=door
    kind:      int  = 0


class DungeonMap:
    def __init__(self, width: int = MAP_W, height: int = MAP_H):
        self.width  = width
        self.height = height
        self.tiles: List[List[Tile]] = [
            [Tile() for _ in range(height)] for _ in range(width)
        ]
        self.rooms: list = []

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def walkable(self, x: int, y: int) -> bool:
        return self.in_bounds(x, y) and self.tiles[x][y].walkable

    def transparent(self, x: int, y: int) -> bool:
        return self.in_bounds(x, y) and self.tiles[x][y].transparent

    def reset_visibility(self):
        for col in self.tiles:
            for t in col:
                t.visible = False
