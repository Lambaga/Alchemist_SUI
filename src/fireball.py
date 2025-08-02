# src/fireball.py
# Fireball projectile class

import pygame
import math
import os
from settings import *

class Fireball(pygame.sprite.Sprite):
    """
    Fireball projectile that moves toward the player
    """
    def __init__(self, start_x, start_y, target_x, target_y, asset_path, scale_factor=1.0):
        """
        Initialize the fireball.
        :param start_x: Starting X position
        :param start_y: Starting Y position
        :param target_x: Target X position (usually player position)
        :param target_y: Target Y position (usually player position)
        :param asset_path: Path to fireball sprite folder
        :param scale_factor: Scale the fireball size
        """
        super().__init__()
        
        # Animation configuration
        self.animation_speed_ms = 150  # Fast animation for fireball
        self.last_update_time = pygame.time.get_ticks()
        self.current_frame_index = 0
        
        # Fireball properties
        self.scale_factor = scale_factor
        self.speed = 200  # Pixels per second
        self.damage = 25
        self.is_alive = True
        
        # Movement calculation
        direction = pygame.math.Vector2(target_x - start_x, target_y - start_y)
        if direction.length() > 0:
            direction = direction.normalize()
        self.direction = direction
        
        # Animation frames
        self.move_frames = []
        self.explosion_frames = []
        self.state = "moving"  # "moving" or "exploding"
        
        self.load_animations(asset_path)
        
        # Set initial image and position
        self.image = self.move_frames[0] if self.move_frames else self.create_placeholder()
        self.rect = self.image.get_rect(center=(start_x, start_y))
        
        # Collision box
        self.hitbox = self.rect.inflate(-10, -10)
        
        # Explosion timer
        self.explosion_timer = 0
        self.explosion_duration = 500  # 0.5 seconds
        
    def load_animations(self, asset_path):
        """Load fireball animation frames"""
        if not os.path.exists(asset_path):
            print("⚠️ Fireball asset path not found: {}".format(asset_path))
            return
            
        try:
            # Load Move animation (fireball flying)
            move_path = os.path.join(asset_path, "Move.png")
            if os.path.exists(move_path):
                move_sheet = pygame.image.load(move_path).convert_alpha()
                frame_height = move_sheet.get_height()
                # Assuming 5 frames in a horizontal sprite sheet
                frame_width = move_sheet.get_width() // 5
                for i in range(5):
                    frame = move_sheet.subsurface((i * frame_width, 0, frame_width, frame_height))
                    if self.scale_factor != 1.0:
                        new_width = int(frame.get_width() * self.scale_factor)
                        new_height = int(frame.get_height() * self.scale_factor)
                        frame = pygame.transform.scale(frame, (new_width, new_height))
                    self.move_frames.append(frame)
                print("✅ Fireball loaded {} move frames".format(len(self.move_frames)))
            
            # Load Explosion animation
            explosion_path = os.path.join(asset_path, "Explosion.png")
            if os.path.exists(explosion_path):
                explosion_sheet = pygame.image.load(explosion_path).convert_alpha()
                # For now, we'll use the whole image as one frame
                if self.scale_factor != 1.0:
                    new_width = int(explosion_sheet.get_width() * self.scale_factor)
                    new_height = int(explosion_sheet.get_height() * self.scale_factor)
                    explosion_sheet = pygame.transform.scale(explosion_sheet, (new_width, new_height))
                self.explosion_frames.append(explosion_sheet)
                print("✅ Fireball loaded explosion animation")
                
        except Exception as e:
            print("❌ Error loading fireball animations: {}".format(e))
            
    def create_placeholder(self):
        """Create a placeholder if no sprites are found"""
        placeholder = pygame.Surface((32, 32), pygame.SRCALPHA)
        pygame.draw.circle(placeholder, (255, 100, 0), (16, 16), 15)  # Orange fireball
        pygame.draw.circle(placeholder, (255, 255, 0), (16, 16), 10)  # Yellow center
        return placeholder
    
    def get_current_frames(self):
        """Get the current animation frames based on state"""
        if self.state == "exploding" and self.explosion_frames:
            return self.explosion_frames
        else:
            return self.move_frames
    
    def update_animation(self, current_time):
        """Update animation frame"""
        current_frames = self.get_current_frames()
        if not current_frames:
            return
            
        if current_time - self.last_update_time >= self.animation_speed_ms:
            self.current_frame_index = (self.current_frame_index + 1) % len(current_frames)
            self.image = current_frames[self.current_frame_index]
            self.last_update_time = current_time
    
    def explode(self):
        """Start explosion animation"""
        if self.state != "exploding":
            self.state = "exploding"
            self.current_frame_index = 0
            self.explosion_timer = pygame.time.get_ticks()
    
    def update(self, dt=None, player=None):
        """Update fireball movement and animation"""
        current_time = pygame.time.get_ticks()
        
        if self.state == "moving":
            # Move toward target
            if dt:
                movement = self.direction * self.speed * dt
                self.rect.centerx += movement.x
                self.rect.centery += movement.y
                self.hitbox.center = self.rect.center
                
                # Check collision with player
                if player and self.hitbox.colliderect(player.hitbox):
                    self.explode()
                    # Deal damage to player (implement player.take_damage if needed)
                    print("🔥 Fireball hit player for {} damage!".format(self.damage))
                    
        elif self.state == "exploding":
            # Check if explosion animation is complete
            if current_time - self.explosion_timer >= self.explosion_duration:
                self.is_alive = False
        
        # Update animation
        self.update_animation(current_time)
        
    def should_remove(self):
        """Check if fireball should be removed"""
        return not self.is_alive
