# -*- coding: utf-8 -*-
"""
🚀 Memory Monitor System für Raspberry Pi Performance-Tests

Bietet Echtzeit-Memory-Tracking für:
- Python Heap-Nutzung
- Pygame Surface Memory
- Cache-Größen (AssetManager, FontManager)
- Gesamt-System-Memory (falls psutil verfügbar)

Usage:
    from managers.memory_monitor import MemoryMonitor, get_memory_monitor
    
    # Im Game-Loop:
    monitor = get_memory_monitor()
    monitor.update()
    monitor.render(screen)  # Optional: Zeigt Overlay an
    
    # Für Logging:
    monitor.log_snapshot()
"""

import pygame
import gc
import sys
from typing import Dict, Any, Optional, List, Tuple
from collections import deque
import time

# Optional: psutil für System-Memory (nicht auf allen RPi vorinstalliert)
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


class MemoryMonitor:
    """
    Memory-Monitoring für RPi Performance-Tests.
    Trackt Python-Memory, Cache-Größen und optional System-Memory.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        
        # Konfiguration
        self.update_interval_ms = 1000  # Update alle 1 Sekunde
        self.history_size = 60  # 60 Sekunden Historie
        self.show_overlay = False
        self.overlay_position = (10, 100)  # Unter FPS-Anzeige
        
        # Timing
        self._last_update = 0
        
        # Memory-History für Trends
        self._memory_history: deque = deque(maxlen=self.history_size)
        
        # Aktuelle Werte
        self._current_stats: Dict[str, Any] = {}
        
        # Font (wird lazy initialisiert)
        self._font: Optional[pygame.font.Font] = None
        
        # Warnschwellen (in MB)
        self.warning_threshold_mb = 256  # Warnung bei 256 MB
        self.critical_threshold_mb = 384  # Kritisch bei 384 MB
        
        # Peak-Tracking
        self.peak_memory_mb = 0.0
        
    def _get_font(self) -> pygame.font.Font:
        """Lazy Font-Initialisierung"""
        if self._font is None:
            try:
                from managers.font_manager import get_font_manager
                self._font = get_font_manager().get_font(18)
            except Exception:
                pygame.font.init()
                self._font = pygame.font.Font(None, 18)
        return self._font
    
    def update(self) -> Dict[str, Any]:
        """
        Aktualisiert Memory-Statistiken (rate-limited).
        
        Returns:
            Dict mit aktuellen Memory-Statistiken
        """
        current_time = pygame.time.get_ticks()
        
        # Rate-limiting
        if current_time - self._last_update < self.update_interval_ms:
            return self._current_stats
            
        self._last_update = current_time
        
        stats = {}
        
        # 1. Python Object Count und GC Stats
        stats['gc_objects'] = len(gc.get_objects())
        stats['gc_counts'] = gc.get_count()
        
        # 2. Python Memory (via sys.getsizeof approximation)
        try:
            # Approximiere Heap-Größe durch Objekt-Count
            stats['python_objects_kb'] = stats['gc_objects'] * 0.1  # ~100 bytes pro Objekt
        except Exception:
            stats['python_objects_kb'] = 0
        
        # 3. System Memory (falls psutil verfügbar)
        if HAS_PSUTIL:
            try:
                process = psutil.Process()
                mem_info = process.memory_info()
                stats['process_rss_mb'] = mem_info.rss / (1024 * 1024)
                stats['process_vms_mb'] = mem_info.vms / (1024 * 1024)
                
                # System-weiter Memory
                sys_mem = psutil.virtual_memory()
                stats['system_total_mb'] = sys_mem.total / (1024 * 1024)
                stats['system_available_mb'] = sys_mem.available / (1024 * 1024)
                stats['system_percent'] = sys_mem.percent
            except Exception as e:
                stats['psutil_error'] = str(e)
        else:
            stats['process_rss_mb'] = stats.get('python_objects_kb', 0) / 1024
        
        # 4. Cache-Statistiken
        stats['caches'] = self._get_cache_stats()
        
        # 5. Pygame Surface Memory (Approximation)
        stats['pygame_surfaces'] = self._estimate_pygame_memory()
        
        # Peak-Tracking
        current_mb = stats.get('process_rss_mb', 0)
        if current_mb > self.peak_memory_mb:
            self.peak_memory_mb = current_mb
        stats['peak_memory_mb'] = self.peak_memory_mb
        
        # Status-Level
        if current_mb >= self.critical_threshold_mb:
            stats['status'] = 'critical'
        elif current_mb >= self.warning_threshold_mb:
            stats['status'] = 'warning'
        else:
            stats['status'] = 'ok'
        
        # Timestamp
        stats['timestamp'] = time.time()
        
        # Historie aktualisieren
        self._memory_history.append({
            'time': current_time,
            'rss_mb': stats.get('process_rss_mb', 0)
        })
        
        self._current_stats = stats
        return stats
    
    def _get_cache_stats(self) -> Dict[str, int]:
        """Sammelt Statistiken von allen Cache-Systemen"""
        cache_stats = {}
        
        # AssetManager
        try:
            from managers.asset_manager import AssetManager
            am = AssetManager()
            usage = am.get_memory_usage()
            cache_stats['asset_images'] = usage.get('images', 0)
            cache_stats['asset_sounds'] = usage.get('sounds', 0)
            cache_stats['asset_animations'] = usage.get('animations', 0)
            cache_stats['asset_sprites'] = usage.get('scaled_sprites', 0)
        except Exception:
            pass
        
        # FontManager
        try:
            from managers.font_manager import get_font_manager
            fm = get_font_manager()
            info = fm.get_cache_info()
            cache_stats['fonts'] = info.get('cached_fonts', 0)
        except Exception:
            pass
        
        return cache_stats
    
    def _estimate_pygame_memory(self) -> Dict[str, Any]:
        """Schätzt Pygame Surface Memory-Nutzung"""
        surface_info = {
            'display_size': (0, 0),
            'display_bytes': 0
        }
        
        try:
            display = pygame.display.get_surface()
            if display:
                w, h = display.get_size()
                bpp = display.get_bytesize()
                surface_info['display_size'] = (w, h)
                surface_info['display_bytes'] = w * h * bpp
                surface_info['display_mb'] = surface_info['display_bytes'] / (1024 * 1024)
        except Exception:
            pass
            
        return surface_info
    
    def get_memory_trend(self) -> str:
        """Berechnet Memory-Trend (steigend/stabil/fallend)"""
        if len(self._memory_history) < 10:
            return 'insufficient_data'
            
        recent = list(self._memory_history)[-10:]
        first_half = sum(h['rss_mb'] for h in recent[:5]) / 5
        second_half = sum(h['rss_mb'] for h in recent[5:]) / 5
        
        diff = second_half - first_half
        if diff > 5:  # > 5 MB Anstieg
            return 'rising'
        elif diff < -5:  # > 5 MB Abfall
            return 'falling'
        else:
            return 'stable'
    
    def render(self, screen: pygame.Surface):
        """Zeichnet Memory-Overlay auf den Screen"""
        if not self.show_overlay:
            return
            
        stats = self._current_stats
        if not stats:
            return
            
        font = self._get_font()
        x, y = self.overlay_position
        line_height = 16
        
        # Hintergrund
        bg_rect = pygame.Rect(x - 5, y - 5, 200, 120)
        bg_surface = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        bg_surface.fill((0, 0, 0, 180))
        screen.blit(bg_surface, bg_rect)
        
        # Status-Farbe
        status = stats.get('status', 'ok')
        if status == 'critical':
            color = (255, 80, 80)
        elif status == 'warning':
            color = (255, 200, 80)
        else:
            color = (80, 255, 80)
        
        # Titel
        title = font.render("🧠 Memory Monitor", True, (255, 255, 255))
        screen.blit(title, (x, y))
        y += line_height + 4
        
        # Process Memory
        rss = stats.get('process_rss_mb', 0)
        text = font.render(f"RSS: {rss:.1f} MB", True, color)
        screen.blit(text, (x, y))
        y += line_height
        
        # Peak
        peak = stats.get('peak_memory_mb', 0)
        text = font.render(f"Peak: {peak:.1f} MB", True, (200, 200, 200))
        screen.blit(text, (x, y))
        y += line_height
        
        # Trend
        trend = self.get_memory_trend()
        trend_symbols = {'rising': '📈', 'falling': '📉', 'stable': '➡️', 'insufficient_data': '❓'}
        text = font.render(f"Trend: {trend_symbols.get(trend, '?')} {trend}", True, (200, 200, 200))
        screen.blit(text, (x, y))
        y += line_height
        
        # Caches
        caches = stats.get('caches', {})
        total_cached = sum(caches.values())
        text = font.render(f"Cached: {total_cached} items", True, (180, 180, 255))
        screen.blit(text, (x, y))
        y += line_height
        
        # GC Objects
        gc_objs = stats.get('gc_objects', 0)
        text = font.render(f"GC Objects: {gc_objs:,}", True, (180, 180, 180))
        screen.blit(text, (x, y))
    
    def log_snapshot(self, label: str = ""):
        """Loggt aktuellen Memory-Status zur Konsole"""
        stats = self.update()
        
        print("\n" + "=" * 50)
        print(f"📊 MEMORY SNAPSHOT {label}")
        print("=" * 50)
        
        print(f"Process RSS:    {stats.get('process_rss_mb', 0):.2f} MB")
        print(f"Peak Memory:    {stats.get('peak_memory_mb', 0):.2f} MB")
        print(f"Status:         {stats.get('status', 'unknown').upper()}")
        print(f"Trend:          {self.get_memory_trend()}")
        
        print("\nCaches:")
        for name, count in stats.get('caches', {}).items():
            print(f"  {name}: {count}")
        
        print(f"\nGC Objects:     {stats.get('gc_objects', 0):,}")
        print(f"GC Counts:      {stats.get('gc_counts', (0,0,0))}")
        
        if HAS_PSUTIL:
            print(f"\nSystem Memory:  {stats.get('system_percent', 0):.1f}% used")
            print(f"Available:      {stats.get('system_available_mb', 0):.0f} MB")
        
        print("=" * 50 + "\n")
    
    def force_gc(self) -> int:
        """Erzwingt Garbage Collection und gibt Anzahl gesammelter Objekte zurück"""
        collected = gc.collect()
        print(f"🗑️ GC collected {collected} objects")
        return collected
    
    def toggle_overlay(self):
        """Schaltet Overlay-Anzeige um"""
        self.show_overlay = not self.show_overlay
        print(f"Memory Overlay: {'ON' if self.show_overlay else 'OFF'}")


# Convenience-Funktion
def get_memory_monitor() -> MemoryMonitor:
    """Gibt die MemoryMonitor Singleton-Instanz zurück"""
    return MemoryMonitor()
