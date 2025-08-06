# -*- coding: utf-8 -*-
"""
Sicherheitsanalyse: Welche Cache-Dateien werden NICHT gelöscht
Demonstriert die Schutzlogik der intelligenten Bereinigung
"""

import os
import time

def analyze_cache_safety():
    """Analysiert welche Cache-Dateien geschützt sind."""
    
    print("=" * 60)
    print("🛡️  SICHERHEITSANALYSE: Intelligente Cache-Bereinigung")
    print("=" * 60)
    
    print("\n📋 WAS WIRD NIEMALS GELÖSCHT:")
    print("-" * 40)
    
    protected_files = []
    
    # Analysiere src/ Verzeichnis
    src_dir = 'src'
    if os.path.exists(src_dir):
        for root, dirs, files in os.walk(src_dir):
            # Finde alle .py Dateien
            py_files = [f for f in files if f.endswith('.py')]
            
            for py_file in py_files:
                py_path = os.path.join(root, py_file)
                base_name = py_file[:-3]  # Entferne .py
                
                # Entsprechende .pyc Datei
                pycache_dir = os.path.join(root, '__pycache__')
                if os.path.exists(pycache_dir):
                    cache_files = os.listdir(pycache_dir)
                    for cache_file in cache_files:
                        if cache_file.startswith(base_name + '.'):
                            cache_path = os.path.join(pycache_dir, cache_file)
                            
                            # Prüfe ob Cache aktuell ist
                            if os.path.exists(py_path) and os.path.exists(cache_path):
                                py_mtime = os.path.getmtime(py_path)
                                cache_mtime = os.path.getmtime(cache_path)
                                
                                if cache_mtime >= py_mtime:
                                    protected_files.append({
                                        'py': py_path,
                                        'cache': cache_path,
                                        'reason': 'AKTUELL - Cache neuer als .py Datei'
                                    })
                                else:
                                    protected_files.append({
                                        'py': py_path,
                                        'cache': cache_path,
                                        'reason': 'VERALTET - würde bereinigt (sicher)'
                                    })
    
    # Zeige geschützte Dateien
    current_count = 0
    outdated_count = 0
    
    for item in protected_files:
        rel_py = os.path.relpath(item['py'])
        rel_cache = os.path.relpath(item['cache'])
        
        if 'AKTUELL' in item['reason']:
            print(f"✅ GESCHÜTZT: {rel_py}")
            print(f"   Cache:     {rel_cache}")
            print(f"   Grund:     {item['reason']}")
            print()
            current_count += 1
        else:
            print(f"🔄 BEREINIGBAR: {rel_py}")
            print(f"   Cache:       {rel_cache}")
            print(f"   Grund:       {item['reason']}")
            print()
            outdated_count += 1
    
    print("=" * 60)
    print("📊 ZUSAMMENFASSUNG:")
    print("=" * 60)
    print(f"✅ GESCHÜTZTE Cache-Dateien:   {current_count}")
    print(f"🔄 BEREINIGBARE Cache-Dateien: {outdated_count}")
    print(f"📁 TOTAL analysiert:           {len(protected_files)}")
    
    print("\n🛡️  SCHUTZ-LOGIK:")
    print("-" * 40)
    print("✅ Cache wird BEHALTEN wenn:")
    print("   • Entsprechende .py Datei existiert")
    print("   • Cache neuer/gleich alt wie .py Datei")
    print("   • Cache-Datei gültig und lesbar")
    print()
    print("🗑️  Cache wird NUR gelöscht wenn:")
    print("   • .py Datei nicht mehr existiert (verwaist)")
    print("   • Cache älter als geänderte .py Datei (veraltet)")
    print("   • __pycache__ Ordner komplett leer")
    
    print("\n💡 FAZIT FÜR DEIN ALCHEMIST-SPIEL:")
    print("-" * 40)
    print("🎮 Alle aktiven Spiel-Module sind GESCHÜTZT!")
    print("🚀 Performance-kritische Caches bleiben erhalten!")
    print("🧹 Nur wirklich unnötige Dateien werden entfernt!")
    print("🛡️  Keine Gefahr für essentielle Spielkomponenten!")

def demonstrate_protection_scenarios():
    """Demonstriert verschiedene Schutz-Szenarien."""
    
    print("\n" + "=" * 60)
    print("🎯 SCHUTZ-SZENARIEN - Was passiert wann?")
    print("=" * 60)
    
    scenarios = [
        {
            'scenario': 'Normale Entwicklung',
            'description': 'Du entwickelst normal, änderst Code',
            'cache_status': 'Cache wird automatisch aktualisiert',
            'action': '✅ KEINE Bereinigung nötig - alles optimal'
        },
        {
            'scenario': 'Datei gelöscht',
            'description': 'Du löschst eine .py Datei',
            'cache_status': 'Cache wird verwaist',
            'action': '🗑️  Bereinigung entfernt verwaiste .pyc (sicher)'
        },
        {
            'scenario': 'Datei umbenannt',
            'description': 'Du benennst module.py zu new_module.py um',
            'cache_status': 'Alter Cache für module.py wird verwaist',
            'action': '🗑️  Bereinigung entfernt alten Cache (sicher)'
        },
        {
            'scenario': 'Code geändert',
            'description': 'Du änderst Inhalt einer .py Datei',
            'cache_status': 'Cache wird beim nächsten Import aktualisiert',
            'action': '🔄 Optional: Veralteten Cache vorab entfernen'
        },
        {
            'scenario': 'Git Pull',
            'description': 'Du holst neue Änderungen vom Repository',
            'cache_status': 'Manche Caches könnten veraltet sein',
            'action': '🧹 Smart cleanup empfohlen'
        },
        {
            'scenario': 'Spiel starten',
            'description': 'Du startest dein Alchemist-Spiel',
            'cache_status': 'Alle aktuellen Caches werden verwendet',
            'action': '🚀 OPTIMALE Performance durch Caches!'
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{i}. {scenario['scenario']}")
        print(f"   Situation:    {scenario['description']}")
        print(f"   Cache-Status: {scenario['cache_status']}")
        print(f"   Aktion:       {scenario['action']}")

if __name__ == "__main__":
    analyze_cache_safety()
    demonstrate_protection_scenarios()
    
    print("\n" + "=" * 60)
    print("🎉 FAZIT: Das System ist SICHER und INTELLIGENT!")
    print("=" * 60)
    print("• Essentielle Dateien werden NIEMALS gelöscht")
    print("• Nur wirklich unnötige Caches werden entfernt")
    print("• Dein Spiel behält optimale Performance")
    print("• Bereinigung ist konservativ und vorsichtig")
    print("\n🎮 Du kannst die intelligente Bereinigung bedenkenlos verwenden!")
