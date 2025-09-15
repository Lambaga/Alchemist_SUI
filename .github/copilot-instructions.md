# Copilot Instructions for Alchemist_SUI

## Project Overview
- **Alchemist_SUI** is a Python-based 2D adventure game using Pygame, with hardware integration (ESP32, Raspberry Pi), modular architecture, and multi-platform launcher scripts.
- Main gameplay logic is in `src/`, with subfolders for core systems, entities, managers, UI, and world/map handling.
- Asset management (sprites, sounds, maps) is in `assets/`.
- Hardware and platform-specific scripts are in the project root and `scripts/`.

## Key Components & Data Flow
- **Game Loop:** Entry point is typically in `src/core/main.py`, which initializes game logic, rendering (`GameRenderer`), input, and map loading.
- **Level System:** `src/core/level.py` manages level state, player/NPC interactions, collectibles, and map transitions. Map files are loaded via `MapLoader`.
- **Rendering:** `GameRenderer` in `level.py` handles layered rendering, alpha/transparency caching, and performance optimizations.
- **Input:** Unified input system (`input_system.py`) supports keyboard, gamepad, and hardware (ESP32) with priority and fallback logic.
- **Assets:** Sprites, sounds, and maps are loaded from `assets/`, with asset scaling/caching via `asset_manager.py`.
- **Save System:** Multiple save slots, quick save/load via F9-F12, managed in `level.py` and related modules.

## Developer Workflows
- **Run Game:** Use launcher scripts (`run_game.bat`, `run_game.sh`, etc.) for automatic venv setup and dependency install.
- **Test Hardware:** Use `test_hardware_input.py` after activating venv.
- **Map Editing:** TMX/TSX files in `assets/maps/` must have correct relative paths; all referenced tilesets/images must exist locally.
- **Debugging:** Console output provides detailed error/warning info for map loading, asset issues, and hardware integration.

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
