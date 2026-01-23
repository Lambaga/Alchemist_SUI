# -*- coding: utf-8 -*-
"""
GIF Overlay - Spielt animierte GIFs als Overlay ab
Easter Egg System für Alchemist_SUI
"""

import pygame
import os
from typing import List, Optional, Tuple
from PIL import Image


class GifOverlay:
    """Spielt ein animiertes GIF als Vollbild-Overlay ab."""
    
    def __init__(self, screen_size: Tuple[int, int]):
        self.screen_width, self.screen_height = screen_size
        self.frames: List[pygame.Surface] = []
        self.frame_durations: List[int] = []  # ms pro Frame
        self.current_frame = 0
        self.frame_timer = 0
        self.is_playing = False
        self.gif_loaded = False
        self.loop = False  # Einmal abspielen
        
        # Overlay-Hintergrund (semi-transparent)
        self.overlay_bg = pygame.Surface((self.screen_width, self.screen_height))
        self.overlay_bg.fill((0, 0, 0))
        self.overlay_bg.set_alpha(200)
    
    def load_gif(self, gif_path: str, scale_to_fit: bool = True) -> bool:
        """
        Lädt ein GIF und konvertiert es zu Pygame Surfaces.
        
        Args:
            gif_path: Pfad zur GIF-Datei
            scale_to_fit: Skaliere auf Bildschirmgröße
            
        Returns:
            True wenn erfolgreich geladen
        """
        try:
            if not os.path.exists(gif_path):
                print(f"⚠️ GIF nicht gefunden: {gif_path}")
                return False
            
            # GIF mit Pillow laden
            gif = Image.open(gif_path)
            
            self.frames = []
            self.frame_durations = []
            
            # Alle Frames extrahieren
            frame_count = 0
            try:
                while True:
                    # Frame zu RGB konvertieren
                    frame = gif.convert("RGBA")
                    
                    # Frame-Dauer holen (in ms, default 100ms)
                    duration = gif.info.get('duration', 100)
                    if duration == 0:
                        duration = 100
                    
                    # Zu Pygame Surface konvertieren
                    frame_data = frame.tobytes()
                    pygame_surface = pygame.image.fromstring(
                        frame_data, frame.size, "RGBA"
                    ).convert_alpha()
                    
                    # Optional skalieren
                    if scale_to_fit:
                        # Behalte Aspect Ratio, passe an Bildschirm an
                        img_w, img_h = frame.size
                        scale_w = self.screen_width / img_w
                        scale_h = self.screen_height / img_h
                        scale = min(scale_w, scale_h) * 0.5  # 50% der Bildschirmgröße (kleiner!)
                        
                        new_w = int(img_w * scale)
                        new_h = int(img_h * scale)
                        pygame_surface = pygame.transform.smoothscale(
                            pygame_surface, (new_w, new_h)
                        )
                    
                    self.frames.append(pygame_surface)
                    self.frame_durations.append(duration)
                    
                    frame_count += 1
                    gif.seek(gif.tell() + 1)
                    
            except EOFError:
                pass  # Ende des GIFs erreicht
            
            self.gif_loaded = len(self.frames) > 0
            print(f"🎬 GIF geladen: {frame_count} Frames")
            return self.gif_loaded
            
        except Exception as e:
            print(f"❌ Fehler beim Laden des GIFs: {e}")
            return False
    
    def play(self, loop: bool = False):
        """Startet die GIF-Wiedergabe."""
        if not self.gif_loaded:
            return
        
        self.is_playing = True
        self.current_frame = 0
        self.frame_timer = 0
        self.loop = loop
        print("▶️ GIF-Overlay gestartet!")
    
    def stop(self):
        """Stoppt die GIF-Wiedergabe."""
        self.is_playing = False
        self.current_frame = 0
        self.frame_timer = 0
    
    def update(self, dt: float):
        """
        Aktualisiert die Animation.
        
        Args:
            dt: Delta-Zeit in Sekunden
        """
        if not self.is_playing or not self.gif_loaded:
            return
        
        # Timer in Millisekunden
        self.frame_timer += dt * 1000
        
        # Nächster Frame?
        if self.frame_timer >= self.frame_durations[self.current_frame]:
            self.frame_timer = 0
            self.current_frame += 1
            
            # Ende erreicht?
            if self.current_frame >= len(self.frames):
                if self.loop:
                    self.current_frame = 0
                else:
                    self.stop()
    
    def render(self, screen: pygame.Surface):
        """
        Zeichnet das GIF-Overlay.
        
        Args:
            screen: Pygame Surface zum Zeichnen
        """
        if not self.is_playing or not self.gif_loaded:
            return
        
        # Aktuelle Screen-Größe verwenden (falls anders als initialisiert)
        screen_w, screen_h = screen.get_size()
        
        # Dunkler Hintergrund (auf volle Screengröße)
        overlay = pygame.Surface((screen_w, screen_h))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(200)
        screen.blit(overlay, (0, 0))
        
        # Aktuelles Frame zentriert zeichnen
        frame = self.frames[self.current_frame]
        frame_rect = frame.get_rect()
        frame_rect.center = (screen_w // 2, screen_h // 2)
        screen.blit(frame, frame_rect)
        
        # Optional: "Drücke ESC" Text
        try:
            font = pygame.font.Font(None, 24)
            hint = font.render("Drücke ESC zum Überspringen", True, (200, 200, 200))
            hint_rect = hint.get_rect()
            hint_rect.midbottom = (screen_w // 2, screen_h - 20)
            screen.blit(hint, hint_rect)
        except:
            pass
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Verarbeitet Events während der Wiedergabe.
        
        Args:
            event: Pygame Event
            
        Returns:
            True wenn Event konsumiert wurde
        """
        if not self.is_playing:
            return False
        
        # ESC oder Space zum Überspringen
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_SPACE, pygame.K_RETURN):
                self.stop()
                return True
        
        # Mausklick zum Überspringen
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.stop()
            return True
        
        return False


class EasterEggSequence:
    """Erkennt Easter Egg Tastenkombinationen."""
    
    # Sequenz: 3x Wasser, 2x Feuer (schnell hintereinander)
    ISHOWSPEED_SEQUENCE = ["water", "water", "water", "fire", "fire"]
    SEQUENCE_TIMEOUT = 3.0  # Sekunden für die gesamte Sequenz
    
    def __init__(self):
        self.input_history: List[Tuple[str, float]] = []  # (element, timestamp)
        self.triggered_easter_egg: Optional[str] = None
    
    def add_input(self, element_id: str) -> Optional[str]:
        """
        Fügt eine Eingabe hinzu und prüft auf Easter Eggs.
        
        Args:
            element_id: Element-ID ("water", "fire", "stone")
            
        Returns:
            Easter Egg ID wenn ausgelöst, sonst None
        """
        import time
        current_time = time.time()
        
        # Alte Eingaben entfernen (außerhalb des Timeout)
        self.input_history = [
            (elem, ts) for elem, ts in self.input_history
            if current_time - ts < self.SEQUENCE_TIMEOUT
        ]
        
        # Neue Eingabe hinzufügen
        self.input_history.append((element_id, current_time))
        
        # Prüfe auf ishowspeed Sequenz
        if self._check_sequence(self.ISHOWSPEED_SEQUENCE):
            self.input_history = []  # Reset
            print("🚀 EASTER EGG: IShowSpeed aktiviert!")
            return "ishowspeed"
        
        return None
    
    def _check_sequence(self, target_sequence: List[str]) -> bool:
        """Prüft ob die letzten Eingaben der Zielsequenz entsprechen."""
        if len(self.input_history) < len(target_sequence):
            return False
        
        # Letzte N Eingaben prüfen
        recent = [elem for elem, ts in self.input_history[-len(target_sequence):]]
        return recent == target_sequence
    
    def reset(self):
        """Setzt die Eingabe-Historie zurück."""
        self.input_history = []
