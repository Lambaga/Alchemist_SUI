# -*- coding: utf-8 -*-
"""
🚀 RPi-Optimierung: Zentrales Font-Management
Vermeidet mehrfache Font-Erstellung und reduziert Memory-Verbrauch
"""

import pygame
from typing import Dict, Tuple, Optional
from core.config import DisplayConfig


class FontManager:
    """
    Singleton Font-Manager für zentrales Font-Caching.
    Verhindert redundante pygame.font.Font() Aufrufe in verschiedenen Klassen.
    """
    
    _instance = None
    
    # Standard Font-Größen für verschiedene UI-Elemente
    FONT_SIZES = {
        'tiny': 16,
        'small': 20,
        'normal': 24,
        'medium': 28,
        'large': 32,
        'xlarge': 36,
        'title': 48,
        'huge': 64,
    }
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._fonts: Dict[Tuple[Optional[str], int], pygame.font.Font] = {}
            cls._instance._initialized = False
        return cls._instance
    
    def _ensure_initialized(self):
        """Lazy initialization - pygame.font muss initialisiert sein"""
        if not self._initialized:
            if not pygame.font.get_init():
                pygame.font.init()
            self._initialized = True
    
    def get_font(self, size: int, font_path: Optional[str] = None) -> pygame.font.Font:
        """
        Gibt eine gecachte Font-Instanz zurück.
        
        :param size: Schriftgröße in Pixel
        :param font_path: Optionaler Pfad zu einer TTF-Datei (None = System-Font)
        :return: pygame.font.Font Instanz
        """
        self._ensure_initialized()
        
        cache_key = (font_path, size)
        
        if cache_key not in self._fonts:
            try:
                self._fonts[cache_key] = pygame.font.Font(font_path, size)
            except Exception as e:
                print(f"⚠️ Font-Fehler ({font_path}, {size}): {e}, verwende Fallback")
                # Fallback auf System-Font
                self._fonts[cache_key] = pygame.font.Font(None, size)
        
        return self._fonts[cache_key]
    
    def get_sized(self, size_name: str, font_path: Optional[str] = None) -> pygame.font.Font:
        """
        Gibt Font mit vordefinierter Größe zurück.
        
        :param size_name: Name aus FONT_SIZES ('tiny', 'small', 'normal', etc.)
        :param font_path: Optionaler Pfad zu einer TTF-Datei
        :return: pygame.font.Font Instanz
        """
        size = self.FONT_SIZES.get(size_name, self.FONT_SIZES['normal'])
        return self.get_font(size, font_path)
    
    def get_scaled_font(self, base_size: int, font_path: Optional[str] = None) -> pygame.font.Font:
        """
        Gibt skalierte Font basierend auf Display-Konfiguration zurück.
        Nützlich für RPi 7-Zoll Display Anpassung.
        
        :param base_size: Basis-Größe für 1080p
        :param font_path: Optionaler Pfad zu einer TTF-Datei
        :return: pygame.font.Font Instanz mit angepasster Größe
        """
        try:
            scale = DisplayConfig.get_ui_scale()
        except Exception:
            scale = 1.0
        
        scaled_size = max(10, int(base_size * scale))
        return self.get_font(scaled_size, font_path)
    
    # === Convenience-Methoden für häufig verwendete Fonts ===
    
    def debug_font(self) -> pygame.font.Font:
        """Font für Debug/FPS-Anzeige"""
        return self.get_font(24)
    
    def ui_font(self) -> pygame.font.Font:
        """Standard UI-Font"""
        return self.get_font(28)
    
    def small_font(self) -> pygame.font.Font:
        """Kleine Schrift für Items/Labels"""
        return self.get_font(22)
    
    def title_font(self) -> pygame.font.Font:
        """Große Schrift für Titel"""
        return self.get_font(48)
    
    def interaction_font(self) -> pygame.font.Font:
        """Font für Interaktionstexte"""
        return self.get_font(32)
    
    def get_cache_info(self) -> Dict[str, int]:
        """Cache-Statistiken für Debugging"""
        return {
            'cached_fonts': len(self._fonts),
            'font_sizes': list(set(size for _, size in self._fonts.keys()))
        }
    
    def clear_cache(self):
        """Leert den Font-Cache (z.B. bei Resolution-Wechsel)"""
        self._fonts.clear()


# Convenience-Funktion für einfachen Zugriff
def get_font_manager() -> FontManager:
    """Gibt die FontManager Singleton-Instanz zurück"""
    return FontManager()
