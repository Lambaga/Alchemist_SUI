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
from managers.asset_manager import AssetManager
from managers.font_manager import get_font_manager
from systems.combat_system import CombatEntity, DamageType

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
        # Baseline HP for difficulty scaling (filled when EnemyManager applies scaling)
        self.base_max_health: Optional[int] = None
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
        self.attack_duration_ms = 400  # attack animation hold before resuming

        # Cached directional frames (Performance: avoids per-frame pygame.transform.flip)
        self._frames_right: Dict[str, List[pygame.Surface]] = {}
        self._frames_left: Dict[str, List[pygame.Surface]] = {}

        # Death fade-out handling
        self._death_time = None
        self.fade_duration_ms = 3000
        
        self.load_animations(asset_path)

        # Build directional caches after animations are loaded
        self._rebuild_directional_frames()
        
        # Set initial image and position
        current_frames = self.get_current_frames_directional()
        self.image = current_frames[0] if current_frames else self.create_placeholder()
        self.rect = self.image.get_rect(center=(pos_x, pos_y))
        
        # Collision box (smaller for closer combat) — shrink a bit more to avoid snagging
        # Previously: inflate(-60, -40). Increase shrink slightly for smoother navigation.
        self.hitbox = self.rect.inflate(-70, -50)
        self.hitbox.center = self.rect.center
        
        # Obstacles for collision + vision checks (set by manager)
        self.obstacle_sprites = None
        
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
        # 🚀 RPi-Optimierung: FontManager für gecachte Fonts
        font = get_font_manager().get_font(24)
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

    def _rebuild_directional_frames(self) -> None:
        """Rebuild left/right frame caches from base frame lists."""
        def flip_frames(frames: List[pygame.Surface]) -> List[pygame.Surface]:
            # Flip once, reuse forever
            return [pygame.transform.flip(img, True, False) for img in frames]

        # Use current lists as the canonical "right" direction
        self._frames_right = {
            "idle": self.idle_frames or [],
            "walking": self.walk_frames or [],
            "chasing": self.walk_frames or [],
            "attacking": self.attack_frames or [],
            "death": self.death_frames or [],
        }
        self._frames_left = {
            key: flip_frames(frames) if frames else []
            for key, frames in self._frames_right.items()
        }

    def get_current_frames_directional(self) -> List[pygame.Surface]:
        """Return animation frames for current state and facing direction."""
        # Prefer caches; fall back to non-cached behavior if something is missing
        if self._frames_right:
            frames = (self._frames_right if self.facing_right else self._frames_left).get(self.state, [])
            if frames:
                return frames
        return self.get_current_frames()
    
    def update_animation(self, current_time):
        """Update animation frame based on current state"""
        frames = self.get_current_frames_directional()
        if not frames:
            return

        # If the state (animation type) changed, reset frame and update image immediately
        new_anim = self.state
        if new_anim != self.current_animation:
            self.current_animation = new_anim
            self.current_frame_index = 0
            self.last_update_time = current_time  # reset timer to avoid instant skip
            # Set image immediately on switch
            self.image = frames[self.current_frame_index]
            return

        # Regular timed frame advance
        if current_time - self.last_update_time >= self.animation_speed_ms:
            if self.state == "death":
                if self.current_frame_index < len(frames) - 1:
                    self.current_frame_index += 1
                    self.last_update_time = current_time
            else:
                self.current_frame_index = (self.current_frame_index + 1) % len(frames)
                self.last_update_time = current_time

            img = frames[self.current_frame_index]
            self.image = img
    
    def take_damage(self, amount: int, damage_type: DamageType = DamageType.PHYSICAL, 
                   source: Optional['CombatEntity'] = None) -> bool:
        """
        Fügt dem Gegner Schaden zu und behandelt den Tod.
        
        Args:
            amount: Schadensmenge die zugefügt werden soll
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
        
        if amount < 0:
            # Negative Schadenswerte = Heilung
            self.current_health = min(self.max_health, self.current_health - amount)
        else:
            # Normaler Schaden
            self.current_health = max(0, self.current_health - amount)
            
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
            # Initialize death timestamp once
            if self._death_time is None:
                self._death_time = current_time

            # Continue any death animation
            self.update_animation(current_time)

            # Compute fade-out alpha and assign to image
            elapsed = current_time - self._death_time
            if elapsed >= self.fade_duration_ms:
                # Remove from all groups after fade completes
                try:
                    self.kill()
                except Exception:
                    pass
                return
            else:
                try:
                    alpha = max(0, min(255, int(255 * (1.0 - (elapsed / self.fade_duration_ms)))))
                    if self.image:
                        # Create a faded copy to avoid mutating shared surfaces
                        base = self.get_current_frames_directional()
                        frame = base[self.current_frame_index] if base else self.image
                        faded = frame.copy()
                        faded.set_alpha(alpha)
                        self.image = faded
                except Exception:
                    pass
            return
            
        current_time = pygame.time.get_ticks()
        
        # Recover from short attack state into movement state after duration
        if self.state == "attacking":
            if current_time - self.last_attack_time >= self.attack_duration_ms:
                # Resume chasing if we still have a target; otherwise idle
                self.state = "chasing" if self.target_player is not None else "idle"

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

    # --- Obstacle/vision helpers shared by enemies ---
    def set_obstacle_sprites(self, obstacle_sprites):
        """Assign obstacle sprites/group used for collisions and line-of-sight"""
        self.obstacle_sprites = obstacle_sprites

    def _iter_obstacle_rects(self):
        """Yield pygame.Rect for each obstacle sprite or rect"""
        if not self.obstacle_sprites:
            return
        try:
            iterable = self.obstacle_sprites.sprites() if hasattr(self.obstacle_sprites, 'sprites') else self.obstacle_sprites
            for o in iterable:
                if hasattr(o, 'hitbox') and isinstance(o.hitbox, pygame.Rect):
                    yield o.hitbox
                elif hasattr(o, 'rect') and isinstance(o.rect, pygame.Rect):
                    yield o.rect
                elif isinstance(o, pygame.Rect):
                    yield o
        except Exception:
            # Fallback: treat as generic iterable
            for o in self.obstacle_sprites:
                if hasattr(o, 'hitbox') and isinstance(o.hitbox, pygame.Rect):
                    yield o.hitbox
                elif hasattr(o, 'rect') and isinstance(o.rect, pygame.Rect):
                    yield o.rect
                elif isinstance(o, pygame.Rect):
                    yield o

    def check_collision_with_obstacles(self, rect: Optional[pygame.Rect] = None) -> bool:
        """Return True if given rect (or self.hitbox) collides with any obstacle"""
        if not self.obstacle_sprites:
            return False
        r = rect if rect is not None else self.hitbox
        for orect in self._iter_obstacle_rects():
            if r.colliderect(orect):
                return True
        return False

    def can_see_player(self, player, step: int = 16) -> bool:
        """Check line-of-sight to player using simple ray sampling through obstacles.
        Returns True if no obstacle blocks the line from enemy center to player center.
        """
        if player is None:
            return False
        if not self.obstacle_sprites:
            # No obstacles registered -> assume visible
            return True

        sx, sy = self.hitbox.center
        if hasattr(player, 'hitbox') and isinstance(player.hitbox, pygame.Rect):
            tx, ty = player.hitbox.center
        else:
            tx, ty = player.rect.center

        dx = tx - sx
        dy = ty - sy
        dist = max(1, int(pygame.math.Vector2(dx, dy).length()))
        steps = max(1, dist // step)

        # Sample along the line; use a tiny rect to test collisions
        for i in range(1, steps + 1):
            px = sx + (dx * i) / steps
            py = sy + (dy * i) / steps
            probe = pygame.Rect(int(px) - 1, int(py) - 1, 2, 2)
            for orect in self._iter_obstacle_rects():
                if probe.colliderect(orect):
                    return False
        return True
