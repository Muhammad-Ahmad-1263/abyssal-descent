"""
dungeon_gen.py — BSP (Binary Space Partitioning) dungeon generator
"""
from __future__ import annotations
import random
from dataclasses import dataclass
from typing import List, Optional, Tuple
from tiles import DungeonMap, Tile


@dataclass
class Rect:
    x: int; y: int; w: int; h: int

    @property
    def cx(self): return self.x + self.w // 2
    @property
    def cy(self): return self.y + self.h // 2
    @property
    def x2(self): return self.x + self.w
    @property
    def y2(self): return self.y + self.h

    def inner(self):
        return (self.x + 1, self.y + 1, self.w - 2, self.h - 2)

    def intersects(self, other: "Rect") -> bool:
        return (self.x <= other.x2 and self.x2 >= other.x and
                self.y <= other.y2 and self.y2 >= other.y)


class BSPNode:
    MIN_SIZE = 10

    def __init__(self, rect: Rect):
        self.rect   = rect
        self.left:  Optional[BSPNode] = None
        self.right: Optional[BSPNode] = None
        self.room:  Optional[Rect]    = None

    def split(self) -> bool:
        if self.left or self.right:
            return self.left.split() or self.right.split()  # type: ignore

        split_h = random.random() > 0.5
        if self.rect.w > self.rect.h and self.rect.w / self.rect.h >= 1.25:
            split_h = False
        elif self.rect.h > self.rect.w and self.rect.h / self.rect.w >= 1.25:
            split_h = True

        max_size = (self.rect.h if split_h else self.rect.w) - self.MIN_SIZE
        if max_size <= self.MIN_SIZE:
            return False

        split = random.randint(self.MIN_SIZE, max_size)
        if split_h:
            self.left  = BSPNode(Rect(self.rect.x, self.rect.y, self.rect.w, split))
            self.right = BSPNode(Rect(self.rect.x, self.rect.y + split, self.rect.w, self.rect.h - split))
        else:
            self.left  = BSPNode(Rect(self.rect.x, self.rect.y, split, self.rect.h))
            self.right = BSPNode(Rect(self.rect.x + split, self.rect.y, self.rect.w - split, self.rect.h))
        return True

    def create_rooms(self, dmap: DungeonMap, rooms: list):
        if self.left or self.right:
            if self.left:  self.left.create_rooms(dmap, rooms)
            if self.right: self.right.create_rooms(dmap, rooms)
            # connect children
            if self.left and self.right:
                lc = self.left.get_room()
                rc = self.right.get_room()
                if lc and rc:
                    carve_tunnel(dmap, lc.cx, lc.cy, rc.cx, rc.cy)
        else:
            rx, ry, rw, rh = self.rect.inner()
            room_w = random.randint(5, min(rw, 14))
            room_h = random.randint(4, min(rh, 10))
            room_x = rx + random.randint(0, rw - room_w)
            room_y = ry + random.randint(0, rh - room_h)
            self.room = Rect(room_x, room_y, room_w, room_h)
            carve_room(dmap, self.room)
            rooms.append(self.room)

    def get_room(self) -> Optional[Rect]:
        if self.room:
            return self.room
        left_room  = self.left.get_room()  if self.left  else None
        right_room = self.right.get_room() if self.right else None
        if left_room and right_room:
            return random.choice([left_room, right_room])
        return left_room or right_room


def carve_room(dmap: DungeonMap, room: Rect):
    for x in range(room.x, room.x2):
        for y in range(room.y, room.y2):
            if dmap.in_bounds(x, y):
                t = dmap.tiles[x][y]
                t.walkable    = True
                t.transparent = True
                t.glyph       = "."
                t.kind        = 1


def carve_tunnel(dmap: DungeonMap, x1: int, y1: int, x2: int, y2: int):
    cx, cy = x1, y1
    while cx != x2:
        step = 1 if cx < x2 else -1
        cx += step
        if dmap.in_bounds(cx, cy):
            t = dmap.tiles[cx][cy]
            t.walkable = True; t.transparent = True
            t.glyph = "."; t.kind = 1
    while cy != y2:
        step = 1 if cy < y2 else -1
        cy += step
        if dmap.in_bounds(cx, cy):
            t = dmap.tiles[cx][cy]
            t.walkable = True; t.transparent = True
            t.glyph = "."; t.kind = 1


def generate_dungeon(width: int, height: int, floor: int) -> Tuple[DungeonMap, list]:
    dmap = DungeonMap(width, height)
    rooms: list = []

    root = BSPNode(Rect(1, 1, width - 2, height - 2))
    depth = 4 + min(floor, 4)
    for _ in range(depth):
        root.split()
    root.create_rooms(dmap, rooms)

    random.shuffle(rooms)
    return dmap, rooms
