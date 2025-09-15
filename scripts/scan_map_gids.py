#!/usr/bin/env python3
import argparse
import json
import os
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict, Counter

try:
    import pygame  # optional
except ImportError:  # allow running without pygame (no image inference)
    pygame = None
try:
    import pytmx
except ImportError:
    print("❌ Modul 'pytmx' nicht gefunden. Bitte zuerst virtuelle Umgebung aktivieren oder installieren:")
    print("   PowerShell: .\\.venv\\Scripts\\Activate.ps1")
    print("   Dann:       pip install pytmx")
    print("Oder direkt:  .\\.venv\\Scripts\\python.exe -m pip install pytmx")
    sys.exit(1)

TMX_FLIP_H = 0x80000000
TMX_FLIP_V = 0x40000000
TMX_FLIP_D = 0x20000000
TMX_FLAG_MASK = ~(TMX_FLIP_H | TMX_FLIP_V | TMX_FLIP_D)

# -------------------------------------------------------------
# Utility: compute tilecount / lastgid from a pytmx tileset
# -------------------------------------------------------------

def compute_tileset_bounds(ts):
    tilecount = getattr(ts, 'tilecount', None)
    try:
        tilecount = int(tilecount) if tilecount is not None else None
    except Exception:
        tilecount = None
    if tilecount is None and pygame is not None:
        # Try infer from image if pygame available
        image = getattr(ts, 'image', None)
        if image:
            path_root = os.path.dirname(getattr(ts, 'filename', '') or '')
            img_path = os.path.join(path_root, image)
            if os.path.exists(img_path):
                try:
                    surf = pygame.image.load(img_path)
                    tilew = getattr(ts, 'tilewidth', 32) or 32
                    tileh = getattr(ts, 'tileheight', 32) or 32
                    spacing = getattr(ts, 'spacing', 0) or 0
                    margin = getattr(ts, 'margin', 0) or 0
                    usable_w = surf.get_width() - 2 * margin + spacing
                    usable_h = surf.get_height() - 2 * margin + spacing
                    cols = max(1, usable_w // (tilew + spacing))
                    rows = max(1, usable_h // (tileh + spacing))
                    tilecount = cols * rows
                except Exception:
                    pass
    if tilecount is None:
        # Fallback: count defined tiles (animations etc.)
        try:
            tilecount = len(ts.tiles())
        except Exception:
            tilecount = 0
    firstgid = ts.firstgid
    lastgid = firstgid + tilecount - 1 if tilecount else firstgid
    return firstgid, lastgid, tilecount

# -------------------------------------------------------------
# Gap detection and classification
# -------------------------------------------------------------

def detect_gaps(tileset_bounds):
    gaps = []  # (start, end)
    if not tileset_bounds:
        return gaps
    tileset_bounds_sorted = sorted(tileset_bounds, key=lambda t: t[0])
    expected = tileset_bounds_sorted[0][0]
    for firstgid, lastgid, _ in tileset_bounds_sorted:
        if firstgid > expected:
            gaps.append((expected, firstgid - 1))
        expected = lastgid + 1
    return gaps

# -------------------------------------------------------------
# Remap suggestion: collapse each gap length from any gid inside gap
# -------------------------------------------------------------

def build_gap_remap(gaps):
    remap = {}
    cumulative = 0
    suggestions = []
    for (start, end) in gaps:
        length = (end - start + 1)
        # For every gid in gap -> gid - cumulative - length (collapse current + previous gaps)
        for gid in range(start, end + 1):
            remap[gid] = gid - (length + cumulative)
        suggestions.append({
            'gap_start': start,
            'gap_end': end,
            'gap_length': length,
            'rule': f"gid in [{start},{end}] => gid - {length + cumulative}",
            'offset_applied': length + cumulative
        })
        cumulative += length
    return remap, suggestions

# -------------------------------------------------------------
# Write modified TMX (CSV encoding only)
# -------------------------------------------------------------

def apply_remap_to_tmx(tmx_path, remap, output_path):
    tree = ET.parse(tmx_path)
    root = tree.getroot()
    changed = 0
    for layer in root.findall('layer'):
        data = layer.find('data')
        if data is None:
            continue
        encoding = data.get('encoding')
        if encoding != 'csv':
            print(f"[Skip] Layer '{layer.get('name')}' nicht CSV-encodiert (encoding={encoding}) -> Remap übersprungen")
            continue
        text = data.text or ''
        numbers = [n.strip() for n in text.strip().split(',') if n.strip()]
        new_numbers = []
        for n in numbers:
            try:
                v = int(n)
            except ValueError:
                new_numbers.append(n)
                continue
            if v in remap:
                new_numbers.append(str(remap[v]))
                changed += 1
            else:
                new_numbers.append(n)
        data.text = ',\n'.join(new_numbers) + '\n'
    tree.write(output_path, encoding='utf-8')
    return changed

# -------------------------------------------------------------
# Main diagnostic
# -------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description='Scan TMX map for GID issues, gaps and suggest remaps.')
    parser.add_argument('--map', default='assets/maps/Map2.tmx', help='Path to TMX map file')  # Geändert von Map_Town.tmx
    parser.add_argument('--report', default='map_town_gid_report.json', help='Report JSON output path')
    parser.add_argument('--suggest-remap', action='store_true', help='Generate remap suggestion JSON')
    parser.add_argument('--apply-remap', action='store_true', help='Apply remap and create fixed TMX copy')
    parser.add_argument('--remap-json', default='map_town_gid_remap.json', help='Remap suggestion output path')
    parser.add_argument('--fixed-out', default='assets/maps/Map_Town_fixed.tmx', help='Output TMX for applied remap')
    args = parser.parse_args()

    if not os.path.exists(args.map):
        print(f"❌ Map nicht gefunden: {args.map}")
        sys.exit(1)

    if pygame is not None:
        try:
            pygame.init()
        except Exception:
            pass
    print(f"🗺️ Lade TMX für Analyse: {args.map}")
    if pygame is None:
        print("[Hinweis] pygame nicht installiert -> keine Bild-basierte Tilecount-Inferrenz (verwende deklarierte Werte).")
    # Vermeide pygame-Image-Conversion: No-Op Loader mit kompatibler Signatur
    def _noop_loader(filename, colorkey, **kwargs):
        def _tile_loader(rect, flags):
            return None
        return _tile_loader
    tmx = pytmx.TiledMap(args.map, image_loader=_noop_loader)

    # Tileset bounds
    tileset_bounds = []  # list of (firstgid, lastgid, tilecount, name)
    for ts in tmx.tilesets:
        firstgid, lastgid, tilecount = compute_tileset_bounds(ts)
        name = getattr(ts, 'name', 'unknown')
        tileset_bounds.append((firstgid, lastgid, tilecount, name))

    tileset_bounds_sorted = sorted(tileset_bounds, key=lambda t: t[0])

    # Build gap list
    gaps = []
    expected = tileset_bounds_sorted[0][0] if tileset_bounds_sorted else 0
    for firstgid, lastgid, tilecount, name in tileset_bounds_sorted:
        if firstgid > expected:
            gaps.append((expected, firstgid - 1))
        expected = lastgid + 1

    gap_set = []
    for g in gaps:
        gap_set.append({'start': g[0], 'end': g[1], 'length': g[1]-g[0]+1})

    # Quick lookup for tileset assignment
    def lookup_tileset(gid):
        for firstgid, lastgid, tilecount, name in tileset_bounds_sorted:
            if firstgid <= gid <= lastgid:
                return (firstgid, lastgid, tilecount, name)
        return None

    # Build gap ranges for classification
    gap_ranges = gaps

    # Classification
    usage_counter = Counter()
    gid_usage = Counter()
    problematic_gids = {}

    layer_summaries = []

    for layer in tmx.visible_layers:
        if not hasattr(layer, 'data'):
            continue
        layer_info = {
            'name': layer.name,
            'total_tiles': 0,
            'used_gids': 0,
            'gap_hits': 0,
            'oob_hits': 0,
            'unknown_hits': 0
        }
        for y, row in enumerate(layer.data):
            for x, raw_gid in enumerate(row):
                if raw_gid == 0:
                    continue
                gid = raw_gid & TMX_FLAG_MASK
                layer_info['total_tiles'] += 1
                gid_usage[gid] += 1
                ts = lookup_tileset(gid)
                in_gap = any(start <= gid <= end for start, end in gap_ranges)
                if ts is None and in_gap:
                    usage_counter['gap'] += 1
                    layer_info['gap_hits'] += 1
                    problematic_gids.setdefault(gid, set()).add('gap')
                elif ts is None:
                    usage_counter['unknown'] += 1
                    layer_info['unknown_hits'] += 1
                    problematic_gids.setdefault(gid, set()).add('unknown')
                else:
                    firstgid, lastgid, tilecount, ts_name = ts
                    local_id = gid - firstgid
                    if tilecount is not None and local_id >= tilecount:
                        usage_counter['oob_local'] += 1
                        layer_info['oob_hits'] += 1
                        problematic_gids.setdefault(gid, set()).add('oob_local')
                    else:
                        usage_counter['valid'] += 1
                        layer_info['used_gids'] += 1
        layer_summaries.append(layer_info)

    total_unique = len(gid_usage)

    report = {
        'map': args.map,
        'tilesets': [
            {
                'name': name,
                'firstgid': firstgid,
                'lastgid': lastgid,
                'tilecount': tilecount
            } for (firstgid, lastgid, tilecount, name) in tileset_bounds_sorted
        ],
        'gaps': gap_set,
        'usage_summary': dict(usage_counter),
        'unique_gid_count': total_unique,
        'layer_summaries': layer_summaries,
        'problematic_gid_samples': [
            {'gid': gid, 'issues': sorted(list(issues)), 'usage': gid_usage[gid]}
            for gid, issues in list(problematic_gids.items())[:50]
        ]
    }

    with open(args.report, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    print(f"✅ Diagnose-Report geschrieben: {args.report}")

    # Remap suggestion
    if args.suggest_remap and gaps:
        remap_dict, suggestions = build_gap_remap(gaps)
        remap_wrapper = {
            'map': args.map,
            'gaps': gap_set,
            'suggestions': suggestions,
            'remap_entries': len(remap_dict)
        }
        with open(args.remap_json, 'w', encoding='utf-8') as f:
            json.dump(remap_wrapper, f, indent=2)
        print(f"💡 Remap-Vorschlag gespeichert: {args.remap_json}")
    elif args.suggest_remap:
        print("💡 Keine Gaps gefunden -> kein Remap nötig.")

    # Apply remap
    if args.apply_remap:
        if not gaps:
            print("[Remap] Keine GIDLücken -> Anwendung übersprungen.")
        else:
            if not args.suggest_remap:
                # Build anyway
                remap_dict, suggestions = build_gap_remap(gaps)
            else:
                remap_dict, suggestions = build_gap_remap(gaps)
            backup_path = args.map + '.bak'
            if not os.path.exists(backup_path):
                try:
                    import shutil
                    shutil.copy2(args.map, backup_path)
                    print(f"[Remap] Backup erstellt: {backup_path}")
                except Exception as e:
                    print(f"[Remap] Backup fehlgeschlagen: {e}")
            changed = apply_remap_to_tmx(args.map, remap_dict, args.fixed_out)
            print(f"🛠️ Remap angewendet -> {args.fixed_out} (geänderte Tiles: {changed})")

    print("Fertig.")

if __name__ == '__main__':
    main()
