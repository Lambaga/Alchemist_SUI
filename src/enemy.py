# src/enemy.py
# Base Enemy class for all enemy types

import pygame
import os
from settings import *

class Enemy(pygame.sprite.Sprite):
    """
    Base class for all enemy types with common functionality.
    """
    def __init__(self, asset_path, pos_x, pos_y, scale_factor=1.0):
        """
        Initialize the base enemy.
        :param asset_path: Path to enemy sprite folder containing animation frames
        :param pos_x: X position on the map
        :param pos_y: Y position on the map  
        :param scale_factor: Scale the enemy size (1.0 = original size)
        """
        super().__init__()
        
        # Animation configuration
        self.animation_speed_ms = 300  # Animation speed in milliseconds
        self.last_update_time = pygame.time.get_ticks()
        self.current_frame_index = 0
        
        # Enemy properties
        self.scale_factor = scale_factor
        self.facing_right = True
        
        # AI and movement properties
        self.speed = 100  # Pixel per second
        self.detection_range = 15 * 64  # 15 tiles * 64 pixels per tile = 960 pixels
        self.state = "idle"  # "idle", "walking", "attacking", "death"
        self.target_player = None
        self.direction = pygame.math.Vector2(0, 0)
        
        # Health system
        self.max_health = 100
        self.current_health = self.max_health
        self.is_alive = True
        
        # Animation frames - to be populated by subclasses
        self.idle_frames = []
        self.walk_frames = []
        self.attack_frames = []
        self.death_frames = []
        self.current_animation = "idle"  # Track current animation type
        
        # Combat properties
        self.attack_damage = 25
        self.attack_range = 3 * 64  # 3 tiles
        self.attack_cooldown = 2000  # 2 seconds in milliseconds
        self.last_attack_time = 0
        
        self.load_animations(asset_path)
        
        # Set initial image and position
        self.image = self.get_current_frames()[0] if self.get_current_frames() else self.create_placeholder()
        self.rect = self.image.get_rect(center=(pos_x, pos_y))
        
        # Collision box (smaller for closer combat)
        self.hitbox = self.rect.inflate(-60, -40)
        
    def load_animations(self, asset_path):
        """Load animation frames - to be implemented by subclasses"""
        pass
        
    def create_placeholder(self):
        """Create a placeholder if no sprites are found"""
        placeholder = pygame.Surface((64, 64), pygame.SRCALPHA)
        pygame.draw.circle(placeholder, (255, 0, 0), (32, 32), 30, 3)
        font = pygame.font.Font(None, 24)
        text = font.render("ENEMY", True, (255, 255, 255))
        text_rect = text.get_rect(center=(32, 32))
        placeholder.blit(text, text_rect)
        return placeholder
        
    def get_current_frames(self):
        """Get the current animation frames based on state"""
        if self.state == "death" and self.death_frames:
            return self.death_frames
        elif self.state == "attacking" and self.attack_frames:
            return self.attack_frames
        elif self.state in ["walking", "chasing"] and self.walk_frames:
            return self.walk_frames
        else:
            return self.idle_frames
    
    def update_animation(self, current_time):
        """Update animation frame based on current state"""
        current_frames = self.get_current_frames()
        if not current_frames:
            return
            
        # Check if enough time has passed to update frame
        if current_time - self.last_update_time >= self.animation_speed_ms:
            # Handle death animation (play once)
            if self.state == "death":
                if self.current_frame_index < len(current_frames) - 1:
                    self.current_frame_index += 1
                    self.last_update_time = current_time
            else:
                # Normal looping animations
                self.current_frame_index = (self.current_frame_index + 1) % len(current_frames)
                self.last_update_time = current_time
            
            # Update current animation type
            new_animation = self.state
            if new_animation != self.current_animation:
                self.current_animation = new_animation
                self.current_frame_index = 0  # Reset frame when switching animations
            
            # Update the image
            self.image = current_frames[self.current_frame_index]
            
            # Handle facing direction
            if not self.facing_right:
                self.image = pygame.transform.flip(self.image, True, False)
    
    def take_damage(self, damage):
        """Take damage and handle death"""
        if not self.is_alive:
            return
            
        self.current_health -= damage
        if self.current_health <= 0:
            self.current_health = 0
            self.is_alive = False
            self.state = "death"
            self.current_frame_index = 0
    
    def can_attack(self, current_time):
        """Check if enemy can attack based on cooldown"""
        return current_time - self.last_attack_time >= self.attack_cooldown
    
    def start_attack(self, current_time):
        """Start attack animation and set cooldown"""
        if self.can_attack(current_time) and self.is_alive:
            self.state = "attacking"
            self.last_attack_time = current_time
            self.current_frame_index = 0
            return True
        return False
    
    def update(self, dt=None, player=None, other_enemies=None):
        """Update enemy animation and AI - to be extended by subclasses"""
        if not self.is_alive:
            current_time = pygame.time.get_ticks()
            self.update_animation(current_time)
            return
            
        current_time = pygame.time.get_ticks()
        
        # Basic AI logic - to be extended by subclasses
        self.update_ai(dt, player, other_enemies)
        
        # Update animation
        self.update_animation(current_time)
    
    def update_ai(self, dt, player, other_enemies):
        """AI logic - to be implemented by subclasses"""
        pass
    
    def set_facing_direction(self, facing_right):
        """Change the direction the enemy is facing"""
        self.facing_right = facing_right
        
    def get_interaction_rect(self):
        """Get the area where player can interact with this enemy"""
        return self.hitbox.inflate(40, 40)
