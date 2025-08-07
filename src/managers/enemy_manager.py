# src/enemy_manager.py
# Manages all enemy types on the map

import pygame
from demon import Demon
from fireworm import FireWorm
import os

class EnemyManager:
    """Manages all enemies on the map"""
    
    def __init__(self):
        self.enemies = pygame.sprite.Group()
        self.demon_asset_path = os.path.join("assets", "Demon Pack")
        self.fireworm_asset_path = os.path.join("assets", "fireWorm")
        
    def add_demon(self, x, y, scale=1.0, facing_right=True):
        """Add a demon at specified position"""
        demon = Demon(self.demon_asset_path, x, y, scale)
        demon.set_facing_direction(facing_right)
        # Set obstacle sprites if available
        if hasattr(self, 'obstacle_sprites') and self.obstacle_sprites:
            if hasattr(demon, 'set_obstacle_sprites'):
                demon.set_obstacle_sprites(self.obstacle_sprites)
        self.enemies.add(demon)
        return demon
    
    def add_fireworm(self, x, y, scale=1.0, facing_right=True):
        """Add a fireworm at specified position"""
        fireworm = FireWorm(self.fireworm_asset_path, x, y, scale)
        fireworm.set_facing_direction(facing_right)
        # Set obstacle sprites if available
        if hasattr(self, 'obstacle_sprites') and self.obstacle_sprites:
            fireworm.set_obstacle_sprites(self.obstacle_sprites)
        self.enemies.add(fireworm)
        return fireworm
        
    def add_enemies_from_map(self, map_loader):
        """Add enemies based on map object layer"""
        if not map_loader or not map_loader.tmx_data:
            return
            
        # Look for enemy spawn points in Tiled map
        for layer in map_loader.tmx_data.visible_layers:
            if hasattr(layer, 'objects'):
                for obj in layer.objects:
                    if obj.name and obj.name.lower() in ['demon', 'monster', 'enemy']:
                        # Get scale from properties if available
                        scale = getattr(obj, 'scale', 1.0) if hasattr(obj, 'scale') else 1.0
                        
                        # Get facing direction from properties
                        facing_right = True
                        if hasattr(obj, 'properties') and 'facing' in obj.properties:
                            facing_right = obj.properties['facing'].lower() != 'left'
                            
                        # Get enemy type from properties
                        enemy_type = "demon"  # default
                        if hasattr(obj, 'properties') and 'type' in obj.properties:
                            enemy_type = obj.properties['type'].lower()
                        
                        if enemy_type == "fireworm":
                            enemy = self.add_fireworm(obj.x, obj.y, scale, facing_right)
                            print(f"🐍 FireWorm spawned at ({obj.x}, {obj.y})")
                        else:
                            enemy = self.add_demon(obj.x, obj.y, scale, facing_right)
                            print(f"👹 Demon spawned at ({obj.x}, {obj.y})")
                        
    def update(self, dt, player=None):
        """Update all enemies with player reference for AI and collision detection"""
        for enemy in self.enemies:
            # Pass other enemies for collision detection
            other_enemies = [e for e in self.enemies if e != enemy]
            enemy.update(dt, player, other_enemies)
        
    def draw(self, screen, camera):
        """Draw all enemies with camera transformation"""
        for enemy in self.enemies:
            enemy_pos = camera.apply(enemy)
            screen.blit(enemy.image, enemy_pos)
            
            # Draw fireballs if this is a FireWorm
            if hasattr(enemy, 'draw_fireballs'):
                enemy.draw_fireballs(screen, camera)
            
    def draw_debug(self, screen, camera):
        """Draw enemy hitboxes and detection ranges for debugging"""
        for enemy in self.enemies:
            # Enemy hitbox
            hitbox_transformed = camera.apply_rect(enemy.hitbox)
            color = (255, 165, 0) if type(enemy).__name__ == "Demon" else (255, 100, 0)  # Orange for demons, red-orange for fireworms
            pygame.draw.rect(screen, color, hitbox_transformed, 2)
            
            # Detection range circle
            enemy_center = camera.apply_rect(enemy.rect)
            detection_radius = int(enemy.detection_range * camera.zoom_factor)
            if detection_radius > 5:  # Only draw if visible
                pygame.draw.circle(screen, (255, 255, 0), 
                                 (enemy_center.centerx, enemy_center.centery), 
                                 detection_radius, 2)  # Yellow detection circle
            
            # State indicator
            if enemy.state in ["chasing", "walking"]:
                # Red line to target
                if hasattr(enemy, 'target_player') and enemy.target_player:
                    player_center = camera.apply_rect(enemy.target_player.rect)
                    pygame.draw.line(screen, (255, 0, 0), 
                                   (enemy_center.centerx, enemy_center.centery),
                                   (player_center.centerx, player_center.centery), 3)
            
            # Attack range for FireWorms
            if hasattr(enemy, 'attack_range'):
                attack_radius = int(enemy.attack_range * camera.zoom_factor)
                if attack_radius > 5:
                    pygame.draw.circle(screen, (255, 0, 0), 
                                     (enemy_center.centerx, enemy_center.centery), 
                                     attack_radius, 1)  # Red attack range circle
    
    def check_player_interactions(self, player):
        """Check if player is near any enemy for interaction"""
        interactions = []
        for enemy in self.enemies:
            interaction_rect = enemy.get_interaction_rect()
            if player.hitbox.colliderect(interaction_rect):
                interactions.append(enemy)
        return interactions
        
    def get_collision_sprites(self):
        """Get enemies as collision sprites if they should block movement"""
        return self.enemies
    
    def get_all_fireballs(self):
        """Get all fireballs from all FireWorms for collision checking"""
        all_fireballs = pygame.sprite.Group()
        for enemy in self.enemies:
            if hasattr(enemy, 'get_fireballs'):
                all_fireballs.add(enemy.get_fireballs())
        return all_fireballs
    
    def set_obstacle_sprites(self, obstacle_sprites):
        """Set obstacle sprites for all enemies"""
        self.obstacle_sprites = obstacle_sprites
        for enemy in self.enemies:
            if hasattr(enemy, 'set_obstacle_sprites'):
                enemy.set_obstacle_sprites(obstacle_sprites)
    
    def reset_enemies(self):
        """Setzt alle Feinde zurück (für Game Over / Neustart)"""
        # Alle aktuellen Feinde entfernen
        self.enemies.empty()
        print("🔄 Alle Feinde zurückgesetzt")
