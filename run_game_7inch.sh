#!/bin/bash

# Der Alchemist - 7-Zoll Monitor Launcher für Linux/macOS
# Optimiert für 1024x600 Auflösung

echo "🧙‍♂️ DER ALCHEMIST - 7-ZOLL MONITOR MODUS"
echo "📱 Optimiert für 1024x600 Auflösung"
echo ""

# Prüfe ob Python verfügbar ist
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 ist nicht installiert oder nicht im PATH verfügbar."
    echo "   Bitte installiere Python 3.7+ und versuche es erneut."
    exit 1
fi

# Zeige Python-Version
PYTHON_VERSION=$(python3 --version 2>&1)
echo "🐍 Verwende $PYTHON_VERSION"

# Prüfe ob .venv Ordner existiert
if [ ! -d ".venv" ]; then
    echo "🔧 Erstelle virtuelle Umgebung..."
    python3 -m venv .venv
    if [ $? -ne 0 ]; then
        echo "❌ Fehler beim Erstellen der virtuellen Umgebung."
        exit 1
    fi
    echo "✅ Virtuelle Umgebung erstellt."
fi

# Aktiviere virtuelle Umgebung
echo "🔌 Aktiviere virtuelle Umgebung..."
source .venv/bin/activate
if [ $? -ne 0 ]; then
    echo "❌ Fehler beim Aktivieren der virtuellen Umgebung."
    exit 1
fi

# Installiere/Aktualisiere Abhängigkeiten
echo "📦 Installiere/Aktualisiere Abhängigkeiten..."
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Fehler beim Installieren der Abhängigkeiten."
    echo "   Überprüfe deine requirements.txt und Internetverbindung."
    exit 1
fi

echo ""
echo "🚀 STARTE SPIEL IM 7-ZOLL MODUS..."
echo ""
echo "📱 Erwartete Einstellungen:"
echo "   - Auflösung: 1024x600 (Vollbild)"
echo "   - FPS: 45 (optimiert für kleine Displays)"
echo "   - UI: Kompakt skaliert"
echo "   - Spell Bar: Angepasste Größe"
echo "   - Hotkeys: Kompakte Anzeige"
echo ""

# Setze Umgebungsvariable für 7-Zoll Modus
export ALCHEMIST_SMALL_SCREEN=1

# Starte das Spiel
cd src
python -m core.main

# Behandle mögliche Fehler
if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Das Spiel wurde mit einem Fehler beendet."
    echo ""
    echo "🔧 Fehlerbehebung:"
    echo "   1. Stelle sicher, dass dein Display 1024x600 unterstützt"
    echo "   2. Überprüfe ob alle Dateien vorhanden sind"
    echo "   3. Prüfe die Konsole für spezifische Fehlermeldungen"
    echo ""
    read -p "Drücke Enter zum Beenden..."
    exit 1
fi

echo ""
echo "🎮 Spiel beendet. Danke fürs Spielen!"
read -p "Drücke Enter zum Beenden..."
