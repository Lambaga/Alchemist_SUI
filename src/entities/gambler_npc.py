# -*- coding: utf-8 -*-
"""
Gambler NPC - Ein NPC der Blackjack anbietet
"""

import pygame
import os
from typing import Optional, Tuple

class GamblerNPC(pygame.sprite.Sprite):
    """
    Ein mysteriöser Glücksspiel-NPC der Blackjack anbietet.
    Platzhalter-Character mit einfacher Animation.
    """
    
    def __init__(self, x: int, y: int):
        super().__init__()
        
        self.name = "Der Spieler"
        
        # Position
        self.pos_x = float(x)
        self.pos_y = float(y)
        
        # Platzhalter-Sprite erstellen (wird später durch echtes Asset ersetzt)
        self._create_placeholder_sprite()
        
        self.rect = self.image.get_rect()
        self.rect.midbottom = (int(self.pos_x), int(self.pos_y))
        
        # Animation
        self.animation_timer = 0.0
        self.animation_speed = 0.5  # Langsame Idle-Animation
        self.frame_index = 0
        
        # Interaktion
        self.interaction_radius = 80
        self.can_interact = False
        self.is_interacting = False
        
    def _create_placeholder_sprite(self):
        """Erstellt einen Platzhalter-Sprite für den Gambler."""
        # Einfacher Platzhalter - kann später durch echtes Asset ersetzt werden
        width, height = 48, 64
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        
        # Körper (dunkler Mantel)
        pygame.draw.ellipse(self.image, (30, 30, 40), (8, 24, 32, 40))
        
        # Kopf
        pygame.draw.circle(self.image, (200, 160, 130), (24, 16), 12)
        
        # Zylinderhut (typisch für Glücksspieler)
        pygame.draw.rect(self.image, (20, 20, 25), (12, 0, 24, 12))
        pygame.draw.rect(self.image, (20, 20, 25), (8, 10, 32, 4))
        
        # Augen (mysteriös)
        pygame.draw.circle(self.image, (200, 50, 50), (20, 14), 2)
        pygame.draw.circle(self.image, (200, 50, 50), (28, 14), 2)
        
        # Spielkarten in der Hand
        pygame.draw.rect(self.image, (255, 255, 255), (34, 32, 10, 14))
        pygame.draw.rect(self.image, (255, 255, 255), (36, 34, 10, 14))
        pygame.draw.rect(self.image, (0, 0, 0), (34, 32, 10, 14), 1)
        pygame.draw.rect(self.image, (0, 0, 0), (36, 34, 10, 14), 1)
        
        # Kleines Herz auf der Karte
        pygame.draw.circle(self.image, (200, 0, 0), (39, 37), 2)
        
    def update(self, dt: float = None):
        """Aktualisiert die Animation."""
        if dt is None:
            dt = 1/60
            
        # Einfache "schwebende" Idle-Animation
        self.animation_timer += dt
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0.0
            # Leichtes Auf- und Abschweben
            self.frame_index = (self.frame_index + 1) % 4
            
    def check_player_nearby(self, player_pos: Tuple[float, float]) -> bool:
        """Prüft ob der Spieler in Interaktionsreichweite ist."""
        dx = player_pos[0] - self.pos_x
        dy = player_pos[1] - self.pos_y
        distance = (dx * dx + dy * dy) ** 0.5
        
        self.can_interact = distance <= self.interaction_radius
        return self.can_interact
    
    def get_interaction_prompt(self) -> str:
        """Gibt den Interaktions-Hinweis zurück."""
        return "Drücke C um zu spielen"
    
    def draw(self, screen: pygame.Surface, camera):
        """Zeichnet den NPC."""
        # Kamera-Transformation anwenden (wie Beckalof)
        screen_pos = camera.apply(self)
        
        # Leichtes Schweben basierend auf frame_index
        hover_offset = [0, -2, 0, 2][self.frame_index]
        
        screen.blit(self.image, (screen_pos.x, screen_pos.y + hover_offset))
        
    def draw_interaction_prompt(self, screen: pygame.Surface, camera):
        """Zeichnet den Interaktions-Hinweis über dem NPC."""
        if not self.can_interact:
            return
            
        # Kamera-Transformation anwenden
        screen_pos = camera.apply(self)
        prompt_x = screen_pos.centerx
        prompt_y = screen_pos.top - 25
        
        # Text rendern
        try:
            font = pygame.font.Font(None, 20)
            text = font.render(self.get_interaction_prompt(), True, (255, 220, 100))
            text_rect = text.get_rect(center=(prompt_x, prompt_y))
            
            # Hintergrund
            bg_rect = text_rect.inflate(10, 6)
            pygame.draw.rect(screen, (0, 0, 0, 180), bg_rect, border_radius=4)
            pygame.draw.rect(screen, (255, 200, 50), bg_rect, 1, border_radius=4)
            
            screen.blit(text, text_rect)
        except:
            pass
