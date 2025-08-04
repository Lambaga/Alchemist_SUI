# -*- coding: utf-8 -*-
# src/game.py
# Erweiterte Alchemist-Spiel Logik mit animiertem Spieler

import pygame
from os import path
from player import Player
from settings import *

class Game:
    """
    Erweiterte Spiellogik mit Spieler-Bewegung und NFC-Token System
    """
    
    def __init__(self):
        print("🧙‍♂️ Der Alchemist - Erweiterte Version startet!")
        
        # Pygame muss initialisiert sein für die Player-Klasse
        if not pygame.get_init():
            pygame.init()
        
        # Spieler erstellen (mit Multi-Animation System)
        # Versuche zuerst das Wizard Pack, dann Fallbacks
        sprite_paths = [
            SPRITES_DIR,  # Absoluter Pfad aus settings.py
            path.join(ASSETS_DIR, "wizard_char.png"),
            path.join(ASSETS_DIR, "wizard_char_demo.png")
        ]
        
        player_created = False
        # Player in der Mitte der Game-Surface platzieren
        start_x, start_y = PLAYER_START_POS  # Verwende Settings-Konstante
        for asset_path in sprite_paths:
            try:
                self.player = Player(asset_path, start_x, start_y)
                # Prüfen, ob der Player tatsächlich ein Bild hat
                if self.player.image.get_width() > 1: # Placeholder ist 1x1
                    player_created = True
                    print("✅ Spieler erfolgreich erstellt mit: {}".format(asset_path))
                    break
                else:
                    print("⚠️ Spieler mit Pfad '{}' erstellt, aber nur als Platzhalter.".format(asset_path))
            except Exception as e:
                print("❌ Fehler beim Erstellen des Spielers mit Pfad '{}': {}".format(asset_path, e))
                continue
        
        if not player_created:
            # Letzter Fallback: Player ohne Spritesheet
            self.player = Player("", start_x, start_y)
            print("⚠️ Kritisch: Spieler konnte nur als leerer Platzhalter erstellt werden.")
        
        # Aktive Zutaten für das Brauen (werden durch NFC-Tokens hinzugefügt)
        self.aktive_zutaten = []
        
        # KEINE Zutaten in der Welt - diese werden durch NFC-Tokens ersetzt
        # self.world_zutaten = []  # Entfernt!
        
        # Rezeptbuch
        self.rezepte = {
            ("wasserkristall", "wasserkristall"): "💧 Feuer gelöscht! Ein starker Wasserzauber.",
            ("feueressenz", "wasserkristall"): "❤️ Heiltrank gebraut! Lebenspunkte wiederhergestellt.",
            ("erdkristall", "feueressenz"): "💥 Explosion! Das war die falsche Mischung.",
            ("wasserkristall", "erdkristall"): "🌱 Wachstumstrank! Pflanzen sprießen.",
            ("feueressenz", "feueressenz"): "🔥 Feuerball! Mächtiger Angriffszauber.",
            ("erdkristall", "erdkristall"): "🏔️ Steinwall! Schutz vor Angriffen."
        } 
        #Wasser
        #Erde
        #Feuer

        #Feuer+Feuer = Feuerball
        #Wasser+Wasser= Wasserball
        #Feuer+Wasser=  Heiltrank
        #Erde+Feuer= Area Damage
        #Erde+Erde= Schutz für 3 Sekunden
        #Erde+Wasser= Verlangsamt Gegner?
        
        # Spielstatus
        self.last_brew_result = "Spiel gestartet"
        self.score = 0
        
        
    def update(self, dt=None, collision_objects=None):
        """Update-Schleife mit Delta Time - aktualisiert Spieler-Animation"""
        # Aktualisiere nur die Animation, Bewegung wird separat behandelt
        self.player.update(dt)
    
    def move_player_with_collision(self, dt, direction_vector, collision_objects):
        """Bewegt den Spieler mit der neuen dt-basierten Bewegung und Kollisionserkennung"""
        # Setze die Bewegungsrichtung
        self.player.direction = direction_vector
        
        # Verwende die neue move-Methode mit dt
        self.player.move(dt)
        
        # Falls zusätzliche Kollisionsobjekte vorhanden sind, überprüfe diese auch
        if collision_objects:
            # Setze die obstacle_sprites für die Kollisionserkennung
            self.player.set_obstacle_sprites(collision_objects)

    def add_zutat(self, zutat_name):
        """Fügt eine Zutat zur Brau-Liste hinzu (normalerweise durch NFC-Token)"""
        if len(self.aktive_zutaten) < 5:  # Maximal 5 Zutaten
            self.aktive_zutaten.append(zutat_name)
            print("🎯 NFC-Token erkannt: {} | Alchemisten-Feld: {}".format(zutat_name, self.aktive_zutaten))
        else:
            print("🚫 Alchemisten-Feld voll! Maximal 5 Zutaten.")

    def remove_last_zutat(self):
        """Entfernt die zuletzt hinzugefügte Zutat"""
        if self.aktive_zutaten:
            entfernte_zutat = self.aktive_zutaten.pop()
            print("➖ Zutat entfernt: {} | Alchemisten-Feld: {}".format(entfernte_zutat, self.aktive_zutaten))
        else:
            print("📭 Keine Zutaten zum Entfernen.")
            
    def brew(self):
        """Braut einen Trank aus den aktiven Zutaten"""
        if not self.aktive_zutaten:
            result = "🤷‍♂️ Nichts zum Brauen da."
            self.last_brew_result = "Rezept erfolgreich gebraut: {}".format(result)
            return result

        # Zutaten sortieren für Rezept-Lookup
        rezept_schluessel = tuple(sorted(self.aktive_zutaten))
        
        # Rezept suchen
        ergebnis = self.rezepte.get(rezept_schluessel, "❓ Unbekanntes Rezept. Nichts passiert.")
        
        if ergebnis != "❓ Unbekanntes Rezept. Nichts passiert.":
            self.score += 50  # Bonus für erfolgreiches Brauen
        
        print("🧪 Brauen: {} → {}".format(self.aktive_zutaten, ergebnis))
        print("📊 Aktuelle Punkte: {}".format(self.score))

        # Feld nach Brauen leeren
        self.aktive_zutaten.clear()
        self.last_brew_result = ergebnis
        
        return ergebnis
        
    def reset_game(self):
        """Setzt das Spiel zurück"""
        self.aktive_zutaten.clear()
        self.player.rect.centerx = PLAYER_START_POS[0]  # Verwende rect für Position
        self.player.rect.centery = PLAYER_START_POS[1]
        self.player.position = pygame.math.Vector2(self.player.rect.center)  # Synchronisiere Float-Position
        self.score = 0
        self.last_brew_result = "🔄 Spiel zurückgesetzt!"
        print("🔄 Spiel wurde zurückgesetzt!")
        
    def get_game_state(self):
        """Gibt den aktuellen Spielzustand zurück"""
        return {
            'player_pos': (self.player.rect.centerx, self.player.rect.centery),  # Verwende rect für Position
            'aktive_zutaten': self.aktive_zutaten.copy(),
            'last_brew_result': self.last_brew_result,
            'score': self.score
        }

# Test der erweiterten Funktionalität
if __name__ == "__main__":
    print("🧪 GAME TEST")
    print("=" * 40)
    
    game = Game()
    
    print("🏁 Startposition Spieler: ({}, {})".format(game.player.rect.centerx, game.player.rect.centery))
    print("🎯 NFC-Token System aktiviert - keine Boden-Kristalle!")
    
    # Bewegungstest mit neuer Methode
    print("\n🏃‍♂️ BEWEGUNGSTEST:")
    print("Position vorher: {}".format(game.player.rect.centerx))
    
    # Simuliere Bewegung nach rechts
    import pygame
    for i in range(10):
        game.player.direction.x = 1  # Bewegung nach rechts
        game.player.move(1.0/60.0)  # Simuliere 60 FPS
    print("Nach 10x rechts: {}".format(game.player.rect.centerx))
    
    # Simuliere Bewegung nach links
    for i in range(5):
        game.player.direction.x = -1  # Bewegung nach links
        game.player.move(1.0/60.0)  # Simuliere 60 FPS
    print("Nach 5x links: {}".format(game.player.rect.centerx))
    
    # Zutat-Test (simuliert)
    print("\n🎒 ZUTAT-SAMMEL-TEST:")
    game.add_zutat("wasserkristall")
    game.add_zutat("feueressenz")
    
    print("\n🧪 BRAU-TEST:")
    game.brew()
    
    print("\n📊 Endstand: {} Punkte".format(game.score))
    print("✅ Game funktioniert!")
