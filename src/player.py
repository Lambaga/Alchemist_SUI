# src/player.py
# Enthält die Klasse für den Spieler-Charakter (den Alchemisten) mit verschiedenen Animationen.

import pygame
import os
from settings import *

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
        self.animation_speed_ms = {"idle": 200, "run": 120}  # Robuste Animation timings
        self.last_update_time = pygame.time.get_ticks()
        self.current_frame_index = 0
        
        # Bewegungs-Konfiguration (Delta Time Support)
        self.speed = PLAYER_SPEED
        self.direction = pygame.math.Vector2(0, 0)  # Verwende Vector2 für präzise Bewegung
        self.facing_right = True  # Spieler schaut standardmäßig nach rechts
        self.status = "idle"  # Neues robustes Status-System
        
        # Animations-Zustände
        self.animation_frames = {"idle": [], "run": []}
        
        self.load_animations(asset_path)
        
        # Initiales Bild und Position setzen
        self.image = self.animation_frames["idle"][0] if self.animation_frames["idle"] else self.create_placeholder()
        self.rect = self.image.get_rect(center=(pos_x, pos_y))
        # Perfekt angepasste Hitbox - genau um den Charakter herum
        self.hitbox = self.rect.inflate(-50, -70)  # Optimal: -50 Breite, -70 Höhe
        self.position = pygame.math.Vector2(self.rect.center)  # Genaue Float-Position für dt-Berechnungen
        
        # Für Kollisionserkennung
        self.obstacle_sprites = pygame.sprite.Group()
    
    def update_hitbox(self):
        """Aktualisiert die Hitbox basierend auf der aktuellen rect-Position"""
        # Perfekt angepasste Hitbox - genau um den Charakter herum
        self.hitbox = self.rect.inflate(-70, -70)  # Optimal: -50 Breite, -70 Höhe
        self.position = pygame.math.Vector2(self.rect.center)

    def create_placeholder(self):
        """Erstellt einen Platzhalter-Sprite bei Asset-Ladeproblemen"""
        placeholder = pygame.Surface(PLAYER_SIZE, pygame.SRCALPHA)
        placeholder.fill((0, 255, 0))  # Grün als Platzhalter
        return placeholder

    def load_animations(self, path):
        """
        Lädt Animationen. Prüft, ob der Pfad ein Ordner (für mehrere Animationen)
        oder eine einzelne Datei ist.
        
        TODO: Refactor für Asset-Loading-System
        - Erstelle asset_loader.py für zentrales Asset-Management
        - Lade Animationen nur einmal und teile sie zwischen allen Instanzen
        - Verwende Sprite-Atlas für bessere Performance
        """
        # Fall 1: Der Pfad ist ein Ordner (z.B. "assets/Wizard Pack")
        if os.path.isdir(path):
            # Annahme: Idle.png hat 6 Frames, Run.png hat 8 Frames
            self.animation_frames["idle"] = self.load_frames_from_spritesheet(os.path.join(path, "Idle.png"), 6)
            self.animation_frames["run"] = self.load_frames_from_spritesheet(os.path.join(path, "Run.png"), 8)
        # Fall 2: Der Pfad ist eine einzelne Datei
        elif os.path.isfile(path):
            # Wir nehmen an, die einzelne Datei ist eine Idle-Animation mit 60 Frames
            frames = self.load_frames_from_spritesheet(path, 60)
            self.animation_frames["idle"] = frames
            self.animation_frames["run"] = frames # Verwenden die gleiche Animation für "run"
        else:
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
            # Erstelle einen Platzhalter in der richtigen Größe
            return [self.create_placeholder()]

        sheet_width = spritesheet.get_width()
        sheet_height = spritesheet.get_height()
        
        frame_width = sheet_width // num_frames
        frame_height = sheet_height

        for i in range(num_frames):
            x = i * frame_width
            frame_surface = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
            frame_surface.blit(spritesheet, (0, 0), (x, 0, frame_width, frame_height))
            
            # Skaliere das Bild für passende Größe zu den Kacheln
            # Original: 231x190 -> Ziel: PLAYER_SIZE für bessere Sichtbarkeit
            scaled_frame = pygame.transform.scale(frame_surface, PLAYER_SIZE)
            frames.append(scaled_frame)
            
        return frames

    def get_status(self):
        """
        Robuste Status-Bestimmung für Animationen.
        Bestimmt den Status in jedem Frame neu, um 'steckenbleibende' Animationen zu vermeiden.
        """
        # idle status
        if self.direction.x == 0 and self.direction.y == 0:
            # Wenn der Status nicht schon 'idle' ist, setze ihn und starte die Animation neu
            if 'idle' not in self.status:
                self.status = 'idle'
                self.current_frame_index = 0
        else:
            # Bewegung erkannt
            if 'run' not in self.status:
                self.status = 'run'
                self.current_frame_index = 0
        
        # TODO: Erweitert für Kampf-Status
        # if self.attacking:
        #     self.direction.x = 0
        #     self.direction.y = 0
        #     if 'attack' not in self.status:
        #         self.status = 'attack'
        #         self.current_frame_index = 0

    def update(self, dt=None):
        """
        Aktualisiert den Zustand und die Animation des Spielers.
        dt: Delta Time in Sekunden (obligatorisch für framerate-unabhängige Bewegung)
        """
        if dt is None:
            dt = 1.0 / 60.0  # Fallback für 60 FPS
        
        # 1. Status basierend auf aktueller Bewegungsrichtung bestimmen
        self.get_status()

        # 2. Animation fortschreiten lassen (Delta Time basiert)
        now = pygame.time.get_ticks()
        if now - self.last_update_time > self.animation_speed_ms[self.status]:
            self.last_update_time = now
            
            frames_for_current_status = self.animation_frames[self.status]
            if frames_for_current_status:  # Sicherheitsprüfung
                self.current_frame_index = (self.current_frame_index + 1) % len(frames_for_current_status)
                
                # Das Bild des Sprites aktualisieren
                new_image = frames_for_current_status[self.current_frame_index]
                
                # Bild spiegeln, falls der Spieler nach links schaut
                if not self.facing_right:
                    new_image = pygame.transform.flip(new_image, True, False)
                
                # Position beibehalten, während das Bild aktualisiert wird
                old_center = self.rect.center
                self.image = new_image
                self.rect = self.image.get_rect(center=old_center)

    def move(self, dt=1.0/60.0):
        """
        Delta Time basierte Bewegung mit präziser Float-Position und Kollisionserkennung.
        dt: Delta Time in Sekunden für framerate-unabhängige Bewegung
        """
        if self.direction.magnitude() > 0:
            # Normalisiere die Richtung, um diagonale Bewegung zu korrigieren
            normalized_direction = self.direction.normalize()
            
            # Aktualisiere Blickrichtung
            if normalized_direction.x > 0:
                self.facing_right = True
            elif normalized_direction.x < 0:
                self.facing_right = False
            
            # Berechne die Bewegung mit Float-Präzision
            speed_multiplier = self.speed * dt * 60  # * 60 für 60fps Referenz
            
            # Berechnungen mit der Float-Position durchführen
            self.position.x += normalized_direction.x * speed_multiplier
            self.position.y += normalized_direction.y * speed_multiplier
            
            # Die Integer-Hitbox von der Float-Position aktualisieren
            self.hitbox.centerx = round(self.position.x)
            self.collision('horizontal')  # Kollision mit der gerundeten Position prüfen
            self.hitbox.centery = round(self.position.y)
            self.collision('vertical')  # Kollision mit der gerundeten Position prüfen
            
            # Das finale rect von der (möglicherweise korrigierten) Hitbox aktualisieren
            self.rect.center = self.hitbox.center

    def collision(self, direction):
        """
        Kollisionserkennung mit Hindernissen.
        Nach einer Kollision wird auch die Float-Position synchronisiert.
        """
        if direction == 'horizontal':
            for sprite in self.obstacle_sprites:
                if sprite.hitbox.colliderect(self.hitbox):
                    if self.direction.x > 0:  # Bewegung nach rechts
                        self.hitbox.right = sprite.hitbox.left
                    if self.direction.x < 0:  # Bewegung nach links
                        self.hitbox.left = sprite.hitbox.right
                    self.position.x = self.hitbox.centerx  # Float-Position synchronisieren

        if direction == 'vertical':
            for sprite in self.obstacle_sprites:
                if sprite.hitbox.colliderect(self.hitbox):
                    if self.direction.y > 0:  # Bewegung nach unten
                        self.hitbox.bottom = sprite.hitbox.top
                    if self.direction.y < 0:  # Bewegung nach oben
                        self.hitbox.top = sprite.hitbox.bottom
                    self.position.y = self.hitbox.centery  # Float-Position synchronisieren

    def set_obstacle_sprites(self, obstacle_sprites):
        """Setzt die Sprite-Gruppe für Kollisionserkennung"""
        self.obstacle_sprites = obstacle_sprites

    def set_direction(self, direction_vector):
        """Setzt die Bewegungsrichtung als Vector2 (modern approach)"""
        self.direction = direction_vector

    def get_movement_left(self):
        """Legacy Kompatibilität - gibt die Bewegung nach links zurück"""
        self.direction.x = -1
        return (-self.speed, 0)
        
    def get_movement_right(self):
        """Legacy Kompatibilität - gibt die Bewegung nach rechts zurück"""
        self.direction.x = 1
        return (self.speed, 0)

    def get_movement_up(self):
        """Legacy Kompatibilität - gibt die Bewegung nach oben zurück"""
        self.direction.y = -1
        return (0, -self.speed)
        
    def get_movement_down(self):
        """Legacy Kompatibilität - gibt die Bewegung nach unten zurück"""
        self.direction.y = 1
        return (0, self.speed)
        
    # Legacy Kompatibilität: Behalte die alten Methoden bei
    def move_left(self):
        """Legacy: Bewegt den Spieler nach links"""
        self.direction.x = -1
        
    def move_right(self):
        """Legacy: Bewegt den Spieler nach rechts"""
        self.direction.x = 1

    def move_up(self):
        """Legacy: Bewegt den Spieler nach oben"""
        self.direction.y = -1
        
    def move_down(self):
        """Legacy: Bewegt den Spieler nach unten"""
        self.direction.y = 1

    def stop_moving(self):
        """Stoppt die Bewegung des Spielers"""
        self.direction = pygame.math.Vector2(0, 0)

    def update_position_properties(self):
        """Aktualisiert Position-Properties für Kompatibilität"""
        self.x = self.rect.centerx
        self.y = self.rect.centery
        self.width = self.rect.width
        self.height = self.rect.height

    def get_rect(self):
        """Gibt das Rechteck des Spielers zurück für Kollisionserkennung"""
        return (self.rect.x, self.rect.y, self.rect.width, self.rect.height)
