# hardware_interface.py
# Interface für die Kommunikation zwischen Raspberry Pi und ESP32

import serial
import json
import threading
import time
from typing import Callable, Dict, Any, Optional
from collections import deque
import pygame

try:
    from core.settings import VERBOSE_LOGS
except Exception:
    VERBOSE_LOGS = False

class HardwareInterface:
    """
    Verwaltet die Kommunikation zwischen Raspberry Pi (Spiel) und ESP32 (Hardware)
    """
    
    def __init__(self, port='/dev/ttyUSB0', baud_rate=115200, mock_mode=True):
        self.port = port
        self.baud_rate = baud_rate
        self.mock_mode = mock_mode
        self.serial_connection: Optional[serial.Serial] = None
        self.is_connected = False
        
        # Message handling
        self.message_callbacks = {}
        self.message_queue = deque()  # Thread-safe queue for incoming messages
        
        # Thread für kontinuierliches Lesen
        self.read_thread = None
        self.running = False
        
        # Hardware state tracking
        self.last_joystick_vector = pygame.math.Vector2(0, 0)
        self.button_states = {}  # Track button states for edge detection
        self.last_heartbeat = 0
        self.heartbeat_timeout = 3.0  # Seconds
        
        # Mock-Daten für Entwicklung ohne Hardware
        self.mock_tokens = {}
        
        if VERBOSE_LOGS:
            print(f"🔌 Hardware Interface initialisiert (Mock-Mode: {mock_mode})")
        
    def connect(self):
        """Verbindung zum ESP32 herstellen"""
        if self.mock_mode:
            if VERBOSE_LOGS:
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
            
            if VERBOSE_LOGS:
                print(f"✅ Verbunden mit ESP32 auf {self.port}")
            return True
            
        except Exception as e:
            if VERBOSE_LOGS:
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
        if VERBOSE_LOGS:
            print("🔌 Hardware-Verbindung getrennt")
    
    def register_callback(self, message_type: str, callback: Callable):
        """Callback für bestimmten Message-Typ registrieren"""
        self.message_callbacks[message_type] = callback
        if VERBOSE_LOGS:
            print(f"📋 Callback registriert für: {message_type}")
    
    def send_message(self, message_type: str, data: Dict[str, Any]):
        """Nachricht an ESP32 senden"""
        message = {
            'type': message_type,
            'data': data,
            'timestamp': time.time()
        }
        
        if self.mock_mode:
            if VERBOSE_LOGS:
                print(f"🎭 Mock-Send: {message}")
            return True
            
        if not self.is_connected:
            if VERBOSE_LOGS:
                print("❌ Nicht verbunden - kann nicht senden")
            return False
            
        try:
            message_json = json.dumps(message) + '\n'
            sc = self.serial_connection
            if sc is None:
                return False
            sc.write(message_json.encode())
            return True
        except Exception as e:
            if VERBOSE_LOGS:
                print(f"❌ Sende-Fehler: {e}")
            return False
    
    def _read_messages(self):
        """Kontinuierlich Nachrichten vom ESP32 lesen (läuft in eigenem Thread)"""
        while self.running and self.is_connected:
            try:
                sc = self.serial_connection
                if sc is None:
                    time.sleep(0.01)
                    continue
                if sc.in_waiting > 0:
                    line = sc.readline().decode().strip()
                    if line:
                        message = json.loads(line)
                        self._handle_message(message)
            except Exception as e:
                if VERBOSE_LOGS:
                    print(f"❌ Lese-Fehler: {e}")
            
            time.sleep(0.01)  # Kurze Pause
    
    def _handle_message(self, message: Dict[str, Any]):
        """Empfangene Nachricht verarbeiten"""
        message_type = message.get('type')
        
        # Add to queue for thread-safe processing
        self.message_queue.append(message)
        
        if self.mock_mode and message_type != "PING" and VERBOSE_LOGS:
            print(f"📨 Hardware empfangen: {message_type} - {message}")
        
        # Handle different message types
        if message_type == "BUTTON":
            self._handle_button_message(message)
        elif message_type == "JOYSTICK":
            self._handle_joystick_message(message)
        elif message_type == "HEARTBEAT":
            self.last_heartbeat = time.time()
        elif message_type == "PING":
            # Respond to ping
            self.send_message("PONG", {"fw": "pi_1.0"})
        elif message_type == "STATUS" and VERBOSE_LOGS:
            print(f"📡 Hardware Status: {message.get('code', 'unknown')}")
        
        # Legacy callback system
        if message_type in self.message_callbacks:
            data = message.get('data', message)  # Backward compatibility
            self.message_callbacks[message_type](data)
    
    def _handle_button_message(self, message: Dict[str, Any]):
        """Handle BUTTON message type"""
        button_id = message.get('id')
        state = message.get('state', 0)
        
        if button_id:
            # Track state for edge detection
            old_state = self.button_states.get(button_id, 0)
            self.button_states[button_id] = state
            
            # Only trigger callback on state change
            if old_state != state:
                # Map hardware button IDs to logical actions
                button_map = {
                    "FIRE": "magic_fire",
                    "WATER": "magic_water", 
                    "STONE": "magic_stone",
                    "CAST": "cast_magic",
                    "CLEAR": "clear_magic"
                }
                
                action = button_map.get(button_id)
                if action and "BUTTON_ACTION" in self.message_callbacks:
                    self.message_callbacks["BUTTON_ACTION"]({
                        "action": action,
                        "pressed": bool(state),
                        "button_id": button_id
                    })
    
    def _handle_joystick_message(self, message: Dict[str, Any]):
        """Handle JOYSTICK message type"""
        x = message.get('x', 0.0)
        y = message.get('y', 0.0)
        
        # Only process if significant change (delta > 0.05)
        new_vector = pygame.math.Vector2(x, y)
        delta = new_vector.distance_to(self.last_joystick_vector)
        
        if delta > 0.05:
            self.last_joystick_vector = new_vector
            
            if "JOYSTICK_MOVE" in self.message_callbacks:
                self.message_callbacks["JOYSTICK_MOVE"]({
                    "x": x,
                    "y": y,
                    "vector": new_vector
                })
    
    def poll_messages(self) -> int:
        """
        Poll and process queued messages (non-blocking)
        Should be called once per frame from main thread
        
        Returns:
            Number of messages processed
        """
        processed = 0
        
        # Process all queued messages
        while self.message_queue:
            try:
                message = self.message_queue.popleft()
                # Message already processed in _handle_message, just count
                processed += 1
            except IndexError:
                break
        
        return processed
    
    def is_hardware_active(self) -> bool:
        """Check if hardware is actively connected and responsive"""
        if not self.is_connected:
            return False
        
        # In mock mode, always active
        if self.mock_mode:
            return True
        
        # Check heartbeat timeout
        return (time.time() - self.last_heartbeat) < self.heartbeat_timeout
    
    def get_joystick_vector(self) -> pygame.math.Vector2:
        """Get current joystick vector"""
        return self.last_joystick_vector.copy()
    
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
    
    def simulate_button_press(self, button_id: str = "FIRE"):
        """Mock: Button-Press simulieren (nur für Entwicklung)"""
        if self.mock_mode:
            # Send press event
            self._handle_message({
                "type": "BUTTON",
                "id": button_id,
                "state": 1
            })
            
            # Send release event after short delay (simulated in separate thread)
            def delayed_release():
                time.sleep(0.1)  # 100ms press duration
                self._handle_message({
                    "type": "BUTTON",
                    "id": button_id,
                    "state": 0
                })
            
            thread = threading.Thread(target=delayed_release)
            thread.daemon = True
            thread.start()
    
    def simulate_joystick_move(self, x: float, y: float):
        """Mock: Joystick-Bewegung simulieren"""
        if self.mock_mode:
            self._handle_message({
                "type": "JOYSTICK",
                "x": x,
                "y": y
            })
    
    def simulate_heartbeat(self):
        """Mock: Heartbeat simulieren"""
        if self.mock_mode:
            self._handle_message({
                "type": "HEARTBEAT"
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
