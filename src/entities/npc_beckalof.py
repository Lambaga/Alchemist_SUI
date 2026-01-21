"""
The Great Beckalof - NPC Character
Ein freundlicher Alchemist-Meister der in der Welt herumsteht und trinkt.
"""

import pygame
import os
import random
from managers.font_manager import get_font_manager


# Beckalofs Geschichten über Milchschokolade
BECKALOF_DIALOGUES = [
    "Ah, junger Alchemist! Weißt du, was das Geheimnis wahrer Magie ist? MILCHSCHOKOLADE! "
    "Sie enthält die perfekte Balance aus Kakao und Milch - wie Yin und Yang!",
    
    "In meinen jungen Jahren war ich ein schwacher Zauberer... bis ich entdeckte, dass "
    "eine Tasse heiße Milchschokolade vor dem Brauen die Mana-Kanäle öffnet!",
    
    "Die alten Meister sagten: 'Wasser ist Leben, Feuer ist Kraft.' Aber ICH sage: "
    "Milchschokolade ist BEIDES! Plus sie schmeckt fantastisch!",
    
    "Einst besiegte ich einen Drachen... nicht mit Magie, nein! Ich bot ihm "
    "Milchschokolade an. Wir sind jetzt beste Freunde. Er heißt Gerald.",
    
    "Merke dir: Jeden Morgen ein Becher Milchschokolade, und du wirst unsterblich! "
    "...Nun ja, vielleicht nicht unsterblich, aber definitiv glücklicher!",
]


class BeckalofNPC(pygame.sprite.Sprite):
    """The Great Beckalof - NPC mit Idle und Drinking Animationen."""
    
    # Interaktions-Distanz in Pixeln (groß für einfache Interaktion)
    INTERACTION_DISTANCE = 200
    
    def __init__(self, x: int, y: int):
        super().__init__()
        
        self.x = x
        self.y = y
        
        # Animation States
        self.state = "idle"  # idle, drinking
        self.animations = {}
        self.current_frame = 0
        self.animation_speed = 0.08  # Frames pro Update (idle)
        self.drinking_animation_speed = 0.03  # Langsamer beim Trinken
        self.animation_timer = 0.0
        
        # Timing für Drinking (alle 10 Sekunden)
        self.drinking_interval = 10000  # 10 Sekunden in ms
        self.last_drinking_time = pygame.time.get_ticks()
        self.drinking_duration = 0  # Wird gesetzt wenn Drinking startet
        
        # Idle-Variation (wechselt zwischen verschiedenen Idle-Animationen)
        self.idle_variation_interval = 3000  # Alle 3 Sekunden neue Idle-Variation
        self.last_idle_variation = pygame.time.get_ticks()
        self.current_idle_index = 0
        self.idle_animation_keys = []  # Wird nach Laden gefüllt
        
        # Interaktion
        self.can_interact = False  # Spieler ist nah genug
        self.dialogue_index = 0  # Welcher Dialog als nächstes
        self._font_manager = get_font_manager()
        self._interaction_font = self._font_manager.get_font(24)
        
        # Lade Animationen
        self._load_animations()
        
        # Initiales Setup
        if self.animations:
            first_anim = list(self.animations.values())[0]
            if first_anim:
                self.image = first_anim[0]
                self.rect = self.image.get_rect()
                self.rect.midbottom = (x, y)
            else:
                self._create_placeholder()
        else:
            self._create_placeholder()
    
    def _create_placeholder(self):
        """Erstellt einen Platzhalter falls keine Sprites geladen werden können."""
        self.image = pygame.Surface((64, 128), pygame.SRCALPHA)
        self.image.fill((150, 100, 50, 200))
        pygame.draw.rect(self.image, (200, 150, 100), self.image.get_rect(), 3)
        self.rect = self.image.get_rect()
        self.rect.midbottom = (self.x, self.y)
    
    def _load_animations(self):
        """Lädt alle Animationen aus dem Beckalof Pack."""
        base_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "assets", "Beckalof Pack"
        )
        
        # Animation-Definitionen: (Dateiname, Animation-Key)
        # Jede Datei ist EIN Frame (352x628)
        animation_files = {
            "Idle_Beckers.png": ("idle1", 1),
            "Idle2_Beckers.png": ("idle2", 1),
            "Idle3_Beckers.png": ("idle3", 1),
            "Drinking1_Beckers.png": ("drinking1", 1),
            "Drinking2_Beckers.png": ("drinking2", 1),
            "DrinkingEnd_Beckers.png": ("drinking_end", 1),
        }
        
        for filename, (anim_key, num_frames) in animation_files.items():
            filepath = os.path.join(base_path, filename)
            if os.path.exists(filepath):
                try:
                    sheet = pygame.image.load(filepath).convert_alpha()
                    frames = self._split_spritesheet(sheet, num_frames)
                    self.animations[anim_key] = frames
                    
                    # Sammle Idle-Keys
                    if anim_key.startswith("idle"):
                        self.idle_animation_keys.append(anim_key)
                    
                    print(f"✅ Beckalof Animation geladen: {anim_key} ({len(frames)} Frames)")
                except Exception as e:
                    print(f"⚠️ Fehler beim Laden von {filename}: {e}")
        
        if not self.idle_animation_keys:
            self.idle_animation_keys = ["idle1"]
    
    def _split_spritesheet(self, sheet: pygame.Surface, num_frames: int) -> list:
        """Lädt Frame(s) aus einem Sprite Sheet."""
        frames = []
        sheet_width = sheet.get_width()
        sheet_height = sheet.get_height()
        
        # Jede Datei ist ein einzelner Frame (352x628)
        # Skaliere proportional auf Ziel-Höhe
        target_height = 70  # Halb so groß wie vorher
        scale_factor = target_height / sheet_height
        target_width = int(sheet_width * scale_factor)
        
        print(f"  📐 Original: {sheet_width}x{sheet_height} → {target_width}x{target_height}")
        
        # Skaliere das ganze Bild als einen Frame
        scaled = pygame.transform.smoothscale(sheet, (target_width, target_height))
        frames.append(scaled)
        
        return frames
    
    def update(self, dt: float = None):
        """Update Animation und State."""
        current_time = pygame.time.get_ticks()
        
        # Prüfe ob es Zeit zum Trinken ist
        if self.state == "idle":
            if current_time - self.last_drinking_time >= self.drinking_interval:
                self._start_drinking()
            else:
                # Idle-Variation wechseln
                if current_time - self.last_idle_variation >= self.idle_variation_interval:
                    self._change_idle_variation()
        
        # Prüfe ob Drinking fertig ist
        elif self.state == "drinking":
            if current_time - self.last_drinking_time >= self.drinking_duration:
                self._end_drinking()
        
        # Animation Frame Update - langsamer beim Trinken
        speed = self.drinking_animation_speed if self.state == "drinking" else self.animation_speed
        self.animation_timer += speed
        if self.animation_timer >= 1.0:
            self.animation_timer = 0.0
            self._next_frame()
    
    def _start_drinking(self):
        """Startet die Drinking-Animation."""
        self.state = "drinking"
        self.current_frame = 0
        self.last_drinking_time = pygame.time.get_ticks()
        
        # Berechne Drinking-Dauer (drinking1 + drinking2 + drinking_end)
        total_frames = 0
        for key in ["drinking1", "drinking2", "drinking_end"]:
            if key in self.animations:
                total_frames += len(self.animations[key])
        
        # Ca. 400ms pro Frame (langsamer trinken)
        self.drinking_duration = total_frames * 400
        print("🍺 Beckalof trinkt!")
    
    def _end_drinking(self):
        """Beendet Drinking und wechselt zurück zu Idle."""
        self.state = "idle"
        self.current_frame = 0
        self.last_drinking_time = pygame.time.get_ticks()
        self._change_idle_variation()
    
    def _change_idle_variation(self):
        """Wechselt zu einer anderen Idle-Animation."""
        self.last_idle_variation = pygame.time.get_ticks()
        if len(self.idle_animation_keys) > 1:
            # Wähle zufällig eine andere Idle-Animation
            available = [k for k in self.idle_animation_keys if k != self.idle_animation_keys[self.current_idle_index]]
            if available:
                new_key = random.choice(available)
                self.current_idle_index = self.idle_animation_keys.index(new_key)
        self.current_frame = 0
    
    def _next_frame(self):
        """Wechselt zum nächsten Animation-Frame."""
        current_anim = self._get_current_animation()
        if current_anim:
            self.current_frame = (self.current_frame + 1) % len(current_anim)
            self.image = current_anim[self.current_frame]
    
    def _get_current_animation(self) -> list:
        """Gibt die aktuelle Animation basierend auf State zurück."""
        if self.state == "idle":
            if self.idle_animation_keys:
                key = self.idle_animation_keys[self.current_idle_index]
                return self.animations.get(key, [])
        elif self.state == "drinking":
            # Sequenz: drinking1 -> drinking2 -> drinking_end (länger)
            drinking_seq = []
            for key in ["drinking1", "drinking2"]:
                drinking_seq.extend(self.animations.get(key, []))
            # DrinkingEnd 5x wiederholen für längere Pause am Ende
            drinking_end = self.animations.get("drinking_end", [])
            for _ in range(5):
                drinking_seq.extend(drinking_end)
            return drinking_seq if drinking_seq else self.animations.get("idle1", [])
        
        return []
    
    def check_player_distance(self, player_rect: pygame.Rect) -> bool:
        """Prüft ob der Spieler nah genug für Interaktion ist."""
        if not self.rect:
            return False
        
        # Berechne Distanz zwischen Spieler und Beckalof
        dx = player_rect.centerx - self.rect.centerx
        dy = player_rect.centery - self.rect.centery
        distance = (dx * dx + dy * dy) ** 0.5
        
        was_interactable = self.can_interact
        self.can_interact = distance <= self.INTERACTION_DISTANCE
        
        # Debug: Zeige wenn Interaktion möglich wird
        if self.can_interact and not was_interactable:
            print(f"✨ Beckalof Interaktion möglich! Distanz: {distance:.0f} (Max: {self.INTERACTION_DISTANCE})")
        
        return self.can_interact
    
    def get_next_dialogue(self) -> str:
        """Gibt den nächsten Dialog zurück und rotiert."""
        dialogue = BECKALOF_DIALOGUES[self.dialogue_index]
        self.dialogue_index = (self.dialogue_index + 1) % len(BECKALOF_DIALOGUES)
        return dialogue
    
    def render(self, screen: pygame.Surface, camera):
        """Zeichnet Beckalof auf den Bildschirm."""
        if self.image:
            # Kamera-Transformation anwenden
            screen_pos = camera.apply(self)
            screen.blit(self.image, screen_pos)
            
            # Zeige Interaktions-Hinweis wenn Spieler nah ist
            if self.can_interact:
                self._render_interaction_hint(screen, screen_pos)
    
    def _render_interaction_hint(self, screen: pygame.Surface, screen_pos: pygame.Rect):
        """Zeichnet den 'C drücken' Hinweis über Beckalof."""
        hint_text = "[ C ] Sprechen"
        hint_surf = self._interaction_font.render(hint_text, True, (255, 255, 200))
        
        # Hintergrund für bessere Lesbarkeit
        padding = 6
        bg_rect = pygame.Rect(
            screen_pos.centerx - hint_surf.get_width() // 2 - padding,
            screen_pos.top - 30 - padding,
            hint_surf.get_width() + padding * 2,
            hint_surf.get_height() + padding * 2
        )
        
        # Halbtransparenter Hintergrund
        bg_surf = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        bg_surf.fill((20, 20, 40, 180))
        screen.blit(bg_surf, bg_rect)
        
        # Rahmen
        pygame.draw.rect(screen, (100, 150, 255), bg_rect, 2)
        
        # Text
        text_x = screen_pos.centerx - hint_surf.get_width() // 2
        text_y = screen_pos.top - 30
        screen.blit(hint_surf, (text_x, text_y))


# Singleton-artige Factory-Funktion
_beckalof_instance = None

def get_beckalof(x: int = None, y: int = None) -> BeckalofNPC:
    """Gibt die Beckalof-Instanz zurück oder erstellt eine neue."""
    global _beckalof_instance
    if _beckalof_instance is None and x is not None and y is not None:
        _beckalof_instance = BeckalofNPC(x, y)
    return _beckalof_instance

def reset_beckalof():
    """Setzt die Beckalof-Instanz zurück (für Map-Wechsel)."""
    global _beckalof_instance
    _beckalof_instance = None
