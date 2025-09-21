# -*- coding: utf-8 -*-
"""
Action System - Zentrale Aktions-Verwaltung für Der Alchemist
Abstraktion für alle Input-Quellen (Tastatur, Gamepad, Hardware)
"""

from enum import Enum
from typing import Dict, List, Callable, Optional
from dataclasses import dataclass
import pygame
import time

class ActionType(Enum):
    """Verfügbare Aktionen im Spiel"""
    # Bewegung
    MOVE_LEFT = "move_left"
    MOVE_RIGHT = "move_right"
    MOVE_UP = "move_up"
    MOVE_DOWN = "move_down"
    
    # Magic System
    MAGIC_FIRE = "magic_fire"
    MAGIC_WATER = "magic_water"
    MAGIC_STONE = "magic_stone"
    CAST_MAGIC = "cast_magic"
    CLEAR_MAGIC = "clear_magic"
    
    # Combat
    ATTACK = "attack"
    
    # UI/System
    PAUSE = "pause"
    MUSIC_TOGGLE = "music_toggle"
    RESET_GAME = "reset_game"
    
    # Debug
    TOGGLE_DEBUG = "toggle_debug"
    TOGGLE_FPS = "toggle_fps"

@dataclass
class ActionEvent:
    """Repräsentiert ein Aktions-Event"""
    action: ActionType
    pressed: bool  # True = press, False = release
    source: str    # "keyboard", "gamepad", "hardware"
    timestamp: float
    
    def __post_init__(self):
        if self.timestamp == 0:
            self.timestamp = time.time()

class ActionSystem:
    """
    Zentrale Aktions-Verwaltung die alle Input-Quellen koordiniert
    """
    
    def __init__(self):
        """Initialisiert das Action System"""
        self.action_handlers: Dict[ActionType, List[Callable[[ActionEvent], None]]] = {}
        self.action_state: Dict[ActionType, bool] = {}
        self.input_priority = ["hardware", "gamepad", "keyboard"]  # Höchste zu niedrigste Priorität
        self.last_input_source: Dict[ActionType, str] = {}
        self.source_timeout = 2.0  # Sekunden bis Fallback zu niedrigerer Priorität
        self.last_input_time: Dict[ActionType, float] = {}
        
        # Magic System Integration
        self.magic_handler = None
        
        # Debug
        self.debug_enabled = False
        
        try:
            from core.settings import VERBOSE_LOGS
        except Exception:
            VERBOSE_LOGS = False  # type: ignore
        if VERBOSE_LOGS:  # type: ignore[name-defined]
            print("🎯 Action System initialisiert")
    
    def register_handler(self, action: ActionType, handler: Callable[[ActionEvent], None]):
        """Registriert einen Handler für eine Aktion"""
        if action not in self.action_handlers:
            self.action_handlers[action] = []
        self.action_handlers[action].append(handler)
        
        if self.debug_enabled:
            print(f"📋 Handler registriert für {action.value}")
    
    def dispatch_action(self, action: ActionType, pressed: bool, source: str = "unknown"):
        """Versendet eine Aktion an alle registrierten Handler"""
        current_time = time.time()
        
        # Priorisierung: Höhere Priorität überschreibt niedrigere
        if action in self.last_input_source:
            last_source = self.last_input_source[action]
            last_time = self.last_input_time.get(action, 0)
            
            # Wenn letzte Eingabe von höherer Priorität und noch nicht timeout
            if (self._get_source_priority(last_source) > self._get_source_priority(source) and 
                current_time - last_time < self.source_timeout):
                if self.debug_enabled:
                    print(f"🚫 Action {action.value} ignoriert - {last_source} hat Priorität")
                return
        
        # Update state tracking
        self.action_state[action] = pressed
        self.last_input_source[action] = source
        self.last_input_time[action] = current_time
        
        # Create action event
        event = ActionEvent(action, pressed, source, current_time)
        
        # Debug output
        if self.debug_enabled:
            status = "PRESS" if pressed else "RELEASE"
            print(f"⚡ {status}: {action.value} from {source}")
        
        # Dispatch to handlers
        if action in self.action_handlers:
            for handler in self.action_handlers[action]:
                try:
                    handler(event)
                except Exception as e:
                    print(f"❌ Error in action handler for {action.value}: {e}")
    
    def _get_source_priority(self, source: str) -> int:
        """Gibt die Priorität einer Input-Quelle zurück (höher = wichtiger)"""
        try:
            return len(self.input_priority) - self.input_priority.index(source)
        except ValueError:
            return 0  # Unbekannte Quelle hat niedrigste Priorität
    
    def is_action_active(self, action: ActionType) -> bool:
        """Prüft ob eine Aktion aktuell aktiv ist"""
        return self.action_state.get(action, False)
    
    def set_magic_handler(self, handler):
        """Setzt den Magic System Handler"""
        self.magic_handler = handler
        print("🧙‍♂️ Magic Handler registriert")
    
    def handle_magic_action(self, action: ActionType, pressed: bool, source: str):
        """Spezielle Behandlung für Magic Actions"""
        if not pressed:  # Nur auf Press reagieren
            return
            
        if self.magic_handler:
            if action == ActionType.MAGIC_FIRE:
                self.magic_handler.add_element('fire')
            elif action == ActionType.MAGIC_WATER:
                self.magic_handler.add_element('water')
            elif action == ActionType.MAGIC_STONE:
                self.magic_handler.add_element('stone')
            elif action == ActionType.CAST_MAGIC:
                self.magic_handler.cast_current_spell()
            elif action == ActionType.CLEAR_MAGIC:
                self.magic_handler.clear_elements()
        
        # Normale Dispatch auch ausführen
        self.dispatch_action(action, pressed, source)
    
    def print_debug_info(self):
        """Gibt Debug-Informationen aus"""
        print("\n🎯 ACTION SYSTEM STATUS:")
        print("="*40)
        print(f"Aktive Aktionen: {len([a for a in self.action_state.values() if a])}")
        print(f"Registrierte Handler: {len(self.action_handlers)}")
        print(f"Input Priorität: {' > '.join(self.input_priority)}")
        
        current_time = time.time()
        for action, active in self.action_state.items():
            if active:
                source = self.last_input_source.get(action, "unknown")
                age = current_time - self.last_input_time.get(action, 0)
                print(f"  ⚡ {action.value}: {source} ({age:.1f}s alt)")
        print("="*40)

# Magic System Adapter für Action System
class MagicSystemAdapter:
    """Adapter zwischen Action System und Magic System"""
    
    def __init__(self, level_reference):
        """
        Args:
            level_reference: Referenz auf das Level-Objekt für Magic Access
        """
        self.level = level_reference
    
    def add_element(self, element_name: str):
        """Fügt ein Magic Element hinzu (abstrakte Schnittstelle)"""
        try:
            if self.level and self.level.main_game and hasattr(self.level.main_game, 'element_mixer'):
                success = self.level.main_game.element_mixer.handle_element_press(element_name)
                print(f"🔥 Element {element_name} hinzugefügt: {success}")
                return success
        except Exception as e:
            print(f"❌ Fehler beim Element hinzufügen: {e}")
        return False
    
    def cast_current_spell(self):
        """Wirkt den aktuellen Zauber (abstrakte Schnittstelle)"""
        try:
            if self.level:
                self.level.handle_cast_magic()
                print("✨ Zauber gewirkt")
                return True
        except Exception as e:
            print(f"❌ Fehler beim Zauber wirken: {e}")
        return False
    
    def clear_elements(self):
        """Löscht alle ausgewählten Elemente (abstrakte Schnittstelle)"""
        try:
            if self.level and self.level.main_game and hasattr(self.level.main_game, 'element_mixer'):
                self.level.main_game.element_mixer.reset_combination()
                print("🧹 Elemente gelöscht")
                return True
        except Exception as e:
            print(f"❌ Fehler beim Elemente löschen: {e}")
        return False

# Globale Action System Instanz
_global_action_system = None

def get_action_system() -> ActionSystem:
    """Gibt die globale Action System Instanz zurück"""
    global _global_action_system
    if _global_action_system is None:
        _global_action_system = ActionSystem()
    return _global_action_system

def init_action_system() -> ActionSystem:
    """Initialisiert das Action System"""
    global _global_action_system
    _global_action_system = ActionSystem()
    return _global_action_system
