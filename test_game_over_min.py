#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Minimal test: ensure Level.update() returns "game_over" when player health <= 0
"""
import os
import sys
import pygame

# Ensure src on path
ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, 'src')
for p in [SRC, os.path.join(SRC, 'core'), os.path.join(SRC, 'entities'), os.path.join(SRC, 'systems'), os.path.join(SRC, 'world'), os.path.join(SRC, 'managers'), os.path.join(SRC, 'ui')]:
    if p not in sys.path:
        sys.path.insert(0, p)

from core.settings import SCREEN_WIDTH, SCREEN_HEIGHT
from core.level import Level

pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Game Over Test")

level = Level(screen)
# Force HP to zero
level.game_logic.player.current_health = 0

result = level.update(0.016)
print("RESULT:", result)

pygame.quit()
