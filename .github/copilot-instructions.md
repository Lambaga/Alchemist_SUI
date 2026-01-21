# Copilot Instructions for Alchemist_SUI

Keep changes concrete and code-referenced; follow the repo’s runtime patterns (Pygame loop, caching, optional hardware input).

## Quick start (preferred)
- Use the launchers from repo root: `run_game.(bat|sh)` or `run_game_7inch.(bat|sh)` (they create/activate `.venv`, install `requirements.txt`, then run `cd src && python -m core.main`).
- Manual run: `cd src` then `python -m core.main`.

## Architecture (big picture)
- Entry/state hub: `src/core/main.py` (`Game`) initializes audio + display profile via `DisplayConfig`, sets up universal input, then orchestrates `MenuSystem` + `Level`.
- Menus/states: `src/ui/menu_system.py` defines `GameState` screens; transitions are handled by `Game.handle_events()` + `MenuSystem.handle_event()/change_state()`.
- Rendering: `Level.render()` uses `GameRenderer` in `src/core/level.py`; UI overlays (hotkeys / element mixer / FPS) are drawn last.

## Input + hardware integration
- Default abstraction: `src/systems/input_system.py` (`UniversalInputSystem`).
- Optional Action System: `src/systems/action_system.py` enforces input priority `hardware > gamepad > keyboard` with a short timeout.
- ESP32/serial path: `src/systems/hardware_interface.py` (JSON messages at 115200) + `src/systems/hardware_input_adapter.py` (maps to `ActionType`).
- Enable real hardware: set `ALCHEMIST_HW=1` (optional `ALCHEMIST_HW_PORT=/dev/ttyACM0`). Without it, hardware is typically mock/fallback.

## Performance-critical conventions
- Always load/scale sprites via `src/managers/asset_manager.py` (`AssetManager` singleton). Prefer `get_scaled_sprite()` over per-frame `pygame.transform.scale()`.
- Transparency effects are cached: `GameRenderer._alpha_cache` in `src/core/level.py`.

## Maps/assets
- TMX loading uses PyTMX with TSX workarounds: `src/world/map_loader.py` temporarily `chdir()`s into the map dir to resolve relative TSX/PNG. Keep tileset/image paths relative to the TMX.
- Maps live under `assets/maps/` and referenced images under `assets/`.
- Menu art overrides: `ALCHEMIST_MENU_BG` and `ALCHEMIST_MENU_BUTTON_TEXTURE` (see `src/ui/menu_system.py`).

## Saves/config
- Saves: `src/managers/save_system.py` (slots 1..5 + `save_auto`), stored under `saves/`.
- Config layering: `src/core/config.py` is the “real” config; `src/core/settings.py` is a compatibility wrapper (`from settings import *`). Toggle console noise via `VERBOSE_LOGS` there.
