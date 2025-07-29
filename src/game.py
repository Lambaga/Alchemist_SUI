# src/game.py
# Enthält die Haupt-Spiellogik und die Zustandsverwaltung.

class Game:
    """
    Verwaltet den Zustand des Spiels, inklusive der aktiven Zutaten
    und der verfügbaren Rezepte.
    """
    def __init__(self):
        """Initialisiert das Spiel mit einer leeren Zutatenliste und den Rezepten."""
        print("Ein neues Alchemie-Spiel beginnt!")
        
        # Die Liste der Zutaten, die aktuell auf dem Alchemisten-Feld liegen.
        self.aktive_zutaten = []
        
        # Das Rezeptbuch als Dictionary.
        # Die Schlüssel sind Tuples von sortierten Zutaten, der Wert ist der Effekt.
        self.rezepte = {
            ("wasserkristall", "wasserkristall"): "Feuer gelöscht! Ein starker Wasserzauber.",
            ("feueressenz", "wasserkristall"): "Heiltrank gebraut! Lebenspunkte wiederhergestellt.",
            ("erdkristall", "feueressenz"): "Explosion! Das war die falsche Mischung."
            # Füge hier weitere Rezepte hinzu
        }

    def add_zutat(self, zutat_name):
        """Fügt eine Zutat zur Liste der aktiven Zutaten hinzu."""
        # Hier könnte man eine maximale Anzahl an Zutaten prüfen, falls gewünscht.
        self.aktive_zutaten.append(zutat_name)
        print(f"Zutat hinzugefügt: {zutat_name} | Aktuelles Feld: {self.aktive_zutaten}")

    def remove_last_zutat(self):
        """Entfernt die zuletzt hinzugefügte Zutat vom Feld."""
        if self.aktive_zutaten:
            entfernte_zutat = self.aktive_zutaten.pop()
            print(f"Zutat entfernt: {entfernte_zutat} | Aktuelles Feld: {self.aktive_zutaten}")
        else:
            print("Keine Zutaten zum Entfernen auf dem Feld.")
            
    def brew(self):
        """
        Versucht, aus den aktiven Zutaten einen Trank zu brauen.
        Prüft die Kombination gegen das Rezeptbuch und gibt das Ergebnis zurück.
        """
        if not self.aktive_zutaten:
            print("Brauversuch ohne Zutaten.")
            return "Nichts zum Brauen da."

        # Zutaten sortieren, damit die Reihenfolge keine Rolle spielt.
        # Ein Tuple wird erstellt, da Listen nicht als Dictionary-Schlüssel verwendet werden können.
        rezept_schluessel = tuple(sorted(self.aktive_zutaten))
        
        # Rezept im Buch nachschlagen. .get() gibt einen Standardwert zurück, wenn nichts gefunden wird.
        ergebnis = self.rezepte.get(rezept_schluessel, "Unbekanntes Rezept. Nichts passiert.")
        
        print(f"Brauen versucht mit {self.aktive_zutaten}. Schlüssel: {rezept_schluessel}. Ergebnis: {ergebnis}")

        # Nach dem Brauversuch wird das Feld immer geleert.
        self.aktive_zutaten.clear()
        
        return ergebnis

# --- Beispiel für die Ausführung der Datei ---
if __name__ == "__main__":
    # Dieser Block wird nur ausgeführt, wenn du `python src/game.py` direkt startest.
    # Er dient zum Testen der Klassenlogik, bevor du Pygame einbindest.
    
    print("\n--- Testlauf der Game-Klasse ---")
    mein_spiel = Game()

    # Test 1: Ein erfolgreiches Rezept (Reihenfolge der Zutaten ist egal)
    print("\n[Test 1: Erfolgreiches Rezept]")
    mein_spiel.add_zutat("wasserkristall")
    mein_spiel.add_zutat("feueressenz") # Reihenfolge ist anders als im Rezeptbuch
    brau_ergebnis = mein_spiel.brew()
    print(f"==> Ergebnis des Brauens: {brau_ergebnis}")
    print(f"Feld nach dem Brauen: {mein_spiel.aktive_zutaten}") # Sollte leer sein

    # Test 2: Ein unbekanntes Rezept
    print("\n[Test 2: Unbekanntes Rezept]")
    mein_spiel.add_zutat("erdkristall")
    brau_ergebnis = mein_spiel.brew()
    print(f"==> Ergebnis des Brauens: {brau_ergebnis}")

    # Test 3: Zutat entfernen und dann brauen
    print("\n[Test 3: Zutat entfernen]")
    mein_spiel.add_zutat("wasserkristall")
    mein_spiel.add_zutat("wasserkristall")
    mein_spiel.add_zutat("feueressenz")
    mein_spiel.remove_last_zutat() # Entfernt "feueressenz"
    brau_ergebnis = mein_spiel.brew() # Braut mit zwei "wasserkristall"
    print(f"==> Ergebnis des Brauens: {brau_ergebnis}")
