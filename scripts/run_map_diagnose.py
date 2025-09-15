#!/usr/bin/env python3
import os
import sys
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAP = os.path.join(ROOT, 'assets', 'maps', 'Map2.tmx')  # Geändert von Map_Town.tmx
REPORT = os.path.join(ROOT, 'map2_gid_report.json')  # Angepasster Report-Name

cmd = [sys.executable, os.path.join(ROOT, 'scripts', 'scan_map_gids.py'), '--map', MAP, '--report', REPORT, '--suggest-remap']
print('Running:', ' '.join(cmd))
res = subprocess.run(cmd, cwd=ROOT)
print('Exit code:', res.returncode)
