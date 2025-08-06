# -*- coding: utf-8 -*-
# src/game.py
# Erweiterte Alchemist-Spiel-Logik mit animiertem Spieler

import pygame
from os import path
from player import Player
from settings import *
from alchemy_system import AlchemySystem, IngredientType, create_ingredient_from_string
from combat_system import CombatEntity, DamageType

class Game:
    """
    Erweiterte Spiellogik mit Spieler-Bewegung und NFC-Token System
    """
    
    def __init__(self):
        print("🧙‍♂️ Der Alchemist - Erweiterte Version startet!")
        
        # Pygame muss initialisiert sein für die Player-Klasse
        if not pygame.get_init():
            pygame.init()
        
        # Player-Charaktere laden
        start_x, start_y = PLAYER_START_POS
        
        try:
            # Versuche zuerst mit dem Wizard Pack
            wizard_path = path.join(ASSETS_DIR, "Wizard Pack")
            if path.exists(wizard_path):
                self.player = Player(wizard_path, start_x, start_y)
                print(f"✅ Spieler erfolgreich erstellt mit: {wizard_path}")
            else:
                raise FileNotFoundError("Wizard Pack Ordner nicht gefunden")
        except Exception as e:
            print(f"⚠️ Fehler beim Laden der Wizard-Sprites: {e}")
            try:
                # Fallback: Versuche anderen verfügbaren Spritesheet
                fallback_path = path.join(ASSETS_DIR, "images", "player.png")
                if path.exists(fallback_path):
                    self.player = Player(fallback_path, start_x, start_y)
                    print(f"✅ Spieler mit Fallback-Sprite erstellt: {fallback_path}")
                else:
                    raise FileNotFoundError("Kein Fallback-Sprite gefunden")
            except Exception as fallback_error:
                print(f"⚠️ Auch Fallback fehlgeschlagen: {fallback_error}")
                # Letzter Fallback: Player ohne Spritesheet
                self.player = Player("", start_x, start_y)
                print("⚠️ Kritisch: Spieler konnte nur als leerer Platzhalter erstellt werden.")
        
        # Neues Alchemie-System initialisieren
        self.alchemy_system = AlchemySystem()
        
        # Legacy-Attribute für Kompatibilität
        self.aktive_zutaten = []  # Wird durch alchemy_system.active_ingredients ersetzt
        
        # Spielstatus
        self.last_brew_result = "Spiel gestartet"
        self.score = 0
        
    def reset_game(self):
        """Setzt das Spiel zurück (für neues Spiel nach Game Over)"""
        # Spieler wiederbeleben
        self.player.revive()
        print("💖 Spieler wiederbelebt!")
        
        # Position zurücksetzen
        start_x, start_y = PLAYER_START_POS
        self.player.rect.centerx = start_x
        self.player.rect.centery = start_y
        self.player.update_hitbox()
        
        # Spielstatus zurücksetzen
        self.score = 0
        self.last_brew_result = "Neues Spiel gestartet"
        
        # Alchemie-System zurücksetzen
        self.alchemy_system.clear_all_ingredients()
        self.aktive_zutaten = []
        
        print("🔄 Spiel wurde zurückgesetzt!")
        
        
    def update(self, dt=None, collision_objects=None):
        """Update-Schleife mit Delta Time - aktualisiert Spieler-Animation"""
        # Aktualisiere nur die Animation, Bewegung wird separat behandelt
        self.player.update(dt)
        
        # Prüfe, ob der Spieler gestorben ist
        if self.player.is_dead():
            return "game_over"  # Signal für Game Over
        
        return None
    
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
        ingredient = create_ingredient_from_string(zutat_name)
        if ingredient:
            success = self.alchemy_system.add_ingredient(ingredient)
            if success:
                # Update legacy attribute for compatibility
                self.aktive_zutaten = [ing if isinstance(ing, str) else ing.value 
                                     for ing in self.alchemy_system.get_active_ingredients()]
                print("🎯 NFC-Token erkannt: {} | Alchemisten-Feld: {}".format(zutat_name, self.aktive_zutaten))
            else:
                print("🚫 Alchemisten-Feld voll! Maximal {} Zutaten.".format(self.alchemy_system.max_ingredients))
        else:
            print("❌ Unbekannte Zutat: {}".format(zutat_name))

    def remove_last_zutat(self):
        """Entfernt die zuletzt hinzugefügte Zutat"""
        removed_ingredient = self.alchemy_system.remove_last_ingredient()
        if removed_ingredient:
            # Update legacy attribute for compatibility
            self.aktive_zutaten = [ing if isinstance(ing, str) else ing.value 
                                 for ing in self.alchemy_system.get_active_ingredients()]
            print("➖ Zutat entfernt: {} | Alchemisten-Feld: {}".format(
                removed_ingredient if isinstance(removed_ingredient, str) else removed_ingredient.value, 
                self.aktive_zutaten))
        else:
            print("📭 Keine Zutaten zum Entfernen.")
            
    def brew(self):
        """Braut einen Trank aus den aktiven Zutaten"""
        recipe = self.alchemy_system.brew()
        
        if recipe and recipe.name != "Nichts":
            # Erfolgreiche Alchemie!
            points = recipe.complexity * 10
            self.score += points
            self.last_brew_result = f"✨ {recipe.name} gebraut! (+{points} Punkte)"
            print(f"🧪 Erfolgreich gebraut: {recipe.name} | Punkte: +{points} | Gesamt: {self.score}")
            
            # Reset aktive_zutaten after brewing
            self.aktive_zutaten = []
            
            return recipe
        else:
            # Gescheiterte Alchemie
            self.last_brew_result = "💨 Nichts Brauchbares entstanden..."
            self.aktive_zutaten = []  # Zutaten trotzdem verbraucht
            print("💨 Brauen fehlgeschlagen.")
            return None
            
    def get_player_health_percentage(self):
        """Gibt den Gesundheitsprozentsatz des Spielers zurück"""
        if hasattr(self.player, 'get_health_percentage'):
            return self.player.get_health_percentage()
        return 1.0  # Fallback: 100% Gesundheit
    
    def get_player_health(self):
        """Gibt die aktuelle Gesundheit des Spielers zurück"""
        if hasattr(self.player, 'get_health'):
            return self.player.get_health()
        return 100  # Fallback
    
    def get_player_max_health(self):
        """Gibt die maximale Gesundheit des Spielers zurück"""
        if hasattr(self.player, 'get_max_health'):
            return self.player.get_max_health()
        return 100  # Fallback
