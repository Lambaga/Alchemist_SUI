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
        self.foreground_layer = None  # Initialisiere das Attribut, um AttributeError zu vermeiden
        
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
        self.depth_objects = []
        self.foreground_tiles = []  # NEU: Für Foreground-Tiles
        
        self.build_map()
        self.load_depth_objects_from_map()
        self.extract_foreground_layer()  # NEU: Lade Foreground-Layer
    
    def extract_foreground_layer(self):
        """Extrahiert den Foreground-Tile-Layer"""
        if not self.tmx_data:
            return
        
        self.foreground_layer = None
        
        for layer in self.tmx_data.visible_layers:
            # Suche nach Foreground/Front Layer
            if hasattr(layer, 'data') and layer.name.lower() in ['foreground', 'front', 'overlay']:
                self.foreground_layer = layer
                print(f"🎭 Foreground-Layer gefunden: {layer.name}")
                break
        
        if not self.foreground_layer:
            print("⚠️ Kein Foreground-Layer gefunden")
    
    def render(self, surface, camera):
        """Rendert alle Layer inklusive Foreground in der richtigen Reihenfolge"""
        if not self.tmx_data:
            return
        
        # 1. Alle normalen Layer rendern (außer Foreground)
        for layer in self.tmx_data.visible_layers:
            if hasattr(layer, 'data') and layer.name.lower() not in ['foreground', 'front', 'overlay']:
                self._render_tile_layer(layer, surface, camera)
    
    def render_foreground(self, surface, camera):
        """Rendert Foreground-Layer genau wie andere Tile-Layer"""
        if not self.foreground_layer:
            return
        
        # Nutze die gleiche Render-Methode wie für normale Layer
        self._render_tile_layer(self.foreground_layer, surface, camera)

    def _render_tile_layer(self, layer, surface, camera):
        """Rendert einen einzelnen Tile-Layer ohne Qualitätsverlust"""
        if not layer or not hasattr(layer, 'data'):
            return
        
        # Sichtbarer Bereich
        screen_rect = pygame.Rect(
            camera.camera_rect.x, camera.camera_rect.y,
            surface.get_width(), surface.get_height()
        )
        
        tile_width = self.tmx_data.tilewidth
        tile_height = self.tmx_data.tileheight
        
        start_x = max(0, screen_rect.left // tile_width)
        start_y = max(0, screen_rect.top // tile_height)
        end_x = min(layer.width, (screen_rect.right // tile_width) + 1)
        end_y = min(layer.height, (screen_rect.bottom // tile_height) + 1)
        
        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                gid = layer.data[y][x]
                if gid == 0:
                    continue
                
                tile_x = x * tile_width - camera.camera_rect.x
                tile_y = y * tile_height - camera.camera_rect.y
                
                # Original TMX-Tile-Image verwenden (keine Skalierung!)
                try:
                    tile_image = self.tmx_data.get_tile_image_by_gid(gid)
                    if tile_image:
                        surface.blit(tile_image, (tile_x, tile_y))
                    else:
                        # Fallback
                        color = self.get_placeholder_color(gid)
                        pygame.draw.rect(surface, color, (tile_x, tile_y, tile_width, tile_height))
                except:
                    # Fallback
                    color = self.get_placeholder_color(gid)
                    pygame.draw.rect(surface, color, (tile_x, tile_y, tile_width, tile_height))

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

    def load_depth_objects_from_map(self):
        """Lädt Objekte mit Depth-Information aus der Tiled-Map"""
        if not self.tmx_data:
            return
        
        for layer in self.tmx_data.visible_layers:
            if hasattr(layer, 'objects') and layer.name.lower() in ['decoration', 'objects', 'depth_objects']:
                for obj in layer.objects:
                    if obj.name:
                        depth_obj = {
                            'rect': pygame.Rect(obj.x, obj.y, obj.width, obj.height),
                            'name': obj.name,
                            'type': getattr(obj, 'type', 'decoration'),
                            'y_bottom': obj.y + obj.height,  # Wichtig für Sorting!
                            'depth_layer': getattr(obj, 'depth_layer', 'auto'),  # Custom Property
                            'image_path': getattr(obj, 'image_path', None),  # Optional: Pfad zu Sprite
                            'color': self._get_object_color(obj.name),  # Fallback-Farbe
                            'properties': dict(obj.properties) if hasattr(obj, 'properties') else {}
                        }
                        self.depth_objects.append(depth_obj)
                        print(f"🎨 Depth-Objekt geladen: {obj.name} bei ({obj.x}, {obj.y}) - Y-Bottom: {depth_obj['y_bottom']}")
    
    def _get_object_color(self, obj_name):
        """Gibt Fallback-Farben für verschiedene Objekttypen zurück"""
        color_map = {
            'tree': (34, 139, 34),      # Grün
            'rock': (105, 105, 105),    # Grau
            'building': (139, 69, 19),   # Braun
            'fence': (160, 82, 45),      # Saddlbraun
            'bush': (0, 100, 0),        # Dunkelgrün
        }
        
        for key, color in color_map.items():
            if key.lower() in obj_name.lower():
                return color
        
        return (200, 200, 200)  # Standard-Grau

