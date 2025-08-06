# -*- coding: utf-8 -*-
"""
Combat System - Enhanced Combat Management

Verbessertes Kampfsystem mit Interface-Definition,
zentraler Schadensberechnung und Event-Integration.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from enum import Enum
import pygame

# Import the existing event system
from event_manager import EventManager, GameEvent, EventData


class DamageType(Enum):
    """Verschiedene Schadenstypen für erweiterte Kampfmechaniken"""
    PHYSICAL = "physical"
    MAGICAL = "magical"
    FIRE = "fire"
    WATER = "water"
    EARTH = "earth"


class CombatEntity(ABC):
    """
    Interface für kampffähige Entities (Player, Enemies, etc.)
    
    Definiert die minimalen Methoden die jede kampffähige Entity
    implementieren muss für das zentrale Kampfsystem.
    """
    
    @abstractmethod
    def take_damage(self, amount: int, damage_type: DamageType = DamageType.PHYSICAL, 
                   source: Optional['CombatEntity'] = None) -> bool:
        """
        Fügt der Entity Schaden zu
        
        Args:
            amount: Schadensmenge
            damage_type: Art des Schadens
            source: Quelle des Schadens (Optional)
            
        Returns:
            bool: True wenn die Entity noch lebt, False wenn gestorben
        """
        pass
    
    @abstractmethod
    def can_attack(self) -> bool:
        """
        Prüft ob die Entity angreifen kann
        
        Returns:
            bool: True wenn angreifen möglich
        """
        pass
    
    @abstractmethod
    def get_attack_damage(self) -> int:
        """
        Gibt den Angriffsschaden zurück
        
        Returns:
            int: Angriffsschaden
        """
        pass
    
    @abstractmethod
    def get_health(self) -> int:
        """
        Gibt die aktuelle Gesundheit zurück
        
        Returns:
            int: Aktuelle Lebenspunkte
        """
        pass
    
    @abstractmethod
    def get_max_health(self) -> int:
        """
        Gibt die maximale Gesundheit zurück
        
        Returns:
            int: Maximale Lebenspunkte
        """
        pass
    
    @abstractmethod
    def is_alive(self) -> bool:
        """
        Prüft ob die Entity noch lebt
        
        Returns:
            bool: True wenn noch lebendig
        """
        pass
    
    @abstractmethod
    def get_position(self) -> tuple:
        """
        Gibt die Position der Entity zurück
        
        Returns:
            tuple: (x, y) Position
        """
        pass


class CombatModifier:
    """
    Kampf-Modifikatoren für erweiterte Kampfmechaniken
    
    Ermöglicht temporäre Buffs/Debuffs, Rüstung, etc.
    """
    
    def __init__(self, name: str, damage_multiplier: float = 1.0, 
                 damage_reduction: float = 0.0, duration: int = 0):
        """
        Initialisiert einen Kampf-Modifikator
        
        Args:
            name: Name des Modifikators
            damage_multiplier: Schadens-Multiplikator (1.0 = normal)
            damage_reduction: Schadensreduktion (0.0-1.0)
            duration: Dauer in Millisekunden (0 = permanent)
        """
        self.name = name
        self.damage_multiplier = damage_multiplier
        self.damage_reduction = damage_reduction
        self.duration = duration
        self.start_time = pygame.time.get_ticks() if duration > 0 else 0
    
    def is_expired(self) -> bool:
        """
        Prüft ob der Modifikator abgelaufen ist
        
        Returns:
            bool: True wenn abgelaufen
        """
        if self.duration == 0:
            return False
        return pygame.time.get_ticks() - self.start_time >= self.duration
    
    def apply_damage_modifier(self, damage: int) -> int:
        """
        Wendet den Schadens-Modifikator an
        
        Args:
            damage: Ursprünglicher Schaden
            
        Returns:
            int: Modifizierter Schaden
        """
        modified_damage = damage * self.damage_multiplier
        modified_damage *= (1.0 - self.damage_reduction)
        return max(0, int(modified_damage))


class CombatSystem:
    """
    Zentrales Kampfsystem mit Schadensberechnung und Event-Integration
    
    Verwaltet alle Kampfinteraktionen zwischen Entities und
    integriert sich in das Event-System für lose Kopplung.
    """
    
    def __init__(self, event_manager: Optional[EventManager] = None):
        """
        Initialisiert das Kampfsystem
        
        Args:
            event_manager: Event-Manager für Event-Benachrichtigungen
        """
        self.event_manager = event_manager
        self.active_modifiers: Dict[CombatEntity, list] = {}
        self.damage_history: list = []
        
    def add_modifier(self, entity: CombatEntity, modifier: CombatModifier) -> None:
        """
        Fügt einem Entity einen Kampf-Modifikator hinzu
        
        Args:
            entity: Die betroffene Entity
            modifier: Der hinzuzufügende Modifikator
        """
        if entity not in self.active_modifiers:
            self.active_modifiers[entity] = []
        self.active_modifiers[entity].append(modifier)
    
    def remove_modifier(self, entity: CombatEntity, modifier_name: str) -> bool:
        """
        Entfernt einen Modifikator von einer Entity
        
        Args:
            entity: Die betroffene Entity
            modifier_name: Name des zu entfernenden Modifikators
            
        Returns:
            bool: True wenn erfolgreich entfernt
        """
        if entity not in self.active_modifiers:
            return False
        
        for i, modifier in enumerate(self.active_modifiers[entity]):
            if modifier.name == modifier_name:
                del self.active_modifiers[entity][i]
                return True
        return False
    
    def update_modifiers(self) -> None:
        """
        Aktualisiert alle aktiven Modifikatoren und entfernt abgelaufene
        """
        for entity in list(self.active_modifiers.keys()):
            modifiers = self.active_modifiers[entity]
            self.active_modifiers[entity] = [mod for mod in modifiers if not mod.is_expired()]
            
            # Entferne leere Listen
            if not self.active_modifiers[entity]:
                del self.active_modifiers[entity]
    
    def process_attack(self, attacker: CombatEntity, target: CombatEntity, 
                      damage_type: DamageType = DamageType.PHYSICAL) -> bool:
        """
        Verarbeitet einen Angriff zwischen zwei Entities
        
        Args:
            attacker: Die angreifende Entity
            target: Das Ziel des Angriffs
            damage_type: Art des Schadens
            
        Returns:
            bool: True wenn der Angriff erfolgreich war
        """
        if not attacker.can_attack() or not target.is_alive():
            return False
        
        # Berechne Basisschaden
        base_damage = attacker.get_attack_damage()
        final_damage = self.calculate_damage(attacker, target, base_damage, damage_type)
        
        # Führe Schaden aus
        target_survived = target.take_damage(final_damage, damage_type, attacker)
        
        # Speichere in Historie
        self.damage_history.append({
            'attacker': attacker,
            'target': target,
            'damage': final_damage,
            'damage_type': damage_type,
            'timestamp': pygame.time.get_ticks(),
            'target_survived': target_survived
        })
        
        # Events auslösen
        if self.event_manager:
            # Bestimme Event-Typ basierend auf Target-Typ
            if hasattr(target, '__class__') and 'Player' in target.__class__.__name__:
                event_type = GameEvent.PLAYER_DAMAGED
            else:
                event_type = GameEvent.ENEMY_DAMAGED
            
            self.event_manager.emit(
                event_type,
                EventData(
                    attacker=attacker,
                    target=target,
                    damage=final_damage,
                    damage_type=damage_type.value,
                    target_survived=target_survived
                )
            )
            
            # Tod-Event falls Entity gestorben
            if not target_survived:
                if hasattr(target, '__class__') and 'Player' in target.__class__.__name__:
                    death_event = GameEvent.PLAYER_DIED
                else:
                    death_event = GameEvent.ENEMY_DEFEATED
                
                self.event_manager.emit(
                    death_event,
                    EventData(
                        entity=target,
                        killer=attacker,
                        final_damage=final_damage
                    )
                )
        
        return True
    
    def calculate_damage(self, attacker: CombatEntity, target: CombatEntity, 
                        base_damage: int, damage_type: DamageType) -> int:
        """
        Berechnet den finalen Schaden mit allen Modifikatoren
        
        Args:
            attacker: Die angreifende Entity
            target: Das Ziel
            base_damage: Basis-Schaden
            damage_type: Art des Schadens
            
        Returns:
            int: Finaler Schaden nach allen Modifikationen
        """
        final_damage = base_damage
        
        # Angreifer-Modifikatoren (Schadens-Verstärkung)
        if attacker in self.active_modifiers:
            for modifier in self.active_modifiers[attacker]:
                final_damage = modifier.apply_damage_modifier(final_damage)
        
        # Ziel-Modifikatoren (Schadensreduktion)
        if target in self.active_modifiers:
            for modifier in self.active_modifiers[target]:
                final_damage = modifier.apply_damage_modifier(final_damage)
        
        # Elementare Resistenzen/Schwächen könnten hier hinzugefügt werden
        final_damage = self._apply_elemental_modifiers(target, final_damage, damage_type)
        
        return max(0, final_damage)
    
    def _apply_elemental_modifiers(self, target: CombatEntity, damage: int, 
                                  damage_type: DamageType) -> int:
        """
        Wendet elementare Modifikatoren an (Platzhalter für zukünftige Erweiterung)
        
        Args:
            target: Das Ziel
            damage: Aktueller Schaden
            damage_type: Art des Schadens
            
        Returns:
            int: Modifizierter Schaden
        """
        # Hier könnten später elementare Resistenzen implementiert werden
        # Zum Beispiel: Fire-Entities nehmen weniger Fire-Schaden
        return damage
    
    def heal_entity(self, target: CombatEntity, amount: int, 
                   source: Optional[CombatEntity] = None) -> int:
        """
        Heilt eine Entity (negative Schadenszufügung)
        
        Args:
            target: Die zu heilende Entity
            amount: Heilmenge
            source: Quelle der Heilung (Optional)
            
        Returns:
            int: Tatsächlich geheilte Menge
        """
        if not target.is_alive():
            return 0
        
        old_health = target.get_health()
        max_health = target.get_max_health()
        
        # Negative Schadenszufügung = Heilung
        target.take_damage(-amount, DamageType.MAGICAL, source)
        
        new_health = target.get_health()
        actual_healing = new_health - old_health
        
        # Event auslösen
        if self.event_manager and actual_healing > 0:
            self.event_manager.emit(
                GameEvent.PLAYER_HEALED,
                EventData(
                    target=target,
                    source=source,
                    amount=actual_healing
                )
            )
        
        return actual_healing
    
    def get_damage_history(self, limit: int = 10) -> list:
        """
        Gibt die letzten Schadens-Ereignisse zurück
        
        Args:
            limit: Maximale Anzahl zurückzugebender Einträge
            
        Returns:
            list: Liste der letzten Schadens-Ereignisse
        """
        return self.damage_history[-limit:] if self.damage_history else []
    
    def clear_damage_history(self) -> None:
        """Leert die Schadens-Historie"""
        self.damage_history.clear()
    
    def get_entity_modifiers(self, entity: CombatEntity) -> list:
        """
        Gibt alle aktiven Modifikatoren einer Entity zurück
        
        Args:
            entity: Die Entity
            
        Returns:
            list: Liste der aktiven Modifikatoren
        """
        return self.active_modifiers.get(entity, []).copy()


if __name__ == "__main__":
    # Test des Kampfsystems
    print("⚔️ COMBAT SYSTEM TEST")
    print("=" * 40)
    
    # Mock Entity für Tests
    class MockEntity(CombatEntity):
        def __init__(self, name: str, health: int, attack_damage: int):
            self.name = name
            self.current_health = health
            self.max_health = health
            self.attack_damage = attack_damage
            self.position = (0, 0)
        
        def take_damage(self, amount: int, damage_type: DamageType = DamageType.PHYSICAL, 
                       source: Optional[CombatEntity] = None) -> bool:
            if amount < 0:  # Heilung
                self.current_health = min(self.max_health, self.current_health - amount)
            else:  # Schaden
                self.current_health = max(0, self.current_health - amount)
            return self.current_health > 0
        
        def can_attack(self) -> bool:
            return self.current_health > 0
        
        def get_attack_damage(self) -> int:
            return self.attack_damage
        
        def get_health(self) -> int:
            return self.current_health
        
        def get_max_health(self) -> int:
            return self.max_health
        
        def is_alive(self) -> bool:
            return self.current_health > 0
        
        def get_position(self) -> tuple:
            return self.position
    
    # Test-Entities erstellen
    player = MockEntity("Player", 100, 25)
    enemy = MockEntity("Enemy", 80, 20)
    
    # Kampfsystem erstellen
    combat_system = CombatSystem()
    
    print(f"Player: {player.get_health()}/{player.get_max_health()} HP")
    print(f"Enemy: {enemy.get_health()}/{enemy.get_max_health()} HP")
    
    # Test 1: Normaler Angriff
    print("\n1. Player greift Enemy an:")
    success = combat_system.process_attack(player, enemy)
    print(f"   Angriff erfolgreich: {success}")
    print(f"   Enemy HP: {enemy.get_health()}/{enemy.get_max_health()}")
    
    # Test 2: Angriff mit Modifikator
    print("\n2. Enemy greift Player mit Schadens-Buff an:")
    damage_buff = CombatModifier("Schadens-Buff", damage_multiplier=1.5)
    combat_system.add_modifier(enemy, damage_buff)
    success = combat_system.process_attack(enemy, player)
    print(f"   Angriff erfolgreich: {success}")
    print(f"   Player HP: {player.get_health()}/{player.get_max_health()}")
    
    # Test 3: Heilung
    print("\n3. Player wird geheilt:")
    healed = combat_system.heal_entity(player, 30)
    print(f"   Geheilte HP: {healed}")
    print(f"   Player HP: {player.get_health()}/{player.get_max_health()}")
    
    print(f"\n📊 Schadens-Historie: {len(combat_system.get_damage_history())} Einträge")
