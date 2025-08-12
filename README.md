# 🧙‍♂️ Der Alchemist

A Python-based 2D adventure game built with Pygame where you play as an alchemist mastering elemental magic and battling monsters.

## 🎮 Game Features

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
.\run_game.bat
```

**Linux/macOS:**
```bash
./run_game.sh
```

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
| `1-6` | Cast spells from spell bar |
| `Backspace` | Clear selected elements |

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
├── run_game.bat   # Windows launcher
├── run_game.sh    # Linux/macOS launcher
└── requirements.txt # Python dependencies
```

## 🛠️ Development & Advanced Usage

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

## 🎯 **For Your Friends/New Contributors**

**The Golden Rule**: Always start with the launcher scripts!

```bash
# ✅ CORRECT way (everything works automatically):
git clone <repo>
cd Alchemist_SUI
.\run_game.bat  # Windows
# or
./run_game.sh   # Linux/macOS

# ❌ WRONG ways (will cause problems):
python main.py
python src/main.py  
cd src && python main.py
python -m main
```

**Why this matters**: The launcher scripts solve ALL the common setup issues automatically and ensure proper initialization of all game systems including the magic system, spell bar, and asset loading.

### System Requirements

- **OS**: Windows 10+, macOS 10.14+, or Linux
- **Python**: 3.7 or higher
- **RAM**: 512MB minimum
- **Graphics**: Any graphics card with OpenGL support

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
