# -*- coding: utf-8 -*-
"""
Health Bar Component - OOP Health Display System

Wiederverwendbare Health-Bar Komponente für alle CombatEntity-Objekte.
Implementiert nach OOP Best Practices für einfache Erweiterung und Wartung.
"""

import pygame
from typing import Optional, Tuple, Union, Any, Dict
from abc import ABC, abstractmethod
from combat_system import CombatEntity


class HealthBarRenderer(ABC):
    """
    Abstract Base Class für verschiedene Health-Bar Rendering-Stile.
    Ermöglicht einfache Erweiterung um verschiedene Designs.
    """
    
    @abstractmethod
    def render(self, surface: pygame.Surface, rect: pygame.Rect, 
               health_percentage: float, **kwargs) -> None:
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
    Moderner Pixel-Art Health-Bar Renderer mit Gradient und mehrstufigem Rahmen.
    Passend zum UI-Design von Inventar, Manabar und Element Mixer.
    """
    
    def __init__(self, 
                 bg_color: Tuple[int, int, int] = (15, 20, 35),
                 border_color: Tuple[int, int, int] = (40, 50, 70),
                 health_color_full: Tuple[int, int, int] = (50, 200, 80),
                 health_color_medium: Tuple[int, int, int] = (220, 180, 50),
                 health_color_low: Tuple[int, int, int] = (200, 50, 50),
                 border_width: int = 1):
        """
        Initialisiert den modernen Health-Bar Renderer.
        
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
        
        # Moderne Farben für Rahmen (wie andere UI-Elemente)
        self.border_outer = (25, 30, 50)
        self.border_inner = (60, 80, 120)
    
    def get_health_color(self, health_percentage: float) -> Tuple[int, int, int]:
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
    
    def get_health_gradient(self, health_percentage: float) -> Tuple[Tuple[int, int, int], Tuple[int, int, int]]:
        """Gibt Gradient-Farben für die Health-Füllung zurück."""
        base = self.get_health_color(health_percentage)
        # Hellere Version für oben
        bright = tuple(min(255, c + 60) for c in base)
        # Dunklere Version für unten
        dark = tuple(max(0, c - 30) for c in base)
        return (bright, dark)
    
    def render(self, surface: pygame.Surface, rect: pygame.Rect, 
               health_percentage: float, **kwargs) -> None:
        """
        Rendert eine moderne Pixel-Art Health-Bar mit Gradient und Rahmen.
        
        Args:
            surface: Pygame Surface zum Zeichnen
            rect: Rechteck für die Health-Bar Position und Größe
            health_percentage: Gesundheit als Prozentwert (0.0 - 1.0)
            **kwargs: Zusätzliche Parameter (wird ignoriert)
        """
        x, y, w, h = rect.x, rect.y, rect.width, rect.height
        
        # Äußerer Rahmen (dunkel)
        pygame.draw.rect(surface, self.border_outer, (x-1, y-1, w+2, h+2))
        
        # Hintergrund mit Gradient
        for row in range(h):
            ratio = row / max(1, h)
            r = int(self.bg_color[0] * (1 - ratio * 0.3))
            g = int(self.bg_color[1] * (1 - ratio * 0.3))
            b = int(self.bg_color[2] * (1 - ratio * 0.3))
            pygame.draw.line(surface, (r, g, b), (x, y + row), (x + w - 1, y + row))
        
        # Gesundheitsbalken mit Gradient (falls Gesundheit > 0)
        if health_percentage > 0:
            health_width = max(1, int(w * health_percentage))
            bright, dark = self.get_health_gradient(health_percentage)
            
            for row in range(h):
                ratio = row / max(1, h)
                r = int(bright[0] * (1 - ratio) + dark[0] * ratio)
                g = int(bright[1] * (1 - ratio) + dark[1] * ratio)
                b = int(bright[2] * (1 - ratio) + dark[2] * ratio)
                pygame.draw.line(surface, (r, g, b), (x, y + row), (x + health_width - 1, y + row))
            
            # Highlight-Linie oben
            highlight = tuple(min(255, c + 40) for c in bright)
            pygame.draw.line(surface, highlight, (x, y), (x + health_width - 1, y))
        
        # Innerer Rahmen (heller)
        pygame.draw.rect(surface, self.border_inner, rect, 1)


class AnimatedHealthBarRenderer(StandardHealthBarRenderer):
    """
    Erweiterte Health-Bar mit Animationen für Schaden/Heilung.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.previous_health = 1.0
        self.animation_speed = 0.02  # Geschwindigkeit der Animation
        self.displayed_health = 1.0  # Aktuell angezeigte Gesundheit (für Animation)
    
    def render(self, surface: pygame.Surface, rect: pygame.Rect, 
               health_percentage: float, animate: bool = True, **kwargs) -> None:
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
        super().render(surface, rect, display_percentage, **kwargs)


class HealthBar:
    """
    Hauptklasse für Health-Bar Management.
    Verbindet CombatEntity-Objekte mit Health-Bar Renderern.
    """
    
    def __init__(self, 
                 entity: CombatEntity,
                 width: int = None,
                 height: int = None,
                 offset_x: int = 0,
                 offset_y: int = -15,
                 renderer: Optional[HealthBarRenderer] = None,
                 show_when_full: bool = False,
                 fade_delay: float = 3.0):
        """
        Initialisiert eine Health-Bar für eine CombatEntity mit 7-Zoll Display-Optimierung.
        
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
        
        # Größe basierend auf UI-Settings anpassen
        try:
            from core.config import config
            ui_settings = config.ui.get_ui_settings()
            
            # Standard-Größen basierend auf UI-Skalierung
            if width is None:
                self.width = ui_settings.get('HEALTH_BAR_WIDTH', 60)
            else:
                self.width = width
                
            if height is None:
                self.height = ui_settings.get('HEALTH_BAR_HEIGHT', 8)
            else:
                self.height = height
        except ImportError:
            # Fallback wenn config nicht verfügbar
            self.width = width if width is not None else 60
            self.height = height if height is not None else 8
        
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
    
    def update(self, dt: float) -> None:
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
    
    def get_health_percentage(self) -> float:
        """
        Berechnet den Gesundheitsprozentwert der Entity.
        
        Returns:
            float: Gesundheit als Prozentwert (0.0 - 1.0)
        """
        max_health = self.entity.get_max_health()
        current_health = self.entity.get_health()
        
        if max_health <= 0:
            return 0.0
        
        return max(0.0, min(1.0, current_health / max_health))
    
    def get_position(self) -> Tuple[int, int]:
        """
        Berechnet die Position der Health-Bar basierend auf der Entity-Position.
        
        Returns:
            Tuple[int, int]: (x, y) Position der Health-Bar
        """
        entity_pos = self.entity.get_position()
        x = entity_pos[0] + self.offset_x - self.width // 2
        y = entity_pos[1] + self.offset_y
        return (x, y)
    
    def draw(self, surface: pygame.Surface, camera_offset: Tuple[int, int] = (0, 0)) -> None:
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


class HealthBarManager:
    """
    Manager-Klasse für mehrere Health-Bars.
    Verwaltet Health-Bars für alle Entitäten in einem Level.
    """
    
    def __init__(self):
        """Initialisiert den Health-Bar Manager."""
        self.health_bars: Dict[Any, HealthBar] = {}
        self.default_renderer = StandardHealthBarRenderer()
        # Spieler-Renderer erbt jetzt das moderne Design von StandardHealthBarRenderer
        self.player_renderer = AnimatedHealthBarRenderer()
    
    def add_entity(self, entity: CombatEntity, 
                   renderer: Optional[HealthBarRenderer] = None,
                   **health_bar_kwargs) -> HealthBar:
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
    
    def remove_entity(self, entity: CombatEntity) -> None:
        """
        Entfernt eine Entity aus dem Health-Bar System.
        
        Args:
            entity: Die Entity die entfernt werden soll
        """
        if entity in self.health_bars:
            del self.health_bars[entity]
    
    def update(self, dt: float) -> None:
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
    
    def draw_all(self, surface: pygame.Surface, camera_offset: Tuple[int, int] = (0, 0)) -> None:
        """
        Zeichnet alle Health-Bars.
        
        Args:
            surface: Pygame Surface zum Zeichnen
            camera_offset: Kamera-Offset für Scroll-Effekte
        """
        for health_bar in self.health_bars.values():
            health_bar.draw(surface, camera_offset)
    
    def get_health_bar(self, entity: CombatEntity) -> Optional[HealthBar]:
        """
        Holt die Health-Bar für eine spezifische Entity.
        
        Args:
            entity: Die Entity deren Health-Bar gesucht wird
            
        Returns:
            Optional[HealthBar]: Die Health-Bar oder None falls nicht gefunden
        """
        return self.health_bars.get(entity)


# Convenience-Funktionen für einfache Verwendung
def create_player_health_bar(player: CombatEntity, **kwargs) -> HealthBar:
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


def create_enemy_health_bar(enemy: CombatEntity, **kwargs) -> HealthBar:
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
