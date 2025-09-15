@echo off
chcp 65001 >nul
REM Generate a PNG snapshot of Map_Town with diagnostics
set ALCHEMIST_MAP_DEBUG=1
set ALCHEMIST_TILE_DEBUG_SOLID=1
set ALCHEMIST_TILE_GRID=1
set ALCHEMIST_DISABLE_FOREGROUND=1
set ALCHEMIST_SLICE_PREFERRED=1

REM Ensure venv and deps via main runner
if not exist "..\.venv\" (
  echo Creating venv via main runner...
  call "%~dp0..\run_game.bat" >nul 2>&1
)

call "%~dp0..\.venv\Scripts\activate.bat"
python "%~dp0map_snapshot.py" --out "%~dp0snapshot_no_fg.png"
echo Snapshot written to %~dp0snapshot_no_fg.png
