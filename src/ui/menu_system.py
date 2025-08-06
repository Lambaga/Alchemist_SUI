# -*- coding: utf-8 -*-
"""
Menu System for the Alchemist Game
Provides main menu, settings, credits, and game state management
"""

import pygame
import sys
import os
from typing import Optional, List, Dict, Any
from enum import Enum
from settings import *
from save_system import save_manager

class GameState(Enum):
    """Game state enumeration"""
    MAIN_MENU = "main_menu"
    NEW_GAME = "new_game"
    LOAD_GAME = "load_game"
    SETTINGS = "settings"
    CREDITS = "credits"
    GAMEPLAY = "gameplay"
    PAUSE = "pause"
    GAME_OVER = "game_over"
    QUIT = "quit"

class SavePopup:
    """Pop-up for save confirmation"""
    
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.active = False
        self.message = ""
        self.message_type = "success"  # "success" or "warning"
        self.timer = 0
        self.duration = 2000  # 2 seconds
        self.font = pygame.font.Font(None, 48)
        self.small_font = pygame.font.Font(None, 36)
        
        # Pop-up dimensions
        self.width = 400
        self.height = 150
        self.x = (screen.get_width() - self.width) // 2
        self.y = (screen.get_height() - self.height) // 2
        
        # Colors
        self.bg_color = (30, 30, 50)
        self.border_color_success = (100, 200, 100)
        self.border_color_warning = (200, 200, 100)
        self.text_color = (255, 255, 255)
        self.success_color = (100, 255, 100)
        self.warning_color = (255, 255, 100)
    
    def show(self, message: str, message_type: str = "success"):
        """Show the pop-up with a message"""
        self.message = message
        self.message_type = message_type
        self.active = True
        self.timer = pygame.time.get_ticks()
    
    def update(self):
        """Update the pop-up state"""
        if self.active and pygame.time.get_ticks() - self.timer > self.duration:
            self.active = False
    
    def draw(self):
        """Draw the pop-up"""
        if not self.active:
            return
            
        # Draw semi-transparent background
        overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()))
        overlay.set_alpha(128)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        # Choose colors based on message type
        if self.message_type == "success":
            border_color = self.border_color_success
            icon_color = self.success_color
            icon_text = "✅"
        else:
            border_color = self.border_color_warning
            icon_color = self.warning_color
            icon_text = "⚠️"
        
        # Draw pop-up box
        popup_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(self.screen, self.bg_color, popup_rect)
        pygame.draw.rect(self.screen, border_color, popup_rect, 3)
        
        # Draw icon
        icon_surface = self.font.render(icon_text, True, icon_color)
        icon_rect = icon_surface.get_rect(center=(self.x + self.width // 2, self.y + 50))
        self.screen.blit(icon_surface, icon_rect)
        
        # Draw message
        message_surface = self.small_font.render(self.message, True, self.text_color)
        message_rect = message_surface.get_rect(center=(self.x + self.width // 2, self.y + 100))
        self.screen.blit(message_surface, message_rect)

class MenuButton:
    """A clickable menu button"""
    
    def __init__(self, x: int, y: int, width: int, height: int, text: str, 
                 font: pygame.font.Font, action: GameState = None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.action = action
        self.hovered = False
        self.clicked = False
        
        # Colors
        self.normal_color = (40, 40, 60)
        self.hover_color = (60, 60, 90)
        self.click_color = (80, 80, 120)
        self.text_color = (255, 255, 255)
        self.border_color = (100, 100, 150)
    
    def update(self, mouse_pos: tuple, mouse_clicked: bool) -> bool:
        """Update button state and return True if clicked"""
        self.hovered = self.rect.collidepoint(mouse_pos)
        
        if self.hovered and mouse_clicked:
            self.clicked = True
            return True
        else:
            self.clicked = False
            return False
    
    def draw(self, screen: pygame.Surface):
        """Draw the button"""
        # Choose color based on state
        if self.clicked:
            color = self.click_color
        elif self.hovered:
            color = self.hover_color
        else:
            color = self.normal_color
        
        # Draw button background
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, self.border_color, self.rect, 2)
        
        # Draw text with emoji support
        try:
            # Try to render with the font that supports emojis
            text_surface = self.font.render(self.text, True, self.text_color)
        except (UnicodeEncodeError, UnicodeError):
            # Fallback if emojis can't be rendered - remove emojis
            fallback_text = ''.join(char for char in self.text if ord(char) < 128)
            text_surface = self.font.render(fallback_text, True, self.text_color)
        
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

class BaseMenuState:
    """Base class for all menu states"""
    
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.buttons: List[MenuButton] = []
        
        # Try to use system fonts that support emojis better
        try:
            # Try Segoe UI Emoji (Windows) first for better emoji support
            self.title_font = pygame.font.SysFont('segoeuiemoji', 56)  # Smaller title
            self.button_font = pygame.font.SysFont('segoeuiemoji', 36)  # Smaller buttons
            self.text_font = pygame.font.SysFont('segoeuiemoji', 28)   # Smaller text
            self.emoji_font = self.button_font  # Add emoji_font reference
        except:
            try:
                # Fallback to Segoe UI (Windows default)
                self.title_font = pygame.font.SysFont('segoeui', 56)
                self.button_font = pygame.font.SysFont('segoeui', 36)
                self.text_font = pygame.font.SysFont('segoeui', 28)
                self.emoji_font = self.button_font
            except:
                # Final fallback to pygame default fonts
                self.title_font = pygame.font.Font(None, 56)
                self.button_font = pygame.font.Font(None, 36)
                self.text_font = pygame.font.Font(None, 28)
                self.emoji_font = self.button_font
        
        self.background_color = (20, 20, 40)
        
    def handle_event(self, event: pygame.event.Event) -> Optional[GameState]:
        """Handle events and return new state if needed"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            for button in self.buttons:
                if button.update(mouse_pos, True):
                    return button.action
        elif event.type == pygame.MOUSEMOTION:
            mouse_pos = pygame.mouse.get_pos()
            for button in self.buttons:
                button.update(mouse_pos, False)
        
        return None
    
    def update(self, dt: float):
        """Update menu state"""
        pass
    
    def draw(self):
        """Draw the menu"""
        self.screen.fill(self.background_color)
        for button in self.buttons:
            button.draw(self.screen)

class MainMenuState(BaseMenuState):
    """Main menu state"""
    
    def __init__(self, screen: pygame.Surface):
        super().__init__(screen)
        self.setup_buttons()
        self.save_popup = SavePopup(screen)
        
    def setup_buttons(self):
        """Setup main menu buttons"""
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()
        
        button_width = 320  # Breiter für bessere Textpassung
        button_height = 50
        button_spacing = 65
        start_y = screen_height // 2 - 120
        
        buttons_data = [
            ("🎮 Neues Spiel", GameState.NEW_GAME),
            ("💾 Spiel speichern", "save_game"),
            ("📁 Spiel laden", GameState.LOAD_GAME),
            ("⚙️ Einstellungen", GameState.SETTINGS),
            ("📜 Credits", GameState.CREDITS),
            ("❌ Beenden", GameState.QUIT)
        ]
        
        # Fallback text without emojis if font doesn't support them
        fallback_buttons_data = [
            ("[NEW] Neues Spiel", GameState.NEW_GAME),
            ("[SAVE] Spiel speichern", "save_game"),
            ("[LOAD] Spiel laden", GameState.LOAD_GAME),
            ("[SET] Einstellungen", GameState.SETTINGS),
            ("[INFO] Credits", GameState.CREDITS),
            ("[EXIT] Beenden", GameState.QUIT)
        ]
        
        for i, (text, action) in enumerate(buttons_data):
            x = screen_width // 2 - button_width // 2
            y = start_y + i * button_spacing
            
            # Test if emojis render properly by checking if the first emoji renders
            test_emoji = "🎮"
            emoji_works = False
            try:
                test_surface = self.emoji_font.render(test_emoji, True, (255, 255, 255))
                # Check if emoji renders properly (width should be reasonable for emoji)
                if test_surface.get_width() > 20 and test_surface.get_height() > 15:
                    emoji_works = True
            except:
                pass
            
            # Use fallback text if emojis don't work
            if not emoji_works:
                text = fallback_buttons_data[i][0]
            
            button = MenuButton(x, y, button_width, button_height, 
                              text, self.button_font, action)
            self.buttons.append(button)
    
    def handle_event(self, event: pygame.event.Event) -> Optional[Any]:
        """Handle main menu events"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            for button in self.buttons:
                if button.update(mouse_pos, True):
                    if button.action == "save_game":
                        return "save_game"  # Special action for saving
                    else:
                        return button.action
        elif event.type == pygame.MOUSEMOTION:
            mouse_pos = pygame.mouse.get_pos()
            for button in self.buttons:
                button.update(mouse_pos, False)
        
        return None
    
    def update(self, dt: float):
        """Update main menu state"""
        self.save_popup.update()
    
    def show_save_confirmation(self):
        """Show save confirmation pop-up"""
        self.save_popup.show("Spiel gespeichert!")
    
    def show_no_game_message(self):
        """Show message when no game is active"""
        self.save_popup.show("Kein aktives Spiel!", "warning")
    
    def draw(self):
        """Draw main menu"""
        super().draw()
        
        # Title
        title_text = "🧙‍♂️ Der Alchemist"
        title_surface = self.title_font.render(title_text, True, (255, 215, 0))
        title_rect = title_surface.get_rect(center=(self.screen.get_width() // 2, 120))
        self.screen.blit(title_surface, title_rect)
        
        # Subtitle
        subtitle_text = "Ein magisches Abenteuer"
        subtitle_surface = self.text_font.render(subtitle_text, True, (200, 200, 200))
        subtitle_rect = subtitle_surface.get_rect(center=(self.screen.get_width() // 2, 160))
        self.screen.blit(subtitle_surface, subtitle_rect)
        
        # Draw save pop-up on top
        self.save_popup.draw()

class SettingsMenuState(BaseMenuState):
    """Settings menu state"""
    
    def __init__(self, screen: pygame.Surface):
        super().__init__(screen)
        self.settings = self.load_settings()
        self.setup_buttons()
    
    def load_settings(self) -> Dict[str, Any]:
        """Load current settings"""
        return {
            "music_volume": 0.7,
            "sound_volume": 0.8,
            "fullscreen": False,
            "show_fps": True,
            "difficulty": "Normal"
        }
    
    def setup_buttons(self):
        """Setup settings menu buttons"""
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()
        
        # Back button
        back_button = MenuButton(50, screen_height - 80, 180, 50, 
                               "← Zurück", self.button_font, GameState.MAIN_MENU)
        self.buttons.append(back_button)
    
    def draw(self):
        """Draw settings menu"""
        super().draw()
        
        # Title
        title_text = "⚙️ Einstellungen"
        title_surface = self.title_font.render(title_text, True, (255, 215, 0))
        title_rect = title_surface.get_rect(center=(self.screen.get_width() // 2, 100))
        self.screen.blit(title_surface, title_rect)
        
        # Settings options (placeholder for now)
        y_offset = 200
        settings_text = [
            f"🎵 Musik Lautstärke: {int(self.settings['music_volume'] * 100)}%",
            f"🔊 Sound Lautstärke: {int(self.settings['sound_volume'] * 100)}%",
            f"🖥️ Vollbild: {'Ein' if self.settings['fullscreen'] else 'Aus'}",
            f"📊 FPS anzeigen: {'Ein' if self.settings['show_fps'] else 'Aus'}",
            f"⚔️ Schwierigkeit: {self.settings['difficulty']}"
        ]
        
        for i, text in enumerate(settings_text):
            text_surface = self.text_font.render(text, True, (200, 200, 200))
            self.screen.blit(text_surface, (100, y_offset + i * 40))

class CreditsMenuState(BaseMenuState):
    """Credits menu state"""
    
    def __init__(self, screen: pygame.Surface):
        super().__init__(screen)
        self.setup_buttons()
    
    def setup_buttons(self):
        """Setup credits menu buttons"""
        screen_height = self.screen.get_height()
        
        # Back button
        back_button = MenuButton(50, screen_height - 80, 180, 50, 
                               "← Zurück", self.button_font, GameState.MAIN_MENU)
        self.buttons.append(back_button)
    
    def draw(self):
        """Draw credits menu"""
        super().draw()
        
        # Title
        title_text = "📜 Credits"
        title_surface = self.title_font.render(title_text, True, (255, 215, 0))
        title_rect = title_surface.get_rect(center=(self.screen.get_width() // 2, 100))
        self.screen.blit(title_surface, title_rect)
        
        # Credits content
        credits_text = [
            "",
            "🧙‍♂️ Der Alchemist",
            "",
            "👥 Entwicklungsteam:",
            "• Kirill Lambaga",
            "• Jonas Dagger", 
            "• Christian Fußmann",
            "• Waseem Hayat",
            "• Simon Milkyboy",
            "",
            "Entwickelt mit Python & Pygame",
            "",
            "📌 Features:",
            "• Magisches Gameplay",
            "• Alchemie System",
            "• Feinde und Kämpfe",
            "• Karten und Erkundung",
            "",
            "🎨 Assets:",
            "• Sprite Sammlungen",
            "• Tiled Map Editor",
            "• Pygame Community",
            "",
            "💻 Technologie:",
            "• Python 3.9+",
            "• Pygame",
            "• Tiled TMX Maps",
            "",
            "Vielen Dank fürs Spielen! 🎮"
        ]
        
        y_offset = 150
        for line in credits_text:
            if line:  # Skip empty lines
                text_surface = self.text_font.render(line, True, (200, 200, 200))
                text_rect = text_surface.get_rect(center=(self.screen.get_width() // 2, y_offset))
                self.screen.blit(text_surface, text_rect)
            y_offset += 25

class LoadGameMenuState(BaseMenuState):
    """Load game menu state"""
    
    def __init__(self, screen: pygame.Surface):
        super().__init__(screen)
        self.save_slots = []
        self.selected_slot = None
        self.refresh_save_slots()
        self.setup_buttons()
    
    def refresh_save_slots(self):
        """Refresh save slots from save system"""
        self.save_slots = save_manager.get_save_slots_info()
    
    def setup_buttons(self):
        """Setup load game menu buttons"""
        self.buttons.clear()  # Clear existing buttons
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()
        
        # Save slot buttons
        for i, save_slot in enumerate(self.save_slots):
            if save_slot["exists"]:
                button_text = f"{save_slot['name']} - {save_slot['level']}"
                button = MenuButton(screen_width // 2 - 270, 180 + i * 70, 
                                  540, 50, button_text, self.button_font)
                button.action = ("load_slot", save_slot["slot"])  # Custom action with slot number
                self.buttons.append(button)
        
        # Back button
        back_button = MenuButton(50, screen_height - 80, 180, 50, 
                               "← Zurück", self.button_font, GameState.MAIN_MENU)
        self.buttons.append(back_button)
    
    def handle_event(self, event: pygame.event.Event) -> Optional[GameState]:
        """Handle events for load game menu"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            for button in self.buttons:
                if button.update(mouse_pos, True):
                    if isinstance(button.action, tuple) and button.action[0] == "load_slot":
                        self.selected_slot = button.action[1]
                        return ("load_game", self.selected_slot)  # Return special load action
                    else:
                        return button.action
        elif event.type == pygame.MOUSEMOTION:
            mouse_pos = pygame.mouse.get_pos()
            for button in self.buttons:
                button.update(mouse_pos, False)
        
        return None
    
    def draw(self):
        """Draw load game menu"""
        super().draw()
        
        # Title
        title_text = "📁 Spiel laden"
        title_surface = self.title_font.render(title_text, True, (255, 215, 0))
        title_rect = title_surface.get_rect(center=(self.screen.get_width() // 2, 100))
        self.screen.blit(title_surface, title_rect)
        
        # Show save slot details
        y_offset = 180
        for i, slot in enumerate(self.save_slots):
            if slot["exists"]:
                # Show additional details for existing saves
                date_text = f"Gespeichert: {slot['date']}"
                date_surface = self.text_font.render(date_text, True, (150, 150, 150))
                self.screen.blit(date_surface, (self.screen.get_width() // 2 - 240, y_offset + 55))
            y_offset += 70
        
        # If no saves available
        if not any(slot["exists"] for slot in self.save_slots):
            no_saves_text = "Keine Speicherstände gefunden"
            text_surface = self.text_font.render(no_saves_text, True, (150, 150, 150))
            text_rect = text_surface.get_rect(center=(self.screen.get_width() // 2, 300))
            self.screen.blit(text_surface, text_rect)

class PauseMenuState(BaseMenuState):
    """Pause menu state (shown during gameplay)"""
    
    def __init__(self, screen: pygame.Surface):
        super().__init__(screen)
        self.show_save_menu = False
        self.setup_buttons()
        # Semi-transparent background
        self.background_color = (0, 0, 0, 180)
        self.background_surface = pygame.Surface((screen.get_width(), screen.get_height()))
        self.background_surface.set_alpha(180)
        self.background_surface.fill((0, 0, 0))
        self.save_buttons = []
        self.setup_save_buttons()
    
    def setup_buttons(self):
        """Setup pause menu buttons"""
        self.buttons.clear()
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()
        
        button_width = 340  # Breiter für bessere Textpassung
        button_height = 55
        button_spacing = 70
        start_y = screen_height // 2 - 120
        
        if not self.show_save_menu:
            buttons_data = [
                ("▶️ Weiter spielen", "resume"),
                ("💾 Spiel speichern", "show_save_menu"),
                ("📁 Spiel laden", GameState.LOAD_GAME),
                ("📋 Hauptmenü", GameState.MAIN_MENU),
                ("❌ Spiel beenden", GameState.QUIT)
            ]
        else:
            # Save menu buttons with slot information
            buttons_data = [
                ("💾 Schnell speichern (Slot 1)", "save_slot_1"),
                ("💾 Speichern in Slot 2", "save_slot_2"),  
                ("💾 Speichern in Slot 3", "save_slot_3"),
                ("💾 Speichern in Slot 4", "save_slot_4"),
                ("🔙 Zurück", "back_to_pause")
            ]
        
        for i, (text, action) in enumerate(buttons_data):
            x = screen_width // 2 - button_width // 2
            y = start_y + i * button_spacing
            button = MenuButton(x, y, button_width, button_height, 
                              text, self.button_font, action)
            self.buttons.append(button)
    
    def setup_save_buttons(self):
        """Setup save slot buttons with previews"""
        self.save_buttons.clear()
        # This could be enhanced to show save slot previews
        pass
    
    def handle_event(self, event: pygame.event.Event) -> Optional[Any]:
        """Handle pause menu events"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            for button in self.buttons:
                if button.update(mouse_pos, True):
                    if button.action == "show_save_menu":
                        self.show_save_menu = True
                        self.setup_buttons()
                        return None
                    elif button.action == "back_to_pause":
                        self.show_save_menu = False
                        self.setup_buttons()
                        return None
                    elif button.action == "save_slot_1":
                        return ("save_to_slot", 1)
                    elif button.action == "save_slot_2":
                        return ("save_to_slot", 2)
                    elif button.action == "save_slot_3":
                        return ("save_to_slot", 3)
                    elif button.action == "save_slot_4":
                        return ("save_to_slot", 4)
                    else:
                        return button.action
        elif event.type == pygame.MOUSEMOTION:
            mouse_pos = pygame.mouse.get_pos()
            for button in self.buttons:
                button.update(mouse_pos, False)
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.show_save_menu:
                    self.show_save_menu = False
                    self.setup_buttons()
                    return None
                else:
                    return "resume"
            elif self.show_save_menu:
                # Direct save shortcuts in save menu
                if event.key == pygame.K_1:
                    return ("save_to_slot", 1)
                elif event.key == pygame.K_2:
                    return ("save_to_slot", 2)
                elif event.key == pygame.K_3:
                    return ("save_to_slot", 3)
                elif event.key == pygame.K_4:
                    return ("save_to_slot", 4)
        
        return None

    def draw(self):
        """Draw pause menu"""
        # Draw semi-transparent background
        self.screen.blit(self.background_surface, (0, 0))
        
        # Title
        if not self.show_save_menu:
            title_text = "⏸️ Spiel Pausiert"
            subtitle_text = "ESC zum Fortsetzen"
        else:
            title_text = "💾 Spiel Speichern"
            subtitle_text = "Wähle einen Speicherplatz"
            
        title_surface = self.title_font.render(title_text, True, (255, 215, 0))
        title_rect = title_surface.get_rect(center=(self.screen.get_width() // 2, 180))
        self.screen.blit(title_surface, title_rect)
        
        # Subtitle
        subtitle_surface = self.text_font.render(subtitle_text, True, (200, 200, 200))
        subtitle_rect = subtitle_surface.get_rect(center=(self.screen.get_width() // 2, 220))
        self.screen.blit(subtitle_surface, subtitle_rect)
        
        # Draw buttons
        for button in self.buttons:
            button.draw(self.screen)
            
        # Additional save menu information
        if self.show_save_menu:
            info_text = "💡 Tipp: F9-F12 für Schnellspeichern in Slots 1-4"
            info_surface = pygame.font.Font(None, 28).render(info_text, True, (150, 150, 150))
            info_rect = info_surface.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() - 100))
            self.screen.blit(info_surface, info_rect)
            
            # Show keyboard shortcuts
            shortcuts_text = "⌨️ ESC: Zurück  •  1-4: Direkt speichern"
            shortcuts_surface = pygame.font.Font(None, 24).render(shortcuts_text, True, (120, 120, 120))
            shortcuts_rect = shortcuts_surface.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() - 70))
            self.screen.blit(shortcuts_surface, shortcuts_rect)
        else:
            # Show main pause menu shortcuts
            shortcuts_text = "⌨️ ESC: Fortsetzen  •  F9-F12: Schnellspeichern"  
            shortcuts_surface = pygame.font.Font(None, 24).render(shortcuts_text, True, (120, 120, 120))
            shortcuts_rect = shortcuts_surface.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() - 70))
            self.screen.blit(shortcuts_surface, shortcuts_rect)

class GameOverMenuState(BaseMenuState):
    """Game Over menu state (shown when player dies)"""
    
    def __init__(self, screen: pygame.Surface):
        super().__init__(screen)
        self.setup_buttons()
        # Dark semi-transparent background
        self.background_color = (0, 0, 0, 240)  # Darker background
        self.background_surface = pygame.Surface((screen.get_width(), screen.get_height()))
        self.background_surface.set_alpha(240)  # More opaque
        self.background_surface.fill((0, 0, 0))  # Pure black
        
        # Animation timer for dramatic effect
        self.animation_timer = 0
        self.fade_in_duration = 500  # 0.5 seconds fade in (faster)
    
    def setup_buttons(self):
        """Setup game over menu buttons"""
        self.buttons.clear()
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()
        
        button_width = 300
        button_height = 55
        button_spacing = 80
        start_y = screen_height // 2 + 50
        
        buttons_data = [
            ("🔄 Spiel neu starten", "restart_game"),
            ("📁 Spiel laden", GameState.LOAD_GAME),
            ("📋 Hauptmenü", GameState.MAIN_MENU),
            ("❌ Spiel beenden", GameState.QUIT)
        ]
        
        for i, (text, action) in enumerate(buttons_data):
            x = screen_width // 2 - button_width // 2
            y = start_y + i * button_spacing
            button = MenuButton(x, y, button_width, button_height, 
                              text, self.button_font, action)
            self.buttons.append(button)
    
    def update(self, dt: float):
        """Update game over state"""
        self.animation_timer += dt * 1000  # Convert seconds to milliseconds
    
    def draw(self):
        """Draw game over menu"""
        # Draw dark semi-transparent background
        self.screen.blit(self.background_surface, (0, 0))
        
        # Calculate fade-in effect
        fade_progress = min(1.0, self.animation_timer / self.fade_in_duration)
        alpha = max(200, int(255 * fade_progress))  # Minimum visibility
        
        # Game Over title with dramatic effect
        title_text = "💀 GAME OVER 💀"
        title_color = (255, 50, 50)  # Red color
        title_surface = self.title_font.render(title_text, True, title_color)
        title_surface.set_alpha(alpha)
        title_rect = title_surface.get_rect(center=(self.screen.get_width() // 2, 200))
        self.screen.blit(title_surface, title_rect)
        
        # Death message
        death_message = "Du bist gefallen, tapferer Alchemist..."
        message_surface = self.text_font.render(death_message, True, (200, 200, 200))
        message_surface.set_alpha(alpha)
        message_rect = message_surface.get_rect(center=(self.screen.get_width() // 2, 260))
        self.screen.blit(message_surface, message_rect)
        
        # Subtitle
        subtitle_text = "Was möchtest du tun?"
        subtitle_surface = self.text_font.render(subtitle_text, True, (150, 150, 150))
        subtitle_surface.set_alpha(alpha)
        subtitle_rect = subtitle_surface.get_rect(center=(self.screen.get_width() // 2, 320))
        self.screen.blit(subtitle_surface, subtitle_rect)
        
        # Draw buttons (always visible for debugging)
        for button in self.buttons:
            button.draw(self.screen)
        
        # Show controls hint (always visible)
        hint_text = "⌨️ ESC: Hauptmenü  •  R: Neues Spiel"
        hint_surface = pygame.font.Font(None, 24).render(hint_text, True, (100, 100, 100))
        hint_rect = hint_surface.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() - 50))
        self.screen.blit(hint_surface, hint_rect)
    
    def handle_event(self, event: pygame.event.Event) -> Optional[Any]:
        """Handle game over events"""
        # Always allow interaction (remove fade-in restriction for debugging)
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                return "restart_game"  # Quick restart with specific signal
            elif event.key == pygame.K_ESCAPE:
                return GameState.MAIN_MENU
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            for button in self.buttons:
                if button.update(mouse_pos, True):
                    return button.action
        elif event.type == pygame.MOUSEMOTION:
            mouse_pos = pygame.mouse.get_pos()
            for button in self.buttons:
                button.update(mouse_pos, False)
        
        return None

class MenuSystem:
    """Main menu system controller"""
    
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.current_state = GameState.MAIN_MENU
        self.states = {
            GameState.MAIN_MENU: MainMenuState(screen),
            GameState.SETTINGS: SettingsMenuState(screen),
            GameState.CREDITS: CreditsMenuState(screen),
            GameState.LOAD_GAME: LoadGameMenuState(screen),
            GameState.PAUSE: PauseMenuState(screen),
            GameState.GAME_OVER: GameOverMenuState(screen)
        }
        
        # Return values for game state management
        self.last_action = None
        self.selected_save_slot = None
        
        # Fade in/out effects
        self.fade_surface = pygame.Surface((screen.get_width(), screen.get_height()))
        self.fade_surface.set_alpha(0)
        self.fade_alpha = 0
        self.fading = False
        self.next_state = None
    
    def handle_event(self, event: pygame.event.Event) -> Optional[Any]:
        """Handle events and return state change if needed"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                # Don't allow ESC to leave Game Over screen
                if self.current_state == GameState.GAME_OVER:
                    self.change_state(GameState.MAIN_MENU)
                    return None
                elif self.current_state != GameState.MAIN_MENU:
                    self.change_state(GameState.MAIN_MENU)
                    return None
                else:
                    return GameState.QUIT
        
        # Pass event to current state
        if self.current_state in self.states:
            result = self.states[self.current_state].handle_event(event)
            if result:
                if result == GameState.NEW_GAME:
                    return GameState.GAMEPLAY  # Start new game
                elif result == "restart_game":
                    return "restart_game"  # Restart current game
                elif result == GameState.QUIT:
                    return GameState.QUIT
                elif result == "save_game":
                    return "save_game"  # Pass save action to main game
                elif isinstance(result, tuple) and result[0] == "load_game":
                    # Handle load game with slot number
                    self.selected_save_slot = result[1]
                    return ("load_game", result[1])
                elif isinstance(result, tuple) and result[0] == "save_to_slot":
                    # Handle save to specific slot
                    return result
                else:
                    self.change_state(result)
        
        return None
    
    def change_state(self, new_state: GameState):
        """Change to a new menu state"""
        if new_state in self.states:
            self.current_state = new_state
            # Refresh load game menu when entering it
            if new_state == GameState.LOAD_GAME:
                self.states[GameState.LOAD_GAME].refresh_save_slots()
                self.states[GameState.LOAD_GAME].setup_buttons()
    
    def show_save_confirmation(self):
        """Show save confirmation in main menu"""
        if self.current_state == GameState.MAIN_MENU:
            self.states[GameState.MAIN_MENU].show_save_confirmation()
    
    def show_no_game_message(self):
        """Show no active game message in main menu"""
        if self.current_state == GameState.MAIN_MENU:
            self.states[GameState.MAIN_MENU].show_no_game_message()
    
    def show_game_over(self):
        """Show game over screen when player dies"""
        print("📺 Switching to Game Over menu state")
        self.change_state(GameState.GAME_OVER)
        # Reset animation timer to ensure proper fade-in
        if GameState.GAME_OVER in self.states:
            self.states[GameState.GAME_OVER].animation_timer = 0
            print("🎬 Game Over animation timer reset")
    
    def update(self, dt: float):
        """Update menu system"""
        if self.current_state in self.states:
            self.states[self.current_state].update(dt)
    
    def draw(self):
        """Draw current menu state"""
        if self.current_state in self.states:
            self.states[self.current_state].draw()
        
        # Draw fade effect if active
        if self.fading:
            self.fade_surface.set_alpha(self.fade_alpha)
            self.screen.blit(self.fade_surface, (0, 0))
