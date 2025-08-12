# -*- coding: utf-8 -*-
"""
FPS Monitor System für Performance-Tracking

Zeigt FPS, Frame-Times und Performance-Metriken in Echtzeit an.
Hilft bei der Identifikation von Performance-Bottlenecks und Frame-Drops.
"""

import pygame
from typing import List, Tuple, Optional, Dict, Any
import time
from collections import deque


class FPSMonitor:
    """
    Erweiterte FPS-Anzeige mit Performance-Metriken und Frame-Drop-Detektion.
    
    Features:
    - Echtzeit FPS-Anzeige
    - Frame-Time Tracking
    - Frame-Drop Detektion
    - Performance-Warnungen
    - Historische Daten für Trends
    
    Attributes:
        position (Tuple[int, int]): Position des FPS-Displays
        font_size (int): Schriftgröße für die Anzeige
        show_detailed (bool): Ob detaillierte Metriken angezeigt werden sollen
        frame_history (deque): Speicher für Frame-Time Historie
        
    Example:
        >>> fps_monitor = FPSMonitor(position=(10, 10))
        >>> fps_monitor.update(clock.get_fps(), delta_time)
        >>> fps_monitor.draw(screen)
    """
    
    def __init__(self, position: Tuple[int, int] = None, font_size: int = None, 
                 show_detailed: bool = True, history_size: int = 60) -> None:
        """
        Initialisiert den FPS-Monitor mit 7-Zoll Display-Optimierung.
        
        Args:
            position: Position (x, y) für die Anzeige auf dem Bildschirm
            font_size: Schriftgröße für Text-Anzeige
            show_detailed: Ob erweiterte Metriken angezeigt werden sollen
            history_size: Anzahl der Frame-Times die gespeichert werden
        """
        # Import config für Display-Settings
        try:
            from core.config import config
            ui_settings = config.ui.get_ui_settings()
            display_settings = config.display.get_optimized_settings()
        except ImportError:
            ui_settings = {}
            display_settings = {}
        
        # Position basierend auf Display-Typ
        if position is None:
            self.position = (
                ui_settings.get('FPS_POSITION_X', 10),
                ui_settings.get('FPS_POSITION_Y', 10)
            )
        else:
            self.position = position
        
        # Schriftgröße basierend auf Display-Typ
        if font_size is None:
            if display_settings.get('HOTKEY_DISPLAY_COMPACT', False):
                self.font_size = int(20 * ui_settings.get('UI_SCALE', 1.0))  # 7-Zoll kleiner
            else:
                self.font_size = 24  # Standard
        else:
            self.font_size = font_size
            
        self.show_detailed = show_detailed
        self.history_size = history_size
        self.show_detailed: bool = show_detailed
        self.history_size: int = history_size
        
        # Font für Text-Rendering
        pygame.font.init()
        self.font: pygame.font.Font = pygame.font.Font(None, self.font_size)
        self.small_font: pygame.font.Font = pygame.font.Font(None, self.font_size - 4)
        
        # Performance-Daten
        self.current_fps: float = 0.0
        self.current_frame_time: float = 0.0
        self.frame_history: deque = deque(maxlen=history_size)
        
        # Frame-Drop Detektion
        self.target_fps: float = 60.0
        self.frame_drop_threshold: float = 0.8  # 80% der Ziel-FPS
        self.consecutive_drops: int = 0
        self.max_consecutive_drops: int = 5
        
        # Farben für verschiedene Performance-Levels
        self.colors: Dict[str, Tuple[int, int, int]] = {
            'excellent': (0, 255, 0),      # Grün: > 90% Ziel-FPS
            'good': (255, 255, 0),         # Gelb: 70-90% Ziel-FPS
            'poor': (255, 165, 0),         # Orange: 50-70% Ziel-FPS
            'critical': (255, 0, 0),       # Rot: < 50% Ziel-FPS
            'background': (0, 0, 0, 128),  # Halbtransparenter Hintergrund
            'text': (255, 255, 255)        # Weißer Text
        }
        
        # Update-Timer für weniger häufige Berechnungen
        self.last_detailed_update: float = 0.0
        self.detailed_update_interval: float = 0.1  # 10x pro Sekunde
        
        # Cached Metriken
        self.average_fps: float = 0.0
        self.min_fps: float = 0.0
        self.max_fps: float = 0.0
        self.frame_drops_per_second: float = 0.0
        
    def update(self, fps: float, frame_time: float) -> None:
        """
        Aktualisiert die FPS-Metriken.
        
        Args:
            fps: Aktuelle FPS von pygame.Clock.get_fps()
            frame_time: Frame-Zeit in Sekunden (Delta-Time)
        """
        self.current_fps = fps
        self.current_frame_time = frame_time * 1000  # Konvertierung zu Millisekunden
        
        # Frame-Time zur Historie hinzufügen
        self.frame_history.append(frame_time)
        
        # Frame-Drop Detektion
        self._detect_frame_drops()
        
        # Erweiterte Metriken berechnen (weniger häufig für Performance)
        current_time = time.time()
        if current_time - self.last_detailed_update >= self.detailed_update_interval:
            self._calculate_detailed_metrics()
            self.last_detailed_update = current_time
    
    def _detect_frame_drops(self) -> None:
        """Erkennt Frame-Drops basierend auf FPS-Schwellenwerten."""
        threshold_fps = self.target_fps * self.frame_drop_threshold
        
        if self.current_fps < threshold_fps and self.current_fps > 0:
            self.consecutive_drops += 1
        else:
            self.consecutive_drops = 0
    
    def _calculate_detailed_metrics(self) -> None:
        """Berechnet erweiterte Performance-Metriken."""
        if not self.frame_history:
            return
            
        frame_times = list(self.frame_history)
        fps_values = [1.0 / ft for ft in frame_times if ft > 0]
        
        if fps_values:
            self.average_fps = sum(fps_values) / len(fps_values)
            self.min_fps = min(fps_values)
            self.max_fps = max(fps_values)
            
            # Frame-Drops pro Sekunde berechnen
            drops = sum(1 for fps in fps_values if fps < self.target_fps * self.frame_drop_threshold)
            self.frame_drops_per_second = drops / len(fps_values) * self.target_fps
    
    def _get_performance_color(self) -> Tuple[int, int, int]:
        """
        Bestimmt die Farbe basierend auf der Performance.
        
        Returns:
            Tuple[int, int, int]: RGB-Farbwerte
        """
        fps_ratio = self.current_fps / self.target_fps if self.target_fps > 0 else 0
        
        if fps_ratio >= 0.9:
            return self.colors['excellent']
        elif fps_ratio >= 0.7:
            return self.colors['good']
        elif fps_ratio >= 0.5:
            return self.colors['poor']
        else:
            return self.colors['critical']
    
    def _create_background_surface(self, width: int, height: int) -> pygame.Surface:
        """
        Erstellt einen halbtransparenten Hintergrund für bessere Lesbarkeit.
        
        Args:
            width, height: Größe der Hintergrund-Surface
            
        Returns:
            pygame.Surface: Halbtransparente Hintergrund-Surface
        """
        background = pygame.Surface((width, height), pygame.SRCALPHA)
        background.fill(self.colors['background'])
        return background
    
    def draw(self, surface: pygame.Surface) -> None:
        """
        Zeichnet das FPS-Display auf die gegebene Surface.
        
        Args:
            surface: Pygame-Surface zum Zeichnen
        """
        x, y = self.position
        line_height = self.font_size + 2
        current_y = y
        
        # Performance-Farbe bestimmen
        perf_color = self._get_performance_color()
        
        # Texte vorbereiten
        texts = []
        
        # Haupt-FPS Anzeige (immer sichtbar)
        fps_text = f"FPS: {self.current_fps:.1f}"
        texts.append((fps_text, self.font, perf_color))
        
        if self.show_detailed and self.frame_history:
            # Frame-Time
            frame_time_text = f"Frame: {self.current_frame_time:.1f}ms"
            texts.append((frame_time_text, self.small_font, self.colors['text']))
            
            # Durchschnittliche FPS
            avg_text = f"Avg: {self.average_fps:.1f}"
            texts.append((avg_text, self.small_font, self.colors['text']))
            
            # Min/Max FPS
            minmax_text = f"Min/Max: {self.min_fps:.0f}/{self.max_fps:.0f}"
            texts.append((minmax_text, self.small_font, self.colors['text']))
            
            # Frame-Drop Warnung
            if self.consecutive_drops > self.max_consecutive_drops:
                warning_text = f"⚠️ Frame Drops: {self.consecutive_drops}"
                texts.append((warning_text, self.small_font, self.colors['critical']))
        
        # Hintergrund-Größe berechnen
        max_width = max(font.size(text)[0] for text, font, _ in texts)
        total_height = len(texts) * line_height + 10
        
        # Hintergrund zeichnen
        background = self._create_background_surface(max_width + 20, total_height)
        surface.blit(background, (x - 5, y - 5))
        
        # Texte zeichnen
        for text, font, color in texts:
            text_surface = font.render(text, True, color)
            surface.blit(text_surface, (x, current_y))
            current_y += line_height
    
    def set_target_fps(self, target_fps: float) -> None:
        """
        Setzt die Ziel-FPS für Frame-Drop Detektion.
        
        Args:
            target_fps: Gewünschte FPS (normalerweise 60)
        """
        self.target_fps = target_fps
    
    def toggle_detailed(self) -> None:
        """Schaltet die detaillierte Anzeige ein/aus."""
        self.show_detailed = not self.show_detailed
    
    def reset_stats(self) -> None:
        """Setzt alle Statistiken zurück."""
        self.frame_history.clear()
        self.consecutive_drops = 0
        self.average_fps = 0.0
        self.min_fps = 0.0
        self.max_fps = 0.0
        self.frame_drops_per_second = 0.0
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Gibt eine Zusammenfassung der Performance-Daten zurück.
        
        Returns:
            Dict[str, Any]: Performance-Metriken
        """
        return {
            'current_fps': self.current_fps,
            'average_fps': self.average_fps,
            'min_fps': self.min_fps,
            'max_fps': self.max_fps,
            'frame_time_ms': self.current_frame_time,
            'consecutive_drops': self.consecutive_drops,
            'frame_drops_per_second': self.frame_drops_per_second,
            'performance_rating': self._get_performance_rating()
        }
    
    def _get_performance_rating(self) -> str:
        """
        Gibt eine Textbewertung der Performance zurück.
        
        Returns:
            str: Performance-Rating ('Excellent', 'Good', 'Poor', 'Critical')
        """
        fps_ratio = self.current_fps / self.target_fps if self.target_fps > 0 else 0
        
        if fps_ratio >= 0.9:
            return "Excellent"
        elif fps_ratio >= 0.7:
            return "Good"
        elif fps_ratio >= 0.5:
            return "Poor"
        else:
            return "Critical"


# Convenience-Funktionen für einfache Nutzung
def create_simple_fps_display(position: Tuple[int, int] = (10, 10)) -> FPSMonitor:
    """
    Erstellt einen einfachen FPS-Monitor mit Standardeinstellungen.
    
    Args:
        position: Position auf dem Bildschirm
        
    Returns:
        FPSMonitor: Konfigurierter FPS-Monitor
    """
    return FPSMonitor(position=position, show_detailed=False)


def create_detailed_fps_display(position: Tuple[int, int] = (10, 10)) -> FPSMonitor:
    """
    Erstellt einen detaillierten FPS-Monitor mit erweiterten Metriken.
    
    Args:
        position: Position auf dem Bildschirm
        
    Returns:
        FPSMonitor: Konfigurierter FPS-Monitor mit Details
    """
    return FPSMonitor(position=position, show_detailed=True)
