# -*- coding: utf-8 -*-
"""
Menu System for the Alchemist Game
Provides main menu, settings, credits, and game state management
"""

import pygame
import sys
import os
from typing import Optional, List, Dict, Any, Callable, Tuple
from enum import Enum
from settings import *
from managers.settings_manager import SettingsManager
from save_system import save_manager
from managers.asset_manager import AssetManager

# Optional Action System integration (for hardware/buttons)
# Define safe stubs so Pylance doesn't flag possibly-unbound
get_action_system: Optional[Callable[..., Any]] = None
ActionType: Any = None
try:
    from systems.action_system import get_action_system as _get_action_system, ActionType as _ActionType
    get_action_system = _get_action_system
    ActionType = _ActionType
    _ACTION_SYSTEM_AVAILABLE = True
except Exception:
    _ACTION_SYSTEM_AVAILABLE = False

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

# Image-based textured button backgrounds (user-provided texture)
_MENU_TEX_BASES: Dict[str, Optional[pygame.Surface]] = {"normal": None, "hover": None, "click": None}
_MENU_TEX_PATHS_RESOLVED = False
_asset_mgr = AssetManager()

def _resolve_menu_texture_paths() -> Dict[str, Optional[str]]:
    global _MENU_TEX_PATHS_RESOLVED
    _MENU_TEX_PATHS_RESOLVED = True
    # Determine project root
    ui_dir = os.path.dirname(__file__)
    src_dir = os.path.dirname(ui_dir)
    project_root = os.path.dirname(src_dir)
    assets_ui = os.path.join(project_root, 'assets', 'ui')
    assets_ui_spells = os.path.join(assets_ui, 'spells')

    env_base = os.environ.get('ALCHEMIST_MENU_BUTTON_TEXTURE', '').strip()
    def abs_if_exists(p: str) -> Optional[str]:
        if not p:
            return None
        candidate = p if os.path.isabs(p) else os.path.normpath(os.path.join(project_root, p))
        return candidate if os.path.isfile(candidate) else None

    paths: Dict[str, Optional[str]] = {"normal": None, "hover": None, "click": None}
    base_path = abs_if_exists(env_base) if env_base else None
    if base_path:
        root, ext = os.path.splitext(base_path)
        paths["normal"] = base_path
        hover = root + "_hover" + ext
        click = root + "_click" + ext
        paths["hover"] = hover if os.path.isfile(hover) else None
        paths["click"] = click if os.path.isfile(click) else None
        return paths

    # Helper to search multiple extensions and folders
    def find_any(name_no_ext: str) -> Optional[str]:
        for folder in (assets_ui, assets_ui_spells):
            for ext in ('.png', '.jpg', '.jpeg'):
                candidate = os.path.join(folder, name_no_ext + ext)
                if os.path.isfile(candidate):
                    return candidate
        return None

    # Defaults under assets/ui (with fallbacks to assets/ui/spells)
    paths["normal"] = find_any('menu_button_stone')
    paths["hover"] = find_any('menu_button_stone_hover')
    paths["click"] = find_any('menu_button_stone_click')
    return paths

def _ensure_menu_textures_loaded() -> None:
    paths = _resolve_menu_texture_paths() if not _MENU_TEX_PATHS_RESOLVED else _resolve_menu_texture_paths()
    for state, p in paths.items():
        if p and _MENU_TEX_BASES.get(state) is None:
            try:
                _MENU_TEX_BASES[state] = _asset_mgr.load_image(p)
            except Exception:
                _MENU_TEX_BASES[state] = None

def _get_menu_texture_scaled(size: Tuple[int, int], state: str) -> Optional[pygame.Surface]:
    _ensure_menu_textures_loaded()
    base = _MENU_TEX_BASES.get(state) or _MENU_TEX_BASES.get('normal')
    if not base:
        return None
    return _asset_mgr.get_scaled_sprite(base, size)

# Menu background image (user-provided)
_MENU_BG_BASE: Optional[pygame.Surface] = None
_MENU_BG_PATH_RESOLVED = False

def _resolve_menu_bg_path() -> Optional[str]:
    global _MENU_BG_PATH_RESOLVED
    _MENU_BG_PATH_RESOLVED = True
    # Project root
    ui_dir = os.path.dirname(__file__)
    src_dir = os.path.dirname(ui_dir)
    project_root = os.path.dirname(src_dir)
    assets_ui = os.path.join(project_root, 'assets', 'ui')
    assets_ui_spells = os.path.join(assets_ui, 'spells')

    env_bg = os.environ.get('ALCHEMIST_MENU_BG', '').strip()
    def abs_if_exists(p: str) -> Optional[str]:
        if not p:
            return None
        candidate = p if os.path.isabs(p) else os.path.normpath(os.path.join(project_root, p))
        return candidate if os.path.isfile(candidate) else None

    if env_bg:
        p = abs_if_exists(env_bg)
        if p:
            return p

    # Try common base names and extensions
    def find_any(name_no_ext: str) -> Optional[str]:
        for folder in (assets_ui, assets_ui_spells):
            for ext in ('.png', '.jpg', '.jpeg'):
                candidate = os.path.join(folder, name_no_ext + ext)
                if os.path.isfile(candidate):
                    return candidate
        return None

    return (
        find_any('menu_bg') or
        find_any('main_menu_bg') or
        None
    )

def _ensure_menu_bg_loaded() -> None:
    global _MENU_BG_BASE
    if _MENU_BG_BASE is not None:
        return
    path = _resolve_menu_bg_path()
    if path:
        try:
            _MENU_BG_BASE = _asset_mgr.load_image(path)
        except Exception:
            _MENU_BG_BASE = None

def _get_menu_bg_scaled(size: Tuple[int, int]) -> Optional[pygame.Surface]:
    _ensure_menu_bg_loaded()
    if not _MENU_BG_BASE:
        return None
    return _asset_mgr.get_scaled_sprite(_MENU_BG_BASE, size)

class MenuButton:
    """A clickable menu button"""
    
    def __init__(self, x: int, y: int, width: int, height: int, text: str, 
                 font: pygame.font.Font, action: Optional[Any] = None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.action: Optional[Any] = action
        self.hovered = False
        self.clicked = False
        
        # Colors
        self.normal_color: tuple[int, int, int] = (40, 40, 60)
        self.hover_color: tuple[int, int, int] = (60, 60, 90)
        self.click_color: tuple[int, int, int] = (80, 80, 120)
        self.text_color: tuple[int, int, int] = (255, 255, 255)
        self.border_color: tuple[int, int, int] = (100, 100, 150)

    # Allow external code to set a generic "color" which maps to normal_color
    @property
    def color(self) -> tuple[int, int, int]:
        return self.normal_color

    @color.setter
    def color(self, value: tuple[int, int, int]) -> None:
        self.normal_color = value
    
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
        # Choose texture or solid color based on availability
        state = 'click' if self.clicked else ('hover' if self.hovered else 'normal')
        tex = _get_menu_texture_scaled((self.rect.width, self.rect.height), state)
        if tex is not None:
            screen.blit(tex, self.rect)
        else:
            # Fallback to color fill
            if self.clicked:
                color = self.click_color
            elif self.hovered:
                color = self.hover_color
            else:
                color = self.normal_color
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
        self.selected_index: int = 0
        self._last_axis_move_time: float = 0.0
        self._axis_move_cooldown: float = 0.18  # seconds, to debounce joystick
        self.disable_menu_emojis: bool = False  # When using a custom font without emoji glyphs
        self._custom_menu_font_loaded: bool = False
        
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
        
        # Try to load a custom medieval/alchemic menu font from assets or env
        try:
            self._try_load_custom_menu_font()
        except Exception:
            # Non-fatal: keep defaults if anything goes wrong
            pass

        self.background_color = (20, 20, 40)

    def _try_load_custom_menu_font(self) -> None:
        """Load a custom menu font if present.
        Priority:
        1) Env var ALCHEMIST_MENU_FONT (absolute or path relative to project root)
        2) assets/fonts/menu.ttf or menu.otf
        3) First matching medieval-ish font in assets/fonts directory
        """
        # Determine project root (repo root), then assets/fonts path
        ui_dir = os.path.dirname(__file__)
        src_dir = os.path.dirname(ui_dir)
        project_root = os.path.dirname(src_dir)
        fonts_dir = os.path.join(project_root, 'assets', 'fonts')

        def _font_path_exists(path: str) -> Optional[str]:
            if not path:
                return None
            # If not absolute, resolve against project root
            candidate = path
            if not os.path.isabs(candidate):
                candidate = os.path.normpath(os.path.join(project_root, candidate))
            return candidate if os.path.isfile(candidate) else None

        # 1) Env override
        env_font = os.environ.get('ALCHEMIST_MENU_FONT', '').strip()
        font_path: Optional[str] = _font_path_exists(env_font) if env_font else None

        # 2) Default menu.ttf/otf in assets/fonts
        if not font_path and os.path.isdir(fonts_dir):
            for fname in ('menu.ttf', 'menu.otf'):
                candidate = os.path.join(fonts_dir, fname)
                if os.path.isfile(candidate):
                    font_path = candidate
                    break

        # 3) Try to pick a medieval-looking font from assets/fonts
        if not font_path and os.path.isdir(fonts_dir):
            try:
                candidates = [f for f in os.listdir(fonts_dir) if f.lower().endswith(('.ttf', '.otf'))]
            except Exception:
                candidates = []
            # Prefer names with these keywords
            keywords = ('fraktur', 'blackletter', 'medieval', 'gothic', 'celtic', 'unifraktur', 'alchemy', 'alchemist')
            prioritized: List[str] = []
            others: List[str] = []
            for f in candidates:
                name = f.lower()
                if any(k in name for k in keywords):
                    prioritized.append(f)
                else:
                    others.append(f)
            chosen = prioritized[0] if prioritized else (others[0] if others else None)
            if chosen:
                font_path = os.path.join(fonts_dir, chosen)

        if not font_path:
            return  # Nothing to do

        # Load sizes (keep title larger, buttons/text smaller)
        try:
            self.title_font = pygame.font.Font(font_path, 56)
            self.button_font = pygame.font.Font(font_path, 36)
            self.text_font = pygame.font.Font(font_path, 28)
            # When a custom TTF is used, assume it has no emoji glyphs
            # Keep emoji_font as a system font for icon rendering tests if needed, but disable emoji usage explicitly
            try:
                self.emoji_font = pygame.font.SysFont('segoeuiemoji', 28)
            except Exception:
                self.emoji_font = self.text_font
            self._custom_menu_font_loaded = True
            self.disable_menu_emojis = True
            # Slightly adjust background to complement medieval look
            self.background_color = (18, 16, 28)
        except Exception:
            # If loading fails, silently keep defaults
            self._custom_menu_font_loaded = False
        
    def handle_event(self, event: pygame.event.Event) -> Optional[Any]:
        """Handle events and return new state if needed (mouse + keyboard + joystick)"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            for button in self.buttons:
                if button.update(mouse_pos, True):
                    return button.action
        elif event.type == pygame.MOUSEMOTION:
            mouse_pos = pygame.mouse.get_pos()
            for button in self.buttons:
                button.update(mouse_pos, False)
        elif event.type == pygame.KEYDOWN:
            if not self.buttons:
                return None
            # Navigation: Up/Down arrows or W/S
            if event.key in (pygame.K_UP, pygame.K_w):
                self.selected_index = (self.selected_index - 1) % len(self.buttons)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected_index = (self.selected_index + 1) % len(self.buttons)
            # Confirm: Space, C, or Enter
            elif event.key in (pygame.K_SPACE, pygame.K_c, pygame.K_RETURN, pygame.K_i):
                return self.buttons[self.selected_index].action
        elif event.type == pygame.JOYAXISMOTION:
            # Basic joystick navigation on vertical axis (usually axis 1)
            if not self.buttons:
                return None
            now = pygame.time.get_ticks() / 1000.0
            if now - self._last_axis_move_time < self._axis_move_cooldown:
                return None
            if event.axis == 1:
                if event.value <= -0.6:
                    self.selected_index = (self.selected_index - 1) % len(self.buttons)
                    self._last_axis_move_time = now
                elif event.value >= 0.6:
                    self.selected_index = (self.selected_index + 1) % len(self.buttons)
                    self._last_axis_move_time = now
        elif event.type == pygame.JOYBUTTONDOWN:
            # Typical confirm buttons (A or X on many controllers) map variably; use any press as confirm
            if self.buttons:
                return self.buttons[self.selected_index].action
        
        return None
    
    def update(self, dt: float):
        """Update menu state"""
        pass
    
    def draw(self):
        """Draw the menu with selection highlight"""
        # Draw custom background if available, else solid color
        bg = _get_menu_bg_scaled((self.screen.get_width(), self.screen.get_height()))
        if bg is not None:
            self.screen.blit(bg, (0, 0))
        else:
            self.screen.fill(self.background_color)
        for i, button in enumerate(self.buttons):
            button.draw(self.screen)
            if i == self.selected_index:
                # Draw a subtle highlight border and left arrow
                pygame.draw.rect(self.screen, (255, 215, 0), button.rect.inflate(8, 6), 2)
                # Skip left arrow if special glyphs may render as squares
                if not getattr(self, 'disable_menu_emojis', False):
                    try:
                        arrow_surface = self.text_font.render("➤", True, (255, 215, 0))
                        arrow_rect = arrow_surface.get_rect()
                        arrow_rect.centery = button.rect.centery
                        arrow_rect.right = button.rect.left - 12
                        self.screen.blit(arrow_surface, arrow_rect)
                    except Exception:
                        pass

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
            ("Neues Spiel", GameState.NEW_GAME),
            ("Spiel speichern", "save_game"),
            ("Spiel laden", GameState.LOAD_GAME),
            ("Einstellungen", GameState.SETTINGS),
            ("Credits", GameState.CREDITS),
            ("Beenden", GameState.QUIT)
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
            # Force-disable emojis when a custom font is active
            if getattr(self, 'disable_menu_emojis', False):
                emoji_works = False
            
            # Use fallback text if emojis don't work
            if not emoji_works:
                text = fallback_buttons_data[i][0]
            
            button = MenuButton(x, y, button_width, button_height, 
                              text, self.button_font, action)
            self.buttons.append(button)
    
    def handle_event(self, event: pygame.event.Event) -> Optional[Any]:
        """Handle main menu events (mouse + keyboard/joystick)"""
        result = super().handle_event(event)
        if result is not None:
            # Map special action
            if result == "save_game":
                return "save_game"
            return result
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
        title_text = "Der Alchemist" if getattr(self, 'disable_menu_emojis', False) else "🧙‍♂️ Der Alchemist"
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
        self._settings_mgr = SettingsManager()
        self.settings = self.load_settings()
        # Keys shown as rows (order matters). Last virtual row is "Back".
        self._setting_keys = [
            "master_volume",
            "music_volume",
            "sound_volume",
            "fullscreen",
            "show_fps",
            "difficulty",
        ]
        self.selected_row = 0
        self._rows_count = len(self._setting_keys) + 1
        self.setup_buttons()
    
    def load_settings(self) -> Dict[str, Any]:
        """Load current settings"""
        return {
            "master_volume": float(self._settings_mgr.master_volume),
            "master_mute": bool(self._settings_mgr.master_mute),
            "music_volume": float(self._settings_mgr.music_volume),
            "sound_volume": float(self._settings_mgr.sound_volume),
            "fullscreen": False,
            "show_fps": True,
            "difficulty": str(self._settings_mgr.get('difficulty', 'Normal'))
        }
    
    def setup_buttons(self):
        """Setup settings menu buttons"""
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()
        
        # Back button (clickable with mouse); keyboard/gamepad uses virtual back row
        back_button = MenuButton(50, screen_height - 80, 180, 50, 
                               "← Zurück", self.button_font, GameState.MAIN_MENU)
        self.buttons.append(back_button)
    
    def draw(self):
        """Draw settings menu"""
        super().draw()
        
        # Title
        title_text = "Einstellungen" if getattr(self, 'disable_menu_emojis', False) else "⚙️ Einstellungen"
        title_surface = self.title_font.render(title_text, True, (255, 215, 0))
        title_rect = title_surface.get_rect(center=(self.screen.get_width() // 2, 100))
        self.screen.blit(title_surface, title_rect)
        
        # Settings rows with icons, values and sliders for clarity
        # Build rows from keys
        label_map = {
            "master_volume": ("🕹️ Master Lautstärke", "volume"),
            "music_volume": ("🎵 Musik Lautstärke", "volume"),
            "sound_volume": ("🔊 Sound Lautstärke", "volume"),
            "fullscreen": ("🖥️ Vollbild", "bool"),
            "show_fps": ("📊 FPS anzeigen", "bool"),
            "difficulty": ("⚔️ Schwierigkeit", "choice"),
        }
        rows = [(k, label_map[k][0], label_map[k][1]) for k in self._setting_keys]
        y_base = 200
        line_h = 46
        left_x = 100
        value_x = self.screen.get_width() - 160
        slider_left = 420
        slider_right = self.screen.get_width() - 220
        slider_w = max(120, slider_right - slider_left)
        
        for i, (key, label, kind) in enumerate(rows):
            y = y_base + i * line_h
            # Active row highlight
            if i == self.selected_row:
                rect = pygame.Rect(left_x - 20, y - 8, self.screen.get_width() - (left_x - 20) - 80, line_h)
                pygame.draw.rect(self.screen, (255, 215, 0), rect, 2)
            # Label
            label_surface = self.text_font.render(label + ":", True, (220, 220, 220))
            self.screen.blit(label_surface, (left_x, y))
            # Value + slider
            if kind == "volume":
                pct = int(self.settings[key] * 100)
                # Slider background
                pygame.draw.rect(self.screen, (60, 60, 90), (slider_left, y + 8, slider_w, 10))
                # Slider fill
                fill_w = int(slider_w * max(0.0, min(1.0, self.settings[key])))
                pygame.draw.rect(self.screen, (120, 200, 255) if key != "master_volume" else (255, 215, 0), (slider_left, y + 8, fill_w, 10))
                # Percentage text
                val_surface = self.text_font.render(f"{pct}%" + (" (Mute)" if key == "master_volume" and self.settings.get("master_mute") else ""), True, (200, 200, 200))
                val_rect = val_surface.get_rect()
                val_rect.right = self.screen.get_width() - 100
                val_rect.top = y - 4
                self.screen.blit(val_surface, val_rect)
            elif kind == "bool":
                v = self.settings[key]
                val_surface = self.text_font.render("Ein" if v else "Aus", True, (200, 200, 200))
                val_rect = val_surface.get_rect()
                val_rect.right = self.screen.get_width() - 100
                val_rect.top = y - 4
                self.screen.blit(val_surface, val_rect)
            elif kind == "choice":
                v = self.settings[key]
                val_surface = self.text_font.render(str(v), True, (200, 200, 200))
                val_rect = val_surface.get_rect()
                val_rect.right = self.screen.get_width() - 100
                val_rect.top = y - 4
                self.screen.blit(val_surface, val_rect)

        # Draw virtual 'Back' row and highlight if selected
        back_label = "← Zurück"
        back_index = len(rows)
        back_y = y_base + back_index * line_h + 14
        if self.selected_row == back_index:
            rect = pygame.Rect(left_x - 20, back_y - 8, 260, line_h)
            pygame.draw.rect(self.screen, (255, 215, 0), rect, 2)
        back_surface = self.text_font.render(back_label, True, (220, 220, 220))
        self.screen.blit(back_surface, (left_x, back_y))

        # Key hints at the bottom
        hints = "↑/↓: Auswahl  •  ←/→: Wert ändern  •  Enter/I: Bestätigen  •  N: Master Mute  •  ESC: Fokus auf Zurück"
        hint_surface = pygame.font.Font(None, 24).render(hints, True, (140, 140, 140))
        hint_rect = hint_surface.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() - 60))
        self.screen.blit(hint_surface, hint_rect)

    def handle_event(self, event: pygame.event.Event) -> Optional[Any]:
        """Extend to adjust settings with keyboard arrows and save."""
        result = super().handle_event(event)
        if event is None:
            return result
        if event.type == pygame.KEYDOWN:
            # Navigate rows
            if event.key in (pygame.K_UP, pygame.K_w):
                self.selected_row = (self.selected_row - 1) % self._rows_count
                return None
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected_row = (self.selected_row + 1) % self._rows_count
                return None
            # ESC moves focus to Back first; if already on Back, go to Main Menu
            if event.key == pygame.K_ESCAPE:
                back_index = len(self._setting_keys)
                if self.selected_row != back_index:
                    self.selected_row = back_index
                    return None
                return GameState.MAIN_MENU
            # Toggle master mute
            if event.key == pygame.K_n:
                muted = not bool(self.settings.get('master_mute', False))
                self.settings['master_mute'] = muted
                self._settings_mgr.master_mute = muted
                self._settings_mgr.save()
                try:
                    pygame.event.post(pygame.event.Event(pygame.USEREVENT, {'name': 'APPLY_MUSIC_VOLUME'}))
                except Exception:
                    pass
            # Adjust master volume Q/E (legacy)
            if event.key in (pygame.K_q, pygame.K_e):
                step = -0.05 if event.key == pygame.K_q else 0.05
                new_vol = max(0.0, min(1.0, self.settings['master_volume'] + step))
                self.settings['master_volume'] = new_vol
                self._settings_mgr.master_volume = new_vol
                self._settings_mgr.save()
                try:
                    pygame.event.post(pygame.event.Event(pygame.USEREVENT, {'name': 'APPLY_MUSIC_VOLUME'}))
                except Exception:
                    pass
            # Row-context adjustments with Left/Right (and A/D as alt) — only when not on Back
            if event.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_a, pygame.K_d):
                is_left = event.key in (pygame.K_LEFT, pygame.K_a)
                step = -0.05 if is_left else 0.05
                if self.selected_row >= len(self._setting_keys):
                    return None
                key_order = self._setting_keys
                active_key = key_order[self.selected_row]
                kind = "volume" if active_key.endswith("volume") else ("bool" if active_key in ("fullscreen", "show_fps") else "choice")
                if kind == "volume":
                    new_val = max(0.0, min(1.0, self.settings[active_key] + step))
                    self.settings[active_key] = new_val
                    setattr(self._settings_mgr, active_key, new_val)
                    self._settings_mgr.save()
                    # Re-apply music volume if master or music changed
                    if active_key in ("master_volume", "music_volume"):
                        try:
                            pygame.event.post(pygame.event.Event(pygame.USEREVENT, {'name': 'APPLY_MUSIC_VOLUME'}))
                        except Exception:
                            pass
                    return None
                elif kind == "bool":
                    # Left/Right toggles
                    new_val = not bool(self.settings[active_key])
                    self.settings[active_key] = new_val
                    # Persist if supported by settings manager
                    try:
                        setattr(self._settings_mgr, active_key, new_val)
                        self._settings_mgr.save()
                    except Exception:
                        pass
                    return None
                elif kind == "choice":
                    choices = ["Leicht", "Normal", "Schwer"]
                    cur = self.settings.get(active_key, "Normal")
                    idx = choices.index(cur) if cur in choices else 1
                    idx = (idx - 1) % len(choices) if is_left else (idx + 1) % len(choices)
                    new_val = choices[idx]
                    self.settings[active_key] = new_val
                    try:
                        self._settings_mgr.set('difficulty', new_val)
                        self._settings_mgr.save()
                        pygame.event.post(pygame.event.Event(pygame.USEREVENT, {'name': 'APPLY_DIFFICULTY'}))
                    except Exception:
                        pass
                    return None
            # Enter/I toggles for bool/choice rows; when on Back, acts as confirm back
            if event.key in (pygame.K_RETURN, pygame.K_i):
                if self.selected_row >= len(self._setting_keys):
                    return GameState.MAIN_MENU
                key_order = self._setting_keys
                active_key = key_order[self.selected_row]
                if active_key in ("fullscreen", "show_fps"):
                    self.settings[active_key] = not bool(self.settings[active_key])
                    try:
                        setattr(self._settings_mgr, active_key, self.settings[active_key])
                        self._settings_mgr.save()
                    except Exception:
                        pass
                    return None
                elif active_key == "difficulty":
                    # cycle forward
                    choices = ["Leicht", "Normal", "Schwer"]
                    cur = self.settings.get(active_key, "Normal")
                    idx = (choices.index(cur) + 1) % len(choices) if cur in choices else 1
                    new_val = choices[idx]
                    self.settings[active_key] = new_val
                    try:
                        self._settings_mgr.set('difficulty', new_val)
                        self._settings_mgr.save()
                        pygame.event.post(pygame.event.Event(pygame.USEREVENT, {'name': 'APPLY_DIFFICULTY'}))
                    except Exception:
                        pass
                    return None
        elif event.type == pygame.JOYAXISMOTION:
            now = pygame.time.get_ticks() / 1000.0
            if now - self._last_axis_move_time >= self._axis_move_cooldown:
                if event.axis == 1:  # vertical select
                    if event.value <= -0.6:
                        self.selected_row = (self.selected_row - 1) % self._rows_count
                        self._last_axis_move_time = now
                    elif event.value >= 0.6:
                        self.selected_row = (self.selected_row + 1) % self._rows_count
                        self._last_axis_move_time = now
                elif event.axis == 0:  # horizontal adjust
                    if self.selected_row >= len(self._setting_keys):
                        self._last_axis_move_time = now
                        return result
                    key_order = self._setting_keys
                    active_key = key_order[self.selected_row]
                    is_left = event.value <= -0.6
                    step = -0.05 if is_left else 0.05
                    if active_key.endswith("volume"):
                        new_val = max(0.0, min(1.0, self.settings[active_key] + step))
                        self.settings[active_key] = new_val
                        try:
                            setattr(self._settings_mgr, active_key, new_val)
                            self._settings_mgr.save()
                        except Exception:
                            pass
                        if active_key in ("master_volume", "music_volume"):
                            try:
                                pygame.event.post(pygame.event.Event(pygame.USEREVENT, {'name': 'APPLY_MUSIC_VOLUME'}))
                            except Exception:
                                pass
                        self._last_axis_move_time = now
                    elif active_key in ("fullscreen", "show_fps", "difficulty"):
                        # treat as toggle/cycle
                        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RETURN}))
                        self._last_axis_move_time = now
        return result

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
        
        # Title (no emojis)
        title_text = "Credits"
        title_surface = self.title_font.render(title_text, True, (255, 215, 0))
        title_rect = title_surface.get_rect(center=(self.screen.get_width() // 2, 100))
        self.screen.blit(title_surface, title_rect)
        
        # Credits content (simplified as requested, no emojis)
        credits_text = [
            "Der Alchemist",
            "",
            "👥 Entwicklungsteam:",
            "• Kirill: Game Design und UX",
            "• Jonas: Kartenerstellung und Platzierung der Gegner",
            "• Christian: Entwicklung der Spiellogik",
            "• Waseem: Arduino-Programmierung",
            "• Simon: Gehäusebau, Verkabelung und Löten",
        ]
        
        # Background panel for readability
        import pygame
        screen_w = self.screen.get_width()
        line_height = 25
        start_y = 150
        # Count drawn lines (skip empty draws but account for spacing)
        lines_to_draw = [ln for ln in credits_text]
        block_h = len(lines_to_draw) * line_height + 32
        block_w = min(int(screen_w * 0.8), 900)
        block_x = (screen_w - block_w) // 2
        block_y = start_y - 16
        bg = pygame.Surface((block_w, block_h), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 180))  # semi-transparent dark
        self.screen.blit(bg, (block_x, block_y))
        pygame.draw.rect(self.screen, (180, 180, 220), (block_x, block_y, block_w, block_h), 2)

        # Draw text centered on panel
        y_offset = start_y
        for line in credits_text:
            if line:  # Skip empty lines
                text_surface = self.text_font.render(line, True, (200, 200, 200))
                text_rect = text_surface.get_rect(center=(self.screen.get_width() // 2, y_offset))
                self.screen.blit(text_surface, text_rect)
            y_offset += line_height

class LoadGameMenuState(BaseMenuState):
    """Load game menu state"""
    
    def __init__(self, screen: pygame.Surface):
        super().__init__(screen)
        self.save_slots: List[Dict[str, Any]] = []
        self.selected_slot: Optional[int] = None
        self.show_delete_confirmation: bool = False
        self.delete_slot: Optional[int] = None
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
        
        # Save slot buttons with delete buttons
        for i, save_slot in enumerate(self.save_slots):
            if save_slot["exists"]:
                # Load button
                button_text = f"{save_slot['name']} - {save_slot['level']}"
                load_button = MenuButton(screen_width // 2 - 270, 180 + i * 70, 
                                       430, 50, button_text, self.button_font)
                load_button.action = ("load_slot", save_slot["slot"])
                self.buttons.append(load_button)
                
                # Delete button (smaller, red)
                delete_button = MenuButton(screen_width // 2 + 180, 180 + i * 70,
                                         90, 50, "🗑️ Löschen", self.button_font)
                delete_button.action = ("delete_slot", save_slot["slot"])
                delete_button.color = (150, 50, 50)  # Red background
                delete_button.hover_color = (200, 70, 70)  # Lighter red on hover
                self.buttons.append(delete_button)
        
        # Back button
        back_button = MenuButton(50, screen_height - 80, 180, 50, 
                               "← Zurück", self.button_font, GameState.MAIN_MENU)
        self.buttons.append(back_button)
        
        # Delete confirmation buttons (only show when needed)
        if self.show_delete_confirmation:
            # Position buttons better within the dialog
            dialog_y = screen_height // 2 - 100
            button_y = dialog_y + 120
            
            confirm_button = MenuButton(screen_width // 2 - 90, button_y,
                                       80, 40, "Ja", self.button_font)
            confirm_button.action = ("confirm_delete", self.delete_slot)
            confirm_button.color = (150, 50, 50)
            confirm_button.hover_color = (200, 70, 70)
            self.buttons.append(confirm_button)
            
            cancel_button = MenuButton(screen_width // 2 + 10, button_y,
                                     80, 40, "Nein", self.button_font)
            cancel_button.action = ("cancel_delete", None)
            cancel_button.color = (80, 80, 80)
            cancel_button.hover_color = (120, 120, 120)
            self.buttons.append(cancel_button)
    
    
    def handle_event(self, event: pygame.event.Event) -> Optional[Any]:
        """Handle events for load game menu (mouse + keyboard/joystick)"""
        # If confirmation dialog is open, prioritize confirm/cancel hotkeys
        if self.show_delete_confirmation:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_i):
                    if isinstance(self.delete_slot, int) and save_manager.delete_save(self.delete_slot):
                        print(f"🗑️ Save slot {self.delete_slot} deleted successfully")
                    else:
                        print(f"❌ Failed to delete save slot {self.delete_slot}")
                    self.show_delete_confirmation = False
                    self.delete_slot = None
                    self.refresh_save_slots()
                    self.setup_buttons()
                    return None
                elif event.key in (pygame.K_ESCAPE, pygame.K_z):
                    self.show_delete_confirmation = False
                    self.delete_slot = None
                    self.setup_buttons()
                    return None
        # First try base navigation
        base_result = super().handle_event(event)
        if base_result is not None:
            # Map base_result (could be tuple actions from keyboard/joystick confirm)
            if isinstance(base_result, tuple):
                kind = base_result[0]
                if kind == "load_slot":
                    slot_val = base_result[1]
                    if isinstance(slot_val, int):
                        self.selected_slot = slot_val
                        return ("load_game", self.selected_slot)
                    return None
                elif kind == "delete_slot":
                    # Show delete confirmation
                    self.delete_slot = base_result[1] if isinstance(base_result[1], int) else None
                    self.show_delete_confirmation = True
                    self.setup_buttons()
                    return None
                elif kind == "confirm_delete":
                    if isinstance(base_result[1], int) and save_manager.delete_save(base_result[1]):
                        print(f"🗑️ Save slot {base_result[1]} deleted successfully")
                    else:
                        print(f"❌ Failed to delete save slot {base_result[1]}")
                    self.show_delete_confirmation = False
                    self.delete_slot = None
                    self.refresh_save_slots()
                    self.setup_buttons()
                    return None
                elif kind == "cancel_delete":
                    self.show_delete_confirmation = False
                    self.delete_slot = None
                    self.setup_buttons()
                    return None
                else:
                    return base_result
            return base_result
        # Horizontal navigation between Load and Delete buttons on the same slot row
        if event.type == pygame.KEYDOWN and not self.show_delete_confirmation and self.buttons:
            if event.key in (pygame.K_LEFT, pygame.K_a, pygame.K_RIGHT, pygame.K_d):
                current_btn = self.buttons[self.selected_index]
                target_kind = None
                if isinstance(current_btn.action, tuple):
                    if current_btn.action[0] == "load_slot":
                        target_kind = "delete_slot"
                    elif current_btn.action[0] == "delete_slot":
                        target_kind = "load_slot"
                if target_kind:
                    for idx, btn in enumerate(self.buttons):
                        if btn is current_btn:
                            continue
                        if isinstance(btn.action, tuple) and btn.action[0] == target_kind and btn.rect.y == current_btn.rect.y:
                            self.selected_index = idx
                            break
        # Gamepad: axis 0 (left/right) and hat/dpad
        if not self.show_delete_confirmation and self.buttons:
            now = pygame.time.get_ticks() / 1000.0
            if event.type == pygame.JOYAXISMOTION and event.axis == 0 and abs(event.value) >= 0.6:
                if now - self._last_axis_move_time >= self._axis_move_cooldown:
                    current_btn = self.buttons[self.selected_index]
                    target_kind = None
                    if isinstance(current_btn.action, tuple):
                        if current_btn.action[0] == "load_slot":
                            target_kind = "delete_slot"
                        elif current_btn.action[0] == "delete_slot":
                            target_kind = "load_slot"
                    if target_kind:
                        for idx, btn in enumerate(self.buttons):
                            if btn is current_btn:
                                continue
                            if isinstance(btn.action, tuple) and btn.action[0] == target_kind and btn.rect.y == current_btn.rect.y:
                                self.selected_index = idx
                                self._last_axis_move_time = now
                                break
            elif event.type == pygame.JOYHATMOTION:
                # event.value is a tuple (x,y); x=-1 left, 1 right
                if event.value[0] != 0 and now - self._last_axis_move_time >= self._axis_move_cooldown:
                    current_btn = self.buttons[self.selected_index]
                    target_kind = None
                    if isinstance(current_btn.action, tuple):
                        if current_btn.action[0] == "load_slot":
                            target_kind = "delete_slot"
                        elif current_btn.action[0] == "delete_slot":
                            target_kind = "load_slot"
                    if target_kind:
                        for idx, btn in enumerate(self.buttons):
                            if btn is current_btn:
                                continue
                            if isinstance(btn.action, tuple) and btn.action[0] == target_kind and btn.rect.y == current_btn.rect.y:
                                self.selected_index = idx
                                self._last_axis_move_time = now
                                break
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            for button in self.buttons:
                if button.update(mouse_pos, True):
                    if isinstance(button.action, tuple):
                        if button.action[0] == "load_slot":
                            slot_val = button.action[1]
                            if isinstance(slot_val, int):
                                self.selected_slot = slot_val
                                return ("load_game", self.selected_slot)  # Return special load action
                            return None
                        elif button.action[0] == "delete_slot":
                            # Show delete confirmation
                            self.delete_slot = button.action[1] if isinstance(button.action[1], int) else None
                            self.show_delete_confirmation = True
                            self.setup_buttons()  # Refresh buttons to show confirmation
                            return None
                        elif button.action[0] == "confirm_delete":
                            # Actually delete the save
                            if isinstance(button.action[1], int) and save_manager.delete_save(button.action[1]):
                                print(f"🗑️ Save slot {button.action[1]} deleted successfully")
                            else:
                                print(f"❌ Failed to delete save slot {button.action[1]}")
                            self.show_delete_confirmation = False
                            self.delete_slot = None
                            self.refresh_save_slots()  # Refresh save data
                            self.setup_buttons()  # Refresh buttons
                            return None
                        elif button.action[0] == "cancel_delete":
                            # Cancel delete confirmation
                            self.show_delete_confirmation = False
                            self.delete_slot = None
                            self.setup_buttons()  # Refresh buttons to hide confirmation
                            return None
                    else:
                        return button.action
        elif event.type == pygame.MOUSEMOTION:
            mouse_pos = pygame.mouse.get_pos()
            for button in self.buttons:
                button.update(mouse_pos, False)
        
        # Handle ESC key to cancel delete confirmation
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE and self.show_delete_confirmation:
                self.show_delete_confirmation = False
                self.delete_slot = None
                self.setup_buttons()
                return None
            elif event.key == pygame.K_RETURN and self.show_delete_confirmation:
                # Enter key confirms delete
                if isinstance(self.delete_slot, int) and save_manager.delete_save(self.delete_slot):
                    print(f"🗑️ Save slot {self.delete_slot} deleted successfully")
                else:
                    print(f"❌ Failed to delete save slot {self.delete_slot}")
                self.show_delete_confirmation = False
                self.delete_slot = None
                self.refresh_save_slots()
                self.setup_buttons()
                return None
        
        return None
    
    def draw(self):
        """Draw load game menu"""
        super().draw()
        
        # Title
        title_text = "Spiel laden" if getattr(self, 'disable_menu_emojis', False) else "📁 Spiel laden"
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
        
        # Draw delete confirmation dialog
        if self.show_delete_confirmation:
            self.draw_delete_confirmation()
    
    def draw_delete_confirmation(self):
        """Draw delete confirmation dialog"""
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()
        
        # Semi-transparent overlay
        overlay = pygame.Surface((screen_width, screen_height))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        # Dialog box
        dialog_width = 400
        dialog_height = 220
        dialog_x = (screen_width - dialog_width) // 2
        dialog_y = (screen_height - dialog_height) // 2
        
        dialog_rect = pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height)
        pygame.draw.rect(self.screen, (40, 40, 60), dialog_rect)
        pygame.draw.rect(self.screen, (200, 100, 100), dialog_rect, 3)
        
        # Warning icon and text
        warning_text = "⚠️"
        warning_surface = self.title_font.render(warning_text, True, (255, 200, 100))
        warning_rect = warning_surface.get_rect(center=(screen_width // 2, dialog_y + 50))
        self.screen.blit(warning_surface, warning_rect)
        
        # Confirmation message
        slot_name = "Unbekannt"
        for slot in self.save_slots:
            if slot["slot"] == self.delete_slot:
                slot_name = slot["name"]
                break
        
        message_lines = [
            "Spielstand löschen?",
            f"'{slot_name}' wird unwiderruflich gelöscht!",
            "Diese Aktion kann nicht rückgängig gemacht werden.",
            "",
            "Enter/I = Bestätigen, Esc/Z = Abbrechen"
        ]
        
        y_text = dialog_y + 90
        for line in message_lines:
            text_surface = self.text_font.render(line, True, (255, 255, 255))
            text_rect = text_surface.get_rect(center=(screen_width // 2, y_text))
            self.screen.blit(text_surface, text_rect)
            y_text += 25

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
                ("💾 Speichern in Slot 5", "save_slot_5"),
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
        """Handle pause menu events (mouse + keyboard/joystick)"""
        # First try base navigation
        base_result = super().handle_event(event)
        if base_result is not None:
            if base_result == "show_save_menu":
                self.show_save_menu = True
                self.setup_buttons()
                return None
            elif base_result == "back_to_pause":
                self.show_save_menu = False
                self.setup_buttons()
                return None
            elif base_result in ("save_slot_1", "save_slot_2", "save_slot_3", "save_slot_4", "save_slot_5"):
                slot_map: Dict[str, int] = {"save_slot_1": 1, "save_slot_2": 2, "save_slot_3": 3, "save_slot_4": 4, "save_slot_5": 5}
                slot_val = slot_map.get(str(base_result))
                if slot_val is not None:
                    return ("save_to_slot", slot_val)
                return None
            else:
                return base_result
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
                    elif button.action == "save_slot_5":
                        return ("save_to_slot", 5)
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
                elif event.key == pygame.K_5:
                    return ("save_to_slot", 5)
        
        return None

    def draw(self):
        """Draw pause menu"""
        # Draw semi-transparent background
        self.screen.blit(self.background_surface, (0, 0))
        
        # Title
        if not self.show_save_menu:
            title_text = "Spiel Pausiert" if getattr(self, 'disable_menu_emojis', False) else "⏸️ Spiel Pausiert"
            subtitle_text = "ESC zum Fortsetzen"
        else:
            title_text = "Spiel Speichern" if getattr(self, 'disable_menu_emojis', False) else "💾 Spiel Speichern"
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
        title_text = "GAME OVER" if getattr(self, 'disable_menu_emojis', False) else "💀 GAME OVER 💀"
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
        for i, button in enumerate(self.buttons):
            button.draw(self.screen)
            if i == self.selected_index:
                # Draw a selection highlight similar to BaseMenuState
                pygame.draw.rect(self.screen, (255, 215, 0), button.rect.inflate(8, 6), 2)
                if not getattr(self, 'disable_menu_emojis', False):
                    try:
                        arrow_surface = self.text_font.render("➤", True, (255, 215, 0))
                        arrow_rect = arrow_surface.get_rect()
                        arrow_rect.centery = button.rect.centery
                        arrow_rect.right = button.rect.left - 12
                        self.screen.blit(arrow_surface, arrow_rect)
                    except Exception:
                        pass
        
        # Show controls hint (always visible)
        hint_text = "⌨️ ESC: Hauptmenü  •  R: Neues Spiel"
        hint_surface = pygame.font.Font(None, 24).render(hint_text, True, (100, 100, 100))
        hint_rect = hint_surface.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() - 50))
        self.screen.blit(hint_surface, hint_rect)
    
    def handle_event(self, event: pygame.event.Event) -> Optional[Any]:
        """Handle game over events"""
        # Always allow interaction (remove fade-in restriction for debugging)
        # Delegate to base handler to support mouse/keyboard/joystick navigation
        result = super().handle_event(event)
        if result is not None:
            return result
        
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

        # Integrate Action System so hardware "brew/attack" selects in menus
        if _ACTION_SYSTEM_AVAILABLE and get_action_system is not None:
            try:
                self._action_system = get_action_system()

                def _confirm_from_action(evt):
                    # Only react on PRESS and when we are in menu-like states
                    if not evt.pressed:
                        return
                    if self.current_state in [GameState.MAIN_MENU, GameState.SETTINGS, GameState.CREDITS,
                                              GameState.LOAD_GAME, GameState.PAUSE, GameState.GAME_OVER]:
                        # Post a synthetic ENTER key event so existing handlers run
                        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))

                # Map both ATTACK and CAST_MAGIC to confirm selection
                if hasattr(self._action_system, "register_handler") and ActionType is not None:
                    self._action_system.register_handler(ActionType.ATTACK, _confirm_from_action)
                    self._action_system.register_handler(ActionType.CAST_MAGIC, _confirm_from_action)
            except Exception:
                self._action_system = None
    
    def handle_event(self, event: pygame.event.Event) -> Optional[Any]:
        """Handle events and return state change if needed"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                # Don't allow ESC to leave Game Over screen
                if self.current_state == GameState.GAME_OVER:
                    self.change_state(GameState.MAIN_MENU)
                    return None
                # Let Settings screen handle its own ESC/back logic
                elif self.current_state != GameState.MAIN_MENU and self.current_state != GameState.SETTINGS:
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
                elif isinstance(result, GameState):
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
            # Reset selection so first item is focused by default
            state_obj = self.states.get(new_state)
            if state_obj is not None and hasattr(state_obj, 'selected_index'):
                state_obj.selected_index = 0
    
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
