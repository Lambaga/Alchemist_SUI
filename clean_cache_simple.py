# -*- coding: utf-8 -*-
"""
Einfacher Python Cache Cleaner fuer das Alchemist Projekt
Kompatibel mit Python 2.7+ und 3.x
"""

import os
import sys
import shutil

def find_cache_files(root_dir):
    """Findet alle Cache-Dateien und -Ordner."""
    pyc_files = []
    pyo_files = []
    pycache_dirs = []
    
    for root, dirs, files in os.walk(root_dir):
        # Finde __pycache__ Ordner
        if '__pycache__' in dirs:
            pycache_dirs.append(os.path.join(root, '__pycache__'))
        
        # Finde .pyc und .pyo Dateien
        for file in files:
            if file.endswith('.pyc'):
                pyc_files.append(os.path.join(root, file))
            elif file.endswith('.pyo'):
                pyo_files.append(os.path.join(root, file))
    
    return pyc_files, pyo_files, pycache_dirs

def clean_cache(root_dir='.', verbose=False):
    """Bereinigt alle Python Cache-Dateien."""
    print("Python Cache Bereinigung fuer Alchemist")
    print("=" * 50)
    
    # Finde alle Cache-Dateien
    pyc_files, pyo_files, pycache_dirs = find_cache_files(root_dir)
    
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
    
    # .pyc Dateien loeschen
    for pyc_file in pyc_files:
        try:
            os.remove(pyc_file)
            removed_count += 1
            if verbose:
                print("   Geloescht: {}".format(pyc_file))
        except OSError as e:
            print("   Fehler: {}".format(e))
    
    # .pyo Dateien loeschen
    for pyo_file in pyo_files:
        try:
            os.remove(pyo_file)
            removed_count += 1
            if verbose:
                print("   Geloescht: {}".format(pyo_file))
        except OSError as e:
            print("   Fehler: {}".format(e))
    
    # __pycache__ Ordner loeschen
    for pycache_dir in pycache_dirs:
        try:
            shutil.rmtree(pycache_dir)
            removed_count += 1
            if verbose:
                print("   Geloescht: {}".format(pycache_dir))
        except OSError as e:
            print("   Fehler: {}".format(e))
    
    print("\nCache-Bereinigung abgeschlossen! {} Elemente entfernt.".format(removed_count))
    
    # Verifikation
    print("\nVerifikation...")
    pyc_remaining, pyo_remaining, cache_remaining = find_cache_files(root_dir)
    total_remaining = len(pyc_remaining) + len(pyo_remaining) + len(cache_remaining)
    
    if total_remaining == 0:
        print("Alle Cache-Dateien erfolgreich entfernt!")
    else:
        print("Noch vorhanden: {} .pyc, {} .pyo, {} __pycache__".format(
            len(pyc_remaining), len(pyo_remaining), len(cache_remaining)))
    
    print("\nTipp: Fuehre dieses Skript regelmaessig aus!")

if __name__ == "__main__":
    # Einfache Argument-Behandlung
    verbose = '--verbose' in sys.argv or '-v' in sys.argv
    
    try:
        clean_cache('.', verbose)
    except KeyboardInterrupt:
        print("\nBereinigung abgebrochen.")
    except Exception as e:
        print("\nFehler: {}".format(e))
