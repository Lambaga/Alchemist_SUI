#!/usr/bin/env python3
# Debug-Skript: Charaktergröße vs. Tile-Größe analysieren

import os
import sys

# Füge src-Verzeichnis zum Python-Pfad hinzu
sys.path.insert(0, 'src')

import pygame
pygame.init()

try:
    from map_loader import MapLoader
    from config import PlayerConfig
    
    print("🔍 CHARAKTER-GRÖSSEN ANALYSE")
    print("=" * 50)
    
    # Map laden
    project_root = os.getcwd()
    map_path = os.path.join(project_root, "assets", "maps", "Map1.tmx")
    
    print(f"📁 Map-Pfad: {map_path}")
    print(f"📁 Existiert: {os.path.exists(map_path)}")
    
    if os.path.exists(map_path):
        map_loader = MapLoader(map_path)
        
        if map_loader.tmx_data:
            tile_w = map_loader.tmx_data.tilewidth
            tile_h = map_loader.tmx_data.tileheight
            
            print(f"\n🗺️  MAP INFORMATIONEN:")
            print(f"   Tile-Breite: {tile_w} Pixel")
            print(f"   Tile-Höhe: {tile_h} Pixel")
            
            print(f"\n🧙‍♂️ CHARAKTER INFORMATIONEN:")
            char_w = PlayerConfig.SPRITE_WIDTH
            char_h = PlayerConfig.SPRITE_HEIGHT
            print(f"   Charakter-Breite: {char_w} Pixel")
            print(f"   Charakter-Höhe: {char_h} Pixel")
            
            print(f"\n📏 VERHÄLTNIS BERECHNUNG:")
            ratio_w = char_w / tile_w
            ratio_h = char_h / tile_h
            print(f"   Breite: {char_w} ÷ {tile_w} = {ratio_w:.2f} Tiles")
            print(f"   Höhe: {char_h} ÷ {tile_h} = {ratio_h:.2f} Tiles")
            
            print(f"\n🎯 BEWERTUNG:")
            if 1.8 <= ratio_w <= 2.2 and 1.8 <= ratio_h <= 2.2:
                print("   ✅ PERFEKT - Charakter ist ~2 Tiles groß")
            elif ratio_w < 1.5 or ratio_h < 1.5:
                print("   ⚠️  ZU KLEIN - Charakter schwer sichtbar")
            elif ratio_w > 3.0 or ratio_h > 3.0:
                print("   ⚠️  ZU GROSS - Charakter dominiert zu sehr")
            else:
                print("   ✅ GUT - Akzeptable Größe")
                
        else:
            print("❌ Map-Daten konnten nicht geladen werden")
    else:
        print("❌ Map-Datei nicht gefunden")
        
except Exception as e:
    print(f"❌ Fehler beim Laden: {e}")
    import traceback
    traceback.print_exc()
