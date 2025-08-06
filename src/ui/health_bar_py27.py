# -*- coding: utf-8 -*-
"""
Health Bar Component - OOP Health Display System (Python 2.7 Compatible)

Wiederverwendbare Health-Bar Komponente für alle CombatEntity-Objekte.
Implementiert nach OOP Best Practices für einfache Erweiterung und Wartung.
"""

import pygame
from abc import ABCMeta, abstractmethod


class HealthBarRenderer(object):
    """
    Abstract Base Class für verschiedene Health-Bar Rendering-Stile.
    Ermöglicht einfache Erweiterung um verschiedene Designs.
    """
    __metaclass__ = ABCMeta
    
    @abstractmethod
    def render(self, surface, rect, health_percentage, **kwargs):
        """
        Rendert die Health-Bar auf die gegebene Surface.
        
        Args:
            surface: Pygame Surface zum Zeichnen
            rect: Rechteck für die Health-Bar Position und Größe
            health_percentage: Gesundheit als Prozentwert (0.0 - 1.0)
            **kwargs: Zusätzliche Rendering-Parameter
        """
        pass


class StandardHealthBarRenderer(HealthBarRenderer):
    """
    Standard Health-Bar Renderer mit konfigurierbaren Farben und Stil.
    """
    
    def __init__(self, 
                 bg_color=(60, 60, 60),
                 border_color=(20, 20, 20),
                 health_color_full=(0, 255, 0),
                 health_color_medium=(255, 255, 0),
                 health_color_low=(255, 0, 0),
                 border_width=2):
        """
        Initialisiert den Standard Health-Bar Renderer.
        
        Args:
            bg_color: Hintergrundfarbe der Health-Bar
            border_color: Rahmenfarbe
            health_color_full: Farbe bei voller Gesundheit (>60%)
            health_color_medium: Farbe bei mittlerer Gesundheit (30-60%)
            health_color_low: Farbe bei niedriger Gesundheit (<30%)
            border_width: Breite des Rahmens in Pixeln
        """
        self.bg_color = bg_color
        self.border_color = border_color
        self.health_color_full = health_color_full
        self.health_color_medium = health_color_medium
        self.health_color_low = health_color_low
        self.border_width = border_width
    
    def get_health_color(self, health_percentage):
        """
        Bestimmt die Farbe basierend auf dem Gesundheitsprozentwert.
        
        Args:
            health_percentage: Gesundheit als Prozentwert (0.0 - 1.0)
            
        Returns:
            RGB-Tuple der entsprechenden Farbe
        """
        if health_percentage > 0.6:
            return self.health_color_full
        elif health_percentage > 0.3:
            return self.health_color_medium
        else:
            return self.health_color_low
    
    def render(self, surface, rect, health_percentage, **kwargs):
        """
        Rendert eine Standard Health-Bar mit Rahmen und farbiger Füllung.
        
        Args:
            surface: Pygame Surface zum Zeichnen
            rect: Rechteck für die Health-Bar Position und Größe
            health_percentage: Gesundheit als Prozentwert (0.0 - 1.0)
            **kwargs: Zusätzliche Parameter (wird ignoriert)
        """
        # Rahmen zeichnen
        pygame.draw.rect(surface, self.border_color, rect, self.border_width)
        
        # Hintergrund zeichnen
        inner_rect = rect.inflate(-self.border_width * 2, -self.border_width * 2)
        pygame.draw.rect(surface, self.bg_color, inner_rect)
        
        # Gesundheitsbalken zeichnen (falls Gesundheit > 0)
        if health_percentage > 0:
            health_width = int(inner_rect.width * health_percentage)
            health_rect = pygame.Rect(inner_rect.x, inner_rect.y, 
                                    health_width, inner_rect.height)
            health_color = self.get_health_color(health_percentage)
            pygame.draw.rect(surface, health_color, health_rect)


class AnimatedHealthBarRenderer(StandardHealthBarRenderer):
    """
    Erweiterte Health-Bar mit Animationen für Schaden/Heilung.
    """
    
    def __init__(self, *args, **kwargs):
        super(AnimatedHealthBarRenderer, self).__init__(*args, **kwargs)
        self.previous_health = 1.0
        self.animation_speed = 0.02  # Geschwindigkeit der Animation
        self.displayed_health = 1.0  # Aktuell angezeigte Gesundheit (für Animation)
    
    def render(self, surface, rect, health_percentage, animate=True, **kwargs):
        """
        Rendert eine animierte Health-Bar.
        
        Args:
            surface: Pygame Surface zum Zeichnen
            rect: Rechteck für die Health-Bar Position und Größe
            health_percentage: Gesundheit als Prozentwert (0.0 - 1.0)
            animate: Ob Animation verwendet werden soll
            **kwargs: Zusätzliche Parameter
        """
        if animate:
            # Animiere zur neuen Gesundheit
            if abs(self.displayed_health - health_percentage) > 0.001:
                if self.displayed_health < health_percentage:
                    # Heilung - schnell nach oben
                    self.displayed_health = min(health_percentage, 
                                              self.displayed_health + self.animation_speed * 2)
                else:
                    # Schaden - langsam nach unten
                    self.displayed_health = max(health_percentage, 
                                              self.displayed_health - self.animation_speed)
            
            display_percentage = self.displayed_health
        else:
            display_percentage = health_percentage
            self.displayed_health = health_percentage
        
        # Verwende den Standard-Renderer mit der angezeigten Gesundheit
        super(AnimatedHealthBarRenderer, self).render(surface, rect, display_percentage, **kwargs)


class HealthBar(object):
    """
    Hauptklasse für Health-Bar Management.
    Verbindet CombatEntity-Objekte mit Health-Bar Renderern.
    """
    
    def __init__(self, 
                 entity,
                 width=60,
                 height=8,
                 offset_x=0,
                 offset_y=-15,
                 renderer=None,
                 show_when_full=False,
                 fade_delay=3.0):
        """
        Initialisiert eine Health-Bar für eine CombatEntity.
        
        Args:
            entity: Das CombatEntity-Objekt (Player, Enemy, etc.)
            width: Breite der Health-Bar in Pixeln
            height: Höhe der Health-Bar in Pixeln
            offset_x: X-Offset relativ zur Entity-Position
            offset_y: Y-Offset relativ zur Entity-Position (negativ = über dem Kopf)
            renderer: Health-Bar Renderer (Standard falls None)
            show_when_full: Ob die Bar auch bei voller Gesundheit gezeigt werden soll
            fade_delay: Zeit in Sekunden bevor die Bar ausgeblendet wird
        """
        self.entity = entity
        self.width = width
        self.height = height
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.show_when_full = show_when_full
        self.fade_delay = fade_delay
        
        # Renderer setzen (Standard falls nicht angegeben)
        self.renderer = renderer if renderer else StandardHealthBarRenderer()
        
        # State-Management
        self.visible = True
        self.last_damage_time = 0
        self.alpha = 255  # Transparenz für Fade-Effekt
        
        # Temporäre Surface für Transparenz-Effekte
        self._temp_surface = pygame.Surface((width, height), pygame.SRCALPHA)
    
    def update(self, dt):
        """
        Aktualisiert die Health-Bar (für Animationen und Fade-Effekte).
        
        Args:
            dt: Delta-Time in Sekunden
        """
        if not self.entity.is_alive():
            self.visible = False
            return
        
        current_health_percentage = self.get_health_percentage()
        
        # Prüfe ob Health-Bar sichtbar sein soll
        if not self.show_when_full and current_health_percentage >= 1.0:
            # Fade out wenn bei voller Gesundheit und nicht immer sichtbar
            current_time = pygame.time.get_ticks() / 1000.0
            if current_time - self.last_damage_time > self.fade_delay:
                self.alpha = max(0, self.alpha - 255 * dt * 2)  # 2 Sekunden Fade
                if self.alpha <= 0:
                    self.visible = False
            else:
                self.alpha = 255
                self.visible = True
        else:
            # Immer sichtbar wenn nicht bei voller Gesundheit
            self.alpha = 255
            self.visible = True
            self.last_damage_time = pygame.time.get_ticks() / 1000.0
    
    def get_health_percentage(self):
        """
        Berechnet den Gesundheitsprozentwert der Entity.
        
        Returns:
            float: Gesundheit als Prozentwert (0.0 - 1.0)
        """
        max_health = self.entity.get_max_health()
        current_health = self.entity.get_health()
        
        if max_health <= 0:
            return 0.0
        
        return max(0.0, min(1.0, float(current_health) / float(max_health)))
    
    def get_position(self):
        """
        Berechnet die Position der Health-Bar basierend auf der Entity-Position.
        
        Returns:
            tuple: (x, y) Position der Health-Bar
        """
        entity_pos = self.entity.get_position()
        x = entity_pos[0] + self.offset_x - self.width // 2
        y = entity_pos[1] + self.offset_y
        return (x, y)
    
    def draw(self, surface, camera_offset=(0, 0)):
        """
        Zeichnet die Health-Bar auf die gegebene Surface.
        
        Args:
            surface: Pygame Surface zum Zeichnen
            camera_offset: Kamera-Offset für Scroll-Effekte (x, y)
        """
        if not self.visible or self.alpha <= 0:
            return
        
        # Position berechnen (mit Kamera-Offset)
        pos = self.get_position()
        x = pos[0] - camera_offset[0]
        y = pos[1] - camera_offset[1]
        
        # Prüfe ob Health-Bar im sichtbaren Bereich ist
        if (x + self.width < 0 or x > surface.get_width() or 
            y + self.height < 0 or y > surface.get_height()):
            return
        
        # Health-Bar Rechteck
        health_bar_rect = pygame.Rect(x, y, self.width, self.height)
        
        # Gesundheitsprozentwert
        health_percentage = self.get_health_percentage()
        
        # Auf temporäre Surface rendern für Transparenz
        self._temp_surface.fill((0, 0, 0, 0))  # Transparent
        
        # Renderer aufrufen
        self.renderer.render(self._temp_surface, 
                           pygame.Rect(0, 0, self.width, self.height),
                           health_percentage)
        
        # Transparenz anwenden und auf Haupt-Surface zeichnen
        if self.alpha < 255:
            self._temp_surface.set_alpha(int(self.alpha))
        
        surface.blit(self._temp_surface, (x, y))


class HealthBarManager(object):
    """
    Manager-Klasse für mehrere Health-Bars.
    Verwaltet Health-Bars für alle Entitäten in einem Level.
    """
    
    def __init__(self):
        """Initialisiert den Health-Bar Manager."""
        self.health_bars = {}
        self.default_renderer = StandardHealthBarRenderer()
        self.player_renderer = AnimatedHealthBarRenderer(
            health_color_full=(0, 200, 255),  # Blau für Spieler
            health_color_medium=(255, 200, 0),
            health_color_low=(255, 100, 100)
        )
    
    def add_entity(self, entity, renderer=None, **health_bar_kwargs):
        """
        Fügt eine Entity zum Health-Bar System hinzu.
        
        Args:
            entity: Die CombatEntity die eine Health-Bar bekommen soll
            renderer: Spezifischer Renderer für diese Entity
            **health_bar_kwargs: Zusätzliche Parameter für die HealthBar
            
        Returns:
            HealthBar: Die erstellte Health-Bar Instanz
        """
        # Spezielle Renderer für verschiedene Entity-Typen
        if renderer is None:
            # Prüfe Entity-Typ für automatischen Renderer
            entity_type = type(entity).__name__.lower()
            if 'player' in entity_type:
                renderer = self.player_renderer
            else:
                renderer = self.default_renderer
        
        # Health-Bar erstellen
        health_bar = HealthBar(entity, renderer=renderer, **health_bar_kwargs)
        self.health_bars[entity] = health_bar
        
        return health_bar
    
    def remove_entity(self, entity):
        """
        Entfernt eine Entity aus dem Health-Bar System.
        
        Args:
            entity: Die Entity die entfernt werden soll
        """
        if entity in self.health_bars:
            del self.health_bars[entity]
    
    def update(self, dt):
        """
        Aktualisiert alle Health-Bars.
        
        Args:
            dt: Delta-Time in Sekunden
        """
        # Liste für Entitäten die entfernt werden sollen
        to_remove = []
        
        for entity, health_bar in self.health_bars.items():
            if not entity.is_alive():
                to_remove.append(entity)
            else:
                health_bar.update(dt)
        
        # Tote Entitäten entfernen
        for entity in to_remove:
            self.remove_entity(entity)
    
    def draw_all(self, surface, camera_offset=(0, 0)):
        """
        Zeichnet alle Health-Bars.
        
        Args:
            surface: Pygame Surface zum Zeichnen
            camera_offset: Kamera-Offset für Scroll-Effekte
        """
        for health_bar in self.health_bars.values():
            health_bar.draw(surface, camera_offset)
    
    def get_health_bar(self, entity):
        """
        Holt die Health-Bar für eine spezifische Entity.
        
        Args:
            entity: Die Entity deren Health-Bar gesucht wird
            
        Returns:
            HealthBar or None: Die Health-Bar oder None falls nicht gefunden
        """
        return self.health_bars.get(entity)
    
    def reset(self):
        """
        Setzt den Health-Bar Manager zurück (für Game Over / Neustart).
        Entfernt alle Health-Bars.
        """
        self.health_bars.clear()
        print("🔄 Health-Bar System zurückgesetzt")


# Convenience-Funktionen für einfache Verwendung
def create_player_health_bar(player, **kwargs):
    """
    Erstellt eine optimierte Health-Bar für den Spieler.
    
    Args:
        player: Player-Entity
        **kwargs: Zusätzliche HealthBar-Parameter
        
    Returns:
        HealthBar: Konfigurierte Player Health-Bar
    """
    renderer = AnimatedHealthBarRenderer(
        health_color_full=(0, 200, 255),  # Blau
        health_color_medium=(255, 200, 0),  # Gelb  
        health_color_low=(255, 100, 100),   # Rot
        border_width=3
    )
    
    defaults = {
        'width': 80,
        'height': 12,
        'offset_y': -25,
        'show_when_full': True,  # Spieler Health-Bar immer sichtbar
        'renderer': renderer
    }
    defaults.update(kwargs)
    
    return HealthBar(player, **defaults)


def create_enemy_health_bar(enemy, **kwargs):
    """
    Erstellt eine Health-Bar für Feinde.
    
    Args:
        enemy: Enemy-Entity  
        **kwargs: Zusätzliche HealthBar-Parameter
        
    Returns:
        HealthBar: Konfigurierte Enemy Health-Bar
    """
    renderer = StandardHealthBarRenderer(
        health_color_full=(255, 0, 0),     # Rot
        health_color_medium=(255, 100, 0), # Orange
        health_color_low=(150, 0, 0),      # Dunkelrot
        border_width=2
    )
    
    defaults = {
        'width': 50,
        'height': 6,
        'offset_y': -20,
        'show_when_full': False,  # Nur bei Schaden sichtbar
        'fade_delay': 2.0,
        'renderer': renderer
    }
    defaults.update(kwargs)
    
    return HealthBar(enemy, **defaults)
