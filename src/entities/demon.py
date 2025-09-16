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
        # Path following state
        self._path: list[tuple[int, int]] = []
        self._path_idx: int = 0
        self._blocked_frames: int = 0
        
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
            
        # AI Logic: Check for player in detection range (LOS not required for acquisition)
        if self.target_player is None:
            distance_to_player = pygame.math.Vector2(
                player.rect.centerx - self.rect.centerx,
                player.rect.centery - self.rect.centery
            ).length()
            # Acquire target purely by distance to preserve original trigger range
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
                has_los = self.can_see_player(self.target_player)
                # If we already have a computed path, prefer following it
                if dt and getattr(self, '_path', None) and self._path_idx < len(self._path):
                    wx, wy = self._path[self._path_idx]
                    to_wp = pygame.math.Vector2(wx - self.rect.centerx, wy - self.rect.centery)
                    if to_wp.length() < 12:
                        self._path_idx += 1
                    else:
                        step_dir = to_wp.normalize()
                        # Update facing for animation
                        if step_dir.x > 0:
                            self.facing_right = True
                        elif step_dir.x < 0:
                            self.facing_right = False
                        move = step_dir * self.speed * dt
                        npos = pygame.math.Vector2(self.rect.centerx + move.x, self.rect.centery + move.y)
                        trect = self.hitbox.copy(); trect.center = npos
                        if not self.check_collision_with_obstacles(trect):
                            self.rect.centerx = round(npos.x)
                            self.rect.centery = round(npos.y)
                            self.hitbox.center = self.rect.center
                        else:
                            # Path became invalid; drop it and try recompute below
                            self._path = []
                            self._path_idx = 0

                # If no path active, do direct chase with wall avoidance
                if (not getattr(self, '_path', None)) or self._path_idx >= len(self._path):
                    if direction_to_player.length() > 0:
                        self.direction = direction_to_player.normalize()
                        # Update facing direction
                        if self.direction.x > 0:
                            self.facing_right = True
                        elif self.direction.x < 0:
                            self.facing_right = False
                        if dt:
                            movement = self.direction * self.speed * dt
                        # Attempt move with wall + enemy collision constraints
                        # First try full move
                        new_center = pygame.math.Vector2(self.rect.centerx + movement.x,
                                                         self.rect.centery + movement.y)
                        trial_rect = self.hitbox.copy()
                        trial_rect.center = new_center
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
                            # Try axis-separated moves to slide along walls
                            # Horizontal only
                            hx = pygame.math.Vector2(self.rect.centerx + movement.x, self.rect.centery)
                            hrect = self.hitbox.copy(); hrect.center = hx
                            h_blocked = self.check_collision_with_obstacles(hrect)
                            if other_enemies and not h_blocked:
                                for other in other_enemies:
                                    if other is not self and hrect.colliderect(other.hitbox):
                                        h_blocked = True
                                        break

                            # Vertical only
                            vy = pygame.math.Vector2(self.rect.centerx, self.rect.centery + movement.y)
                            vrect = self.hitbox.copy(); vrect.center = vy
                            v_blocked = self.check_collision_with_obstacles(vrect)
                            if other_enemies and not v_blocked:
                                for other in other_enemies:
                                    if other is not self and vrect.colliderect(other.hitbox):
                                        v_blocked = True
                                        break

                            # Prefer unblocked axis to allow sliding
                            if not h_blocked:
                                self.rect.centerx = round(hx.x)
                                self.hitbox.centerx = self.rect.centerx
                            if not v_blocked:
                                self.rect.centery = round(vy.y)
                                self.hitbox.centery = self.rect.centery

                            # If repeatedly blocked or LOS blocked, try pathfinding around obstacles
                            try:
                                from core.level import Level  # type: ignore
                            except Exception:
                                Level = None  # noqa
                            # Access shared pathfinder via enemy manager if available
                            pathfinder = None
                            try:
                                # EnemyManager attaches itself as owner of our group; walk up via groups not trivial.
                                # Instead, look for a global reference on player/level if target_player has _level_ref.
                                level_ref = getattr(self.target_player, '_level_ref', None)
                                if level_ref and hasattr(level_ref, 'pathfinder'):
                                    pathfinder = level_ref.pathfinder
                            except Exception:
                                pathfinder = None

                            if pathfinder and (self._blocked_frames >= 4 or not has_los):
                                sx, sy = self.rect.centerx, self.rect.centery
                                tx, ty = self.target_player.rect.centerx, self.target_player.rect.centery
                                path = pathfinder.find_path((sx, sy), (tx, ty), max_closed=4000)
                                # Keep short, drop starting cell
                                if len(path) >= 2:
                                    self._path = path[1:]
                                    self._path_idx = 0
                                    self._blocked_frames = 0
                # Clear path if close and LOS regained
                if has_los and direction_to_player.length() < 160:
                    self._path = []
                    self._path_idx = 0
