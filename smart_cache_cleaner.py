# -*- coding: utf-8 -*-
"""
Intelligenter Python Cache Cleaner - Erkennt verwaiste .pyc Dateien
Löscht nur .pyc Dateien, deren entsprechende .py Dateien nicht mehr existieren
"""

import os
import sys
import shutil
import time

def find_orphaned_cache_files(root_dir):
    """Findet verwaiste Cache-Dateien ohne entsprechende .py Dateien."""
    orphaned_pyc = []
    orphaned_pyo = []
    empty_pycache_dirs = []
    all_pycache_dirs = []
    
    print("Analysiere Projekt auf verwaiste Cache-Dateien...")
    
    for root, dirs, files in os.walk(root_dir):
        # Sammle alle __pycache__ Ordner
        if '__pycache__' in dirs:
            pycache_path = os.path.join(root, '__pycache__')
            all_pycache_dirs.append(pycache_path)
            
            # Prüfe Dateien im __pycache__ Ordner
            try:
                cache_files = os.listdir(pycache_path)
                has_valid_cache = False
                
                for cache_file in cache_files:
                    if cache_file.endswith('.pyc') or cache_file.endswith('.pyo'):
                        # Extrahiere den ursprünglichen .py Dateinamen
                        # Format: filename.cpython-39.pyc oder filename.pyc
                        base_name = cache_file.split('.')[0]
                        py_file = os.path.join(root, base_name + '.py')
                        
                        cache_file_path = os.path.join(pycache_path, cache_file)
                        
                        if not os.path.exists(py_file):
                            # .py Datei existiert nicht mehr - Cache ist verwaist
                            if cache_file.endswith('.pyc'):
                                orphaned_pyc.append(cache_file_path)
                            else:
                                orphaned_pyo.append(cache_file_path)
                        else:
                            has_valid_cache = True
                
                # Markiere leere oder komplett verwaiste __pycache__ Ordner
                if not has_valid_cache:
                    empty_pycache_dirs.append(pycache_path)
                    
            except OSError:
                # Ordner nicht lesbar
                pass
        
        # Prüfe auch .pyc/.pyo Dateien direkt im Verzeichnis (alte Python-Versionen)
        for file in files:
            if file.endswith('.pyc') or file.endswith('.pyo'):
                cache_file_path = os.path.join(root, file)
                base_name = file.rsplit('.', 1)[0]  # Entferne .pyc/.pyo
                py_file = os.path.join(root, base_name + '.py')
                
                if not os.path.exists(py_file):
                    if file.endswith('.pyc'):
                        orphaned_pyc.append(cache_file_path)
                    else:
                        orphaned_pyo.append(cache_file_path)
    
    return orphaned_pyc, orphaned_pyo, empty_pycache_dirs, all_pycache_dirs

def find_outdated_cache_files(root_dir):
    """Findet .pyc Dateien, die älter als ihre entsprechenden .py Dateien sind."""
    outdated_pyc = []
    
    print("Suche veraltete Cache-Dateien...")
    
    for root, dirs, files in os.walk(root_dir):
        if '__pycache__' in dirs:
            pycache_path = os.path.join(root, '__pycache__')
            
            try:
                cache_files = os.listdir(pycache_path)
                
                for cache_file in cache_files:
                    if cache_file.endswith('.pyc'):
                        base_name = cache_file.split('.')[0]
                        py_file = os.path.join(root, base_name + '.py')
                        cache_file_path = os.path.join(pycache_path, cache_file)
                        
                        if os.path.exists(py_file):
                            # Vergleiche Änderungszeiten
                            py_mtime = os.path.getmtime(py_file)
                            cache_mtime = os.path.getmtime(cache_file_path)
                            
                            if cache_mtime < py_mtime:
                                outdated_pyc.append(cache_file_path)
                                
            except OSError:
                pass
    
    return outdated_pyc

def smart_cache_cleanup(root_dir='.', mode='orphaned', verbose=False):
    """
    Intelligente Cache-Bereinigung mit verschiedenen Modi.
    
    Modi:
    - 'orphaned': Nur verwaiste .pyc ohne entsprechende .py Datei
    - 'outdated': Nur veraltete .pyc (älter als .py Datei)
    - 'all': Alle .pyc Dateien
    - 'smart': Kombiniert orphaned + outdated
    """
    print("Intelligenter Python Cache Cleaner")
    print("=" * 50)
    print("Modus: {}".format(mode))
    print("")
    
    removed_count = 0
    
    if mode in ['orphaned', 'smart', 'all']:
        orphaned_pyc, orphaned_pyo, empty_dirs, all_dirs = find_orphaned_cache_files(root_dir)
        
        print("Verwaiste Cache-Dateien gefunden:")
        print("   - Verwaiste .pyc: {}".format(len(orphaned_pyc)))
        print("   - Verwaiste .pyo: {}".format(len(orphaned_pyo)))
        print("   - Leere __pycache__: {}".format(len(empty_dirs)))
        
        # Lösche verwaiste .pyc Dateien
        for pyc_file in orphaned_pyc:
            try:
                os.remove(pyc_file)
                removed_count += 1
                if verbose:
                    print("   Verwaiste .pyc gelöscht: {}".format(pyc_file))
            except OSError as e:
                print("   Fehler: {}".format(e))
        
        # Lösche verwaiste .pyo Dateien
        for pyo_file in orphaned_pyo:
            try:
                os.remove(pyo_file)
                removed_count += 1
                if verbose:
                    print("   Verwaiste .pyo gelöscht: {}".format(pyo_file))
            except OSError as e:
                print("   Fehler: {}".format(e))
        
        # Lösche leere __pycache__ Ordner
        for empty_dir in empty_dirs:
            try:
                shutil.rmtree(empty_dir)
                removed_count += 1
                if verbose:
                    print("   Leerer __pycache__ gelöscht: {}".format(empty_dir))
            except OSError as e:
                print("   Fehler: {}".format(e))
    
    if mode in ['outdated', 'smart']:
        outdated_pyc = find_outdated_cache_files(root_dir)
        
        print("\nVeraltete Cache-Dateien gefunden: {}".format(len(outdated_pyc)))
        
        # Lösche veraltete .pyc Dateien
        for pyc_file in outdated_pyc:
            try:
                os.remove(pyc_file)
                removed_count += 1
                if verbose:
                    print("   Veraltete .pyc gelöscht: {}".format(pyc_file))
            except OSError as e:
                print("   Fehler: {}".format(e))
    
    if mode == 'all':
        # Lösche alle verbliebenen Cache-Dateien
        all_pyc, all_pyo, all_dirs = find_cache_files(root_dir)
        
        for pyc_file in all_pyc:
            try:
                os.remove(pyc_file)
                removed_count += 1
            except OSError:
                pass
        
        for pyo_file in all_pyo:
            try:
                os.remove(pyo_file)
                removed_count += 1
            except OSError:
                pass
        
        for cache_dir in all_dirs:
            try:
                shutil.rmtree(cache_dir)
                removed_count += 1
            except OSError:
                pass
    
    print("\nBereinigung abgeschlossen: {} Elemente entfernt".format(removed_count))
    return removed_count

def find_cache_files(root_dir):
    """Hilfsfunktion - findet alle Cache-Dateien (für 'all' Modus)."""
    pyc_files = []
    pyo_files = []
    pycache_dirs = []
    
    for root, dirs, files in os.walk(root_dir):
        if '__pycache__' in dirs:
            pycache_dirs.append(os.path.join(root, '__pycache__'))
        
        for file in files:
            if file.endswith('.pyc'):
                pyc_files.append(os.path.join(root, file))
            elif file.endswith('.pyo'):
                pyo_files.append(os.path.join(root, file))
    
    return pyc_files, pyo_files, pycache_dirs

if __name__ == "__main__":
    import argparse
    
    # Einfache Argument-Behandlung für ältere Python-Versionen
    mode = 'smart'  # Standard: intelligente Bereinigung
    verbose = False
    
    if '--mode=orphaned' in sys.argv:
        mode = 'orphaned'
    elif '--mode=outdated' in sys.argv:
        mode = 'outdated'
    elif '--mode=all' in sys.argv:
        mode = 'all'
    elif '--mode=smart' in sys.argv:
        mode = 'smart'
    
    if '--verbose' in sys.argv or '-v' in sys.argv:
        verbose = True
    
    try:
        smart_cache_cleanup('.', mode, verbose)
    except KeyboardInterrupt:
        print("\nBereinigung abgebrochen.")
    except Exception as e:
        print("\nFehler: {}".format(e))
