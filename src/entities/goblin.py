# src/entities/goblin.py
# Goblin enemy for Castle map - follows FireWorm pattern

import pygame
import os
from settings import *
from enemy import Enemy
from asset_manager import AssetManager
from goblin_bomb import GoblinBomb


class Goblin(Enemy):
    """
    Goblin enemy - fast, low HP melee attacker.
    Uses Attack3.png spritesheet (12 frames, 150x150 each).
    """
    def __init__(self, asset_path, pos_x, pos_y, scale_factor=1.0):
        # AssetManager instance (before super!)
        self.asset_manager = AssetManager()
        
        # Call parent constructor - this calls load_animations() and _rebuild_directional_frames()
        super().__init__(asset_path, pos_x, pos_y, scale_factor)
        
        # Goblin specific properties - fast but fragile (override parent values AFTER super)
        self.max_health = 100
        self.current_health = self.max_health
        self.speed = 130  # Faster than demon
        self.detection_range = 7 * 64  # 7 tiles = 448 pixels
        self.attack_range = 48  # Melee range
        self.attack_damage = 15
        self.attack_cooldown = 1200  # 1.2 seconds - quick attacks
        self._melee_inflate = (10, 8)
        
        # Animation
        self.animation_speed_ms = 150  # Fast animation
        
        # Bomb throwing
        self.bomb_range = 5 * 64  # 5 tiles = 320 pixels
        self.bomb_cooldown = 2500  # 2.5 seconds between throws
        self.last_bomb_time = 0
        self.fireballs = pygame.sprite.Group()  # Reuse 'fireballs' name for level.py compat
        
        # Path following state
        self._path: list[tuple[int, int]] = []
        self._path_idx: int = 0
        self._blocked_frames: int = 0
        
    def load_animations(self, asset_path):
        """Load goblin animations from spritesheet using AssetManager config"""
        if not os.path.exists(asset_path):
            print(f"⚠️ Goblin asset path not found: {asset_path}")
            return

        try:
            # Load all animations via config (following FireWorm pattern)
            self.idle_frames = self.asset_manager.load_entity_animation(
                'goblin', 'idle', asset_path, self.scale_factor
            )
            self.walk_frames = self.asset_manager.load_entity_animation(
                'goblin', 'walk', asset_path, self.scale_factor
            )
            self.attack_frames = self.asset_manager.load_entity_animation(
                'goblin', 'attack', asset_path, self.scale_factor
            )
            # No separate death spritesheet - use idle as fallback
            self.death_frames = self.idle_frames[:1] if self.idle_frames else []

            # Logging
            try:
                from core.settings import VERBOSE_LOGS
            except Exception:
                VERBOSE_LOGS = False
            if self.idle_frames and VERBOSE_LOGS:
                print(f"✅ Goblin loaded {len(self.idle_frames)} idle frames")
            if self.walk_frames and VERBOSE_LOGS:
                print(f"✅ Goblin loaded {len(self.walk_frames)} walk frames")
            if self.attack_frames and VERBOSE_LOGS:
                print(f"✅ Goblin loaded {len(self.attack_frames)} attack frames")

        except Exception as e:
            print(f"❌ Error loading goblin animations: {e}")
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
        """Goblin AI - ranged bomber that keeps distance from the player."""
        if not self.is_alive() or not player:
            return

        current_time = pygame.time.get_ticks()

        # Check player invisibility
        if hasattr(player, 'magic_system') and player.magic_system.is_invisible(player):
            if self.state != "idle":
                self.state = "idle"
            return

        # Calculate distance to player
        dir_to_player = pygame.math.Vector2(
            player.rect.centerx - self.rect.centerx,
            player.rect.centery - self.rect.centery
        )
        distance_to_player = dir_to_player.length()

        # Preferred distance: stay between keep_distance and bomb_range
        keep_distance = 180  # Don't get closer than ~3 tiles

        # State machine
        if distance_to_player <= self.detection_range:
            self.target_player = player

            if distance_to_player < keep_distance and dt:
                # Too close — retreat away from the player
                self.state = "walking"
                if dir_to_player.length() > 0:
                    retreat_dir = -dir_to_player.normalize()
                    if retreat_dir.x > 0:
                        self.facing_right = True
                    elif retreat_dir.x < 0:
                        self.facing_right = False
                    move = retreat_dir * self.speed * dt
                    new_center = pygame.math.Vector2(
                        self.rect.centerx + move.x,
                        self.rect.centery + move.y
                    )
                    trial_rect = self.hitbox.copy()
                    trial_rect.center = (round(new_center.x), round(new_center.y))
                    if not self.check_collision_with_obstacles(trial_rect):
                        self.rect.center = (round(new_center.x), round(new_center.y))
                        self.hitbox.center = self.rect.center
                # Still throw bombs while retreating
                if current_time - self.last_bomb_time >= self.bomb_cooldown:
                    if self.can_see_player(player):
                        self._throw_bomb(player)
                        self.last_bomb_time = current_time

            elif distance_to_player <= self.bomb_range:
                # In ideal range — hold position, throw bombs
                self.state = "idle"
                if dir_to_player.x > 0:
                    self.facing_right = True
                elif dir_to_player.x < 0:
                    self.facing_right = False
                if current_time - self.last_bomb_time >= self.bomb_cooldown:
                    if self.can_see_player(player):
                        self._throw_bomb(player)
                        self.last_bomb_time = current_time
            else:
                # Beyond bomb range but detected — approach until in range
                self.state = "walking"
                self._move_toward_player(dt, player, other_enemies)
        else:
            # Player not detected - idle
            if self.state != "attacking":
                self.state = "idle"
                self.target_player = None

    def _move_toward_player(self, dt, player, other_enemies):
        """Move toward player with pathfinding and wall sliding."""
        direction_to_player = pygame.math.Vector2(
            player.rect.centerx - self.rect.centerx,
            player.rect.centery - self.rect.centery
        )
        has_los = self.can_see_player(player)
        distance_to_player = direction_to_player.length()

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

    # ---------- Bomb throwing (follows FireWorm fireball pattern) ----------
    def _throw_bomb(self, player):
        """Throw a bomb at the player."""
        bomb_asset_path = os.path.join("assets", "Goblin")
        bomb = GoblinBomb(
            self.rect.centerx,
            self.rect.centery,
            player.rect.centerx,
            player.rect.centery,
            bomb_asset_path,
            0.5
        )
        self.fireballs.add(bomb)
        self.state = "attacking"
        print("💣 Goblin threw a bomb!")

    def update(self, dt=None, player=None, other_enemies=None):
        """Update Goblin and its bombs."""
        super().update(dt, player, other_enemies)
        # Update all bombs
        for bomb in self.fireballs.copy():
            bomb.update(dt, player)
            if bomb.should_remove():
                self.fireballs.remove(bomb)

    def draw_fireballs(self, screen, camera):
        """Draw all active bombs with camera transformation."""
        for bomb in self.fireballs:
            bomb_pos = camera.apply(bomb)
            screen.blit(bomb.image, bomb_pos)

    def get_fireballs(self):
        """Get all active bombs for collision checking."""
        return self.fireballs
