/*
 * ESP32 Hardware Controller für Der Alchemist
 * 
 * Hardware Setup:
 * - 5 Buttons: FIRE, WATER, STONE, CAST, CLEAR
 * - 1 Analog Joystick (X/Y Achsen)
 * - USB Serial für Kommunikation (115200 baud)
 * 
 * Protokoll: JSON über Serial
 * {"type":"BUTTON","id":"FIRE","state":1}
 * {"type":"JOYSTICK","x":0.5,"y":-0.3}
 * {"type":"HEARTBEAT"}
 */

#include <ArduinoJson.h>

// ===== PIN DEFINITIONS =====
// Digital Pins für Buttons (mit Pull-up Widerständen)
const int PIN_BUTTON_FIRE = 2;   // GPIO2 - B1 Feuer
const int PIN_BUTTON_WATER = 4;  // GPIO4 - B2 Wasser  
const int PIN_BUTTON_STONE = 5;  // GPIO5 - B3 Stein
const int PIN_BUTTON_CAST = 18;  // GPIO18 - B4 Zauber ausführen
const int PIN_BUTTON_CLEAR = 19; // GPIO19 - B5 Kombination löschen

// Analog Pins für Joystick
const int PIN_JOYSTICK_X = 34;   // ADC1_CH6 - X-Achse
const int PIN_JOYSTICK_Y = 35;   // ADC1_CH7 - Y-Achse

// Optional: LED für Status-Anzeige
const int PIN_STATUS_LED = 2;    // Eingebaute LED

// ===== CONFIGURATION =====
const int SERIAL_BAUD = 115200;
const int DEBOUNCE_DELAY = 20;        // Button Debounce in ms
const int HEARTBEAT_INTERVAL = 1000;  // Heartbeat alle 1000ms
const int JOYSTICK_DEADZONE = 100;    // Deadzone für Joystick (0-4095)
const int JOYSTICK_THRESHOLD = 50;    // Minimum Änderung für Joystick-Event

// ADC Kalibrierung (ESP32 spezifisch)
const int ADC_MIN = 0;
const int ADC_MAX = 4095;
const int ADC_CENTER = 2048;

// ===== GLOBAL VARIABLES =====
// Button States
struct ButtonState {
  int pin;
  bool currentState;
  bool lastState;
  unsigned long lastDebounceTime;
  const char* id;
};

ButtonState buttons[] = {
  {PIN_BUTTON_FIRE,  false, false, 0, "FIRE"},
  {PIN_BUTTON_WATER, false, false, 0, "WATER"},
  {PIN_BUTTON_STONE, false, false, 0, "STONE"},
  {PIN_BUTTON_CAST,  false, false, 0, "CAST"},
  {PIN_BUTTON_CLEAR, false, false, 0, "CLEAR"}
};

const int BUTTON_COUNT = sizeof(buttons) / sizeof(buttons[0]);

// Joystick State
struct JoystickState {
  int lastX;
  int lastY;
  float normalizedX;
  float normalizedY;
  unsigned long lastSendTime;
};

JoystickState joystick = {ADC_CENTER, ADC_CENTER, 0.0, 0.0, 0};

// Timing
unsigned long lastHeartbeat = 0;
unsigned long lastJoystickCheck = 0;
const int JOYSTICK_CHECK_INTERVAL = 50; // Check joystick every 50ms

// ===== SETUP =====
void setup() {
  Serial.begin(SERIAL_BAUD);
  
  // Initialize digital pins with pull-up resistors
  for (int i = 0; i < BUTTON_COUNT; i++) {
    pinMode(buttons[i].pin, INPUT_PULLUP);
    buttons[i].lastState = digitalRead(buttons[i].pin);
  }
  
  // Initialize analog pins (no setup needed for ESP32 ADC)
  
  // Initialize status LED
  pinMode(PIN_STATUS_LED, OUTPUT);
  digitalWrite(PIN_STATUS_LED, LOW);
  
  // Initialize joystick center values
  joystick.lastX = analogRead(PIN_JOYSTICK_X);
  joystick.lastY = analogRead(PIN_JOYSTICK_Y);
  
  // Send initial ping
  sendPing();
  
  Serial.println("ESP32 Alchemist Controller initialized");
  Serial.printf("Firmware Version: 1.0\n");
  Serial.printf("Buttons: %d\n", BUTTON_COUNT);
  Serial.printf("Joystick Deadzone: %d\n", JOYSTICK_DEADZONE);
}

// ===== MAIN LOOP =====
void loop() {
  unsigned long currentTime = millis();
  
  // Check buttons
  checkButtons(currentTime);
  
  // Check joystick
  if (currentTime - lastJoystickCheck >= JOYSTICK_CHECK_INTERVAL) {
    checkJoystick(currentTime);
    lastJoystickCheck = currentTime;
  }
  
  // Send heartbeat
  if (currentTime - lastHeartbeat >= HEARTBEAT_INTERVAL) {
    sendHeartbeat();
    lastHeartbeat = currentTime;
  }
  
  // Process incoming serial commands (optional)
  processSerial();
  
  // Small delay to prevent overwhelming the CPU
  delay(1);
}

// ===== BUTTON HANDLING =====
void checkButtons(unsigned long currentTime) {
  for (int i = 0; i < BUTTON_COUNT; i++) {
    ButtonState* btn = &buttons[i];
    
    // Read current state (inverted because of pull-up)
    bool reading = !digitalRead(btn->pin);
    
    // Check if button state changed
    if (reading != btn->lastState) {
      btn->lastDebounceTime = currentTime;
    }
    
    // If enough time has passed, update the state
    if ((currentTime - btn->lastDebounceTime) > DEBOUNCE_DELAY) {
      if (reading != btn->currentState) {
        btn->currentState = reading;
        
        // Send button event
        sendButtonEvent(btn->id, btn->currentState ? 1 : 0);
        
        // Visual feedback
        digitalWrite(PIN_STATUS_LED, btn->currentState);
      }
    }
    
    btn->lastState = reading;
  }
}

// ===== JOYSTICK HANDLING =====
void checkJoystick(unsigned long currentTime) {
  // Read raw ADC values
  int rawX = analogRead(PIN_JOYSTICK_X);
  int rawY = analogRead(PIN_JOYSTICK_Y);
  
  // Apply deadzone
  int deltaX = abs(rawX - ADC_CENTER);
  int deltaY = abs(rawY - ADC_CENTER);
  
  if (deltaX < JOYSTICK_DEADZONE) {
    rawX = ADC_CENTER;
  }
  if (deltaY < JOYSTICK_DEADZONE) {
    rawY = ADC_CENTER;
  }
  
  // Check if significant change occurred
  int changeX = abs(rawX - joystick.lastX);
  int changeY = abs(rawY - joystick.lastY);
  
  if (changeX >= JOYSTICK_THRESHOLD || changeY >= JOYSTICK_THRESHOLD) {
    // Normalize to -1.0 to 1.0 range
    float normalizedX = (float)(rawX - ADC_CENTER) / (float)(ADC_MAX - ADC_CENTER);
    float normalizedY = (float)(rawY - ADC_CENTER) / (float)(ADC_MAX - ADC_CENTER);
    
    // Clamp values
    normalizedX = constrain(normalizedX, -1.0, 1.0);
    normalizedY = constrain(normalizedY, -1.0, 1.0);
    
    // Send joystick event
    sendJoystickEvent(normalizedX, normalizedY);
    
    // Update last known position
    joystick.lastX = rawX;
    joystick.lastY = rawY;
    joystick.normalizedX = normalizedX;
    joystick.normalizedY = normalizedY;
    joystick.lastSendTime = currentTime;
  }
  
  // Send periodic updates even without change (every 100ms)
  else if (currentTime - joystick.lastSendTime >= 100) {
    // Only if not centered
    if (abs(joystick.normalizedX) > 0.1 || abs(joystick.normalizedY) > 0.1) {
      sendJoystickEvent(joystick.normalizedX, joystick.normalizedY);
      joystick.lastSendTime = currentTime;
    }
  }
}

// ===== SERIAL COMMUNICATION =====
void sendButtonEvent(const char* buttonId, int state) {
  StaticJsonDocument<200> doc;
  
  doc["type"] = "BUTTON";
  doc["id"] = buttonId;
  doc["state"] = state;
  doc["timestamp"] = millis();
  
  serializeJson(doc, Serial);
  Serial.println();
}

void sendJoystickEvent(float x, float y) {
  StaticJsonDocument<200> doc;
  
  doc["type"] = "JOYSTICK";
  doc["x"] = x;
  doc["y"] = y;
  doc["timestamp"] = millis();
  
  serializeJson(doc, Serial);
  Serial.println();
}

void sendHeartbeat() {
  StaticJsonDocument<100> doc;
  
  doc["type"] = "HEARTBEAT";
  doc["timestamp"] = millis();
  
  serializeJson(doc, Serial);
  Serial.println();
}

void sendPing() {
  StaticJsonDocument<100> doc;
  
  doc["type"] = "PING";
  doc["fw"] = "1.0";
  doc["device"] = "ESP32_Alchemist";
  
  serializeJson(doc, Serial);
  Serial.println();
}

void sendStatus(const char* message) {
  StaticJsonDocument<200> doc;
  
  doc["type"] = "STATUS";
  doc["code"] = message;
  doc["timestamp"] = millis();
  
  serializeJson(doc, Serial);
  Serial.println();
}

// ===== INCOMING SERIAL PROCESSING =====
void processSerial() {
  if (Serial.available()) {
    String input = Serial.readStringUntil('\n');
    input.trim();
    
    if (input.length() > 0) {
      StaticJsonDocument<200> doc;
      DeserializationError error = deserializeJson(doc, input);
      
      if (!error) {
        String type = doc["type"];
        
        if (type == "PING") {
          sendStatus("PONG");
        }
        else if (type == "LED_EFFECT") {
          // Handle LED effects from game
          String effect = doc["effect"];
          String color = doc["color"];
          handleLedEffect(effect.c_str(), color.c_str());
        }
        else if (type == "RESET") {
          // Reset to initial state
          sendStatus("RESET");
          ESP.restart();
        }
      }
    }
  }
}

// ===== LED EFFECTS =====
void handleLedEffect(const char* effect, const char* color) {
  // Simple LED feedback
  if (strcmp(effect, "success") == 0) {
    // Flash LED 3 times for success
    for (int i = 0; i < 3; i++) {
      digitalWrite(PIN_STATUS_LED, HIGH);
      delay(100);
      digitalWrite(PIN_STATUS_LED, LOW);
      delay(100);
    }
  }
  else if (strcmp(effect, "error") == 0) {
    // Long flash for error
    digitalWrite(PIN_STATUS_LED, HIGH);
    delay(500);
    digitalWrite(PIN_STATUS_LED, LOW);
  }
  else if (strcmp(effect, "idle") == 0) {
    // Breathing effect (simplified)
    for (int i = 0; i < 255; i += 5) {
      analogWrite(PIN_STATUS_LED, i);
      delay(10);
    }
    for (int i = 255; i >= 0; i -= 5) {
      analogWrite(PIN_STATUS_LED, i);
      delay(10);
    }
  }
}

// ===== DEBUG FUNCTIONS =====
void printDebugInfo() {
  Serial.printf("=== DEBUG INFO ===\n");
  Serial.printf("Uptime: %lu ms\n", millis());
  Serial.printf("Free Heap: %d bytes\n", ESP.getFreeHeap());
  
  Serial.printf("Buttons: ");
  for (int i = 0; i < BUTTON_COUNT; i++) {
    Serial.printf("%s=%d ", buttons[i].id, buttons[i].currentState);
  }
  Serial.printf("\n");
  
  Serial.printf("Joystick: X=%.2f Y=%.2f (Raw: %d, %d)\n", 
                joystick.normalizedX, joystick.normalizedY,
                joystick.lastX, joystick.lastY);
  Serial.printf("==================\n");
}
