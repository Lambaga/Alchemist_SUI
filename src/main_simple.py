# -*- coding: utf-8 -*-
# src/main_simple.py
# Simple main file without special characters

import pygame
import sys
import os
from settings import *
from level import Level

class Game:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        
        self.game_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption(GAME_TITLE)
        
        self.clock = pygame.time.Clock()
        self.running = True
        
        self.load_background_music()
        self.current_state = Level(self.game_surface)
        
        print("Game started!")
        print("Architecture: Central Game class with Level system")
    
    def load_background_music(self):
        try:
            pygame.mixer.music.load(BACKGROUND_MUSIC)
            pygame.mixer.music.set_volume(MUSIC_VOLUME)
            pygame.mixer.music.play(-1)
            print("Music started:", BACKGROUND_MUSIC)
        except Exception as e:
            print("Music error:", e)
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            # Pass all keyboard events to the current state
            if event.type in [pygame.KEYDOWN, pygame.KEYUP]:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.running = False
                
                if hasattr(self.current_state, 'handle_event'):
                    self.current_state.handle_event(event)
    
    def update(self):
        dt = self.clock.tick(FPS) / 1000.0
        if self.current_state:
            self.current_state.update(dt)
    
    def draw(self):
        if self.current_state:
            self.current_state.render()
        pygame.display.flip()
    
    def run(self):
        print("Main loop started!")
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
        
        print("Game is shutting down...")
        pygame.quit()
        sys.exit()

def main():
    print("The Alchemist - Enhanced Version starting!")
    game = Game()
    game.run()

if __name__ == "__main__":
    main()
