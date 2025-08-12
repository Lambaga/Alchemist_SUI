@echo off
title Der Alchemist - 7-Zoll Monitor Modus
echo.
echo 🧙‍♂️ DER ALCHEMIST - 7-ZOLL MONITOR MODUS
echo 📱 Optimiert für 1024x600 Auflösung
echo.

REM Prüfe ob Python verfügbar ist
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python ist nicht installiert oder nicht im PATH verfügbar.
    echo    Bitte installiere Python 3.7+ und versuche es erneut.
    pause
    exit /b 1
)

REM Prüfe ob .venv Ordner existiert
if not exist ".venv" (
    echo 🔧 Erstelle virtuelle Umgebung...
    python -m venv .venv
    if errorlevel 1 (
        echo ❌ Fehler beim Erstellen der virtuellen Umgebung.
        pause
        exit /b 1
    )
    echo ✅ Virtuelle Umgebung erstellt.
)

REM Aktiviere virtuelle Umgebung
echo 🔌 Aktiviere virtuelle Umgebung...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo ❌ Fehler beim Aktivieren der virtuellen Umgebung.
    pause
    exit /b 1
)

REM Installiere/Aktualisiere Abhängigkeiten
echo 📦 Installiere/Aktualisiere Abhängigkeiten...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

REM Prüfe ob Installation erfolgreich war
if errorlevel 1 (
    echo ❌ Fehler beim Installieren der Abhängigkeiten.
    echo    Überprüfe deine requirements.txt und Internetverbindung.
    pause
    exit /b 1
)

echo.
echo 🚀 STARTE SPIEL IM 7-ZOLL MODUS...
echo.
echo 📱 Erwartete Einstellungen:
echo    - Auflösung: 1024x600 (Vollbild)
echo    - FPS: 45 (optimiert für kleine Displays)
echo    - UI: Kompakt skaliert
echo    - Spell Bar: Angepasste Größe
echo    - Hotkeys: Kompakte Anzeige
echo.

REM Setze Umgebungsvariable für 7-Zoll Modus
set ALCHEMIST_SMALL_SCREEN=1

REM Starte das Spiel
cd src
python -m core.main

REM Behandle mögliche Fehler
if errorlevel 1 (
    echo.
    echo ❌ Das Spiel wurde mit einem Fehler beendet.
    echo.
    echo 🔧 Fehlerbehebung:
    echo    1. Stelle sicher, dass dein Monitor 1024x600 unterstützt
    echo    2. Überprüfe ob alle Dateien vorhanden sind
    echo    3. Prüfe die Konsole für spezifische Fehlermeldungen
    echo.
    pause
    exit /b 1
)

echo.
echo 🎮 Spiel beendet. Danke fürs Spielen!
pause
