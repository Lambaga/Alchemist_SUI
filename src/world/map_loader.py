# -*- coding: utf-8 -*-
# src/map_loader.py
import os
try:
    from core.settings import VERBOSE_LOGS
except Exception:
    VERBOSE_LOGS = False
import pygame
import pytmx
from config import Colors
from asset_manager import AssetManager
from typing import Optional

class MapLoader:
    """
    Lädt eine TMX-Karte (Tiled) und stellt Rendering-/Hilfsfunktionen bereit.
    Enthält Workarounds für externe TSX/Tileset-Bilder.
    """
    def __init__(self, filename):
        """Lädt die Kartendaten aus der angegebenen TMX-Datei."""
        self.asset_manager = AssetManager()
        self.foreground_layer = None
        self.tile_cache = {}

        # Chunk cache for tile rendering (huge speedup vs per-tile blits on RPi)
        self._layer_chunk_cache = {}
        self._layer_chunk_access = []  # LRU order
        self._chunk_size_tiles = 16
        # Max chunks is tuned by DisplayConfig (falls back to a safe default)
        self._max_cached_chunks = 80
        try:
            from config import DisplayConfig
            self._max_cached_chunks = int(DisplayConfig.get_optimized_settings().get('TILE_CACHE_SIZE', 80))
        except Exception:
            pass

        original_cwd = os.getcwd()
        maps_dir: Optional[str] = None
        try:
            # Absoluten TMX-Pfad bestimmen
            if os.path.isabs(filename):
                tmx_filename = filename
                maps_dir = os.path.dirname(filename)
            else:
                tmx_filename = os.path.abspath(filename)
                maps_dir = os.path.dirname(tmx_filename)

            if VERBOSE_LOGS:
                print(f"🗂️ Maps-Verzeichnis: {maps_dir}")
                print(f"📁 Lade TMX: {tmx_filename}")

            # Temporär ins Maps-Verzeichnis wechseln (relative TSX/PNG-Auflösung)
            if maps_dir and os.path.exists(maps_dir):
                os.chdir(maps_dir)
                if VERBOSE_LOGS:
                    print(f"✅ Arbeitsverzeichnis gewechselt zu: {maps_dir}")
            else:
                if VERBOSE_LOGS:
                    print(f"⚠️ Maps-Verzeichnis nicht gefunden: {maps_dir}")

            # TMX laden und Pfad merken
            self.tmx_data = pytmx.load_pygame(tmx_filename, pixelalpha=True)
            self.map_path = tmx_filename
            if VERBOSE_LOGS:
                print(f"✅ TMX-Datei geladen: {tmx_filename}")

            # Externe TSX manuell korrigieren
            if VERBOSE_LOGS:
                print("🔧 MANUELLES TSX-LOADING: Korrigiere externe Tileset-Referenzen...")
            self._load_external_tilesets_manually(tmx_filename)
        except FileNotFoundError:
            print(f"FEHLER: Kartendatei nicht gefunden: {filename}")
            self.tmx_data = None
            self.width = 0
            self.height = 0
            self.collision_objects = []
            return
        except Exception as e:
            print(f"WARNUNG: Tileset-Fehler ignoriert: {e}")
            print("🎨 Versuche trotzdem zu laden...")
            try:
                # Letzter Versuch: TMX relativ laden
                tmx_basename = os.path.basename(filename)
                self.tmx_data = pytmx.load_pygame(tmx_basename, pixelalpha=True)
            except Exception:
                print("❌ Map konnte gar nicht geladen werden")
                self.tmx_data = None
                self.width = 0
                self.height = 0
                self.collision_objects = []
                return
        finally:
            # Ursprüngliches Arbeitsverzeichnis wiederherstellen
            os.chdir(original_cwd)
            
            # Debug: Prüfe Tilesets
            if self.tmx_data is not None and hasattr(self.tmx_data, 'tilesets') and VERBOSE_LOGS:
                print("🎨 Verfügbare Tilesets:")
                for i, tileset in enumerate(self.tmx_data.tilesets):
                    source = getattr(tileset, 'source', 'embedded')
                    first_gid = getattr(tileset, 'firstgid', 'unknown')
                    if VERBOSE_LOGS:
                        print(f"  {i+1}. {tileset.name} (GID: {first_gid}, Source: {source})")

                    # Prüfe ob Tileset-Bilder geladen wurden und ob die Bilddatei existiert / geladen werden kann
                    if hasattr(tileset, 'image') and getattr(tileset.image, 'source', None):
                        img_source = getattr(tileset.image, 'source')
                        # Versuche verschiedene Pfad-Kombinationen
                        possible_paths_candidates = [
                            img_source,
                            os.path.join(maps_dir, img_source) if maps_dir else None,
                            os.path.join(os.getcwd(), img_source),
                            os.path.abspath(img_source),
                        ]
                        possible_paths = [p for p in possible_paths_candidates if isinstance(p, str)]
                        
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
                        tsx_paths_candidates = [
                            tsx_source,
                            os.path.join(maps_dir, tsx_source) if maps_dir else None,
                            os.path.join(os.getcwd(), tsx_source),
                        ]
                        tsx_paths = [p for p in tsx_paths_candidates if isinstance(p, str)]
                        
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
                                    if png_source:
                                        png_paths_candidates = [
                                            os.path.join(tsx_dir, png_source),
                                            os.path.join(maps_dir, png_source) if maps_dir else None,
                                            png_source,
                                        ]
                                        png_paths = [p for p in png_paths_candidates if isinstance(p, str)]
                                    else:
                                        png_paths = []
                                    
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
                        if VERBOSE_LOGS:
                            print(f"     ✅ Bild bereits geladen: {img_source}")
                    else:
                        if VERBOSE_LOGS:
                            print(f"     ⚠️ Unbekannter Tileset-Status")
                        
                    # Zusätzliche Debug-Info für alle Tilesets
                    if VERBOSE_LOGS:
                        print(f"     📊 Tileset {tileset.name}: firstgid={tileset.firstgid}, tilecount={tileset.tilecount}, range={tileset.firstgid}-{tileset.firstgid + tileset.tilecount - 1}")
                        if hasattr(tileset, 'columns'):
                            print(f"         Columns: {tileset.columns}, TileSize: {tileset.tilewidth}x{tileset.tileheight}")
        
            # Debug: Zähle erfolgreich geladene Tilesets
            loaded_tilesets = 0
            for tileset in (self.tmx_data.tilesets if self.tmx_data else []):
                if hasattr(tileset, 'image') and tileset.image:
                    loaded_tilesets += 1
            total_tilesets = len(self.tmx_data.tilesets) if self.tmx_data else 0
            if VERBOSE_LOGS:
                print(f"🎨 Tilesets-Status: {loaded_tilesets}/{total_tilesets} erfolgreich geladen")
            if self.tmx_data and loaded_tilesets < total_tilesets and VERBOSE_LOGS:
                print(f"⚠️ {total_tilesets - loaded_tilesets} Tilesets konnten nicht geladen werden!")
                
            # ZUSÄTZLICH: Analysiere GID-Ranges auf Überlappungen/Lücken
            if VERBOSE_LOGS:
                print("🔍 GID-Range-Analyse:")
            sorted_tilesets = sorted(self.tmx_data.tilesets, key=lambda ts: ts.firstgid) if self.tmx_data else []
            for i, tileset in enumerate(sorted_tilesets):
                range_end = tileset.firstgid + tileset.tilecount - 1
                range_status = "✅" if hasattr(tileset, 'image') and tileset.image else "❌"
                if VERBOSE_LOGS:
                    print(f"  {range_status} {tileset.name}: GID {tileset.firstgid}-{range_end} ({tileset.tilecount} tiles)")
                
                # Prüfe auf Lücken/Überlappungen
                if i > 0:
                    prev_tileset = sorted_tilesets[i-1]
                    prev_end = prev_tileset.firstgid + prev_tileset.tilecount - 1
                    if prev_end + 1 != tileset.firstgid:
                        if prev_end >= tileset.firstgid:
                            if VERBOSE_LOGS:
                                print(f"    ⚠️ ÜBERLAPPUNG mit {prev_tileset.name}: {prev_end} >= {tileset.firstgid}")
                        else:
                            if VERBOSE_LOGS:
                                print(f"    ⚠️ LÜCKE nach {prev_tileset.name}: {prev_end+1} bis {tileset.firstgid-1} ({tileset.firstgid-prev_end-1} GIDs)")

    def _load_external_tilesets_manually(self, tmx_filename):
        """
        Lädt externe TSX-Dateien manuell, da PyTMX sie oft falsch lädt.
        KRITISCHER FIX für das terrain-map-v81.tsx Problem.
        """
        import xml.etree.ElementTree as ET
        
        tmx_dir = os.path.dirname(tmx_filename)
        if VERBOSE_LOGS:
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
            
            if VERBOSE_LOGS:
                print(f"   Gefunden: {len(external_tilesets)} externe Tileset-Referenzen")
            
            # Lade jedes externe Tileset manuell
            for firstgid, tsx_source in external_tilesets:
                tsx_path = os.path.join(tmx_dir, tsx_source)
                if VERBOSE_LOGS:
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
                    
                    if VERBOSE_LOGS:
                        print(f"     TSX-Info: {name}, {tilecount} tiles, {columns} cols, PNG: {png_source}")
                    
                    # Finde PNG-Datei
                    if not png_source:
                        print(f"     ❌ PNG-Quelle fehlt im TSX: {tsx_source}")
                        continue
                    png_path = os.path.join(tmx_dir, png_source)
                    if not os.path.exists(png_path):
                        print(f"     ❌ PNG nicht gefunden: {png_path}")
                        continue
                    
                    # Lade PNG mit pygame
                    try:
                        png_surface = pygame.image.load(png_path).convert_alpha()
                        if VERBOSE_LOGS:
                            print(f"     ✅ PNG geladen: {png_surface.get_size()}")
                        
                        # Finde das entsprechende Tileset in tmx_data und setze das Bild
                        for tileset in (self.tmx_data.tilesets if self.tmx_data else []):
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
                                
                                if VERBOSE_LOGS:
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
            if hasattr(layer, 'data') and layer.name and layer.name.lower() in ['foreground', 'front', 'overlay']:
                self.foreground_layer = layer
                if VERBOSE_LOGS:  # type: ignore[name-defined]
                    print(f"🎭 Foreground-Layer gefunden: {layer.name}")
                break
        
        if not self.foreground_layer:
            if VERBOSE_LOGS:  # type: ignore[name-defined]
                print("⚠️ Kein Foreground-Layer gefunden")
    
    def render(self, surface, camera):
        """Rendert alle Layer inklusive Foreground in der richtigen Reihenfolge"""
        if not self.tmx_data:
            return
        
        total_tiles_rendered = 0
        layers_with_tiles = 0
        
        # 1. Alle normalen Layer rendern (außer Foreground)
        for layer in self.tmx_data.visible_layers:
            # ✅ BEHALTEN: Sichere layer.name Prüfung
            if hasattr(layer, 'data') and layer.name and layer.name.lower() not in ['foreground', 'front', 'overlay']:
                layer_tiles = self._render_tile_layer(layer, surface, camera)
                if layer_tiles > 0:
                    total_tiles_rendered += layer_tiles
                    layers_with_tiles += 1
    
        # Debug-Zusammenfassung nur einmal
        if VERBOSE_LOGS and not hasattr(self, '_render_summary_logged'):
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

        # Debug-Ausgabe nur bei VERBOSE_LOGS (sonst massiver I/O-Overhead, v.a. auf RPi)
        debug_this_tile = bool(VERBOSE_LOGS) and len(self.tile_cache) < 50  # type: ignore[name-defined]
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
                if debug_this_tile:
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
            return 0
        tmx = self.tmx_data
        if not tmx:
            return 0

        # Debug: Layer-Diagnose ist teuer -> nur bei VERBOSE_LOGS und nur einmal.
        if VERBOSE_LOGS and not hasattr(layer, '_debug_logged'):  # type: ignore[name-defined]
            total_tiles = 0
            non_empty_tiles = 0
            sample_gids = []

            for y in range(min(10, layer.height)):
                for x in range(min(10, layer.width)):
                    gid = layer.data[y][x]
                    total_tiles += 1
                    if gid != 0:
                        non_empty_tiles += 1
                        sample_gids.append(gid)

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
                if mid_non_empty > 0:
                    print(f"🎯 Layer {layer.name} (Mitte): {mid_non_empty} nicht-leere Tiles gefunden!")

            print(f"🔍 Layer {layer.name}: {non_empty_tiles}/{total_tiles} nicht-leere Tiles (Sample: {sample_gids[:5]})")
            layer._debug_logged = True
        
        # Sichtbarer Bereich
        screen_rect = pygame.Rect(
            camera.camera_rect.x, camera.camera_rect.y,
            surface.get_width(), surface.get_height()
        )
        
        tile_width = tmx.tilewidth
        tile_height = tmx.tileheight
        
        start_x = max(0, screen_rect.left // tile_width)
        start_y = max(0, screen_rect.top // tile_height)
        end_x = min(layer.width, (screen_rect.right // tile_width) + 1)
        end_y = min(layer.height, (screen_rect.bottom // tile_height) + 1)

        # Chunked rendering: pre-render chunks of tiles into surfaces and blit chunks.
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
            chunk = self._chunk_size_tiles

            def get_chunk_surface(chunk_x: int, chunk_y: int):
                key = (getattr(layer, 'name', 'layer'), chunk_x, chunk_y)
                cached = self._layer_chunk_cache.get(key)
                if cached is not None:
                    try:
                        self._layer_chunk_access.remove(key)
                    except ValueError:
                        pass
                    self._layer_chunk_access.append(key)
                    return cached

                # LRU eviction
                while len(self._layer_chunk_cache) >= self._max_cached_chunks and self._layer_chunk_access:
                    old = self._layer_chunk_access.pop(0)
                    self._layer_chunk_cache.pop(old, None)

                chunk_w = chunk * tile_width
                chunk_h = chunk * tile_height
                chunk_surface = pygame.Surface((chunk_w, chunk_h), pygame.SRCALPHA).convert_alpha()

                base_x = chunk_x * chunk
                base_y = chunk_y * chunk
                for ty in range(chunk):
                    map_y = base_y + ty
                    if map_y >= layer.height:
                        break
                    row = layer.data[map_y]
                    for tx in range(chunk):
                        map_x = base_x + tx
                        if map_x >= layer.width:
                            break
                        gid = row[map_x]
                        if gid == 0:
                            continue
                        try:
                            tile_image = tmx.get_tile_image_by_gid(gid)
                            if not tile_image:
                                tile_image = self.get_tile_image_direct(gid)
                            if tile_image:
                                chunk_surface.blit(tile_image, (tx * tile_width, ty * tile_height))
                        except Exception:
                            continue

                self._layer_chunk_cache[key] = chunk_surface
                self._layer_chunk_access.append(key)
                return chunk_surface

            start_cx = start_x // chunk
            start_cy = start_y // chunk
            end_cx = (end_x - 1) // chunk
            end_cy = (end_y - 1) // chunk

            for cy in range(start_cy, end_cy + 1):
                for cx in range(start_cx, end_cx + 1):
                    chunk_surface = get_chunk_surface(cx, cy)
                    draw_x = cx * chunk * tile_width - camera.camera_rect.x
                    draw_y = cy * chunk * tile_height - camera.camera_rect.y
                    surface.blit(chunk_surface, (draw_x, draw_y))
                    tiles_rendered += 1
        
        # Ergebnis-Log mit detaillierter Tile-Statistik
        if VERBOSE_LOGS and tiles_rendered > 0 and not hasattr(layer, '_render_logged'):  # type: ignore[name-defined]
            print(f"  ✅ Layer {layer.name}: {tiles_rendered} Tiles gerendert")
            
            # ERWEITERT: Zeige GID-Verteilung für diesen Layer
            if VERBOSE_LOGS and hasattr(layer, '_missing_gids') and layer._missing_gids:
                print(f"    ❌ Fehlende GIDs: {sorted(list(layer._missing_gids))}")
            
            layer._render_logged = True
        elif tiles_rendered == 0 and not hasattr(layer, '_empty_logged'):
            if VERBOSE_LOGS:
                if VERBOSE_LOGS:
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
        Baut die Kollisionsobjekte-Liste aus allen relevanten Ebenen:
        - Objekt-Ebenen: Namen enthalten 'Walls', 'Collision', 'Obstacles' (case-insensitive) oder Property collidable=true
        - Tile-Ebenen: Namen enthalten 'hitbox', 'collision', 'solid', 'wall' (case-insensitive) oder Property collidable=true

        Diese erweiterten Kollisionen werden für Bewegung, LOS und Pathfinding genutzt,
        damit Gegner um Bäume/Steine herum navigieren und nicht hindurch laufen.
        """
        if not self.tmx_data:
            return

        try:
            from core.settings import VERBOSE_LOGS
        except Exception:
            VERBOSE_LOGS = False  # type: ignore
        if VERBOSE_LOGS:  # type: ignore[name-defined]
            print("Baue Kollisionsobjekte aus der Karte...")
        try:
            # Reset, then gather ONLY from Tiled Object Layers that represent colliders
            self.collision_objects = []
            added_from_layers = []

            try:
                import pytmx  # ensure type checks
            except Exception:
                pytmx = None  # type: ignore

            def object_layer_is_collidable(layer) -> bool:
                # Only object groups by explicit property or trusted names
                try:
                    if hasattr(layer, 'properties'):
                        props = dict(layer.properties)
                        if str(props.get('collidable', '')).lower() in ('1', 'true', 'yes'):
                            return True
                except Exception:
                    pass
                name = (getattr(layer, 'name', '') or '').lower()
                return name in ('walls', 'collision')

            layers = list(getattr(self.tmx_data, 'visible_layers', [])) or list(getattr(self.tmx_data, 'layers', []))
            if not layers:
                print("WARNUNG: Keine Layer in TMX-Daten gefunden.")
                return

            for layer in layers:
                # Only consider object groups
                if not (pytmx and isinstance(layer, pytmx.TiledObjectGroup)):
                    continue
                if not object_layer_is_collidable(layer):
                    continue

                count_before = len(self.collision_objects)
                for obj in layer:
                    try:
                        rect = pygame.Rect(obj.x, obj.y, obj.width, obj.height)
                        self.collision_objects.append(rect)
                    except Exception:
                        continue
                added = len(self.collision_objects) - count_before
                if added:
                    added_from_layers.append((layer.name, added, 'objects'))

            # Fallback: try to get specific well-known object groups if not included by filter
            if not added_from_layers:
                for name in ('Walls', 'Collision'):
                    try:
                        lyr = self.tmx_data.get_layer_by_name(name)
                    except Exception:
                        lyr = None
                    if not lyr or not (pytmx and isinstance(lyr, pytmx.TiledObjectGroup)):
                        continue
                    count_before = len(self.collision_objects)
                    for obj in lyr:
                        self.collision_objects.append(pygame.Rect(obj.x, obj.y, obj.width, obj.height))
                    added = len(self.collision_objects) - count_before
                    if added:
                        added_from_layers.append((name, added, 'objects'))

            # Deduplicate
            try:
                seen = set()
                unique = []
                for r in self.collision_objects:
                    key = (r.x, r.y, r.width, r.height)
                    if key not in seen:
                        unique.append(r)
                        seen.add(key)
                if len(unique) != len(self.collision_objects):
                    print(f"ℹ️ {len(self.collision_objects) - len(unique)} doppelte Kollisions-Rechtecke entfernt")
                self.collision_objects = unique
            except Exception:
                pass

            total = len(self.collision_objects)
            if added_from_layers:
                summary = ", ".join([f"{name}:+{cnt} ({kind})" for name, cnt, kind in added_from_layers])
                if VERBOSE_LOGS:
                    print(f"✅ {total} Kollisionsobjekte aus Objektebenen: {summary}")
            else:
                if VERBOSE_LOGS:
                    print("WARNUNG: Keine kollidierbaren Objektebenen gefunden – keine Kollisionsobjekte erstellt")

        except Exception as e:
            if VERBOSE_LOGS:
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
                        if VERBOSE_LOGS:  # type: ignore[name-defined]
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

