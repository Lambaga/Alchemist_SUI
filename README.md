# 🧙‍♂️ Der Alchemist

A Python-based 2D adventure game built with Pygame where you play as an alchemist mastering elemental magic and battling mons## 🎯 Game Controls

### Movement & Basic Actions
| Key | Action |
|-----|--------|
| `W A S D` or `←→↑↓` | Move character |
| `Mouse` | Control look direction |
| `Left Click` | Attack/Fireball |
| `Space` | Attack/Cast selected spell |
| `ESC` | Pause menu |

### Magic System
| Key | Action |
|-----|--------|
| `1` | Select Water element |
| `2` | Select Fire element |
| `3` | Select Stone element |
| `1-6` | Cast spells from spell bar |
| `Backspace` | Clear selected elements |

### 🔌 Hardware-Steuerung (ESP32)

**🎮 Hardware-Setup:**
- **1x Analog-Joystick**: Bewegung (X/Y-Achse)
- **5x Buttons**: 
  - B1 = Feuer-Element (🔥)
  - B2 = Wasser-Element (💧) 
  - B3 = Stein-Element (🗿)
  - B4 = Zauber ausführen (✨)
  - B5 = Kombination löschen (🧹)

**🔧 Aktivierung:**
```bash
# Hardware-Modus aktivieren
export ALCHEMIST_HW=1

# Spiel starten
./run_game.sh
```

**📡 Protokoll (Option B - Serial JSON):**
```json
{"type":"PING","fw":"1.0"}
{"type":"BUTTON","id":"FIRE","state":1}
{"type":"BUTTON","id":"FIRE","state":0}
{"type":"JOYSTICK","x":0.18,"y":-0.62}
{"type":"HEARTBEAT"}
```

**🔌 ESP32 Pin-Mapping:**
- **Digitale Pins**: 5 Buttons mit Debounce (10-20ms)
- **Analoge Pins**: Joystick X/Y (ADC mit Deadzone & Mittelwert)
- **Serial**: 115200 Baud USB/UART
- **Heartbeat**: 1s Intervall für Verbindungsüberwachung

**⚡ Features:**
- ✅ **Input-Priorität**: Hardware > Gamepad > Keyboard
- ✅ **Automatischer Fallback** bei Hardware-Timeout (3s)
- ✅ **Thread-sichere** Kommunikation
- ✅ **Deadzone-Filterung** für Joystick-Rauschen
- ✅ **Edge-Detection** für Buttons (nur Änderungen senden)
- ✅ **Mock-Mode** für Entwicklung ohne Hardware

**🧪 Hardware testen:**
```bash
# Aktiviere venv und teste Hardware-System
.\.venv\Scripts\Activate.ps1
python test_hardware_input.py
``` Features

- **Character Control**: Move with arrow keys or WASD, mouse for direction
- **Magic System**: Combine elements (Fire, Water, Stone) to cast powerful spells
- **Spell Bar**: 6-slot spell bar with individual cooldowns and animations
- **Health System**: Visual health bars for player and enemies
- **Combat System**: Battle demons and fire worms with strategic magic combat
- **Mana System**: Manage mana resources for spell casting
- **Enemy System**: AI-driven enemies with different behaviors
- **Map System**: Tiled map integration with collision detection
- **Camera System**: Dynamic camera with zoom controls
- **Audio**: Background music and sound effects
- **Save System**: Multiple save slots (F9-F12) with quick save/load
- **Performance Monitoring**: Built-in FPS monitoring and optimization tools

## 🚀 Quick Start

### Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

### Installation & Running

**🎯 Option 1: Use the automated scripts (RECOMMENDED)**

The launcher scripts handle everything automatically - virtual environment creation, dependency installation, and correct game startup.

**Windows:**
```bash
.\run_game.bat      # Standard-Modus (1280x720)
.\run_game_7inch.bat # 7-Zoll Monitor (1024x600)
```

**Linux/macOS:**
```bash
./run_game.sh       # Standard-Modus (1280x720)
./run_game_7inch.sh # 7-Zoll Monitor (1024x600)
```

**🥧 Raspberry Pi (mit 7-Zoll Display):**
```bash
# 1. System-Updates (wichtig für Pi)
sudo apt update && sudo apt upgrade -y

# 2. Python und Git installieren (falls noch nicht vorhanden)
sudo apt install python3 python3-pip python3-venv git -y

# 3. SDL2 Abhängigkeiten für Pygame installieren
sudo apt install python3-dev libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev -y

# 4. Repository klonen und zum Verzeichnis wechseln
git clone https://github.com/Lambaga/Alchemist_SUI.git
cd Alchemist_SUI

# 5. Ausführbar machen
chmod +x run_game_7inch.sh

# 6. Spiel für 7-Zoll Monitor starten
./run_game_7inch.sh
```

**🔧 Raspberry Pi Konfiguration für optimale Performance:**
```bash
# GPU Memory auf 128MB setzen (für bessere Grafik-Performance)
sudo raspi-config
# → Advanced Options → Memory Split → 128

# Oder direkt in /boot/config.txt:
echo "gpu_mem=128" | sudo tee -a /boot/config.txt

# 7-Zoll Display Auflösung forcieren (falls Auto-Erkennung fehlschlägt)
echo "hdmi_group=2" | sudo tee -a /boot/config.txt
echo "hdmi_mode=87" | sudo tee -a /boot/config.txt
echo "hdmi_cvt=1024 600 60 6 0 0 0" | sudo tee -a /boot/config.txt

# Nach Änderungen neu starten
sudo reboot
```

**📱 7-Zoll Monitor Support:**
- 🎯 **Raspberry Pi optimiert**: Automatische Hardware-Erkennung
- 📱 **1024x600 Auflösung**: Speziell für 7-Zoll Displays angepasst  
- ⚡ **Performance**: 45 FPS für flüssiges Gameplay auf RPi4
- 🖼️ **Vollbild-Modus**: Optimale Bildschirmnutzung
- 🎨 **UI-Skalierung**: Kompakte, lesbare Oberfläche
- 🔧 **Smart Cache**: Reduzierte Speichernutzung
- 🎵 **Audio**: Angepasste Audio-Einstellungen für Pi

**What the scripts do:**
1. ✅ Check if `.venv` virtual environment exists, create if needed
2. ✅ Activate the virtual environment automatically  
3. ✅ Install/update all dependencies (pygame, pytmx, etc.)
4. ✅ Run the game with correct module paths: `python -m core.main`
5. ✅ Ensure assets load properly with absolute paths

**🔧 Option 2: Manual setup (for developers who want control)**

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Lambaga/Alchemist_SUI.git
   cd Alchemist_SUI
   ```

2. **Create and activate virtual environment:**
   ```bash
   # Windows
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   
   # Linux/macOS
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   # Windows
   python -m pip install -r requirements.txt
   
   # Linux/macOS
   python3 -m pip install -r requirements.txt
   ```

4. **Run the game:**
   ```bash
   cd src
   # Windows
   python -m core.main
   
   # Linux/macOS
   python3 -m core.main
   ```

## ⚡ **Why Use the Launcher Scripts?**

| Old Manual Way | New Launcher Scripts |
|----------------|---------------------|
| ❌ Manual venv creation | ✅ Automatic venv management |
| ❌ Remember to activate | ✅ Always activates correctly |
| ❌ Manual dependency install | ✅ Auto-installs/updates deps |
| ❌ Import/path issues | ✅ Correct module resolution |
| ❌ Platform-specific commands | ✅ Works on all platforms |
| ❌ Asset loading problems | ✅ Absolute asset paths |
| ❌ Complex for new developers | ✅ One command = everything works |

## 🎯 Game Controls

### Movement & Basic Actions
| Key | Action |
|-----|--------|
| `W A S D` or `←→↑↓` | Move character |
| `Mouse` | Control look direction |
| `Left Click` | Attack/Fireball |
| `Space` | Attack/Cast selected spell |
| `ESC` | Pause menu |

### Magic System
| Key | Action |
|-----|--------|
| `1` | Select Water element |
| `2` | Select Fire element |
| `3` | Select Stone element |
| `C` or `Space` | Cast spell |
| `Backspace` or `X` | Clear selected elements |

### 🔌 Hardware Controller (ESP32 + Joystick + 5 Buttons)

**Physical Layout:**
- 1 Analog Joystick (X/Y movement)
- 5 Buttons:
  - **B1 (Fire)**: Select Fire element
  - **B2 (Water)**: Select Water element  
  - **B3 (Stone)**: Select Stone element
  - **B4 (Cast)**: Cast current spell
  - **B5 (Clear)**: Clear element selection

**Protocol (Serial JSON over USB):**
```json
{"type":"BUTTON","id":"FIRE","state":1}    // Button press
{"type":"BUTTON","id":"FIRE","state":0}    // Button release
{"type":"JOYSTICK","x":0.18,"y":-0.62}     // Analog movement
{"type":"HEARTBEAT"}                        // Keep-alive
```

**Hardware Priority:** Hardware > Gamepad > Keyboard (automatic fallback)

### Interface & Debug
| Key | Action |
|-----|--------|
| `H` | Toggle hotkey display |
| `Tab` | Inventory (when available) |
| `M` | Toggle music |
| `+/-` | Zoom in/out |
| `R` | Reset game |

### Save System
| Key | Action |
|-----|--------|
| `F9-F12` | Save to slots 1-4 |
| `Shift + F9-F12` | Delete save slots 1-4 |

### Debug Controls
| Key | Action |
|-----|--------|
| `F1` | Toggle collision debug |
| `F2` | Toggle health bars |
| `F3` | Toggle FPS display |
| `F4` | Toggle detailed FPS info |
| `F5` | Reset performance stats |
| `F6` | Show performance summary |
| `F7` | Magic system test |
| `F8` | Fire + Healing test |

## 🧙‍♂️ Magic System

### Element Combinations
- **Fire + Fire** → Fireball (projectile)
- **Water + Water** → Water Bolt (anti-fire damage)
- **Stone + Stone** → Shield (temporary invulnerability)
- **Fire + Water** → Healing (restore HP)
- **Fire + Stone** → Whirlwind (area attack)
- **Water + Stone** → Invisibility (stealth mode)

## 📁 Project Structure

```
Alchemist/
├── src/           # Source code
│   ├── core/      # Core game modules
│   │   ├── main.py    # Main game entry point
│   │   ├── game.py    # Core game logic
│   │   ├── level.py   # Level management
│   │   └── config.py  # Game configuration
│   ├── entities/  # Game entities (player, enemies)
│   ├── managers/  # Game managers (assets, saves)
│   ├── systems/   # Game systems (magic, combat, etc.)
│   ├── ui/        # User interface components
│   └── world/     # World and map related code
├── assets/        # Game assets
│   ├── Wizard Pack/    # Player sprites
│   ├── Demon Pack/     # Enemy sprites
│   ├── fireWorm/       # Fire worm sprites
│   ├── maps/           # Tiled maps (.tmx files)
│   ├── sounds/         # Audio files
│   └── ui/             # UI assets and spell icons
├── docs/          # Documentation
├── scripts/       # Utility scripts and tools
├── saves/         # Save game files
├── run_game.bat   # Windows launcher (Standard)
├── run_game.sh    # Linux/macOS launcher (Standard)
├── run_game_7inch.bat  # Windows launcher (7-Zoll Monitor)
├── run_game_7inch.sh   # Linux/Pi launcher (7-Zoll Monitor)
├── test_7inch_display.py # Test-Script für 7-Zoll Optimierungen
└── requirements.txt # Python dependencies
```

## 🛠️ Development & Advanced Usage

### Hardware Controller Development

**🔌 ESP32 Setup (für externe Hardware-Steuerung):**
```bash
# 1. ESP32 Development Setup
# Install Arduino IDE or PlatformIO
# Install ESP32 board package

# 2. Hardware Configuration
# Pins: 5 digital inputs (buttons) + 2 analog (joystick X/Y)  
# Debounce: 10-20ms software debounce
# USB Serial: 115200 baud, JSON protocol

# 3. Test mit Mock Mode
python test_hardware_input.py

# 4. Connect echte Hardware
# In src/core/config.py: HARDWARE_CONFIG['mock_mode'] = False
```

**Hardware Pin-Mapping (ESP32 Beispiel):**
```cpp
// Button Pins (Digital Input mit Pull-up)
#define BUTTON_FIRE    12  // B1 = Fire
#define BUTTON_WATER   14  // B2 = Water  
#define BUTTON_STONE   27  // B3 = Stone
#define BUTTON_CAST    26  // B4 = Cast
#define BUTTON_CLEAR   25  // B5 = Clear

// Joystick Pins (Analog Input)
#define JOYSTICK_X     34  // ADC1_CH6 (X-Axis)
#define JOYSTICK_Y     35  // ADC1_CH7 (Y-Axis)
```

**Protokoll Implementation:**
```cpp
// Sende nur bei Änderungen (Edge-Detection + Delta > 0.05)
void sendButtonEvent(String buttonId, int state) {
  JsonDocument doc;
  doc["type"] = "BUTTON";
  doc["id"] = buttonId; 
  doc["state"] = state;
  serializeJson(doc, Serial);
  Serial.println();
}

void sendJoystickEvent(float x, float y) {
  JsonDocument doc;
  doc["type"] = "JOYSTICK";
  doc["x"] = x;
  doc["y"] = y; 
  serializeJson(doc, Serial);
  Serial.println();
}
```

### Main Entry Point

The main game entry point is located at `src/core/main.py`. Run the game using:
- Windows: `python -m core.main` (from inside src directory)
- Linux/macOS: `python3 -m core.main` (from inside src directory)

### Cache Management

The project includes smart cache management tools:

```bash
# Smart cleanup (removes only orphaned/outdated cache)
python smart_cache_cleaner.py --mode=smart

# Remove only orphaned .pyc files
python smart_cache_cleaner.py --mode=orphaned --verbose

# Remove only outdated .pyc files
python smart_cache_cleaner.py --mode=outdated --verbose

# Traditional full cleanup
python clean_cache_simple.py
```

### Performance Testing

```bash
# Run performance benchmarks
python performance_demo.py

# Simple performance test
python simple_performance_demo.py
```

### Testing Tools

```bash
# Test magic system
python test_magic.py
python test_magic_direct.py

# Test mana system
python test_mana_system.py

# Test spell cooldowns
python test_spell_cooldown.py

# 🔌 NEW: Test hardware input system
python test_hardware_input.py

# Test 7-inch display optimizations  
python test_7inch_display.py
```

### Dependencies

- **pygame**: Main game engine (≥2.0.0)
- **pytmx**: Tiled map loading support (≥3.21.7)

### Game Systems

- **Magic System**: Elemental combination system with 6 different spells
- **Spell Bar**: UI component with cooldown animations and key bindings
- **Health System**: Visual health bars for all entities
- **Mana System**: Resource management for magic spells
- **Combat System**: Turn-based combat with buffs/debuffs
- **Save System**: Multiple save slots with automatic backup
- **Performance Monitoring**: FPS tracking and optimization tools
- **🔌 Hardware Input System**: ESP32-based physical controls with analog joystick and buttons

### Input Architecture

**🎯 Action System**: Zentrale Abstraktionsschicht für alle Input-Quellen
- **Input-Priorität**: Hardware > Gamepad > Keyboard
- **Automatischer Fallback**: Bei Hardware-Timeout zu Tastatur/Gamepad
- **Thread-sichere Events**: Async Hardware-Kommunikation
- **Abstrakte Actions**: `magic_fire`, `magic_water`, `cast_magic`, etc.

**📱 Universal Input System**: Multi-Device Support
- **Tastatur**: WASD/Arrow Keys + Magic Keys (1,2,3)  
- **Gamepad**: Xbox/PS4 Controller mit Button-Mapping
- **Hardware**: ESP32 mit Joystick und 5 Physical Buttons

**🔌 Hardware Integration**: 
- **Serial JSON Protocol**: Zeilenbasiert, Event-driven
- **Mock Mode**: Entwicklung ohne Hardware möglich
- **Auto-Reconnect**: Automatische Wiederverbindung
- **Performance**: < 10ms Latenz, 60 FPS kompatibel
- **🔌 Hardware Input System**: ESP32 joystick + buttons support with automatic fallback

### Development Tools

- **Smart Cache Cleaner**: Intelligent Python cache management
- **Performance Demo**: Benchmark and optimization tools
- **Raspberry Pi Support**: Cross-platform compatibility testing

### Asset Credits

- Wizard sprites: Custom sprite pack
- Demon sprites: Custom demon pack
- Fire worm sprites: Custom enemy pack
- Maps: Created with Tiled Map Editor

## 🐛 Troubleshooting

### Common Issues

1. **"pygame not found"**: 
   - ✅ **Solution**: Use the launcher scripts (`.\run_game.bat` or `./run_game.sh`)
   - The scripts automatically install all dependencies

2. **"No module named 'core'"**: 
   - ✅ **Solution**: Always use the launcher scripts, don't run Python files directly
   - The scripts use the correct module execution: `python -m core.main`

3. **Black screen or missing graphics**: 
   - ✅ **Solution**: Use the launcher scripts - they set up absolute asset paths correctly
   - ❌ **Don't**: Run `python main.py` or similar commands directly
   - ✅ **Do**: Use `.\run_game.bat` (Windows) or `./run_game.sh` (Linux/macOS)

4. **"Assets not found" or sprite loading issues**:
   - ✅ **Root cause**: The launcher scripts fix asset path resolution
   - The game now uses absolute paths like `D:\Alchemist\assets\` instead of relative paths
   - Starting the game any other way can break asset loading

5. **Import errors or module not found**:
   - ✅ **Solution**: The launcher scripts handle Python path setup correctly
   - Uses proper module execution with `python -m core.main` from the right directory

6. **Audio issues**: 
   - Ensure your system has audio drivers installed and pygame.mixer is working
   - The launcher scripts load audio from the correct absolute paths

7. **Magic spells not working**:
   - Press `1, 2, 3` to select elements, then `Space` or spell hotkeys to cast
   - Check mana levels - spells require mana to cast
   - Use `H` to toggle hotkey display for reference

8. **Performance issues**:
   - Use `F3` to monitor FPS
   - Run cache cleanup tools: `python smart_cache_cleaner.py --mode=smart`
   - Check system requirements and close other applications

9. **Raspberry Pi 7-Zoll Display Probleme**:
   - ✅ **System-Vorbereitung**: Installiere SDL2-Bibliotheken: `sudo apt install python3-dev libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev -y`
   - ✅ **GPU Memory**: Setze GPU-Speicher auf min. 128MB: `sudo raspi-config` → Advanced Options → Memory Split → 128
   - ✅ **Display-Konfiguration**: Für 7-Zoll Displays in `/boot/config.txt`:
     ```
     hdmi_group=2
     hdmi_mode=87
     hdmi_cvt=1024 600 60 6 0 0 0
     gpu_mem=128
     ```
   - ✅ **Automatische Erkennung**: Das Spiel erkennt 7-Zoll Displays automatisch
   - ✅ **Manuell erzwingen**: `export ALCHEMIST_SMALL_SCREEN=1` vor dem Start
   - ✅ **Performance**: Nutze immer `./run_game_7inch.sh` für beste Performance
   - ✅ **Audio**: ALSA-Konfiguration: `sudo apt install alsa-utils -y && alsamixer`
   - ✅ **Display prüfen**: `tvservice -s` für aktuelle Auflösung, `vcgencmd get_mem gpu` für GPU-Speicher

10. **Virtuelle Umgebung Probleme**:
    - ✅ **Windows**: Nutze `.\run_game.bat` oder `.\run_game_7inch.bat`
    - ✅ **Linux/Pi**: Nutze `./run_game.sh` oder `./run_game_7inch.sh`
    - Die Scripts erstellen und verwalten die .venv automatisch
    - Keine manuelle venv-Aktivierung nötig

## 🎯 **For Your Friends/New Contributors**

**The Golden Rule**: Always start with the launcher scripts!

```bash
# ✅ CORRECT way (everything works automatically):
git clone <repo>
cd Alchemist_SUI

# Windows:
.\run_game.bat          # Standard
.\run_game_7inch.bat    # 7-Zoll

# Linux/macOS/Raspberry Pi:
./run_game.sh           # Standard
./run_game_7inch.sh     # 7-Zoll (Pi optimiert)

# ❌ WRONG ways (will cause problems):
python main.py
python src/main.py  
cd src && python main.py
python -m main
```

**🥧 Für Raspberry Pi Benutzer:** Nutzt immer `./run_game_7inch.sh` - das Script erkennt automatisch die Pi-Hardware und verwendet optimierte Einstellungen!

**Why this matters**: The launcher scripts solve ALL the common setup issues automatically and ensure proper initialization of all game systems including the magic system, spell bar, and asset loading.

### System Requirements

**Desktop/Laptop:**
- **OS**: Windows 10+, macOS 10.14+, or Linux
- **Python**: 3.7 or higher
- **RAM**: 512MB minimum
- **Graphics**: Any graphics card with OpenGL support

**🥧 Raspberry Pi (empfohlen für 7-Zoll Displays):**
- **Model**: Raspberry Pi 4B (4GB RAM empfohlen, 2GB minimum)
- **OS**: Raspberry Pi OS (64-bit empfohlen) oder Ubuntu für Pi
- **Display**: 7-Zoll Display mit 1024x600 Auflösung
- **SD-Karte**: Class 10, min. 16GB (32GB empfohlen)
- **Kühlung**: Passiver Kühlkörper oder Lüfter für längere Sessions
- **GPU-Speicher**: Min. 128MB (in raspi-config eingestellt)

## 📄 License

This project is for educational and personal use. Asset credits belong to their respective creators.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📧 Contact

Project Link: [https://github.com/Lambaga/Alchemist_SUI](https://github.com/Lambaga/Alchemist_SUI)
