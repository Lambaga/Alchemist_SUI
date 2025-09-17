# Copilot Instructions for Alchemist_SUI

## Project Overview
- **Alchemist_SUI** is a Python-based 2D adventure game using Pygame, with hardware integration (ESP32, Raspberry Pi), modular architecture, and multi-platform launcher scripts.
- Core gameplay logic in `src/`, organized into subfolders:
  - `core/`: Main game loop, level management, config
  - `entities/`: Player, enemies, game objects
  - `managers/`: Asset, save, enemy management
  - `systems/`: Magic, combat, pathfinding
  - `ui/`: Menu system, HUD elements
  - `world/`: Map loading, camera, collision
- Asset management (sprites, sounds, maps) in `assets/`, including character packs and map files
- Hardware and platform-specific scripts in project root and `scripts/`

## Key Components & Data Flow
- **Game Loop:** (`src/core/main.py`)
  - Initializes core systems: display, audio, input
  - Manages game states: menu, gameplay, pause, game over
  - Handles hardware integration and performance monitoring

- **Level System:** (`src/core/level.py`)
  - Controls gameplay state and map transitions
  - Manages entities: player, enemies, collectibles
  - Integrates pathfinding and collision systems
  - Processes save/load requests (F9-F12 slots)

- **Input Architecture:**
  - Priority system: Hardware > Gamepad > Keyboard
  - JSON protocol for ESP32 communication
  - Action abstraction layer for device-agnostic input
  - Automatic fallback on hardware disconnect

- **Rendering Pipeline:**
  - Layered rendering with depth sorting
  - Alpha/transparency caching for performance
  - Camera system with zoom controls
  - HUD elements and status displays

- **State Management:**
  - Menu system for game flow control
  - Save/load system with multiple slots
  - Console debugging output
  - Performance monitoring (FPS tracking)

## Developer Workflows
- **Run Game:** Use platform-specific launchers for automatic venv and dependency setup:
  ```
  # Windows
  run_game.bat         # Standard display
  run_game_7inch.bat   # 7-inch display optimization
  
  # Linux/Raspberry Pi
  ./run_game.sh
  ./run_game_7inch.sh
  ```

- **Test Hardware:**
  ```
  # Enable hardware mode
  set ALCHEMIST_HW=1  # Windows
  export ALCHEMIST_HW=1  # Linux/Pi

  # Test controller
  python test_hardware_input.py
  ```

- **Debug Tools:**
  - F1: Toggle collision visualization
  - F3: Toggle FPS display
  - F4: Switch between simple/detailed FPS view
  - Console for detailed error/warning output

- **Map Editing:** TMX/TSX files must use relative paths; verify all referenced tilesets/images exist

## Project-Specific Patterns
- **Map Transitions:** Level completion triggers (`trigger_level_completion`) show a message and load the next map. Always check for missing tilesets/images in TMX/TSX.
- **Alpha/Transparency:** Use the `_alpha_cache` in `GameRenderer` for performance when rendering sprites with transparency.
- **Input Priority:** Hardware > Gamepad > Keyboard, with automatic fallback and mock mode for development.
- **Error Handling:** Most critical errors (map loading, asset missing) are logged to console; game attempts to continue with degraded features if possible.

## Integration Points
- **Hardware:** ESP32 input via serial JSON protocol; Raspberry Pi compatibility scripts provided.
- **External:** Uses Pygame, pytmx for map loading, and standard Python modules.

## Examples
- **Map Transition:** See `Level.trigger_level_completion()` in `src/core/level.py`.
- **Asset Loading:** See `asset_manager.py` and usage in `GameRenderer`.
- **Input System:** See `input_system.py` for unified input handling.

## Conventions
- All new features should be modular (new files/classes in `src/` subfolders).
- Map and asset paths must be relative and compatible with project structure.
- Console output is the primary debugging tool; add clear messages for new error cases.

---

If any section is unclear or missing important project-specific details, please provide feedback or point to relevant files for further refinement.
