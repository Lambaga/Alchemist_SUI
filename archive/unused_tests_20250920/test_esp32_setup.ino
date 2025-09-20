/*
 * ESP32 Installation Test
 * Sollte "Hello ESP32!" im Serial Monitor ausgeben
 */

void setup() {
  Serial.begin(115200);
  Serial.println("Hello ESP32!");
  Serial.printf("Chip Model: %s\n", ESP.getChipModel());
  Serial.printf("Chip Revision: %d\n", ESP.getChipRevision());
  Serial.printf("CPU Frequency: %d MHz\n", ESP.getCpuFreqMHz());
  Serial.printf("Flash Size: %d bytes\n", ESP.getFlashChipSize());
}

void loop() {
  Serial.println("ESP32 läuft korrekt!");
  delay(2000);
}
