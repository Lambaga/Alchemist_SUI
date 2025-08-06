# -*- coding: utf-8 -*-
"""
Player Module - Enhanced with Type Hints and Documentation

Enthält die Player-Klasse für den Spieler-Charakter (den Alchemisten) 
mit erweiterten Animationen, optimierter Bewegung und Kollisionssystem.
"""

import pygame
import os
from typing import Dict, List, Tuple, Optional, Union, Any
from settings import *
from asset_manager import AssetManager
from collision_optimizer import OptimizedCollisionSystem
from combat_system import CombatEntity, DamageType

class Player(pygame.sprite.Sprite, CombatEntity):
    """
    Erweiterte Spieler-Klasse mit optimierter Animation und Bewegung.
    
    Diese Klasse implementiert den Hauptcharakter des Spiels mit:
    - Delta-Time basierter Bewegung für framerate-unabhängige Performance
    - Optimiertes Animations-System mit konfigurierbaren Geschwindigkeiten
    - Präzise Kollisionserkennung mit anpassbarer Hitbox
    - Asset-Management für effizientes Laden von Sprite-Animationen
    - Vector2-basierte Positionierung für subpixel-genaue Bewegung
    
    Attributes:
        position (pygame.math.Vector2): Exakte Spieler-Position (Float-Koordinaten)
        animation_frames (Dict[str, List[pygame.Surface]]): Animationsframes nach Zustand
        animation_speed_ms (Dict[str, int]): Animationsgeschwindigkeiten in Millisekunden
        speed (int): Bewegungsgeschwindigkeit in Pixeln pro Sekunde
        direction (pygame.math.Vector2): Bewegungsrichtung (-1 bis 1 für X/Y)
        facing_right (bool): Blickrichtung des Spielers
        status (str): Aktueller Animationszustand ('idle', 'run')
        hitbox (pygame.Rect): Kollisions-Rechteck für präzise Kollisionserkennung
        
    Example:
        >>> player = Player("assets/Wizard Pack", 400, 300)
        >>> player.move(dt=0.016)  # 60 FPS Delta-Time
        >>> player.update_animation()
    """
    
    def __init__(self, asset_path: str, pos_x: float, pos_y: float) -> None:
        """
        Initialisiert den Spieler mit erweiterten Konfigurationen.
        
        Args:
            asset_path: Pfad zum Spritesheet (Datei) oder Animations-Ordner
            pos_x: Start-X-Position des Spielers in Pixeln
            pos_y: Start-Y-Position des Spielers in Pixeln
            
        Raises:
            FileNotFoundError: Wenn der Asset-Pfad nicht existiert
            ValueError: Wenn die Position außerhalb gültiger Grenzen liegt
        """
        super().__init__()
        
        # AssetManager instance
        self.asset_manager: AssetManager = AssetManager()
        
        # Animations-Konfiguration mit Type Hints
        self.animation_speed_ms: Dict[str, int] = {"idle": 200, "run": 120}
        self.last_update_time: int = pygame.time.get_ticks()
        self.current_frame_index: int = 0
        
        # Bewegungs-Konfiguration (Delta Time Support)
        self.speed: int = PLAYER_SPEED
        self.direction: pygame.math.Vector2 = pygame.math.Vector2(0, 0)
        self.facing_right: bool = True
        self.status: str = "idle"
        
        # Animations-Zustände mit Type Hints
        self.animation_frames: Dict[str, List[pygame.Surface]] = {"idle": [], "run": []}
        
        self.load_animations(asset_path)
        
        # Initiales Bild und Position setzen
        self.image: pygame.Surface = (self.animation_frames["idle"][0] 
                                    if self.animation_frames["idle"] 
                                    else self.create_placeholder())
        self.rect: pygame.Rect = self.image.get_rect(center=(pos_x, pos_y))
        # Perfekt angepasste Hitbox - genau um den Charakter herum
        self.hitbox: pygame.Rect = self.rect.inflate(-50, -70)
        self.position: pygame.math.Vector2 = pygame.math.Vector2(self.rect.center)
        
        # Für Kollisionserkennung
        self.obstacle_sprites: pygame.sprite.Group = pygame.sprite.Group()
        
        # Optimiertes Kollisionssystem
        self.collision_system: OptimizedCollisionSystem = OptimizedCollisionSystem(cell_size=128)
        self.collision_optimization_enabled: bool = False
        
        # Combat System Attributes
        self.max_health: int = 100
        self.current_health: int = self.max_health
        self.attack_damage: int = 30
        self.is_player_alive: bool = True
        self.last_attack_time: int = 0
        self.attack_cooldown: int = 1000  # 1 second attack cooldown
    
    def update_hitbox(self) -> None:
        """
        Aktualisiert die Hitbox basierend auf der aktuellen rect-Position.
        
        Die Hitbox wird zentriert auf die aktuelle Position gesetzt und
        die Vector2-Position für präzise Bewegungsberechnungen aktualisiert.
        """
        self.hitbox = self.rect.inflate(-70, -70)
        self.position = pygame.math.Vector2(self.rect.center)

    def create_placeholder(self) -> pygame.Surface:
        """
        Erstellt einen Platzhalter-Sprite bei Asset-Ladeproblemen.
        
        Returns:
            pygame.Surface: Grüner Platzhalter-Sprite in Spielergröße
        """
        placeholder = pygame.Surface(PLAYER_SIZE, pygame.SRCALPHA)
        placeholder.fill((0, 255, 0))
        return placeholder

    def load_animations(self, path: str) -> None:
        """
        Lädt Animationen über AssetManager für bessere Performance und Caching.
        
        Versucht zuerst die konfigurierte Methode über AssetManager,
        fällt bei Fehlern auf Legacy-Methoden zurück.
        
        Args:
            path: Pfad zu den Asset-Dateien oder Ordner
            
        Raises:
            Exception: Wenn sowohl konfigurierte als auch Legacy-Methoden fehlschlagen
        """
        # Versuche zuerst die konfigurierte Methode
        try:
            self.animation_frames["idle"] = self.asset_manager.load_entity_animation(
                'player', 'idle', path
            )
            self.animation_frames["run"] = self.asset_manager.load_entity_animation(
                'player', 'run', path
            )
            
            # Prüfe ob Animationen erfolgreich geladen wurden
            if self.animation_frames["idle"] and self.animation_frames["run"]:
                return
        except Exception as e:
            print(f"⚠️ Konfigurierte Animation-Ladung fehlgeschlagen: {e}")
        
        # Fallback: Legacy-Methode
        # Fall 1: Der Pfad ist ein Ordner (z.B. "assets/Wizard Pack")
        if os.path.isdir(path):
            # Annahme: Idle.png hat 6 Frames, Run.png hat 8 Frames
            idle_path = os.path.join(path, "Idle.png")
            run_path = os.path.join(path, "Run.png")
            
            self.animation_frames["idle"] = self.asset_manager.load_spritesheet_frames(
                idle_path, 6, scale_to=PLAYER_SIZE
            )
            self.animation_frames["run"] = self.asset_manager.load_spritesheet_frames(
                run_path, 8, scale_to=PLAYER_SIZE
            )
        # Fall 2: Der Pfad ist eine einzelne Datei
        elif os.path.isfile(path):
            # Wir nehmen an, die einzelne Datei ist eine Idle-Animation mit 60 Frames
            frames = self.asset_manager.load_spritesheet_frames(path, 60, scale_to=PLAYER_SIZE)
            self.animation_frames["idle"] = frames
            self.animation_frames["run"] = frames # Verwenden die gleiche Animation für "run"
        else:
            # Erstelle einen Fallback-Platzhalter, damit das Spiel nicht abstürzt
            placeholder = self.create_placeholder()
            self.animation_frames["idle"] = [placeholder]
            self.animation_frames["run"] = [placeholder]

    def load_frames_from_spritesheet(self, spritesheet_path, num_frames):
        """
        Legacy-Methode - wird jetzt über AssetManager abgewickelt.
        Lädt eine Spritesheet-Datei und schneidet sie in einzelne Animations-Frames.
        :param spritesheet_path: Der genaue Pfad zur Bilddatei.
        :param num_frames: Die exakte Anzahl der Frames in dieser Datei.
        """
        return self.asset_manager.load_spritesheet_frames(
            spritesheet_path, num_frames, scale_to=PLAYER_SIZE
        )
            
        return frames

    def get_status(self):
        """
        Robuste Status-Bestimmung für Animationen.
        Bestimmt den Status in jedem Frame neu, um 'steckenbleibende' Animationen zu vermeiden.
        """
        # idle status
        if self.direction.x == 0 and self.direction.y == 0:
            # Wenn der Status nicht schon 'idle' ist, setze ihn und starte die Animation neu
            if 'idle' not in self.status:
                self.status = 'idle'
                self.current_frame_index = 0
        else:
            # Bewegung erkannt
            if 'run' not in self.status:
                self.status = 'run'
                self.current_frame_index = 0
        
        # TODO: Erweitert für Kampf-Status
        # if self.attacking:
        #     self.direction.x = 0
        #     self.direction.y = 0
        #     if 'attack' not in self.status:
        #         self.status = 'attack'
        #         self.current_frame_index = 0

    def update(self, dt: Optional[float] = None) -> None:
        """
        Aktualisiert den Zustand und die Animation des Spielers.
        
        Führt alle notwendigen Updates in der korrekten Reihenfolge durch:
        1. Status-Bestimmung basierend auf Bewegung
        2. Animation-Fortschritt
        3. Sprite-Aktualisierung mit Orientierung
        
        Args:
            dt: Delta Time in Sekunden für framerate-unabhängige Animation.
                Bei None wird Fallback zu 60 FPS verwendet.
                
        Note:
            Diese Methode sollte einmal pro Frame aufgerufen werden.
        """
        if dt is None:
            dt = 1.0 / 60.0  # Fallback für 60 FPS
        
        # 1. Status basierend auf aktueller Bewegungsrichtung bestimmen
        self.get_status()

        # 2. Animation fortschreiten lassen (Delta Time basiert)
        now = pygame.time.get_ticks()
        if now - self.last_update_time > self.animation_speed_ms[self.status]:
            self.last_update_time = now
            
            frames_for_current_status = self.animation_frames[self.status]
            if frames_for_current_status:  # Sicherheitsprüfung
                self.current_frame_index = (self.current_frame_index + 1) % len(frames_for_current_status)
                
                # Das Bild des Sprites aktualisieren
                new_image = frames_for_current_status[self.current_frame_index]
                
                # Bild spiegeln, falls der Spieler nach links schaut
                if not self.facing_right:
                    new_image = pygame.transform.flip(new_image, True, False)
                
                # Position beibehalten, während das Bild aktualisiert wird
                old_center = self.rect.center
                self.image = new_image
                self.rect = self.image.get_rect(center=old_center)

    def move(self, dt: float = 1.0/60.0) -> None:
        """
        Bewegt den Spieler basierend auf Delta-Time für framerate-unabhängige Bewegung.
        
        Verwendet Vector2-Mathematik für präzise Positionsberechnung und
        normalisiert die Bewegungsrichtung für konsistente diagonale Bewegung.
        
        Args:
            dt: Delta-Time in Sekunden für framerate-unabhängige Bewegung.
                Standard: 1/60 (entspricht 60 FPS)
                
        Note:
            - Aktualisiert sowohl die Float-Position als auch die Integer-Hitbox
            - Normalisiert Richtungsvektoren um diagonale Geschwindigkeitsunterschiede zu vermeiden
            - Berücksichtigt Blickrichtung für Sprite-Orientierung
        """
        if self.direction.magnitude() > 0:
            # Normalisiere die Richtung, um diagonale Bewegung zu korrigieren
            normalized_direction = self.direction.normalize()
            
            # Aktualisiere Blickrichtung
            if normalized_direction.x > 0:
                self.facing_right = True
            elif normalized_direction.x < 0:
                self.facing_right = False
            
            # Berechne die Bewegung mit Float-Präzision
            speed_multiplier = self.speed * dt * 60  # * 60 für 60fps Referenz
            
            # Berechnungen mit der Float-Position durchführen
            self.position.x += normalized_direction.x * speed_multiplier
            self.position.y += normalized_direction.y * speed_multiplier
            
            # Die Integer-Hitbox von der Float-Position aktualisieren
            self.hitbox.centerx = round(self.position.x)
            self.collision('horizontal')  # Kollision mit der gerundeten Position prüfen
            self.hitbox.centery = round(self.position.y)
            self.collision('vertical')  # Kollision mit der gerundeten Position prüfen
            
            # Das finale rect von der (möglicherweise korrigierten) Hitbox aktualisieren
            self.rect.center = self.hitbox.center

    def collision(self, direction):
        """
        Kollisionserkennung mit Hindernissen (optimiert mit räumlicher Hashtabelle).
        Nach einer Kollision wird auch die Float-Position synchronisiert.
        """
        # Verwende optimiertes System falls verfügbar
        if self.collision_optimization_enabled:
            return self.collision_optimized(direction)
        else:
            return self.collision_traditional(direction)
    
    def collision_optimized(self, direction):
        """
        Optimierte Kollisionserkennung mit räumlicher Hashtabelle
        """
        # Aktualisiere Position im räumlichen Hash
        self.collision_system.update_dynamic_object(self)
        
        if direction == 'horizontal':
            collisions = self.collision_system.check_horizontal_collision(self, self.direction.x)
            
            for collision_obj in collisions:
                collision_rect = self.collision_system._get_rect_from_object(collision_obj)
                if collision_rect and collision_rect.colliderect(self.hitbox):
                    if self.direction.x > 0:  # Bewegung nach rechts
                        self.hitbox.right = collision_rect.left
                    elif self.direction.x < 0:  # Bewegung nach links
                        self.hitbox.left = collision_rect.right
                    
                    self.position.x = self.hitbox.centerx  # Float-Position synchronisieren
                    break  # Erste Kollision reicht
                        
        elif direction == 'vertical':
            collisions = self.collision_system.check_vertical_collision(self, self.direction.y)
            
            for collision_obj in collisions:
                collision_rect = self.collision_system._get_rect_from_object(collision_obj)
                if collision_rect and collision_rect.colliderect(self.hitbox):
                    if self.direction.y > 0:  # Bewegung nach unten
                        self.hitbox.bottom = collision_rect.top
                    elif self.direction.y < 0:  # Bewegung nach oben
                        self.hitbox.top = collision_rect.bottom
                    
                    self.position.y = self.hitbox.centery  # Float-Position synchronisieren
                    break  # Erste Kollision reicht
    
    def collision_traditional(self, direction):
        """
        Traditionelle Kollisionserkennung (Fallback)
        """
        if direction == 'horizontal':
            for sprite in self.obstacle_sprites:
                if sprite.hitbox.colliderect(self.hitbox):
                    if self.direction.x > 0:  # Bewegung nach rechts
                        self.hitbox.right = sprite.hitbox.left
                    if self.direction.x < 0:  # Bewegung nach links
                        self.hitbox.left = sprite.hitbox.right
                    self.position.x = self.hitbox.centerx  # Float-Position synchronisieren

        if direction == 'vertical':
            for sprite in self.obstacle_sprites:
                if sprite.hitbox.colliderect(self.hitbox):
                    if self.direction.y > 0:  # Bewegung nach unten
                        self.hitbox.bottom = sprite.hitbox.top
                    if self.direction.y < 0:  # Bewegung nach oben
                        self.hitbox.top = sprite.hitbox.bottom
                    self.position.y = self.hitbox.centery  # Float-Position synchronisieren

    def set_obstacle_sprites(self, obstacle_sprites):
        """Setzt die Sprite-Gruppe für Kollisionserkennung"""
        self.obstacle_sprites = obstacle_sprites
        
        # Initialisiere optimiertes Kollisionssystem
        try:
            # Konvertiere zu Liste falls nötig
            if hasattr(obstacle_sprites, 'sprites'):
                obstacles = obstacle_sprites.sprites()
            else:
                obstacles = list(obstacle_sprites)
            
            # Initialisiere das räumliche Hash-System
            self.collision_system.initialize_static_objects(obstacles)
            
            # Füge sich selbst als dynamisches Objekt hinzu
            self.collision_system.add_dynamic_object(self)
            
            self.collision_optimization_enabled = True
            print(f"✅ Optimierte Kollisionserkennung aktiviert mit {len(obstacles)} Objekten")
            
        except Exception as e:
            print(f"⚠️ Fallback zu traditioneller Kollisionserkennung: {e}")
            self.collision_optimization_enabled = False

    def set_direction(self, direction_vector):
        """Setzt die Bewegungsrichtung als Vector2 (modern approach)"""
        self.direction = direction_vector
        
    def get_collision_performance_stats(self):
        """
        Gibt Performance-Statistiken der Kollisionserkennung zurück
        """
        if self.collision_optimization_enabled:
            return self.collision_system.get_performance_stats()
        else:
            return {
                'optimization_enabled': False,
                'system': 'traditional O(n) collision detection'
            }

    def get_movement_left(self):
        """Legacy Kompatibilität - gibt die Bewegung nach links zurück"""
        self.direction.x = -1
        return (-self.speed, 0)
        
    def get_movement_right(self):
        """Legacy Kompatibilität - gibt die Bewegung nach rechts zurück"""
        self.direction.x = 1
        return (self.speed, 0)

    def get_movement_up(self):
        """Legacy Kompatibilität - gibt die Bewegung nach oben zurück"""
        self.direction.y = -1
        return (0, -self.speed)
        
    def get_movement_down(self):
        """Legacy Kompatibilität - gibt die Bewegung nach unten zurück"""
        self.direction.y = 1
        return (0, self.speed)
        
    # Legacy Kompatibilität: Behalte die alten Methoden bei
    def move_left(self):
        """Legacy: Bewegt den Spieler nach links"""
        self.direction.x = -1
        
    def move_right(self):
        """Legacy: Bewegt den Spieler nach rechts"""
        self.direction.x = 1

    def move_up(self):
        """Legacy: Bewegt den Spieler nach oben"""
        self.direction.y = -1
        
    def move_down(self):
        """Legacy: Bewegt den Spieler nach unten"""
        self.direction.y = 1

    def stop_moving(self):
        """Stoppt die Bewegung des Spielers"""
        self.direction = pygame.math.Vector2(0, 0)

    def update_position_properties(self):
        """Aktualisiert Position-Properties für Kompatibilität"""
        self.x = self.rect.centerx
        self.y = self.rect.centery
        self.width = self.rect.width
        self.height = self.rect.height

    def get_rect(self):
        """Gibt das Rechteck des Spielers zurück für Kollisionserkennung"""
        return (self.rect.x, self.rect.y, self.rect.width, self.rect.height)

    # CombatEntity Interface Implementation
    def take_damage(self, amount: int, damage_type: DamageType = DamageType.PHYSICAL, 
                   source: Optional['CombatEntity'] = None) -> bool:
        """
        Fügt dem Spieler Schaden zu oder heilt ihn.
        
        Args:
            amount: Schadensmenge (positiv) oder Heilmenge (negativ)
            damage_type: Art des Schadens
            source: Quelle des Schadens (Optional)
            
        Returns:
            bool: True wenn der Spieler noch lebt, False wenn gestorben
        """
        if not self.is_player_alive:
            return False
        
        if amount < 0:
            # Negative Schadenswerte = Heilung
            self.current_health = min(self.max_health, self.current_health - amount)
        else:
            # Normaler Schaden
            self.current_health = max(0, self.current_health - amount)
            
        if self.current_health <= 0:
            self.is_player_alive = False
            # Hier könnte später Tod-Animation gesetzt werden
            
        return self.is_player_alive
    
    def can_attack(self) -> bool:
        """
        Prüft ob der Spieler angreifen kann basierend auf Cooldown und Lebensstatus.
        
        Returns:
            bool: True wenn Angriff möglich ist
        """
        current_time = pygame.time.get_ticks()
        return (self.is_player_alive and 
                current_time - self.last_attack_time >= self.attack_cooldown)
    
    def get_attack_damage(self) -> int:
        """
        Gibt den Angriffsschaden des Spielers zurück.
        
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
        Prüft ob der Spieler noch lebt (CombatEntity Interface).
        
        Returns:
            bool: True wenn noch lebendig
        """
        return self.is_player_alive
    
    def get_position(self) -> tuple:
        """
        Gibt die Position des Spielers zurück.
        
        Returns:
            tuple: (x, y) Position
        """
        return (self.rect.centerx, self.rect.centery)
    
    def attack(self) -> bool:
        """
        Führt einen Spieler-Angriff aus.
        
        Returns:
            bool: True wenn Angriff erfolgreich ausgeführt
        """
        if not self.can_attack():
            return False
            
        self.last_attack_time = pygame.time.get_ticks()
        # Hier könnte später Angriffs-Animation gesetzt werden
        return True
    
    def take_damage(self, damage: int, damage_type=None) -> bool:
        """
        Fügt dem Spieler Schaden zu.
        
        Args:
            damage: Schadensmenge
            damage_type: Art des Schadens (optional, für zukünftige Erweiterungen)
            
        Returns:
            bool: True wenn der Spieler noch lebt, False wenn er gestorben ist
        """
        if not self.is_player_alive:
            return False
            
        self.current_health -= damage
        if self.current_health <= 0:
            self.current_health = 0
            self.is_player_alive = False
            return False
        return True
    
    def is_dead(self) -> bool:
        """
        Prüft, ob der Spieler tot ist.
        
        Returns:
            bool: True wenn der Spieler tot ist (HP <= 0)
        """
        return self.current_health <= 0 or not self.is_player_alive
    
    def heal(self, heal_amount: int) -> None:
        """
        Heilt den Spieler.
        
        Args:
            heal_amount: Menge der Heilung
        """
        if self.is_player_alive:
            self.current_health = min(self.max_health, self.current_health + heal_amount)
    
    def revive(self) -> None:
        """
        Wiederbelebt den Spieler mit voller Gesundheit.
        """
        self.current_health = self.max_health
        self.is_player_alive = True
    
    def get_health_percentage(self) -> float:
        """
        Gibt den Gesundheitsprozentsatz zurück.
        
        Returns:
            float: Gesundheit als Prozentsatz (0.0 bis 1.0)
        """
        return self.current_health / self.max_health if self.max_health > 0 else 0.0
