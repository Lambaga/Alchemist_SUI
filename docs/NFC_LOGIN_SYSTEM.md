# NFC-Login System für Alchemist_SUI

Ein vollständiges NFC-Login-System für Alchemist_SUI, das es Spielern ermöglicht, sich mit einem NFC-Tag einzuloggen, bevor sie ein neues Spiel starten.

## Überblick

Wenn ein Spieler auf **"Neues Spiel"** klickt, erscheint ein Login-Bildschirm, der auf einen NFC-Tag wartet. Nachdem der Tag gescannt wurde, wird ein personalisierter Willkommensgruß angezeigt (z.B. "Herzlich willkommen Jonas!"), und das Spiel startet automatisch.

## Hardware-Anforderungen

### Notwendige Komponenten

1. **Adafruit Metro ESP32-S2 Express Beta**
   - Microcontroller mit WiFi/Bluetooth
   - USB-C Verbindung
   - [Datenseite](https://www.adafruit.com/product/5000)

2. **PN532 NFC Reader Module (HW-147)** 
   - ISO14443A kompatibel
   - SPI oder I2C Modus
   - [Dokumentation](https://www.adafruit.com/product/364)

3. **NFC-Tags (MIFARE)**
   - Kompatibel mit ISO14443A
   - Zum Beschreiben mit UID verwenden

### Verdrahtung (SPI-Modus)

```
PN532 Module          Adafruit Metro ESP32-S2
═══════════════════════════════════════════
CS/SDA (Pin 1)   →   GPIO 10 (D10)
SCK (Pin 2)      →   GPIO 13 (SCK/D13)
MOSI (Pin 3)     →   GPIO 11 (MOSI/D11)
MISO (Pin 4)     →   GPIO 12 (MISO/D12)
GND (Pin 5)      →   GND
VCC (Pin 8)      →   3.3V
```

⚠️ **Wichtig**: Achte auf die korrekte Spannungsversorgung (3.3V, nicht 5V)!

## Software-Installation

### 1. Arduino IDE Setup

1. [Arduino IDE herunterladen](https://www.arduino.cc/en/software) und installieren
2. **Arduino IDE starten** und zum Sketch öffnen

### 2. Board Support hinzufügen

1. Gehe zu **Datei → Einstellungen (Preferences)**
2. Unter "Zusätzliche Boards-Manager-URLs" einfügen:
   ```
   https://espressif.github.io/arduino-esp32/package_esp32_index.json
   ```
3. Klicke **OK**
4. Gehe zu **Tools → Board → Boards Manager**
5. Suche nach "ESP32" und installiere "esp32" von Espressif Systems

### 3. Board auswählen

1. Gehe zu **Tools → Board: → esp32 → "Adafruit Metro ESP32-S2"**
   - Falls nicht vorhanden: "ESP32S2 Dev Module" wählen
2. Gehe zu **Tools → Port → COM# (erkannter Port für dein Gerät)**

### 4. Erforderliche Bibliotheken installieren

1. Gehe zu **Sketch → Bibliothek einbinden → Bibliteken verwalten**
2. Installiere diese Bibliotheken:
   - **"Adafruit PN532"** von Adafruit
   - **"ArduinoJson"** von Benoit Blanchon

(Oder einfach diesen Code vor dem Hochladen einfügen, Arduino installiert sie automatisch)

## Sketch hochladen

1. Öffne die Datei `nfc_reader_esp32.ino` in Arduino IDE
2. Verbinde das ESP32-Board via USB mit deinem Computer
3. Klicke **Sketch → Hochladen** (oder Strg+U)
4. Warte, bis "Hochladen abgeschlossen" angezeigt wird

### Troubleshooting beim Upload

**Problem**: "COM7 wird nicht erkannt"
- Installiere die [CH340 Treiber](https://sparks.gogo.co.nz/ch340.html)
- Oder: Aktualisiere die Arduino IDE auf die neueste Version

**Problem**: "Verbindungszeitüberschreitung"
- Drücke zweimal schnell hintereinander die Reset-Taste (RST) auf dem Board
- Wiederhole den Upload innerhalb von 2 Sekunden

## NFC-Tag UIDs konfigurieren

Die UID-zu-Name-Zuordnung ist in `src/ui/menu_system.py` definiert:

```python
NFC_TAG_MAPPING = {
    "04:8e:b4:da:be:72:80": "Jonas",
    "04:10:b1:da:be:72:80": "Simon",
    "04:66:41:da:be:72:80": "Christian"
}
```

### Tag-UID auslesen

1. **Serielle Monitor öffnen**: Arduino IDE → Tools → Serieller Monitor (115200 Baud)
2. **NFC-Tag scannen**
3. Die UID wird angezeigt, z.B. `04 8e b4 da be 72 80`
4. Diese in `menu_system.py` unter `NFC_TAG_MAPPING` eintragen

Automatische Formatierung:
- Input: `04 8E B4 DA BE 72 80` → Output: `04:8e:b4:da:be:72:80` ✓
- Input: `048EB4DABE7280` → Output: `04:8e:b4:da:be:72:80` ✓

## Spiel-Integration

### Hardware aktivieren

Die Hardware ist standardmäßig im **Mock-Modus** (Simulation). Um echte Hardware zu aktivieren:

**Windows** (PowerShell):
```powershell
$env:ALCHEMIST_HW=1
$env:ALCHEMIST_HW_PORT="COM7"
python -m core.main
```

**Linux/Mac** (Bash):
```bash
export ALCHEMIST_HW=1
export ALCHEMIST_HW_PORT=/dev/ttyACM0
python -m core.main
```

Mögliche Ports:
- **Windows**: COM3, COM7, COM8
- **Linux**: /dev/ttyACM0, /dev/ttyUSB0
- **macOS**: /dev/cu.usbserial-*

### Spielablauf

1. Starte das Spiel normal
2. Klicke auf **"Neues Spiel"**
3. Der NFC-Login-Bildschirm erscheint
4. Halte deinen NFC-Tag an den Reader
5. Das Spiel zeigt einen Willkommensgruß an
6. Nach 2 Sekunden startet das Gameplay automatisch

### Mock-Modus (Entwicklung ohne Hardware)

Zum Testen ohne echte Hardware einfach die Tags manuell eingeben:

```python
# In deinem Test-Skript
from systems.hardware_interface import HardwareInterface

hw = HardwareInterface(mock_mode=True)
hw.connect()
hw.simulate_nfc_tag_detected("04:8e:b4:da:be:72:80")
```

## Gameplay-Integration

Der Spielername wird in `Game.player_name` gespeichert und kann vom Level/Gameplay verwendet werden:

```python
# In Level.__init__ oder bei Bedarf:
if hasattr(self.main_game, 'player_name') and self.main_game.player_name:
    print(f"🎮 Spieler: {self.main_game.player_name}")
    # Kann für Highscores, Speicherdaten, etc. verwendet werden
```

## Debugging

### Verbose Logs aktivieren

Setze in `src/core/settings.py`:
```python
VERBOSE_LOGS = True
```

Dann werden Debug-Meldungen angezeigt:
```
✅ Hardware Interface initialisiert für NFC-Login
🎫 NFC-Tag erkannt: Jonas (04:8e:b4:da:be:72:80)
👤 Spielername gespeichert: Jonas
```

### Serielle Ausgabe/Echo überprüfen

Öffne den seriellen Monitor in Arduino IDE und überprüfe, ob die PN532 initialisiert wird:
```
=====================================
🎫 NFC Reader for Alchemist_SUI
ESP32-S2 + PN532 NFC Module
=====================================

✅ PN532 found! Firmware version: 0x32000907
⚙️ PN532 configured

🎫 Waiting for NFC tags... Please scan a card/tag to login!
```

## Technische Spezifikationen

### Nachrichtenformat (JSON über Serial)

```json
{
  "type": "NFC_READ",
  "uid": "04 8e b4 da be 72 80",
  "uidLength": 7,
  "timestamp": 12345680
}
```

### Baud Rate
- **115200** (Standard für Alchemist_SUI)
- Höhere Raten möglich, aber nicht empfohlen für Serial-Zuverlässigkeit

### Block-Größe auf PN532
- ISO14443A MIFARE: 16 Bytes pro Sektor
- UID: 4-7 Bytes (abhängig vom Tag-Typ)

## Known Issues & Lösungen

| Problem | Ursache | Lösung |
|---------|--------|--------|
| "Unbekannter NFC-Tag" beim Scannen | UID nicht in Mapping konfiguriert | UID in `menu_system.py` `NFC_TAG_MAPPING` eintragen |
| Kein Willkommensgruß angezeigt | Hardware nicht verbunden oder Timeout | Überprüfe Verdrahtung, versuche Debug-Meldungen auszugeben |
| ESP32 wird nicht erkannt | USB-Port falsch oder Treiber fehlt | COM-Port überprüfen, CH340 Treiber installieren |
| Tag wird mehrfach erkannt | Debounce-Zeit zu kurz | Erhöhe `DEBOUNCE_DELAY` im Arduino-Code auf 2000ms |

## Zukünftige Erweiterungen

- [ ] Multiple Spieler-Profile pro Tag
- [ ] Highscore-Speicherung nach Spieler
- [ ] WireGuard/QR-Code Alternative Login
- [ ] Karten-Auszahlung nach Spiel basierend auf UID
- [ ] Admin-Tag zum Zurücksetzen der Highscores

## Lizenz

Dieses System ist Teil von Alchemist_SUI und unterliegt der gleichen Lizenz.

## Support

Bei Problemen:
1. Überprüfe die Verdrahtung
2. Teste den seriellen Monitor (115200 Baud)
3. Aktiviere `VERBOSE_LOGS = True` für Debug-Ausgaben
4. Konsultiere die [Adafruit PN532 Dokumentation](https://learn.adafruit.com/adafruit-pn532-rfid-nfc/)
