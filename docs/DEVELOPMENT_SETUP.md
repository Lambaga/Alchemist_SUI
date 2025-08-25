# 🚀 Development Setup Guide

## Quick Start for Developers

### The Modern Way (Recommended)

```bash
# Clone and run in one step:
git clone https://github.com/Lambaga/Alchemist_SUI.git
cd Alchemist_SUI

# Windows
.\run_game.bat  # 🚀 PRIMARY LAUNCH METHOD

# Linux/macOS  
./run_game.sh
```

**Note**: Always use `.\run_game.bat` to start the game - this handles all dependencies and paths automatically!

## Why the Launcher Scripts are Superior

### Technical Benefits

1. **Proper Module Resolution**
   - Uses `python -m core.main` which correctly resolves imports
   - No more manual `sys.path.insert()` hacks
   - Works regardless of current working directory

2. **Absolute Asset Paths**
   - Assets load correctly from `D:\Alchemist\assets\` (absolute paths)
   - No more "missing sprites" issues
   - Works when launched from any directory

3. **Virtual Environment Management**
   - Automatically creates `.venv` if it doesn't exist
   - Always activates the correct environment
   - Prevents dependency conflicts with other projects

4. **Dependency Management**
   - Ensures latest compatible versions are installed
   - Uses `python -m pip` to install into correct environment
   - Handles updates automatically

### Before vs After

**❌ Old Problematic Ways:**
```bash
# These caused issues:
python main.py                     # Wrong file location
cd src && python main.py           # Import errors
python src/main.py                 # Path issues
.\.venv\Scripts\python.exe ...     # Manual, error-prone
```

**✅ New Reliable Way:**
```bash
.\run_game.bat                     # Everything just works
```

## Development Workflow

### Daily Development
```bash
# Just run the launcher - it handles everything
.\run_game.bat  # Windows
./run_game.sh   # Linux/macOS
```

### Code Changes
- Edit files in `src/`
- Launcher scripts automatically use latest code
- No build step needed (Python)

### Adding Dependencies
1. Add package to `requirements.txt`
2. Run launcher script - it auto-installs new dependencies

### Git Workflow
```bash
# Always work on feature branches
git checkout -b feature/my-awesome-feature

# Make changes, test with launcher
.\run_game.bat

# Commit and push
git add .
git commit -m "Add awesome feature"
git push origin feature/my-awesome-feature
```

## File Structure & Module System

```
Alchemist_SUI/
├── run_game.bat           # Windows launcher
├── run_game.sh            # Linux/macOS launcher
├── requirements.txt       # Python dependencies
├── .venv/                 # Virtual environment (auto-created)
├── src/
│   ├── core/
│   │   ├── main.py       # Entry point: python -m core.main
│   │   ├── config.py     # Centralized configuration
│   │   └── ...
│   ├── managers/         # Game managers (assets, saves, etc.)
│   ├── entities/         # Game entities (player, enemies)
│   ├── ui/              # User interface components
│   ├── systems/         # Game systems (magic, input, etc.)
│   └── world/           # World-related code (camera, maps)
└── assets/              # Game assets (sprites, sounds, maps)
    ├── Wizard Pack/     # Player sprites
    ├── Demon Pack/      # Enemy sprites  
    ├── sounds/          # Audio files
    └── maps/           # Tiled map files
```

## Key Technical Details

### Module System
- Entry point: `src/core/main.py`
- Executed via: `python -m core.main` (from `src/` directory)
- Imports work correctly: `from managers.asset_manager import AssetManager`

### Asset Path Resolution
```python
# config.py uses absolute paths:
ASSETS_DIR = path.abspath(path.join(ROOT_DIR, 'assets'))
# Results in: D:\Alchemist\assets\

# This ensures sprites load from correct location regardless of working directory
```

### Virtual Environment
- Name: `.venv` (consistent across platforms)
- Location: Project root directory
- Ignored by Git (each developer has their own)
- Auto-created by launcher scripts

## Troubleshooting

### "Sprites not loading"
✅ **Solution**: Use launcher scripts - they set correct asset paths

### "Import errors"  
✅ **Solution**: Use `python -m core.main` (handled by launcher scripts)

### "pygame not found"
✅ **Solution**: Launcher scripts auto-install dependencies

### "Wrong Python version"
✅ **Solution**: Virtual environment isolates Python version per project

## For New Contributors

1. **Install Python 3.7+**
2. **Clone repository**
3. **Run launcher script**
4. **Start coding!**

The launcher handles all the complex setup. Focus on writing great code! 🚀

## Best Practices

- ✅ Always use launcher scripts for development
- ✅ Never commit `.venv/` directory
- ✅ Add new dependencies to `requirements.txt`
- ✅ Test with launcher before committing
- ✅ Use feature branches for development
- ❌ Don't run Python files directly
- ❌ Don't manually manage virtual environments
- ❌ Don't use relative asset paths in code
