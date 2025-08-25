# src/demon.py
# Animated Demon NPC with idle animation

import pygame
import os
from settings import *
from enemy import Enemy
from asset_manager import AssetManager

class Demon(Enemy):
    """
    Animated demon NPC that inherits from Enemy base class.
    """
    def __init__(self, asset_path, pos_x, pos_y, scale_factor=1.0):
        """
        Initialize the demon.
        """
        # AssetManager instance
        self.asset_manager = AssetManager()
        
        # Call parent constructor
        super().__init__(asset_path, pos_x, pos_y, scale_factor)
        
        # Demon specific properties (override parent values)
        self.max_health = 200  # Erhöhte Health
        self.current_health = self.max_health  # Vollständige Health beim Start
        self.speed = 100  # Pixel per second
        self.detection_range = 8 * 64  # 8 tiles * 64 pixels per tile = 512 pixels (verkürzt von 15)
        
        # Animation specific to demon
        self.animation_speed_ms = 300  # Slower animation for demons
        
        # Additional demon frames (for run animation compatibility)
        self.run_frames = []
        
        # Initialize after setting up the additional frames
        self.load_animations(asset_path)
        
    def load_animations(self, asset_path):
        """Load demon animation frames using AssetManager with configuration"""
        if not os.path.exists(asset_path):
            print(f"⚠️ Demon asset path not found: {asset_path}")
            return
            
        try:
            # Versuche konfigurierte Animation-Ladung
            self.idle_frames = self.asset_manager.load_entity_animation(
                'demon', 'idle', asset_path, self.scale_factor
            )
            self.run_frames = self.asset_manager.load_entity_animation(
                'demon', 'run', asset_path, self.scale_factor
            )
            
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
            # Fallback zu leeren Listen, damit das Spiel nicht abstürzt
            if not self.idle_frames:
                self.idle_frames = [self.asset_manager._create_placeholder()]
            if not self.run_frames:
                self.run_frames = [self.asset_manager._create_placeholder()]
    
    def get_current_frames(self):
        """Get the current animation frames based on state"""
        if self.state in ["chasing", "walking"] and self.run_frames:
            return self.run_frames
        else:
            return self.idle_frames
    
    def update_ai(self, dt, player, other_enemies):
        """Demon AI logic"""
        if not player:
            return
            
        # Prüfe ob Spieler unsichtbar ist
        player_invisible = False
        if hasattr(player, 'magic_system') and player.magic_system.is_invisible(player):
            player_invisible = True
            # Unsichtbarer Spieler wird nicht verfolgt - stoppe Verfolgung
            if self.target_player is not None:
                self.state = "idle"
                self.target_player = None
                self.direction = pygame.math.Vector2(0, 0)
                print(f"👹 Demon verliert unsichtbaren Spieler aus den Augen!")
            return  # Früher Exit - keine weitere KI wenn Spieler unsichtbar
            
        # AI Logic: Check for player in detection range (nur wenn nicht unsichtbar)
        if self.target_player is None:
            distance_to_player = pygame.math.Vector2(
                player.rect.centerx - self.rect.centerx,
                player.rect.centery - self.rect.centery
            ).length()
            
            if distance_to_player <= self.detection_range:
                self.target_player = player
                self.state = "chasing"
                # Debug nur gelegentlich anzeigen um Spam zu vermeiden
                if hasattr(self, '_last_debug_time'):
                    current_time = pygame.time.get_ticks()
                    if current_time - self._last_debug_time > 3000:  # Alle 3 Sekunden
                        print(f"👹 Demon verfolgt Spieler - Distanz: {distance_to_player:.0f}")
                        self._last_debug_time = current_time
                else:
                    self._last_debug_time = pygame.time.get_ticks()
                    print(f"👹 Demon startet Verfolgung - Distanz: {distance_to_player:.0f}")
        
        # Movement AI
        if self.state == "chasing" and self.target_player:
            # Calculate direction to player
            direction_to_player = pygame.math.Vector2(
                self.target_player.rect.centerx - self.rect.centerx,
                self.target_player.rect.centery - self.rect.centery
            )
            
            # Check if still in range
            if direction_to_player.length() > self.detection_range * 1.2:  # Stop chasing if too far
                self.state = "idle"
                self.target_player = None
                self.direction = pygame.math.Vector2(0, 0)
                # Debug nur gelegentlich anzeigen
                print(f"👹 Demon stoppt Verfolgung - zu weit: {direction_to_player.length():.0f}")
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
                        if other_enemies:
                            for other_enemy in other_enemies:
                                if other_enemy != self and temp_rect.colliderect(other_enemy.rect):
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
                            if other_enemies:
                                for other_enemy in other_enemies:
                                    if other_enemy != self and temp_rect.colliderect(other_enemy.rect):
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
                                if other_enemies:
                                    for other_enemy in other_enemies:
                                        if other_enemy != self and temp_rect.colliderect(other_enemy.rect):
                                            vertical_collision = True
                                            break
                                
                                if not vertical_collision:
                                    self.rect.centery = new_y
                                    self.hitbox.centery = self.rect.centery
