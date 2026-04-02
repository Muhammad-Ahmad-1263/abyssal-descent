# Abyssal Descent 🗡️

A feature-rich, turn-based **roguelike dungeon crawler** built entirely in Python with Pygame.

Every run is different — procedurally generated dungeons, randomized loot, and increasingly brutal enemies await you in the depths.

---

## Features

- **Procedural dungeon generation** using BSP (Binary Space Partitioning) — no two floors are the same
- **Recursive shadowcasting FOV** — fog of war that reveals the dungeon as you explore
- **A\* pathfinding** — enemies intelligently hunt you through corridors
- **Turn-based combat** with attack, defense, and damage variance
- **8 enemy types** scaling in difficulty: Rats, Goblins, Orcs, Trolls, Vampires, Demons, and 2 unique Bosses
- **Full inventory system** — pick up, equip, and use items
- **8 item types**: potions, weapons, armor, and scrolls (Fireball, Teleport)
- **Leveling system** — gain XP, level up, and grow stronger
- **10 floors** — boss encounters every 5 floors
- **Color-coded log** — track every event in the message panel

---

## Screenshots

> *(Add screenshots here once you run the game)*
> <img width="1351" height="888" alt="Screenshot 2026-04-03 004641" src="https://github.com/user-attachments/assets/54aa420f-fa1a-4e95-aab6-85975a4e2e41" />


---

## Installation

**Requirements:** Python 3.8+ and Pygame

```bash
pip install pygame
```

**Run the game:**

```bash
git clone https://github.com/YOUR_USERNAME/abyssal-descent.git
cd abyssal-descent
python main.py
```

---

## Controls

| Key | Action |
|-----|--------|
| Arrow keys / HJKL | Move |
| YUBN | Diagonal movement |
| G | Pick up item |
| I | Open inventory |
| E (in inventory) | Equip item |
| U (in inventory) | Use item |
| D (in inventory) | Drop item |
| > | Descend stairs |
| ESC | Quit |

---

## Architecture

```
abyssal-descent/
├── main.py          # Entry point
├── game.py          # Game loop, state machine, turn management
├── entities.py      # Player, Enemy, Item classes
├── dungeon_gen.py   # BSP procedural dungeon generator
├── fov.py           # Recursive shadowcasting field-of-view
├── pathfinding.py   # A* pathfinding for enemy AI
├── renderer.py      # All Pygame rendering
├── tiles.py         # Tile and map data structures
├── constants.py     # Tunable config values and color palette
└── README.md
```

---

## License

MIT — free to use, modify, and distribute.
