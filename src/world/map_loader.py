# -*- coding: utf-8 -*-
# src/map_loader.py
import os
import pygame
import pytmx
from config import Colors
from asset_manager import AssetManager

class MapLoader:
    """
    Diese Klasse lädt eine TMX-Karte aus Tiled und stellt sie dar.
    Sie extrahiert auch Kollisionsobjekte aus einer spez                    # Versuche Tile-Image zu laden
                    try:
                        tile_image = self.tmx_data.get_tile_image_by_gid(gid)
                        if not tile_image:
                            # Fallback: Versuche Tile direkt aus Bilddatei zu laden
                            tile_image = self.get_tile_image_direct(gid)

                        if tile_image:
                            surface.blit(tile_image, (tile_x, tile_y))
                        else:
                            # Debug: Erster Fehler - tile_image ist None
                            if not hasattr(layer, '_tile_none_logged'):
                                print(f"� Layer {layer.name}: GID {gid} gibt tile_image=None zurück")
                                print(f"   Erstes Tileset: {self.tmx_data.tilesets[0].name if self.tmx_data.tilesets else 'Keine Tilesets'}")
                                if self.tmx_data.tilesets:
                                    ts = self.tmx_data.tilesets[0]
                                    print(f"   GID-Range: {ts.firstgid} bis {ts.firstgid + ts.tilecount - 1}")
                                layer._tile_none_logged = Truebene.
    """
    def __init__(self, filename):
        """
        Lädt die Kartendaten aus der angegebenen TMX-Datei.
        """
        # Initialize AssetManager
        self.asset_manager = AssetManager()
        
        # Cache für geladene Tile-Images (Performance-Optimierung)
        # BEHOBEN: Verwende String-Keys statt GID-Keys um Tileset-Konflikte zu vermeiden
        self.tile_cache = {}
        
        # Speichere ursprüngliches Arbeitsverzeichnis
        original_cwd = os.getcwd()
        
        try:
            # Verwende absoluten Pfad für TMX-Datei - pytmx kann relative Pfade in TSX-Dateien besser auflösen
            if os.path.isabs(filename):
                tmx_filename = filename
                maps_dir = os.path.dirname(filename)
            else:
                tmx_filename = os.path.abspath(filename)
                maps_dir = os.path.dirname(tmx_filename)
            
            print(f"🗂️ Maps-Verzeichnis: {maps_dir}")
            print(f"📁 Lade TMX: {tmx_filename}")
            
            # Speichere aktuelles Arbeitsverzeichnis
            original_cwd = os.getcwd()
            
            # Wechsle temporär ins maps-Verzeichnis für bessere relative Pfad-Auflösung
            if maps_dir and os.path.exists(maps_dir):
                os.chdir(maps_dir)
                print(f"✅ Arbeitsverzeichnis gewechselt zu: {maps_dir}")
            else:
                print(f"⚠️ Maps-Verzeichnis nicht gefunden: {maps_dir}")
            
            # Lade TMX-Datei mit absolutem Pfad
            self.tmx_data = pytmx.load_pygame(tmx_filename, pixelalpha=True)
            print("✅ TMX-Datei geladen: {}".format(tmx_filename))
            
            # **CRITICAL FIX**: PyTMX lädt externe TSX falsch - manuelle Lösung
            print("🔧 MANUELLES TSX-LOADING: Korrigiere externe Tileset-Referenzen...")
            self._load_external_tilesets_manually(tmx_filename)
            
            # Debug: Prüfe Tilesets
            if hasattr(self.tmx_data, 'tilesets'):
                print("🎨 Verfügbare Tilesets:")
                for i, tileset in enumerate(self.tmx_data.tilesets):
                    source = getattr(tileset, 'source', 'embedded')
                    first_gid = getattr(tileset, 'firstgid', 'unknown')
                    print(f"  {i+1}. {tileset.name} (GID: {first_gid}, Source: {source})")

                    # Prüfe ob Tileset-Bilder geladen wurden und ob die Bilddatei existiert / geladen werden kann
                    if hasattr(tileset, 'image') and getattr(tileset.image, 'source', None):
                        img_source = getattr(tileset.image, 'source')
                        # Versuche verschiedene Pfad-Kombinationen
                        possible_paths = [
                            img_source,  # Relativer Pfad aus TSX
                            os.path.join(maps_dir, img_source),  # Relativer Pfad vom maps-Verzeichnis
                            os.path.join(os.getcwd(), img_source),  # Relativer Pfad vom aktuellen Arbeitsverzeichnis
                            os.path.abspath(img_source)  # Absoluter Pfad
                        ]
                        
                        img_path = None
                        for path in possible_paths:
                            if os.path.exists(path):
                                img_path = path
                                break
                        
                        if img_path:
                            print(f"     Image: {img_source} => Path: {img_path} (exists: True)")
                            
                            # Versuche, das Bild mit pygame zu laden
                            try:
                                surf = pygame.image.load(img_path).convert_alpha()
                                print(f"       ✅ pygame: Bild geladen, Size={surf.get_size()}")
                            except Exception as e:
                                print(f"       ❌ pygame: FEHLER beim Laden: {type(e).__name__}: {e}")
                        else:
                            print(f"     ❌ Image: {img_source} => KEINE der Pfad-Kombinationen gefunden:")
                            for path in possible_paths:
                                print(f"         - {path} (exists: {os.path.exists(path)})")
                    else:
                        img_source = getattr(tileset, 'image', None)
                        print(f"     ⚠️ Image: no source (tileset.image={img_source})")
                        
                    # **BESSERE LÖSUNG**: Prüfe ob tileset.source (TSX-Pfad) existiert
                    print(f"     🔧 DEBUG: tileset.source = '{getattr(tileset, 'source', 'None')}' | tileset.image = {hasattr(tileset, 'image')}")
                    
                    # Wenn das Tileset eine externe TSX-Quelle hat aber kein Bild geladen wurde
                    if hasattr(tileset, 'source') and tileset.source and (not hasattr(tileset, 'image') or not tileset.image):
                        tsx_source = tileset.source
                        print(f"     🔧 MANUAL LOAD: Lade PNG-Pfad aus TSX '{tsx_source}'...")
                        
                        # Finde die TSX-Datei  
                        tsx_paths = [
                            tsx_source,  # Relativer Pfad
                            os.path.join(maps_dir, tsx_source),  # maps-Verzeichnis
                            os.path.join(os.getcwd(), tsx_source),  # Aktuelles Verzeichnis
                        ]
                        
                        tsx_path = None
                        for path in tsx_paths:
                            if os.path.exists(path):
                                tsx_path = path
                                break
                        
                        if tsx_path:
                            try:
                                # Parse die TSX-Datei um den PNG-Pfad zu finden
                                import xml.etree.ElementTree as ET
                                tree = ET.parse(tsx_path)
                                root = tree.getroot()
                                
                                # Finde das <image source="..."/> Element
                                image_elem = root.find('image')
                                if image_elem is not None:
                                    png_source = image_elem.get('source')
                                    print(f"       📄 TSX parsed: PNG-Datei = '{png_source}'")
                                    
                                    # Versuche verschiedene Pfad-Kombinationen für PNG (relativ zur TSX-Datei)
                                    tsx_dir = os.path.dirname(tsx_path)
                                    png_paths = [
                                        os.path.join(tsx_dir, png_source),  # Relativ zur TSX-Datei
                                        os.path.join(maps_dir, png_source),  # maps-Verzeichnis
                                        png_source,  # Direkter Pfad
                                    ]
                                    
                                    png_path = None
                                    for path in png_paths:
                                        if os.path.exists(path):
                                            png_path = path
                                            break
                                    
                                    if png_path:
                                        # Lade das PNG und setze es ins Tileset
                                        loaded_surf = pygame.image.load(png_path).convert_alpha()
                                        print(f"       ✅ Manual PNG Load: {png_source} => {loaded_surf.get_size()}")
                                        
                                        # Erstelle ein Mock-Image-Objekt für das Tileset
                                        class MockImage:
                                            def __init__(self, surface, source):
                                                self.surface = surface
                                                self.source = source
                                                self.get_size = lambda: surface.get_size()
                                        
                                        tileset.image = MockImage(loaded_surf, png_source)
                                        print(f"       ✅ Tileset {tileset.name} Image erfolgreich nachgeladen!")
                                    else:
                                        print(f"       ❌ PNG '{png_source}' nicht gefunden in: {png_paths}")
                                else:
                                    print(f"       ❌ Kein <image> Element in TSX gefunden")
                                    
                            except Exception as e:
                                print(f"       ❌ TSX Parse FEHLER: {type(e).__name__}: {e}")
                        else:
                            print(f"       ❌ TSX nicht gefunden in: {tsx_paths}")
                    
                    # Wenn das Tileset bereits ein geladenes Bild hat (embedded oder bereits nachgeladen)
                    elif hasattr(tileset, 'image') and tileset.image and hasattr(tileset.image, 'source'):
                        img_source = tileset.image.source
                        print(f"     ✅ Bild bereits geladen: {img_source}")
                    else:
                        print(f"     ⚠️ Unbekannter Tileset-Status")
                        
                    # Zusätzliche Debug-Info für alle Tilesets
                    print(f"     📊 Tileset {tileset.name}: firstgid={tileset.firstgid}, tilecount={tileset.tilecount}, range={tileset.firstgid}-{tileset.firstgid + tileset.tilecount - 1}")
                    if hasattr(tileset, 'columns'):
                        print(f"         Columns: {tileset.columns}, TileSize: {tileset.tilewidth}x{tileset.tileheight}")
        
            # Debug: Zähle erfolgreich geladene Tilesets
            loaded_tilesets = 0
            for tileset in self.tmx_data.tilesets:
                if hasattr(tileset, 'image') and tileset.image:
                    loaded_tilesets += 1
            print(f"🎨 Tilesets-Status: {loaded_tilesets}/{len(self.tmx_data.tilesets)} erfolgreich geladen")
            if loaded_tilesets < len(self.tmx_data.tilesets):
                print(f"⚠️ {len(self.tmx_data.tilesets) - loaded_tilesets} Tilesets konnten nicht geladen werden!")
                
            # ZUSÄTZLICH: Analysiere GID-Ranges auf Überlappungen/Lücken
            print("🔍 GID-Range-Analyse:")
            sorted_tilesets = sorted(self.tmx_data.tilesets, key=lambda ts: ts.firstgid)
            for i, tileset in enumerate(sorted_tilesets):
                range_end = tileset.firstgid + tileset.tilecount - 1
                range_status = "✅" if hasattr(tileset, 'image') and tileset.image else "❌"
                print(f"  {range_status} {tileset.name}: GID {tileset.firstgid}-{range_end} ({tileset.tilecount} tiles)")
                
                # Prüfe auf Lücken/Überlappungen
                if i > 0:
                    prev_tileset = sorted_tilesets[i-1]
                    prev_end = prev_tileset.firstgid + prev_tileset.tilecount - 1
                    if prev_end + 1 != tileset.firstgid:
                        if prev_end >= tileset.firstgid:
                            print(f"    ⚠️ ÜBERLAPPUNG mit {prev_tileset.name}: {prev_end} >= {tileset.firstgid}")
                        else:
                            print(f"    ⚠️ LÜCKE nach {prev_tileset.name}: {prev_end+1} bis {tileset.firstgid-1} ({tileset.firstgid-prev_end-1} GIDs)")
                        
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
                if maps_dir:
                    tmx_filename = os.path.basename(filename)
                else:
                    tmx_filename = filename
                self.tmx_data = pytmx.load_pygame(tmx_filename, pixelalpha=True)
            except:
                print("❌ Map konnte gar nicht geladen werden")
                self.tmx_data = None
                self.width = 0
                self.height = 0
                self.collision_objects = []
                return
        finally:
            # Setze ursprüngliches Arbeitsverzeichnis zurück
            os.chdir(original_cwd)

    def _load_external_tilesets_manually(self, tmx_filename):
        """
        Lädt externe TSX-Dateien manuell, da PyTMX sie oft falsch lädt.
        KRITISCHER FIX für das terrain-map-v81.tsx Problem.
        """
        import xml.etree.ElementTree as ET
        
        tmx_dir = os.path.dirname(tmx_filename)
        print(f"🔧 Manuelles TSX-Loading aus: {tmx_dir}")
        
        # Parse TMX direkt um Tileset-Referenzen zu finden
        try:
            tree = ET.parse(tmx_filename)
            root = tree.getroot()
            
            # Finde externe Tileset-Referenzen
            external_tilesets = []
            for tileset_elem in root.findall("tileset"):
                firstgid = int(tileset_elem.get('firstgid', 0))
                source = tileset_elem.get('source')
                if source:
                    external_tilesets.append((firstgid, source))
            
            print(f"   Gefunden: {len(external_tilesets)} externe Tileset-Referenzen")
            
            # Lade jedes externe Tileset manuell
            for firstgid, tsx_source in external_tilesets:
                tsx_path = os.path.join(tmx_dir, tsx_source)
                print(f"   Lade: {tsx_source} (firstgid={firstgid})")
                
                if not os.path.exists(tsx_path):
                    print(f"   ❌ TSX nicht gefunden: {tsx_path}")
                    continue
                
                try:
                    # Parse TSX-Datei
                    tsx_tree = ET.parse(tsx_path)
                    tsx_root = tsx_tree.getroot()
                    
                    # Extrahiere Tileset-Infos
                    name = tsx_root.get('name', f'tileset_{firstgid}')
                    tilecount = int(tsx_root.get('tilecount', 0))
                    columns = int(tsx_root.get('columns', 16))
                    tilewidth = int(tsx_root.get('tilewidth', 32))
                    tileheight = int(tsx_root.get('tileheight', 32))
                    
                    # Finde das Image-Element
                    image_elem = tsx_root.find('image')
                    if image_elem is None:
                        print(f"   ❌ Kein <image> Element in {tsx_source}")
                        continue
                    
                    png_source = image_elem.get('source')
                    width = int(image_elem.get('width', 0))
                    height = int(image_elem.get('height', 0))
                    
                    print(f"     TSX-Info: {name}, {tilecount} tiles, {columns} cols, PNG: {png_source}")
                    
                    # Finde PNG-Datei
                    png_path = os.path.join(tmx_dir, png_source)
                    if not os.path.exists(png_path):
                        print(f"     ❌ PNG nicht gefunden: {png_path}")
                        continue
                    
                    # Lade PNG mit pygame
                    try:
                        png_surface = pygame.image.load(png_path).convert_alpha()
                        print(f"     ✅ PNG geladen: {png_surface.get_size()}")
                        
                        # Finde das entsprechende Tileset in tmx_data und setze das Bild
                        for tileset in self.tmx_data.tilesets:
                            if tileset.firstgid == firstgid:
                                # Erstelle MockImage
                                class MockImage:
                                    def __init__(self, surface, source):
                                        self.surface = surface
                                        self.source = source
                                        self.get_size = lambda: surface.get_size()
                                
                                tileset.image = MockImage(png_surface, png_source)
                                # Aktualisiere auch andere Attribute falls nötig
                                tileset.tilecount = tilecount
                                tileset.columns = columns
                                tileset.tilewidth = tilewidth
                                tileset.tileheight = tileheight
                                
                                print(f"     ✅ Tileset {name} erfolgreich korrigiert!")
                                break
                        else:
                            print(f"     ⚠️ Tileset mit firstgid={firstgid} nicht in tmx_data gefunden")
                    
                    except Exception as e:
                        print(f"     ❌ PNG-Load Fehler: {e}")
                
                except Exception as e:
                    print(f"   ❌ TSX-Parse Fehler {tsx_source}: {e}")
            
        except Exception as e:
            print(f"🔧 Manuelles TSX-Loading fehlgeschlagen: {e}")

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
        
        total_tiles_rendered = 0
        layers_with_tiles = 0
        
        # 1. Alle normalen Layer rendern (außer Foreground)
        for layer in self.tmx_data.visible_layers:
            if hasattr(layer, 'data') and layer.name.lower() not in ['foreground', 'front', 'overlay']:
                layer_tiles = self._render_tile_layer(layer, surface, camera)
                if layer_tiles > 0:
                    total_tiles_rendered += layer_tiles
                    layers_with_tiles += 1
        
        # Debug-Zusammenfassung nur einmal
        if not hasattr(self, '_render_summary_logged'):
            print(f"🎨 RENDER-ZUSAMMENFASSUNG: {total_tiles_rendered} Tiles in {layers_with_tiles} Layern")
            print(f"   Map-Größe: {self.tmx_data.width}x{self.tmx_data.height} Tiles ({self.width}x{self.height} Pixel)")
            self._render_summary_logged = True

    def render_foreground(self, surface, camera):
        """Rendert Foreground-Layer genau wie andere Tile-Layer"""
        if not self.foreground_layer:
            return
        
        # Nutze die gleiche Render-Methode wie für normale Layer
        self._render_tile_layer(self.foreground_layer, surface, camera)

    def get_tile_image_direct(self, gid):
        """
        Lädt Tile-Image direkt aus Bilddateien, wenn pytmx es nicht kann.
        Das ist ein Fallback für den Fall, dass pytmx Tileset-Bilder nicht lädt.
        PERFORMANCE-OPTIMIERT: Nutzt Caching um wiederholtes Laden zu vermeiden.
        BEHOBEN: Cache-Key-Konflikte, korrekte Column-Berechnung
        """
        if not self.tmx_data or gid == 0:
            return None

        # Finde das Tileset für diesen GID ZUERST
        target_tileset = None
        local_id = 0
        
        for tileset in self.tmx_data.tilesets:
            if tileset.firstgid <= gid < tileset.firstgid + tileset.tilecount:
                target_tileset = tileset
                local_id = gid - tileset.firstgid
                break
        
        if not target_tileset:
            return None

        # Cache das Ergebnis und gib es zurück
        cache_key = f"{target_tileset.name}_{local_id}"
        if cache_key in self.tile_cache:
            return self.tile_cache[cache_key]

        # ERWEITERT: Debug-Ausgabe für mehr Tiles
        debug_this_tile = len(self.tile_cache) < 50  # Erste 50 Tiles debuggen statt nur 10
        if debug_this_tile:
            print(f"🔧 DIRECT LOAD: Versuche GID {gid} direkt zu laden")
            print(f"   Gefunden in Tileset '{target_tileset.name}', local_id={local_id}")

        # Versuche, das Tileset-Bild zu laden
        tileset_surface = None
        
        # ERWEITERT: Prüfe ob wir das Bild bereits manuell geladen haben
        if hasattr(target_tileset, 'image') and target_tileset.image:
            if hasattr(target_tileset.image, 'surface'):
                # Verwende das bereits manuell geladene Bild (MockImage)
                tileset_surface = target_tileset.image.surface
                if debug_this_tile:
                    print(f"   Verwende MockImage: {tileset_surface.get_size()}")
            else:
                # Standard pytmx image (pygame Surface)
                tileset_surface = target_tileset.image
                if debug_this_tile:
                    print(f"   Verwende pytmx Surface: {type(tileset_surface)}")
        
        # Falls kein Bild verfügbar, versuche manuell zu laden
        if not tileset_surface:
            if debug_this_tile:
                print(f"   ❌ Kein Tileset-Bild verfügbar für {target_tileset.name}")
            self.tile_cache[cache_key] = None
            return None
        
        # Verarbeite das Tileset-Surface
        if tileset_surface and hasattr(tileset_surface, 'get_size'):
            # BEHOBEN: Korrekte Column-Berechnung aus TSX-Datei
            tiles_per_row = getattr(target_tileset, 'columns', 16)
            if tiles_per_row <= 0:  # Fallback falls columns = 0
                # Berechne aus Bildbreite und Tile-Breite
                img_width = tileset_surface.get_width()
                tiles_per_row = img_width // target_tileset.tilewidth
                if debug_this_tile:
                    print(f"   Berechnete Spalten: {tiles_per_row} (Bildbreite: {img_width}, Tile-Breite: {target_tileset.tilewidth})")
            elif debug_this_tile:
                print(f"   TSX-Spalten: {tiles_per_row}")
            
            # Berechne Position des Tiles im Tileset-Bild
            tile_x = (local_id % tiles_per_row) * target_tileset.tilewidth
            tile_y = (local_id // tiles_per_row) * target_tileset.tileheight

            # BEHOBEN: Verbesserte Bounds-Prüfung
            if (tile_x + target_tileset.tilewidth <= tileset_surface.get_width() and 
                tile_y + target_tileset.tileheight <= tileset_surface.get_height()):
                
                # Schneide das Tile aus dem Tileset-Bild aus
                tile_surface = pygame.Surface((target_tileset.tilewidth, target_tileset.tileheight), pygame.SRCALPHA)
                tile_surface.blit(tileset_surface, (0, 0),
                                (tile_x, tile_y, target_tileset.tilewidth, target_tileset.tileheight))
                
                # WICHTIG: convert_alpha() anwenden für korrekte Transparenz
                tile_surface = tile_surface.convert_alpha()
                
                if debug_this_tile:
                    print(f"   ✅ Tile erfolgreich ausgeschnitten! Position: ({tile_x}, {tile_y})")
                
                # Cache das Ergebnis und gib es zurück
                self.tile_cache[cache_key] = tile_surface
                return tile_surface
            else:
                if debug_this_tile or True:  # IMMER loggen wenn Bounds überschritten werden
                    print(f"   ❌ Tile außerhalb der Bildgrenzen: ({tile_x}, {tile_y}) + ({target_tileset.tilewidth}, {target_tileset.tileheight}) > {tileset_surface.get_size()}")
                    print(f"      GID {gid}, local_id {local_id}, tiles_per_row {tiles_per_row}")
        
        # Cache leeres Ergebnis
        self.tile_cache[cache_key] = None
        if debug_this_tile:
            print(f"   ❌ Konnte GID {gid} nicht laden")
        return None

    def _render_tile_layer(self, layer, surface, camera):
        """Rendert einen einzelnen Tile-Layer mit Debug-Informationen"""
        if not layer or not hasattr(layer, 'data'):
            return
        
        # Debug: Prüfe Layer-Daten (erweitert)
        total_tiles = 0
        non_empty_tiles = 0
        sample_gids = []
        
        # Prüfe größeren Bereich: 10x10 statt 5x5
        for y in range(min(10, layer.height)):
            for x in range(min(10, layer.width)):
                gid = layer.data[y][x]
                total_tiles += 1
                if gid != 0:
                    non_empty_tiles += 1
                    sample_gids.append(gid)
        
        # Zusätzlich: Prüfe mittleren Bereich der Map
        if non_empty_tiles == 0 and layer.height > 20 and layer.width > 20:
            mid_y = layer.height // 2
            mid_x = layer.width // 2
            mid_non_empty = 0
            
            for y in range(max(0, mid_y-5), min(layer.height, mid_y+5)):
                for x in range(max(0, mid_x-5), min(layer.width, mid_x+5)):
                    gid = layer.data[y][x]
                    if gid != 0:
                        mid_non_empty += 1
                        sample_gids.append(gid)
            
            if mid_non_empty > 0 and not hasattr(layer, '_mid_debug_logged'):
                print(f"🎯 Layer {layer.name} (Mitte): {mid_non_empty} nicht-leere Tiles gefunden!")
                layer._mid_debug_logged = True

        # Debug-Ausgabe nur einmal pro Layer
        if not hasattr(layer, '_debug_logged'):
            print(f"🔍 Layer {layer.name}: {non_empty_tiles}/{total_tiles} nicht-leere Tiles (Sample: {sample_gids[:5]})")
            layer._debug_logged = True
        
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
        
        tiles_rendered = 0
        
        # NOTFALL-MODUS: Test-Pattern deaktiviert (da Tilesets jetzt funktionieren)
        # if non_empty_tiles == 0:
        #     for y in range(start_y, end_y):
        #         for x in range(start_x, end_x):
        #             if (x + y) % 10 == 0:  # Jeder 10. Tile
        #                 tile_x = x * tile_width - camera.camera_rect.x
        #                 tile_y = y * tile_height - camera.camera_rect.y
        #                 
        #                 # Test-Farbe basierend auf Layer-Name
        #                 if 'Trn' in layer.name:
        #                     color = (100, 200, 100)  # Grün für Terrain
        #                 elif 'Bldg' in layer.name:
        #                     color = (200, 100, 100)  # Rot für Gebäude
        #                 else:
        #                     color = (100, 100, 200)  # Blau für Rest
        #                     
        #                 pygame.draw.rect(surface, color, (tile_x, tile_y, tile_width, tile_height))
        #                 pygame.draw.rect(surface, (255, 255, 255), (tile_x, tile_y, tile_width, tile_height), 1)
        #                 tiles_rendered += 1
        if False:  # Test-Pattern komplett deaktiviert
            pass
        else:
            # Normale Tile-Rendering
            for y in range(start_y, end_y):
                for x in range(start_x, end_x):
                    gid = layer.data[y][x]
                    if gid == 0:
                        continue
                    
                    tiles_rendered += 1
                    tile_x = x * tile_width - camera.camera_rect.x
                    tile_y = y * tile_height - camera.camera_rect.y
                    
                    # Versuche Tile-Image zu laden
                    try:
                        tile_image = self.tmx_data.get_tile_image_by_gid(gid)
                        if not tile_image:
                            # Fallback: Versuche Tile direkt aus Bilddatei zu laden
                            tile_image = self.get_tile_image_direct(gid)
                        if tile_image:
                            surface.blit(tile_image, (tile_x, tile_y))
                        else:
                            # Debug: Erweiterte Fehlerdiagnose für fehlende Tiles
                            if not hasattr(layer, '_tile_none_logged'):
                                print(f"❌ Layer {layer.name}: GID {gid} gibt tile_image=None zurück")
                                print(f"   Erstes Tileset: {self.tmx_data.tilesets[0].name if self.tmx_data.tilesets else 'Keine Tilesets'}")
                                if self.tmx_data.tilesets:
                                    ts = self.tmx_data.tilesets[0]
                                    print(f"   GID-Range: {ts.firstgid} bis {ts.firstgid + ts.tilecount - 1}")
                                layer._tile_none_logged = True
                            
                            # ERWEITERT: Detaillierte GID-Analyse für fehlende Tiles
                            if not hasattr(layer, '_missing_gids'):
                                layer._missing_gids = set()
                            
                            if gid not in layer._missing_gids and len(layer._missing_gids) < 20:  # Erste 20 fehlende GIDs
                                layer._missing_gids.add(gid)
                                # Analysiere warum dieses GID fehlt
                                found_tileset = None
                                for ts in self.tmx_data.tilesets:
                                    if ts.firstgid <= gid < ts.firstgid + ts.tilecount:
                                        found_tileset = ts
                                        break
                                
                                if found_tileset:
                                    local_id = gid - found_tileset.firstgid
                                    print(f"🔍 Fehlender Tile - GID {gid}: Tileset '{found_tileset.name}', local_id={local_id}")
                                    
                                    # ERWEITERTE DIAGNOSE
                                    if hasattr(found_tileset, 'image') and found_tileset.image:
                                        if hasattr(found_tileset.image, 'surface'):
                                            surf = found_tileset.image.surface
                                            print(f"   MockImage verfügbar: {surf.get_size()}, Columns: {getattr(found_tileset, 'columns', 'unknown')}")
                                            
                                            # Prüfe ob local_id innerhalb der erwarteten Grenzen liegt
                                            max_tiles_in_surface = (surf.get_width() // found_tileset.tilewidth) * (surf.get_height() // found_tileset.tileheight)
                                            if local_id >= max_tiles_in_surface:
                                                print(f"   ❌ local_id {local_id} > max_tiles {max_tiles_in_surface} in Surface!")
                                            else:
                                                print(f"   ✅ local_id {local_id} < max_tiles {max_tiles_in_surface} - sollte funktionieren!")
                                                
                                        else:
                                            print(f"   PyTMX Image verfügbar: {type(found_tileset.image)}")
                                        
                                        # Prüfe Cache
                                        cache_key = f"{found_tileset.name}_{local_id}"
                                        if cache_key in self.tile_cache:
                                            cached_result = self.tile_cache[cache_key]
                                            print(f"   Cache-Inhalt: {type(cached_result)} ({cached_result is not None})")
                                        else:
                                            print(f"   ❌ Nicht im Cache: '{cache_key}'")
                                            
                                            # ZUSÄTZLICH: Versuche das Tile JETZT direkt zu laden
                                            print(f"   🔧 Versuche direktes Laden für GID {gid}...")
                                            direct_tile = self.get_tile_image_direct(gid)
                                            if direct_tile:
                                                print(f"   ✅ Direktes Laden erfolgreich: {direct_tile.get_size()}")
                                            else:
                                                print(f"   ❌ Direktes Laden fehlgeschlagen!")
                                    else:
                                        print(f"   ❌ Kein Tileset-Bild verfügbar!")
                                else:
                                    print(f"🔍 Fehlender Tile - GID {gid}: ❌ Kein zuständiges Tileset gefunden!")
                            
                            # Fallback: Bunte Rechtecke für fehlende Tiles (DEAKTIVIERT)
                            # color = self.get_placeholder_color(gid)
                            # pygame.draw.rect(surface, color, (tile_x, tile_y, tile_width, tile_height))
                            pass  # Keine Platzhalter mehr zeichnen
                    except Exception as e:
                        # Debug: Exception Details
                        if not hasattr(layer, '_exception_logged'):
                            print(f"❌ Tile-Exception Layer {layer.name}: {type(e).__name__}: {e}")
                            layer._exception_logged = True
                        
                        # Fallback: Bunte Rechtecke für fehlende Tiles (DEAKTIVIERT)
                        # color = self.get_placeholder_color(gid)
                        # pygame.draw.rect(surface, color, (tile_x, tile_y, tile_width, tile_height))
                        pass  # Keine Platzhalter mehr zeichnen
        
        # Ergebnis-Log mit detaillierter Tile-Statistik
        if tiles_rendered > 0 and not hasattr(layer, '_render_logged'):
            print(f"  ✅ Layer {layer.name}: {tiles_rendered} Tiles gerendert")
            
            # ERWEITERT: Zeige GID-Verteilung für diesen Layer
            if hasattr(layer, '_missing_gids') and layer._missing_gids:
                print(f"    ❌ Fehlende GIDs: {sorted(list(layer._missing_gids))}")
            
            layer._render_logged = True
        elif tiles_rendered == 0 and not hasattr(layer, '_empty_logged'):
            print(f"  ⚠️ Layer {layer.name}: Keine Tiles gerendert (leer oder außerhalb Sichtbereich)")
            layer._empty_logged = True
        
        # ERWEITERT: Rückgabe der Anzahl gerenderter Tiles
        return tiles_rendered

    def get_placeholder_color(self, gid):
        """
        Gibt eine Platzhalter-Farbe basierend auf der Kachel-ID zurück.
        BEHOBEN: Reduzierte Debug-Ausgabe und bessere Fehlerdiagnose
        """
        # Debug: Log dass Fallback-Farben verwendet werden (nur einmal pro GID-Bereich)
        gid_range = gid // 100 * 100  # Gruppiere GIDs in 100er-Bereiche
        fallback_key = f"fallback_{gid_range}"
        
        if not hasattr(self, '_fallback_logged'):
            self._fallback_logged = set()
        
        if fallback_key not in self._fallback_logged:
            print(f"🟦 FALLBACK: Platzhalter-Farben für GID-Bereich {gid_range}-{gid_range + 99}")
            print(f"🔍 Debugging: Erstes GID {gid} in diesem Bereich verwendet Fallback")
            
            # Prüfe warum Fallback verwendet wird
            if self.tmx_data and self.tmx_data.tilesets:
                for ts in self.tmx_data.tilesets:
                    if ts.firstgid <= gid < ts.firstgid + ts.tilecount:
                        print(f"   Zuständiges Tileset: {ts.name} (GID {ts.firstgid}-{ts.firstgid + ts.tilecount - 1})")
                        if hasattr(ts, 'image') and ts.image:
                            if hasattr(ts.image, 'surface'):
                                print(f"     MockImage verfügbar: {ts.image.surface.get_size()}")
                            else:
                                print(f"     PyTMX Image: {type(ts.image)}")
                        else:
                            print(f"     ❌ KEIN BILD GELADEN!")
                        break
            else:
                print("   ❌ KEINE TILESETS GEFUNDEN!")
            
            self._fallback_logged.add(fallback_key)
        
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

