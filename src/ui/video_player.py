# -*- coding: utf-8 -*-
"""
Video Player - Spielt MP4-Videos als Cinematic ab
Verwendet OpenCV für Video-Dekodierung und Pygame für Rendering
"""

import pygame
import os
from typing import Optional, Tuple

# OpenCV Import (wird für MP4 benötigt)
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("⚠️ OpenCV nicht installiert - pip install opencv-python")


class VideoPlayer:
    """Spielt ein MP4-Video als Vollbild-Cinematic ab."""
    
    def __init__(self, screen_size: Tuple[int, int], scale_factor: float = 0.85):
        self.screen_width, self.screen_height = screen_size
        self.scale_factor = scale_factor  # Video auf 85% skalieren damit alles passt
        self.video_path: Optional[str] = None
        self.video_capture = None
        self.is_playing = False
        self.video_loaded = False
        self.fps = 30
        self.frame_duration = 1.0 / 30  # Sekunden pro Frame
        self.frame_timer = 0.0
        self.current_frame: Optional[pygame.Surface] = None
        self.skip_enabled = True
        
        # Audio (optional - wird separat gehandhabt falls vorhanden)
        self.audio_path: Optional[str] = None
        self._music_was_playing = False  # Merken ob Musik lief
        
    def load_video(self, video_path: str, audio_path: Optional[str] = None) -> bool:
        """
        Lädt ein MP4-Video.
        
        Args:
            video_path: Pfad zur MP4-Datei
            audio_path: Optionaler Pfad zur Audio-Datei (MP3/WAV)
            
        Returns:
            True wenn erfolgreich geladen
        """
        if not CV2_AVAILABLE:
            print("❌ OpenCV nicht verfügbar - kann Video nicht laden")
            return False
        
        if not os.path.exists(video_path):
            print(f"⚠️ Video nicht gefunden: {video_path}")
            return False
        
        try:
            self.video_capture = cv2.VideoCapture(video_path)
            
            if not self.video_capture.isOpened():
                print(f"❌ Konnte Video nicht öffnen: {video_path}")
                return False
            
            # Video-Eigenschaften auslesen
            self.fps = self.video_capture.get(cv2.CAP_PROP_FPS)
            if self.fps <= 0:
                self.fps = 30  # Fallback
            self.frame_duration = 1.0 / self.fps
            
            self.video_width = int(self.video_capture.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.video_height = int(self.video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self.total_frames = int(self.video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
            self.duration = self.total_frames / self.fps
            
            self.video_path = video_path
            self.audio_path = audio_path
            self.video_loaded = True
            
            print(f"🎬 Video geladen: {os.path.basename(video_path)}")
            print(f"   Auflösung: {self.video_width}x{self.video_height}")
            print(f"   FPS: {self.fps:.1f}, Dauer: {self.duration:.1f}s")
            
            return True
            
        except Exception as e:
            print(f"❌ Fehler beim Laden des Videos: {e}")
            return False
    
    def play(self):
        """Startet die Video-Wiedergabe."""
        if not self.video_loaded or not CV2_AVAILABLE:
            print("⚠️ Kein Video geladen")
            return
        
        # Spielmusik pausieren (nicht stoppen!)
        try:
            self._music_was_playing = pygame.mixer.music.get_busy()
            if self._music_was_playing:
                pygame.mixer.music.pause()
                print("🔇 Spielmusik pausiert für Intro")
        except:
            pass
        
        # Video zum Anfang zurücksetzen
        self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
        self.is_playing = True
        self.frame_timer = 0.0
        
        # Video-Audio starten (falls vorhanden)
        if self.audio_path and os.path.exists(self.audio_path):
            try:
                pygame.mixer.music.load(self.audio_path)
                pygame.mixer.music.play()
                print("🔊 Video-Audio wird abgespielt")
            except Exception as e:
                print(f"⚠️ Konnte Video-Audio nicht abspielen: {e}")
        
        print("▶️ Video-Cinematic gestartet!")
    
    def stop(self):
        """Stoppt die Video-Wiedergabe."""
        self.is_playing = False
        self.current_frame = None
        
        # Video-Audio stoppen
        try:
            pygame.mixer.music.stop()
        except:
            pass
        
        # Spielmusik wieder starten falls sie vorher lief
        # (wird vom Spiel selbst gemacht nach dem Callback)
        
        print("⏹️ Video-Cinematic beendet")
    
    def update(self, dt: float) -> bool:
        """
        Aktualisiert die Video-Wiedergabe.
        
        Args:
            dt: Delta-Zeit in Sekunden
            
        Returns:
            True wenn Video noch läuft, False wenn beendet
        """
        if not self.is_playing or not self.video_loaded:
            return False
        
        self.frame_timer += dt
        
        # Nächstes Frame holen wenn Zeit
        if self.frame_timer >= self.frame_duration:
            self.frame_timer = 0.0
            
            ret, frame = self.video_capture.read()
            
            if not ret:
                # Video zu Ende
                self.stop()
                return False
            
            # OpenCV BGR -> RGB konvertieren
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Frame skalieren (mit scale_factor damit alles passt)
            scale_w = self.screen_width / self.video_width
            scale_h = self.screen_height / self.video_height
            scale = min(scale_w, scale_h) * self.scale_factor
            
            new_w = int(self.video_width * scale)
            new_h = int(self.video_height * scale)
            
            frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
            
            # Zu Pygame Surface konvertieren
            # Frame ist (height, width, 3) - muss transponiert werden für pygame
            self.current_frame = pygame.image.frombuffer(
                frame.tobytes(), (new_w, new_h), "RGB"
            )
        
        return True
    
    def render(self, screen: pygame.Surface):
        """
        Zeichnet das aktuelle Video-Frame.
        
        Args:
            screen: Pygame Surface zum Zeichnen
        """
        if not self.is_playing or self.current_frame is None:
            return
        
        screen_w, screen_h = screen.get_size()
        
        # Schwarzer Hintergrund
        screen.fill((0, 0, 0))
        
        # Frame zentriert zeichnen
        frame_rect = self.current_frame.get_rect()
        frame_rect.center = (screen_w // 2, screen_h // 2)
        screen.blit(self.current_frame, frame_rect)
        
        # Skip-Hinweis
        if self.skip_enabled:
            try:
                font = pygame.font.Font(None, 22)
                hint = font.render("Druecke C, SPACE oder ESC zum Ueberspringen", True, (150, 150, 150))
                hint_rect = hint.get_rect()
                hint_rect.midbottom = (screen_w // 2, screen_h - 15)
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
        
        # Skip mit ESC, Space, Enter oder C
        if event.type == pygame.KEYDOWN:
            if self.skip_enabled and event.key in (pygame.K_ESCAPE, pygame.K_SPACE, pygame.K_RETURN, pygame.K_c):
                self.stop()
                return True
        
        # Mausklick zum Überspringen
        if event.type == pygame.MOUSEBUTTONDOWN and self.skip_enabled:
            self.stop()
            return True
        
        return False
    
    def cleanup(self):
        """Gibt Ressourcen frei."""
        if self.video_capture:
            self.video_capture.release()
            self.video_capture = None
        self.video_loaded = False
        self.is_playing = False


class IntroCinematic:
    """
    Verwaltet das Intro-Cinematic beim Spielstart.
    Wrapper um VideoPlayer mit spezifischer Logik für Intro.
    """
    
    def __init__(self, screen_size: Tuple[int, int], scale_factor: float = 0.70):
        self.video_player = VideoPlayer(screen_size, scale_factor=scale_factor)
        self.intro_played = False
        self.on_complete_callback = None
        
        # Standard-Pfade für Intro-Video
        self._setup_paths()
    
    def _setup_paths(self):
        """Setzt die Pfade für Intro-Assets."""
        assets_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
            "assets"
        )
        
        # Mögliche Pfade für das Intro-Video
        self.video_paths = [
            os.path.join(assets_path, "cinematics", "intro.mp4"),
            os.path.join(assets_path, "videos", "intro.mp4"),
            os.path.join(assets_path, "intro.mp4"),
        ]
        
        # Optionaler separater Audio-Track
        self.audio_paths = [
            os.path.join(assets_path, "cinematics", "intro_audio.mp3"),
            os.path.join(assets_path, "sounds", "intro.mp3"),
        ]
    
    def load(self) -> bool:
        """
        Lädt das Intro-Video falls vorhanden.
        
        Returns:
            True wenn Video gefunden und geladen
        """
        # Suche nach Video
        video_path = None
        for path in self.video_paths:
            if os.path.exists(path):
                video_path = path
                break
        
        if not video_path:
            print("ℹ️ Kein Intro-Video gefunden (assets/cinematics/intro.mp4)")
            return False
        
        # Suche nach Audio (optional)
        audio_path = None
        for path in self.audio_paths:
            if os.path.exists(path):
                audio_path = path
                break
        
        return self.video_player.load_video(video_path, audio_path)
    
    def play(self, on_complete=None):
        """
        Startet das Intro-Cinematic.
        
        Args:
            on_complete: Callback-Funktion die nach dem Video aufgerufen wird
        """
        self.on_complete_callback = on_complete
        self._last_update_time = pygame.time.get_ticks() / 1000.0  # Timer zurücksetzen
        
        if self.video_player.video_loaded:
            self.video_player.play()
        else:
            # Kein Video - direkt zum Callback
            print("ℹ️ Kein Intro-Video - überspringe Cinematic")
            if on_complete:
                on_complete()
    
    def update(self, dt: float = None) -> bool:
        """
        Aktualisiert das Intro.
        
        Args:
            dt: Delta-Zeit (optional, wird berechnet wenn nicht angegeben)
        
        Returns:
            True wenn Intro noch läuft
        """
        if not self.video_player.is_playing:
            return False
        
        # Falls kein dt übergeben, selbst berechnen
        if dt is None:
            current_time = pygame.time.get_ticks() / 1000.0
            if not hasattr(self, '_last_update_time'):
                self._last_update_time = current_time
            dt = current_time - self._last_update_time
            self._last_update_time = current_time
        
        still_playing = self.video_player.update(dt)
        
        if not still_playing:
            # Video beendet
            self.intro_played = True
            if self.on_complete_callback:
                self.on_complete_callback()
        
        return still_playing
    
    def render(self, screen: pygame.Surface):
        """Rendert das Intro."""
        self.video_player.render(screen)
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Verarbeitet Events."""
        consumed = self.video_player.handle_event(event)
        
        # Wenn übersprungen, Callback aufrufen
        if consumed and not self.video_player.is_playing:
            self.intro_played = True
            if self.on_complete_callback:
                self.on_complete_callback()
        
        return consumed
    
    @property
    def is_playing(self) -> bool:
        return self.video_player.is_playing
    
    def skip(self):
        """Überspringt das Intro."""
        self.video_player.stop()
        self.intro_played = True
        if self.on_complete_callback:
            self.on_complete_callback()
