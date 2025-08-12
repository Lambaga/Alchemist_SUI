# 🔌 ESP32 Hardware Setup - Der Alchemist

## 📋 Benötigte Komponenten

### Hauptkomponenten
- **1x ESP32 DevKit** (oder ähnlich)
- **5x Tactile Buttons** (6x6mm oder 12x12mm)
- **1x Analog Joystick Modul** (wie KY-023)
- **5x 10kΩ Widerstände** (Pull-up für Buttons)
- **1x Breadboard oder Perfboard**
- **Jumper Wires** (Male-to-Male, Male-to-Female)
- **USB Kabel** für Programmierung und Power

### Optional
- **1x RGB LED** für Status-Anzeige
- **1x Buzzer** für Audio-Feedback
- **1x Gehäuse** (3D-gedruckt oder gekauft)

## 🔧 Pin-Belegung ESP32

| Komponente | ESP32 Pin | GPIO | Beschreibung |
|------------|-----------|------|--------------|
| **Button FIRE** | D2 | GPIO2 | Feuer-Element |
| **Button WATER** | D4 | GPIO4 | Wasser-Element |
| **Button STONE** | D5 | GPIO5 | Stein-Element |
| **Button CAST** | D18 | GPIO18 | Zauber ausführen |
| **Button CLEAR** | D19 | GPIO19 | Kombination löschen |
| **Joystick X** | A0 | GPIO34 (ADC1_CH6) | X-Achse Bewegung |
| **Joystick Y** | A3 | GPIO35 (ADC1_CH7) | Y-Achse Bewegung |
| **Joystick VCC** | 3V3 | 3.3V | Spannungsversorgung |
| **Joystick GND** | GND | GND | Masse |
| **Status LED** | D2 | GPIO2 | Eingebaute LED |

## 🔌 Schaltplan

```
ESP32 DevKit                    Komponenten
                               
GPIO2  ────┬─── Button FIRE ─── GND
           │    (Pull-up 10kΩ zu 3V3)
           └─── LED Status

GPIO4  ──── Button WATER ────── GND
            (Pull-up 10kΩ zu 3V3)

GPIO5  ──── Button STONE ────── GND  
            (Pull-up 10kΩ zu 3V3)

GPIO18 ──── Button CAST ─────── GND
            (Pull-up 10kΩ zu 3V3)

GPIO19 ──── Button CLEAR ───── GND
            (Pull-up 10kΩ zu 3V3)

GPIO34 ──── Joystick X-Axis
GPIO35 ──── Joystick Y-Axis

3V3 ───┬─── Joystick VCC
       └─── Pull-up Widerstände (5x 10kΩ)

GND ───┬─── Joystick GND
       └─── Alle Button Pins
```

## ⚡ Verdrahtung Schritt-für-Schritt

### 1. Buttons verdrahten
```
Jeder Button:
- Pin 1 → ESP32 GPIO Pin
- Pin 2 → GND
- 10kΩ Widerstand zwischen GPIO Pin und 3V3 (Pull-up)
```

### 2. Joystick verdrahten
```
Joystick Modul:
- VCC → ESP32 3V3
- GND → ESP32 GND  
- X-Axis → ESP32 GPIO34
- Y-Axis → ESP32 GPIO35
```

### 3. Power & Kommunikation
```
- USB Kabel → ESP32 für Power + Serial
- Alternativ: Externes 5V Netzteil
```

## 📝 Kalibrierung

### Joystick Center-Punkt finden
```cpp
void calibrateJoystick() {
  int centerX = analogRead(PIN_JOYSTICK_X);
  int centerY = analogRead(PIN_JOYSTICK_Y);
  
  Serial.printf("Center: X=%d, Y=%d\n", centerX, centerY);
  // Diese Werte in ADC_CENTER setzen
}
```

### Button Test
```cpp
void testButtons() {
  for (int i = 0; i < BUTTON_COUNT; i++) {
    if (digitalRead(buttons[i].pin) == LOW) {
      Serial.printf("Button %s pressed\n", buttons[i].id);
    }
  }
}
```

## 🛠️ Arduino IDE Setup

### 1. ESP32 Board Package installieren
```
1. Arduino IDE öffnen
2. File → Preferences
3. Additional Boards Manager URLs: 
   https://dl.espressif.com/dl/package_esp32_index.json
4. Tools → Board → Boards Manager
5. Suchen nach "ESP32" → Install
```

### 2. Libraries installieren
```
Tools → Manage Libraries → Install:
- ArduinoJson (v6.x)
```

### 3. Board konfigurieren
```
Tools → Board → ESP32 Arduino → ESP32 Dev Module
Tools → Port → (Dein COM Port)
Tools → Upload Speed → 115200
```

## 🚀 Upload & Test

### 1. Code uploaden
```
1. Arduino IDE öffnen
2. esp32_alchemist_controller.ino laden  
3. Board und Port auswählen
4. Upload Button klicken
```

### 2. Serial Monitor testen
```
1. Tools → Serial Monitor
2. Baud Rate: 115200
3. Buttons drücken → JSON Messages sehen
4. Joystick bewegen → Koordinaten sehen
```

### 3. Mit Spiel verbinden
```bash
# Hardware-Modus aktivieren
export ALCHEMIST_HW=1

# Port anpassen (Linux/Pi)
# /dev/ttyUSB0 oder /dev/ttyACM0

# Spiel starten
./run_game.sh
```

## 🔧 Troubleshooting

### Problem: ESP32 nicht erkannt
**Lösung:**
```
1. USB Kabel prüfen (Daten + Power)
2. ESP32 in Flash-Mode versetzen (BOOT Button gedrückt halten beim Upload)
3. Driver installieren (CP210x oder CH340)
4. Anderen USB Port probieren
```

### Problem: Buttons reagieren nicht
**Lösung:**
```
1. Pull-up Widerstände prüfen (10kΩ zwischen GPIO und 3V3)
2. Verkabelung prüfen
3. Serial Monitor → Debug-Nachrichten aktivieren
```

### Problem: Joystick springt
**Lösung:**
```
1. Deadzone erhöhen (JOYSTICK_DEADZONE)
2. Kondensator 100nF zwischen VCC und GND
3. Kabel kürzer/besser abschirmen
```

### Problem: Keine Serial-Verbindung zum Spiel
**Lösung:**
```
1. Richtigen COM Port in config.py eintragen
2. Baud Rate prüfen (115200)
3. Hardware-Modus aktivieren (ALCHEMIST_HW=1)
4. Firewall/Antivirus prüfen
```

## 📊 Performance

### Latenz
- **Button Response**: < 20ms (mit Debounce)
- **Joystick Update**: 50ms Intervall
- **Serial Baudrate**: 115200 (sehr schnell)
- **Heartbeat**: 1000ms Intervall

### Stromverbrauch
- **Idle**: ~80mA
- **Active**: ~120mA
- **USB Power**: Ausreichend für alle Komponenten

## 🎯 Erweiterungen

### RGB LED Status
```cpp
#include <FastLED.h>

CRGB leds[1];
void setup() {
  FastLED.addLeds<WS2812, PIN_STATUS_LED, GRB>(leds, 1);
}

void setStatusColor(CRGB color) {
  leds[0] = color;
  FastLED.show();
}
```

### Buzzer Feedback
```cpp
void playTone(int frequency, int duration) {
  tone(PIN_BUZZER, frequency, duration);
}
```

### OLED Display
```cpp
#include <Wire.h>
#include <Adafruit_SSD1306.h>

void showGameStatus(String status) {
  display.clearDisplay();
  display.println(status);
  display.display();
}
```
