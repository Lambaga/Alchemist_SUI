# -*- coding: utf-8 -*-
"""
Event-Management System für Spielereignisse
Ermöglicht lose gekoppelte Kommunikation zwischen Spielkomponenten
"""

from enum import Enum, auto
from typing import Callable, Dict, List, Any, Optional
import logging


class GameEvent(Enum):
    """
    Aufzählung aller verfügbaren Spielereignisse
    
    Diese Events ermöglichen es verschiedenen Spielkomponenten,
    auf wichtige Ereignisse zu reagieren, ohne direkt gekoppelt zu sein.
    """
    # Player Events
    PLAYER_DAMAGED = auto()
    PLAYER_HEALED = auto()
    PLAYER_DIED = auto()
    PLAYER_RESPAWNED = auto()
    PLAYER_LEVEL_UP = auto()
    PLAYER_MOVED = auto()
    
    # Enemy Events
    ENEMY_DEFEATED = auto()
    ENEMY_SPAWNED = auto()
    ENEMY_DAMAGED = auto()
    
    # Item Events
    ITEM_COLLECTED = auto()
    ITEM_DROPPED = auto()
    ITEM_USED = auto()
    
    # Potion Events
    POTION_BREWED = auto()
    POTION_CONSUMED = auto()
    
    # Game Events
    GAME_STARTED = auto()
    GAME_PAUSED = auto()
    GAME_RESUMED = auto()
    GAME_OVER = auto()
    
    # Level Events
    LEVEL_LOADED = auto()
    LEVEL_COMPLETED = auto()
    AREA_ENTERED = auto()
    AREA_EXITED = auto()
    
    # Combat Events
    FIREBALL_CAST = auto()
    SPELL_CAST = auto()
    COLLISION_DETECTED = auto()
    
    # UI Events
    MENU_OPENED = auto()
    MENU_CLOSED = auto()
    SETTING_CHANGED = auto()


class EventData:
    """
    Container für Event-Daten
    
    Ermöglicht typisierte Event-Parameter und bessere Dokumentation
    der erwarteten Datenstrukturen.
    """
    
    def __init__(self, **kwargs):
        """
        Initialisiert EventData mit beliebigen Parametern
        
        Args:
            **kwargs: Event-spezifische Daten
        """
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Holt einen Wert mit Fallback
        
        Args:
            key: Der Schlüssel
            default: Fallback-Wert
            
        Returns:
            Der Wert oder default
        """
        return getattr(self, key, default)
    
    def has(self, key: str) -> bool:
        """
        Prüft ob ein Schlüssel vorhanden ist
        
        Args:
            key: Der zu prüfende Schlüssel
            
        Returns:
            True wenn vorhanden
        """
        return hasattr(self, key)


class EventManager:
    """
    Zentraler Event-Manager für das Spiel
    
    Verwaltet Event-Listener und ermöglicht lose gekoppelte
    Kommunikation zwischen Spielkomponenten.
    """
    
    def __init__(self, enable_logging: bool = False):
        """
        Initialisiert den EventManager
        
        Args:
            enable_logging: Ob Event-Logging aktiviert werden soll
        """
        self._listeners: Dict[GameEvent, List[Callable]] = {}
        self._one_time_listeners: Dict[GameEvent, List[Callable]] = {}
        self._event_history: List[tuple] = []
        self._max_history = 100
        self._logging_enabled = enable_logging
        
        if enable_logging:
            logging.basicConfig(level=logging.INFO)
            self._logger = logging.getLogger(__name__)
        else:
            self._logger = None
    
    def subscribe(self, event: GameEvent, callback: Callable, one_time: bool = False) -> bool:
        """
        Registriert einen Event-Listener
        
        Args:
            event: Das Event, auf das gehört werden soll
            callback: Die Callback-Funktion
            one_time: Ob der Listener nur einmal ausgelöst werden soll
            
        Returns:
            True wenn erfolgreich registriert
        """
        try:
            if one_time:
                if event not in self._one_time_listeners:
                    self._one_time_listeners[event] = []
                if callback not in self._one_time_listeners[event]:
                    self._one_time_listeners[event].append(callback)
            else:
                if event not in self._listeners:
                    self._listeners[event] = []
                if callback not in self._listeners[event]:
                    self._listeners[event].append(callback)
            
            if self._logger:
                self._logger.info(f"Registered {'one-time ' if one_time else ''}listener for {event.name}")
            
            return True
            
        except Exception as e:
            if self._logger:
                self._logger.error(f"Failed to subscribe to {event}: {e}")
            return False
    
    def unsubscribe(self, event: GameEvent, callback: Callable) -> bool:
        """
        Entfernt einen Event-Listener
        
        Args:
            event: Das Event
            callback: Die zu entfernende Callback-Funktion
            
        Returns:
            True wenn erfolgreich entfernt
        """
        try:
            removed = False
            
            # Aus normalen Listenern entfernen
            if event in self._listeners:
                if callback in self._listeners[event]:
                    self._listeners[event].remove(callback)
                    removed = True
            
            # Aus One-Time Listenern entfernen
            if event in self._one_time_listeners:
                if callback in self._one_time_listeners[event]:
                    self._one_time_listeners[event].remove(callback)
                    removed = True
            
            if removed and self._logger:
                self._logger.info(f"Unsubscribed listener from {event.name}")
            
            return removed
            
        except Exception as e:
            if self._logger:
                self._logger.error(f"Failed to unsubscribe from {event}: {e}")
            return False
    
    def emit(self, event: GameEvent, data: Optional[EventData] = None, **kwargs) -> int:
        """
        Löst ein Event aus und ruft alle registrierten Listener auf
        
        Args:
            event: Das auszulösende Event
            data: Event-Daten als EventData Objekt
            **kwargs: Zusätzliche Event-Daten (werden zu EventData hinzugefügt)
            
        Returns:
            Anzahl der aufgerufenen Listener
        """
        # Event-Daten vorbereiten
        if data is None:
            data = EventData(**kwargs)
        else:
            # kwargs zu bestehenden Daten hinzufügen
            for key, value in kwargs.items():
                setattr(data, key, value)
        
        # Event zur Historie hinzufügen
        self._add_to_history(event, data)
        
        listeners_called = 0
        
        try:
            # Normale Listener aufrufen
            if event in self._listeners:
                for callback in self._listeners[event][:]:  # Kopie für sichere Iteration
                    try:
                        callback(event, data)
                        listeners_called += 1
                    except Exception as e:
                        if self._logger:
                            self._logger.error(f"Error in listener for {event.name}: {e}")
            
            # One-Time Listener aufrufen und entfernen
            if event in self._one_time_listeners:
                one_time_callbacks = self._one_time_listeners[event][:]
                self._one_time_listeners[event].clear()
                
                for callback in one_time_callbacks:
                    try:
                        callback(event, data)
                        listeners_called += 1
                    except Exception as e:
                        if self._logger:
                            self._logger.error(f"Error in one-time listener for {event.name}: {e}")
            
            if self._logger and listeners_called > 0:
                self._logger.info(f"Emitted {event.name} to {listeners_called} listeners")
                
        except Exception as e:
            if self._logger:
                self._logger.error(f"Error emitting event {event.name}: {e}")
        
        return listeners_called
    
    def _add_to_history(self, event: GameEvent, data: EventData) -> None:
        """
        Fügt ein Event zur Historie hinzu
        
        Args:
            event: Das Event
            data: Die Event-Daten
        """
        import time
        self._event_history.append((time.time(), event, data))
        
        # Historie begrenzen
        if len(self._event_history) > self._max_history:
            self._event_history = self._event_history[-self._max_history:]
    
    def get_listener_count(self, event: GameEvent) -> int:
        """
        Gibt die Anzahl der Listener für ein Event zurück
        
        Args:
            event: Das Event
            
        Returns:
            Anzahl der registrierten Listener
        """
        count = 0
        if event in self._listeners:
            count += len(self._listeners[event])
        if event in self._one_time_listeners:
            count += len(self._one_time_listeners[event])
        return count
    
    def clear_listeners(self, event: Optional[GameEvent] = None) -> None:
        """
        Entfernt alle Listener
        
        Args:
            event: Spezifisches Event oder None für alle Events
        """
        if event is None:
            self._listeners.clear()
            self._one_time_listeners.clear()
            if self._logger:
                self._logger.info("Cleared all event listeners")
        else:
            if event in self._listeners:
                del self._listeners[event]
            if event in self._one_time_listeners:
                del self._one_time_listeners[event]
            if self._logger:
                self._logger.info(f"Cleared listeners for {event.name}")
    
    def get_event_history(self, limit: Optional[int] = None) -> List[tuple]:
        """
        Gibt die Event-Historie zurück
        
        Args:
            limit: Maximale Anzahl zurückzugebender Events
            
        Returns:
            Liste von (timestamp, event, data) Tupeln
        """
        if limit is None:
            return self._event_history[:]
        return self._event_history[-limit:]
    
    def clear_history(self) -> None:
        """Leert die Event-Historie"""
        self._event_history.clear()
        if self._logger:
            self._logger.info("Cleared event history")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Gibt Statistiken über den EventManager zurück
        
        Returns:
            Dictionary mit Statistiken
        """
        total_listeners = sum(len(listeners) for listeners in self._listeners.values())
        total_one_time = sum(len(listeners) for listeners in self._one_time_listeners.values())
        
        return {
            'total_listeners': total_listeners,
            'one_time_listeners': total_one_time,
            'unique_events_with_listeners': len(self._listeners) + len(self._one_time_listeners),
            'event_history_size': len(self._event_history),
            'logging_enabled': self._logging_enabled
        }


# Globaler EventManager für einfache Nutzung
_global_event_manager: Optional[EventManager] = None


def get_event_manager() -> EventManager:
    """
    Gibt den globalen EventManager zurück (Singleton-Pattern)
    
    Returns:
        Der globale EventManager
    """
    global _global_event_manager
    if _global_event_manager is None:
        _global_event_manager = EventManager()
    return _global_event_manager


def emit_event(event: GameEvent, **kwargs) -> int:
    """
    Convenience-Funktion zum Auslösen von Events
    
    Args:
        event: Das auszulösende Event
        **kwargs: Event-Daten
        
    Returns:
        Anzahl der aufgerufenen Listener
    """
    return get_event_manager().emit(event, **kwargs)


def subscribe_to_event(event: GameEvent, callback: Callable, one_time: bool = False) -> bool:
    """
    Convenience-Funktion zum Registrieren von Event-Listenern
    
    Args:
        event: Das Event
        callback: Die Callback-Funktion
        one_time: Ob der Listener nur einmal ausgelöst werden soll
        
    Returns:
        True wenn erfolgreich registriert
    """
    return get_event_manager().subscribe(event, callback, one_time)


def unsubscribe_from_event(event: GameEvent, callback: Callable) -> bool:
    """
    Convenience-Funktion zum Entfernen von Event-Listenern
    
    Args:
        event: Das Event
        callback: Die zu entfernende Callback-Funktion
        
    Returns:
        True wenn erfolgreich entfernt
    """
    return get_event_manager().unsubscribe(event, callback)
