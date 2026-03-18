# -*- coding: utf-8 -*-
"""
Magic System - Elemental Combination System
Implementiert das Magiesystem mit Elementkombinationen für Der Alchemist
"""

import pygame
import math
import random
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

try:
    from core.settings import VERBOSE_LOGS as _VERBOSE_LOGS
except Exception:
    _VERBOSE_LOGS = False

# Import MANA_SPELL_COST constant
MANA_SPELL_COST = 10  # Default value, can be overridden by settings

class ElementType(Enum):
    """Verfügbare Elemente für Magie-Kombinationen"""
    FEUER = "feuer"
    WASSER = "wasser"
    STEIN = "stein"

@dataclass
class FloatingDamage:
    """Schwebende Schadenszahl, die einem Ziel folgt"""
    damage: int
    target: Any
    start_time: float
    duration: float = 2.0  # 2 Sekunden Anzeige
    color: Tuple[int, int, int] = (255, 100, 100)  # Rot für Schaden
    offset_y: int = -30  # Über dem Ziel
    
    def is_expired(self) -> bool:
        """Prüft ob der Floating Damage abgelaufen ist"""
        current_time = pygame.time.get_ticks()
        return (current_time - self.start_time) >= (self.duration * 1000)
    
    def get_alpha(self) -> int:
        """Berechnet Alpha-Wert basierend auf Alter"""
        current_time = pygame.time.get_ticks()
        elapsed = (current_time - self.start_time) / 1000.0  # In Sekunden
        progress = elapsed / self.duration  # 0.0 bis 1.0
        
        # Fade out in den letzten 50% der Zeit
        if progress > 0.5:
            fade_progress = (progress - 0.5) / 0.5  # 0.0 bis 1.0
            return int(255 * (1.0 - fade_progress))
        return 255
    
    def get_position(self, camera=None) -> Tuple[int, int]:
        """Berechnet die aktuelle Position des Floating Damage"""
        if not hasattr(self.target, 'rect'):
            return (0, 0)
        
        # Floating-Effekt: bewegt sich nach oben
        current_time = pygame.time.get_ticks()
        elapsed = (current_time - self.start_time) / 1000.0
        float_offset = int(elapsed * 20)  # 20 Pixel pro Sekunde nach oben
        
        target_pos = (self.target.rect.centerx, self.target.rect.centery + self.offset_y - float_offset)
        
        # Kamera-Transformation anwenden
        if camera:
            # Erstelle temporäres Rect für Transformation
            temp_rect = pygame.Rect(target_pos[0] - 10, target_pos[1] - 10, 20, 20)
            transformed_rect = camera.apply_rect(temp_rect)
            return (transformed_rect.centerx, transformed_rect.centery)
        
        return target_pos

@dataclass
class MagicEffect:
    """Repräsentiert einen Magie-Effekt"""
    name: str
    description: str
    elements: List[ElementType]
    effect_type: str
    damage: int = 0
    healing: int = 0
    duration: int = 0
    radius: int = 0
    special_effects: Dict[str, Any] = None

    def __post_init__(self):
        if self.special_effects is None:
            self.special_effects = {}

class MagicProjectile(pygame.sprite.Sprite):
    """Basis-Klasse für Magie-Projektile"""

    _FRAME_SIZE = (80, 80)
    _FRAME_COUNT = 16
    _FRAMES_CACHE: Dict[str, List[pygame.Surface]] = {}
    
    def __init__(self, start_x: int, start_y: int, target_x: int, target_y: int, 
                 speed: int = 300, damage: int = 25, element_type: str = "feuer"):  # Schnellere Projektile
        super().__init__()
        
        self.damage = damage
        self.speed = speed
        self.element_type = element_type
        self.is_alive = True
        
        # Berechne Richtung
        direction = pygame.math.Vector2(target_x - start_x, target_y - start_y)
        if direction.length() > 0:
            direction = direction.normalize()
        self.direction = direction
        
        # Erstelle Sprite basierend auf Element
        self._frames = self._get_projectile_frames(element_type)
        self._anim_frame = 0
        self.image = self._frames[self._anim_frame]
        self.rect = self.image.get_rect(center=(start_x, start_y))
        self.hitbox = self.rect.copy()
        
        # Animation
        self.last_update = pygame.time.get_ticks()
        self.animation_speed = 100  # ms

    @classmethod
    def _get_projectile_frames(cls, element_type: str) -> List[pygame.Surface]:
        cached = cls._FRAMES_CACHE.get(element_type)
        if cached is not None:
            return cached

        frames: List[pygame.Surface] = []
        width, height = cls._FRAME_SIZE
        center = (width // 2, height // 2)

        for frame_index in range(cls._FRAME_COUNT):
            sprite = pygame.Surface(cls._FRAME_SIZE, pygame.SRCALPHA)

            phase = (frame_index / cls._FRAME_COUNT) * (2 * math.pi)
            pulse = abs(math.sin(phase)) * 0.3 + 0.7

            if element_type == "feuer":
                outer_radius = int(35 * pulse)
                inner_radius = int(25 * pulse)
                core_radius = int(15 * pulse)
                pygame.draw.circle(sprite, (255, 50, 0), center, outer_radius)
                pygame.draw.circle(sprite, (255, 200, 0), center, inner_radius)
                pygame.draw.circle(sprite, (255, 255, 100), center, core_radius)

            elif element_type == "wasser":
                outer_radius = int(35 * pulse)
                inner_radius = int(25 * pulse)
                core_radius = int(15 * pulse)
                pygame.draw.circle(sprite, (0, 50, 255), center, outer_radius)
                pygame.draw.circle(sprite, (100, 150, 255), center, inner_radius)
                pygame.draw.circle(sprite, (200, 230, 255), center, core_radius)

            elif element_type == "wirbelattacke":
                rotation_angle = phase
                center_x, center_y = center

                for i in range(8):
                    angle = rotation_angle + (i * math.pi / 4)
                    radius = 30 * pulse
                    x = center_x + int(radius * math.cos(angle))
                    y = center_y + int(radius * math.sin(angle))
                    pygame.draw.circle(sprite, (150 + int(50 * pulse), 50, 200), (x, y), 8)

                pygame.draw.circle(sprite, (200, 100, 255), center, int(12 * pulse))

            frames.append(sprite)

        cls._FRAMES_CACHE[element_type] = frames
        return frames
        
    def create_projectile_sprite(self, element_type: str) -> pygame.Surface:
        """Erstellt animiertes Sprite basierend auf Element-Typ"""
        return self._get_projectile_frames(element_type)[0]
    
    def update(self, dt: float = 1.0/60.0, targets: List[Any] = None, magic_system=None):
        """Update Projektil Position und Kollision"""
        if not self.is_alive:
            return
            
        # Bewegung
        movement = self.direction * self.speed * dt
        self.rect.centerx += movement.x
        self.rect.centery += movement.y
        self.hitbox.center = self.rect.center
        
        # Debug: Position ausgeben (nur alle 60 Frames = 1 Sekunde)
        if hasattr(self, '_debug_counter'):
            self._debug_counter += 1
        else:
            self._debug_counter = 0
        
        # Rotation und Animation für visuellen Effekt
        current_time = pygame.time.get_ticks()
        if current_time - self.last_update >= self.animation_speed:
            self._anim_frame = (self._anim_frame + 1) % len(self._frames)
            self.image = self._frames[self._anim_frame]
            self.last_update = current_time
        
        # Kollision mit Zielen prüfen
        if targets:
            for target in targets:
                if hasattr(target, 'hitbox') and self.hitbox.colliderect(target.hitbox):
                    self.hit_target(target, magic_system)
                    return
                elif hasattr(target, 'rect') and self.hitbox.colliderect(target.rect):
                    self.hit_target(target, magic_system)
                    return
        
        # Bildschirmgrenzen prüfen (entferne Projektil)
        # Erweiterte Weltgrenzen für größere Maps
        world_bounds = 3000  # Viel größere Welt
        if (self.rect.centerx < -world_bounds or self.rect.centerx > world_bounds or
            self.rect.centery < -world_bounds or self.rect.centery > world_bounds):
            self.is_alive = False
    
    def hit_target(self, target, magic_system=None):
        """Behandle Treffer auf Ziel (Schaden skaliert mit Spieler-Level)"""
        if hasattr(target, 'take_damage'):
            class_name = target.__class__.__name__.lower() if hasattr(target, '__class__') else ""
            
            # self.damage enthält den level-skalierten Basisschaden (z.B. 25 * 1.15 bei Lvl 2)
            base = self.damage  # Bereits vom Level-Scaling berechnet
            
            if self.element_type == "feuer":
                # Feuerball: ×2 Schaden gegen Wasserkreaturen, normaler Schaden sonst
                if ('water' in class_name or 'wasser' in class_name or 
                    'ice' in class_name or 'eis' in class_name):
                    damage = int(base * 2)
                    target.take_damage(damage)
                    if magic_system:
                        magic_system.add_floating_damage(target, damage, "fire")
                    if _VERBOSE_LOGS:
                        print(f"🔥 Feuerball trifft Wasserkreatur für {damage} Schaden! (Lvl-Basis: {base})")
                else:
                    damage = base
                    target.take_damage(damage)
                    if magic_system:
                        magic_system.add_floating_damage(target, damage, "fire")
                    if _VERBOSE_LOGS:
                        print(f"🔥 Feuerball trifft für {damage} Schaden! (Lvl-Basis: {base})")
                    
            elif self.element_type == "wasser":
                # Wasserkugel: ×2 Schaden gegen Feuerkreaturen, normaler Schaden sonst
                if ('fire' in class_name or 'feuer' in class_name or 
                    'fireworm' in class_name or 'demon' in class_name or 
                    'flame' in class_name or 'lava' in class_name):
                    damage = int(base * 2)
                    target.take_damage(damage)
                    if magic_system:
                        magic_system.add_floating_damage(target, damage, "water")
                    if _VERBOSE_LOGS:
                        print(f"💧 Wasserkugel trifft Feuerkreatur für {damage} Schaden! (Lvl-Basis: {base})")
                else:
                    damage = base
                    target.take_damage(damage)
                    if magic_system:
                        magic_system.add_floating_damage(target, damage, "water")
                    if _VERBOSE_LOGS:
                        print(f"💧 Wasserkugel trifft für {damage} Schaden! (Lvl-Basis: {base})")
                    
            else:
                # Andere Projektile verwenden Standard-Schaden
                damage = base
                target.take_damage(damage)
                if magic_system:
                    magic_system.add_floating_damage(target, damage, "normal")
                if _VERBOSE_LOGS:
                    print(f"✨ Projektil trifft für {damage} Schaden!")
        
        self.is_alive = False
    
    def should_remove(self) -> bool:
        """Prüft ob Projektil entfernt werden soll"""
        return not self.is_alive

class MagicSystem:
    """Hauptklasse für das Magie-System"""
    
    def __init__(self):
        self.selected_elements: List[ElementType] = []
        self.max_elements = 2  # Maximum 2 Elemente für Kombinationen
        self.magic_effects: Dict[Tuple[ElementType, ...], MagicEffect] = {}
        self.active_effects: Dict[str, Dict[str, Any]] = {}  # Aktive Buffs/Debuffs
        self.projectiles: pygame.sprite.Group = pygame.sprite.Group()
        self.floating_damages: List[FloatingDamage] = []  # Liste der schwebenden Schadenszahlen
        self.is_ready = False  # Warmup-Status

        # Render-Caches (Performance: vermeidet per-frame Font/Suface Erstellung)
        self._floating_damage_font: Optional[pygame.font.Font] = None
        self._floating_damage_shadow_font: Optional[pygame.font.Font] = None
        self._floating_damage_surface_cache: Dict[Tuple[str, Tuple[int, int, int], bool, int], pygame.Surface] = {}
        self._floating_damage_alpha_bucket: int = 16

        self._whirlwind_font: Optional[pygame.font.Font] = None
        self._whirlwind_range_surface: Optional[pygame.Surface] = None
        
        self._initialize_magic_effects()
        self._warmup_system()  # Sofortiges Warmup beim Start

    def _get_floating_damage_font(self) -> pygame.font.Font:
        if self._floating_damage_font is None or not pygame.font.get_init():
            self._floating_damage_font = pygame.font.Font(None, 36)
        return self._floating_damage_font

    def _get_floating_damage_shadow_font(self) -> pygame.font.Font:
        if self._floating_damage_shadow_font is None or not pygame.font.get_init():
            self._floating_damage_shadow_font = pygame.font.Font(None, 36)
        return self._floating_damage_shadow_font

    def _alpha_bucket(self, alpha: int) -> int:
        if alpha >= 255:
            return 255
        if alpha <= 0:
            return 0
        bucket = self._floating_damage_alpha_bucket
        return max(0, min(255, (alpha // bucket) * bucket))

    def _get_floating_damage_surface(
        self,
        text: str,
        color: Tuple[int, int, int],
        alpha: int,
        is_shadow: bool,
    ) -> pygame.Surface:
        bucketed_alpha = self._alpha_bucket(alpha)
        key = (text, color, is_shadow, bucketed_alpha)
        cached = self._floating_damage_surface_cache.get(key)
        if cached is not None:
            return cached

        font = self._get_floating_damage_shadow_font() if is_shadow else self._get_floating_damage_font()
        surface = font.render(text, True, color)
        if bucketed_alpha < 255:
            surface.set_alpha(bucketed_alpha)
        self._floating_damage_surface_cache[key] = surface
        return surface

    def _get_whirlwind_range_surface(self) -> pygame.Surface:
        if self._whirlwind_range_surface is None or not pygame.font.get_init():
            if self._whirlwind_font is None or not pygame.font.get_init():
                self._whirlwind_font = pygame.font.Font(None, 24)
            self._whirlwind_range_surface = self._whirlwind_font.render("2 Tiles Reichweite", True, (255, 255, 255))
        return self._whirlwind_range_surface
    
    def _initialize_magic_effects(self):
        """Initialisiert alle verfügbaren Magie-Effekte"""
        
        # Feuer + Feuer = Feuerball
        self.magic_effects[(ElementType.FEUER, ElementType.FEUER)] = MagicEffect(
            name="Feuerball",
            description="Fliegt in die Richtung, in welche der Spieler schaut",
            elements=[ElementType.FEUER, ElementType.FEUER],
            effect_type="projectile",
            damage=25
        )
        
        # Wasser + Wasser = Wasserkugel
        self.magic_effects[(ElementType.WASSER, ElementType.WASSER)] = MagicEffect(
            name="Wasserkugel",
            description="Macht 50 Schaden gegen Feuerkreaturen",
            elements=[ElementType.WASSER, ElementType.WASSER],
            effect_type="projectile",
            damage=25,
            special_effects={"anti_fire": 50}
        )
        
        # Stein + Stein = Schutzschild
        self.magic_effects[(ElementType.STEIN, ElementType.STEIN)] = MagicEffect(
            name="Schutzschild",
            description="Unverwundbar für 2 Sekunden",
            elements=[ElementType.STEIN, ElementType.STEIN],
            effect_type="shield",
            duration=2000  # 2 Sekunden in Millisekunden
        )
        
        # Feuer + Wasser = Heilungstrank (beide Reihenfolgen)
        self.magic_effects[(ElementType.FEUER, ElementType.WASSER)] = MagicEffect(
            name="Heilungstrank",
            description="Regeneriert 50 HP",
            elements=[ElementType.FEUER, ElementType.WASSER],
            effect_type="healing",
            healing=50
        )
        self.magic_effects[(ElementType.WASSER, ElementType.FEUER)] = MagicEffect(
            name="Heilungstrank",
            description="Regeneriert 50 HP",
            elements=[ElementType.WASSER, ElementType.FEUER],
            effect_type="healing",
            healing=50
        )
        
        # Feuer + Stein = Wirbelattacke (beide Reihenfolgen)
        self.magic_effects[(ElementType.FEUER, ElementType.STEIN)] = MagicEffect(
            name="Wirbelattacke",
            description="Macht allen Gegnern 10 Schaden im Radius von 2 Tiles",
            elements=[ElementType.FEUER, ElementType.STEIN],
            effect_type="area_attack",
            damage=10,
            radius=128  # 2 Tiles (64px pro Tile)
        )
        self.magic_effects[(ElementType.STEIN, ElementType.FEUER)] = MagicEffect(
            name="Wirbelattacke",
            description="Macht allen Gegnern 10 Schaden im Radius von 2 Tiles",
            elements=[ElementType.STEIN, ElementType.FEUER],
            effect_type="area_attack",
            damage=10,
            radius=128
        )
        
        # Wasser + Stein = Unsichtbarkeit (beide Reihenfolgen)
        self.magic_effects[(ElementType.WASSER, ElementType.STEIN)] = MagicEffect(
            name="Unsichtbarkeit",
            description="Unsichtbar für 5 Sekunden",
            elements=[ElementType.WASSER, ElementType.STEIN],
            effect_type="invisibility",
            duration=5000  # 5 Sekunden
        )
        self.magic_effects[(ElementType.STEIN, ElementType.WASSER)] = MagicEffect(
            name="Unsichtbarkeit",
            description="Unsichtbar für 5 Sekunden",
            elements=[ElementType.STEIN, ElementType.WASSER],
            effect_type="invisibility",
            duration=5000
        )
    
    def _warmup_system(self):
        """Erwärmt das Magie-System durch Vor-Erstellung der Sprites"""
        # Erstelle einmal alle Sprite-Typen zur Vorbereitung
        dummy_sprites = []
        try:
            # Erstelle ein temporäres Projektil um die create_projectile_sprite Methode zu testen
            temp_projectile = MagicProjectile(100, 100, 200, 100, element_type="feuer")
            dummy_sprites.append(temp_projectile.image)
            
            temp_projectile2 = MagicProjectile(100, 100, 200, 100, element_type="wasser")
            dummy_sprites.append(temp_projectile2.image)
            
            temp_projectile3 = MagicProjectile(100, 100, 200, 100, element_type="wirbelattacke")
            dummy_sprites.append(temp_projectile3.image)
            
            self.is_ready = True
            
        except Exception as e:
            self.is_ready = True  # Trotzdem als bereit markieren
    
    def add_element(self, element: ElementType) -> bool:
        """Fügt ein Element zur Auswahl hinzu"""
        if len(self.selected_elements) >= self.max_elements:
            return False
        
        self.selected_elements.append(element)
        return True
    
    def clear_elements(self):
        """Leert die Element-Auswahl"""
        self.selected_elements.clear()
    
    def get_selected_elements_str(self) -> str:
        """Gibt ausgewählte Elemente als String zurück"""
        return " + ".join([e.value for e in self.selected_elements])
    
    def can_cast_magic(self) -> bool:
        """Prüft ob Magie gewirkt werden kann"""
        return len(self.selected_elements) >= 2
    
    def cast_magic(self, caster, target_pos: Optional[Tuple[int, int]] = None, 
                   enemies: Optional[List[Any]] = None) -> Optional[MagicEffect]:
        """Wirkt Magie basierend auf ausgewählten Elementen"""
        # Prüfe ob System bereit ist
        if not hasattr(self, 'is_ready') or not self.is_ready:
            self._warmup_system()
        
        if not self.can_cast_magic():
            return None
        
        # Erstelle Tupel für Dictionary-Lookup (nicht sortiert - direkte Reihenfolge)
        element_key = tuple(self.selected_elements)
        
        # Falls direkte Reihenfolge nicht funktioniert, versuche umgekehrte Reihenfolge
        if element_key not in self.magic_effects and len(self.selected_elements) == 2:
            element_key = (self.selected_elements[1], self.selected_elements[0])
        
        if element_key not in self.magic_effects:
            self.clear_elements()
            return None
        
        effect = self.magic_effects[element_key]
        
        # Spellspezifische Mana-Kosten (Unsichtbarkeit und Schild sind teuer)
        spell_mana_cost = MANA_SPELL_COST
        if effect.effect_type == "invisibility":
            spell_mana_cost = 60  # Unsichtbarkeit kostet 60% des Max-Mana
        elif effect.effect_type == "shield":
            spell_mana_cost = 50  # Schild kostet 50% des Max-Mana
        
        # Mana-Kosten prüfen
        if hasattr(caster, 'spend_mana') and not caster.spend_mana(spell_mana_cost):
            # Optionales Feedback für nicht genug Mana
            if _VERBOSE_LOGS:
                print("⚠️ Nicht genug Mana!")
            self.clear_elements()
            return None
        
        # Effekt ausführen
        self._execute_effect(effect, caster, target_pos, enemies)
        
        # Elemente nach erfolgreichem Zaubern leeren
        self.clear_elements()
        return effect
    
    def _execute_effect(self, effect: MagicEffect, caster, target_pos: Optional[Tuple[int, int]], 
                       enemies: Optional[List[Any]]):
        """Führt den spezifischen Magie-Effekt aus (mit Level- + Shop-Scaling)"""
        
        # Level-Damage-Multiplikator anwenden
        damage_mult = getattr(caster, 'get_damage_multiplier', lambda: 1.0)()
        
        # Shop-Damage-Bonus: base_attack_damage über dem Standard (30) erhöht auch Magie
        base_std = 30  # Standard-Basis-Schaden ohne Upgrades
        base_attack = getattr(caster, 'base_attack_damage', base_std)
        if base_attack > base_std:
            # Zusätzlicher Multiplikator basierend auf Shop-Upgrade
            damage_mult *= (base_attack / base_std)
        
        if effect.effect_type == "projectile":
            # Skalierter Effekt für Projektile
            scaled_effect = MagicEffect(
                name=effect.name, description=effect.description,
                elements=effect.elements, effect_type=effect.effect_type,
                damage=int(effect.damage * damage_mult),
                duration=effect.duration, radius=effect.radius,
                healing=effect.healing, special_effects=effect.special_effects
            )
            self._cast_projectile(scaled_effect, caster, target_pos)
        
        elif effect.effect_type == "healing":
            self._cast_healing(effect, caster)
        
        elif effect.effect_type == "shield":
            self._cast_shield(effect, caster)
        
        elif effect.effect_type == "area_attack":
            # Skalierter Effekt für Area Attack
            scaled_effect = MagicEffect(
                name=effect.name, description=effect.description,
                elements=effect.elements, effect_type=effect.effect_type,
                damage=int(effect.damage * damage_mult),
                duration=effect.duration, radius=effect.radius,
                healing=effect.healing, special_effects=effect.special_effects
            )
            self._cast_area_attack(scaled_effect, caster, enemies)
        
        elif effect.effect_type == "invisibility":
            self._cast_invisibility(effect, caster)
    
    def _cast_projectile(self, effect: MagicEffect, caster, target_pos: Optional[Tuple[int, int]]):
        """Erstellt Projektil-Magie"""        
        # Nutze die letzte Bewegungsrichtung des Spielers (unterstützt alle Richtungen)
        if hasattr(caster, 'last_direction') and caster.last_direction.length() > 0:
            # Volle 2D-Richtung: hoch, runter, links, rechts, diagonal
            direction = caster.last_direction.normalize()
            target_pos = (caster.rect.centerx + int(direction.x * 500),
                          caster.rect.centery + int(direction.y * 500))
        elif hasattr(caster, 'facing_right'):
            # Fallback: nur horizontal
            offset_x = 500 if caster.facing_right else -500
            target_pos = (caster.rect.centerx + offset_x, caster.rect.centery)
        else:
            # Fallback: nach rechts
            target_pos = (caster.rect.centerx + 500, caster.rect.centery)
        
        # Element-Typ für Projektil bestimmen
        element_type = "feuer"
        if ElementType.WASSER in effect.elements:
            element_type = "wasser"
        elif ElementType.FEUER in effect.elements and ElementType.STEIN in effect.elements:
            element_type = "wirbelattacke"
        
        projectile = MagicProjectile(
            start_x=caster.rect.centerx,
            start_y=caster.rect.centery,
            target_x=target_pos[0],
            target_y=target_pos[1],
            damage=effect.damage,
            element_type=element_type
        )
        
        self.projectiles.add(projectile)
    
    def _cast_healing(self, effect: MagicEffect, caster):
        """Führt Heilung aus (+ Level-Bonus)"""
        if hasattr(caster, 'current_health') and hasattr(caster, 'max_health'):
            old_health = caster.current_health
            # Level-Bonus: +5 HP Heilung pro Level
            heal_bonus = getattr(caster, 'get_heal_bonus', lambda: 0)()
            total_healing = effect.healing + heal_bonus
            caster.current_health = min(caster.max_health, caster.current_health + total_healing)
            healed = caster.current_health - old_health
            
            # Floating Damage für Heilung hinzufügen (positiver Wert)
            if healed > 0:
                self.add_floating_damage(caster, healed, "heal")
            
            try:
                from core.settings import VERBOSE_LOGS
            except Exception:
                VERBOSE_LOGS = False  # type: ignore
            if VERBOSE_LOGS:  # type: ignore[name-defined]
                print(f"💚 Geheilt um {healed} HP! ({caster.current_health}/{caster.max_health})")
    
    def _cast_shield(self, effect: MagicEffect, caster):
        """Aktiviert Schutzschild"""
        current_time = pygame.time.get_ticks()
        self.active_effects["shield"] = {
            "start_time": current_time,
            "duration": effect.duration,
            "target": caster
        }
        if _VERBOSE_LOGS:
            print(f"🛡️ Schutzschild aktiviert für {effect.duration/1000}s!")
    
    def _cast_area_attack(self, effect: MagicEffect, caster, enemies: Optional[List[Any]]):
        """Führt Flächenangriff aus"""        
        if not enemies:
            return
        
        caster_pos = pygame.math.Vector2(caster.rect.center)
        hit_enemies = []
        
        for enemy in enemies:
            if hasattr(enemy, 'rect'):
                enemy_pos = pygame.math.Vector2(enemy.rect.center)
                distance = caster_pos.distance_to(enemy_pos)
                
                if distance <= effect.radius:
                    if hasattr(enemy, 'take_damage'):
                        # Übergebe Caster als Angreifer für Aggro-System
                        try:
                            enemy.take_damage(effect.damage, attacker=caster)
                        except TypeError:
                            enemy.take_damage(effect.damage)
                        # Floating Damage für Area Attack hinzufügen
                        self.add_floating_damage(enemy, effect.damage, "area")
                        hit_enemies.append(enemy)
        
        # Visueller Effekt für Wirbelattacke mit Reichweiten-Anzeige
        self._create_whirlwind_effect(caster_pos, effect.radius)
        
        if hit_enemies:
            try:
                from core.settings import VERBOSE_LOGS
            except Exception:
                VERBOSE_LOGS = False  # type: ignore
            if VERBOSE_LOGS:  # type: ignore[name-defined]
                print(f"🌪️ Wirbelattacke trifft {len(hit_enemies)} Feinde!")
        else:
            try:
                from core.settings import VERBOSE_LOGS
            except Exception:
                VERBOSE_LOGS = False  # type: ignore
            if VERBOSE_LOGS:  # type: ignore[name-defined]
                print(f"🌪️ Wirbelattacke ausgeführt - keine Feinde in Reichweite (2 Tiles)")
    
    def _create_whirlwind_effect(self, center_pos, radius):
        """Erstellt visuellen Wirbel-Effekt mit deutlicher Reichweiten-Animation"""
        current_time = pygame.time.get_ticks()

        # Precompute particles once (vermeidet per-frame random)
        rng = random.Random(current_time)
        particles = [(rng.random() * 2 * math.pi, rng.uniform(0.5, 1.0)) for _ in range(10)]
        
        # Erstelle Whirlwind-Effekt mit verbesserter Animation
        whirlwind_effect = {
            "center": center_pos,
            "radius": radius,
            "start_time": current_time,
            "duration": 3000,  # 3 Sekunden Animation für bessere Sichtbarkeit
            "type": "whirlwind",
            "_particles": particles,
            "_spiral_angles": list(range(0, 360, 20)),
            "_scratch": None,
            "_scratch_size": None,
            "_scratch_pad": 8,
        }
        
        # Füge Effekt zu aktiven visuellen Effekten hinzu
        if "visual_effects" not in self.active_effects:
            self.active_effects["visual_effects"] = []
        self.active_effects["visual_effects"].append(whirlwind_effect)
        try:
            from core.settings import VERBOSE_LOGS
        except Exception:
            VERBOSE_LOGS = False  # type: ignore
        if VERBOSE_LOGS:  # type: ignore[name-defined]
            print(f"🌪️ Whirlwind-Animation startet - Reichweite: {radius} Pixel (2 Tiles)")
    
    def add_floating_damage(self, target, damage: int, damage_type: str = "normal"):
        """Fügt eine schwebende Schadenszahl hinzu"""
        current_time = pygame.time.get_ticks()
        
        # Farbe basierend auf Schadenstyp
        color = (255, 100, 100)  # Standard Rot
        if damage_type == "fire":
            color = (255, 150, 50)   # Orange für Feuer
        elif damage_type == "water":
            color = (100, 150, 255)  # Blau für Wasser
        elif damage_type == "area":
            color = (255, 200, 100)  # Gelb für Bereichsschaden
        elif damage_type == "heal":
            color = (100, 255, 100)  # Grün für Heilung
        
        floating_damage = FloatingDamage(
            damage=damage,
            target=target,
            start_time=current_time,
            duration=2.5,  # 2.5 Sekunden sichtbar
            color=color
        )
        
        self.floating_damages.append(floating_damage)
    
    def _cast_invisibility(self, effect: MagicEffect, caster):
        """Aktiviert Unsichtbarkeit (+ Level-Speed-Bonus)"""
        current_time = pygame.time.get_ticks()
        
        # Level-Bonus: +5% Speed pro Level während Unsichtbarkeit
        speed_bonus = getattr(caster, 'get_invis_speed_bonus', lambda: 0)()
        if speed_bonus > 0 and hasattr(caster, 'base_speed'):
            caster.speed = int(caster.base_speed * (1 + speed_bonus))
        
        self.active_effects["invisibility"] = {
            "start_time": current_time,
            "duration": effect.duration,
            "target": caster,
            "speed_bonus_applied": speed_bonus > 0
        }
        if _VERBOSE_LOGS:
            print(f"👻 Unsichtbarkeit aktiviert für {effect.duration/1000}s! Speed-Bonus: +{int(speed_bonus*100)}%")
    
    def update(self, dt: float = 1.0/60.0, enemies: Optional[List[Any]] = None):
        """Update das Magie-System"""
        # Update Projektile
        for projectile in self.projectiles.copy():
            projectile.update(dt, enemies, magic_system=self)  # Übergebe self als magic_system
            if projectile.should_remove():
                self.projectiles.remove(projectile)
        
        # Update Floating Damages
        self.floating_damages = [fd for fd in self.floating_damages if not fd.is_expired()]
        
        # Update aktive Effekte
        current_time = pygame.time.get_ticks()
        expired_effects = []
        
        for effect_name, effect_data in self.active_effects.items():
            # Spezialbehandlung für visual_effects (ist eine Liste)
            if effect_name == "visual_effects":
                continue  # Wird in _draw_visual_effects gehandhabt
            
            # Normale Effekte haben start_time und duration
            if isinstance(effect_data, dict) and "start_time" in effect_data and "duration" in effect_data:
                if current_time - effect_data["start_time"] >= effect_data["duration"]:
                    expired_effects.append(effect_name)
        
        # Entferne abgelaufene Effekte
        for effect_name in expired_effects:
            # Speed-Bonus zurücksetzen wenn Unsichtbarkeit endet
            if effect_name == "invisibility":
                effect_data = self.active_effects[effect_name]
                target = effect_data.get("target")
                if target and effect_data.get("speed_bonus_applied", False):
                    if hasattr(target, 'base_speed'):
                        target.speed = target.base_speed
                        if _VERBOSE_LOGS:
                            print(f"👻 Unsichtbarkeit endet - Speed zurückgesetzt auf {target.base_speed}")
            del self.active_effects[effect_name]
    
    def is_effect_active(self, effect_name: str) -> bool:
        """Prüft ob ein Effekt aktiv ist"""
        return effect_name in self.active_effects
    
    def is_shielded(self, target) -> bool:
        """Prüft ob Ziel durch Schild geschützt ist"""
        if "shield" not in self.active_effects:
            return False
        
        shield_data = self.active_effects["shield"]
        return shield_data["target"] == target
    
    def is_invisible(self, target) -> bool:
        """Prüft ob Ziel unsichtbar ist"""
        if "invisibility" not in self.active_effects:
            return False
        
        invis_data = self.active_effects["invisibility"]
        return invis_data["target"] == target
    
    def get_projectiles(self) -> pygame.sprite.Group:
        """Gibt alle aktiven Projektile zurück"""
        return self.projectiles
    
    def draw_projectiles(self, screen, camera=None):
        """Zeichnet alle Projektile, visuellen Effekte und Floating Damages"""
        # Projektile zeichnen
        for projectile in self.projectiles:
            if camera:
                # Camera.apply() gibt ein Rect zurück
                screen_rect = camera.apply(projectile)
                screen.blit(projectile.image, screen_rect)
            else:
                screen.blit(projectile.image, projectile.rect)
        
        # Visuelle Effekte zeichnen (Whirlwind-Animation)
        self._draw_visual_effects(screen, camera)
        
        # Floating Damages zeichnen
        self._draw_floating_damages(screen, camera)
    
    def _draw_floating_damages(self, screen, camera=None):
        """Zeichnet alle aktiven Floating Damage Zahlen"""
        for floating_damage in self.floating_damages:
            # Position des Floating Damage ermitteln
            pos = floating_damage.get_position(camera)
            
            # Alpha-Wert für Fade-Out Effekt
            alpha = floating_damage.get_alpha()
            
            # Text basierend auf Damage-Typ
            if floating_damage.color == (100, 255, 100):  # Grün = Heilung
                text = f"+{floating_damage.damage}"
            else:  # Schaden
                text = f"-{floating_damage.damage}"

            # Text + Shadow Surfaces (gecached, inkl. Alpha-Buckets)
            text_surface = self._get_floating_damage_surface(text, floating_damage.color, alpha, is_shadow=False)
            
            # Zentriere den Text über dem Ziel
            text_rect = text_surface.get_rect(center=pos)
            
            # Schwarzer Schatten für bessere Lesbarkeit
            shadow_surface = self._get_floating_damage_surface(text, (0, 0, 0), alpha, is_shadow=True)
            
            # Schatten leicht versetzt zeichnen
            shadow_rect = shadow_surface.get_rect(center=(pos[0] + 2, pos[1] + 2))
            screen.blit(shadow_surface, shadow_rect)
            
            # Haupttext zeichnen
            screen.blit(text_surface, text_rect)
    
    def _draw_visual_effects(self, screen, camera=None):
        """Zeichnet visuelle Effekte wie Whirlwind-Animationen"""
        if "visual_effects" not in self.active_effects:
            return
            
        current_time = pygame.time.get_ticks()
        effects_to_remove = []
        
        for effect in self.active_effects["visual_effects"]:
            if effect["type"] == "whirlwind":
                # Prüfe ob Effekt noch aktiv ist
                elapsed = current_time - effect["start_time"]
                if elapsed >= effect["duration"]:
                    effects_to_remove.append(effect)
                    continue
                
                # Animation-Progress (0.0 bis 1.0)
                progress = elapsed / effect["duration"]
                
                # Zeichne Whirlwind-Effekt
                self._draw_whirlwind_animation(screen, camera, effect, progress)
        
        # Entferne abgelaufene Effekte
        for effect in effects_to_remove:
            self.active_effects["visual_effects"].remove(effect)
        
        # Entferne leere visual_effects Liste
        if not self.active_effects["visual_effects"]:
            del self.active_effects["visual_effects"]
    
    def _draw_whirlwind_animation(self, screen, camera, effect, progress):
        """Zeichnet die Whirlwind-Animation mit deutlicher Reichweiten-Anzeige"""
        center = effect["center"]
        radius = effect["radius"]
        
        # Kamera-Transformation anwenden
        if camera:
            # Erstelle temporäres Rect für Transformation
            temp_rect = pygame.Rect(center.x - radius, center.y - radius, radius * 2, radius * 2)
            transformed_rect = camera.apply_rect(temp_rect)
            screen_center = (transformed_rect.centerx, transformed_rect.centery)
            screen_radius = int(radius * camera.zoom_factor)
        else:
            screen_center = (int(center.x), int(center.y))
            screen_radius = int(radius)

        # Scratch surface für korrektes Alpha + weniger Screen-Overdraw
        pad = int(effect.get("_scratch_pad", 8))
        scratch_size = (max(1, screen_radius * 2 + pad), max(1, screen_radius * 2 + pad))
        if effect.get("_scratch") is None or effect.get("_scratch_size") != scratch_size:
            effect["_scratch"] = pygame.Surface(scratch_size, pygame.SRCALPHA)
            effect["_scratch_size"] = scratch_size
        scratch: pygame.Surface = effect["_scratch"]
        scratch.fill((0, 0, 0, 0))

        local_center = (scratch_size[0] // 2, scratch_size[1] // 2)
        topleft = (screen_center[0] - local_center[0], screen_center[1] - local_center[1])
        
        # Mehrphasige Animation
        
        # Phase 1: Reichweiten-Ring erscheint (erste 30%)
        if progress < 0.3:
            # Expandierender Ring zur Reichweiten-Anzeige
            current_radius = int(screen_radius * (progress / 0.3))
            alpha = int(200 * (progress / 0.3))
            
            # Deutlicher Reichweiten-Ring
            pygame.draw.circle(scratch, (255, 255, 0, alpha), local_center, current_radius, 4)  # Gelber Ring
            pygame.draw.circle(scratch, (255, 150, 0, alpha), local_center, current_radius, 2)  # Orange Akzent
            
            # Text-Anzeige für Reichweite
            if progress > 0.1:  # Nach kurzer Verzögerung
                text_surface = self._get_whirlwind_range_surface()
                text_rect = text_surface.get_rect(center=(screen_center[0], screen_center[1] - screen_radius - 30))
                screen.blit(text_surface, text_rect)
        
        # Phase 2: Wirbel-Effekt (30% - 70%)
        elif progress < 0.7:
            phase_progress = (progress - 0.3) / 0.4  # 0.0 bis 1.0
            
            # Pulsierender Reichweiten-Ring
            pulse = abs(math.sin(phase_progress * math.pi * 8)) * 0.2 + 0.8
            ring_radius = int(screen_radius * pulse)
            
            # Mehrere konzentrische Ringe
            colors = [
                (255, 100, 0, 180),   # Feuer-Orange
                (139, 69, 19, 150),   # Stein-Braun
                (255, 200, 100, 120)  # Hell-Orange
            ]
            
            for i, color in enumerate(colors):
                ring_r = ring_radius - (i * 20)
                if ring_r > 0:
                    pygame.draw.circle(scratch, color, local_center, ring_r, max(1, 4 - i))
            
            # Rotierendes Spiral-Muster
            rotation_angle = phase_progress * 720  # 2 volle Umdrehungen
            
            for angle_step in effect.get("_spiral_angles", range(0, 360, 20)):
                angle = math.radians(angle_step + rotation_angle)
                spiral_radius = screen_radius * 0.8
                x = local_center[0] + int(math.cos(angle) * spiral_radius)
                y = local_center[1] + int(math.sin(angle) * spiral_radius)
                
                # Zeichne Wirbel-Punkte
                pygame.draw.circle(scratch, (255, 255, 150, 255), (x, y), 3)
        
        # Phase 3: Ausklang-Effekt (70% - 100%)
        else:
            fade_progress = (progress - 0.7) / 0.3  # 0.0 bis 1.0
            alpha = int(150 * (1.0 - fade_progress))
            
            # Schrumpfender Ring
            final_radius = int(screen_radius * (1.0 - fade_progress))
            if final_radius > 0 and alpha > 0:
                pygame.draw.circle(scratch, (255, 200, 0, alpha), local_center, final_radius, 3)
                
                # Funkelnde Partikel-Effekte
                particle_count = int(10 * (1.0 - fade_progress))
                particles = effect.get("_particles") or []
                for i in range(min(particle_count, len(particles))):
                    angle, dist_ratio = particles[i]
                    distance = int(final_radius * dist_ratio)
                    px = local_center[0] + int(math.cos(angle) * distance)
                    py = local_center[1] + int(math.sin(angle) * distance)
                    pygame.draw.circle(scratch, (255, 255, 255, alpha), (px, py), 2)
        
        # Immer sichtbare Reichweiten-Markierung (schwach)
        if screen_radius > 0:
            pygame.draw.circle(scratch, (100, 100, 100, 60), local_center, screen_radius, 1)

        screen.blit(scratch, topleft)
    
    def get_available_combinations(self) -> List[str]:
        """Gibt alle verfügbaren Magie-Kombinationen zurück"""
        combinations = []
        for elements, effect in self.magic_effects.items():
            element_names = " + ".join([e.value for e in elements])
            combinations.append(f"{element_names} = {effect.name}")
        
        return combinations
    
    def update_projectiles(self, dt: float, targets: List[Any] = None):
        """Aktualisiert alle aktiven Projektile"""        
        # Update alle Projektile
        for projectile in self.projectiles:
            projectile.update(dt, targets)
        
        # Entferne tote Projektile
        old_count = len(self.projectiles)
        dead_projectiles = [p for p in self.projectiles if not p.is_alive]
        for projectile in dead_projectiles:
            self.projectiles.remove(projectile)
