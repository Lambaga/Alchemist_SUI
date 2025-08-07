# -*- coding: utf-8 -*-
"""
Enemy Module - Enhanced Base Enemy System

Basis-Klasse für alle Gegnertypen mit erweiterten KI-Systemen,
Animations-Management und Gesundheitssystem.
"""

import pygame
import os
from typing import Dict, List, Tuple, Optional, Union, Any
from settings import *
from asset_manager import AssetManager
from combat_system import CombatEntity, DamageType

class Enemy(pygame.sprite.Sprite, CombatEntity):
    """
    Basis-Klasse für alle Gegnertypen mit erweiterten Systemen.
    
    Diese Klasse implementiert gemeinsame Funktionalität für alle Feinde:
    - Animations-System mit konfigurierbaren Geschwindigkeiten
    - KI-Verhalten mit Zustandsmaschine (idle, walking, attacking, death)
    - Gesundheitssystem mit Leben und Tod-Zuständen
    - Kollisionserkennung und Bewegungslogik
    - Asset-Management für effizientes Sprite-Laden
    - Spieler-Erkennungssystem mit konfigurierbarer Reichweite
    
    Attributes:
        speed (int): Bewegungsgeschwindigkeit in Pixeln pro Sekunde
        detection_range (int): Reichweite für Spieler-Erkennung in Pixeln  
        state (str): Aktueller KI-Zustand ('idle', 'walking', 'attacking', 'death')
        current_health (int): Aktuelle Lebenspunkte
        max_health (int): Maximale Lebenspunkte
        is_alive (bool): Ob der Gegner noch lebt
        facing_right (bool): Blickrichtung des Gegners
        target_player (Optional[Player]): Referenz zum verfolgten Spieler
        
    Example:
        >>> demon = Demon("assets/demon", 100, 100)
        >>> demon.update(dt=0.016, player=player_instance)
        >>> if demon.can_see_player(player_instance):
        ...     demon.attack_player()
    """
    
    def __init__(self, asset_path: str, pos_x: float, pos_y: float, scale_factor: float = 1.0) -> None:
        """
        Initialisiert den Basis-Gegner mit konfigurierbaren Eigenschaften.
        
        Args:
            asset_path: Pfad zum Sprite-Ordner mit Animationsframes
            pos_x: X-Position auf der Karte in Pixeln
            pos_y: Y-Position auf der Karte in Pixeln  
            scale_factor: Skalierungsfaktor für Sprite-Größe (1.0 = Originalgröße)
            
        Raises:
            FileNotFoundError: Wenn der Asset-Pfad nicht existiert
            ValueError: Wenn scale_factor <= 0
        """
        super().__init__()
        
        # Validierung der Eingabeparameter
        if scale_factor <= 0:
            raise ValueError("scale_factor muss größer als 0 sein")
        
        # AssetManager instance - verfügbar für alle Gegner-Subklassen
        self.asset_manager: AssetManager = AssetManager()
        
        # Animations-Konfiguration mit Type Hints
        self.animation_speed_ms: int = 300
        self.last_update_time: int = pygame.time.get_ticks()
        self.current_frame_index: int = 0
        
        # Gegner-Eigenschaften
        self.scale_factor: float = scale_factor
        self.facing_right: bool = True
        
        # KI und Bewegungs-Eigenschaften
        self.speed: int = 100  # Pixel pro Sekunde
        self.detection_range: int = 8 * 64  # 8 Kacheln * 64 Pixel = 512 Pixel (reduziert von 15)
        self.state: str = "idle"  # "idle", "walking", "attacking", "death"
        self.target_player: Optional[Any] = None  # Wird zur Laufzeit auf Player-Typ gesetzt
        self.direction: pygame.math.Vector2 = pygame.math.Vector2(0, 0)
        
        # Gesundheitssystem
        self.max_health: int = 100
        self.current_health: int = self.max_health
        self.alive_status: bool = True  # Renamed from is_alive to avoid conflict
        
        # Animations-Frames - werden von Subklassen befüllt
        self.idle_frames: List[pygame.Surface] = []
        self.walk_frames: List[pygame.Surface] = []
        self.attack_frames: List[pygame.Surface] = []
        self.death_frames: List[pygame.Surface] = []
        self.death_frames = []
        self.current_animation = "idle"  # Track current animation type
        
        # Combat properties
        self.attack_damage = 25
        self.attack_range = 3 * 64  # 3 tiles
        self.attack_cooldown = 2000  # 2 seconds in milliseconds
        self.last_attack_time = 0
        
        self.load_animations(asset_path)
        
        # Set initial image and position
        self.image = self.get_current_frames()[0] if self.get_current_frames() else self.create_placeholder()
        self.rect = self.image.get_rect(center=(pos_x, pos_y))
        
        # Collision box (smaller for closer combat)
        self.hitbox = self.rect.inflate(-60, -40)
        
    def load_animations(self, asset_path: str) -> None:
        """
        Lädt Animations-Frames - muss von Subklassen implementiert werden.
        
        Args:
            asset_path: Pfad zu den Asset-Dateien
            
        Note:
            Diese Methode sollte in Subklassen überschrieben werden,
            um spezifische Animationen zu laden.
        """
        pass
        
    def create_placeholder(self) -> pygame.Surface:
        """
        Erstellt einen Platzhalter-Sprite falls keine Sprites gefunden werden.
        
        Returns:
            pygame.Surface: Roter Kreis mit "ENEMY" Text als Platzhalter
        """
        placeholder = pygame.Surface((64, 64), pygame.SRCALPHA)
        pygame.draw.circle(placeholder, (255, 0, 0), (32, 32), 30, 3)
        font = pygame.font.Font(None, 24)
        text = font.render("ENEMY", True, (255, 255, 255))
        text_rect = text.get_rect(center=(32, 32))
        placeholder.blit(text, text_rect)
        return placeholder
        
    def get_current_frames(self) -> List[pygame.Surface]:
        """
        Gibt die aktuellen Animations-Frames basierend auf dem Zustand zurück.
        
        Returns:
            List[pygame.Surface]: Liste der Frames für den aktuellen Zustand
            
        Note:
            Priorität: death > attacking > walking > idle
        """
        if self.state == "death" and self.death_frames:
            return self.death_frames
        elif self.state == "attacking" and self.attack_frames:
            return self.attack_frames
        elif self.state in ["walking", "chasing"] and self.walk_frames:
            return self.walk_frames
        else:
            return self.idle_frames
    
    def update_animation(self, current_time):
        """Update animation frame based on current state"""
        current_frames = self.get_current_frames()
        if not current_frames:
            return
            
        # Check if enough time has passed to update frame
        if current_time - self.last_update_time >= self.animation_speed_ms:
            # Handle death animation (play once)
            if self.state == "death":
                if self.current_frame_index < len(current_frames) - 1:
                    self.current_frame_index += 1
                    self.last_update_time = current_time
            else:
                # Normal looping animations
                self.current_frame_index = (self.current_frame_index + 1) % len(current_frames)
                self.last_update_time = current_time
            
            # Update current animation type
            new_animation = self.state
            if new_animation != self.current_animation:
                self.current_animation = new_animation
                self.current_frame_index = 0  # Reset frame when switching animations
            
            # Update the image
            self.image = current_frames[self.current_frame_index]
            
            # Handle facing direction
            if not self.facing_right:
                self.image = pygame.transform.flip(self.image, True, False)
    
    def take_damage(self, damage: int, damage_type: DamageType = DamageType.PHYSICAL, 
                   source: Optional['CombatEntity'] = None) -> bool:
        """
        Fügt dem Gegner Schaden zu und behandelt den Tod.
        
        Args:
            damage: Schadensmenge die zugefügt werden soll
            damage_type: Art des Schadens
            source: Quelle des Schadens (Optional)
            
        Returns:
            bool: True wenn der Gegner noch lebt, False wenn gestorben
            
        Note:
            - Ignoriert Schaden wenn der Gegner bereits tot ist
            - Setzt Zustand auf "death" wenn Gesundheit <= 0
            - Reset Animation beim Übergang zum Tod-Zustand
            - Negative Schadenswerte = Heilung
        """
        if not self.alive_status:
            return False
        
        if damage < 0:
            # Negative Schadenswerte = Heilung
            self.current_health = min(self.max_health, self.current_health - damage)
        else:
            # Normaler Schaden
            self.current_health = max(0, self.current_health - damage)
            
        if self.current_health <= 0:
            self.alive_status = False
            self.state = "death"
            self.current_frame_index = 0
            
        return self.alive_status
    
    def can_attack(self) -> bool:
        """
        Prüft ob der Gegner angreifen kann basierend auf Cooldown und Lebensstatus.
        
        Returns:
            bool: True wenn Angriff möglich ist
        """
        current_time = pygame.time.get_ticks()
        return (self.alive_status and 
                current_time - self.last_attack_time >= self.attack_cooldown)
    
    def get_attack_damage(self) -> int:
        """
        Gibt den Angriffsschaden des Gegners zurück.
        
        Returns:
            int: Angriffsschaden
        """
        return self.attack_damage
    
    def get_health(self) -> int:
        """
        Gibt die aktuelle Gesundheit zurück.
        
        Returns:
            int: Aktuelle Lebenspunkte
        """
        return self.current_health
    
    def get_max_health(self) -> int:
        """
        Gibt die maximale Gesundheit zurück.
        
        Returns:
            int: Maximale Lebenspunkte
        """
        return self.max_health
    
    def is_alive(self) -> bool:
        """
        Prüft ob der Gegner noch lebt (CombatEntity Interface).
        
        Returns:
            bool: True wenn noch lebendig
        """
        return self.alive_status
    
    def get_position(self) -> tuple:
        """
        Gibt die Position des Gegners zurück.
        
        Returns:
            tuple: (x, y) Position
        """
        return (self.rect.centerx, self.rect.centery)
    
    def can_attack_old(self, current_time: int) -> bool:
        """
        Legacy-Methode: Prüft ob der Gegner angreifen kann basierend auf Cooldown.
        
        Args:
            current_time: Aktuelle Zeit in Millisekunden
            
        Returns:
            bool: True wenn Angriff möglich ist
        """
        return current_time - self.last_attack_time >= self.attack_cooldown
    
    def start_attack(self, current_time: int) -> bool:
        """
        Startet Angriffs-Animation und setzt Cooldown.
        
        Args:
            current_time: Aktuelle Zeit in Millisekunden
            
        Returns:
            bool: True wenn Angriff gestartet wurde
        """
        if self.can_attack_old(current_time) and self.alive_status:
            self.state = "attacking"
            self.last_attack_time = current_time
            self.current_frame_index = 0
            return True
        return False
    
    def update(self, dt: Optional[float] = None, player: Optional[Any] = None, 
              other_enemies: Optional[List['Enemy']] = None) -> None:
        """
        Aktualisiert Gegner-Animation und KI.
        
        Args:
            dt: Delta-Time in Sekunden für framerate-unabhängige Updates
            player: Referenz zum Spieler-Objekt für KI-Entscheidungen
            other_enemies: Liste anderer Gegner für Kollisionsvermeidung
            
        Note:
            Diese Methode sollte von Subklassen erweitert werden.
            Tote Gegner werden nur animiert, KI wird übersprungen.
        """
        if not self.alive_status:
            current_time = pygame.time.get_ticks()
            self.update_animation(current_time)
            return
            
        current_time = pygame.time.get_ticks()
        
        # Basic AI logic - to be extended by subclasses
        self.update_ai(dt, player, other_enemies)
        
        # Update animation
        self.update_animation(current_time)
    
    def update_ai(self, dt, player, other_enemies):
        """AI logic - to be implemented by subclasses"""
        pass
    
    def set_facing_direction(self, facing_right):
        """Change the direction the enemy is facing"""
        self.facing_right = facing_right
        
    def get_interaction_rect(self):
        """Get the area where player can interact with this enemy"""
        return self.hitbox.inflate(40, 40)
