@echo off
REM Aktiviert venv (falls vorhanden) und führt GID Diagnose inkl. Remap aus
set MAP_FILE=assets\maps\Map2.tmx
set FIXED_OUT=assets\maps\Map2_fixed.tmx

if exist .venv\Scripts\activate.bat (
  call .venv\Scripts\activate.bat
) else (
  echo [WARN] Kein .venv gefunden. Fortsetzen mit globalem Python...
)

python scripts/scan_map_gids.py --map %MAP_FILE% --report map_town_gid_report.json --suggest-remap --apply-remap --fixed-out %FIXED_OUT%
if errorlevel 1 (
  echo Diagnose fehlgeschlagen.
  exit /b 1
)

echo Fertig. Report: map_town_gid_report.json  Fixed: %FIXED_OUT%
