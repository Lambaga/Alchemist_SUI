# src/entities/castle_boss.py
# Castle Boss enemy - final boss for Map3Castle

import pygame
import os
from settings import *
from enemy import Enemy
from asset_manager import AssetManager


class CastleBoss(Enemy):
    """
    Castle Boss - powerful final boss of the castle map.
    High HP, high damage, large detection range.
    Uses Skeleton Attack3.png spritesheet (scaled up).
    """
    def __init__(self, asset_path, pos_x, pos_y, scale_factor=1.0):
        self.asset_manager = AssetManager()
        
        # Call parent constructor (scale_factor larger for boss)
        super().__init__(asset_path, pos_x, pos_y, scale_factor * 1.5)
        
        # Boss specific properties - tanky and powerful
        self.max_health = 500
        self.current_health = self.max_health
        self.speed = 70  # Slow but dangerous
        self.detection_range = 10 * 64  # 10 tiles = 640 pixels
        self.attack_range = 64  # Slightly larger melee range
        self.attack_damage = 40  # Heavy hits
        self.attack_cooldown = 2000  # 2 seconds between attacks
        self._melee_inflate = (20, 16)
        
        # Animation
        self.animation_speed_ms = 350  # Slow, imposing animation
        self.run_frames = []
        
        # Boss flag
        self.is_boss = True
        
        # Load animations
        self.load_animations(asset_path)
        
        # Path following state
        self._path = []
        self._path_idx = 0
        self._blocked_frames = 0
        
    def load_animations(self, asset_path):
        """Load boss animations"""
        if not os.path.exists(asset_path):
            print(f"⚠️ CastleBoss asset path not found: {asset_path}")
            return
            
        try:
            self.idle_frames = self.asset_manager.load_entity_animation(
                'castle_boss', 'idle', asset_path, self.scale_factor
            )
            self.run_frames = self.asset_manager.load_entity_animation(
                'castle_boss', 'walk', asset_path, self.scale_factor
            )
            self.attack_frames = self.asset_manager.load_entity_animation(
                'castle_boss', 'attack', asset_path, self.scale_factor
            )
            
            if self.idle_frames:
                try:
                    from core.settings import VERBOSE_LOGS
                except Exception:
                    VERBOSE_LOGS = False
                if VERBOSE_LOGS:
                    print(f"✅ CastleBoss loaded {len(self.idle_frames)} idle frames")
            else:
                print(f"⚠️ No CastleBoss idle frames found in {asset_path}")
                
        except Exception as e:
            print(f"❌ Error loading CastleBoss animations: {e}")
            if not self.idle_frames:
                self.idle_frames = [self.asset_manager._create_placeholder(64, 64)]
            if not self.run_frames:
                self.run_frames = [self.asset_manager._create_placeholder(64, 64)]
    
    def get_current_frames(self):
        """Get the current animation frames based on state"""
        if self.state == "attacking" and self.attack_frames:
            return self.attack_frames
        elif self.state in ["chasing", "walking"] and self.run_frames:
            return self.run_frames
        return self.idle_frames
    
    def update_ai(self, dt, player, other_enemies):
        """Boss AI - aggressive melee with large detection"""
        if not player:
            return
            
        # Check player invisibility
        if hasattr(player, 'magic_system') and player.magic_system.is_invisible(player):
            if self.target_player is not None:
                self.state = "idle"
                self.target_player = None
                self.direction = pygame.math.Vector2(0, 0)
            return
            
        # Detect player
        if self.target_player is None:
            distance_to_player = pygame.math.Vector2(
                player.rect.centerx - self.rect.centerx,
                player.rect.centery - self.rect.centery
            ).length()
            if distance_to_player <= self.detection_range:
                self.target_player = player
                self.state = "chasing"
                print(f"💀 Castle Boss hat den Spieler entdeckt!")
        
        # Chase and attack
        if self.state == "chasing" and self.target_player:
            direction_to_player = pygame.math.Vector2(
                self.target_player.rect.centerx - self.rect.centerx,
                self.target_player.rect.centery - self.rect.centery
            )
            
            # Boss doesn't give up easily - wider range before losing interest
            if direction_to_player.length() > self.detection_range * 1.5:
                self.state = "idle"
                self.target_player = None
                self.direction = pygame.math.Vector2(0, 0)
            else:
                # Melee contact check
                player_rect = getattr(self.target_player, 'hitbox', self.target_player.rect)
                in_contact = self.hitbox.inflate(*self._melee_inflate).colliderect(player_rect)
                if in_contact and self.can_attack():
                    now = pygame.time.get_ticks()
                    if self.start_attack(now):
                        try:
                            dmg = self.attack_damage
                            if hasattr(self.target_player, 'take_damage'):
                                survived = self.target_player.take_damage(dmg)
                                if survived:
                                    print(f"💀 Castle Boss trifft für {dmg} Schaden!")
                                else:
                                    print("💀 Castle Boss hat den Spieler getötet!")
                        except Exception:
                            pass
                
                # Move toward player
                if direction_to_player.length() > 0 and dt:
                    self.direction = direction_to_player.normalize()
                    if self.direction.x > 0:
                        self.facing_right = True
                    elif self.direction.x < 0:
                        self.facing_right = False
                    
                    movement = self.direction * self.speed * dt
                    new_center = pygame.math.Vector2(
                        self.rect.centerx + movement.x,
                        self.rect.centery + movement.y
                    )
                    trial_rect = self.hitbox.copy()
                    trial_rect.center = (round(new_center.x), round(new_center.y))
                    
                    blocked = self.check_collision_with_obstacles(trial_rect)
                    if other_enemies and not blocked:
                        for other in other_enemies:
                            if other is not self and trial_rect.colliderect(other.hitbox):
                                blocked = True
                                break
                    
                    if not blocked:
                        self.rect.centerx = round(new_center.x)
                        self.rect.centery = round(new_center.y)
                        self.hitbox.center = self.rect.center
                        self._blocked_frames = 0
                    else:
                        self._blocked_frames += 1
                        # Slide along walls
                        hx = pygame.math.Vector2(self.rect.centerx + movement.x, self.rect.centery)
                        hrect = self.hitbox.copy()
                        hrect.center = (round(hx.x), round(hx.y))
                        if not self.check_collision_with_obstacles(hrect):
                            self.rect.centerx = round(hx.x)
                            self.hitbox.centerx = self.rect.centerx
                        
                        vy = pygame.math.Vector2(self.rect.centerx, self.rect.centery + movement.y)
                        vrect = self.hitbox.copy()
                        vrect.center = (round(vy.x), round(vy.y))
                        if not self.check_collision_with_obstacles(vrect):
                            self.rect.centery = round(vy.y)
                            self.hitbox.centery = self.rect.centery
