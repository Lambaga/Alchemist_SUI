# src/enemy_manager.py
# Manages all enemy types on the map

import pygame
from entities.demon import Demon
from entities.fireworm import FireWorm
from entities.skeleton import Skeleton
from entities.goblin import Goblin
from entities.castle_boss import CastleBoss
import os
from settings import ASSETS_DIR
from managers.settings_manager import SettingsManager

class EnemyManager:
    """Manages all enemies on the map"""
    
    def __init__(self):
        self.enemies = pygame.sprite.Group()
        self.demon_asset_path = os.path.join(ASSETS_DIR, "Demon Pack")
        self.fireworm_asset_path = os.path.join(ASSETS_DIR, "fireWorm")
        self.skeleton_asset_path = os.path.join(ASSETS_DIR, "Skeleton")
        self.goblin_asset_path = os.path.join(ASSETS_DIR, "Goblin")
        self.castle_boss_asset_path = os.path.join(ASSETS_DIR, "Skeleton")  # Boss uses Skeleton sprites
        self.pathfinder = None
        
        try:
            from core.settings import VERBOSE_LOGS
        except Exception:
            VERBOSE_LOGS = False
        if VERBOSE_LOGS:
            print(f"🔧 ENEMY MANAGER DEBUG:")
            print(f"   Demon path: {self.demon_asset_path} (exists: {os.path.exists(self.demon_asset_path)})")
            try:
                from core.settings import VERBOSE_LOGS
            except Exception:
                VERBOSE_LOGS = False  # type: ignore
            if VERBOSE_LOGS:  # type: ignore[name-defined]
                print(f"   FireWorm path: {self.fireworm_asset_path} (exists: {os.path.exists(self.fireworm_asset_path)})")
        
    def add_demon(self, x, y, scale=1.0, facing_right=True):
        """Add a demon at specified position"""
        demon = Demon(self.demon_asset_path, x, y, scale)
        demon.set_facing_direction(facing_right)
        # Set obstacle sprites if available
        if hasattr(self, 'obstacle_sprites') and self.obstacle_sprites:
            if hasattr(demon, 'set_obstacle_sprites'):
                demon.set_obstacle_sprites(self.obstacle_sprites)
        # Apply difficulty scaling
        try:
            self._apply_difficulty(demon)
        except Exception:
            pass
        self.enemies.add(demon)
        return demon
    
    def add_fireworm(self, x, y, scale=1.0, facing_right=True):
        """Add a fireworm at specified position"""
        fireworm = FireWorm(self.fireworm_asset_path, x, y, scale)
        fireworm.set_facing_direction(facing_right)
        # Set obstacle sprites if available
        if hasattr(self, 'obstacle_sprites') and self.obstacle_sprites:
            fireworm.set_obstacle_sprites(self.obstacle_sprites)
        # Apply difficulty scaling
        try:
            self._apply_difficulty(fireworm)
        except Exception:
            pass
        self.enemies.add(fireworm)
        return fireworm

    def add_skeleton(self, x, y, scale=1.0, facing_right=True):
        """Add a skeleton at specified position"""
        skeleton = Skeleton(self.skeleton_asset_path, x, y, scale)
        skeleton.set_facing_direction(facing_right)
        if hasattr(self, 'obstacle_sprites') and self.obstacle_sprites:
            if hasattr(skeleton, 'set_obstacle_sprites'):
                skeleton.set_obstacle_sprites(self.obstacle_sprites)
        try:
            self._apply_difficulty(skeleton)
        except Exception:
            pass
        self.enemies.add(skeleton)
        return skeleton

    def add_goblin(self, x, y, scale=1.0, facing_right=True):
        """Add a goblin at specified position"""
        goblin = Goblin(self.goblin_asset_path, x, y, scale)
        goblin.set_facing_direction(facing_right)
        if hasattr(self, 'obstacle_sprites') and self.obstacle_sprites:
            if hasattr(goblin, 'set_obstacle_sprites'):
                goblin.set_obstacle_sprites(self.obstacle_sprites)
        try:
            self._apply_difficulty(goblin)
        except Exception:
            pass
        self.enemies.add(goblin)
        return goblin

    def add_castle_boss(self, x, y, scale=1.0, facing_right=True):
        """Add a castle boss at specified position"""
        boss = CastleBoss(self.castle_boss_asset_path, x, y, scale)
        boss.set_facing_direction(facing_right)
        if hasattr(self, 'obstacle_sprites') and self.obstacle_sprites:
            if hasattr(boss, 'set_obstacle_sprites'):
                boss.set_obstacle_sprites(self.obstacle_sprites)
        try:
            self._apply_difficulty(boss)
        except Exception:
            pass
        self.enemies.add(boss)
        return boss
        
    def add_enemies_from_map(self, map_loader):
        """Spawn enemies from Tiled object layers: 'Enemy', 'Skeleton', 'Goblin', 'Boss'. Falls pytmx-Objekte nicht verfügbar sind, XML-Fallback."""
        try:
            from core.settings import VERBOSE_LOGS
        except Exception:
            VERBOSE_LOGS = False
        if VERBOSE_LOGS:
            print("🔍 START: add_enemies_from_map")
        if not map_loader or not getattr(map_loader, 'tmx_data', None):
            if VERBOSE_LOGS:
                print("⚠️ Kein MapLoader/TMX vorhanden")
            return

        enemy_count = 0
        pytmx_found = False

        # Mapping of object group names to spawn methods
        # Each entry: (group_name_lower, default_spawn_method, name_overrides)
        group_configs = [
            ('enemy', '_spawn_enemy_by_name'),
            ('skeleton', '_spawn_skeleton'),
            ('goblin', '_spawn_goblin'),
            ('boss', '_spawn_boss'),
        ]

        # 1) Bevorzugt: pytmx
        try:
            from pytmx import TiledObjectGroup
            for layer in map_loader.tmx_data.layers:
                layer_name = (getattr(layer, 'name', '') or '').lower()
                if not isinstance(layer, TiledObjectGroup):
                    continue
                
                for group_name, spawn_method in group_configs:
                    if layer_name == group_name:
                        for obj in layer:
                            x = float(getattr(obj, 'x', 0) or 0)
                            y = float(getattr(obj, 'y', 0) or 0)
                            name = (getattr(obj, 'name', '') or '').lower()
                            
                            spawned = getattr(self, spawn_method)(name, x, y, VERBOSE_LOGS)
                            if spawned:
                                enemy_count += 1
                                pytmx_found = True
        except Exception as e:
            if VERBOSE_LOGS:
                print(f"⚠️ PYTMX Spawn-Fehler: {e}")

        # 2) Fallback: Direktes XML (nur wenn pytmx nichts fand)
        if not pytmx_found:
            try:
                import xml.etree.ElementTree as ET
                map_path = getattr(map_loader, 'map_path', None)
                if not map_path:
                    if VERBOSE_LOGS:
                        print("⚠️ Kein map_path am MapLoader – XML-Fallback übersprungen")
                else:
                    tree = ET.parse(map_path)
                    root = tree.getroot()
                    if root is not None:
                        for objectgroup in root.findall('objectgroup'):
                            group_name_raw = (objectgroup.get('name') or '').lower()
                            for group_name, spawn_method in group_configs:
                                if group_name_raw == group_name:
                                    for obj in objectgroup.findall('object'):
                                        name = (obj.get('name', '') or '').lower()
                                        x = float(obj.get('x', 0) or 0)
                                        y = float(obj.get('y', 0) or 0)
                                        spawned = getattr(self, spawn_method)(name, x, y, VERBOSE_LOGS)
                                        if spawned:
                                            enemy_count += 1
            except Exception as e:
                if VERBOSE_LOGS:
                    print(f"❌ XML Fallback failed: {e}")

        if VERBOSE_LOGS:
            print(f"🎮 ENDE: {enemy_count} Gegner gespawnt (aktuell: {len(self.enemies)})")

    def _spawn_enemy_by_name(self, name, x, y, verbose=False):
        """Spawn enemy from 'Enemy' group based on object name"""
        if name in ('demon', 'enemy', 'monster', 'fireworm', 'skeleton', 'goblin', 'boss', ''):
            if verbose:
                print(f"✅ Enemy: {name or 'default'} @ ({x:.0f},{y:.0f})")
            if name == 'fireworm':
                self.add_fireworm(x, y, 2.0, True)
            elif name == 'skeleton':
                self.add_skeleton(x, y, 0.8, True)
            elif name == 'goblin':
                self.add_goblin(x, y, 0.8, True)
            elif name == 'boss':
                self.add_castle_boss(x, y, 2.0, True)
            else:
                self.add_demon(x, y, 2.0, True)
            return True
        return False

    def _spawn_skeleton(self, name, x, y, verbose=False):
        """Spawn skeleton from 'Skeleton' object group"""
        if verbose:
            print(f"✅ Skeleton @ ({x:.0f},{y:.0f})")
        self.add_skeleton(x, y, 0.8, True)
        return True

    def _spawn_goblin(self, name, x, y, verbose=False):
        """Spawn goblin from 'Goblin' object group"""
        if verbose:
            print(f"✅ Goblin @ ({x:.0f},{y:.0f})")
        self.add_goblin(x, y, 0.8, True)
        return True

    def _spawn_boss(self, name, x, y, verbose=False):
        """Spawn boss from 'Boss' object group (skip DragonLord – handled by Level)."""
        if name in ('dragonlord', 'dragon_lord', 'dragon lord', 'dragon'):
            if verbose:
                print(f"⏭️ DragonLord @ ({x:.0f},{y:.0f}) – übersprungen (Level-Spawner)")
            return False
        if verbose:
            print(f"✅ Castle Boss @ ({x:.0f},{y:.0f})")
        self.add_castle_boss(x, y, 2.0, True)
        return True

    # --- Difficulty management ---
    def _get_difficulty_multiplier(self) -> float:
        """Return HP scaling based on current difficulty setting."""
        try:
            diff = SettingsManager().get('difficulty', 'Normal')
        except Exception:
            diff = 'Normal'
        mapping = {
            'Leicht': 0.5,
            'Normal': 1.0,
            'Schwer': 2.0,
        }
        return mapping.get(diff, 1.0)

    def _apply_difficulty(self, enemy) -> None:
        """Apply HP scaling to a single enemy, preserving current HP percentage.

        Stores `base_max_health` on first application to avoid compounding.
        """
        mult = self._get_difficulty_multiplier()
        # Remember base (normal) max health once
        if not hasattr(enemy, 'base_max_health') or enemy.base_max_health is None:
            try:
                enemy.base_max_health = int(getattr(enemy, 'max_health', 100))
            except Exception:
                enemy.base_max_health = 100
        old_max = int(getattr(enemy, 'max_health', enemy.base_max_health) or enemy.base_max_health)
        base_max = int(getattr(enemy, 'base_max_health', old_max) or old_max)
        new_max = max(1, int(round(base_max * mult)))
        # Preserve health percentage relative to previous max
        old_den = max(1, old_max)
        cur = int(getattr(enemy, 'current_health', new_max) or new_max)
        pct = max(0.0, min(1.0, float(cur) / float(old_den)))
        enemy.max_health = new_max
        enemy.current_health = max(1, min(new_max, int(round(new_max * pct))))

    def apply_difficulty_to_all(self) -> None:
        """Reapply difficulty scaling to all existing enemies."""
        mult = self._get_difficulty_multiplier()
        for enemy in list(self.enemies):
            try:
                self._apply_difficulty(enemy)
            except Exception:
                continue

    def update(self, dt, player=None, companions=None):
        """Update all enemies with player reference for AI and collision detection.
        
        If companions are provided (e.g. KnightCompanion), each enemy
        targets whichever attackable entity is closest.
        """
        # Baue Liste der angreifbaren Ziele
        targets = []
        if player is not None:
            targets.append(player)
        if companions:
            for c in companions:
                if hasattr(c, 'is_alive') and c.is_alive():
                    targets.append(c)

        for enemy in self.enemies:
            other_enemies = [e for e in self.enemies if e != enemy]

            # Nächstes Ziel bestimmen
            chosen_target = player  # Fallback
            if len(targets) > 1:
                ecx = enemy.rect.centerx
                ecy = enemy.rect.centery
                best_dist = float('inf')
                for t in targets:
                    dx = t.rect.centerx - ecx
                    dy = t.rect.centery - ecy
                    d = dx * dx + dy * dy  # kein sqrt nötig zum Vergleichen
                    if d < best_dist:
                        best_dist = d
                        chosen_target = t

            enemy.update(dt, chosen_target, other_enemies)
        
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
            color = (255, 165, 0) if type(enemy).__name__ == "Demon" else \
                   (200, 200, 200) if type(enemy).__name__ == "Skeleton" else \
                   (0, 200, 0) if type(enemy).__name__ == "Goblin" else \
                   (180, 0, 180) if type(enemy).__name__ == "CastleBoss" else \
                   (255, 100, 0)  # Orange for demons, grey skeleton, green goblin, purple boss, red-orange fireworms
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

    def set_pathfinder(self, pathfinder):
        """Expose a shared pathfinder for enemies."""
        self.pathfinder = pathfinder
    
    def reset_enemies(self):
        """Setzt alle Feinde zurück (für Game Over / Neustart)"""
        # Alle aktuellen Feinde entfernen
        self.enemies.empty()
        try:
            from core.settings import VERBOSE_LOGS
        except Exception:
            VERBOSE_LOGS = False
        if VERBOSE_LOGS:
            print("🔄 Alle Feinde zurückgesetzt")
