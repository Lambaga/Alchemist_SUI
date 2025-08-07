# -*- coding: utf-8 -*-
"""
Universelles Input-System für Der Alchemist
Unterstützt Tastatur, Maus und Joystick/Gamepad für Raspberry Pi 4
"""

import pygame
from typing import Dict, List, Tuple, Optional, Union
from enum import Enum

class InputDevice(Enum):
    """Input-Device Typen"""
    KEYBOARD = "keyboard"
    MOUSE = "mouse" 
    JOYSTICK = "joystick"

class GamepadButton(Enum):
    """Standard-Gamepad-Buttons (Xbox/PS4 Layout)"""
    A = 0          # A/X Button
    B = 1          # B/Circle Button  
    X = 2          # X/Square Button
    Y = 3          # Y/Triangle Button
    L1 = 4         # Left Bumper
    R1 = 5         # Right Bumper
    BACK = 6       # Back/Share Button
    START = 7      # Start/Options Button
    L3 = 8         # Left Stick Click
    R3 = 9         # Right Stick Click
    DPAD_UP = 10   # D-Pad Up
    DPAD_DOWN = 11 # D-Pad Down
    DPAD_LEFT = 12 # D-Pad Left
    DPAD_RIGHT = 13# D-Pad Right

class UniversalInputSystem:
    """
    Universelles Input-System das Tastatur, Maus und Joystick unterstützt
    Perfekt für Raspberry Pi 4 mit angeschlossenen Gamepads
    """
    
    def __init__(self):
        """Initialisiert das Input-System"""
        self.joysticks = []
        self.active_joystick = None
        
        # Input-Mappings
        self.movement_mapping = self._create_movement_mapping()
        self.action_mapping = self._create_action_mapping()
        
        # Input-Status
        self.movement_state = {
            'left': False,
            'right': False, 
            'up': False,
            'down': False
        }
        
        # Analog-Stick Einstellungen
        self.stick_deadzone = 0.15  # Deadzone für Analog-Sticks
        self.stick_sensitivity = 1.0
        
        # Joystick initialisieren
        self._init_joysticks()
        
        print("🎮 Universal Input System initialisiert")
        print(f"📱 Gefundene Joysticks: {len(self.joysticks)}")
        
    def _init_joysticks(self):
        """Initialisiert alle verfügbaren Joysticks"""
        pygame.joystick.init()
        joystick_count = pygame.joystick.get_count()
        
        for i in range(joystick_count):
            try:
                joystick = pygame.joystick.Joystick(i)
                joystick.init()
                self.joysticks.append(joystick)
                
                print(f"✅ Joystick {i} verbunden: {joystick.get_name()}")
                print(f"   Achsen: {joystick.get_numaxes()}")
                print(f"   Buttons: {joystick.get_numbuttons()}")
                print(f"   Hats: {joystick.get_numhats()}")
                
                # Ersten Joystick als aktiv setzen
                if self.active_joystick is None:
                    self.active_joystick = joystick
                    print(f"🎯 Aktiver Joystick: {joystick.get_name()}")
                    
            except pygame.error as e:
                print(f"❌ Fehler beim Initialisieren von Joystick {i}: {e}")
    
    def _create_movement_mapping(self) -> Dict:
        """Erstellt Bewegungs-Mappings für alle Input-Devices"""
        return {
            InputDevice.KEYBOARD: {
                'left': [pygame.K_LEFT, pygame.K_a],
                'right': [pygame.K_RIGHT, pygame.K_d],
                'up': [pygame.K_UP, pygame.K_w],
                'down': [pygame.K_DOWN, pygame.K_s]
            },
            InputDevice.JOYSTICK: {
                'left': {'axis': 0, 'threshold': -0.5},   # Left Stick X-Achse
                'right': {'axis': 0, 'threshold': 0.5},
                'up': {'axis': 1, 'threshold': -0.5},     # Left Stick Y-Achse  
                'down': {'axis': 1, 'threshold': 0.5},
                'dpad_left': GamepadButton.DPAD_LEFT.value,
                'dpad_right': GamepadButton.DPAD_RIGHT.value,
                'dpad_up': GamepadButton.DPAD_UP.value,
                'dpad_down': GamepadButton.DPAD_DOWN.value
            }
        }
    
    def _create_action_mapping(self) -> Dict:
        """Erstellt Action-Mappings für alle Input-Devices"""
        return {
            InputDevice.KEYBOARD: {
                'brew': pygame.K_SPACE,
                'remove_ingredient': pygame.K_BACKSPACE,
                'reset': pygame.K_r,
                'music_toggle': pygame.K_m,
                'pause': pygame.K_ESCAPE,
                'ingredient_1': pygame.K_1,
                'ingredient_2': pygame.K_2,
                'ingredient_3': pygame.K_3,
                'cast_magic': pygame.K_c,
                'clear_magic': pygame.K_x
            },
            InputDevice.JOYSTICK: {
                'brew': GamepadButton.A.value,           # A/X Button
                'remove_ingredient': GamepadButton.B.value,  # B/Circle Button
                'reset': GamepadButton.Y.value,          # Y/Triangle Button
                'music_toggle': GamepadButton.X.value,   # X/Square Button
                'pause': GamepadButton.START.value,      # Start/Options Button
                'ingredient_1': GamepadButton.L1.value,  # Left Bumper
                'ingredient_2': GamepadButton.R1.value,  # Right Bumper
                'ingredient_3': GamepadButton.BACK.value, # Back/Share Button
                # Magie-Elemente (Zusätzliche Buttons)
                'magic_fire': GamepadButton.L3.value,    # Left Stick Click
                'magic_water': GamepadButton.R3.value,   # Right Stick Click  
                'magic_stone': 14,  # Zusätzlicher Button falls vorhanden
                'cast_magic': 15,   # Zusätzlicher Button falls vorhanden
                'clear_magic': 16   # Zusätzlicher Button falls vorhanden
            }
        }
    
    def update(self):
        """Update Input-System (sollte jeden Frame aufgerufen werden)"""
        self._update_movement_state()
    
    def _update_movement_state(self):
        """Aktualisiert den Bewegungsstatus basierend auf allen Inputs"""
        # Reset movement state
        for direction in self.movement_state:
            self.movement_state[direction] = False
        
        # Tastatur-Input prüfen
        keys = pygame.key.get_pressed()
        keyboard_mapping = self.movement_mapping[InputDevice.KEYBOARD]
        
        for direction, key_list in keyboard_mapping.items():
            for key in key_list:
                if keys[key]:
                    self.movement_state[direction] = True
                    break
        
        # Joystick-Input prüfen
        if self.active_joystick:
            joystick_mapping = self.movement_mapping[InputDevice.JOYSTICK]
            
            # Analog-Stick prüfen
            try:
                # Left Stick X-Achse
                left_x = self.active_joystick.get_axis(0)
                if abs(left_x) > self.stick_deadzone:
                    if left_x < -self.stick_deadzone:
                        self.movement_state['left'] = True
                    elif left_x > self.stick_deadzone:
                        self.movement_state['right'] = True
                
                # Left Stick Y-Achse
                left_y = self.active_joystick.get_axis(1)
                if abs(left_y) > self.stick_deadzone:
                    if left_y < -self.stick_deadzone:
                        self.movement_state['up'] = True
                    elif left_y > self.stick_deadzone:
                        self.movement_state['down'] = True
                
                # D-Pad prüfen
                if self.active_joystick.get_button(GamepadButton.DPAD_LEFT.value):
                    self.movement_state['left'] = True
                if self.active_joystick.get_button(GamepadButton.DPAD_RIGHT.value):
                    self.movement_state['right'] = True
                if self.active_joystick.get_button(GamepadButton.DPAD_UP.value):
                    self.movement_state['up'] = True
                if self.active_joystick.get_button(GamepadButton.DPAD_DOWN.value):
                    self.movement_state['down'] = True
                    
            except pygame.error:
                # Joystick wurde getrennt
                self.active_joystick = None
                print("⚠️ Joystick getrennt")
    
    def is_action_pressed(self, action: str) -> bool:
        """Prüft ob eine Action gerade gedrückt wird (alle Input-Devices)"""
        # Tastatur prüfen
        keys = pygame.key.get_pressed()
        keyboard_actions = self.action_mapping[InputDevice.KEYBOARD]
        if action in keyboard_actions and keys[keyboard_actions[action]]:
            return True
        
        # Joystick prüfen
        if self.active_joystick and action in self.action_mapping[InputDevice.JOYSTICK]:
            button = self.action_mapping[InputDevice.JOYSTICK][action]
            try:
                return self.active_joystick.get_button(button)
            except pygame.error:
                self.active_joystick = None
                return False
        
        return False
    
    def get_movement_vector(self) -> pygame.math.Vector2:
        """Gibt den aktuellen Bewegungsvektor zurück"""
        direction = pygame.math.Vector2(0, 0)
        
        if self.movement_state['left']:
            direction.x -= 1
        if self.movement_state['right']:
            direction.x += 1
        if self.movement_state['up']:
            direction.y -= 1
        if self.movement_state['down']:
            direction.y += 1
        
        return direction
    
    def get_right_stick_vector(self) -> pygame.math.Vector2:
        """Gibt den rechten Analog-Stick als Vektor zurück (für Blickrichtung)"""
        if not self.active_joystick:
            return pygame.math.Vector2(0, 0)
        
        try:
            # Right Stick (normalerweise Achse 2 und 3)
            if self.active_joystick.get_numaxes() >= 4:
                right_x = self.active_joystick.get_axis(2)
                right_y = self.active_joystick.get_axis(3)
                
                # Deadzone anwenden
                if abs(right_x) < self.stick_deadzone:
                    right_x = 0
                if abs(right_y) < self.stick_deadzone:
                    right_y = 0
                
                return pygame.math.Vector2(right_x, right_y) * self.stick_sensitivity
                
        except pygame.error:
            self.active_joystick = None
        
        return pygame.math.Vector2(0, 0)
    
    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """
        Behandelt Input-Events und gibt Action-Namen zurück
        Kompatibel mit dem bestehenden Event-System
        """
        action = None
        
        # Joystick-Events
        if event.type == pygame.JOYBUTTONDOWN:
            joystick_actions = self.action_mapping[InputDevice.JOYSTICK]
            for action_name, button in joystick_actions.items():
                if event.button == button:
                    return action_name
        
        # Joystick-Verbindung/Trennung
        elif event.type == pygame.JOYDEVICEADDED:
            print(f"🎮 Neuer Joystick verbunden: Index {event.device_index}")
            self._init_joysticks()
            
        elif event.type == pygame.JOYDEVICEREMOVED:
            print(f"🎮 Joystick getrennt: Index {event.instance_id}")
            # Joystick-Liste aktualisieren
            self.joysticks = [j for j in self.joysticks if j.get_instance_id() != event.instance_id]
            if self.active_joystick and self.active_joystick.get_instance_id() == event.instance_id:
                self.active_joystick = self.joysticks[0] if self.joysticks else None
        
        # Tastatur-Events (für Kompatibilität)
        elif event.type == pygame.KEYDOWN:
            keyboard_actions = self.action_mapping[InputDevice.KEYBOARD]
            for action_name, key in keyboard_actions.items():
                if event.key == key:
                    return action_name
        
        return None
    
    def get_joystick_info(self) -> Dict:
        """Gibt Informationen über angeschlossene Joysticks zurück"""
        info = {
            'count': len(self.joysticks),
            'active': None,
            'devices': []
        }
        
        for i, joystick in enumerate(self.joysticks):
            device_info = {
                'index': i,
                'name': joystick.get_name(),
                'axes': joystick.get_numaxes(),
                'buttons': joystick.get_numbuttons(),
                'hats': joystick.get_numhats(),
                'is_active': joystick == self.active_joystick
            }
            info['devices'].append(device_info)
            
            if joystick == self.active_joystick:
                info['active'] = device_info
        
        return info
    
    def set_active_joystick(self, index: int) -> bool:
        """Setzt einen bestimmten Joystick als aktiv"""
        if 0 <= index < len(self.joysticks):
            self.active_joystick = self.joysticks[index]
            print(f"🎯 Aktiver Joystick gewechselt zu: {self.active_joystick.get_name()}")
            return True
        return False
    
    def print_control_scheme(self):
        """Gibt das aktuelle Kontroll-Schema aus"""
        print("\n🎮 UNIVERSELLES KONTROLL-SCHEMA:")
        print("="*50)
        
        print("\n📱 TASTATUR:")
        print("   Bewegung: WASD / Pfeiltasten")
        print("   Brauen: Leertaste")
        print("   Zutat entfernen: Backspace")
        print("   Reset: R")
        print("   Musik: M")
        print("   Pause: ESC")
        print("   Zutaten: 1, 2, 3")
        
        if self.active_joystick:
            print(f"\n🎮 GAMEPAD ({self.active_joystick.get_name()}):")
            print("   Bewegung: Left Stick / D-Pad")
            print("   Blickrichtung: Right Stick")
            print("   Brauen: A/X Button")
            print("   Zutat entfernen: B/Circle Button")
            print("   Reset: Y/Triangle Button") 
            print("   Musik: X/Square Button")
            print("   Pause: Start/Options Button")
            print("   Zutaten: L1, R1, Back/Share")
        else:
            print("\n🎮 GAMEPAD: Nicht verbunden")
        
        print("="*50)

# Globale Input-System Instanz für einfachen Zugriff
universal_input = None

def get_input_system() -> UniversalInputSystem:
    """Gibt die globale Input-System Instanz zurück"""
    global universal_input
    if universal_input is None:
        universal_input = UniversalInputSystem()
    return universal_input

def init_universal_input() -> UniversalInputSystem:
    """Initialisiert das universelle Input-System"""
    global universal_input
    universal_input = UniversalInputSystem()
    return universal_input
