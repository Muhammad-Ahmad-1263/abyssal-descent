"""
renderer.py — All drawing logic
"""
from __future__ import annotations
import pygame
from typing import List, TYPE_CHECKING
from constants import TILE, VIEW_W, VIEW_H, SIDE_PANEL_W, LOG_PANEL_H, C

if TYPE_CHECKING:
    from tiles import DungeonMap
    from entities import Player, Enemy, Item


class Renderer:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        pygame.font.init()
        self.font       = pygame.font.SysFont("consolas,monospace", TILE - 4, bold=True)
        self.font_sm    = pygame.font.SysFont("consolas,monospace", 14)
        self.font_md    = pygame.font.SysFont("consolas,monospace", 17)
        self.font_lg    = pygame.font.SysFont("consolas,monospace", 22, bold=True)
        self.font_title = pygame.font.SysFont("consolas,monospace", 36, bold=True)

    # ── helpers ──────────────────────────────────────────────────────────────

    def text(self, surf, txt, font, color, x, y):
        s = font.render(str(txt), True, color)
        surf.blit(s, (x, y))
        return s.get_width()

    def text_center(self, surf, txt, font, color, cx, y):
        s = font.render(str(txt), True, color)
        surf.blit(s, (cx - s.get_width()//2, y))

    def bar(self, surf, x, y, w, h, value, maximum, color_full, color_empty):
        pygame.draw.rect(surf, color_empty, (x, y, w, h))
        fill = int(w * max(0, value) / max(1, maximum))
        if fill > 0:
            pygame.draw.rect(surf, color_full, (x, y, fill, h))
        pygame.draw.rect(surf, C["panel_border"], (x, y, w, h), 1)

    # ── main render ──────────────────────────────────────────────────────────

    def render_all(self, dmap: "DungeonMap", player: "Player",
                   enemies: List["Enemy"], items: List["Item"],
                   log_lines: list, game_state: str,
                   cam_x: int, cam_y: int,
                   inventory_open: bool = False, inv_cursor: int = 0):

        W, H = self.screen.get_size()
        map_area_w = W - SIDE_PANEL_W
        map_area_h = H - LOG_PANEL_H

        self.screen.fill(C["bg"])

        if game_state == "playing" or game_state == "inventory":
            self._draw_map(dmap, player, enemies, items, cam_x, cam_y, map_area_w, map_area_h)
            self._draw_side_panel(player, W, H)
            self._draw_log(log_lines, map_area_w, map_area_h, W, H)

            if inventory_open:
                self._draw_inventory(player, inv_cursor, W, H)

        elif game_state == "menu":
            self._draw_menu(W, H)

        elif game_state == "dead":
            self._draw_game_over(player, W, H)

        elif game_state == "win":
            self._draw_win(player, W, H)

    # ── map drawing ──────────────────────────────────────────────────────────

    def _draw_map(self, dmap, player, enemies, items, cam_x, cam_y, area_w, area_h):
        item_pos  = {(it.x, it.y): it for it in items}
        enemy_pos = {(e.x, e.y): e for e in enemies}

        for vx in range(VIEW_W + 1):
            for vy in range(VIEW_H + 1):
                mx = cam_x + vx
                my = cam_y + vy
                if not dmap.in_bounds(mx, my):
                    continue
                tile = dmap.tiles[mx][my]
                px   = vx * TILE
                py   = vy * TILE
                if px + TILE > area_w or py + TILE > area_h:
                    continue

                if tile.visible:
                    # floor / wall base
                    bg = C["floor_lit"] if tile.walkable else C["wall_lit"]
                    pygame.draw.rect(self.screen, bg, (px, py, TILE, TILE))

                    if tile.kind == 2:  # stairs
                        self.text(self.screen, ">", self.font, C["stairs_lit"], px+4, py+2)
                    elif tile.kind == 1:
                        self._draw_glyph(".", C["floor_lit"], px, py, dim=True)

                    # items
                    if (mx, my) in item_pos:
                        it = item_pos[(mx, my)]
                        self.text(self.screen, it.glyph, self.font, it.color, px+4, py+2)

                    # enemies
                    if (mx, my) in enemy_pos:
                        en = enemy_pos[(mx, my)]
                        self.text(self.screen, en.glyph, self.font, en.color, px+4, py+2)
                        # mini health bar above
                        bw = TILE - 4
                        self.bar(self.screen, px+2, py, bw, 3,
                                 en.hp, en.max_hp, (220,60,60), (60,20,20))

                    # player
                    if mx == player.x and my == player.y:
                        self.text(self.screen, "@", self.font, C["player"], px+4, py+2)

                elif tile.visited:
                    # fog of war — show visited but dark
                    bg = (25, 22, 35) if tile.walkable else (15, 13, 22)
                    pygame.draw.rect(self.screen, bg, (px, py, TILE, TILE))
                    if tile.kind == 2:
                        self.text(self.screen, ">", self.font, (120, 100, 40), px+4, py+2)

    def _draw_glyph(self, g, color, px, py, dim=False):
        c = tuple(max(0, v - 20) for v in color) if dim else color
        s = self.font.render(g, True, c)
        self.screen.blit(s, (px+4, py+2))

    # ── side panel ───────────────────────────────────────────────────────────

    def _draw_side_panel(self, player, W, H):
        px = W - SIDE_PANEL_W
        panel = pygame.Surface((SIDE_PANEL_W, H), pygame.SRCALPHA)
        panel.fill(C["panel_bg"])
        pygame.draw.line(panel, C["panel_border"], (0,0), (0,H), 2)

        y = 10
        def row(txt, color=C["text"], bold=False):
            nonlocal y
            f = self.font_md if bold else self.font_sm
            s = f.render(txt, True, color)
            panel.blit(s, (12, y))
            y += s.get_height() + 3

        # Title
        s = self.font_lg.render("ABYSSAL DESCENT", True, C["text_gold"])
        panel.blit(s, (SIDE_PANEL_W//2 - s.get_width()//2, y))
        y += s.get_height() + 8
        pygame.draw.line(panel, C["panel_border"], (8,y), (SIDE_PANEL_W-8,y))
        y += 8

        row(f"{player.name}  (Level {player.level})", C["text_gold"], bold=True)
        row(f"Floor: {player.floor}", C["text"])
        row(f"Kills: {player.kills}", C["text_dim"])
        row(f"Gold:  {player.gold}", C["text_gold"])
        y += 4

        # HP bar
        row(f"HP: {player.hp} / {player.max_hp}", C["text_red"])
        self.bar(panel, 12, y, SIDE_PANEL_W-24, 10,
                 player.hp, player.max_hp, C["hpbar_full"], C["hpbar_empty"])
        y += 16

        # XP bar
        row(f"XP: {player.xp} / {player.xp_next}", C["xpbar"])
        self.bar(panel, 12, y, SIDE_PANEL_W-24, 8,
                 player.xp, player.xp_next, C["xpbar"], (30,20,60))
        y += 16
        pygame.draw.line(panel, C["panel_border"], (8,y), (SIDE_PANEL_W-8,y))
        y += 8

        row("STATS", C["text_dim"])
        row(f"ATK: {player.atk_total:>3}  DEF: {player.def_total:>3}", C["text"])

        if player.equipped_weapon:
            row(f"Wpn: {player.equipped_weapon.name}", C["item_weapon"])
        else:
            row("Wpn: (none)", C["text_dim"])
        if player.equipped_armor:
            row(f"Arm: {player.equipped_armor.name}", C["item_armor"])
        else:
            row("Arm: (none)", C["text_dim"])

        y += 6
        pygame.draw.line(panel, C["panel_border"], (8,y), (SIDE_PANEL_W-8,y))
        y += 8

        row("CONTROLS", C["text_dim"])
        for line in [
            "Arrow/HJKL  Move",
            "G           Pick up",
            "I           Inventory",
            "U           Use item",
            ">           Descend",
            "Esc         Quit",
        ]:
            row(line, C["text_dim"])

        self.screen.blit(panel, (px, 0))

    # ── log panel ────────────────────────────────────────────────────────────

    def _draw_log(self, log_lines, area_w, area_h, W, H):
        log_surf = pygame.Surface((area_w, LOG_PANEL_H), pygame.SRCALPHA)
        log_surf.fill(C["panel_bg"])
        pygame.draw.line(log_surf, C["panel_border"], (0,0), (area_w,0), 2)

        visible = log_lines[-6:]
        for i, (msg, color) in enumerate(visible):
            alpha = 255 if i == len(visible)-1 else max(80, 255 - (len(visible)-1-i)*45)
            c = tuple(int(v * alpha/255) for v in color)
            self.text(log_surf, msg, self.font_sm, c, 8, 6 + i*20)

        self.screen.blit(log_surf, (0, area_h))

    # ── inventory overlay ────────────────────────────────────────────────────

    def _draw_inventory(self, player, cursor, W, H):
        iw, ih = 500, 420
        ix, iy = W//2 - iw//2 - SIDE_PANEL_W//2, H//2 - ih//2
        surf = pygame.Surface((iw, ih), pygame.SRCALPHA)
        surf.fill((18, 15, 28, 240))
        pygame.draw.rect(surf, C["panel_border"], (0,0,iw,ih), 2, border_radius=6)

        self.text_center(surf, "— INVENTORY —", self.font_lg, C["text_gold"], iw//2, 12)
        pygame.draw.line(surf, C["panel_border"], (8,44), (iw-8,44))

        if not player.inventory:
            self.text_center(surf, "Empty", self.font_md, C["text_dim"], iw//2, ih//2)
        else:
            for i, item in enumerate(player.inventory):
                y = 52 + i * 22
                if i == cursor:
                    pygame.draw.rect(surf, (50,45,80), (6, y-1, iw-12, 20), border_radius=3)
                tag = ""
                if item == player.equipped_weapon or item == player.equipped_armor:
                    tag = " [E]"
                line = f"{chr(65+i)}) {item.glyph} {item.name}{tag}"
                self.text(surf, line, self.font_sm, item.color, 14, y)
                self.text(surf, item.desc, self.font_sm, C["text_dim"], iw-180, y)

        self.text_center(surf, "E=Equip  U=Use  ESC=Close", self.font_sm, C["text_dim"], iw//2, ih-24)
        self.screen.blit(surf, (ix, iy))

    # ── screens ──────────────────────────────────────────────────────────────

    def _draw_menu(self, W, H):
        self.text_center(self.screen, "ABYSSAL DESCENT", self.font_title,
                         C["text_gold"], W//2 - SIDE_PANEL_W//2, H//3 - 30)
        self.text_center(self.screen, "A Roguelike Dungeon Crawler",
                         self.font_md, C["text_dim"], W//2 - SIDE_PANEL_W//2, H//3 + 30)
        self.text_center(self.screen, "Press ENTER to begin your descent...",
                         self.font_md, C["text"], W//2 - SIDE_PANEL_W//2, H//2 + 20)
        self.text_center(self.screen, "Survive 10 floors to claim victory",
                         self.font_sm, C["text_dim"], W//2 - SIDE_PANEL_W//2, H//2 + 55)

    def _draw_game_over(self, player, W, H):
        cx = W//2 - SIDE_PANEL_W//2
        self.text_center(self.screen, "YOU DIED", self.font_title, C["text_red"], cx, H//3)
        self.text_center(self.screen, f"Reached Floor {player.floor}  |  Level {player.level}",
                         self.font_md, C["text"], cx, H//3 + 55)
        self.text_center(self.screen, f"Kills: {player.kills}   Gold: {player.gold}",
                         self.font_md, C["text_gold"], cx, H//3 + 85)
        self.text_center(self.screen, "Press ENTER to try again",
                         self.font_sm, C["text_dim"], cx, H//2 + 40)

    def _draw_win(self, player, W, H):
        cx = W//2 - SIDE_PANEL_W//2
        self.text_center(self.screen, "VICTORY!", self.font_title, C["text_gold"], cx, H//3)
        self.text_center(self.screen, "You conquered the Abyss!",
                         self.font_md, C["text"], cx, H//3 + 55)
        self.text_center(self.screen, f"Floor 10   Level {player.level}   Kills {player.kills}",
                         self.font_md, C["text_green"], cx, H//3 + 85)
        self.text_center(self.screen, "Press ENTER to play again",
                         self.font_sm, C["text_dim"], cx, H//2 + 40)
