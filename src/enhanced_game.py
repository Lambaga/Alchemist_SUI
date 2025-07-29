# enhanced_game.py
# Erweiterte Alchemist-Spiel Logik mit animiertem Spieler

import pygame
from player import Player

class EnhancedGame:
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
            "assets/Wizard Pack",  # Wizard Pack Ordner
            "assets/wizard_char.png",  # Original Einzeldatei
            "assets/wizard_char_demo.png"  # Demo-Fallback
        ]
        
        player_created = False
        for path in sprite_paths:
            try:
                self.player = Player(path, 960, 500)
                player_created = True
                print(f"✅ Spieler erstellt mit: {path}")
                break
            except:
                continue
        
        if not player_created:
            # Letzter Fallback: Player ohne Spritesheet
            self.player = Player("", 960, 500)
            print("⚠️ Spieler ohne Spritesheet erstellt")
        
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
        
        # Spielstatus
        self.last_brew_result = "Willkommen, Alchemist! Platziere NFC-Tokens zum Brauen."
        self.score = 0
        
        
    def update(self):
        """Update-Schleife - aktualisiert Spieler-Animation"""
        # Aktualisiere Spieler-Animation
        self.player.update()
                
    def add_zutat(self, zutat_name):
        """Fügt eine Zutat zur Brau-Liste hinzu (normalerweise durch NFC-Token)"""
        if len(self.aktive_zutaten) < 5:  # Maximal 5 Zutaten
            self.aktive_zutaten.append(zutat_name)
            print(f"🎯 NFC-Token erkannt: {zutat_name} | Alchemisten-Feld: {self.aktive_zutaten}")
        else:
            print("🚫 Alchemisten-Feld voll! Maximal 5 Zutaten.")

    def remove_last_zutat(self):
        """Entfernt die zuletzt hinzugefügte Zutat"""
        if self.aktive_zutaten:
            entfernte_zutat = self.aktive_zutaten.pop()
            print(f"➖ Zutat entfernt: {entfernte_zutat} | Alchemisten-Feld: {self.aktive_zutaten}")
        else:
            print("📭 Keine Zutaten zum Entfernen.")
            
    def brew(self):
        """Braut einen Trank aus den aktiven Zutaten"""
        if not self.aktive_zutaten:
            result = "🤷‍♂️ Nichts zum Brauen da."
            self.last_brew_result = result
            return result

        # Zutaten sortieren für Rezept-Lookup
        rezept_schluessel = tuple(sorted(self.aktive_zutaten))
        
        # Rezept suchen
        ergebnis = self.rezepte.get(rezept_schluessel, "❓ Unbekanntes Rezept. Nichts passiert.")
        
        if ergebnis != "❓ Unbekanntes Rezept. Nichts passiert.":
            self.score += 50  # Bonus für erfolgreiches Brauen
        
        print(f"🧪 Brauen: {self.aktive_zutaten} → {ergebnis}")
        print(f"📊 Aktuelle Punkte: {self.score}")

        # Feld nach Brauen leeren
        self.aktive_zutaten.clear()
        self.last_brew_result = ergebnis
        
        return ergebnis
        
    def reset_game(self):
        """Setzt das Spiel zurück"""
        self.aktive_zutaten.clear()
        self.player.x = 960  # Zurück zur Mitte
        self.score = 0
        self.last_brew_result = "🔄 Spiel zurückgesetzt!"
        print("🔄 Spiel wurde zurückgesetzt!")
        
    def get_game_state(self):
        """Gibt den aktuellen Spielzustand zurück"""
        return {
            'player_pos': (self.player.x, self.player.y),
            'aktive_zutaten': self.aktive_zutaten.copy(),
            'last_brew_result': self.last_brew_result,
            'score': self.score
        }

# Test der erweiterten Funktionalität
if __name__ == "__main__":
    print("🧪 ENHANCED GAME TEST")
    print("=" * 40)
    
    game = EnhancedGame()
    
    print(f"🏁 Startposition Spieler: ({game.player.x}, {game.player.y})")
    print("� NFC-Token System aktiviert - keine Boden-Kristalle!")
    
    # Bewegungstest
    print("\n🏃‍♂️ BEWEGUNGSTEST:")
    print(f"Position vorher: {game.player.x}")
    
    for i in range(10):
        game.player.move_right()
    print(f"Nach 10x rechts: {game.player.x}")
    
    for i in range(5):
        game.player.move_left()
    print(f"Nach 5x links: {game.player.x}")
    
    # Zutat-Test (simuliert)
    print("\n🎒 ZUTAT-SAMMEL-TEST:")
    game.add_zutat("wasserkristall")
    game.add_zutat("feueressenz")
    
    print("\n🧪 BRAU-TEST:")
    game.brew()
    
    print(f"\n📊 Endstand: {game.score} Punkte")
    print("✅ Enhanced Game funktioniert!")
