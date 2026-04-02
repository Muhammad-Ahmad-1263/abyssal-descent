"""
pathfinding.py — A* pathfinding used by enemy AI
"""
from __future__ import annotations
import heapq
from typing import List, Tuple, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from tiles import DungeonMap


def heuristic(a: Tuple[int,int], b: Tuple[int,int]) -> int:
    return abs(a[0]-b[0]) + abs(a[1]-b[1])


def astar(dmap: "DungeonMap",
          start: Tuple[int,int],
          goal:  Tuple[int,int],
          max_dist: int = 20) -> List[Tuple[int,int]]:
    """Returns path from start to goal (not including start).
    Returns empty list if unreachable within max_dist."""
    if start == goal:
        return []

    open_heap: list = []
    heapq.heappush(open_heap, (0, start))
    came_from: dict = {start: None}
    g_score: dict   = {start: 0}

    while open_heap:
        _, current = heapq.heappop(open_heap)

        if current == goal:
            path = []
            while current != start:
                path.append(current)
                current = came_from[current]
            path.reverse()
            return path

        if g_score.get(current, 0) > max_dist:
            continue

        cx, cy = current
        for dx, dy in [(0,1),(0,-1),(1,0),(-1,0)]:
            nx, ny = cx+dx, cy+dy
            neighbor = (nx, ny)
            if not dmap.in_bounds(nx, ny):
                continue
            if not dmap.walkable(nx, ny) and neighbor != goal:
                continue
            tentative_g = g_score.get(current, 0) + 1
            if tentative_g < g_score.get(neighbor, float('inf')):
                came_from[neighbor] = current
                g_score[neighbor]   = tentative_g
                f = tentative_g + heuristic(neighbor, goal)
                heapq.heappush(open_heap, (f, neighbor))

    return []
