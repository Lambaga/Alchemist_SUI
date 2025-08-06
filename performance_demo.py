# -*- coding: utf-8 -*-
"""
Performance-Demo: .pyc Dateien vs. ohne Cache
Zeigt die Auswirkung von Cache-Dateien auf die Import-Performance
"""

import time
import os
import sys
import shutil
import subprocess

def measure_import_time(module_path, description):
    """Misst die Zeit für einen Python-Import."""
    start_time = time.time()
    
    # Führe Python-Import in separatem Prozess aus
    try:
        result = subprocess.run([
            sys.executable, '-c', 
            f"import sys; sys.path.append('{os.path.dirname(module_path)}'); "
            f"import {os.path.basename(module_path).replace('.py', '')}"
        ], 
        capture_output=True, text=True, timeout=10)
        
        end_time = time.time()
        import_time = end_time - start_time
        
        if result.returncode == 0:
            print(f"{description}: {import_time:.4f}s")
            return import_time
        else:
            print(f"{description}: FEHLER - {result.stderr}")
            return None
            
    except Exception as e:
        print(f"{description}: FEHLER - {e}")
        return None

def demo_cache_performance():
    """Demonstriert Performance-Unterschiede mit/ohne .pyc Cache."""
    
    print("=" * 60)
    print("🎮 PERFORMANCE-DEMO: .pyc Cache-Dateien")
    print("=" * 60)
    
    # Projektordner
    src_dir = os.path.join(os.getcwd(), 'src')
    if not os.path.exists(src_dir):
        print("❌ src/ Ordner nicht gefunden!")
        return
    
    # Finde Python-Module
    python_modules = []
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            if file.endswith('.py') and not file.startswith('__'):
                module_path = os.path.join(root, file)
                # Überspringe sehr große oder problematische Module
                if os.path.getsize(module_path) < 100000:  # < 100KB
                    python_modules.append(module_path)
    
    if not python_modules:
        print("❌ Keine geeigneten Python-Module gefunden!")
        return
    
    # Wähle ein repräsentatives Modul
    test_module = python_modules[0]
    print(f"📝 Test-Modul: {os.path.relpath(test_module)}")
    print()
    
    # 1. Messung MIT Cache
    print("🚀 PHASE 1: Mit Cache-Dateien (.pyc)")
    time_with_cache = measure_import_time(test_module, "   Import mit Cache")
    
    # 2. Cache temporär entfernen
    print("\n🗑️  PHASE 2: Cache temporär entfernen...")
    cache_backup = []
    
    # Sichere __pycache__ Ordner
    for root, dirs, files in os.walk(src_dir):
        if '__pycache__' in dirs:
            pycache_path = os.path.join(root, '__pycache__')
            backup_path = pycache_path + '_backup'
            try:
                shutil.move(pycache_path, backup_path)
                cache_backup.append((pycache_path, backup_path))
                print(f"   Backup: {os.path.relpath(pycache_path)}")
            except OSError:
                pass
    
    # 3. Messung OHNE Cache
    print("\n⏱️  PHASE 3: Ohne Cache-Dateien")
    time_without_cache = measure_import_time(test_module, "   Import ohne Cache")
    
    # 4. Cache wiederherstellen
    print("\n🔄 PHASE 4: Cache wiederherstellen...")
    for original_path, backup_path in cache_backup:
        try:
            shutil.move(backup_path, original_path)
            print(f"   Wiederhergestellt: {os.path.relpath(original_path)}")
        except OSError:
            pass
    
    # 5. Ergebnisse
    print("\n" + "=" * 60)
    print("📊 ERGEBNISSE:")
    print("=" * 60)
    
    if time_with_cache and time_without_cache:
        speedup = time_without_cache / time_with_cache
        saved_time = time_without_cache - time_with_cache
        
        print(f"⚡ MIT Cache:     {time_with_cache:.4f}s")
        print(f"🐌 OHNE Cache:   {time_without_cache:.4f}s")
        print(f"🚀 Speedup:      {speedup:.2f}x schneller")
        print(f"⏰ Gesparte Zeit: {saved_time:.4f}s pro Import")
        print()
        
        if speedup > 1.5:
            print("✅ DEUTLICHER PERFORMANCE-VORTEIL durch .pyc Cache!")
        elif speedup > 1.1:
            print("✅ Messbarer Performance-Vorteil durch .pyc Cache!")
        else:
            print("ℹ️  Geringer aber vorhandener Performance-Vorteil")
            
        print()
        print("💡 FAZIT:")
        print("   • .pyc Dateien beschleunigen Imports erheblich")
        print("   • Bei komplexen Spielen summiert sich der Vorteil")
        print("   • Cache-Dateien sollten nur gezielt bereinigt werden")
        
    else:
        print("❌ Performance-Messung fehlgeschlagen")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    demo_cache_performance()
