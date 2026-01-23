# -*- coding: utf-8 -*-
"""
Blackjack Minispiel - Vollständiges Kartenspiel mit verbessertem Design

Steuerung:
- Einladung: Pfeiltasten ↑↓ zum Auswählen, Enter zum Bestätigen
- Spieler-Zug: 1 = Karte nehmen, 2 = Stehen bleiben
- Ergebnis: 3 = Schließen
"""

import pygame
import random
import math
from typing import List, Tuple, Optional, Callable
from enum import Enum

class CardSuit(Enum):
    """Kartenfarben"""
    HEARTS = "H"
    DIAMONDS = "D"
    CLUBS = "C"
    SPADES = "S"

class CardValue(Enum):
    """Kartenwerte"""
    ACE = (1, "A")
    TWO = (2, "2")
    THREE = (3, "3")
    FOUR = (4, "4")
    FIVE = (5, "5")
    SIX = (6, "6")
    SEVEN = (7, "7")
    EIGHT = (8, "8")
    NINE = (9, "9")
    TEN = (10, "10")
    JACK = (10, "J")
    QUEEN = (10, "Q")
    KING = (10, "K")

class Card:
    """Repräsentiert eine Spielkarte."""
    
    def __init__(self, suit: CardSuit, value: CardValue):
        self.suit = suit
        self.value = value
        self.face_up = True
        
    def get_value(self) -> int:
        """Gibt den numerischen Wert zurück."""
        return self.value.value[0]
    
    def get_display(self) -> str:
        """Gibt die Anzeige-String zurück."""
        return f"{self.value.value[1]}{self.suit.value}"
    
    def is_ace(self) -> bool:
        return self.value == CardValue.ACE
    
    def get_color(self) -> Tuple[int, int, int]:
        """Rot für Herz/Karo, Schwarz für Kreuz/Pik."""
        if self.suit in [CardSuit.HEARTS, CardSuit.DIAMONDS]:
            return (220, 50, 50)
        return (30, 30, 30)

class Hand:
    """Repräsentiert eine Kartenhand."""
    
    def __init__(self):
        self.cards: List[Card] = []
        
    def add_card(self, card: Card):
        self.cards.append(card)
        
    def get_value(self) -> int:
        """Berechnet den Handwert (Asse können 1 oder 11 sein)."""
        value = 0
        aces = 0
        
        for card in self.cards:
            if card.face_up:
                value += card.get_value()
                if card.is_ace():
                    aces += 1
        
        # Asse können 11 statt 1 sein, wenn es nicht über 21 geht
        while aces > 0 and value + 10 <= 21:
            value += 10
            aces -= 1
            
        return value
    
    def is_bust(self) -> bool:
        return self.get_value() > 21
    
    def is_blackjack(self) -> bool:
        return len(self.cards) == 2 and self.get_value() == 21
    
    def clear(self):
        self.cards = []

class Deck:
    """Ein Kartendeck."""
    
    def __init__(self):
        self.cards: List[Card] = []
        self.reset()
        
    def reset(self):
        self.cards = []
        for suit in CardSuit:
            for value in CardValue:
                self.cards.append(Card(suit, value))
        self.shuffle()
        
    def shuffle(self):
        random.shuffle(self.cards)
        
    def draw(self) -> Optional[Card]:
        if len(self.cards) == 0:
            self.reset()
        return self.cards.pop()

class BlackjackState(Enum):
    """Spielzustände"""
    WAITING = "waiting"
    INVITE = "invite"
    PLAYER_TURN = "player"
    DEALER_TURN = "dealer"
    RESULT = "result"

class BlackjackGame:
    """
    Vollständiges Blackjack-Minispiel mit verbessertem Design.
    """
    
    # Dealer-Phrasen
    DEALER_WIN_PHRASES = [
        "Das Glück ist heute auf meiner Seite!",
        "Tja, besser beim nächsten Mal!",
        "Die Bank gewinnt... wie immer!",
        "Haha! Deine Münzen gehören mir!",
        "Versuch's nochmal, Anfänger!"
    ]
    
    DEALER_LOSE_PHRASES = [
        "Verdammt! Gut gespielt...",
        "Du hast mich erwischt!",
        "Nimm deine Münzen und verschwinde!",
        "Anfängerglück, nichts weiter!",
        "Das nächste Mal gewinne ich!"
    ]
    
    DEALER_TIE_PHRASES = [
        "Unentschieden... langweilig!",
        "Wir sind gleich stark!",
        "Niemand gewinnt, niemand verliert.",
        "Das zählt nicht!",
        "Nochmal von vorne?"
    ]
    
    def __init__(self, screen_size: Tuple[int, int]):
        self.screen_width, self.screen_height = screen_size
        
        # Spiellogik
        self.deck = Deck()
        self.player_hand = Hand()
        self.dealer_hand = Hand()
        
        # Spielzustand
        self.state = BlackjackState.WAITING
        self.bet = 1
        self.result_message = ""
        self.dealer_phrase = ""
        self.player_coins = 0
        
        # Menü-Auswahl (für Einladung)
        self.selected_option = 0  # 0 = Ja, 1 = Nein
        
        # Animation
        self.dealer_draw_timer = 0.0
        self.pulse_timer = 0.0
        
        # Callbacks
        self.on_game_end: Optional[Callable[[int], None]] = None
        
        # UI
        self.card_width = 70
        self.card_height = 100
        self.card_spacing = 18
        
        # Fonts werden lazy geladen
        self._font_large = None
        self._font_medium = None
        self._font_small = None
        self._font_title = None
        
    @property
    def font_title(self):
        if self._font_title is None:
            self._font_title = pygame.font.Font(None, 56)
        return self._font_title
        
    @property
    def font_large(self):
        if self._font_large is None:
            self._font_large = pygame.font.Font(None, 42)
        return self._font_large
    
    @property
    def font_medium(self):
        if self._font_medium is None:
            self._font_medium = pygame.font.Font(None, 32)
        return self._font_medium
    
    @property
    def font_small(self):
        if self._font_small is None:
            self._font_small = pygame.font.Font(None, 24)
        return self._font_small
        
    @property
    def is_active(self) -> bool:
        return self.state != BlackjackState.WAITING
    
    def start_invite(self, player_coins: int):
        """Zeigt die Einladung zum Spielen."""
        self.player_coins = player_coins
        self.state = BlackjackState.INVITE
        self.selected_option = 0
        
    def accept_invite(self) -> bool:
        """Spieler akzeptiert - startet das Spiel wenn genug Münzen."""
        if self.player_coins < self.bet:
            self.result_message = "Nicht genug Münzen!"
            self.dealer_phrase = "Komm wieder wenn du Geld hast!"
            self.state = BlackjackState.RESULT
            return False
        
        self.start_game()
        return True
    
    def decline_invite(self):
        """Spieler lehnt ab."""
        self.state = BlackjackState.WAITING
        
    def start_game(self):
        """Startet eine neue Blackjack-Runde."""
        self.player_hand.clear()
        self.dealer_hand.clear()
        
        # Karten austeilen
        self.player_hand.add_card(self.deck.draw())
        self.dealer_hand.add_card(self.deck.draw())
        self.player_hand.add_card(self.deck.draw())
        
        # Dealer-Lochkarte (verdeckt)
        dealer_hidden = self.deck.draw()
        dealer_hidden.face_up = False
        self.dealer_hand.add_card(dealer_hidden)
        
        self.state = BlackjackState.PLAYER_TURN
        self.result_message = ""
        self.dealer_phrase = ""
        
        if self.player_hand.is_blackjack():
            self._reveal_dealer_and_finish()
    
    def player_hit(self):
        """Spieler nimmt eine Karte."""
        if self.state != BlackjackState.PLAYER_TURN:
            return
            
        self.player_hand.add_card(self.deck.draw())
        
        if self.player_hand.is_bust():
            self._end_round(lost=True, message="Überkauft!")
        elif self.player_hand.get_value() == 21:
            self.player_stand()
            
    def player_stand(self):
        """Spieler bleibt stehen."""
        if self.state != BlackjackState.PLAYER_TURN:
            return
        self._reveal_dealer_and_finish()
    
    def _reveal_dealer_and_finish(self):
        """Deckt die Dealer-Karte auf."""
        for card in self.dealer_hand.cards:
            card.face_up = True
        self.state = BlackjackState.DEALER_TURN
        self.dealer_draw_timer = 0.5
        
    def update(self, dt: float):
        """Aktualisiert das Spiel."""
        self.pulse_timer += dt * 3
        
        if self.state == BlackjackState.DEALER_TURN:
            self.dealer_draw_timer -= dt
            
            if self.dealer_draw_timer <= 0:
                if self.dealer_hand.get_value() < 17:
                    self.dealer_hand.add_card(self.deck.draw())
                    self.dealer_draw_timer = 0.5
                else:
                    self._determine_winner()
    
    def _determine_winner(self):
        """Ermittelt den Gewinner."""
        player_value = self.player_hand.get_value()
        dealer_value = self.dealer_hand.get_value()
        
        if self.dealer_hand.is_bust():
            self._end_round(lost=False, message="Dealer überkauft!")
        elif self.player_hand.is_blackjack() and not self.dealer_hand.is_blackjack():
            self._end_round(lost=False, message="BLACKJACK!", blackjack=True)
        elif player_value > dealer_value:
            self._end_round(lost=False, message="Du gewinnst!")
        elif player_value < dealer_value:
            self._end_round(lost=True, message="Dealer gewinnt!")
        else:
            self._end_round(lost=None, message="Unentschieden!")
    
    def _end_round(self, lost: Optional[bool], message: str, blackjack: bool = False):
        """Beendet die Runde."""
        self.result_message = message
        self.state = BlackjackState.RESULT
        
        # Dealer-Phrase auswählen
        if lost is True:
            self.dealer_phrase = random.choice(self.DEALER_WIN_PHRASES)
        elif lost is False:
            self.dealer_phrase = random.choice(self.DEALER_LOSE_PHRASES)
        else:
            self.dealer_phrase = random.choice(self.DEALER_TIE_PHRASES)
        
        # Gewinn/Verlust berechnen
        if lost is True:
            coins_change = -self.bet
        elif lost is False:
            coins_change = self.bet * (2 if blackjack else 1)
        else:
            coins_change = 0
            
        if self.on_game_end:
            self.on_game_end(coins_change)
    
    def close(self):
        """Schließt das Spiel."""
        self.state = BlackjackState.WAITING
        
    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Verarbeitet Events.
        Steuerung:
        - Einladung: Pfeile ↑↓ + Enter
        - Spieler: 1 = Hit, 2 = Stand
        - Ergebnis: 3 = Schließen
        """
        if self.state == BlackjackState.WAITING:
            return False
            
        if event.type == pygame.KEYDOWN:
            if self.state == BlackjackState.INVITE:
                # Pfeiltasten zum Auswählen
                if event.key in [pygame.K_UP, pygame.K_w]:
                    self.selected_option = 0
                    return True
                elif event.key in [pygame.K_DOWN, pygame.K_s]:
                    self.selected_option = 1
                    return True
                # C-Taste oder Enter zum Bestätigen (Braun-Knopf)
                elif event.key in [pygame.K_c, pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER]:
                    if self.selected_option == 0:
                        self.accept_invite()
                    else:
                        self.decline_invite()
                    return True
                elif event.key == pygame.K_j:
                    self.selected_option = 0
                    self.accept_invite()
                    return True
                elif event.key in [pygame.K_n, pygame.K_ESCAPE]:
                    self.decline_invite()
                    return True
                # Blockiere alle anderen Tasten während Einladung
                else:
                    return True
                    
            elif self.state == BlackjackState.PLAYER_TURN:
                # 1 = Karte nehmen (Wasser)
                if event.key in [pygame.K_1, pygame.K_KP1]:
                    self.player_hit()
                    return True
                # 2 = Stehen bleiben (Feuer)
                elif event.key in [pygame.K_2, pygame.K_KP2]:
                    self.player_stand()
                    return True
                # Blockiere alle anderen Tasten während Spieler-Zug
                else:
                    return True
                    
            elif self.state == BlackjackState.RESULT:
                # 3 = Schließen (Stein) oder C
                if event.key in [pygame.K_3, pygame.K_KP3, pygame.K_c, pygame.K_SPACE, pygame.K_RETURN, pygame.K_ESCAPE]:
                    self.close()
                    return True
                # Blockiere alle anderen Tasten während Ergebnis
                else:
                    return True
            
            elif self.state == BlackjackState.DEALER_TURN:
                # Blockiere alle Tasten während Dealer zieht
                return True
                    
        # Blockiere auch Maus-Events wenn aktiv
        if event.type in [pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP]:
            return True
                    
        return False
    
    def _draw_glassmorphism_panel(self, screen: pygame.Surface, rect: pygame.Rect, 
                                   alpha: int = 220):
        """Zeichnet ein Panel mit Glassmorphism-Effekt."""
        panel = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        
        # Gradient-Hintergrund
        for y in range(rect.height):
            progress = y / rect.height
            r = int(20 + progress * 15)
            g = int(50 + progress * 25)
            b = int(35 + progress * 20)
            pygame.draw.line(panel, (r, g, b, alpha), (0, y), (rect.width, y))
        
        # Oberer Glanz
        gloss = pygame.Surface((rect.width, rect.height // 4), pygame.SRCALPHA)
        for y in range(gloss.get_height()):
            alpha_line = int(40 * (1 - y / gloss.get_height()))
            pygame.draw.line(gloss, (255, 255, 255, alpha_line), (0, y), (rect.width, y))
        panel.blit(gloss, (0, 0))
        
        screen.blit(panel, rect.topleft)
        
        # Goldener Rahmen
        pygame.draw.rect(screen, (100, 80, 30), rect.inflate(4, 4), 4, border_radius=15)
        pygame.draw.rect(screen, (255, 215, 0), rect, 3, border_radius=15)
        
        # Innerer Rahmen
        inner_rect = rect.inflate(-6, -6)
        pygame.draw.rect(screen, (255, 255, 255, 30), inner_rect, 1, border_radius=12)
    
    def _draw_button(self, screen: pygame.Surface, rect: pygame.Rect, text: str, 
                     selected: bool, enabled: bool = True):
        """Zeichnet einen Button."""
        if not enabled:
            bg_color = (60, 60, 60, 180)
            text_color = (120, 120, 120)
            border_color = (80, 80, 80)
        elif selected:
            pulse = abs(math.sin(self.pulse_timer))
            bg_color = (40 + int(30 * pulse), 100 + int(30 * pulse), 50, 230)
            text_color = (255, 255, 200)
            border_color = (255, 215, 0)
        else:
            bg_color = (30, 50, 40, 200)
            text_color = (200, 200, 200)
            border_color = (100, 100, 100)
        
        btn_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        pygame.draw.rect(btn_surface, bg_color, btn_surface.get_rect(), border_radius=8)
        screen.blit(btn_surface, rect.topleft)
        
        pygame.draw.rect(screen, border_color, rect, 2, border_radius=8)
        
        text_surf = self.font_medium.render(text, True, text_color)
        text_rect = text_surf.get_rect(center=rect.center)
        screen.blit(text_surf, text_rect)
        
        if selected and enabled:
            arrow = self.font_medium.render(">", True, (255, 215, 0))
            screen.blit(arrow, (rect.left - 25, rect.centery - arrow.get_height() // 2))
    
    def render(self, screen: pygame.Surface):
        """Zeichnet das Blackjack-Spiel."""
        if self.state == BlackjackState.WAITING:
            return
            
        # Overlay
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        
        # Spieltisch
        table_rect = pygame.Rect(
            self.screen_width // 2 - 350,
            self.screen_height // 2 - 230,
            700, 460
        )
        self._draw_glassmorphism_panel(screen, table_rect)
        
        # Titel
        title_shadow = self.font_title.render("BLACKJACK", True, (0, 0, 0))
        title = self.font_title.render("BLACKJACK", True, (255, 215, 0))
        screen.blit(title_shadow, (self.screen_width // 2 - title.get_width() // 2 + 2, table_rect.top + 17))
        screen.blit(title, (self.screen_width // 2 - title.get_width() // 2, table_rect.top + 15))
        
        # Münzen-Anzeige
        coins_bg = pygame.Rect(table_rect.left + 15, table_rect.top + 15, 140, 35)
        pygame.draw.rect(screen, (0, 0, 0, 150), coins_bg, border_radius=8)
        pygame.draw.rect(screen, (200, 170, 50), coins_bg, 2, border_radius=8)
        coins_text = self.font_medium.render(f"{self.player_coins} Coins", True, (255, 215, 0))
        screen.blit(coins_text, (coins_bg.x + 10, coins_bg.y + 5))
        
        if self.state == BlackjackState.INVITE:
            self._render_invite(screen, table_rect)
        else:
            self._render_game(screen, table_rect)
    
    def _render_invite(self, screen: pygame.Surface, table_rect: pygame.Rect):
        """Zeichnet die Einladung."""
        center_x = table_rect.centerx
        center_y = table_rect.centery
        
        # Dealer-Icon (Karten-Symbol statt Emoji)
        dealer_icon_rect = pygame.Rect(center_x - 40, center_y - 120, 80, 80)
        pygame.draw.rect(screen, (50, 40, 60), dealer_icon_rect, border_radius=40)
        pygame.draw.rect(screen, (200, 170, 50), dealer_icon_rect, 2, border_radius=40)
        # Zeichne Karten-Symbol statt Emoji
        card_text = self.font_title.render("BJ", True, (255, 215, 0))
        screen.blit(card_text, (center_x - card_text.get_width() // 2, center_y - 105))
        
        # Dialog-Box
        dialog_rect = pygame.Rect(center_x - 200, center_y - 25, 400, 70)
        pygame.draw.rect(screen, (20, 20, 30, 220), dialog_rect, border_radius=10)
        pygame.draw.rect(screen, (150, 130, 80), dialog_rect, 2, border_radius=10)
        
        invite_text = self.font_medium.render("Möchtest du Blackjack spielen?", True, (255, 255, 255))
        screen.blit(invite_text, (center_x - invite_text.get_width() // 2, center_y - 15))
        
        bet_text = self.font_small.render("Einsatz: 1 Münze pro Runde", True, (180, 180, 180))
        screen.blit(bet_text, (center_x - bet_text.get_width() // 2, center_y + 20))
        
        # Buttons
        btn_width = 160
        btn_height = 45
        btn_y = center_y + 70
        
        can_play = self.player_coins >= self.bet
        
        yes_rect = pygame.Rect(center_x - btn_width - 20, btn_y, btn_width, btn_height)
        self._draw_button(screen, yes_rect, "Ja, spielen!", self.selected_option == 0, can_play)
        
        no_rect = pygame.Rect(center_x + 20, btn_y, btn_width, btn_height)
        self._draw_button(screen, no_rect, "Nein, danke", self.selected_option == 1)
        
        # Steuerungshinweis
        hint = self.font_small.render("Pfeile Auswaehlen  -  C Bestaetigen", True, (150, 150, 150))
        screen.blit(hint, (center_x - hint.get_width() // 2, table_rect.bottom - 40))
        
        if not can_play:
            warning = self.font_small.render("! Nicht genug Muenzen!", True, (255, 100, 100))
            screen.blit(warning, (center_x - warning.get_width() // 2, btn_y + btn_height + 15))
    
    def _render_game(self, screen: pygame.Surface, table_rect: pygame.Rect):
        """Zeichnet das aktive Spiel."""
        center_x = table_rect.centerx
        
        # Dealer-Bereich
        dealer_y = table_rect.top + 80
        dealer_label_bg = pygame.Rect(center_x - 180, dealer_y - 5, 80, 28)
        pygame.draw.rect(screen, (0, 0, 0, 150), dealer_label_bg, border_radius=5)
        label = self.font_small.render("Dealer", True, (255, 200, 100))
        screen.blit(label, (dealer_label_bg.x + 10, dealer_label_bg.y + 5))
        
        self._render_hand(screen, self.dealer_hand, center_x, dealer_y)
        
        if all(c.face_up for c in self.dealer_hand.cards):
            value_text = self.font_medium.render(f"{self.dealer_hand.get_value()}", True, (255, 255, 255))
            value_bg = pygame.Rect(center_x + 130, dealer_y + 35, 40, 30)
            pygame.draw.rect(screen, (0, 0, 0, 180), value_bg, border_radius=5)
            screen.blit(value_text, (value_bg.centerx - value_text.get_width() // 2, value_bg.y + 3))
        
        # Trennlinie
        pygame.draw.line(screen, (100, 80, 50), 
                        (table_rect.left + 50, table_rect.centery), 
                        (table_rect.right - 50, table_rect.centery), 2)
        
        # Spieler-Bereich
        player_y = table_rect.bottom - 180
        player_label_bg = pygame.Rect(center_x - 180, player_y - 5, 60, 28)
        pygame.draw.rect(screen, (0, 0, 0, 150), player_label_bg, border_radius=5)
        label = self.font_small.render("Du", True, (100, 200, 255))
        screen.blit(label, (player_label_bg.x + 15, player_label_bg.y + 5))
        
        self._render_hand(screen, self.player_hand, center_x, player_y)
        
        value_text = self.font_medium.render(f"{self.player_hand.get_value()}", True, (255, 255, 255))
        value_bg = pygame.Rect(center_x + 130, player_y + 35, 40, 30)
        pygame.draw.rect(screen, (0, 0, 0, 180), value_bg, border_radius=5)
        screen.blit(value_text, (value_bg.centerx - value_text.get_width() // 2, value_bg.y + 3))
        
        control_y = table_rect.bottom - 55
        
        if self.state == BlackjackState.PLAYER_TURN:
            hit_rect = pygame.Rect(center_x - 170, control_y - 10, 150, 40)
            stand_rect = pygame.Rect(center_x + 20, control_y - 10, 150, 40)
            
            # Hit Button (Wasser = blau)
            pygame.draw.rect(screen, (30, 80, 150, 220), hit_rect, border_radius=8)
            pygame.draw.rect(screen, (100, 180, 255), hit_rect, 2, border_radius=8)
            hit_text = self.font_medium.render("1  Karte", True, (200, 230, 255))
            screen.blit(hit_text, (hit_rect.centerx - hit_text.get_width() // 2, hit_rect.y + 8))
            
            # Stand Button (Feuer = rot)
            pygame.draw.rect(screen, (150, 50, 30, 220), stand_rect, border_radius=8)
            pygame.draw.rect(screen, (255, 150, 100), stand_rect, 2, border_radius=8)
            stand_text = self.font_medium.render("2  Stehen", True, (255, 220, 200))
            screen.blit(stand_text, (stand_rect.centerx - stand_text.get_width() // 2, stand_rect.y + 8))
            
        elif self.state == BlackjackState.DEALER_TURN:
            hint = self.font_medium.render("Dealer zieht...", True, (255, 200, 100))
            screen.blit(hint, (center_x - hint.get_width() // 2, control_y))
            
        elif self.state == BlackjackState.RESULT:
            result_rect = pygame.Rect(center_x - 200, table_rect.centery - 60, 400, 120)
            pygame.draw.rect(screen, (20, 20, 30, 240), result_rect, border_radius=15)
            pygame.draw.rect(screen, (255, 215, 0), result_rect, 3, border_radius=15)
            
            # Ergebnis-Farbe
            msg_lower = self.result_message.lower()
            if "gewinn" in msg_lower or "blackjack" in msg_lower:
                result_color = (100, 255, 100)
            elif "verlier" in msg_lower or "überkauft" in msg_lower or "dealer" in msg_lower:
                result_color = (255, 100, 100)
            else:
                result_color = (255, 255, 100)
            
            result = self.font_large.render(self.result_message, True, result_color)
            screen.blit(result, (center_x - result.get_width() // 2, result_rect.y + 15))
            
            if self.dealer_phrase:
                phrase = self.font_small.render(f'"{self.dealer_phrase}"', True, (200, 200, 200))
                screen.blit(phrase, (center_x - phrase.get_width() // 2, result_rect.y + 55))
            
            # Schließen (Stein = braun)
            close_rect = pygame.Rect(center_x - 80, result_rect.bottom + 10, 160, 35)
            pygame.draw.rect(screen, (100, 70, 40, 220), close_rect, border_radius=8)
            pygame.draw.rect(screen, (180, 140, 80), close_rect, 2, border_radius=8)
            close_text = self.font_medium.render("3  Schließen", True, (220, 190, 140))
            screen.blit(close_text, (close_rect.centerx - close_text.get_width() // 2, close_rect.y + 5))
    
    def _render_hand(self, screen: pygame.Surface, hand: Hand, x: int, y: int):
        """Zeichnet eine Kartenhand."""
        total_width = len(hand.cards) * (self.card_width + self.card_spacing) - self.card_spacing
        start_x = x - total_width // 2
        
        for i, card in enumerate(hand.cards):
            card_x = start_x + i * (self.card_width + self.card_spacing)
            self._render_card(screen, card, card_x, y)
    
    def _render_card(self, screen: pygame.Surface, card: Card, x: int, y: int):
        """Zeichnet eine einzelne Karte."""
        rect = pygame.Rect(x, y, self.card_width, self.card_height)
        
        if card.face_up:
            # Schatten
            shadow_rect = rect.move(3, 3)
            pygame.draw.rect(screen, (20, 20, 20), shadow_rect, border_radius=8)
            
            # Karten-Hintergrund
            card_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            for cy in range(rect.height):
                brightness = 255 - int(cy * 0.15)
                pygame.draw.line(card_surf, (brightness, brightness, brightness - 10), 
                               (0, cy), (rect.width, cy))
            screen.blit(card_surf, rect.topleft)
            
            pygame.draw.rect(screen, (80, 80, 80), rect, 2, border_radius=8)
            
            display = card.get_display()
            color = card.get_color()
            
            text = self.font_large.render(display, True, color)
            text_rect = text.get_rect(center=rect.center)
            screen.blit(text, text_rect)
            
            corner_text = self.font_small.render(card.value.value[1], True, color)
            screen.blit(corner_text, (rect.x + 5, rect.y + 3))
            
        else:
            shadow_rect = rect.move(3, 3)
            pygame.draw.rect(screen, (20, 20, 20), shadow_rect, border_radius=8)
            
            pygame.draw.rect(screen, (30, 50, 120), rect, border_radius=8)
            pygame.draw.rect(screen, (20, 40, 100), rect, 2, border_radius=8)
            
            inner = rect.inflate(-10, -10)
            pygame.draw.rect(screen, (50, 80, 160), inner, border_radius=5)
            
            # Diagonales Muster
            for i in range(-rect.height, rect.width, 12):
                start_x = max(rect.x + 5, rect.x + i)
                end_x = min(rect.right - 5, rect.x + i + rect.height)
                start_y = max(rect.y + 5, rect.y + (rect.x + 5 - (rect.x + i)))
                end_y = min(rect.bottom - 5, rect.y + (end_x - (rect.x + i)))
                if start_x < end_x:
                    pygame.draw.line(screen, (70, 100, 180), (start_x, start_y), (end_x, end_y), 1)
