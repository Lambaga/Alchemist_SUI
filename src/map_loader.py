# src/map_loader.py
import pygame
import pytmx
from config import Colors

class MapLoader:
    """
    Diese Klasse lädt eine TMX-Karte aus Tiled und stellt sie dar.
    Sie extrahiert auch Kollisionsobjekte aus einer speziellen Objektebene.
    """
    def __init__(self, filename):
        """
        Lädt die Kartendaten aus der angegebenen TMX-Datei.
        """
        try:
            self.tmx_data = pytmx.load_pygame(filename, pixelalpha=True)
            print(f"✅ TMX-Datei geladen: {filename}")
        except FileNotFoundError:
            print(f"FEHLER: Kartendatei nicht gefunden: {filename}")
            # Erstelle ein leeres tmx_data-Objekt, um Abstürze zu vermeiden
            self.tmx_data = None
            self.width = 0
            self.height = 0
            self.collision_objects = []
            return
        except Exception as e:
            print(f"WARNUNG: Tileset-Fehler ignoriert: {e}")
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
        Zeichnet alle sichtbaren Kachelebenen der Karte auf die angegebene Oberfläche.
        Falls Tileset-Grafiken fehlen, werden Platzhalter-Rechtecke gezeichnet.
        """
        if not self.tmx_data:
            return # Nichts zu zeichnen, wenn die Karte nicht geladen wurde

        for layer in self.tmx_data.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer):
                for x, y, gid in layer:
                    if gid:  # Nur zeichnen wenn es eine Kachel gibt
                        tile_image = self.tmx_data.get_tile_image_by_gid(gid)
                        tile_rect = pygame.Rect(x * self.tmx_data.tilewidth, 
                                                y * self.tmx_data.tileheight, 
                                                self.tmx_data.tilewidth, 
                                                self.tmx_data.tileheight)
                        transformed_rect = camera.apply_rect(tile_rect)
                        
                        if tile_image:
                            # Normale Tileset-Grafik verwenden
                            surface.blit(tile_image, transformed_rect)
                        else:
                            # Fallback: Platzhalter-Rechteck zeichnen
                            color = self.get_placeholder_color(gid)
                            pygame.draw.rect(surface, color, transformed_rect)
                            # Optional: Rahmen für bessere Sichtbarkeit
                            pygame.draw.rect(surface, (0, 0, 0), transformed_rect, 1)
    
    def get_placeholder_color(self, gid):
        """
        Gibt eine Platzhalter-Farbe basierend auf der Kachel-ID zurück.
        """
        # Verschiedene Farben für verschiedene Kachel-IDs
        colors = [
            (139, 69, 19),   # Braun - Boden
            (34, 139, 34),   # Grün - Gras  
            (128, 128, 128), # Grau - Stein
            (160, 82, 45),   # Sandbraun
            (0, 100, 0),     # Dunkelgrün
            (105, 105, 105), # Dunkelgrau
            (222, 184, 135), # Beige
            (85, 107, 47),   # Olivgrün
        ]
        return colors[gid % len(colors)]

    def build_map(self):
        """
        Erstellt Kollisionsobjekte aus einer speziellen Ebene namens 'Collision'.
        Unterstützt sowohl Objektebenen als auch Tile-Ebenen.
        """
        if not self.tmx_data:
            return

        print("Baue Kollisionsobjekte aus der Karte...")
        try:
            # Suche nach einer Ebene mit dem Namen 'Collision'
            collision_layer = self.tmx_data.get_layer_by_name('Collision')
            
            if isinstance(collision_layer, pytmx.TiledObjectGroup):
                # Objektebene: Gehe durch alle Objekte (Rechtecke)
                for obj in collision_layer:
                    wall_rect = pygame.Rect(obj.x, obj.y, obj.width, obj.height)
                    self.collision_objects.append(wall_rect)
                print(f"✅ {len(self.collision_objects)} Kollisionsobjekte aus Objektebene 'Collision' geladen.")
                
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
                print(f"✅ {len(self.collision_objects)} Kollisionsobjekte aus Tile-Ebene 'Collision' geladen.")
            else:
                print("WARNUNG: Ebene 'Collision' ist weder eine Objekt- noch eine Tile-Ebene.")

        except ValueError:
            print("WARNUNG: Keine Ebene namens 'Collision' in der TMX-Datei gefunden.")

