#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug script to analyze tile mapping issues in Map_Town
"""
import sys
import os
sys.path.append('src')
sys.path.append('src/managers')

import pygame
from world.map_loader import MapLoader

def debug_tile_mapping():
    pygame.init()
    
    # Load the map
    print("🔍 Loading Map_Town for tile mapping analysis...")
    loader = MapLoader('assets/maps/Map_Town.tmx')
    
    print("\n=== TILESET INFORMATION ===")
    for name, ts_info in loader.tilesets.items():
        firstgid = ts_info.get('firstgid', 0)
        tilecount = ts_info.get('tilecount', 0)
        columns = ts_info.get('columns', 0)
        spacing = ts_info.get('spacing', 0)
        margin = ts_info.get('margin', 0)
        lastgid = firstgid + tilecount - 1
        
        print(f"\n{name}:")
        print(f"  firstgid={firstgid}, lastgid={lastgid}, tilecount={tilecount}")
        print(f"  columns={columns}, spacing={spacing}, margin={margin}")
        
        if ts_info.get('image'):
            img_size = ts_info['image'].get_size()
            print(f"  image_size={img_size}")
            
            # Calculate expected tile dimensions
            if columns > 0 and tilecount > 0:
                rows = (tilecount + columns - 1) // columns  # Ceiling division
                expected_tile_w = (img_size[0] - 2*margin - (columns-1)*spacing) // columns
                expected_tile_h = (img_size[1] - 2*margin - (rows-1)*spacing) // rows
                print(f"  expected_rows={rows}, expected_tile_size={expected_tile_w}x{expected_tile_h}")
    
    print("\n=== GID CACHE ANALYSIS ===")
    print(f"Total GIDs in cache: {len(loader.tileset_cache)}")
    
    # Test first 20 GIDs from terrain tileset
    print("\n=== TERRAIN TILESET GID MAPPING (First 20) ===")
    terrain_firstgid = None
    for name, ts_info in loader.tilesets.items():
        if 'terrain' in name.lower():
            terrain_firstgid = ts_info['firstgid']
            terrain_columns = ts_info['columns']
            break
    
    if terrain_firstgid:
        for i in range(20):
            gid = terrain_firstgid + i
            if gid in loader.tileset_cache:
                tileset_name, local_id = loader.tileset_cache[gid]
                row = local_id // terrain_columns
                col = local_id % terrain_columns
                print(f"GID {gid} -> {tileset_name}, local_id={local_id}, pos=({col},{row})")
                
                # Test actual tile surface
                tile_surface = loader._get_tile_surface(gid)
                if tile_surface:
                    # Sample corner pixels
                    tl = tile_surface.get_at((0, 0))
                    tr = tile_surface.get_at((31, 0))
                    bl = tile_surface.get_at((0, 31))
                    br = tile_surface.get_at((31, 31))
                    print(f"  pixels: TL={tl} TR={tr} BL={bl} BR={br}")
                else:
                    print(f"  NO SURFACE!")
    
    print("\n=== MANUAL SLICE TEST ===")
    # Test manual slicing for first terrain tile
    if terrain_firstgid:
        gid = terrain_firstgid
        terrain_ts = None
        for name, ts_info in loader.tilesets.items():
            if 'terrain' in name.lower():
                terrain_ts = ts_info
                break
        
        if terrain_ts and terrain_ts.get('image'):
            local_id = 0  # First tile
            cols = terrain_ts['columns']
            spacing = terrain_ts['spacing']
            margin = terrain_ts['margin']
            
            col = local_id % cols
            row = local_id // cols
            
            # Manual calculation
            x = margin + col * (32 + spacing)
            y = margin + row * (32 + spacing)
            
            print(f"Manual slice for GID {gid} (local_id={local_id}):")
            print(f"  pos=({col},{row}), pixel_coords=({x},{y})")
            
            # Extract the tile manually
            tile_rect = pygame.Rect(x, y, 32, 32)
            full_image = terrain_ts['image']
            manual_tile = full_image.subsurface(tile_rect).copy()
            
            # Sample pixels
            tl = manual_tile.get_at((0, 0))
            tr = manual_tile.get_at((31, 0))
            bl = manual_tile.get_at((0, 31))
            br = manual_tile.get_at((31, 31))
            print(f"  manual_pixels: TL={tl} TR={tr} BL={bl} BR={br}")
            
            # Compare with loader result
            loader_tile = loader._get_tile_surface(gid)
            if loader_tile:
                l_tl = loader_tile.get_at((0, 0))
                l_tr = loader_tile.get_at((31, 0))
                l_bl = loader_tile.get_at((0, 31))
                l_br = loader_tile.get_at((31, 31))
                print(f"  loader_pixels: TL={l_tl} TR={l_tr} BL={l_bl} BR={l_br}")
                
                # Check if they match
                matches = (tl == l_tl and tr == l_tr and bl == l_bl and br == l_br)
                print(f"  PIXELS MATCH: {matches}")

if __name__ == "__main__":
    debug_tile_mapping()