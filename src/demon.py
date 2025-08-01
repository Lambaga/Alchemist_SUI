# src/demon.py
# Animated Demon NPC with idle animation

import pygame
import os
from settings import *

class Demon(pygame.sprite.Sprite):
    """
    Animated demon NPC with idle animation.
    Can be placed on the map as a static or interactive element.
    """
    def __init__(self, asset_path, pos_x, pos_y, scale_factor=1.0):
        """
        Initialize the demon.
        :param asset_path: Path to demon sprite folder containing idle frames
        :param pos_x: X position on the map
        :param pos_y: Y position on the map  
        :param scale_factor: Scale the demon size (1.0 = original size)
        """
        super().__init__()
        
        # Animation configuration
        self.animation_speed_ms = 300  # Slower animation for idle demons
        self.last_update_time = pygame.time.get_ticks()
        self.current_frame_index = 0
        
        # Demon properties
        self.scale_factor = scale_factor
        self.facing_right = True
        
        # AI and movement properties
        self.speed = 100  # Pixel per second
        self.detection_range = 15 * 64  # 15 tiles * 64 pixels per tile = 960 pixels
        self.state = "idle"  # "idle", "chasing", "attacking"
        self.target_player = None
        self.direction = pygame.math.Vector2(0, 0)
        
        # Animation frames
        self.idle_frames = []
        self.run_frames = []
        self.current_animation = "idle"  # Track current animation type
        
        self.load_animations(asset_path)
        
        # Set initial image and position
        self.image = self.idle_frames[0] if self.idle_frames else self.create_placeholder()
        self.rect = self.image.get_rect(center=(pos_x, pos_y))
        
        # Collision box (smaller for closer combat)
        self.hitbox = self.rect.inflate(-60, -40)
        
    def load_animations(self, asset_path):
        """Load demon animation frames"""
        if not os.path.exists(asset_path):
            print(f"⚠️ Demon asset path not found: {asset_path}")
            return
            
        try:
            # Load Idle animations
            # Method 1: Individual frame files (Idle1.png, Idle2.png, etc.)
            idle_files = []
            for i in range(1, 10):  # Support up to 9 frames
                frame_path = os.path.join(asset_path, f"Idle{i}.png")
                if os.path.exists(frame_path):
                    idle_files.append(frame_path)
                    
            # Method 2: If no numbered files, look for generic names
            if not idle_files:
                potential_names = ["idle1.png", "idle2.png", "idle3.png", "idle4.png",
                                 "demon_idle_1.png", "demon_idle_2.png", "demon_idle_3.png", "demon_idle_4.png"]
                for name in potential_names:
                    frame_path = os.path.join(asset_path, name)
                    if os.path.exists(frame_path):
                        idle_files.append(frame_path)
            
            # Load and scale idle frames
            for frame_path in idle_files:
                frame = pygame.image.load(frame_path).convert_alpha()
                
                # Scale if needed
                if self.scale_factor != 1.0:
                    new_width = int(frame.get_width() * self.scale_factor)
                    new_height = int(frame.get_height() * self.scale_factor)
                    frame = pygame.transform.scale(frame, (new_width, new_height))
                
                self.idle_frames.append(frame)
            
            # Load Run animations
            run_files = []
            # Method 1: Look for big_demon_run_anim_f0, f1, f2, f3 pattern
            for i in range(4):  # 4 run frames: f0, f1, f2, f3
                frame_path = os.path.join(asset_path, f"big_demon_run_anim_f{i}.png")
                if os.path.exists(frame_path):
                    run_files.append(frame_path)
            
            # Method 2: Alternative naming patterns
            if not run_files:
                for i in range(1, 10):  # Support up to 9 frames
                    frame_path = os.path.join(asset_path, f"Run{i}.png")
                    if os.path.exists(frame_path):
                        run_files.append(frame_path)
            
            # Load and scale run frames
            for frame_path in run_files:
                frame = pygame.image.load(frame_path).convert_alpha()
                
                # Scale if needed
                if self.scale_factor != 1.0:
                    new_width = int(frame.get_width() * self.scale_factor)
                    new_height = int(frame.get_height() * self.scale_factor)
                    frame = pygame.transform.scale(frame, (new_width, new_height))
                
                self.run_frames.append(frame)
                
            if self.idle_frames:
                print(f"✅ Demon loaded {len(self.idle_frames)} idle frames")
            else:
                print(f"⚠️ No demon idle frames found in {asset_path}")
                
            if self.run_frames:
                print(f"✅ Demon loaded {len(self.run_frames)} run frames")
            else:
                print(f"⚠️ No demon run frames found in {asset_path}")
                
        except Exception as e:
            print(f"❌ Error loading demon animations: {e}")
            
    def create_placeholder(self):
        """Create a placeholder if no sprites are found"""
        # Make a large, bright placeholder that's easy to see
        placeholder = pygame.Surface((128, 128), pygame.SRCALPHA)
        
        # Large red circle for body
        pygame.draw.circle(placeholder, (255, 0, 0), (64, 64), 60, 5)  # Red outline
        pygame.draw.circle(placeholder, (200, 0, 0), (64, 64), 55)      # Red fill
        
        # Yellow eyes
        pygame.draw.circle(placeholder, (255, 255, 0), (44, 44), 12)  # Left eye
        pygame.draw.circle(placeholder, (255, 255, 0), (84, 44), 12)  # Right eye
        
        # Black pupils
        pygame.draw.circle(placeholder, (0, 0, 0), (44, 44), 6)  # Left pupil
        pygame.draw.circle(placeholder, (0, 0, 0), (84, 44), 6)  # Right pupil
        
        # Demon horns
        pygame.draw.polygon(placeholder, (139, 0, 0), [(44, 20), (54, 0), (64, 20)])  # Left horn
        pygame.draw.polygon(placeholder, (139, 0, 0), [(64, 20), (74, 0), (84, 20)])  # Right horn
        
        # Text label
        font = pygame.font.Font(None, 24)
        text = font.render("DEMON", True, (255, 255, 255))
        text_rect = text.get_rect(center=(64, 100))
        placeholder.blit(text, text_rect)
        
        return placeholder
        
    def get_current_frames(self):
        """Get the current animation frames based on state"""
        if self.state == "chasing" and self.run_frames:
            return self.run_frames
        else:
            return self.idle_frames
    
    def update_animation(self, current_time):
        """Update animation frame based on current state"""
        current_frames = self.get_current_frames()
        if not current_frames:
            return
            
        # Check if enough time has passed to update frame
        if current_time - self.last_update_time >= self.animation_speed_ms:
            self.current_frame_index = (self.current_frame_index + 1) % len(current_frames)
            self.last_update_time = current_time
            
            # Update current animation type
            new_animation = "run" if self.state == "chasing" and self.run_frames else "idle"
            if new_animation != self.current_animation:
                self.current_animation = new_animation
                self.current_frame_index = 0  # Reset frame when switching animations
            
            # Update the image
            self.image = current_frames[self.current_frame_index]
            
            # Handle facing direction
            if not self.facing_right:
                self.image = pygame.transform.flip(self.image, True, False)
        
    def update(self, dt=None, player=None, other_demons=None):
        """Update demon animation and AI with collision detection"""
        if not self.idle_frames:
            return
            
        current_time = pygame.time.get_ticks()
        
        # AI Logic: Check for player in detection range
        if player and self.target_player is None:
            distance_to_player = pygame.math.Vector2(
                player.rect.centerx - self.rect.centerx,
                player.rect.centery - self.rect.centery
            ).length()
            
            if distance_to_player <= self.detection_range:
                self.target_player = player
                self.state = "chasing"
        
        # Movement AI
        if self.state == "chasing" and self.target_player:
            # Calculate direction to player
            direction_to_player = pygame.math.Vector2(
                self.target_player.rect.centerx - self.rect.centerx,
                self.target_player.rect.centery - self.rect.centery
            )
            
            # Check if still in range
            if direction_to_player.length() > self.detection_range * 1.5:  # Stop chasing if too far
                self.state = "idle"
                self.target_player = None
                self.direction = pygame.math.Vector2(0, 0)
            else:
                # Normalize and move towards player
                if direction_to_player.length() > 0:
                    self.direction = direction_to_player.normalize()
                    
                    # Update facing direction
                    if self.direction.x > 0:
                        self.facing_right = True
                    elif self.direction.x < 0:
                        self.facing_right = False
                    
                    # Calculate movement with collision avoidance
                    if dt:
                        movement = self.direction * self.speed * dt
                        new_x = self.rect.centerx + movement.x
                        new_y = self.rect.centery + movement.y
                        
                        # Create temporary rect for collision testing
                        temp_rect = self.rect.copy()
                        temp_rect.centerx = new_x
                        temp_rect.centery = new_y
                        
                        # Check collision with other demons
                        collision_detected = False
                        if other_demons:
                            for other_demon in other_demons:
                                if other_demon != self and temp_rect.colliderect(other_demon.rect):
                                    collision_detected = True
                                    break
                        
                        # Only move if no collision
                        if not collision_detected:
                            self.rect.centerx = new_x
                            self.rect.centery = new_y
                            self.hitbox.center = self.rect.center
                        else:
                            # Try to move around the obstacle
                            # Try moving only horizontally
                            temp_rect = self.rect.copy()
                            temp_rect.centerx = new_x
                            horizontal_collision = False
                            if other_demons:
                                for other_demon in other_demons:
                                    if other_demon != self and temp_rect.colliderect(other_demon.rect):
                                        horizontal_collision = True
                                        break
                            
                            if not horizontal_collision:
                                self.rect.centerx = new_x
                                self.hitbox.centerx = self.rect.centerx
                            else:
                                # Try moving only vertically
                                temp_rect = self.rect.copy()
                                temp_rect.centery = new_y
                                vertical_collision = False
                                if other_demons:
                                    for other_demon in other_demons:
                                        if other_demon != self and temp_rect.colliderect(other_demon.rect):
                                            vertical_collision = True
                                            break
                                
                                if not vertical_collision:
                                    self.rect.centery = new_y
                                    self.hitbox.centery = self.rect.centery
        
        # Update animation using the new animation system
        self.update_animation(current_time)
            
    def set_facing_direction(self, facing_right):
        """Change the direction the demon is facing"""
        self.facing_right = facing_right
        
    def get_interaction_rect(self):
        """Get the area where player can interact with this demon"""
        return self.hitbox.inflate(40, 40)  # Larger area for interaction
