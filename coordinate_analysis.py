import pygame
import sys
import os

# Initialize pygame
pygame.init()
pygame.display.set_mode((800, 600))

# Add src to path
sys.path.append('src')
from map_loader import MapLoader

# Load map and analyze coordinates
map_path = os.path.join('assets', 'maps', 'Map1.tmx')
loader = MapLoader(map_path)

print('=== COORDINATE ANALYSIS ===')
print(f'Map size: {loader.tmx_data.width}x{loader.tmx_data.height} tiles')
print(f'Tile size: {loader.tmx_data.tilewidth}x{loader.tmx_data.tileheight} pixels')
print(f'Map pixel dimensions: {loader.width}x{loader.height}')

print('\nCollision tiles analysis:')
collision_layer = loader.tmx_data.get_layer_by_name('Collision')
min_x, max_x = float('inf'), float('-inf')
min_y, max_y = float('inf'), float('-inf')

collision_tile_positions = []
for x, y, gid in collision_layer:
    if gid != 0:  # Non-empty tile
        tile_x = x * loader.tmx_data.tilewidth
        tile_y = y * loader.tmx_data.tileheight
        collision_tile_positions.append((tile_x, tile_y, x, y))
        min_x, max_x = min(min_x, tile_x), max(min_x, tile_x)
        min_y, max_y = min(min_y, tile_y), max(max_y, tile_y)

print(f'Collision Y range: {min_y} to {max_y} pixels')
print(f'First 10 collision tiles (pixel_x, pixel_y, tile_x, tile_y):')
for i, (px, py, tx, ty) in enumerate(collision_tile_positions[:10]):
    print(f'  {i+1}: pixel=({px}, {py}) tile=({tx}, {ty})')

print('\nVisual layer analysis:')
visual_layer = None
for layer in loader.tmx_data.visible_layers:
    if layer.name != 'Collision':
        visual_layer = layer
        break

if visual_layer:
    print(f'Visual layer "{visual_layer.name}":')
    visual_tile_count = 0
    for x, y, gid in visual_layer:
        if gid != 0 and visual_tile_count < 5:
            tile_x = x * loader.tmx_data.tilewidth
            tile_y = y * loader.tmx_data.tileheight
            print(f'  Visual tile at pixel=({tile_x}, {tile_y}) tile=({x}, {y})')
            visual_tile_count += 1
