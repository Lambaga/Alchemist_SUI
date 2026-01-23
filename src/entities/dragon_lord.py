# -*- coding: utf-8 -*-
"""
Dragon Lord - Boss Character
Ein mächtiger Drachen-Boss der erst angreift wenn er angegriffen wird.
"""

import pygame
import os
import math
from typing import Optional, List, Tuple


class DragonLord(pygame.sprite.Sprite):
    """Dragon Lord Boss mit verschiedenen Animationen."""
    
    # Basis-Stats
    MAX_HEALTH = 20
    ATTACK_DAMAGE = 35
    ATTACK_RANGE = 100  # Pixel
    ATTACK_COOLDOWN = 1.5  # Sekunden
    AGGRO_RANGE = 150  # Pixel - Reichweite für Verfolgung nach Aggro
    MOVE_SPEED = 60  # Pixel pro Sekunde
    
    def __init__(self, x: int, y: int):
        pygame.sprite.Sprite.__init__(self)
        
        self.x = x
        self.y = y
        self.spawn_x = x
        self.spawn_y = y
        
        # Health
        self.max_health = self.MAX_HEALTH
        self.current_health = self.MAX_HEALTH
        
        # Combat State
        self.is_aggro = False  # Wird erst True wenn angegriffen
        self.target = None  # Spieler-Referenz
        self.attack_timer = 0.0
        self.facing_left = False
        
        # Animation State
        self.state = "idle"  # idle, walk, attack, hurt, death
        self.animations = {}
        self.current_frame = 0
        self.animation_timer = 0.0
        self.animation_speed = 0.15
        
        # Hurt Animation
        self.hurt_timer = 0.0
        self.hurt_duration = 0.3
        
        # Death
        self.is_dead = False
        self.death_animation_complete = False
        
        # Intro Dialog
        self.intro_shown = False  # Ob der Intro-Dialog bereits gezeigt wurde
        self.visible = True  # Ob der Dragon Lord sichtbar ist
        
        # Lade Animationen
        self._load_animations()
        
        # Initiales Bild und Rect
        if "idle" in self.animations and self.animations["idle"]:
            self.image = self.animations["idle"][0]
        else:
            # Fallback: Einfaches Rechteck
            self.image = pygame.Surface((74, 74), pygame.SRCALPHA)
            self.image.fill((150, 50, 50))
        
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        
        print(f"🐉 Dragon Lord erschaffen bei ({x}, {y}) mit {self.MAX_HEALTH} HP")
    
    def _load_animations(self):
        """Lädt alle Dragon Lord Animationen."""
        base_path = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "Dragon Lord")
        
        # Animation Definitionen: (Dateiname, Frame-Breite, Anzahl Frames)
        anim_defs = {
            "idle": ("dragon_lord_idle_basic_74x74.png", 74, 4),
            "walk": ("dragon_lord_walk_basic_74x74.png", 74, 8),
            "attack": ("dragon_lord_attack_arms_90x70.png", 90, 16),
            "hurt": ("dragon_lord_hurt_basic_130x130.png", 130, 5),
            "death": ("dragon_lord_death_160x160.png", 160, 36),
        }
        
        for anim_name, (filename, frame_width, num_frames) in anim_defs.items():
            filepath = os.path.join(base_path, filename)
            try:
                if os.path.exists(filepath):
                    sheet = pygame.image.load(filepath).convert_alpha()
                    frames = self._split_spritesheet(sheet, frame_width, num_frames)
                    self.animations[anim_name] = frames
                    print(f"  ✅ Dragon Lord Animation: {anim_name} ({len(frames)} Frames)")
                else:
                    print(f"  ⚠️ Animation nicht gefunden: {filename}")
            except Exception as e:
                print(f"  ❌ Fehler beim Laden von {filename}: {e}")
    
    def _split_spritesheet(self, sheet: pygame.Surface, frame_width: int, num_frames: int) -> List[pygame.Surface]:
        """Teilt ein Spritesheet in einzelne Frames."""
        frames = []
        sheet_height = sheet.get_height()
        
        for i in range(num_frames):
            x = i * frame_width
            if x + frame_width <= sheet.get_width():
                frame = sheet.subsurface((x, 0, frame_width, sheet_height))
                frames.append(frame)
        
        return frames
    
    def _set_animation_state(self, new_state: str):
        """Wechselt den Animations-Zustand und erhält die Position."""
        if new_state == self.state:
            return
        
        # Position speichern
        old_bottom = self.rect.bottom
        old_centerx = self.rect.centerx
        
        self.state = new_state
        self.current_frame = 0
        
        # Erstes Frame der neuen Animation setzen
        anim = self.animations.get(new_state, [])
        if anim:
            self.image = anim[0]
            if self.facing_left:
                self.image = pygame.transform.flip(self.image, True, False)
            
            # Rect an neue Bildgröße anpassen, aber Position erhalten
            self.rect = self.image.get_rect()
            self.rect.bottom = old_bottom
            self.rect.centerx = old_centerx
    
    def take_damage(self, amount: int, attacker=None) -> bool:
        """Nimmt Schaden und wird aggressiv."""
        if self.is_dead:
            return False
        
        # Schaden zufügen
        self.current_health = max(0, self.current_health - amount)
        print(f"🐉 Dragon Lord nimmt {amount} Schaden! HP: {self.current_health}/{self.max_health}")
        
        # Werde aggressiv! (Auch ohne expliziten Angreifer - Spieler wird im Update gefunden)
        if not self.is_aggro:
            self.is_aggro = True
            if attacker:
                self.target = attacker
            print(f"🔥 Dragon Lord ist wütend!")
        
        # Hurt Animation starten
        if self.current_health > 0:
            self._set_animation_state("hurt")
            self.hurt_timer = self.hurt_duration
        
        # Prüfe ob tot
        if self.get_health() <= 0:
            self._start_death()
        
        return self.current_health > 0
    
    def _start_death(self):
        """Startet die Todes-Animation."""
        self.is_dead = True
        self._set_animation_state("death")
        print("💀 Dragon Lord wurde besiegt!")
    
    def update(self, dt: float, player=None):
        """Update Animation und Verhalten."""
        if self.death_animation_complete:
            return
        
        # Speichere Spieler-Referenz falls aggressiv (findet Spieler automatisch)
        if player and self.is_aggro:
            self.target = player
        
        # Timer aktualisieren
        self.attack_timer = max(0, self.attack_timer - dt)
        
        if self.hurt_timer > 0:
            self.hurt_timer -= dt
            if self.hurt_timer <= 0 and not self.is_dead:
                if self.is_aggro:
                    self.state = "walk"  # Weiter angreifen
                else:
                    self.state = "idle"
        
        # Verhalten basierend auf Zustand
        if not self.is_dead and self.is_aggro and self.target:
            self._update_combat(dt)
        
        # Animation aktualisieren
        self._update_animation(dt)
    
    def _update_combat(self, dt: float):
        """Update Kampfverhalten."""
        if not self.target or self.state == "hurt":
            return
        
        # Berechne Distanz zum Ziel
        target_rect = self.target.rect if hasattr(self.target, 'rect') else None
        if not target_rect:
            return
        
        dx = target_rect.centerx - self.rect.centerx
        dy = target_rect.centery - self.rect.centery
        distance = math.sqrt(dx * dx + dy * dy)
        
        # Blickrichtung aktualisieren
        self.facing_left = dx < 0
        
        # Wenn in Angriffs-Reichweite: Angreifen
        if distance <= self.ATTACK_RANGE:
            if self.attack_timer <= 0 and self.state != "attack":
                self._start_attack()
        # Sonst: Zum Ziel bewegen
        elif distance <= self.AGGRO_RANGE * 3:  # Verfolge über längere Distanz
            if self.state != "walk":
                self._set_animation_state("walk")
            # Normalisiere Bewegungsvektor
            if distance > 0:
                move_x = (dx / distance) * self.MOVE_SPEED * dt
                move_y = (dy / distance) * self.MOVE_SPEED * dt
                self.rect.x += move_x
                self.rect.y += move_y
        else:
            # Zu weit weg - zurück zum Idle
            if self.state != "idle":
                self._set_animation_state("idle")
    
    def _start_attack(self):
        """Startet einen Angriff."""
        self._set_animation_state("attack")
        self.attack_timer = self.ATTACK_COOLDOWN
        print("⚔️ Dragon Lord greift an!")
    
    def _deal_damage_to_target(self):
        """Fügt dem Ziel Schaden zu."""
        if self.target and hasattr(self.target, 'take_damage'):
            # Prüfe ob noch in Reichweite
            target_rect = self.target.rect if hasattr(self.target, 'rect') else None
            if target_rect:
                dx = target_rect.centerx - self.rect.centerx
                dy = target_rect.centery - self.rect.centery
                distance = math.sqrt(dx * dx + dy * dy)
                
                if distance <= self.ATTACK_RANGE * 1.2:
                    self.target.take_damage(self.ATTACK_DAMAGE)
                    print(f"🐉 Dragon Lord trifft für {self.ATTACK_DAMAGE} Schaden!")
    
    def _update_animation(self, dt: float):
        """Aktualisiert die Animation."""
        self.animation_timer += self.animation_speed
        
        if self.animation_timer >= 1.0:
            self.animation_timer = 0.0
            self._next_frame()
    
    def _next_frame(self):
        """Wechselt zum nächsten Animation-Frame."""
        anim = self.animations.get(self.state, [])
        if not anim:
            anim = self.animations.get("idle", [])
        
        if anim:
            self.current_frame += 1
            
            # Spezielle Logik für bestimmte Animationen
            if self.state == "attack":
                # Bei Frame 8-10: Schaden zufügen (Mitte der Animation)
                if self.current_frame == 8:
                    self._deal_damage_to_target()
                # Nach Animation: Zurück zu Idle/Walk
                if self.current_frame >= len(anim):
                    if self.is_aggro:
                        self._set_animation_state("walk")
                    else:
                        self._set_animation_state("idle")
                    return  # State wurde gewechselt, Rest überspringen
            
            elif self.state == "death":
                if self.current_frame >= len(anim):
                    self.current_frame = len(anim) - 1
                    self.death_animation_complete = True
            
            elif self.state == "hurt":
                if self.current_frame >= len(anim):
                    self.current_frame = len(anim) - 1
            
            else:
                # Loop für idle/walk
                self.current_frame = self.current_frame % len(anim)
            
            # Position speichern (Fußpunkt = unten Mitte)
            old_bottom = self.rect.bottom
            old_centerx = self.rect.centerx
            
            # Aktualisiere Bild
            self.image = anim[self.current_frame]
            
            # Spiegeln wenn nötig
            if self.facing_left:
                self.image = pygame.transform.flip(self.image, True, False)
            
            # Rect an neue Bildgröße anpassen, aber Position erhalten
            self.rect = self.image.get_rect()
            self.rect.bottom = old_bottom
            self.rect.centerx = old_centerx
    
    def render(self, screen: pygame.Surface, camera):
        """Zeichnet den Dragon Lord."""
        # Nur zeichnen wenn sichtbar und nicht tot
        if self.image and not self.death_animation_complete and self.visible:
            screen_pos = camera.apply(self)
            screen.blit(self.image, screen_pos)
    
    def hide(self):
        """Macht den Dragon Lord unsichtbar."""
        self.visible = False
        
    def show(self):
        """Macht den Dragon Lord sichtbar."""
        self.visible = True
    
    # CombatEntity Interface
    def get_health(self) -> int:
        return self.current_health
    
    def get_max_health(self) -> int:
        return self.max_health
    
    def is_alive(self) -> bool:
        return not self.is_dead


# Factory-Funktion
_dragon_lord_instance = None

def get_dragon_lord(x: int = None, y: int = None) -> Optional[DragonLord]:
    """Gibt die Dragon Lord Instanz zurück oder erstellt eine neue."""
    global _dragon_lord_instance
    if _dragon_lord_instance is None and x is not None and y is not None:
        _dragon_lord_instance = DragonLord(x, y)
    return _dragon_lord_instance

def reset_dragon_lord():
    """Setzt die Dragon Lord Instanz zurück."""
    global _dragon_lord_instance
    _dragon_lord_instance = None
