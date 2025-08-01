# src/demon_manager.py
# Manages multiple demons on the map

import pygame
from demon import Demon
import os

class DemonManager:
    """Manages all demons on the map"""
    
    def __init__(self):
        self.demons = pygame.sprite.Group()
        self.demon_asset_path = os.path.join("assets", "Demon Pack")
        
    def add_demon(self, x, y, scale=1.0, facing_right=True):
        """Add a demon at specified position"""
        demon = Demon(self.demon_asset_path, x, y, scale)
        demon.set_facing_direction(facing_right)
        self.demons.add(demon)
        return demon
        
    def add_demons_from_map(self, map_loader):
        """Add demons based on map object layer"""
        if not map_loader or not map_loader.tmx_data:
            return
            
        # Look for demon spawn points in Tiled map
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
                            
                        demon = self.add_demon(obj.x, obj.y, scale, facing_right)
                        print(f"👹 Demon spawned at ({obj.x}, {obj.y})")
                        
    def update(self, dt, player=None):
        """Update all demons with player reference for AI and collision detection"""
        for demon in self.demons:
            # Pass other demons for collision detection
            other_demons = [d for d in self.demons if d != demon]
            demon.update(dt, player, other_demons)
        
    def draw(self, screen, camera):
        """Draw all demons with camera transformation"""
        for demon in self.demons:
            demon_pos = camera.apply(demon)
            screen.blit(demon.image, demon_pos)
            
    def draw_debug(self, screen, camera):
        """Draw demon hitboxes and detection ranges for debugging"""
        for demon in self.demons:
            # Demon hitbox
            hitbox_transformed = camera.apply_rect(demon.hitbox)
            pygame.draw.rect(screen, (255, 165, 0), hitbox_transformed, 2)  # Orange for demons
            
            # Detection range circle
            demon_center = camera.apply_rect(demon.rect)
            detection_radius = int(demon.detection_range * camera.zoom_factor)
            if detection_radius > 5:  # Only draw if visible
                pygame.draw.circle(screen, (255, 255, 0), 
                                 (demon_center.centerx, demon_center.centery), 
                                 detection_radius, 2)  # Yellow detection circle
            
            # State indicator
            if demon.state == "chasing":
                # Red line to target
                if demon.target_player:
                    player_center = camera.apply_rect(demon.target_player.rect)
                    pygame.draw.line(screen, (255, 0, 0), 
                                   (demon_center.centerx, demon_center.centery),
                                   (player_center.centerx, player_center.centery), 3)
            
    def check_player_interactions(self, player):
        """Check if player is near any demon for interaction"""
        interactions = []
        for demon in self.demons:
            interaction_rect = demon.get_interaction_rect()
            if player.hitbox.colliderect(interaction_rect):
                interactions.append(demon)
        return interactions
        
    def get_collision_sprites(self):
        """Get demons as collision sprites if they should block movement"""
        return self.demons
