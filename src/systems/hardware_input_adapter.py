# -*- coding: utf-8 -*-
"""
Hardware Input Adapter - Brücke zwischen Hardware Interface und Action System
Konvertiert Hardware-Events in abstrakte Actions
"""

import pygame
import time
from typing import Optional, Dict, Any
from systems.hardware_interface import HardwareInterface
from systems.action_system import get_action_system, ActionType
try:
    from core.settings import VERBOSE_LOGS
except Exception:
    VERBOSE_LOGS = False

class HardwareInputAdapter:
    """
    Adapter der Hardware Events in abstrakte Actions konvertiert
    Registriert sich beim HardwareInterface und dispatcht Actions
    """
    
    def __init__(self, hardware_interface: HardwareInterface):
        """
        Initialize hardware input adapter
        
        Args:
            hardware_interface: Instance of HardwareInterface
        """
        self.hardware = hardware_interface
        self.action_system = get_action_system()
        self.enabled = True
        
        # Movement deadzone and sensitivity
        self.movement_deadzone = 0.1
        self.last_movement_state = {'left': False, 'right': False, 'up': False, 'down': False}
        
        # Register callbacks with hardware interface
        self._register_hardware_callbacks()
        
        if VERBOSE_LOGS:
            print("🔌 Hardware Input Adapter initialisiert")
    
    def _register_hardware_callbacks(self):
        """Register callbacks with the hardware interface"""
        self.hardware.register_callback("BUTTON_ACTION", self._handle_button_action)
        self.hardware.register_callback("JOYSTICK_MOVE", self._handle_joystick_move)
    
    def _handle_button_action(self, data: Dict[str, Any]):
        """Handle button action from hardware"""
        if not self.enabled:
            return
        
        action_name = data.get('action')
        pressed = data.get('pressed', False)
        button_id = data.get('button_id', 'unknown')
        
        # Map to ActionType
        action_map = {
            'magic_fire': ActionType.MAGIC_FIRE,
            'magic_water': ActionType.MAGIC_WATER,
            'magic_stone': ActionType.MAGIC_STONE,
            'cast_magic': ActionType.CAST_MAGIC,
            'clear_magic': ActionType.CLEAR_MAGIC
        }
        action_type = action_map.get(action_name) if isinstance(action_name, str) else None
        if action_type:
            # Special handling for magic actions
            if action_type in [ActionType.MAGIC_FIRE, ActionType.MAGIC_WATER, ActionType.MAGIC_STONE, 
                             ActionType.CAST_MAGIC, ActionType.CLEAR_MAGIC]:
                self.action_system.handle_magic_action(action_type, pressed, "hardware")
            else:
                self.action_system.dispatch_action(action_type, pressed, "hardware")
            
            if VERBOSE_LOGS:
                print(f"🔘 Hardware Button: {button_id} -> {action_name} ({'PRESS' if pressed else 'RELEASE'})")
        else:
            if VERBOSE_LOGS:
                print(f"⚠️ Unbekannte Hardware Action: {action_name}")
    
    def _handle_joystick_move(self, data: Dict[str, Any]):
        """Handle joystick movement from hardware"""
        if not self.enabled:
            return
        
        x = data.get('x', 0.0)
        y = data.get('y', 0.0)
        
        # Convert to movement actions with deadzone
        new_movement = {
            'left': x < -self.movement_deadzone,
            'right': x > self.movement_deadzone,
            'up': y < -self.movement_deadzone,
            'down': y > self.movement_deadzone
        }
        
        # Only send actions on state change to avoid spam
        for direction, active in new_movement.items():
            if active != self.last_movement_state[direction]:
                action_map = {
                    'left': ActionType.MOVE_LEFT,
                    'right': ActionType.MOVE_RIGHT,
                    'up': ActionType.MOVE_UP,
                    'down': ActionType.MOVE_DOWN
                }
                
                action_type = action_map[direction]
                self.action_system.dispatch_action(action_type, active, "hardware")
                
                if active and VERBOSE_LOGS:
                    print(f"🕹️ Hardware Joystick: {direction.upper()}")
        
        self.last_movement_state = new_movement
    
    def update(self):
        """Update the adapter (should be called once per frame)"""
        if not self.enabled:
            return
        
        # Poll hardware messages
        messages_processed = self.hardware.poll_messages()
        
        # Check if hardware is still active
        if not self.hardware.is_hardware_active():
            # Hardware timeout - could emit warning or fallback
            pass
    
    def enable(self):
        """Enable hardware input processing"""
        self.enabled = True
        if VERBOSE_LOGS:
            print("✅ Hardware Input aktiviert")
    
    def disable(self):
        """Disable hardware input processing"""
        self.enabled = False
        if VERBOSE_LOGS:
            print("❌ Hardware Input deaktiviert")
    
    def get_movement_vector(self) -> pygame.math.Vector2:
        """Get current movement vector from hardware joystick"""
        if not self.enabled or not self.hardware.is_hardware_active():
            return pygame.math.Vector2(0, 0)
        
        return self.hardware.get_joystick_vector()
    
    def test_all_buttons(self):
        """Test all hardware buttons (development helper)"""
        if not self.hardware.mock_mode:
            if VERBOSE_LOGS:
                print("⚠️ Button test nur im Mock-Mode verfügbar")
            return
        
        if VERBOSE_LOGS:
            print("🧪 Testing all hardware buttons...")
        
        buttons = ["FIRE", "WATER", "STONE", "CAST", "CLEAR"]
        for button in buttons:
            if VERBOSE_LOGS:
                print(f"  Testing {button}...")
            self.hardware.simulate_button_press(button)
            time.sleep(0.5)
        
        if VERBOSE_LOGS:
            print("✅ Button test abgeschlossen")
    
    def test_joystick(self):
        """Test hardware joystick (development helper)"""
        if not self.hardware.mock_mode:
            if VERBOSE_LOGS:
                print("⚠️ Joystick test nur im Mock-Mode verfügbar")
            return
        
        if VERBOSE_LOGS:
            print("🕹️ Testing hardware joystick...")
        
        # Test all directions
        directions = [
            (0, -1, "UP"),
            (1, 0, "RIGHT"), 
            (0, 1, "DOWN"),
            (-1, 0, "LEFT"),
            (0, 0, "CENTER")
        ]
        
        for x, y, name in directions:
            if VERBOSE_LOGS:
                print(f"  Testing {name} ({x}, {y})...")
            self.hardware.simulate_joystick_move(x, y)
            time.sleep(0.5)
        
        if VERBOSE_LOGS:
            print("✅ Joystick test abgeschlossen")

# Factory function für einfache Integration
def create_hardware_input_adapter(port='/dev/ttyUSB0', mock_mode=True) -> Optional[HardwareInputAdapter]:
    """
    Factory function to create and initialize hardware input adapter
    
    Args:
        port: Serial port for hardware connection
        mock_mode: Whether to run in mock mode for development
        
    Returns:
        HardwareInputAdapter instance or None if failed
    """
    try:
        # Create hardware interface
        hardware = HardwareInterface(port=port, mock_mode=mock_mode)
        
        # Try to connect
        if hardware.connect():
            # Create adapter
            adapter = HardwareInputAdapter(hardware)
            if VERBOSE_LOGS:
                print("✅ Hardware Input Adapter erfolgreich erstellt")
            return adapter
        else:
            if VERBOSE_LOGS:
                print("❌ Hardware Interface Verbindung fehlgeschlagen")
            return None
    
    except Exception as e:
        if VERBOSE_LOGS:
            print(f"❌ Fehler beim Erstellen des Hardware Input Adapters: {e}")
        return None
