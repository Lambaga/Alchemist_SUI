# src/entities/skeleton.py
# Skeleton enemy for Castle map - follows FireWorm pattern

import pygame
import os
from settings import *
from enemy import Enemy
from asset_manager import AssetManager


class Skeleton(Enemy):
    """
    Skeleton enemy - melee fighter with sword.
    Uses Attack3.png spritesheet (6 frames, 150x150 each).
    """
    def __init__(self, asset_path, pos_x, pos_y, scale_factor=1.0):
        # AssetManager instance (before super!)
        self.asset_manager = AssetManager()
        
        # Call parent constructor - this calls load_animations() and _rebuild_directional_frames()
        super().__init__(asset_path, pos_x, pos_y, scale_factor)
        
        # Skeleton specific properties (override parent values AFTER super)
        self.max_health = 150
        self.current_health = self.max_health
        self.speed = 90
        self.detection_range = 6 * 64  # 6 tiles = 384 pixels
        self.attack_range = 48  # Melee range
        self.attack_damage = 20
        self.attack_cooldown = 1500  # 1.5 seconds
        self._melee_inflate = (12, 10)
        
        # Animation
        self.animation_speed_ms = 200
        
        # Path following state
        self._path: list[tuple[int, int]] = []
        self._path_idx: int = 0
        self._blocked_frames: int = 0
        
    def load_animations(self, asset_path):
        """Load skeleton animations from spritesheet using AssetManager config"""
        if not os.path.exists(asset_path):
            print(f"⚠️ Skeleton asset path not found: {asset_path}")
            return

        try:
            # Load all animations via config (following FireWorm pattern)
            self.idle_frames = self.asset_manager.load_entity_animation(
                'skeleton', 'idle', asset_path, self.scale_factor
            )
            self.walk_frames = self.asset_manager.load_entity_animation(
                'skeleton', 'walk', asset_path, self.scale_factor
            )
            self.attack_frames = self.asset_manager.load_entity_animation(
                'skeleton', 'attack', asset_path, self.scale_factor
            )
            # No separate death spritesheet - use idle as fallback
            self.death_frames = self.idle_frames[:1] if self.idle_frames else []

            # Logging
            try:
                from core.settings import VERBOSE_LOGS
            except Exception:
                VERBOSE_LOGS = False
            if self.idle_frames and VERBOSE_LOGS:
                print(f"✅ Skeleton loaded {len(self.idle_frames)} idle frames")
            if self.walk_frames and VERBOSE_LOGS:
                print(f"✅ Skeleton loaded {len(self.walk_frames)} walk frames")
            if self.attack_frames and VERBOSE_LOGS:
                print(f"✅ Skeleton loaded {len(self.attack_frames)} attack frames")

        except Exception as e:
            print(f"❌ Error loading skeleton animations: {e}")
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
        """Skeleton AI - melee chaser (follows FireWorm movement pattern)"""
        if not self.is_alive() or not player:
            return

        current_time = pygame.time.get_ticks()

        # Check player invisibility
        if hasattr(player, 'magic_system') and player.magic_system.is_invisible(player):
            if self.state != "idle":
                self.state = "idle"
            return

        # Calculate distance to player
        distance_to_player = pygame.math.Vector2(
            player.rect.centerx - self.rect.centerx,
            player.rect.centery - self.rect.centery
        ).length()

        # State machine
        if distance_to_player <= self.detection_range:
            # Player detected - check melee contact first
            player_rect = getattr(player, 'hitbox', player.rect)
            in_contact = self.hitbox.inflate(*self._melee_inflate).colliderect(player_rect)
            if in_contact and self.can_attack():
                if self.start_attack(current_time):
                    try:
                        if hasattr(player, 'take_damage'):
                            player.take_damage(self.attack_damage)
                    except Exception:
                        pass
            elif not in_contact:
                # Not in melee range - move closer
                self.state = "walking"
                self.target_player = player
                direction_to_player = pygame.math.Vector2(
                    player.rect.centerx - self.rect.centerx,
                    player.rect.centery - self.rect.centery
                )
                has_los = self.can_see_player(player)

                # Prefer following active path if available
                if dt and getattr(self, '_path', None) and self._path_idx < len(self._path):
                    wx, wy = self._path[self._path_idx]
                    to_wp = pygame.math.Vector2(wx - self.rect.centerx, wy - self.rect.centery)
                    if to_wp.length() < 12:
                        self._path_idx += 1
                    else:
                        step_dir = to_wp.normalize()
                        if step_dir.x > 0:
                            self.facing_right = True
                        elif step_dir.x < 0:
                            self.facing_right = False
                        move = step_dir * self.speed * dt
                        npos = pygame.math.Vector2(self.rect.centerx + move.x, self.rect.centery + move.y)
                        trect = self.hitbox.copy()
                        trect.center = (round(npos.x), round(npos.y))
                        if not self.check_collision_with_obstacles(trect):
                            self.rect.centerx = round(npos.x)
                            self.rect.centery = round(npos.y)
                            self.hitbox.center = self.rect.center
                        else:
                            self._path = []
                            self._path_idx = 0

                # If no path, move directly with wall avoidance
                if (not getattr(self, '_path', None)) or self._path_idx >= len(self._path):
                    if direction_to_player.length() > 0 and dt:
                        self.direction = direction_to_player.normalize()
                        if self.direction.x > 0:
                            self.facing_right = True
                        elif self.direction.x < 0:
                            self.facing_right = False

                        movement = self.direction * self.speed * dt

                        # Full move attempt
                        new_center = pygame.math.Vector2(
                            self.rect.centerx + movement.x,
                            self.rect.centery + movement.y
                        )
                        trial_rect = self.hitbox.copy()
                        trial_rect.center = (round(new_center.x), round(new_center.y))
                        blocked = self.check_collision_with_obstacles(trial_rect)
                        if other_enemies and not blocked:
                            for other_enemy in other_enemies:
                                if other_enemy != self and trial_rect.colliderect(other_enemy.hitbox):
                                    blocked = True
                                    break
                        if not blocked:
                            self.rect.centerx = round(new_center.x)
                            self.rect.centery = round(new_center.y)
                            self.hitbox.center = self.rect.center
                            self._blocked_frames = 0
                        else:
                            self._blocked_frames += 1
                            # Try axis-separated sliding
                            hx = pygame.math.Vector2(self.rect.centerx + movement.x, self.rect.centery)
                            hrect = self.hitbox.copy()
                            hrect.center = (round(hx.x), round(hx.y))
                            h_blocked = self.check_collision_with_obstacles(hrect)
                            if other_enemies and not h_blocked:
                                for other_enemy in other_enemies:
                                    if other_enemy != self and hrect.colliderect(other_enemy.hitbox):
                                        h_blocked = True
                                        break
                            vy = pygame.math.Vector2(self.rect.centerx, self.rect.centery + movement.y)
                            vrect = self.hitbox.copy()
                            vrect.center = (round(vy.x), round(vy.y))
                            v_blocked = self.check_collision_with_obstacles(vrect)
                            if other_enemies and not v_blocked:
                                for other_enemy in other_enemies:
                                    if other_enemy != self and vrect.colliderect(other_enemy.hitbox):
                                        v_blocked = True
                                        break
                            if not h_blocked:
                                self.rect.centerx = round(hx.x)
                                self.hitbox.centerx = self.rect.centerx
                            if not v_blocked:
                                self.rect.centery = round(vy.y)
                                self.hitbox.centery = self.rect.centery
                            # If blocked repeatedly, try pathfinding
                            pathfinder = None
                            try:
                                level_ref = getattr(player, '_level_ref', None)
                                if level_ref and hasattr(level_ref, 'pathfinder'):
                                    pathfinder = level_ref.pathfinder
                            except Exception:
                                pathfinder = None
                            if pathfinder and (self._blocked_frames >= 4 or not has_los):
                                sx, sy = self.rect.centerx, self.rect.centery
                                tx, ty = player.rect.centerx, player.rect.centery
                                path = pathfinder.find_path((sx, sy), (tx, ty), max_closed=4000)
                                if len(path) >= 2:
                                    self._path = path[1:]
                                    self._path_idx = 0
                                    self._blocked_frames = 0

                # Clear path if LOS regained and close
                if has_los and distance_to_player < 160:
                    self._path = []
                    self._path_idx = 0
        else:
            # Player not detected - idle
            if self.state != "attacking":
                self.state = "idle"
                self.target_player = None
