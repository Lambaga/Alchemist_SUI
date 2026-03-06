# src/entities/goblin_bomb.py
# Goblin bomb projectile - follows Fireball pattern

import pygame
import os
from settings import *
from asset_manager import AssetManager


class GoblinBomb(pygame.sprite.Sprite):
    """
    Bomb projectile thrown by Goblin toward the player.
    Uses Bomb_sprite.png (19 frames, 100x100 each).
    Flies toward target, explodes on contact dealing 20 damage.
    """

    FRAME_COUNT = 19
    FRAME_SIZE = 100  # 1900 / 19
    SPEED = 180  # px/s
    DAMAGE = 20
    EXPLOSION_DURATION = 400  # ms
    ANIMATION_SPEED = 80  # ms per frame (fast spin)
    MAX_FLIGHT_DISTANCE = 320  # px (~5 tiles) - bomb lands if it doesn't hit

    def __init__(self, start_x, start_y, target_x, target_y, asset_path, scale_factor=0.5):
        super().__init__()

        self.asset_manager = AssetManager()
        self.scale_factor = scale_factor
        self.is_alive = True
        self.state = "moving"  # "moving" or "exploding"

        # Animation
        self.current_frame_index = 0
        self.last_update_time = pygame.time.get_ticks()

        # Movement direction
        direction = pygame.math.Vector2(target_x - start_x, target_y - start_y)
        if direction.length() > 0:
            direction = direction.normalize()
        self.direction = direction
        
        # Track flight distance
        self.start_pos = pygame.math.Vector2(start_x, start_y)
        self.distance_traveled = 0.0

        # Load frames
        self.move_frames = []
        self.explosion_frames = []
        self._load_bomb_sprite(asset_path)

        # Set initial image and position
        self.image = self.move_frames[0] if self.move_frames else self._create_placeholder()
        self.rect = self.image.get_rect(center=(start_x, start_y))
        self.hitbox = self.rect.inflate(-6, -6)

        # Explosion timer
        self.explosion_timer = 0

    # ------------------------------------------------------------------
    def _load_bomb_sprite(self, asset_path):
        """Cut Bomb_sprite.png into individual frames."""
        bomb_path = os.path.join(asset_path, "Bomb_sprite.png")
        if not os.path.exists(bomb_path):
            print(f"⚠️ Bomb sprite not found: {bomb_path}")
            self.move_frames = [self._create_placeholder()]
            self.explosion_frames = [self._create_explosion_placeholder()]
            return

        try:
            sheet = self.asset_manager.load_image(bomb_path)
            sheet_w = sheet.get_width()
            sheet_h = sheet.get_height()
            fw = sheet_w // self.FRAME_COUNT  # Should be 100
            fh = sheet_h  # 100

            for i in range(self.FRAME_COUNT):
                sub = sheet.subsurface(pygame.Rect(i * fw, 0, fw, fh))
                if self.scale_factor != 1.0:
                    new_w = max(1, int(fw * self.scale_factor))
                    new_h = max(1, int(fh * self.scale_factor))
                    sub = pygame.transform.scale(sub, (new_w, new_h))
                self.move_frames.append(sub)

            # Last few frames serve as explosion (frames 15-18 look like impact)
            self.explosion_frames = self.move_frames[-4:] if len(self.move_frames) >= 4 else self.move_frames[-1:]

            try:
                from core.settings import VERBOSE_LOGS
            except Exception:
                VERBOSE_LOGS = False
            if VERBOSE_LOGS:
                print(f"✅ GoblinBomb loaded {len(self.move_frames)} frames ({fw}x{fh} → scale {self.scale_factor})")

        except Exception as e:
            print(f"❌ Error loading bomb sprite: {e}")
            self.move_frames = [self._create_placeholder()]
            self.explosion_frames = [self._create_explosion_placeholder()]

    # ------------------------------------------------------------------
    @staticmethod
    def _create_placeholder():
        s = pygame.Surface((24, 24), pygame.SRCALPHA)
        pygame.draw.circle(s, (60, 60, 60), (12, 12), 11)
        pygame.draw.circle(s, (200, 50, 0), (12, 6), 4)
        return s

    @staticmethod
    def _create_explosion_placeholder():
        s = pygame.Surface((36, 36), pygame.SRCALPHA)
        pygame.draw.circle(s, (255, 160, 0), (18, 18), 17)
        pygame.draw.circle(s, (255, 255, 80), (18, 18), 9)
        return s

    # ------------------------------------------------------------------
    def explode(self):
        if self.state != "exploding":
            self.state = "exploding"
            self.current_frame_index = 0
            self.explosion_timer = pygame.time.get_ticks()

    def update(self, dt=None, player=None):
        current_time = pygame.time.get_ticks()

        if self.state == "moving":
            if dt:
                movement = self.direction * self.SPEED * dt
                self.rect.centerx += round(movement.x)
                self.rect.centery += round(movement.y)
                self.hitbox.center = self.rect.center
                self.distance_traveled += movement.length()

                # Hit player?
                if player:
                    player_hb = getattr(player, 'hitbox', player.rect)
                    if self.hitbox.colliderect(player_hb):
                        self.explode()
                        try:
                            if hasattr(player, 'take_damage'):
                                player.take_damage(self.DAMAGE)
                                print(f"💣 Goblin bomb hit player for {self.DAMAGE} damage!")
                        except Exception:
                            pass

                # Bomb lands after max flight distance
                if self.distance_traveled >= self.MAX_FLIGHT_DISTANCE:
                    self.explode()

        elif self.state == "exploding":
            if current_time - self.explosion_timer >= self.EXPLOSION_DURATION:
                self.is_alive = False

        # Animate
        frames = self.explosion_frames if self.state == "exploding" else self.move_frames
        if frames and current_time - self.last_update_time >= self.ANIMATION_SPEED:
            self.current_frame_index = (self.current_frame_index + 1) % len(frames)
            self.image = frames[self.current_frame_index]
            self.last_update_time = current_time

    def should_remove(self):
        return not self.is_alive
