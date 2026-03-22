/* 
 * NFC Reader for Alchemist_SUI (SIMPLIFIED VERSION)
 * Adafruit Metro ESP32-S2 + PN532 NFC Reader
 * Reads NFC tags and sends UID to Pygame via Serial (JSON format)
 * WITHOUT ArduinoJson dependency
 */

#include <SPI.h>
#include <Adafruit_PN532.h>

// Define PN532 CS pin (for SPI communication)
#define PN532_SS 10

// Initialize PN532 reader (SPI mode)
Adafruit_PN532 nfc(PN532_SS);

// NFC Tag detection state
unsigned long last_tag_read = 0;
uint8_t last_uid[7];
uint8_t last_uid_length = 0;
const unsigned long DEBOUNCE_DELAY = 1000;  // 1 second debounce to avoid duplicates

void setup() {
  // Initialize Serial communication at 115200 baud
  Serial.begin(115200);
  while (!Serial) delay(10);  // Wait until Serial ready
  
  delay(1000);  // Wait for serial monitor to open
  
  Serial.println("\n=====================================");
  Serial.println("🎫 NFC Reader for Alchemist_SUI");
  Serial.println("ESP32-S2 + PN532 NFC Module (SIMPLIFIED)");
  Serial.println("=====================================\n");
  
  // Initialize PN532
  Serial.println("🔌 Initializing PN532...");
  nfc.begin();
  
  // Check if PN532 is present
  uint32_t versiondata = nfc.getFirmwareVersion();
  if (!versiondata) {
    Serial.println("❌ PN532 not found!");
    Serial.println("Please check your wiring:");
    Serial.println("  - PN532 CS  -> GPIO 10");
    Serial.println("  - PN532 SCK -> GPIO 13 (SCK)");
    Serial.println("  - PN532 MOSI -> GPIO 11 (MOSI)");
    Serial.println("  - PN532 MISO -> GPIO 12 (MISO)");
    Serial.println("  - PN532 VCC -> 3.3V");
    Serial.println("  - PN532 GND -> GND");
    while (1) {
      delay(1000);
      Serial.println("⏳ Waiting for PN532...");
    }
  }
  
  // PN532 firmware version
  Serial.print("✅ PN532 found! Firmware version: 0x");
  Serial.println(versiondata, HEX);
  
  // Configure PN532
  nfc.SAMConfig();
  Serial.println("⚙️ PN532 configured\n");
  Serial.println("🎫 Waiting for NFC tags... Please scan a card/tag to login!");
  Serial.println("=====================================\n");
}

void loop() {
  // Try to read an NFC tag
  uint8_t uid[7];
  uint8_t uidLength;
  
  if (nfc.readPassiveTargetID(PN532_MIFARE_ISO14443A, uid, &uidLength)) {
    // Check for debouncing (same tag detected too soon)
    unsigned long current_time = millis();
    bool same_tag = (uidLength == last_uid_length);
    
    if (same_tag) {
      for (uint8_t i = 0; i < uidLength; i++) {
        if (uid[i] != last_uid[i]) {
          same_tag = false;
          break;
        }
      }
    }
    
    // Only process if it's a new tag or debounce time has passed
    if (!same_tag || (current_time - last_tag_read) > DEBOUNCE_DELAY) {
      // Store tag info
      last_tag_read = current_time;
      last_uid_length = uidLength;
      memcpy(last_uid, uid, uidLength);
      
      // Format UID as hex string with spaces
      String uid_hex = "";
      for (uint8_t i = 0; i < uidLength; i++) {
        // Add leading zero if needed
        if (uid[i] < 0x10) {
          uid_hex += "0";
        }
        uid_hex += String(uid[i], HEX);
        if (i < uidLength - 1) {
          uid_hex += " ";
        }
      }
      
      // Print to console
      Serial.print("🎫 Tag UID: ");
      Serial.println(uid_hex);
      
      // Build JSON manually (no ArduinoJson needed!)
      String json = "{\"type\":\"NFC_READ\",\"uid\":\"";
      json += uid_hex;
      json += "\",\"uidLength\":";
      json += uidLength;
      json += ",\"timestamp\":";
      json += current_time;
      json += "}";
      
      // Send JSON to serial (Pygame receives this)
      Serial.println(json);
      Serial.flush();  // Force send immediately
      
      Serial.print("📤 JSON sent: ");
      Serial.println(json);
      
      // Wait before allowing next read
      delay(500);
    }
  }
  
  // Small delay to prevent overwhelming the serial port
  delay(100);
}

/*
 * NFC Tag UID Reference for testing:
 * Jonas:    04 8E B4 DA BE 72 80
 * Simon:    04 10 B1 DA BE 72 80
 * Christian: 04 66 41 DA BE 72 80
 * 
 * Expected JSON output format:
 * {"type":"NFC_READ","uid":"04 8E B4 DA BE 72 80","uidLength":7,"timestamp":12345}
 */
