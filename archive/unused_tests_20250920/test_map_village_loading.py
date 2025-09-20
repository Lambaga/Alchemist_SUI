   #!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script für Map_Village Loading
"""
import sys
import os

# Add src directories to path
src_dir = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_dir)
sys.path.insert(0, os.path.join(src_dir, 'core'))
sys.path.insert(0, os.path.join(src_dir, 'managers'))
sys.path.insert(0, os.path.join(src_dir, 'ui'))
sys.path.insert(0, os.path.join(src_dir, 'entities'))
sys.path.insert(0, os.path.join(src_dir, 'world'))
sys.path.insert(0, os.path.join(src_dir, 'systems'))

import pygame
from settings import *
from level import Level

def test_map_village_loading():
    """Test ob Map_Village korrekt lädt und der Spieler richtig spawnt"""
    print("🧪 Teste Map_Village Loading...")
    
    # Pygame initialisieren
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Map_Village Test")
    
    try:
        # Level erstellen - das löst load_map() aus
        print("\n📋 Erstelle Level...")
        level = Level(screen)
        
        # Map-Info ausgeben
        if level.map_loader and level.map_loader.tmx_data:
            map_width = level.map_loader.tmx_data.width * level.map_loader.tmx_data.tilewidth
            map_height = level.map_loader.tmx_data.height * level.map_loader.tmx_data.tileheight
            print(f"📐 Map-Dimensionen: {map_width}x{map_height} Pixel")
            print(f"🗺️ Map-Größe: {level.map_loader.tmx_data.width}x{level.map_loader.tmx_data.height} Tiles")
            
            # Spieler-Position ausgeben
            player_x = level.game_logic.player.rect.centerx
            player_y = level.game_logic.player.rect.centery
            print(f"🎯 Spieler-Position: ({player_x}, {player_y})")
            
            # Prüfe ob Position gültig ist
            if 0 <= player_x <= map_width and 0 <= player_y <= map_height:
                print("✅ Spieler-Position ist innerhalb der Map!")
            else:
                print("❌ Spieler-Position ist außerhalb der Map!")
        else:
            print("❌ Map konnte nicht geladen werden!")
            
    except Exception as e:
        print(f"❌ Fehler beim Test: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        pygame.quit()
        print("\n🏁 Test beendet.")

if __name__ == "__main__":
    test_map_village_loading()