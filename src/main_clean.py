# -*- coding: utf-8 -*-
# src/main.py
# Main game file

import pygame
import sys
import os
from settings import *
from level import Level

class Game:
    """
    Central Game class - manages states and main loop
    """
    
    def __init__(self):
        # Initialize Pygame
        pygame.init()
        pygame.mixer.init()
        
        # Display setup
        self.game_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption(GAME_TITLE)
        
        # Game clock
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Load background music
        self.load_background_music()
        
        # Start level directly
        # Later: State Machine for Menu -> Level -> GameOver etc.
        self.current_state = Level(self.game_surface)
        
        print(f"🎮 {GAME_TITLE} started!")
        print("🎯 Architecture: Central Game class with Level system")
    
    def load_background_music(self):
        """Load and start background music"""
        try:
            pygame.mixer.music.load(BACKGROUND_MUSIC)
            pygame.mixer.music.set_volume(MUSIC_VOLUME)
            pygame.mixer.music.play(-1)  # Endless loop
            print(f"🎵 Music started: {BACKGROUND_MUSIC}")
        except Exception as e:
            print(f"⚠️ Music error: {e}")
    
    def handle_events(self):
        """Handle global events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                # Pass events to current state
                if hasattr(self.current_state, 'handle_event'):
                    self.current_state.handle_event(event)
    
    def update(self):
        """Update game state"""
        dt = self.clock.tick(TARGET_FPS) / 1000.0  # Delta time in seconds
        
        if self.current_state:
            self.current_state.update(dt)
    
    def draw(self):
        """Draw everything"""
        if self.current_state:
            self.current_state.draw()
        
        pygame.display.flip()
    
    def run(self):
        """Main game loop"""
        print("🚀 Main loop started!")
        
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
        
        # Cleanup
        print("🏁 Game is shutting down...")
        pygame.quit()
        sys.exit()

def main():
    """Entry point"""
    print(f"🧙‍♂️ {GAME_TITLE} - Enhanced Version starting!")
    
    # Create and run game
    game = Game()
    game.run()

if __name__ == "__main__":
    main()
