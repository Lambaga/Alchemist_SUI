#!/usr/bin/env python3
import xml.etree.ElementTree as ET

# Parse Map_Village.tmx direkt
tree = ET.parse('assets/maps/Map_Village.tmx')
root = tree.getroot()

print('=== MAP_VILLAGE TMX ANALYSIS ===')
width = root.get('width')
height = root.get('height')
tile_w = root.get('tilewidth')
tile_h = root.get('tileheight')
print(f'Map size: {width}x{height}')
print(f'Tile size: {tile_w}x{tile_h}')

print('\n=== LAYERS ===')
for i, layer_elem in enumerate(root.findall('layer')):
    name = layer_elem.get('name')
    w = layer_elem.get('width', 0)
    h = layer_elem.get('height', 0)
    print(f'  Layer {i+1}: {name} ({w}x{h}) - Tile Layer')

print('\n=== OBJECT GROUPS ===')
for i, obj_group in enumerate(root.findall('objectgroup')):
    name = obj_group.get('name')
    objects = obj_group.findall('object')
    print(f'  Object Group {i+1}: {name} - {len(objects)} objects')
    
    for j, obj in enumerate(objects):
        obj_name = obj.get('name', 'unnamed')
        obj_x = obj.get('x')
        obj_y = obj.get('y')
        obj_width = obj.get('width', 0)
        obj_height = obj.get('height', 0)
        print(f'    Object {j+1}: "{obj_name}" at ({obj_x}, {obj_y}) size ({obj_width}x{obj_height})')

if len(root.findall('objectgroup')) == 0:
    print('  ⚠️ KEINE OBJECT GROUPS GEFUNDEN!')