#!/bin/bash
# -*- coding: utf-8 -*-
"""
Raspberry Pi 4 Setup-Script für Der Alchemist
Installiert alle Abhängigkeiten und konfiguriert das System
"""

echo "🍓 Der Alchemist - Raspberry Pi 4 Setup"
echo "========================================"

# System-Informationen anzeigen
echo "📊 System-Information:"
echo "   OS: $(lsb_release -d | cut -f2)"
echo "   Kernel: $(uname -r)"
echo "   Architektur: $(uname -m)"
echo "   Memory: $(free -h | awk '/^Mem:/ {print $2}')"

# Python-Version prüfen
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "   Python: $python_version"

# GPU-Memory prüfen
gpu_mem=$(vcgencmd get_mem gpu | cut -d= -f2)
echo "   GPU Memory: $gpu_mem"

if [[ "${gpu_mem%M}" -lt 128 ]]; then
    echo "⚠️  WARNUNG: GPU-Speicher ist unter 128MB."
    echo "   Führe 'sudo raspi-config' aus und erhöhe GPU-Memory auf 128MB+"
fi

echo ""

# Virtual Environment erstellen
echo "🐍 Virtual Environment Setup..."
if [ ! -d "venv" ]; then
    echo "   Erstelle Virtual Environment..."
    python3 -m venv venv
    echo "   ✅ Virtual Environment erstellt"
else
    echo "   ✅ Virtual Environment existiert bereits"
fi

# Virtual Environment aktivieren
source venv/bin/activate
echo "   ✅ Virtual Environment aktiviert"

# Pip aktualisieren
echo "📦 Package Manager aktualisieren..."
pip install --upgrade pip setuptools wheel

# System-Abhängigkeiten prüfen und installieren
echo "🔧 System-Abhängigkeiten prüfen..."

# Audio-Bibliotheken
if ! dpkg -l | grep -q libasound2-dev; then
    echo "   Installing audio libraries..."
    sudo apt update
    sudo apt install -y python3-dev libasound2-dev libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev
fi

# Pygame kompilieren falls nötig
echo "🎮 Pygame Installation..."
pip install pygame>=2.5.2

# Weitere Abhängigkeiten installieren
echo "📚 Weitere Abhängigkeiten..."
pip install -r requirements-rpi.txt

# Test-Skript ausführen
echo ""
echo "🧪 Kompatibilitäts-Test durchführen..."
python3 raspberry_pi_setup.py

echo ""
echo "✅ Setup abgeschlossen!"
echo ""
echo "🚀 Spiel starten mit:"
echo "   source venv/bin/activate"
echo "   cd src/core"
echo "   python3 main.py"
echo ""
echo "🎮 Gamepad-Tipps:"
echo "   - USB-Gamepads werden automatisch erkannt"
echo "   - Xbox/PlayStation Controller empfohlen"
echo "   - Bluetooth-Gamepads: Über Bluetooth-Settings koppeln"
echo ""
echo "⚡ Performance-Tipps:"
echo "   - GPU-Memory: sudo raspi-config -> Advanced -> Memory Split -> 128"
echo "   - Audio: sudo raspi-config -> Advanced Options -> Audio"
echo "   - Für beste Performance: Desktop optional deaktivieren"
