# src/main_new.py
# Schlanke Hauptdatei nach Best Practices
import pygame
import sys
import os
from settings import *
from level import Level

class Game:
    """
    Zentrale Game-Klasse - Verwaltet Zuständen und Hauptschleife
    Vorbereitet für State Machine (Menu, Gameplay, Pause, etc.)
    """
    
    def __init__(self):
        # Pygame initialisieren
        pygame.init()
        pygame.mixer.init()
        
        # Display setup
        self.game_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption(GAME_TITLE)
        
        # Game systems
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Musik laden
        self.load_background_music()
        
        # Vorerst direkt das Level starten
        # Später: State Machine für Menu -> Level -> GameOver etc.
        # WICHTIG: Verwende WINDOW_Dimensionen für die Kamera, nicht SCREEN_
        self.current_state = Level(self.game_surface)
        
        print(f"🎮 {GAME_TITLE} gestartet!")
        print("🎯 Architektur: Zentrale Game-Klasse mit Level-System")
    
    def load_background_music(self):
        """Lädt und startet Hintergrundmusik"""
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(script_dir)
            music_path = os.path.join(project_root, BACKGROUND_MUSIC)
            
            pygame.mixer.music.load(music_path)
            pygame.mixer.music.set_volume(MUSIC_VOLUME)
            pygame.mixer.music.play(-1)  # Endlos-Schleife
            print(f"🎵 Musik gestartet: {music_path}")
        except Exception as e:
            print(f"⚠️ Musik-Fehler: {e}")
    
    def handle_events(self):
        """Zentrale Event-Behandlung"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == ACTION_KEYS['quit']:
                    self.running = False
                else:
                    # Event an aktuellen Zustand weiterleiten
                    self.current_state.handle_input(event)
            elif event.type == pygame.KEYUP:
                self.current_state.handle_input(event)
    
    def update(self, dt):
        """Update der Spiel-Logik"""
        # Aktueller Zustand wird geupdatet
        # Später: State-Transitions hier verwalten
        self.current_state.run(dt)
    
    def render(self):
        """Rendering-Pipeline"""
        # Game surface leeren
        self.game_surface.fill(BACKGROUND_COLOR)
        
        # Aktueller Zustand rendert direkt auf game_surface
        # (Das passiert bereits in Level.run() → Level.render())
        
        # Skalierung auf Display
        scaled_surface = pygame.transform.scale(self.game_surface, (WINDOW_WIDTH, WINDOW_HEIGHT))
        self.display_surface.blit(scaled_surface, (0, 0))
        
        # Debug-Info (optional)
        if DEBUG_MODE and SHOW_FPS:
            fps_text = f"FPS: {int(self.clock.get_fps())}"
            font = pygame.font.Font(None, 36)
            fps_surface = font.render(fps_text, True, (255, 255, 255))
            self.display_surface.blit(fps_surface, (10, 10))
        
        pygame.display.flip()
    
    def run(self):
        """Hauptschleife des Spiels"""
        print("🚀 Hauptschleife gestartet!")
        
        while self.running:
            # Delta time berechnen
            dt = self.clock.tick(FPS) / 1000.0  # In Sekunden
            
            # Game loop
            self.handle_events()
            self.update(dt)
            self.render()
        
        # Cleanup
        self.quit()
    
    def quit(self):
        """Spiel sauber beenden"""
        print("🏁 Spiel wird beendet...")
        pygame.quit()
        sys.exit()

# === ENTRY POINT ===
if __name__ == '__main__':
    # Sauberer Entry Point
    try:
        game = Game()
        game.run()
    except KeyboardInterrupt:
        print("\n🛑 Spiel durch Benutzer unterbrochen")
    except Exception as e:
        print(f"❌ Kritischer Fehler: {e}")
        import traceback
        traceback.print_exc()
    finally:
        pygame.quit()
        sys.exit()
