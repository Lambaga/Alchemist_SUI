# Health-Bar System Dokumentation

## Übersicht

Das Health-Bar System ist eine vollständig objektorientierte, wiederverwendbare Komponente, die Health-Bars für alle `CombatEntity`-Objekte im Spiel anzeigt. Es folgt OOP Best Practices und ist einfach erweiterbar.

## Architektur

### 1. HealthBarRenderer (Abstract Base Class)
- **Zweck**: Interface für verschiedene Health-Bar Rendering-Stile
- **Erweiterbarkeit**: Neue Renderer können einfach hinzugefügt werden
- **Methoden**: `render(surface, rect, health_percentage, **kwargs)`

### 2. StandardHealthBarRenderer
- **Features**: 
  - Konfigurierbare Farben (Grün/Gelb/Rot basierend auf Gesundheit)
  - Anpassbare Rahmenbreite
  - Automatische Farbwechsel bei Gesundheitsänderung
- **Verwendung**: Standard für Enemies

### 3. AnimatedHealthBarRenderer
- **Features**:
  - Sanfte Animationen bei Schaden/Heilung
  - Configurable Animation Geschwindigkeit
  - Erbt von StandardHealthBarRenderer
- **Verwendung**: Standard für Player

### 4. HealthBar (Hauptklasse)
- **Features**:
  - Verbindet CombatEntity mit Renderer
  - Automatische Positionierung relativ zur Entity
  - Fade-Out Effekte bei voller Gesundheit
  - Camera-System Integration
  - Sichtbarkeits-Management
- **Konfiguration**:
  - `width`, `height`: Größe der Health-Bar
  - `offset_x`, `offset_y`: Position relativ zur Entity
  - `show_when_full`: Ob bei voller Gesundheit angezeigt
  - `fade_delay`: Zeit bis Fade-Out beginnt

### 5. HealthBarManager
- **Features**:
  - Zentrale Verwaltung aller Health-Bars
  - Automatisches Cleanup toter Entities
  - Batch-Update und Rendering
  - Automatische Renderer-Zuordnung basierend auf Entity-Typ

## Integration ins Spiel

### Level-System Integration
```python
# In Level.__init__()
self.health_bar_manager = HealthBarManager()

# Nach dem Spawnen von Entities
self.setup_health_bars()

# In Level.update()
self.health_bar_manager.update(dt)

# In Level.render()
camera_offset = (self.camera.camera_rect.x, self.camera.camera_rect.y)
self.health_bar_manager.draw_all(self.screen, camera_offset)
```

### Automatisches Enemy Health-Bar Setup
```python
def add_enemy_health_bar(self, enemy):
    enemy_health_bar = create_enemy_health_bar(
        enemy,
        width=60,
        height=8,
        offset_y=-25,
        show_when_full=False,
        fade_delay=2.5
    )
    self.health_bar_manager.add_entity(enemy, ...)
```

## Verwendung

### Player Health-Bar
```python
player_health_bar = create_player_health_bar(
    player,
    width=100,
    height=12,
    offset_y=-35,
    show_when_full=True  # Immer sichtbar
)
```

### Enemy Health-Bar
```python
enemy_health_bar = create_enemy_health_bar(
    enemy,
    width=60,
    height=8,
    offset_y=-25,
    show_when_full=False,  # Nur bei Schaden sichtbar
    fade_delay=2.5
)
```

### Custom Renderer
```python
custom_renderer = StandardHealthBarRenderer(
    health_color_full=(255, 0, 255),  # Magenta
    health_color_medium=(255, 255, 0),  # Gelb
    health_color_low=(255, 0, 0),     # Rot
    border_width=3
)

health_bar = HealthBar(entity, renderer=custom_renderer)
```

## Features

### 1. Automatische Positionierung
- Health-Bars erscheinen automatisch über dem Kopf der Entität
- Berücksichtigt Camera-Transformationen und Zoom
- Anpassbare Offsets für verschiedene Entity-Größen

### 2. Intelligente Sichtbarkeit
- **Player**: Immer sichtbar (konfigurierbar)
- **Enemies**: Nur bei Schaden sichtbar, Fade-Out nach configurable Zeit
- **Dead Entities**: Automatisch ausgeblendet

### 3. Performance-Optimierungen
- Frustum Culling: Health-Bars außerhalb des Sichtbereichs werden nicht gerendert
- Batch-Updates und -Rendering
- Automatisches Cleanup toter Entities

### 4. Animationen
- Sanfte Animationen bei Gesundheitsänderungen
- Unterschiedliche Geschwindigkeiten für Schaden vs. Heilung
- Fade-In/Fade-Out Effekte

### 5. Konfigurierbarkeit
- Anpassbare Farben, Größen, Positionen
- Verschiedene Renderer für verschiedene Entity-Typen
- Flexible Sichtbarkeits-Regeln

## Steuerung

### Im Spiel
- **F2**: Health-Bars ein/ausschalten
- **Automatisch**: Health-Bars erscheinen bei Schaden

### Für Tests
- **T**: Schaden an Spieler
- **Y**: Schaden an Feinde
- **H**: Spieler heilen
- **U**: Feinde heilen
- **R**: Alle auf volle Gesundheit

## Erweiterung

### Neue Renderer hinzufügen
```python
class GlowHealthBarRenderer(HealthBarRenderer):
    def render(self, surface, rect, health_percentage, **kwargs):
        # Custom glow effect implementation
        pass
```

### Neue Features
- **Mana Bars**: Einfach durch Kopieren und Anpassen für Mana-Werte
- **Status Effects**: Zusätzliche Bars für Buffs/Debuffs
- **Damage Numbers**: Floating damage text integration

## Kompatibilität
- **Python 2.7**: `health_bar_py27.py` Version verfügbar
- **Python 3.x**: `health_bar.py` mit Type Hints
- **Pygame**: Kompatibel mit allen gängigen Pygame-Versionen

## Best Practices

1. **Entity Requirements**: Entities müssen das `CombatEntity` Interface implementieren
2. **Performance**: Health-Bar Manager in Level update/render loop integrieren
3. **Cleanup**: Manager entfernt automatisch Health-Bars toter Entities
4. **Customization**: Verwende Convenience-Funktionen für Standard-Setups
5. **Camera Integration**: Stelle sicher, dass korrekte Camera-Offsets verwendet werden

Das Health-Bar System ist jetzt vollständig integriert und funktional! 🎮✅
