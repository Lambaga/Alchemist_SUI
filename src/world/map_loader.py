# -*- coding: utf-8 -*-
# src/map_loader.py
import pygame
import pytmx
from config import Colors
from asset_manager import AssetManager

class MapLoader:
    """
    Diese Klasse lädt eine TMX-Karte aus Tiled und stellt sie dar.
    Sie extrahiert auch Kollisionsobjekte aus einer speziellen Objektebene.
    """
    def __init__(self, filename):
        """
        Lädt die Kartendaten aus der angegebenen TMX-Datei.
        """
        # Initialize AssetManager
        self.asset_manager = AssetManager()
        
        try:
            self.tmx_data = pytmx.load_pygame(filename, pixelalpha=True)
            print("✅ TMX-Datei geladen: {}".format(filename))
        except FileNotFoundError:
            print("FEHLER: Kartendatei nicht gefunden: {}".format(filename))
            # Erstelle ein leeres tmx_data-Objekt, um Abstürze zu vermeiden
            self.tmx_data = None
            self.width = 0
            self.height = 0
            self.collision_objects = []
            return
        except Exception as e:
            print("WARNUNG: Tileset-Fehler ignoriert: {}".format(e))
            print("🎨 Versuche trotzdem zu laden...")
            # Versuche trotzdem zu laden, auch wenn Tilesets fehlen
            try:
                self.tmx_data = pytmx.load_pygame(filename, pixelalpha=True)
            except:
                print("❌ Map konnte gar nicht geladen werden")
                self.tmx_data = None
                self.width = 0
                self.height = 0
                self.collision_objects = []
                return

        if self.tmx_data:
            self.width = self.tmx_data.width * self.tmx_data.tilewidth
            self.height = self.tmx_data.height * self.tmx_data.tileheight
        else:
            self.width = 0
            self.height = 0
        
        self.collision_objects = []
        self.build_map()

    def render(self, surface, camera):
        """
        🚀 RPi4-Optimiert: Zeichnet nur sichtbare Tiles im Kamera-Viewport (Tile Culling).
        Falls Tileset-Grafiken fehlen, werden Platzhalter-Rechtecke gezeichnet.
        """
        if not self.tmx_data:
            return # Nichts zu zeichnen, wenn die Karte nicht geladen wurde

        # 🚀 TILE CULLING: Berechne sichtbaren Tile-Bereich aus Kamera-Viewport
        screen_width = surface.get_width()
        screen_height = surface.get_height()
        
        # Kamera-Position in Weltkoordinaten
        camera_x = camera.camera_rect.x
        camera_y = camera.camera_rect.y
        
        # Erweitere den sichtbaren Bereich um 1 Tile als Puffer (verhindert Pop-in)
        tile_buffer = 1
        
        # Berechne Tile-Indizes für sichtbaren Bereich
        start_x = max(0, int(camera_x // self.tmx_data.tilewidth) - tile_buffer)
        end_x = min(self.tmx_data.width, int((camera_x + screen_width) // self.tmx_data.tilewidth) + tile_buffer + 1)
        start_y = max(0, int(camera_y // self.tmx_data.tileheight) - tile_buffer)
        end_y = min(self.tmx_data.height, int((camera_y + screen_height) // self.tmx_data.tileheight) + tile_buffer + 1)
        
        # Debug-Info (nur bei ersten paar Frames)
        debug_culling = hasattr(self, '_debug_frame_count')
        if not debug_culling:
            self._debug_frame_count = 0
        
        if self._debug_frame_count < 3:  # Nur erste 3 Frames
            total_tiles = self.tmx_data.width * self.tmx_data.height
            visible_tiles = (end_x - start_x) * (end_y - start_y)
            print(f"🚀 Tile Culling: {visible_tiles}/{total_tiles} Tiles sichtbar ({visible_tiles/total_tiles*100:.1f}%)")
            self._debug_frame_count += 1

        for layer in self.tmx_data.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer):
                # 🚀 Nur sichtbare Tiles iterieren (statt alle Tiles der Map)
                for x in range(start_x, end_x):
                    for y in range(start_y, end_y):
                        gid = layer.data[y][x] if y < len(layer.data) and x < len(layer.data[y]) else 0
                        
                        if gid:  # Nur zeichnen wenn es eine Kachel gibt
                            tile_image = self.tmx_data.get_tile_image_by_gid(gid)
                            tile_rect = pygame.Rect(x * self.tmx_data.tilewidth, 
                                                    y * self.tmx_data.tileheight, 
                                                    self.tmx_data.tilewidth, 
                                                    self.tmx_data.tileheight)
                            transformed_rect = camera.apply_rect(tile_rect)
                            
                            if tile_image:
                                # Performance-Optimierung: Nutze gecachte Skalierung für Tiles
                                target_size = (
                                    int(self.tmx_data.tilewidth * camera.zoom_factor),
                                    int(self.tmx_data.tileheight * camera.zoom_factor)
                                )
                                scaled_image = self.asset_manager.get_scaled_sprite(tile_image, target_size)
                                surface.blit(scaled_image, (transformed_rect.x, transformed_rect.y))
                            else:
                                # Fallback: Platzhalter-Rechteck zeichnen (bereits durch apply_rect skaliert)
                                color = self.get_placeholder_color(gid)
                                pygame.draw.rect(surface, color, transformed_rect)
                                # Optional: Rahmen für bessere Sichtbarkeit
                                pygame.draw.rect(surface, (255, 255, 255), transformed_rect, max(1, int(camera.zoom_factor)))
    
    def get_placeholder_color(self, gid):
        """
        Gibt eine Platzhalter-Farbe basierend auf der Kachel-ID zurück.
        """
        # Hellere, kontrastreichere Farben für bessere Sichtbarkeit
        colors = [
            (200, 120, 60),   # Helles Braun - Boden
            (80, 200, 80),    # Helles Grün - Gras  
            (180, 180, 180),  # Helles Grau - Stein
            (240, 180, 100),  # Helles Sandbraun
            (60, 180, 60),    # Helles Grün
            (160, 160, 160),  # Hellgrau
            (255, 220, 180),  # Helles Beige
            (120, 160, 80),   # Helles Olivgrün
        ]
        return colors[gid % len(colors)]

    def build_map(self):
        """
        Erstellt Kollisionsobjekte aus einer speziellen Ebene namens 'Collision' oder 'Walls'.
        Unterstützt sowohl Objektebenen als auch Tile-Ebenen.
        """
        if not self.tmx_data:
            return

        print("Baue Kollisionsobjekte aus der Karte...")
        try:
            # Suche nach einer Ebene mit dem Namen 'Walls' oder 'Collision'
            collision_layer = None
            for layer_name in ['Walls', 'Collision', 'walls', 'collision', 'Enemy', 'enemy']:
                try:
                    collision_layer = self.tmx_data.get_layer_by_name(layer_name)
                    print(f"✅ Layer '{layer_name}' gefunden")
                    break
                except ValueError:
                    continue
            
            if not collision_layer:
                print("WARNUNG: Keine Ebene namens 'Walls' oder 'Collision' gefunden.")
                return
            
            if isinstance(collision_layer, pytmx.TiledObjectGroup):
                # Objektebene: Gehe durch alle Objekte (Rechtecke)
                for obj in collision_layer:
                    wall_rect = pygame.Rect(obj.x, obj.y, obj.width, obj.height)
                    self.collision_objects.append(wall_rect)
                print("✅ {} Kollisionsobjekte aus Objektebene '{}' geladen.".format(
                    len(self.collision_objects), collision_layer.name))
                
            elif isinstance(collision_layer, pytmx.TiledTileLayer):
                # Tile-Ebene: Gehe durch alle Tiles und erstelle Kollisionen für nicht-leere Tiles
                for x, y, gid in collision_layer:
                    if gid != 0:  # 0 = leere Kachel
                        # Berechne die Pixel-Position der Kachel
                        tile_x = x * self.tmx_data.tilewidth
                        tile_y = y * self.tmx_data.tileheight
                        wall_rect = pygame.Rect(tile_x, tile_y, 
                                              self.tmx_data.tilewidth, 
                                              self.tmx_data.tileheight)
                        self.collision_objects.append(wall_rect)
                print("✅ {} Kollisionsobjekte aus Tile-Ebene '{}' geladen.".format(
                    len(self.collision_objects), collision_layer.name))
            else:
                print("WARNUNG: Ebene '{}' ist weder eine Objekt- noch eine Tile-Ebene.".format(
                    collision_layer.name))

        except Exception as e:
            print("FEHLER beim Laden der Kollisionsobjekte: {}".format(e))

