#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Python Cache Cleaner fuer das Alchemist Projekt

Dieses Skript bereinigt alle Python Cache-Dateien (.pyc, .pyo) 
und __pycache__ Ordner im Projekt-Verzeichnis.

Verwendung:
    python clean_cache.py
    python clean_cache.py --verbose
"""

import os
import sys
import shutil
import argparse
from pathlib import Path

def count_files_and_dirs(project_path):
    """Zaehlt alle Cache-Dateien und -Ordner."""
    pyc_files = list(project_path.rglob("*.pyc"))
    pyo_files = list(project_path.rglob("*.pyo"))
    pycache_dirs = [p for p in project_path.rglob("__pycache__") if p.is_dir()]
    
    return pyc_files, pyo_files, pycache_dirs

def clean_cache_files(project_path, verbose=False):
    """Bereinigt alle Python Cache-Dateien und -Ordner."""
    
    print("Python Cache Bereinigung fuer Alchemist")
    print("=" * 50)
    
    # Zähle Dateien vor der Bereinigung
    pyc_files, pyo_files, pycache_dirs = count_files_and_dirs(project_path)
    
    print("Gefunden:")
    print("   - .pyc Dateien: {}".format(len(pyc_files)))
    print("   - .pyo Dateien: {}".format(len(pyo_files)))
    print("   - __pycache__ Ordner: {}".format(len(pycache_dirs)))
    
    total_items = len(pyc_files) + len(pyo_files) + len(pycache_dirs)
    
    if total_items == 0:
        print("Keine Cache-Dateien gefunden - Projekt ist bereits sauber!")
        return
    
    print("\nBereinige {} Cache-Elemente...".format(total_items))
    
    removed_count = 0
    
    # .pyc Dateien löschen
    for pyc_file in pyc_files:
        try:
            pyc_file.unlink()
            removed_count += 1
            if verbose:
                print("   Geloescht: {}".format(pyc_file))
        except OSError as e:
            print("   Fehler beim Loeschen von {}: {}".format(pyc_file, e))
    
    # .pyo Dateien loeschen
    for pyo_file in pyo_files:
        try:
            pyo_file.unlink()
            removed_count += 1
            if verbose:
                print("   Geloescht: {}".format(pyo_file))
        except OSError as e:
            print("   Fehler beim Loeschen von {}: {}".format(pyo_file, e))
    
    # __pycache__ Ordner loeschen
    for pycache_dir in pycache_dirs:
        try:
            shutil.rmtree(pycache_dir)
            removed_count += 1
            if verbose:
                print("   Geloescht: {}".format(pycache_dir))
        except OSError as e:
            print("   Fehler beim Loeschen von {}: {}".format(pycache_dir, e))
    
    print("\nCache-Bereinigung abgeschlossen! {} Elemente entfernt.".format(removed_count))
    
    # Verifikation
    print("\nVerifikation...")
    pyc_remaining, pyo_remaining, cache_remaining = count_files_and_dirs(project_path)
    total_remaining = len(pyc_remaining) + len(pyo_remaining) + len(cache_remaining)
    
    if total_remaining == 0:
        print("Alle Cache-Dateien erfolgreich entfernt!")
    else:
        print("Noch vorhanden: {} .pyc, {} .pyo, {} __pycache__".format(
            len(pyc_remaining), len(pyo_remaining), len(cache_remaining)))
    
    print("\nTipp: Fuehre dieses Skript regelmaessig aus, besonders nach groesseren Code-Aenderungen!")

def main():
    parser = argparse.ArgumentParser(description="Bereinigt Python Cache-Dateien im Alchemist Projekt")
    parser.add_argument("-v", "--verbose", action="store_true", 
                       help="Zeigt detaillierte Ausgabe fuer jede geloeschte Datei")
    parser.add_argument("--path", type=str, default=".", 
                       help="Pfad zum Projekt-Verzeichnis (Standard: aktuelles Verzeichnis)")
    
    args = parser.parse_args()
    
    project_path = Path(args.path).resolve()
    
    if not project_path.exists():
        print("Pfad existiert nicht: {}".format(project_path))
        sys.exit(1)
    
    if not project_path.is_dir():
        print("Pfad ist kein Verzeichnis: {}".format(project_path))
        sys.exit(1)
    
    try:
        clean_cache_files(project_path, args.verbose)
    except KeyboardInterrupt:
        print("\nBereinigung durch Benutzer abgebrochen.")
        sys.exit(1)
    except Exception as e:
        print("\nUnerwarteter Fehler: {}".format(e))
        sys.exit(1)

if __name__ == "__main__":
    main()
