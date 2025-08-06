# -*- coding: utf-8 -*-
"""
Alchemy System - Enhanced Potion Brewing System

Verbessertes Alchemie-System mit erweiterbaren Rezepten,
Ingredient-Management und Score-System.
"""

from enum import Enum


class IngredientType(object):
    """
    Verfügbare Zutaten-Typen für das Alchemie-System
    """
    WATER_CRYSTAL = "wasserkristall"
    FIRE_ESSENCE = "feueressenz"
    EARTH_CRYSTAL = "erdkristall"


class Recipe(object):
    """
    Klasse für Alchemie-Rezepte
    
    Attributes:
        ingredients: Liste der benötigten Zutaten
        result_name: Name des resultierenden Tranks
        result_effect: Beschreibung des Effekts
        score_value: Punkte die für das Brauen vergeben werden
    """
    
    def __init__(self, ingredients, result_name, result_effect, score_value=50):
        """
        Initialisiert ein Rezept
        
        Args:
            ingredients: Liste der benötigten Zutaten
            result_name: Name des resultierenden Tranks
            result_effect: Beschreibung des Effekts
            score_value: Punkte die für das Brauen vergeben werden
        """
        self.ingredients = ingredients
        self.result_name = result_name
        self.result_effect = result_effect
        self.score_value = score_value
    
    def matches(self, ingredients):
        """
        Prüft ob die Zutaten diesem Rezept entsprechen
        
        Args:
            ingredients: Liste der zu prüfenden Zutaten
            
        Returns:
            bool: True wenn die Zutaten exakt dem Rezept entsprechen
        """
        return sorted(self.ingredients) == sorted(ingredients)


class AlchemySystem(object):
    """
    Verbessertes Alchemie-System mit erweiterbaren Rezepten
    
    Verwaltet Zutaten, Rezepte und das Brauen von Tränken.
    Bietet ein flexibles System für neue Rezepte und Effekte.
    """
    
    def __init__(self):
        """Initialisiert das Alchemie-System"""
        self.recipes = self._load_recipes()
        self.active_ingredients = []
        self.max_ingredients = 5
        self.brew_history = []
        
    def _load_recipes(self):
        """
        Lädt alle verfügbaren Rezepte (später aus JSON-Datei)
        
        Returns:
            List[Recipe]: Liste aller verfügbaren Rezepte
        """
        return [
            # Basis-Wasser-Zauber
            Recipe(
                [IngredientType.WATER_CRYSTAL, IngredientType.WATER_CRYSTAL],
                "Wasserzauber",
                u"💧 Feuer gelöscht! Ein starker Wasserzauber.",
                score_value=50
            ),
            
            # Heiltrank
            Recipe(
                [IngredientType.FIRE_ESSENCE, IngredientType.WATER_CRYSTAL],
                "Heiltrank",
                u"❤️ Heiltrank gebraut! Lebenspunkte wiederhergestellt.",
                score_value=75
            ),
            
            # Feuerball-Zauber
            Recipe(
                [IngredientType.FIRE_ESSENCE, IngredientType.FIRE_ESSENCE],
                "Feuerball",
                u"🔥 Feuerball! Mächtiger Angriffszauber.",
                score_value=60
            ),
            
            # Steinwall-Schutz
            Recipe(
                [IngredientType.EARTH_CRYSTAL, IngredientType.EARTH_CRYSTAL],
                "Steinwall",
                u"🏔️ Steinwall! Schutz vor Angriffen.",
                score_value=55
            ),
            
            # Wachstumstrank
            Recipe(
                [IngredientType.WATER_CRYSTAL, IngredientType.EARTH_CRYSTAL],
                "Wachstumstrank",
                u"🌱 Wachstumstrank! Pflanzen sprießen.",
                score_value=40
            ),
            
            # Explosive Mischung
            Recipe(
                [IngredientType.EARTH_CRYSTAL, IngredientType.FIRE_ESSENCE],
                "Explosive Mischung",
                u"💥 Explosion! Das war die falsche Mischung.",
                score_value=30
            ),
            
            # Verlangsamungstrank
            Recipe(
                [IngredientType.EARTH_CRYSTAL, IngredientType.WATER_CRYSTAL],
                "Verlangsamungstrank",
                u"🐌 Verlangsamungstrank! Gegner werden langsamer.",
                score_value=45
            ),
            
            # Dreifach-Kombination: Universaltrank
            Recipe(
                [IngredientType.WATER_CRYSTAL, IngredientType.FIRE_ESSENCE, IngredientType.EARTH_CRYSTAL],
                "Universaltrank",
                u"✨ Universaltrank! Alle Elemente in Harmonie.",
                score_value=100
            ),
        ]
    
    def add_ingredient(self, ingredient):
        """
        Fügt eine Zutat zum aktiven Brau-Feld hinzu
        
        Args:
            ingredient: Die hinzuzufügende Zutat
            
        Returns:
            bool: True wenn erfolgreich hinzugefügt, False wenn Feld voll
        """
        if len(self.active_ingredients) >= self.max_ingredients:
            return False
        
        self.active_ingredients.append(ingredient)
        return True
    
    def remove_last_ingredient(self):
        """
        Entfernt die zuletzt hinzugefügte Zutat
        
        Returns:
            Die entfernte Zutat oder None wenn leer
        """
        if self.active_ingredients:
            return self.active_ingredients.pop()
        return None
    
    def brew(self):
        """
        Braut einen Trank aus den aktiven Zutaten
        
        Returns:
            Das gebraute Rezept oder None wenn kein Match
        """
        if not self.active_ingredients:
            return None
        
        # Suche nach passendem Rezept
        for recipe in self.recipes:
            if recipe.matches(self.active_ingredients):
                self.brew_history.append(recipe)
                self.active_ingredients = []
                return recipe
        
        # Kein passendes Rezept gefunden
        self.active_ingredients = []
        return None
    
    def clear_ingredients(self):
        """Leert das aktive Brau-Feld"""
        self.active_ingredients = []
    
    def get_active_ingredients_count(self):
        """
        Gibt die Anzahl der aktiven Zutaten zurück
        
        Returns:
            int: Anzahl der aktiven Zutaten
        """
        return len(self.active_ingredients)
    
    def get_active_ingredients(self):
        """
        Gibt eine Kopie der aktiven Zutaten zurück
        
        Returns:
            Liste der aktiven Zutaten
        """
        return list(self.active_ingredients)
    
    def get_recipes(self):
        """
        Gibt alle verfügbaren Rezepte zurück
        
        Returns:
            Liste aller Rezepte
        """
        return list(self.recipes)
    
    def add_recipe(self, recipe):
        """
        Fügt ein neues Rezept hinzu
        
        Args:
            recipe: Das hinzuzufügende Rezept
        """
        self.recipes.append(recipe)
    
    def get_brew_count(self):
        """
        Gibt die Anzahl der erfolgreich gebrauten Tränke zurück
        
        Returns:
            int: Anzahl der erfolgreichen Brau-Vorgänge
        """
        return len(self.brew_history)
    
    def get_total_score(self):
        """
        Berechnet die Gesamtpunktzahl aller gebrauten Tränke
        
        Returns:
            int: Gesamtpunktzahl
        """
        return sum(recipe.score_value for recipe in self.brew_history)


# Hilfsfunktionen für einfache Nutzung
def create_ingredient_from_string(ingredient_str):
    """
    Konvertiert einen String zu einem IngredientType
    
    Args:
        ingredient_str: String-Repräsentation der Zutat
        
    Returns:
        Die Zutat oder None wenn ungültig
    """
    ingredient_mapping = {
        "wasserkristall": IngredientType.WATER_CRYSTAL,
        "feueressenz": IngredientType.FIRE_ESSENCE,
        "erdkristall": IngredientType.EARTH_CRYSTAL,
    }
    
    return ingredient_mapping.get(ingredient_str.lower())


def get_ingredient_display_name(ingredient):
    """
    Gibt den Anzeigenamen einer Zutat zurück
    
    Args:
        ingredient: Die Zutat
        
    Returns:
        str: Anzeigename der Zutat
    """
    display_names = {
        IngredientType.WATER_CRYSTAL: u"Wasserkristall 💧",
        IngredientType.FIRE_ESSENCE: u"Feueressenz 🔥",
        IngredientType.EARTH_CRYSTAL: u"Erdkristall 🌍",
    }
    
    return display_names.get(ingredient, str(ingredient))


if __name__ == "__main__":
    # Test des Alchemie-Systems
    print(u"🧪 ALCHEMY SYSTEM TEST")
    print("=" * 40)
    
    alchemy = AlchemySystem()
    
    print("Verfügbare Rezepte: {}".format(len(alchemy.get_recipes())))
    print("\nTeste Rezepte:")
    
    # Test 1: Wasserzauber
    print("\n1. Wasserzauber (2x Wasserkristall):")
    alchemy.add_ingredient(IngredientType.WATER_CRYSTAL)
    alchemy.add_ingredient(IngredientType.WATER_CRYSTAL)
    result = alchemy.brew()
    if result:
        print("✅ {}: {} (+{} Punkte)".format(result.result_name, result.result_effect, result.score_value))
    else:
        print("❌ Kein Rezept gefunden")
    
    # Test 2: Heiltrank
    print("\n2. Heiltrank (Feuer + Wasser):")
    alchemy.add_ingredient(IngredientType.FIRE_ESSENCE)
    alchemy.add_ingredient(IngredientType.WATER_CRYSTAL)
    result = alchemy.brew()
    if result:
        print("✅ {}: {} (+{} Punkte)".format(result.result_name, result.result_effect, result.score_value))
    else:
        print("❌ Kein Rezept gefunden")
    
    # Test 3: Unbekanntes Rezept
    print("\n3. Test unbekanntes Rezept (nur Feuer):")
    alchemy.add_ingredient(IngredientType.FIRE_ESSENCE)
    result = alchemy.brew()
    if result:
        print("✅ {}: {}".format(result.result_name, result.result_effect))
    else:
        print("❌ Kein passendes Rezept gefunden")
    
    print("\nStatistiken:")
    print("   Gebraute Tränke: {}".format(alchemy.get_brew_count()))
    print("   Gesamtpunktzahl: {}".format(alchemy.get_total_score()))
