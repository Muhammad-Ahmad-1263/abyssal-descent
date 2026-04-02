"""
game.py — Core game loop, state machine, turn management
"""
from __future__ import annotations
import random
import math
import pygame
from typing import List, Tuple

from constants import MAP_W, MAP_H, FOV_RADIUS, C
from tiles import DungeonMap
from dungeon_gen import generate_dungeon
from fov import compute_fov
from entities import Player, Enemy, Item, spawn_enemies, random_item
from pathfinding import astar
from renderer import Renderer


MAX_LOG = 80
MAX_FLOOR = 10


class Game:
    def __init__(self, screen: pygame.Surface):
        self.screen   = screen
        self.renderer = Renderer(screen)
        self.state    = "menu"
        # set at new_game / next_floor
        self.dmap:    DungeonMap  = None  # type: ignore
        self.player:  Player      = None  # type: ignore
        self.enemies: List[Enemy] = []
        self.items:   List[Item]  = []
        self.log_lines: List[Tuple[str,tuple]] = []
        self.cam_x = 0
        self.cam_y = 0
        self.inventory_open = False
        self.inv_cursor     = 0
        self.turn = 0

    # ── public ───────────────────────────────────────────────────────────────

    def new_game(self):
        self.player     = Player(0, 0)
        self.log_lines  = []
        self.turn       = 0
        self.log("Welcome to Abyssal Descent. Descend with '>'.", C["text_gold"])
        self.log("Move with Arrow keys or HJKL. Press I for inventory.", C["text_dim"])
        self._load_floor(1)

    def handle_event(self, event: pygame.event.Event):
        if event.type != pygame.KEYDOWN:
            return

        key = event.key

        if self.state == "menu":
            if key == pygame.K_RETURN:
                self.state = "playing"
            return

        if self.state in ("dead", "win"):
            if key == pygame.K_RETURN:
                self.new_game()
                self.state = "playing"
            return

        if self.state == "inventory":
            self._handle_inventory(key)
            return

        if self.state == "playing":
            self._handle_playing(key)

    def render(self):
        self.renderer.screen = self.screen
        if self.state == "menu":
            self.renderer.render_all(None, None, [], [], self.log_lines, "menu",
                                     0, 0)
            return
        if self.state in ("dead", "win"):
            self.renderer.render_all(self.dmap, self.player, self.enemies,
                                     self.items, self.log_lines, self.state,
                                     self.cam_x, self.cam_y)
            return

        self.renderer.render_all(
            self.dmap, self.player, self.enemies, self.items,
            self.log_lines, self.state, self.cam_x, self.cam_y,
            self.inventory_open, self.inv_cursor
        )

    # ── input handling ───────────────────────────────────────────────────────

    def _handle_playing(self, key):
        dx = dy = 0
        # movement / vi keys
        if key in (pygame.K_UP,    pygame.K_k): dy = -1
        elif key in (pygame.K_DOWN,  pygame.K_j): dy =  1
        elif key in (pygame.K_LEFT,  pygame.K_h): dx = -1
        elif key in (pygame.K_RIGHT, pygame.K_l): dx =  1
        elif key == pygame.K_y: dx=-1; dy=-1
        elif key == pygame.K_u: dx= 1; dy=-1
        elif key == pygame.K_b: dx=-1; dy= 1
        elif key == pygame.K_n: dx= 1; dy= 1

        elif key == pygame.K_g:      self._pick_up(); return
        elif key == pygame.K_i:      self._open_inventory(); return
        elif key == pygame.K_PERIOD and pygame.key.get_mods() & pygame.KMOD_SHIFT:
            self._descend(); return
        elif key == pygame.K_GREATER: self._descend(); return
        elif key == pygame.K_ESCAPE:  pygame.quit(); import sys; sys.exit()

        if dx or dy:
            self._try_move(dx, dy)

    def _handle_inventory(self, key):
        inv = self.player.inventory
        if key == pygame.K_ESCAPE or key == pygame.K_i:
            self.inventory_open = False
            self.state = "playing"
        elif key == pygame.K_UP or key == pygame.K_k:
            self.inv_cursor = max(0, self.inv_cursor - 1)
        elif key == pygame.K_DOWN or key == pygame.K_j:
            self.inv_cursor = min(len(inv)-1, self.inv_cursor + 1)
        elif key == pygame.K_e and inv:
            item = inv[self.inv_cursor]
            self.player.equip(item, self.log)
        elif key == pygame.K_u and inv:
            item = inv[self.inv_cursor]
            self._use_item(item)
        elif key == pygame.K_d and inv:
            item = inv.pop(self.inv_cursor)
            self.log(f"Dropped {item.name}.", C["text_dim"])
            self.items.append(Item(self.player.x, self.player.y, item.kind))
            self.inv_cursor = max(0, self.inv_cursor - 1)

    # ── actions ──────────────────────────────────────────────────────────────

    def _try_move(self, dx: int, dy: int):
        nx = self.player.x + dx
        ny = self.player.y + dy
        # attack if enemy there
        for enemy in self.enemies:
            if enemy.x == nx and enemy.y == ny:
                dmg = self.player.attack_enemy(enemy)
                self.log(f"You hit {enemy.name} for {dmg} damage.", C["text_green"])
                if enemy.is_dead():
                    xp = enemy.xp_val
                    gold = enemy.gold_drop()
                    self.player.gold  += gold
                    self.player.kills += 1
                    self.player.gain_xp(xp, self.log)
                    self.log(f"{enemy.name} slain! +{xp} XP, +{gold} gold.", C["text_gold"])
                    self.enemies.remove(enemy)
                self._end_turn()
                return
        # move
        if self.dmap.walkable(nx, ny):
            self.player.x, self.player.y = nx, ny
            self._update_fov()
            self._update_camera()
            self._end_turn()

    def _pick_up(self):
        for item in self.items:
            if item.x == self.player.x and item.y == self.player.y:
                if self.player.pick_up(item, self.log):
                    self.items.remove(item)
                return
        self.log("Nothing here to pick up.", C["text_dim"])

    def _open_inventory(self):
        if not self.player.inventory:
            self.log("Your inventory is empty.", C["text_dim"])
            return
        self.inventory_open = True
        self.inv_cursor = 0
        self.state = "inventory"

    def _use_item(self, item: Item):
        inv = self.player.inventory

        if item.kind == "scroll_fireball":
            hit = False
            for enemy in list(self.enemies):
                dist = math.hypot(enemy.x - self.player.x, enemy.y - self.player.y)
                if dist <= 5:
                    dmg = random.randint(18, 28)
                    actual = enemy.take_damage(dmg)
                    self.log(f"Fireball hits {enemy.name} for {actual}!", C["text_orange"])
                    if enemy.is_dead():
                        self.player.gain_xp(enemy.xp_val, self.log)
                        self.player.kills += 1
                        self.enemies.remove(enemy)
                    hit = True
            if not hit:
                self.log("The fireball fizzles — no enemies nearby.", C["text_dim"])
            inv.remove(item)

        elif item.kind == "scroll_teleport":
            room = random.choice(self.rooms)
            self.player.x = room.cx
            self.player.y = room.cy
            self.log("Reality warps. You are elsewhere.", C["text_blue"])
            self._update_fov()
            self._update_camera()
            inv.remove(item)

        else:
            used = item.use(self.player, self.log)
            if used:
                inv.remove(item)

        self.inv_cursor = max(0, min(self.inv_cursor, len(inv)-1))
        if not inv:
            self.inventory_open = False
            self.state = "playing"

    def _descend(self):
        t = self.dmap.tiles[self.player.x][self.player.y]
        if t.kind == 2:
            if self.player.floor >= MAX_FLOOR:
                self.log("You ascend victorious from the Abyss!", C["text_gold"])
                self.state = "win"
            else:
                self.log(f"You descend to floor {self.player.floor + 1}...", C["text_blue"])
                self._load_floor(self.player.floor + 1)
        else:
            self.log("No stairs here. Find the '>' to descend.", C["text_dim"])

    # ── turn management ───────────────────────────────────────────────────────

    def _end_turn(self):
        self.turn += 1
        self._run_enemies()
        if self.player.hp <= 0:
            self.state = "dead"
            self.log("You have died. The Abyss claims you.", C["text_red"])

    def _run_enemies(self):
        for enemy in self.enemies:
            dist = math.hypot(enemy.x - self.player.x,
                              enemy.y - self.player.y)
            tile = self.dmap.tiles[enemy.x][enemy.y]
            player_visible = self.dmap.tiles[self.player.x][self.player.y].visible

            if dist <= 1.5:
                # attack player
                dmg = enemy.attack_player(self.player)
                self.log(f"{enemy.name} hits you for {dmg}!", C["text_red"])
            elif dist <= FOV_RADIUS + 2 and player_visible:
                # pathfind toward player
                path = astar(self.dmap,
                             (enemy.x, enemy.y),
                             (self.player.x, self.player.y),
                             max_dist=FOV_RADIUS + 3)
                if path:
                    nx, ny = path[0]
                    occupied = any(e.x == nx and e.y == ny
                                   for e in self.enemies if e is not enemy)
                    if not occupied and (nx != self.player.x or ny != self.player.y):
                        enemy.x, enemy.y = nx, ny
            # else: enemy idles

    # ── floor loading ────────────────────────────────────────────────────────

    def _load_floor(self, floor: int):
        self.player.floor = floor
        is_boss = floor % 5 == 0

        self.dmap, self.rooms = generate_dungeon(MAP_W, MAP_H, floor)

        # place player in first room
        start = self.rooms[0]
        self.player.x = start.cx
        self.player.y = start.cy

        # stairs in last room
        last = self.rooms[-1]
        self.dmap.tiles[last.cx][last.cy].kind  = 2
        self.dmap.tiles[last.cx][last.cy].glyph = ">"

        # enemies
        self.enemies = spawn_enemies(self.rooms, floor, is_boss)
        # make sure no enemy spawns on player
        self.enemies = [e for e in self.enemies
                        if not (e.x == self.player.x and e.y == self.player.y)]

        # items — 1-2 per room
        self.items = []
        for room in self.rooms[1:]:
            count = random.randint(0, 1 + (1 if is_boss else 0))
            for _ in range(count):
                ix = random.randint(room.x+1, room.x2-2)
                iy = random.randint(room.y+1, room.y2-2)
                self.items.append(random_item(ix, iy, floor))

        if is_boss:
            self.log(f"Floor {floor} — A BOSS awaits you...", C["text_red"])
        else:
            self.log(f"Floor {floor} — darkness surrounds you.", C["text_blue"])

        self._update_fov()
        self._update_camera()
        self.inventory_open = False
        self.state = "playing"

    # ── helpers ───────────────────────────────────────────────────────────────

    def _update_fov(self):
        compute_fov(self.dmap, self.player.x, self.player.y, FOV_RADIUS)

    def _update_camera(self):
        from constants import VIEW_W, VIEW_H
        self.cam_x = max(0, min(self.dmap.width  - VIEW_W,
                                self.player.x - VIEW_W // 2))
        self.cam_y = max(0, min(self.dmap.height - VIEW_H,
                                self.player.y - VIEW_H // 2))

    def log(self, msg: str, color: tuple = None):
        if color is None:
            color = C["text"]
        self.log_lines.append((msg, color))
        if len(self.log_lines) > MAX_LOG:
            self.log_lines.pop(0)
