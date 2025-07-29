# src/player.py
# Enthält die Klasse für den Spieler-Charakter (den Alchemisten) mit verschiedenen Animationen.

import pygame
from config import Colors, PlayerConfig
import os

class Player(pygame.sprite.Sprite):
    """
    Diese Klasse repräsentiert den Spieler und verwaltet dessen Animationen.
    Unterstützt verschiedene Animationszustände wie "idle" und "run".
    """
    def __init__(self, asset_path, pos_x, pos_y):
        """
        Initialisiert den Spieler.
        :param asset_path: Pfad zum Spritesheet (Datei) oder Animations-Ordner.
        :param pos_x: Start-X-Position des Spielers.
        :param pos_y: Start-Y-Position des Spielers.
        """
        super().__init__()
        
        # Animations-Konfiguration
        self.animation_speed_ms = PlayerConfig.ANIMATION_SPEED_MS
        self.last_update_time = pygame.time.get_ticks()
        self.current_frame_index = 0
        
        # Bewegungs-Konfiguration
        self.speed = PlayerConfig.SPEED
        self.is_moving = False
        self.facing_right = True # Spieler schaut standardmäßig nach rechts
        
        # Animations-Zustände
        self.current_state = "idle"
        self.animation_frames = {"idle": [], "run": []}
        
        self.load_animations(asset_path)
        
        # Initiales Bild und Position setzen
        self.image = self.animation_frames[self.current_state][0]
        self.rect = self.image.get_rect(center=(pos_x, pos_y))

    def load_animations(self, path):
        """
        Lädt Animationen. Prüft, ob der Pfad ein Ordner (für mehrere Animationen)
        oder eine einzelne Datei ist.
        """
        # Fall 1: Der Pfad ist ein Ordner (z.B. "assets/Wizard Pack")
        if os.path.isdir(path):
            print(f"Lade Animationen aus Ordner: {path}")
            # Annahme: Idle.png hat 6 Frames, Run.png hat 8 Frames
            self.animation_frames["idle"] = self.load_frames_from_spritesheet(os.path.join(path, "Idle.png"), 6)
            self.animation_frames["run"] = self.load_frames_from_spritesheet(os.path.join(path, "Run.png"), 8)
        # Fall 2: Der Pfad ist eine einzelne Datei
        elif os.path.isfile(path):
            print(f"Lade einzelne Spritesheet-Datei: {path}")
            # Wir nehmen an, die einzelne Datei ist eine Idle-Animation mit 60 Frames
            frames = self.load_frames_from_spritesheet(path, 60)
            self.animation_frames["idle"] = frames
            self.animation_frames["run"] = frames # Verwenden die gleiche Animation für "run"
        else:
            print(f"FEHLER: Asset-Pfad nicht gefunden: {path}")
            # Erstelle einen Fallback-Platzhalter, damit das Spiel nicht abstürzt
            self.animation_frames["idle"] = [pygame.Surface((50, 80))]
            self.animation_frames["idle"][0].fill((255, 0, 0))
            self.animation_frames["run"] = self.animation_frames["idle"]


    def load_frames_from_spritesheet(self, spritesheet_path, num_frames):
        """
        Lädt eine Spritesheet-Datei und schneidet sie in einzelne Animations-Frames.
        :param spritesheet_path: Der genaue Pfad zur Bilddatei.
        :param num_frames: Die exakte Anzahl der Frames in dieser Datei.
        """
        frames = []
        try:
            spritesheet = pygame.image.load(spritesheet_path).convert_alpha()
        except pygame.error:
            print(f"Fehler: Spritesheet-Datei konnte nicht geladen werden: {spritesheet_path}")
            # Erstelle einen Platzhalter in der richtigen Größe
            placeholder = pygame.Surface((PlayerConfig.SPRITE_WIDTH, PlayerConfig.SPRITE_HEIGHT), pygame.SRCALPHA)
            placeholder.fill(Colors.PLACEHOLDER_GREEN)  # Grün als Platzhalter
            return [placeholder]

        sheet_width = spritesheet.get_width()
        sheet_height = spritesheet.get_height()
        
        frame_width = sheet_width // num_frames
        frame_height = sheet_height

        print(f"Lade {num_frames} Frames der Größe {frame_width}x{frame_height} aus {os.path.basename(spritesheet_path)}")

        for i in range(num_frames):
            x = i * frame_width
            frame_surface = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
            frame_surface.blit(spritesheet, (0, 0), (x, 0, frame_width, frame_height))
            
            # Skaliere das Bild für passende Größe zu den Kacheln (etwa 2 Kacheln hoch = 64px)
            # Original: 231x190 -> Ziel: etwa 48x64 (2 Kacheln breit, 2 Kacheln hoch)
            target_width = 48
            target_height = 64
            scaled_frame = pygame.transform.scale(frame_surface, (target_width, target_height))
            frames.append(scaled_frame)
            
        return frames

    def update(self):
        """
        Aktualisiert den Zustand und die Animation des Spielers in jedem Tick.
        """
        # 1. Animationszustand basierend auf Bewegung bestimmen
        new_state = "run" if self.is_moving else "idle"
        if new_state != self.current_state:
            self.current_state = new_state
            self.current_frame_index = 0 # Animation zurücksetzen

        # 2. Animation fortschreiten lassen
        now = pygame.time.get_ticks()
        if now - self.last_update_time > self.animation_speed_ms[self.current_state]:
            self.last_update_time = now
            
            frames_for_current_state = self.animation_frames[self.current_state]
            self.current_frame_index = (self.current_frame_index + 1) % len(frames_for_current_state)
            
            # Das Bild des Sprites aktualisieren
            new_image = frames_for_current_state[self.current_frame_index]
            
            # Bild spiegeln, falls der Spieler nach links schaut
            if not self.facing_right:
                new_image = pygame.transform.flip(new_image, True, False)
            
            # Position beibehalten, während das Bild aktualisiert wird
            old_center = self.rect.center
            self.image = new_image
            self.rect = self.image.get_rect(center=old_center)

    def move(self, dx, dy=0):
        """Bewegt den Spieler horizontal und vertikal."""
        if dx > 0:
            self.facing_right = True
        elif dx < 0:
            self.facing_right = False
        
        self.rect.x += dx
        self.rect.y += dy
        
        # Grenzen des Bildschirms einhalten (für sehr große Maps können diese entfernt werden)
        if self.rect.left < -1000:  # Erweiterte Grenzen für größere Maps
            self.rect.left = -1000
        if self.rect.right > 2920:  # Erweiterte Grenzen
            self.rect.right = 2920
        if self.rect.top < -1000:
            self.rect.top = -1000
        if self.rect.bottom > 2080:
            self.rect.bottom = 2080

    def get_movement_left(self):
        """Gibt die Bewegung nach links zurück"""
        self.is_moving = True
        self.facing_right = False
        return (-self.speed, 0)
        
    def get_movement_right(self):
        """Gibt die Bewegung nach rechts zurück"""
        self.is_moving = True
        self.facing_right = True
        return (self.speed, 0)

    def get_movement_up(self):
        """Gibt die Bewegung nach oben zurück"""
        self.is_moving = True
        return (0, -self.speed)
        
    def get_movement_down(self):
        """Gibt die Bewegung nach unten zurück"""
        self.is_moving = True
        return (0, self.speed)
        
    # Behalte die alten Methoden für Kompatibilität bei
    def move_left(self):
        """Bewegt den Spieler nach links"""
        dx, dy = self.get_movement_left()
        self.move(dx, dy)
        
    def move_right(self):
        """Bewegt den Spieler nach rechts"""
        dx, dy = self.get_movement_right()
        self.move(dx, dy)

    def move_up(self):
        """Bewegt den Spieler nach oben"""
        dx, dy = self.get_movement_up()
        self.move(dx, dy)
        
    def move_down(self):
        """Bewegt den Spieler nach unten"""
        dx, dy = self.get_movement_down()
        self.move(dx, dy)

    def stop_moving(self):
        """Stoppt die Bewegung des Spielers"""
        self.is_moving = False

    def update_position_properties(self):
        """Aktualisiert Position-Properties für Kompatibilität"""
        self.x = self.rect.centerx
        self.y = self.rect.centery
        self.width = self.rect.width
        self.height = self.rect.height

    def get_rect(self):
        """Gibt das Rechteck des Spielers zurück für Kollisionserkennung"""
        return (self.rect.x, self.rect.y, self.rect.width, self.rect.height)
