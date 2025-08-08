# -*- coding: utf-8 -*-
"""
Magic System - Elemental Combination System
Implementiert das Magiesystem mit Elementkombinationen für Der Alchemist
"""

import pygame
import math
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

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
    
    def __init__(self, start_x: int, start_y: int, target_x: int, target_y: int, 
                 speed: int = 150, damage: int = 25, element_type: str = "feuer"):  # Langsamere Geschwindigkeit für bessere Sichtbarkeit
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
        self.image = self.create_projectile_sprite(element_type)
        self.rect = self.image.get_rect(center=(start_x, start_y))
        self.hitbox = self.rect.copy()
        
        # Animation
        self.last_update = pygame.time.get_ticks()
        self.animation_speed = 100  # ms
        self.rotation = 0
        
    def create_projectile_sprite(self, element_type: str) -> pygame.Surface:
        """Erstellt animiertes Sprite basierend auf Element-Typ"""
        import math
        size = (80, 80)  # DEUTLICH GRÖßERE Sprites für bessere Sichtbarkeit
        sprite = pygame.Surface(size, pygame.SRCALPHA)
        center = (40, 40)  # Neuer Mittelpunkt
        
        # Basis-Zeit für Animation
        current_time = pygame.time.get_ticks()
        pulse = abs(math.sin(current_time * 0.01)) * 0.3 + 0.7  # Pulsierender Effekt
        
        if element_type == "feuer":
            # Feuerball - Orange/Rot mit Animation - DEUTLICH VERGRÖßERT
            outer_radius = int(35 * pulse)  # Fast verdoppelt
            inner_radius = int(25 * pulse)  # Fast verdoppelt
            core_radius = int(15 * pulse)   # Fast verdoppelt
            pygame.draw.circle(sprite, (255, 50, 0), center, outer_radius)
            pygame.draw.circle(sprite, (255, 200, 0), center, inner_radius)
            pygame.draw.circle(sprite, (255, 255, 100), center, core_radius)
            
        elif element_type == "wasser":
            # Wasserkugel - Blau mit Wellenbewegung - DEUTLICH VERGRÖßERT
            outer_radius = int(35 * pulse)  # Fast verdoppelt
            inner_radius = int(25 * pulse)  # Fast verdoppelt
            core_radius = int(15 * pulse)   # Fast verdoppelt
            pygame.draw.circle(sprite, (0, 50, 255), center, outer_radius)
            pygame.draw.circle(sprite, (100, 150, 255), center, inner_radius)
            pygame.draw.circle(sprite, (200, 230, 255), center, core_radius)
            
        elif element_type == "wirbelattacke":
            # Energiewirbel - Lila mit Rotation - DEUTLICH VERGRÖßERT
            rotation_angle = (current_time * 0.01) % (2 * math.pi)
            center_x, center_y = center
            
            # Mehrere Energiepunkte in kreisender Bewegung - VERGRÖßERT
            for i in range(8):  # Mehr Punkte für besseren Wirbel-Effekt
                angle = rotation_angle + (i * math.pi / 4)
                radius = 30 * pulse  # Deutlich größer
                x = center_x + int(radius * math.cos(angle))
                y = center_y + int(radius * math.sin(angle))
                pygame.draw.circle(sprite, (150 + int(50*pulse), 50, 200), (x, y), 8)  # Größere Punkte
            
            # Zentraler Kern - VERGRÖßERT
            pygame.draw.circle(sprite, (200, 100, 255), center, int(12 * pulse))  # Deutlich größer
            
        return sprite
    
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
            # Sprite neu generieren für Animation
            self.image = self.create_projectile_sprite(self.element_type)
            self.rotation += 15
            if self.rotation >= 360:
                self.rotation = 0
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
        """Behandle Treffer auf Ziel"""
        if hasattr(target, 'take_damage'):
            class_name = target.__class__.__name__.lower() if hasattr(target, '__class__') else ""
            
            if self.element_type == "feuer":
                # Feuerball: 50 Schaden gegen Wasserkreaturen, 10 gegen alle anderen
                if ('water' in class_name or 'wasser' in class_name or 
                    'ice' in class_name or 'eis' in class_name):
                    # Gegen Wasserkreaturen (noch nicht implementiert)
                    damage = 50
                    target.take_damage(damage)
                    if magic_system:
                        magic_system.add_floating_damage(target, damage, "fire")
                    print(f"🔥 Feuerball trifft Wasserkreatur für {damage} Schaden!")
                else:
                    # Gegen alle anderen (Feuerkreaturen, etc.)
                    damage = 10
                    target.take_damage(damage)
                    if magic_system:
                        magic_system.add_floating_damage(target, damage, "fire")
                    print(f"🔥 Feuerball trifft für {damage} Schaden!")
                    
            elif self.element_type == "wasser":
                # Wasserkugel: 50 Schaden gegen Feuerkreaturen, 10 gegen alle anderen  
                if ('fire' in class_name or 'feuer' in class_name or 
                    'fireworm' in class_name or 'demon' in class_name or 
                    'flame' in class_name or 'lava' in class_name):
                    # Gegen Feuerkreaturen (FireWorm UND Demon)
                    damage = 50
                    target.take_damage(damage)
                    if magic_system:
                        magic_system.add_floating_damage(target, damage, "water")
                    print(f"💧 Wasserkugel trifft Feuerkreatur für {damage} Schaden!")
                else:
                    # Gegen alle anderen neutralen Kreaturen
                    damage = 10
                    target.take_damage(damage)
                    if magic_system:
                        magic_system.add_floating_damage(target, damage, "water")
                    print(f"💧 Wasserkugel trifft für {damage} Schaden!")
                    
            else:
                # Andere Projektile verwenden Standard-Schaden
                damage = self.damage
                target.take_damage(damage)
                if magic_system:
                    magic_system.add_floating_damage(target, damage, "normal")
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
        
        self._initialize_magic_effects()
        self._warmup_system()  # Sofortiges Warmup beim Start
    
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
        
        # Mana-Kosten prüfen
        if hasattr(caster, 'spend_mana') and not caster.spend_mana(MANA_SPELL_COST):
            # Optionales Feedback für nicht genug Mana
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
        """Führt den spezifischen Magie-Effekt aus"""
        
        if effect.effect_type == "projectile":
            self._cast_projectile(effect, caster, target_pos)
        
        elif effect.effect_type == "healing":
            self._cast_healing(effect, caster)
        
        elif effect.effect_type == "shield":
            self._cast_shield(effect, caster)
        
        elif effect.effect_type == "area_attack":
            self._cast_area_attack(effect, caster, enemies)
        
        elif effect.effect_type == "invisibility":
            self._cast_invisibility(effect, caster)
    
    def _cast_projectile(self, effect: MagicEffect, caster, target_pos: Optional[Tuple[int, int]]):
        """Erstellt Projektil-Magie"""        
        # Ignoriere target_pos und nutze nur die Blickrichtung des Spielers
        if hasattr(caster, 'facing_right'):
            # Projektil fliegt horizontal in die Blickrichtung
            offset_x = 500 if caster.facing_right else -500  # Weiter für bessere Flugbahn
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
        """Führt Heilung aus"""
        if hasattr(caster, 'current_health') and hasattr(caster, 'max_health'):
            old_health = caster.current_health
            caster.current_health = min(caster.max_health, caster.current_health + effect.healing)
            healed = caster.current_health - old_health
            
            # Floating Damage für Heilung hinzufügen (positiver Wert)
            if healed > 0:
                self.add_floating_damage(caster, healed, "heal")
            
            print(f"💚 Geheilt um {healed} HP! ({caster.current_health}/{caster.max_health})")
    
    def _cast_shield(self, effect: MagicEffect, caster):
        """Aktiviert Schutzschild"""
        current_time = pygame.time.get_ticks()
        self.active_effects["shield"] = {
            "start_time": current_time,
            "duration": effect.duration,
            "target": caster
        }
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
                        enemy.take_damage(effect.damage)
                        # Floating Damage für Area Attack hinzufügen
                        self.add_floating_damage(enemy, effect.damage, "area")
                        hit_enemies.append(enemy)
        
        # Visueller Effekt für Wirbelattacke mit Reichweiten-Anzeige
        self._create_whirlwind_effect(caster_pos, effect.radius)
        
        if hit_enemies:
            print(f"🌪️ Wirbelattacke trifft {len(hit_enemies)} Feinde!")
        else:
            print(f"🌪️ Wirbelattacke ausgeführt - keine Feinde in Reichweite (2 Tiles)")
    
    def _create_whirlwind_effect(self, center_pos, radius):
        """Erstellt visuellen Wirbel-Effekt mit deutlicher Reichweiten-Animation"""
        current_time = pygame.time.get_ticks()
        
        # Erstelle Whirlwind-Effekt mit verbesserter Animation
        whirlwind_effect = {
            "center": center_pos,
            "radius": radius,
            "start_time": current_time,
            "duration": 3000,  # 3 Sekunden Animation für bessere Sichtbarkeit
            "type": "whirlwind"
        }
        
        # Füge Effekt zu aktiven visuellen Effekten hinzu
        if "visual_effects" not in self.active_effects:
            self.active_effects["visual_effects"] = []
        self.active_effects["visual_effects"].append(whirlwind_effect)
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
        """Aktiviert Unsichtbarkeit"""
        current_time = pygame.time.get_ticks()
        self.active_effects["invisibility"] = {
            "start_time": current_time,
            "duration": effect.duration,
            "target": caster
        }
        print(f"👻 Unsichtbarkeit aktiviert für {effect.duration/1000}s!")
    
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
            
            # Font für Schadenszahlen
            font = pygame.font.Font(None, 36)  # Größere Schrift für bessere Lesbarkeit
            
            # Text basierend auf Damage-Typ
            if floating_damage.color == (100, 255, 100):  # Grün = Heilung
                text = f"+{floating_damage.damage}"
            else:  # Schaden
                text = f"-{floating_damage.damage}"
            
            # Text-Surface erstellen
            text_surface = font.render(text, True, floating_damage.color)
            
            # Alpha anwenden für Fade-Out
            if alpha < 255:
                fade_surface = pygame.Surface(text_surface.get_size(), pygame.SRCALPHA)
                fade_surface.set_alpha(alpha)
                fade_surface.blit(text_surface, (0, 0))
                text_surface = fade_surface
            
            # Zentriere den Text über dem Ziel
            text_rect = text_surface.get_rect(center=pos)
            
            # Schwarzer Schatten für bessere Lesbarkeit
            shadow_surface = font.render(text, True, (0, 0, 0))
            if alpha < 255:
                shadow_fade = pygame.Surface(shadow_surface.get_size(), pygame.SRCALPHA)
                shadow_fade.set_alpha(alpha)
                shadow_fade.blit(shadow_surface, (0, 0))
                shadow_surface = shadow_fade
            
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
        
        # Mehrphasige Animation
        import math
        
        # Phase 1: Reichweiten-Ring erscheint (erste 30%)
        if progress < 0.3:
            # Expandierender Ring zur Reichweiten-Anzeige
            current_radius = int(screen_radius * (progress / 0.3))
            alpha = int(200 * (progress / 0.3))
            
            # Deutlicher Reichweiten-Ring
            pygame.draw.circle(screen, (255, 255, 0, alpha), screen_center, current_radius, 4)  # Gelber Ring
            pygame.draw.circle(screen, (255, 150, 0, alpha), screen_center, current_radius, 2)  # Orange Akzent
            
            # Text-Anzeige für Reichweite
            if progress > 0.1:  # Nach kurzer Verzögerung
                font = pygame.font.Font(None, 24)
                text = f"2 Tiles Reichweite"
                text_surface = font.render(text, True, (255, 255, 255))
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
                    pygame.draw.circle(screen, color, screen_center, ring_r, max(1, 4 - i))
            
            # Rotierendes Spiral-Muster
            rotation_angle = phase_progress * 720  # 2 volle Umdrehungen
            spiral_points = []
            
            for angle_step in range(0, 360, 20):  # Alle 20 Grad
                angle = math.radians(angle_step + rotation_angle)
                spiral_radius = screen_radius * 0.8
                x = screen_center[0] + int(math.cos(angle) * spiral_radius)
                y = screen_center[1] + int(math.sin(angle) * spiral_radius)
                
                # Zeichne Wirbel-Punkte
                pygame.draw.circle(screen, (255, 255, 150), (x, y), 3)
        
        # Phase 3: Ausklang-Effekt (70% - 100%)
        else:
            fade_progress = (progress - 0.7) / 0.3  # 0.0 bis 1.0
            alpha = int(150 * (1.0 - fade_progress))
            
            # Schrumpfender Ring
            final_radius = int(screen_radius * (1.0 - fade_progress))
            if final_radius > 0 and alpha > 0:
                pygame.draw.circle(screen, (255, 200, 0, alpha), screen_center, final_radius, 3)
                
                # Funkelnde Partikel-Effekte
                import random
                for _ in range(int(10 * (1.0 - fade_progress))):
                    angle = random.random() * 2 * math.pi
                    distance = random.randint(final_radius // 2, final_radius)
                    px = screen_center[0] + int(math.cos(angle) * distance)
                    py = screen_center[1] + int(math.sin(angle) * distance)
                    pygame.draw.circle(screen, (255, 255, 255, alpha), (px, py), 2)
        
        # Immer sichtbare Reichweiten-Markierung (schwach)
        if screen_radius > 0:
            pygame.draw.circle(screen, (100, 100, 100, 60), screen_center, screen_radius, 1)
    
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
