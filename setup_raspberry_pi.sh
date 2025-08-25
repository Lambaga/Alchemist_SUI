#!/bin/bash
# Setup Script für Der Alchemist auf Raspberry Pi 4

echo "🍓 RASPBERRY PI 4 SETUP FÜR DER ALCHEMIST"
echo "========================================"

# System Update
echo "📦 System wird aktualisiert..."
sudo apt update
sudo apt upgrade -y

# Python und Pygame installieren
echo "🐍 Python-Abhängigkeiten installieren..."
sudo apt install -y python3 python3-pip python3-pygame

# Zusätzliche Abhängigkeiten für bessere Performance
echo "⚡ Performance-Pakete installieren..."
sudo apt install -y python3-numpy python3-scipy

# GPIO-Zugriff für Hardware (falls benötigt)
echo "🔌 GPIO-Bibliotheken installieren..."
sudo apt install -y python3-rpi.gpio python3-gpiozero

# Gamepad/Joystick Support
echo "🎮 Joystick-Support konfigurieren..."
sudo apt install -y joystick jstest-gtk

# Audio-System
echo "🔊 Audio-System konfigurieren..."
sudo apt install -y alsa-utils pulseaudio

# GPU Memory Split für bessere Grafik-Performance
echo "🎨 GPU-Einstellungen optimieren..."
echo "gpu_mem=128" | sudo tee -a /boot/config.txt

# Permissions für Joystick-Zugriff
echo "🔐 Berechtigungen für Joystick-Zugriff einrichten..."
sudo usermod -a -G input,audio,video pi

# Test ob pygame korrekt installiert ist
echo "✅ Installation testen..."
python3 -c "import pygame; print('✅ Pygame:', pygame.version.ver)"

echo ""
echo "🎉 SETUP ABGESCHLOSSEN!"
echo ""
echo "🔄 NEUSTART EMPFOHLEN für GPU-Einstellungen"
echo ""
echo "📝 NÄCHSTE SCHRITTE:"
echo "1. Raspberry Pi neustarten: sudo reboot"
echo "2. Gamepad anschließen"
echo "3. Test ausführen: python3 raspberry_pi_test.py"
echo "4. Spiel starten: python3 src/main.py"
echo ""
echo "🎮 UNTERSTÜTZTE GAMEPADS:"
echo "- Xbox 360/One Controller"
echo "- PlayStation 3/4/5 Controller" 
echo "- Generic USB Gamepads"
echo "- Raspberry Pi GPIO Buttons (mit Hardware-Interface)"
