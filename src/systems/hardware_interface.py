# hardware_interface.py
# Interface für die Kommunikation zwischen Raspberry Pi und ESP32

import serial
import json
import threading
import time
from typing import Callable, Dict, Any

class HardwareInterface:
    """
    Verwaltet die Kommunikation zwischen Raspberry Pi (Spiel) und ESP32 (Hardware)
    """
    
    def __init__(self, port='/dev/ttyUSB0', baud_rate=115200, mock_mode=True):
        self.port = port
        self.baud_rate = baud_rate
        self.mock_mode = mock_mode
        self.serial_connection = None
        self.is_connected = False
        self.message_callbacks = {}
        
        # Thread für kontinuierliches Lesen
        self.read_thread = None
        self.running = False
        
        # Mock-Daten für Entwicklung ohne Hardware
        self.mock_tokens = {}
        
        print(f"🔌 Hardware Interface initialisiert (Mock-Mode: {mock_mode})")
        
    def connect(self):
        """Verbindung zum ESP32 herstellen"""
        if self.mock_mode:
            print("🎭 Mock-Mode: Simuliere Hardware-Verbindung")
            self.is_connected = True
            return True
            
        try:
            self.serial_connection = serial.Serial(self.port, self.baud_rate, timeout=1)
            time.sleep(2)  # Warten bis ESP32 bereit ist
            self.is_connected = True
            
            # Lese-Thread starten
            self.running = True
            self.read_thread = threading.Thread(target=self._read_messages)
            self.read_thread.start()
            
            print(f"✅ Verbunden mit ESP32 auf {self.port}")
            return True
            
        except Exception as e:
            print(f"❌ Verbindung fehlgeschlagen: {e}")
            return False
    
    def disconnect(self):
        """Verbindung trennen"""
        self.running = False
        if self.read_thread:
            self.read_thread.join()
        
        if self.serial_connection:
            self.serial_connection.close()
        
        self.is_connected = False
        print("🔌 Hardware-Verbindung getrennt")
    
    def register_callback(self, message_type: str, callback: Callable):
        """Callback für bestimmten Message-Typ registrieren"""
        self.message_callbacks[message_type] = callback
        print(f"📋 Callback registriert für: {message_type}")
    
    def send_message(self, message_type: str, data: Dict[str, Any]):
        """Nachricht an ESP32 senden"""
        message = {
            'type': message_type,
            'data': data,
            'timestamp': time.time()
        }
        
        if self.mock_mode:
            print(f"🎭 Mock-Send: {message}")
            return True
            
        if not self.is_connected:
            print("❌ Nicht verbunden - kann nicht senden")
            return False
            
        try:
            message_json = json.dumps(message) + '\n'
            self.serial_connection.write(message_json.encode())
            return True
        except Exception as e:
            print(f"❌ Sende-Fehler: {e}")
            return False
    
    def _read_messages(self):
        """Kontinuierlich Nachrichten vom ESP32 lesen (läuft in eigenem Thread)"""
        while self.running and self.is_connected:
            try:
                if self.serial_connection.in_waiting > 0:
                    line = self.serial_connection.readline().decode().strip()
                    if line:
                        message = json.loads(line)
                        self._handle_message(message)
            except Exception as e:
                print(f"❌ Lese-Fehler: {e}")
            
            time.sleep(0.01)  # Kurze Pause
    
    def _handle_message(self, message: Dict[str, Any]):
        """Empfangene Nachricht verarbeiten"""
        message_type = message.get('type')
        data = message.get('data', {})
        
        print(f"📨 Empfangen: {message_type} - {data}")
        
        # Callback aufrufen falls registriert
        if message_type in self.message_callbacks:
            self.message_callbacks[message_type](data)
    
    # Hardware-spezifische Methoden
    def set_led_effect(self, effect_type: str, color: str = "blue"):
        """LED-Effekt setzen"""
        self.send_message("LED_EFFECT", {
            "effect": effect_type,
            "color": color
        })
    
    def simulate_token_placed(self, token_name: str, token_id: str = "mock_123"):
        """Mock: Token-Platzierung simulieren (nur für Entwicklung)"""
        if self.mock_mode:
            self.mock_tokens[token_id] = token_name
            if "TOKEN_PLACED" in self.message_callbacks:
                self.message_callbacks["TOKEN_PLACED"]({
                    "token_name": token_name,
                    "token_id": token_id
                })
    
    def simulate_token_removed(self, token_id: str = "mock_123"):
        """Mock: Token-Entfernung simulieren (nur für Entwicklung)"""
        if self.mock_mode and token_id in self.mock_tokens:
            token_name = self.mock_tokens.pop(token_id)
            if "TOKEN_REMOVED" in self.message_callbacks:
                self.message_callbacks["TOKEN_REMOVED"]({
                    "token_name": token_name,
                    "token_id": token_id
                })
    
    def simulate_button_press(self, button_name: str = "brew"):
        """Mock: Button-Press simulieren (nur für Entwicklung)"""
        if self.mock_mode:
            if "BUTTON_PRESSED" in self.message_callbacks:
                self.message_callbacks["BUTTON_PRESSED"]({
                    "button": button_name
                })

# Beispiel für Integration in das Spiel
if __name__ == "__main__":
    print("🧪 Hardware Interface Test")
    
    # Hardware Interface erstellen (Mock-Mode für Entwicklung)
    hw = HardwareInterface(mock_mode=True)
    hw.connect()
    
    # Callbacks definieren
    def on_token_placed(data):
        print(f"🎯 Token platziert: {data['token_name']} (ID: {data['token_id']})")
    
    def on_button_pressed(data):
        print(f"🔘 Button gedrückt: {data['button']}")
    
    # Callbacks registrieren
    hw.register_callback("TOKEN_PLACED", on_token_placed)
    hw.register_callback("BUTTON_PRESSED", on_button_pressed)
    
    # Test-Simulationen
    print("\n--- SIMULATION STARTEN ---")
    time.sleep(1)
    
    hw.simulate_token_placed("wasserkristall", "nfc_001")
    time.sleep(0.5)
    hw.simulate_token_placed("feueressenz", "nfc_002")
    time.sleep(0.5)
    hw.simulate_button_press("brew")
    time.sleep(0.5)
    hw.set_led_effect("success", "green")
    
    print("\n--- TEST BEENDET ---")
    hw.disconnect()
