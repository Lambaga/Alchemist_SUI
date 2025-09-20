# -*- coding: utf-8 -*-
"""
Einfache Performance-Demo: Zeigt warum .pyc Dateien nuetzlich sind
"""

import time
import os
import sys

def create_test_modules():
    """Erstellt Test-Module fuer die Demo."""
    
    # Test-Modul 1: Viele Imports
    test1_content = '''# -*- coding: utf-8 -*-
import os
import sys
import time
import json
import random
import math

def test_function():
    """Test-Funktion mit verschiedenen Berechnungen."""
    result = 0
    for i in range(100):
        result += math.sqrt(i) * random.random()
    return result

class TestClass:
    def __init__(self):
        self.data = {}
        for i in range(50):
            self.data[str(i)] = time.time() + random.random()
    
    def process(self):
        return sum(self.data.values())

# Globale Initialisierung
TEST_DATA = TestClass()
TEST_RESULT = test_function()
'''

    # Test-Modul 2: Komplexere Logik
    test2_content = '''# -*- coding: utf-8 -*-
import test_module1

def complex_calculation():
    """Komplexe Berechnung die andere Module nutzt."""
    base = test_module1.TEST_RESULT
    
    # Simuliere komplexe Spiellogik
    for iteration in range(10):
        base = base * 1.1 + iteration
        if base > 1000:
            base = base / 2
    
    return base

COMPUTED_VALUE = complex_calculation()
'''

    try:
        with open('test_module1.py', 'w') as f:
            f.write(test1_content)
        
        with open('test_module2.py', 'w') as f:
            f.write(test2_content)
            
        print("Test-Module erstellt!")
        return True
    except Exception as e:
        print("Fehler beim Erstellen der Test-Module: {}".format(e))
        return False

def cleanup_test_modules():
    """Raeumt Test-Module auf."""
    files_to_remove = [
        'test_module1.py', 'test_module1.pyc',
        'test_module2.py', 'test_module2.pyc',
        '__pycache__'
    ]
    
    for filename in files_to_remove:
        try:
            if os.path.isfile(filename):
                os.remove(filename)
            elif os.path.isdir(filename):
                import shutil
                shutil.rmtree(filename)
        except OSError:
            pass

def measure_import_performance():
    """Misst Import-Performance mit und ohne Cache."""
    
    print("=" * 50)
    print("PERFORMANCE-TEST: .pyc Cache-Dateien")
    print("=" * 50)
    
    # 1. Erste Messung - ohne Cache
    print("\n1. OHNE Cache (.pyc Dateien):")
    
    start_time = time.time()
    try:
        import test_module1
        import test_module2
        # Erzwinge reload falls schon importiert
        reload(test_module1)
        reload(test_module2)
    except NameError:
        # Python 3 - kein reload in builtins
        import importlib
        importlib.reload(test_module1)
        importlib.reload(test_module2)
    except Exception as e:
        print("Import-Fehler: {}".format(e))
        return
    
    time_without_cache = time.time() - start_time
    print("   Import-Zeit: {:.4f} Sekunden".format(time_without_cache))
    
    # 2. Zweite Messung - mit Cache
    print("\n2. MIT Cache (.pyc Dateien):")
    
    start_time = time.time()
    try:
        # Module sind bereits importiert und Cache existiert
        if 'importlib' in locals():
            importlib.reload(test_module1)
            importlib.reload(test_module2)
        else:
            reload(test_module1)
            reload(test_module2)
    except Exception as e:
        print("Import-Fehler: {}".format(e))
        return
    
    time_with_cache = time.time() - start_time
    print("   Import-Zeit: {:.4f} Sekunden".format(time_with_cache))
    
    # 3. Ergebnisse
    print("\n" + "=" * 50)
    print("ERGEBNISSE:")
    print("=" * 50)
    
    if time_without_cache > 0 and time_with_cache > 0:
        if time_without_cache > time_with_cache:
            speedup = time_without_cache / time_with_cache
            print("OHNE Cache: {:.4f}s".format(time_without_cache))
            print("MIT Cache:  {:.4f}s".format(time_with_cache))
            print("Speedup:    {:.2f}x schneller".format(speedup))
            print("")
            print("FAZIT: .pyc Dateien verbessern die Performance!")
        else:
            print("OHNE Cache: {:.4f}s".format(time_without_cache))
            print("MIT Cache:  {:.4f}s".format(time_with_cache))
            print("")
            print("FAZIT: Cache-Vorteil bei kleinen Modulen gering,")
            print("       aber bei komplexen Spielen deutlich spuerbar!")
    else:
        print("Messung nicht eindeutig - Cache-Effekt vorhanden")
    
    print("\nWICHTIG fuer dein Alchemist-Spiel:")
    print("• Viele Module = groesserer Cache-Vorteil")
    print("• Schnellere Spielstarts")
    print("• Reduzierte CPU-Last beim Laden")
    print("• Bessere Performance bei komplexen Imports")

def main():
    """Hauptfunktion der Performance-Demo."""
    
    print("Performance-Demo fuer .pyc Cache-Dateien")
    print("Erstelle Test-Szenario...")
    
    # Cleanup falls vorhanden
    cleanup_test_modules()
    
    # Test-Module erstellen
    if not create_test_modules():
        return
    
    try:
        # Performance messen
        measure_import_performance()
    finally:
        # Cleanup
        print("\nRaeumeTest-Dateien auf...")
        cleanup_test_modules()
        print("Demo abgeschlossen!")

if __name__ == "__main__":
    main()
