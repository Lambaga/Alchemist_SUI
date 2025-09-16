# src/enemy_manager.py
# Manages all enemy types on the map

import pygame
from demon import Demon
from fireworm import FireWorm
import os
from settings import ASSETS_DIR

class EnemyManager:
    """Manages all enemies on the map"""
    
    def __init__(self):
        self.enemies = pygame.sprite.Group()
        self.demon_asset_path = os.path.join(ASSETS_DIR, "Demon Pack")
        self.fireworm_asset_path = os.path.join(ASSETS_DIR, "fireWorm")
        
        print(f"🔧 ENEMY MANAGER DEBUG:")
        print(f"   Demon path: {self.demon_asset_path} (exists: {os.path.exists(self.demon_asset_path)})")
        print(f"   FireWorm path: {self.fireworm_asset_path} (exists: {os.path.exists(self.fireworm_asset_path)})")
        
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
        """Spawn enemies from Tiled object layer 'Enemy' (name: demon/fireworm). Falls pytmx-Objekte nicht verfügbar sind, XML-Fallback."""
        print("🔍 START: add_enemies_from_map")
        if not map_loader or not getattr(map_loader, 'tmx_data', None):
            print("⚠️ Kein MapLoader/TMX vorhanden")
            return

        enemy_count = 0
        pytmx_found = False

        # 1) Bevorzugt: pytmx – nur ObjectGroup 'Enemy'
        try:
            for layer in map_loader.tmx_data.layers:
                if getattr(layer, 'name', '') and layer.name.lower() == 'enemy' and hasattr(layer, 'objects'):
                    for obj in layer.objects:
                        name = (getattr(obj, 'name', '') or '').lower()
                        x = float(getattr(obj, 'x', 0) or 0)
                        y = float(getattr(obj, 'y', 0) or 0)
                        if name in ('demon', 'enemy', 'monster', 'fireworm'):
                            print(f"✅ PYTMX: {name} @ ({x:.0f},{y:.0f})")
                            if name == 'fireworm':
                                self.add_fireworm(x, y, 2.0, True)
                            else:
                                self.add_demon(x, y, 2.0, True)
                            enemy_count += 1
                            pytmx_found = True
        except Exception as e:
            print(f"⚠️ PYTMX Spawn-Fehler: {e}")

        # 2) Fallback: Direktes XML für aktuelle Map (nur wenn pytmx nichts fand)
        if not pytmx_found:
            try:
                import xml.etree.ElementTree as ET
                map_path = getattr(map_loader, 'map_path', None)
                if not map_path:
                    print("⚠️ Kein map_path am MapLoader – XML-Fallback übersprungen")
                else:
                    tree = ET.parse(map_path)
                    root = tree.getroot()
                    if root is not None:
                        for objectgroup in root.findall('objectgroup'):
                            if (objectgroup.get('name') or '').lower() == 'enemy':
                                for obj in objectgroup.findall('object'):
                                    name = (obj.get('name', '') or '').lower()
                                    x = float(obj.get('x', 0) or 0)
                                    y = float(obj.get('y', 0) or 0)
                                    if name in ('demon', 'enemy', 'monster', 'fireworm'):
                                        print(f"✅ XML: {name} @ ({x:.0f},{y:.0f})")
                                        if name == 'fireworm':
                                            self.add_fireworm(x, y, 2.0, True)
                                        else:
                                            self.add_demon(x, y, 2.0, True)
                                        enemy_count += 1
            except Exception as e:
                print(f"❌ XML Fallback failed: {e}")

        print(f"🎮 ENDE: {enemy_count} Gegner gespawnt (aktuell: {len(self.enemies)})")

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
