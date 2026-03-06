#!/usr/bin/env python3
"""
Generate Map_Town.tmx - a town map using the same 32x32.tsx tileset
that Map3 and Map_Village use, guaranteeing compatibility.

Town layout (80x60 tiles = 2560x1920 pixels):
- Grassy ground with dirt paths forming a cross/grid
- 6 houses scattered around
- A small pond in the NE corner
- Trees lining the edges and between buildings
- Flowers and decoration
- Stone walls and fences
- Enemies placed in strategic locations
- Player spawn near center-south
"""

import random

random.seed(42)  # Reproducible

W, H = 80, 60

# === Tile GID constants (from 32x32.tsx) ===
EMPTY = 0
GRASS = 35
GRASS_A = 9
GRASS_B = 10
GRASS_TUFT = 14

# Path tiles (outer border - 3x3 autotile)
PATH_TL = 18; PATH_T = 19; PATH_TR = 20
PATH_L = 44; PATH_C = 45; PATH_R = 46
PATH_BL = 70; PATH_B = 71; PATH_BR = 72
# Path inner corners
PATH_I_TL = 15; PATH_I_T = 16; PATH_I_TR = 17
PATH_I_L = 41; PATH_I_R = 43
PATH_I_BL = 67; PATH_I_B = 68; PATH_I_BR = 69

# Water tiles
W_TL = 24; W_T = 25; W_TR = 26
W_L = 50; W_FILL = 181; W_R = 52
W_BL = 336; W_B = 337; W_BR = 338
W_SHALLOW = 51

# Tree trunk (3-wide, placed on ground layer with hitbox)
TREE_A = [209, 210, 211]
TREE_B = [212, 213, 214]
# Tree canopy (3-wide, on Foreground layer)
TREE_CANOPY_A_TOP = [105, 106, 107]
TREE_CANOPY_A_MID = [131, 0, 0]  # Just left trunk visible

# House tiles (3-wide x 4-tall)
ROOF_TOP = [163, 164, 165]
ROOF_BOT = [189, 190, 191]
HOUSE_WALL = [215, 216, 217]
HOUSE_BASE = [241, 242, 243]

# Rocks
ROCK_SM = 6
ROCK_MED = 31
PEBBLES = 32
ROCK_BIG_TL = 7; ROCK_BIG_TR = 8
ROCK_BIG_BL = 33; ROCK_BIG_BR = 34
BOULDER_TL = 59; BOULDER_TR = 60
BOULDER_BL = 85; BOULDER_BR = 86

# Flowers
FLOWERS = [30, 36, 37, 38, 39, 40, 63, 64, 89]

# Fence
FENCE_L = 115; FENCE_R = 116

# Chimney / Sign
CHIMNEY = 90

# ============================================================
# Create layers as 2D arrays
# ============================================================
def make_grid():
    return [[EMPTY] * W for _ in range(H)]

soil = make_grid()      # Base ground fill
path_layer = make_grid() # Paths / roads
trees = make_grid()     # Tree trunks (hitbox)
flowers = make_grid()   # Flowers & decoration
stones = make_grid()    # Stones with hitbox
house = make_grid()     # Buildings
water = make_grid()     # Pond / stream
foreground = make_grid() # Tree canopy, roof details

# === 1. Fill soil with grass ===
for y in range(H):
    for x in range(W):
        r = random.random()
        if r < 0.7:
            soil[y][x] = GRASS
        elif r < 0.85:
            soil[y][x] = GRASS_A
        else:
            soil[y][x] = GRASS_B

# === 2. Create paths (cross pattern + border road) ===
# Main horizontal road at y=28-30
for y in range(28, 31):
    for x in range(2, W - 2):
        if y == 28:
            if x == 2:
                path_layer[y][x] = PATH_TL
            elif x == W - 3:
                path_layer[y][x] = PATH_TR
            else:
                path_layer[y][x] = PATH_T
        elif y == 30:
            if x == 2:
                path_layer[y][x] = PATH_BL
            elif x == W - 3:
                path_layer[y][x] = PATH_BR
            else:
                path_layer[y][x] = PATH_B
        else:
            if x == 2:
                path_layer[y][x] = PATH_L
            elif x == W - 3:
                path_layer[y][x] = PATH_R
            else:
                path_layer[y][x] = PATH_C

# Main vertical road at x=38-40
for y in range(2, H - 2):
    for x in range(38, 41):
        # Skip intersection with horizontal road (already filled)
        if 28 <= y <= 30:
            path_layer[y][x] = PATH_C
            continue
        if y == 2:
            if x == 38:
                path_layer[y][x] = PATH_TL
            elif x == 40:
                path_layer[y][x] = PATH_TR
            else:
                path_layer[y][x] = PATH_T
        elif y == H - 3:
            if x == 38:
                path_layer[y][x] = PATH_BL
            elif x == 40:
                path_layer[y][x] = PATH_BR
            else:
                path_layer[y][x] = PATH_B
        else:
            if x == 38:
                path_layer[y][x] = PATH_L
            elif x == 40:
                path_layer[y][x] = PATH_R
            else:
                path_layer[y][x] = PATH_C

# Fix intersection corners (vertical meets horizontal)
# Top of vertical road meeting horizontal:
# At y=28, x=38 - path already going, use inner corners
path_layer[28][38] = PATH_I_BR
path_layer[28][40] = PATH_I_BL
path_layer[30][38] = PATH_I_TR
path_layer[30][40] = PATH_I_TL

# Secondary paths to houses
# Path from main road going left to house area (y=15-17, x=15-38)
for y in range(15, 18):
    for x in range(15, 38):
        if path_layer[y][x] != EMPTY:
            continue
        if y == 15:
            if x == 15:
                path_layer[y][x] = PATH_TL
            else:
                path_layer[y][x] = PATH_T
        elif y == 17:
            if x == 15:
                path_layer[y][x] = PATH_BL
            else:
                path_layer[y][x] = PATH_B
        else:
            if x == 15:
                path_layer[y][x] = PATH_L
            else:
                path_layer[y][x] = PATH_C

# Connect to vertical road
path_layer[15][38] = PATH_I_BR
path_layer[17][38] = PATH_I_TR

# Path going right from vertical road (y=44-46, x=40-65)
for y in range(44, 47):
    for x in range(41, 65):
        if y == 44:
            if x == 64:
                path_layer[y][x] = PATH_TR
            else:
                path_layer[y][x] = PATH_T
        elif y == 46:
            if x == 64:
                path_layer[y][x] = PATH_BR
            else:
                path_layer[y][x] = PATH_B
        else:
            if x == 64:
                path_layer[y][x] = PATH_R
            else:
                path_layer[y][x] = PATH_C

path_layer[44][40] = PATH_I_BL
path_layer[46][40] = PATH_I_TL


# === 3. Place houses ===
# Each house is 3 wide x 4 tall
# house_positions: (top-left x, top-left y)
house_positions = [
    (8, 8),     # NW house
    (25, 8),    # N house
    (50, 8),    # NE house
    (8, 38),    # SW house
    (25, 42),   # S house
    (55, 40),   # SE house
]

# Track wall collision rects
wall_rects = []

for hx, hy in house_positions:
    # Roof top row
    for i, gid in enumerate(ROOF_TOP):
        house[hy][hx + i] = gid
    # Roof bottom row
    for i, gid in enumerate(ROOF_BOT):
        house[hy + 1][hx + i] = gid
    # Wall row (with door)
    for i, gid in enumerate(HOUSE_WALL):
        house[hy + 2][hx + i] = gid
    # Base row
    for i, gid in enumerate(HOUSE_BASE):
        house[hy + 3][hx + i] = gid

    # Chimney above house
    foreground[hy - 1][hx + 1] = CHIMNEY

    # Collision rect for entire house
    wall_rects.append((hx * 32, hy * 32, 3 * 32, 4 * 32))


# === 4. Place trees ===
# Tree positions (trunk at these coords, canopy 2 rows above)
tree_positions = []

# Top border trees
for x in range(1, W - 4, 5):
    if not any(hx - 4 <= x <= hx + 6 for hx, hy in house_positions if hy < 15):
        tree_positions.append((x, 3))

# Bottom border trees
for x in range(1, W - 4, 5):
    if not any(hx - 4 <= x <= hx + 6 for hx, hy in house_positions if hy > 45):
        tree_positions.append((x, H - 4))

# Left border trees
for y in range(5, H - 5, 5):
    if not any(hy - 4 <= y <= hy + 7 for hx, hy in house_positions if hx < 15):
        tree_positions.append((0, y))

# Right border trees
for y in range(5, H - 5, 5):
    tree_positions.append((W - 4, y))

# Some interior trees (avoid paths and houses)
interior_trees = [
    (18, 22), (30, 20), (48, 22), (62, 18),
    (15, 50), (30, 52), (48, 50), (68, 48),
    (18, 35), (62, 35),
]

for tx, ty in interior_trees:
    # Check not on path or house
    blocked = False
    for hx, hy in house_positions:
        if hx - 4 <= tx <= hx + 5 and hy - 3 <= ty <= hy + 6:
            blocked = True
            break
    if not blocked:
        tree_positions.append((tx, ty))

for tx, ty in tree_positions:
    if tx + 2 >= W or ty >= H or ty - 2 < 0:
        continue
    # Pick tree type
    tree_type = TREE_A if random.random() < 0.5 else TREE_B
    # Place trunk (3 tiles)
    for i, gid in enumerate(tree_type):
        if tx + i < W:
            trees[ty][tx + i] = gid
    # Place canopy on foreground (2 rows above trunk, 3 tiles wide)
    canopy_y = ty - 2
    if canopy_y >= 0:
        for i, gid in enumerate(TREE_CANOPY_A_TOP):
            if tx + i < W:
                foreground[canopy_y][tx + i] = gid
    # Add collision for trunk
    wall_rects.append((tx * 32, ty * 32, 3 * 32, 32))

# === 5. Place pond (NE area) ===
pond_x, pond_y = 62, 24
pond_w, pond_h = 8, 6

# Top edge
water[pond_y][pond_x] = W_TL
for x in range(pond_x + 1, pond_x + pond_w - 1):
    water[pond_y][x] = W_T
water[pond_y][pond_x + pond_w - 1] = W_TR

# Middle rows
for y in range(pond_y + 1, pond_y + pond_h - 1):
    water[y][pond_x] = W_L
    for x in range(pond_x + 1, pond_x + pond_w - 1):
        water[y][x] = W_FILL
    water[y][pond_x + pond_w - 1] = W_R

# Bottom edge
water[pond_y + pond_h - 1][pond_x] = W_BL
for x in range(pond_x + 1, pond_x + pond_w - 1):
    water[pond_y + pond_h - 1][x] = W_B
water[pond_y + pond_h - 1][pond_x + pond_w - 1] = W_BR

# Collision for pond
wall_rects.append((pond_x * 32, pond_y * 32, pond_w * 32, pond_h * 32))


# === 6. Place flowers ===
flower_clusters = [
    (12, 14, 4, 2), (32, 10, 3, 2), (45, 14, 3, 2),
    (10, 48, 4, 2), (35, 48, 3, 2), (60, 48, 3, 2),
    (5, 25, 3, 2), (70, 25, 3, 2),
]

for fx, fy, fw, fh in flower_clusters:
    for dy in range(fh):
        for dx in range(fw):
            if fy + dy < H and fx + dx < W:
                if random.random() < 0.7:
                    flowers[fy + dy][fx + dx] = random.choice(FLOWERS)


# === 7. Place stones ===
stone_positions = [
    (5, 20), (15, 33), (65, 15), (72, 42),
    (22, 55), (55, 55), (3, 53),
]

for sx, sy in stone_positions:
    if sx + 1 < W and sy + 1 < H:
        stones[sy][sx] = BOULDER_TL
        stones[sy][sx + 1] = BOULDER_TR
        stones[sy + 1][sx] = BOULDER_BL
        stones[sy + 1][sx + 1] = BOULDER_BR
        wall_rects.append((sx * 32, sy * 32, 64, 64))

# Place some fences near houses
fence_positions = [
    # Fence below NW house
    (7, 13), (8, 13), (9, 13), (10, 13), (11, 13),
    # Fence below N house
    (24, 13), (25, 13), (26, 13), (27, 13), (28, 13),
]

for fx, fy in fence_positions:
    stones[fy][fx] = FENCE_L if (fx % 2 == 0) else FENCE_R


# === 8. Map border walls ===
# Top wall
wall_rects.append((0, 0, W * 32, 32))
# Bottom wall
wall_rects.append((0, (H - 1) * 32, W * 32, 32))
# Left wall
wall_rects.append((0, 0, 32, H * 32))
# Right wall
wall_rects.append(((W - 1) * 32, 0, 32, H * 32))


# === 9. Generate TMX XML ===
def layer_to_csv(grid):
    rows = []
    for y in range(H):
        row = ",".join(str(grid[y][x]) for x in range(W))
        rows.append(row)
    return ",\n".join(rows)

# Enemy positions (matching level.py integration: 5 demons + 4 fireworms)
# Spread across the map, placed near houses and paths
enemies = [
    ("demon", 300, 300, 41, 34),
    ("demon", 1800, 500, 41, 34),
    ("demon", 700, 1200, 41, 34),
    ("demon", 2100, 1200, 41, 34),
    ("demon", 1200, 1600, 41, 34),
    ("fireworm", 500, 800, 51, 51),
    ("fireworm", 1900, 800, 51, 51),
    ("fireworm", 400, 1500, 51, 51),
    ("fireworm", 2200, 1500, 51, 51),
]

# Spawn point (center-south of map, near the crossroads)
spawn_x = 39 * 32  # Near center of map (vertical road)
spawn_y = 32 * 32  # Just below horizontal road

layer_id = 1
obj_id = 1

tmx = f'''<?xml version="1.0" encoding="UTF-8"?>
<map version="1.10" tiledversion="1.11.2" orientation="orthogonal" renderorder="right-down" width="{W}" height="{H}" tilewidth="32" tileheight="32" infinite="0" nextlayerid="20" nextobjectid="200">
 <tileset firstgid="1" source="32x32.tsx"/>
 <layer id="1" name="Soil" width="{W}" height="{H}">
  <data encoding="csv">
{layer_to_csv(soil)}
</data>
 </layer>
 <layer id="2" name="water" width="{W}" height="{H}">
  <data encoding="csv">
{layer_to_csv(water)}
</data>
 </layer>
 <layer id="3" name="path" width="{W}" height="{H}">
  <data encoding="csv">
{layer_to_csv(path_layer)}
</data>
 </layer>
 <layer id="4" name="Trees" width="{W}" height="{H}">
  <data encoding="csv">
{layer_to_csv(trees)}
</data>
 </layer>
 <layer id="5" name="Flowers (no Hitbox)" width="{W}" height="{H}">
  <data encoding="csv">
{layer_to_csv(flowers)}
</data>
 </layer>
 <layer id="6" name="Stones (Hitbox)" width="{W}" height="{H}">
  <data encoding="csv">
{layer_to_csv(stones)}
</data>
 </layer>
 <layer id="7" name="House" width="{W}" height="{H}">
  <data encoding="csv">
{layer_to_csv(house)}
</data>
 </layer>
 <objectgroup id="10" name="Enemy">
'''

for i, (ename, ex, ey, ew, eh) in enumerate(enemies):
    tmx += f'  <object id="{100 + i}" name="{ename}" x="{ex}" y="{ey}" width="{ew}" height="{eh}"/>\n'

tmx += ''' </objectgroup>
 <objectgroup id="11" name="Walls">
'''

for i, (wx, wy, ww, wh) in enumerate(wall_rects):
    tmx += f'  <object id="{150 + i}" x="{wx}" y="{wy}" width="{ww}" height="{wh}"/>\n'

tmx += f''' </objectgroup>
 <layer id="8" name="Foreground" width="{W}" height="{H}" opacity="0.43">
  <data encoding="csv">
{layer_to_csv(foreground)}
</data>
 </layer>
 <objectgroup id="12" name="Spawn">
  <object id="199" name="spawn" x="{spawn_x}" y="{spawn_y}" width="23" height="21"/>
 </objectgroup>
</map>
'''

output_path = "/Users/kirill/Work/Alchemist_SUI/assets/maps/Map_Town.tmx"
with open(output_path, "w", encoding="utf-8") as f:
    f.write(tmx)

print(f"Generated Map_Town.tmx: {W}x{H} tiles ({W*32}x{H*32} pixels)")
print(f"  Houses: {len(house_positions)}")
print(f"  Trees: {len(tree_positions)}")
print(f"  Enemies: {len(enemies)}")
print(f"  Wall rects: {len(wall_rects)}")
print(f"  Spawn at: ({spawn_x}, {spawn_y})")
print(f"  Saved to: {output_path}")
