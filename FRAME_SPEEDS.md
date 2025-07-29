# Frame-Geschwindigkeiten Erklärung

## 🎬 Variable Frame-Geschwindigkeiten

### Idle Animation (6 Frames):
```
Frame 1: 400ms × 1.5 = 600ms (sehr langsam - Startposition)
Frame 2: 400ms × 1.0 = 400ms (normal)
Frame 3: 400ms × 0.8 = 320ms (schneller - Übergang)
Frame 4: 400ms × 0.8 = 320ms (schneller - Übergang)
Frame 5: 400ms × 1.0 = 400ms (normal)
Frame 6: 400ms × 1.5 = 600ms (sehr langsam - zurück zu Start)
```

### Run Animation (8 Frames):
```
Frame 1: 200ms × 1.2 = 240ms (langsamer - Schritt beginnt)
Frame 2: 200ms × 0.8 = 160ms (schneller)
Frame 3: 200ms × 0.6 = 120ms (am schnellsten - Bewegung)
Frame 4: 200ms × 0.6 = 120ms (am schnellsten - Bewegung)
Frame 5: 200ms × 0.8 = 160ms (schneller)
Frame 6: 200ms × 1.0 = 200ms (normal)
Frame 7: 200ms × 0.8 = 160ms (schneller)
Frame 8: 200ms × 1.2 = 240ms (langsamer - Schritt endet)
```

## 🎯 Anpassungsmöglichkeiten

Um die Animation weiter zu verfeinern, kannst du die `frame_multipliers` in der `player.py` anpassen:

- **Größere Werte** (z.B. 1.5, 2.0) = Frame wird länger angezeigt
- **Kleinere Werte** (z.B. 0.5, 0.3) = Frame wird kürzer angezeigt

Zum Beispiel für noch langsamere mittlere Frames:
```python
"frame_multipliers": [1.5, 1.2, 0.4, 0.4, 1.2, 1.5]  # Sehr kurze mittlere Frames
```
