"""
entities.py — Player, Enemy, Item, and base Entity classes
"""
from __future__ import annotations
import random
import math
from typing import Optional, List, TYPE_CHECKING
from constants import C, XP_TABLE, floor_scale

if TYPE_CHECKING:
    from tiles import DungeonMap


class Entity:
    def __init__(self, x: int, y: int, glyph: str, color: tuple, name: str):
        self.x     = x
        self.y     = y
        self.glyph = glyph
        self.color = color
        self.name  = name


# ─── Items ──────────────────────────────────────────────────────────────────

class Item(Entity):
    def __init__(self, x, y, kind: str):
        data = ITEM_DEFS[kind]
        super().__init__(x, y, data["glyph"], data["color"], data["name"])
        self.kind   = kind
        self.value  = data["value"]
        self.desc   = data["desc"]

    def use(self, player: "Player", log) -> bool:
        """Returns True if item was consumed."""
        if self.kind == "health_potion":
            healed = min(player.max_hp - player.hp, self.value)
            player.hp += healed
            log(f"You drink the {self.name}. +{healed} HP.", C["text_green"])
            return True
        if self.kind == "strength_potion":
            player.attack += self.value
            log(f"Power surges through you! +{self.value} ATK.", C["text_orange"])
            return True
        if self.kind == "scroll_fireball":
            log("The scroll crumbles. (No target — use near enemies.)", C["text_dim"])
            return True  # handled specially in game.py
        if self.kind == "scroll_teleport":
            return False  # handled in game.py
        return False


ITEM_DEFS = {
    "health_potion": {
        "glyph": "!", "color": C["item_potion"],
        "name": "Health Potion", "value": 20,
        "desc": "Restores 20 HP",
    },
    "strength_potion": {
        "glyph": "!", "color": C["text_orange"],
        "name": "Strength Potion", "value": 3,
        "desc": "+3 ATK permanently",
    },
    "scroll_fireball": {
        "glyph": "?", "color": C["item_scroll"],
        "name": "Scroll of Fireball", "value": 15,
        "desc": "Damages all nearby enemies",
    },
    "scroll_teleport": {
        "glyph": "?", "color": C["text_blue"],
        "name": "Scroll of Teleport", "value": 0,
        "desc": "Teleports you to a random room",
    },
    "sword": {
        "glyph": "/", "color": C["item_weapon"],
        "name": "Iron Sword", "value": 5,
        "desc": "+5 ATK",
    },
    "great_sword": {
        "glyph": "/", "color": C["text_gold"],
        "name": "Greatsword", "value": 10,
        "desc": "+10 ATK",
    },
    "leather_armor": {
        "glyph": "[", "color": C["item_armor"],
        "name": "Leather Armor", "value": 3,
        "desc": "+3 DEF",
    },
    "chain_mail": {
        "glyph": "[", "color": C["text_blue"],
        "name": "Chain Mail", "value": 6,
        "desc": "+6 DEF",
    },
    "plate_armor": {
        "glyph": "[", "color": C["text_purple"],
        "name": "Plate Armor", "value": 10,
        "desc": "+10 DEF",
    },
}

ITEM_WEIGHTS = {
    "health_potion": 30,
    "strength_potion": 10,
    "scroll_fireball": 12,
    "scroll_teleport": 8,
    "sword": 14,
    "great_sword": 6,
    "leather_armor": 12,
    "chain_mail": 6,
    "plate_armor": 3,
}


def random_item(x: int, y: int, floor: int) -> Item:
    pool = list(ITEM_WEIGHTS.keys())
    weights = [ITEM_WEIGHTS[k] for k in pool]
    if floor < 3:
        # fewer great weapons early
        weights[pool.index("great_sword")] = 1
        weights[pool.index("plate_armor")] = 1
    kind = random.choices(pool, weights=weights)[0]
    return Item(x, y, kind)


# ─── Player ─────────────────────────────────────────────────────────────────

class Player(Entity):
    def __init__(self, x: int, y: int):
        super().__init__(x, y, "@", C["player"], "Hero")
        self.max_hp  = 80
        self.hp      = 80
        self.attack  = 10
        self.defense = 3
        self.level   = 1
        self.xp      = 0
        self.gold    = 0
        self.floor   = 1
        self.inventory: List[Item] = []
        self.equipped_weapon: Optional[Item] = None
        self.equipped_armor:  Optional[Item] = None
        self.kills   = 0

    @property
    def xp_next(self) -> int:
        return XP_TABLE[min(self.level, len(XP_TABLE)-1)]

    @property
    def atk_total(self) -> int:
        bonus = self.equipped_weapon.value if self.equipped_weapon else 0
        return self.attack + bonus

    @property
    def def_total(self) -> int:
        bonus = self.equipped_armor.value if self.equipped_armor else 0
        return self.defense + bonus

    def gain_xp(self, amount: int, log) -> bool:
        """Returns True if leveled up."""
        self.xp += amount
        if self.xp >= self.xp_next and self.level < len(XP_TABLE) - 1:
            self.xp -= self.xp_next
            self.level += 1
            self.max_hp  += 12
            self.hp       = min(self.hp + 12, self.max_hp)
            self.attack  += 2
            self.defense += 1
            log(f"Level up! You are now level {self.level}!", C["text_gold"])
            return True
        return False

    def take_damage(self, raw: int) -> int:
        dmg = max(1, raw - self.def_total)
        self.hp -= dmg
        return dmg

    def attack_enemy(self, enemy: "Enemy") -> int:
        base = self.atk_total + random.randint(-2, 2)
        return enemy.take_damage(base)

    def move(self, dx: int, dy: int, dmap: "DungeonMap") -> bool:
        nx, ny = self.x + dx, self.y + dy
        if dmap.walkable(nx, ny):
            self.x, self.y = nx, ny
            return True
        return False

    def pick_up(self, item: Item, log):
        if len(self.inventory) >= 16:
            log("Inventory full!", C["text_red"])
            return False
        self.inventory.append(item)
        log(f"Picked up {item.name}.", C["text_green"])
        return True

    def equip(self, item: Item, log):
        if item.kind in ("sword", "great_sword"):
            self.equipped_weapon = item
            log(f"Equipped {item.name}. (+{item.value} ATK)", C["text_gold"])
        elif item.kind in ("leather_armor", "chain_mail", "plate_armor"):
            self.equipped_armor = item
            log(f"Equipped {item.name}. (+{item.value} DEF)", C["text_blue"])


# ─── Enemies ────────────────────────────────────────────────────────────────

ENEMY_DEFS = {
    "rat": {
        "glyph": "r", "color": C["enemy_weak"], "name": "Giant Rat",
        "hp": 12, "atk": 5, "defense": 0, "xp": 10, "gold": (0, 3),
        "speed": 1, "min_floor": 1,
    },
    "goblin": {
        "glyph": "g", "color": C["enemy_weak"], "name": "Goblin",
        "hp": 18, "atk": 8, "defense": 1, "xp": 18, "gold": (1, 6),
        "speed": 1, "min_floor": 1,
    },
    "orc": {
        "glyph": "o", "color": C["enemy_mid"], "name": "Orc",
        "hp": 35, "atk": 14, "defense": 3, "xp": 40, "gold": (3, 10),
        "speed": 1, "min_floor": 3,
    },
    "troll": {
        "glyph": "T", "color": C["enemy_mid"], "name": "Troll",
        "hp": 55, "atk": 18, "defense": 5, "xp": 70, "gold": (5, 15),
        "speed": 1, "min_floor": 5,
    },
    "vampire": {
        "glyph": "V", "color": C["enemy_tough"], "name": "Vampire",
        "hp": 45, "atk": 20, "defense": 4, "xp": 90, "gold": (8, 20),
        "speed": 1, "min_floor": 6,
    },
    "demon": {
        "glyph": "D", "color": C["enemy_tough"], "name": "Demon",
        "hp": 70, "atk": 24, "defense": 7, "xp": 130, "gold": (10, 25),
        "speed": 1, "min_floor": 8,
    },
    # Bosses — spawned explicitly on floor % 5 == 0
    "boss_lich": {
        "glyph": "L", "color": C["enemy_boss"], "name": "The Lich King",
        "hp": 180, "atk": 30, "defense": 10, "xp": 500, "gold": (30, 60),
        "speed": 1, "min_floor": 5,
    },
    "boss_dragon": {
        "glyph": "W", "color": C["enemy_boss"], "name": "Shadow Dragon",
        "hp": 280, "atk": 40, "defense": 14, "xp": 900, "gold": (50, 100),
        "speed": 1, "min_floor": 10,
    },
}


class Enemy(Entity):
    def __init__(self, x: int, y: int, kind: str, floor: int):
        d = ENEMY_DEFS[kind]
        super().__init__(x, y, d["glyph"], d["color"], d["name"])
        scale = floor_scale(floor)
        self.max_hp  = int(d["hp"]  * scale)
        self.hp      = self.max_hp
        self.attack  = int(d["atk"] * scale)
        self.defense = int(d["defense"] * scale)
        self.xp_val  = d["xp"]
        self.gold_range = d["gold"]
        self.kind    = kind
        self.is_boss = kind.startswith("boss")
        self.path: list = []   # for pathfinding

    def take_damage(self, raw: int) -> int:
        dmg = max(1, raw - self.defense)
        self.hp -= dmg
        return dmg

    def is_dead(self) -> bool:
        return self.hp <= 0

    def gold_drop(self) -> int:
        lo, hi = self.gold_range
        return random.randint(lo, hi)

    def attack_player(self, player: Player) -> int:
        raw = self.attack + random.randint(-2, 2)
        return player.take_damage(raw)


def spawn_enemies(rooms: list, floor: int, is_boss_floor: bool) -> List[Enemy]:
    enemies = []
    eligible = [k for k, d in ENEMY_DEFS.items()
                if not k.startswith("boss") and d["min_floor"] <= floor]

    if is_boss_floor:
        boss_kind = "boss_dragon" if floor >= 10 else "boss_lich"
        cx, cy = rooms[0].cx, rooms[0].cy
        enemies.append(Enemy(cx, cy, boss_kind, floor))

    for room in rooms[1:]:
        count = random.randint(0, 2 + floor // 3)
        for _ in range(count):
            if not eligible:
                break
            kind = random.choice(eligible)
            # scatter within room
            ex = random.randint(room.x + 1, room.x2 - 2)
            ey = random.randint(room.y + 1, room.y2 - 2)
            enemies.append(Enemy(ex, ey, kind, floor))

    return enemies
