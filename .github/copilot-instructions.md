# Copilot Instructions for Alchemist_SUI

These instructions make AI agents productive quickly in this repo. Keep answers concrete and code-referenced; prefer repo conventions over generic advice.

## Architecture Overview
- Core in `src/` with these boundaries:
  - `core/`: Entry point and state machine. `main.py` owns the window, music, FPS monitor, menu orchestration, and transitions between `GameState`s (MAIN_MENU, GAMEPLAY, PAUSE, GAME_OVER).
  - `world/`: Maps/camera/collision; TMX loading via pytmx.
  - `entities/`: Player/enemies and projectiles; all use `AssetManager` for sprites.
  - `systems/`: Input, magic, action-system adapters, cooldowns, pathfinding.
  - `ui/`: Menu system, hotkey HUD, element mixer and on-screen bars.
  - `managers/`: Assets, saves, settings, enemy management.
- Rendering flow: `Game.draw()` → `Level.render()` → layered world + UI; FPS/Hotkeys/Element mixer drawn last.
- Save system: `save_manager` with auto-slot and slots 1-4; integrated in menus and gameplay.

## Run/Debug Workflows
- Windows launchers (create venv, install deps, run):
  - `run_game.bat` → runs `python -m core.main` from `src/`.
  - `run_game_7inch.bat` → sets `ALCHEMIST_SMALL_SCREEN=1` and optimizes for 1024x600.
- Linux/RPi equivalents: `run_game.sh`, `run_game_7inch.sh`.
- Useful tasks (VS Code): Smart cache cleaners and “Run Game (BAT)”.
- Hardware mode: set `ALCHEMIST_HW=1` (optionally `ALCHEMIST_HW_PORT`) before launch to prefer ESP32 input; auto-falls back to keyboard/gamepad.

## Input Model
- Priority: Hardware > Gamepad > Keyboard via `systems/input_system.py` (universal abstraction).
- Action System: If available, initialized in `core/main.py`; hardware adapter created via `systems/hardware_input_adapter`.
- In gameplay, element keys 1-3 are intercepted by `Game.handle_events` to avoid double-processing in `Level`.

## Menus & States
- `ui/menu_system.py` defines `GameState` and state screens (Main, Settings, Load, Pause, Game Over).
- State transitions are centralized in `Game.handle_events()` and `MenuSystem.handle_event()`/`change_state()`.
- Quick save/load: F9–F12 save to slots; menu also offers save/load/delete with confirmations.

## Rendering & Performance
- Alpha/transparency cache: `GameRenderer` in `core/level.py` with `_alpha_cache` and bounded size to avoid re-blits of alpha surfaces; use `get_alpha_cache_info()` when debugging.
- FPS monitor: `fps_monitor.py`; toggle with F3, details with F4, reset with F5, summary with F6.
- Element mixer + mana bar: `ui/element_mixer.py` rendered after level; positioned relative to screen bottom.

## Maps & Transitions
- TMX/TSX assets must use relative paths and exist under `assets/maps` (and referenced tilesets/images under `assets/`).
- Level completion: `Level.trigger_level_completion()` handles message + next map load; guard for missing tilesets/images.

## Assets & Managers
- Always load sprites/sounds via `managers/asset_manager.py` (shared caching and scaling). Entities already hold an `AssetManager()` instance.
- Settings/music: `managers/settings_manager.py` and `Game._apply_music_for_state`; runtime music volume keys: PageUp/PageDown, `m` toggles mute.

## Conventions & Tips
- New features should be modular in the appropriate subfolder; follow existing naming and constructor patterns.
- Respect the input priority and avoid re-handling element keys 1–3 in new gameplay code.
- Prefer console logs for recoverable issues; most critical failures continue with degraded behavior.
- For small screens, feature-detect `ALCHEMIST_SMALL_SCREEN` in config paths (`core/config.py` → `DisplayConfig`).

## File Pointers (examples)
- Entry/game loop: `src/core/main.py` (Game class, state management, audio, FPS, element mixer).
- Level/rendering: `src/core/level.py` (`GameRenderer`, `_alpha_cache`, `trigger_level_completion`).
- Input: `src/systems/input_system.py` (universal input), optional hardware adapter in `systems/hardware_input_adapter`.
- UI: `src/ui/menu_system.py`, `src/ui/hotkey_display.py`, `src/ui/element_mixer.py`.
- Saves: `src/managers/save_system.py` (used by menus and gameplay).

If anything here seems off for your task, cite the file you’re reading and propose a correction.
