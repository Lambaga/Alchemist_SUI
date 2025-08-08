# 🧙‍♂️ Der Alchemist

A Python-based 2D adventure game built with Pygame where you play as an alchemist collecting ingredients and brewing potions.

## 🎮 Game Features

- **Character Control**: Move with arrow keys or WASD
- **Alchemy System**: Collect ingredients (1, 2, 3 keys) and brew potions (Space)
- **Enemy System**: Battle demons and fire worms with AI behavior
- **Map System**: Tiled map integration with collision detection
- **Camera System**: Dynamic camera with zoom controls
- **Audio**: Background music and sound effects

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

| Key | Action |
|-----|--------|
| `←→↑↓` or `WASD` | Move character |
| `1, 2, 3` | Collect ingredients |
| `Space` | Brew potion |
| `Backspace` | Remove last ingredient |
| `+/-` | Zoom in/out |
| `R` | Reset game |
| `M` | Toggle music |
| `F1` | Toggle collision debug |
| `ESC` | Exit game |

## 📁 Project Structure

```
Alchemist/
├── src/           # Source code
│   ├── core/      # Core game modules
│   │   ├── main.py    # Main game entry point
│   │   ├── game.py    # Core game logic
│   │   └── ...        # Other core modules
│   ├── entities/  # Game entities (player, enemies)
│   ├── managers/  # Game managers (assets, saves)
│   └── ...        # Other game modules
├── assets/        # Game assets
│   ├── Wizard Pack/    # Player sprites
│   ├── Demon Pack/     # Enemy sprites
│   ├── maps/           # Tiled maps
│   └── sounds/         # Audio files
├── docs/          # Documentation
└── scripts/       # Utility scripts
```

## 🛠️ Development

### Main Entry Point

The main game entry point is located at `src/core/main.py`. Run the game using:
- Windows: `python -m core.main` (from inside src directory)
- Linux/macOS: `python3 -m core.main` (from inside src directory)

### Dependencies

- **pygame**: Main game engine
- **pytmx**: Tiled map loading support

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

**Why this matters**: The launcher scripts solve ALL the common setup issues automatically.

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
