# FPS-Monitoring System 📊

Ein erweiterte FPS-Anzeige und Performance-Tracking System für "Der Alchemist".

## Features ✨

### Echtzeit FPS-Anzeige
- **Live FPS**: Aktuelle Framerate in Echtzeit
- **Frame-Time**: Millisekunden pro Frame
- **Durchschnitt**: Gemittelte FPS über Zeit
- **Min/Max**: Niedrigste und höchste gemessene FPS

### Frame-Drop Detektion 🚨
- Automatische Erkennung von Performance-Problemen
- Warnung bei konsekutiven Frame-Drops
- Farbkodierte Performance-Bewertung:
  - 🟢 **Grün**: Excellent (>90% Ziel-FPS)
  - 🟡 **Gelb**: Good (70-90% Ziel-FPS) 
  - 🟠 **Orange**: Poor (50-70% Ziel-FPS)
  - 🔴 **Rot**: Critical (<50% Ziel-FPS)

### Performance-Metriken 📈
- Frame-Time Verlauf
- Konsekutive Frame-Drops Zähler
- Performance-Rating System
- Historische Daten (60 Frames)

## Steuerung 🎮

### Im Spiel
- **F3**: FPS-Anzeige ein/ausschalten
- **F4**: Wechsel zwischen einfacher/detaillierter Anzeige
- **F5**: Statistiken zurücksetzen
- **F6**: Performance-Zusammenfassung in Konsole ausgeben

### FPS-Demo
```bash
python fps_demo.py
```
- **SPACE**: Wechsel zwischen Performance-Test Modi
- **F4**: Detail-Toggle
- **ESC**: Beenden

## Integration 🔧

### In eigenen Code einbinden:

```python
from src.fps_monitor import FPSMonitor, create_detailed_fps_display

# Einfache FPS-Anzeige
fps_monitor = create_simple_fps_display(position=(10, 10))

# Detaillierte Anzeige mit allen Metriken
fps_monitor = create_detailed_fps_display(position=(10, 10))

# In der Hauptschleife:
def game_loop():
    dt = clock.tick(60) / 1000.0
    fps = clock.get_fps()
    
    # FPS-Monitor aktualisieren
    fps_monitor.update(fps, dt)
    
    # Spiel aktualisieren
    game.update(dt)
    
    # Rendern
    screen.fill((0, 0, 0))
    game.draw(screen)
    
    # FPS-Anzeige zeichnen
    fps_monitor.draw(screen)
    
    pygame.display.flip()
```

## Konfiguration ⚙️

### FPSMonitor Parameter:
```python
fps_monitor = FPSMonitor(
    position=(10, 10),          # Position auf Bildschirm
    font_size=24,               # Schriftgröße
    show_detailed=True,         # Detaillierte Metriken
    history_size=60             # Anzahl gespeicherter Frames
)
```

### Ziel-FPS setzen:
```python
fps_monitor.set_target_fps(60)  # Für Frame-Drop Detektion
```

## Performance-Analyse 🔍

### Typische Ursachen für Frame-Drops:

1. **Zu viele Sprites**: Reduzierung der gezeichneten Objekte
2. **Ineffiziente Kollisionserkennung**: Spatial Hashing nutzen
3. **Große Animationen**: Kleinere Sprite-Größen verwenden
4. **CPU-intensive Berechnungen**: Auf mehrere Frames verteilen
5. **Speicher-Lecks**: Nicht benötigte Objekte freigeben

### Debug-Workflow:

1. **FPS-Monitor aktivieren** (F3)
2. **Detaillierte Anzeige einschalten** (F4)
3. **Performance-kritische Bereiche identifizieren**
4. **Frame-Drop Warnungen beachten**
5. **Statistiken analysieren** (F6)

## Test-Modi (fps_demo.py) 🧪

### Verfügbare Performance-Tests:

1. **Normal**: Baseline-Performance
2. **Lag-Spikes**: Simulierte periodische Verzögerungen
3. **CPU-intensive**: Schwere mathematische Berechnungen
4. **Many Objects**: Viele bewegte Objekte (Rendering-Stress)
5. **Memory Stress**: Speicher-Allokations-Test

### Demo starten:
```bash
cd /path/to/alchemist
python fps_demo.py
```

## Ausgabe-Beispiel 📝

### Konsolen-Output:
```
📊 PERFORMANCE SUMMARY 📊
========================================
Aktuelle FPS: 58.3
Durchschnitt: 59.1
Min/Max: 45/60
Frame-Zeit: 17.2ms
Frame-Drops: 0
Bewertung: Good
Gesamt-Frames: 3540
Laufzeit: 59.8s
========================================
```

### Visuelle Anzeige:
```
FPS: 58.3        [Grüne Zahl]
Frame: 17.2ms    [Weiße Zahl]
Avg: 59.1        [Weiße Zahl]
Min/Max: 45/60   [Weiße Zahl]
```

## Fehlerbehebung 🛠️

### Import-Fehler:
```python
# Stelle sicher, dass der src/ Ordner im Python-Pfad ist
import sys
sys.path.append('path/to/alchemist')
from src.fps_monitor import FPSMonitor
```

### Schlechte Performance:
1. Prüfe die Frame-Drop Warnungen
2. Reduziere die Anzahl der Sprites
3. Optimiere Kollisionserkennung
4. Nutze das Spatial Hashing System

### FPS-Anzeige nicht sichtbar:
1. Prüfe Position (nicht außerhalb des Bildschirms)
2. Prüfe ob `show_fps = True`
3. Prüfe Schriftgrößen-Einstellungen

## Erweiterungen 🚀

### Geplante Features:
- [ ] Performance-Profiling Logs
- [ ] Automatische Performance-Optimierung
- [ ] GPU-Metriken (falls verfügbar)
- [ ] Performance-Vergleiche zwischen Sessions
- [ ] Export von Metriken zu CSV

### Custom Metriken hinzufügen:
```python
# Eigene Performance-Metriken
class CustomFPSMonitor(FPSMonitor):
    def draw_custom_metrics(self, surface):
        # Eigene Metriken hier implementieren
        pass
```

---

Das FPS-Monitoring System hilft dabei, Performance-Probleme schnell zu identifizieren und zu beheben! 🎯
