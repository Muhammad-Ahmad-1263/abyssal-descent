"""
constants.py — All tunable values in one place
"""

# Tile size in pixels
TILE = 28

# Map dimensions (in tiles)
MAP_W = 60
MAP_H = 38

# Viewport (tiles visible at once)
VIEW_W = 28
VIEW_H = 22

# Panel widths
SIDE_PANEL_W = 260   # pixels, right panel
LOG_PANEL_H  = 140   # pixels, bottom log

# Colors  (R, G, B)
C = {
    "bg":           (10,  10,  18),
    "floor":        (40,  38,  52),
    "floor_lit":    (70,  65,  88),
    "wall":         (22,  20,  32),
    "wall_lit":     (100, 92, 120),
    "stairs":       (255, 215,  80),
    "stairs_lit":   (255, 235, 130),
    "player":       (93, 202, 165),
    "hpbar_full":   (29, 158, 117),
    "hpbar_empty":  (80,  30,  30),
    "xpbar":        (100, 80, 200),
    "panel_bg":     (16,  14,  24),
    "panel_border": (50,  46,  70),
    "text":         (210, 205, 225),
    "text_dim":     (110, 105, 130),
    "text_gold":    (255, 215,  80),
    "text_red":     (220,  70,  70),
    "text_green":   (80,  200, 120),
    "text_blue":    (100, 160, 255),
    "text_purple":  (180, 100, 255),
    "text_orange":  (255, 160,  50),
    "fog":          (20,  18,  28),
    # item colors
    "item_potion":  (200,  80, 200),
    "item_weapon":  (200, 160,  50),
    "item_armor":   (80,  160, 220),
    "item_scroll":  (180, 220, 100),
    # enemy colors
    "enemy_weak":   (200,  80,  80),
    "enemy_mid":    (220, 130,  50),
    "enemy_tough":  (180,  60, 220),
    "enemy_boss":   (255,  50,  50),
}

# FOV radius
FOV_RADIUS = 8

# XP required to reach next level (index = current level)
XP_TABLE = [0, 50, 120, 220, 360, 550, 800, 1120, 1520, 2020, 9999]

# Floor difficulty scaling
def floor_scale(floor: int) -> float:
    return 1.0 + (floor - 1) * 0.18
