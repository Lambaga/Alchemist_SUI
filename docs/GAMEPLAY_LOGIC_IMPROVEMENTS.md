# 🧙‍♂️ Gameplay-Logik Verbesserungen - Dokumentation

## Übersicht

Die Gameplay-Logik wurde mit zwei neuen robusten Systemen erweitert:

1. **Alchemie-System**: Strukturiertes, erweiterbares Rezept-Management
2. **Kampfsystem**: Interface-basiertes Combat mit Event-Integration

## 🧪 Alchemie-System (`src/alchemy_system.py`)

### Kernfeatures

- **Typisierte Zutaten**: `IngredientType` Enum für Type Safety
- **Strukturierte Rezepte**: `Recipe` Dataclass mit Metadaten
- **Erweiterbares Design**: Einfaches Hinzufügen neuer Rezepte
- **Score-System**: Punktevergabe pro erfolgreichem Brauen

### Beispiel-Nutzung

```python
from src.alchemy_system import AlchemySystem, IngredientType

# System initialisieren
alchemy = AlchemySystem()

# Zutaten hinzufügen
alchemy.add_ingredient(IngredientType.WATER_CRYSTAL)
alchemy.add_ingredient(IngredientType.FIRE_ESSENCE)

# Trank brauen
recipe = alchemy.brew()
if recipe:
    print(f"Gebraut: {recipe.result_name} (+{recipe.score_value} Punkte)")
```

### Verfügbare Rezepte

| Zutaten | Ergebnis | Punkte |
|---------|----------|--------|
| 2x Wasserkristall | Wasserzauber | 50 |
| Feuer + Wasser | Heiltrank | 75 |
| 2x Feueressenz | Feuerball | 60 |
| 2x Erdkristall | Steinwall | 55 |
| Wasser + Erde | Wachstumstrank | 40 |
| Erde + Feuer | Explosive Mischung | 30 |
| Alle drei Elemente | Universaltrank | 100 |

## ⚔️ Kampfsystem (`src/combat_system.py`)

### CombatEntity Interface

Alle kampffähigen Entities (Player, Enemies) implementieren das `CombatEntity` Interface:

```python
class CombatEntity(ABC):
    @abstractmethod
    def take_damage(self, amount: int, damage_type: DamageType, source: Optional['CombatEntity']) -> bool
    
    @abstractmethod  
    def can_attack(self) -> bool
    
    @abstractmethod
    def get_attack_damage(self) -> int
    
    @abstractmethod
    def get_health(self) -> int
    
    # ... weitere Methoden
```

### Zentrale Kampfverarbeitung

```python
from src.combat_system import CombatSystem

combat_system = CombatSystem(event_manager)

# Angriff verarbeiten
success = combat_system.process_attack(attacker, target, DamageType.FIRE)

# Heilung anwenden
healed = combat_system.heal_entity(player, 30)
```

### Combat-Modifikatoren

Temporäre Buffs/Debuffs für erweiterte Kampfmechaniken:

```python
# Schadens-Buff für 5 Sekunden
damage_buff = CombatModifier("Berserker", damage_multiplier=1.5, duration=5000)
combat_system.add_modifier(player, damage_buff)

# Rüstungs-Buff
armor_buff = CombatModifier("Steinwall", damage_reduction=0.3, duration=3000)
combat_system.add_modifier(player, armor_buff)
```

## 🔗 Event-Integration

Beide Systeme integrieren sich in das bestehende Event-System:

### Kampf-Events

- `PLAYER_DAMAGED`: Spieler erleidet Schaden
- `PLAYER_HEALED`: Spieler wird geheilt  
- `PLAYER_DIED`: Spieler stirbt
- `ENEMY_DEFEATED`: Gegner besiegt

### Alchemie-Events

- `POTION_BREWED`: Trank erfolgreich gebraut
- `POTION_CONSUMED`: Trank verwendet

## 📁 Dateistruktur

```
src/
├── alchemy_system.py      # Neues Alchemie-System
├── combat_system.py       # Neues Kampfsystem  
├── player.py             # Updated: CombatEntity Interface
├── enemy.py              # Updated: CombatEntity Interface
├── game.py               # Updated: AlchemySystem Integration
└── event_manager.py      # Bestehendes Event-System
```

## 🎮 Integration in bestehende Game-Klasse

Die `Game`-Klasse wurde aktualisiert, um das neue Alchemie-System zu verwenden:

```python
# Alte Implementierung (entfernt)
self.rezepte = {...}
self.aktive_zutaten = []

# Neue Implementierung  
self.alchemy_system = AlchemySystem()

# Legacy-Kompatibilität beibehalten
def add_zutat(self, zutat_name):
    ingredient = create_ingredient_from_string(zutat_name)
    success = self.alchemy_system.add_ingredient(ingredient)
    # ... Legacy-Updates für UI-Kompatibilität
```

## 🛠️ Implementierungsdetails

### Player-Klasse Erweiterungen

```python
# Neue Combat-Attribute
self.max_health: int = 100
self.current_health: int = self.max_health  
self.attack_damage: int = 30
self.is_player_alive: bool = True
self.attack_cooldown: int = 1000

# CombatEntity Interface-Methoden
def take_damage(self, amount, damage_type, source) -> bool
def can_attack(self) -> bool
def get_attack_damage(self) -> int
# ... weitere Interface-Methoden
```

### Enemy-Klasse Erweiterungen

```python
# Erweiterte take_damage Methode
def take_damage(self, damage: int, damage_type: DamageType, source: Optional['CombatEntity']) -> bool:
    # Unterstützt jetzt Heilung (negative Werte)
    # Erweiterte Damage-Type Unterstützung
    # Source-Tracking für Event-System
```

## 🎯 Demo-Anwendung

Die Datei `gameplay_logic_demo.py` demonstriert alle neuen Features:

```bash
cd /path/to/Alchemist
python gameplay_logic_demo.py
```

### Demo-Steuerung

- `1, 2, 3`: Zutaten hinzufügen (Wasser, Feuer, Erde)
- `SPACE`: Trank brauen
- `BACKSPACE`: Letzte Zutat entfernen
- `A`: Angriff simulieren
- `H`: Spieler heilen
- `R`: Demo zurücksetzen

## 🔮 Zukünftige Erweiterungen

### Alchemie-System

1. **JSON-Rezept-Dateien**: Externalisierte Rezept-Definitionen
2. **Ingredient-Qualitäten**: Verschiedene Qualitätsstufen für Zutaten
3. **Brauen-Mini-Spiel**: Interaktives Timing-basiertes Brauen
4. **Trank-Effekte**: Direkte Integration mit Gameplay-Systemen

### Kampfsystem

1. **Elementare Resistenzen**: Fire-Entities vs Fire-Damage
2. **Status-Effekte**: Vergiftung, Brennen, Verlangsamung
3. **Kritische Treffer**: Zufalls-basierte Schadens-Multiplikatoren
4. **Combo-System**: Aufeinanderfolgende Angriffe

### Event-System Integration

1. **Achievement-System**: Event-basierte Erfolge
2. **Statistics-Tracking**: Detaillierte Gameplay-Metriken  
3. **Audio-Triggers**: Automatische Sound-Effekte via Events
4. **UI-Updates**: Reactive UI basierend auf Events

## ✅ Kompatibilität

- **Vollständig rückwärtskompatibel** mit bestehender Codebase
- **Legacy-Attribute** bleiben funktional für UI-Integration
- **Schrittweise Migration** möglich
- **Keine Breaking Changes** für bestehende Features

## 🧪 Testing

```python
# Alchemie-System Test
python src/alchemy_system.py

# Kampfsystem Test  
python src/combat_system.py

# Vollständige Integration
python gameplay_logic_demo.py
```

---

*Diese Verbesserungen legen das Fundament für komplexere Gameplay-Mechaniken und bieten eine saubere, erweiterbare Architektur für zukünftige Features.*
