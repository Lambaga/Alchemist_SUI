# src/fireworm.py
# FireWorm enemy class that inherits from Enemy

import pygame
import os
from enemy import Enemy
from fireball import Fireball
from asset_manager import AssetManager

class FireWorm(Enemy):
    """
    FireWorm enemy that can attack with fireballs
    """
    def __init__(self, asset_path, pos_x, pos_y, scale_factor=1.0):
        """
        Initialize the FireWorm.
        """
        # AssetManager instance
        self.asset_manager = AssetManager()
        
        # Call parent constructor
        super().__init__(asset_path, pos_x, pos_y, scale_factor)
        
        # FireWorm specific properties
        self.max_health = 200  # Erhöhte Health
        self.current_health = self.max_health  # Vollständige Health beim Start
        self.speed = 80  # Slightly slower than demon
        self.detection_range = 12 * 64  # 12 tiles detection range
        self.attack_range = 8 * 64  # 8 tiles attack range (longer range)
        self.attack_cooldown = 3000  # 3 seconds between attacks
        self.attack_damage = 30  # Fireball damage
        
        # Animation speed adjustments
        self.animation_speed_ms = 250  # Slightly slower animation
        
        # Fireball management
        self.fireballs = pygame.sprite.Group()
        
        # Collision detection
        self.obstacle_sprites = None
        
        print("🐍 FireWorm created at ({}, {})".format(pos_x, pos_y))
        
    def load_animations(self, asset_path):
        """Load FireWorm animation frames using AssetManager with configuration"""
        if not os.path.exists(asset_path):
            print(f"⚠️ FireWorm asset path not found: {asset_path}")
            return
            
        try:
            # Lade alle Animationen über die Konfiguration
            self.idle_frames = self.asset_manager.load_entity_animation(
                'fireworm', 'idle', asset_path, self.scale_factor
            )
            self.walk_frames = self.asset_manager.load_entity_animation(
                'fireworm', 'walk', asset_path, self.scale_factor
            )
            self.attack_frames = self.asset_manager.load_entity_animation(
                'fireworm', 'attack', asset_path, self.scale_factor
            )
            self.death_frames = self.asset_manager.load_entity_animation(
                'fireworm', 'death', asset_path, self.scale_factor
            )
            
            # Logging
            if self.idle_frames:
                print("✅ FireWorm loaded {} idle frames".format(len(self.idle_frames)))
            if self.walk_frames:
                print("✅ FireWorm loaded {} walk frames".format(len(self.walk_frames)))
            if self.attack_frames:
                print("✅ FireWorm loaded {} attack frames".format(len(self.attack_frames)))
            if self.death_frames:
                print("✅ FireWorm loaded {} death frames".format(len(self.death_frames)))
                
        except Exception as e:
            print("❌ Error loading FireWorm animations: {}".format(e))
            # Fallback zu Placeholdern
            placeholder = self.asset_manager._create_placeholder()
            if not self.idle_frames:
                self.idle_frames = [placeholder]
            if not self.walk_frames:
                self.walk_frames = [placeholder]
            if not self.attack_frames:
                self.attack_frames = [placeholder]
            if not self.death_frames:
                self.death_frames = [placeholder]
    
    def update_ai(self, dt, player, other_enemies):
        """FireWorm AI logic"""
        if not self.is_alive or not player:
            return
            
        current_time = pygame.time.get_ticks()
        
        # Prüfe ob Spieler unsichtbar ist
        player_invisible = False
        if hasattr(player, 'magic_system') and player.magic_system.is_invisible(player):
            player_invisible = True
            # Unsichtbarer Spieler wird nicht erkannt - gehe zu Idle
            if self.state != "idle":
                self.state = "idle"
                print(f"🐍 FireWorm verliert unsichtbaren Spieler aus den Augen!")
            return  # Früher Exit - keine weitere KI wenn Spieler unsichtbar
        
        # Calculate distance to player (nur wenn nicht unsichtbar)
        distance_to_player = pygame.math.Vector2(
            player.rect.centerx - self.rect.centerx,
            player.rect.centery - self.rect.centery
        ).length()
        
        # State machine
        if distance_to_player <= self.detection_range:
            # Player detected
            if distance_to_player <= self.attack_range and self.can_attack():
                # In attack range - shoot fireball
                self.start_attack(current_time)
                self.shoot_fireball(player)
            elif distance_to_player > self.attack_range:
                # Too far - move closer
                self.state = "walking"
                direction_to_player = pygame.math.Vector2(
                    player.rect.centerx - self.rect.centerx,
                    player.rect.centery - self.rect.centery
                )
                
                if direction_to_player.length() > 0:
                    self.direction = direction_to_player.normalize()
                    
                    # Update facing direction
                    if self.direction.x > 0:
                        self.facing_right = True
                    elif self.direction.x < 0:
                        self.facing_right = False
                    
                    # Move with collision detection
                    if dt:
                        movement = self.direction * self.speed * dt
                        
                        # Try horizontal movement first
                        old_x = self.rect.centerx
                        new_x = self.rect.centerx + movement.x
                        self.rect.centerx = new_x
                        self.hitbox.center = self.rect.center
                        
                        # Check collision with obstacles (walls)
                        if self.obstacle_sprites and self.check_collision_with_obstacles():
                            # Collision detected - revert horizontal movement
                            self.rect.centerx = old_x
                            self.hitbox.center = self.rect.center
                        
                        # Try vertical movement
                        old_y = self.rect.centery
                        new_y = self.rect.centery + movement.y
                        self.rect.centery = new_y
                        self.hitbox.center = self.rect.center
                        
                        # Check collision with obstacles (walls)
                        if self.obstacle_sprites and self.check_collision_with_obstacles():
                            # Collision detected - revert vertical movement
                            self.rect.centery = old_y
                            self.hitbox.center = self.rect.center
                        
                        # Check collision with other enemies
                        collision_detected = False
                        if other_enemies:
                            for other_enemy in other_enemies:
                                if other_enemy != self and self.rect.colliderect(other_enemy.rect):
                                    collision_detected = True
                                    # Push away from other enemy
                                    if self.rect.centerx < other_enemy.rect.centerx:
                                        self.rect.centerx -= 5
                                    else:
                                        self.rect.centerx += 5
                                    if self.rect.centery < other_enemy.rect.centery:
                                        self.rect.centery -= 5
                                    else:
                                        self.rect.centery += 5
                                    self.hitbox.center = self.rect.center
                                    break
        else:
            # Player not detected - idle
            if self.state != "attacking":
                self.state = "idle"
    
    def shoot_fireball(self, player):
        """Shoot a fireball at the player"""
        fireball_asset_path = os.path.join("assets", "fireWorm")
        fireball = Fireball(
            self.rect.centerx, 
            self.rect.centery,
            player.rect.centerx, 
            player.rect.centery,
            fireball_asset_path,
            0.5  # Smaller scale for fireball
        )
        self.fireballs.add(fireball)
        print("🔥 FireWorm shot fireball toward player!")
    
    def update(self, dt=None, player=None, other_enemies=None):
        """Update FireWorm and its fireballs"""
        # Update the enemy itself
        super().update(dt, player, other_enemies)
        
        # Update fireballs
        for fireball in self.fireballs.copy():
            fireball.update(dt, player)
            if fireball.should_remove():
                self.fireballs.remove(fireball)
    
    def draw_fireballs(self, screen, camera):
        """Draw all fireballs with camera transformation"""
        for fireball in self.fireballs:
            fireball_pos = camera.apply(fireball)
            screen.blit(fireball.image, fireball_pos)
    
    def get_fireballs(self):
        """Get all active fireballs for collision checking"""
        return self.fireballs
    
    def set_obstacle_sprites(self, obstacle_sprites):
        """Set the obstacle sprites for collision detection"""
        self.obstacle_sprites = obstacle_sprites
    
    def check_collision_with_obstacles(self):
        """Check if FireWorm collides with any obstacle"""
        if not self.obstacle_sprites:
            return False
            
        for obstacle in self.obstacle_sprites:
            if hasattr(obstacle, 'hitbox'):
                if self.hitbox.colliderect(obstacle.hitbox):
                    return True
            elif hasattr(obstacle, 'rect'):
                if self.hitbox.colliderect(obstacle.rect):
                    return True
            elif isinstance(obstacle, pygame.Rect):
                if self.hitbox.colliderect(obstacle):
                    return True
        return False
