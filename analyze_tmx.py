#!/usr/bin/env python3
"""
Quick TMX file analyzer to check data encoding
"""
import xml.etree.ElementTree as ET

def analyze_tmx():
    # Parse TMX file directly
    tree = ET.parse('assets/maps/Map_Town.tmx')
    root = tree.getroot()

    print('=== TMX FILE ANALYSIS ===')
    width = root.get('width')
    height = root.get('height')
    tile_w = root.get('tilewidth')
    tile_h = root.get('tileheight')
    print(f'Map size: {width}x{height}')
    print(f'Tile size: {tile_w}x{tile_h}')

    # Check layers
    for i, layer_elem in enumerate(root.findall('layer')):
        name = layer_elem.get('name')
        width = int(layer_elem.get('width', 0))
        height = int(layer_elem.get('height', 0))
        
        print(f'\nLayer {i+1}: {name} ({width}x{height})')
        
        # Check data encoding
        data_elem = layer_elem.find('data')
        if data_elem is not None:
            encoding = data_elem.get('encoding', 'xml')
            compression = data_elem.get('compression', 'none')
            print(f'  Data encoding: {encoding}, compression: {compression}')
            
            # Check if data contains actual content
            data_text = data_elem.text.strip() if data_elem.text else ''
            if data_text:
                # Show first few characters
                preview = data_text[:100]
                print(f'  Data preview: {preview}...')
                
                # If CSV, check first few values
                if encoding == 'csv':
                    try:
                        # Split and parse first 50 values
                        parts = data_text.replace('\n', '').split(',')
                        values = []
                        for part in parts[:50]:
                            part = part.strip()
                            if part and part.isdigit():
                                values.append(int(part))
                        
                        print(f'  First 20 values: {values[:20]}')
                        non_zero = [v for v in values if v > 0]
                        print(f'  Non-zero count in first 50: {len(non_zero)}')
                        if non_zero:
                            print(f'  Sample non-zero values: {non_zero[:10]}')
                    except Exception as e:
                        print(f'  Error parsing CSV values: {e}')
            else:
                print('  No data content found!')
        
        # Check first 3 layers only
        if i >= 2:
            break

if __name__ == "__main__":
    analyze_tmx()