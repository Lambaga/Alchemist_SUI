# src/main.py
# Dies ist der Haupteinstiegspunkt des Spiels.
# Es initialisiert Pygame, erstellt das Fenster und startet die Spiel-Loop.

import pygame
from game import Game # Importiert unsere Game-Klasse aus game.py

# --- Konstanten und Konfiguration ---
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
FPS = 60
BACKGROUND_COLOR = (25, 25, 50) # Dunkelblau
TEXT_COLOR = (255, 255, 255) # Weiß

# Farben für die Zutaten-Platzhalter
ZUTATEN_FARBEN = {
    "wasserkristall": (0, 150, 255), # Blau
    "feueressenz": (255, 100, 0),   # Orange
    "erdkristall": (139, 69, 19)    # Braun
}

# --- Initialisierung ---
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Der Alchemist - Prototyp")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 50) # Standard-Schriftart für Text

# --- Spiel-Instanz erstellen ---
game = Game()
last_brew_result = "" # Speichert das letzte Brau-Ergebnis für die Anzeige

# --- Haupt-Spiel-Loop ---
running = True
while running:
    # 1. Event-Handling (Eingaben verarbeiten)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        # Tastatureingaben für die Simulation
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            # Zutat 1 hinzufügen
            elif event.key == pygame.K_1:
                game.add_zutat("wasserkristall")
            # Zutat 2 hinzufügen
            elif event.key == pygame.K_2:
                game.add_zutat("feueressenz")
            # Zutat 3 hinzufügen
            elif event.key == pygame.K_3:
                game.add_zutat("erdkristall")
            # Letzte Zutat entfernen
            elif event.key == pygame.K_BACKSPACE:
                game.remove_last_zutat()
            # Brauen auslösen
            elif event.key == pygame.K_SPACE:
                last_brew_result = game.brew()

    # 2. Spiel-Logik (wird hier hauptsächlich durch Events gesteuert)
    # (Hier könnten später Animationen etc. aktualisiert werden)

    # 3. Zeichnen (Rendering)
    # Hintergrund füllen
    screen.fill(BACKGROUND_COLOR)

    # UI-Elemente zeichnen
    # Titel für die Zutatenliste
    titel_surface = font.render("Aktive Zutaten:", True, TEXT_COLOR)
    screen.blit(titel_surface, (50, 50))

    # Zeichne für jede aktive Zutat ein farbiges Rechteck
    start_x = 50
    start_y = 120
    rect_width = 60
    rect_height = 60
    spacing = 20
    for i, zutat in enumerate(game.aktive_zutaten):
        farbe = ZUTATEN_FARBEN.get(zutat, (200, 200, 200)) # Grau für unbekannte Zutaten
        rect_x = start_x + i * (rect_width + spacing)
        pygame.draw.rect(screen, farbe, (rect_x, start_y, rect_width, rect_height))


    # Letztes Brau-Ergebnis als Text anzeigen
    ergebnis_text = f"Ergebnis: {last_brew_result}"
    ergebnis_surface = font.render(ergebnis_text, True, TEXT_COLOR)
    screen.blit(ergebnis_surface, (50, 220)) # Position angepasst
    
    # Steuerungshinweise anzeigen
    hilfe_text1 = "Steuerung: [1] Wasser, [2] Feuer, [3] Erde | [Backspace] Entfernen"
    hilfe_text2 = "[Leertaste] Brauen | [ESC] Beenden"
    hilfe_surface1 = font.render(hilfe_text1, True, TEXT_COLOR)
    hilfe_surface2 = font.render(hilfe_text2, True, TEXT_COLOR)
    screen.blit(hilfe_surface1, (50, SCREEN_HEIGHT - 150))
    screen.blit(hilfe_surface2, (50, SCREEN_HEIGHT - 90))


    # 4. Bildschirm aktualisieren
    pygame.display.flip()

    # Framerate begrenzen
    clock.tick(FPS)

# --- Spiel beenden ---
pygame.quit()
print("Spiel beendet.")

