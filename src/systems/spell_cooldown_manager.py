# -*- coding: utf-8 -*-
"""
Spell Cooldown Manager
Centralized system for tracking individual spell cooldowns with high-resolution timing
"""

import pygame
from typing import Dict, Optional
import time


class SpellCooldownManager:
    """
    Centralized spell cooldown tracking system
    
    Uses pygame.time.get_ticks() for consistency with game timing,
    with fallback to time.perf_counter() for high precision
    """
    
    def __init__(self):
        """Initialize the cooldown manager"""
        self._cooldowns: Dict[str, float] = {}  # spell_id -> end_time (in milliseconds)
        self._use_perf_counter = False  # Flag for timing method
        
        # Test timing precision
        self._init_timing_method()
    
    def _init_timing_method(self) -> None:
        """Choose the best timing method available"""
        try:
            # Test pygame timing
            start = pygame.time.get_ticks()
            time.sleep(0.001)  # 1ms sleep
            end = pygame.time.get_ticks()
            
            if end > start:
                print("🕰️ SpellCooldownManager: Using pygame.time.get_ticks()")
                self._use_perf_counter = False
            else:
                print("🕰️ SpellCooldownManager: Using time.perf_counter() for precision")
                self._use_perf_counter = True
        except:
            self._use_perf_counter = True
    
    def _get_current_time(self) -> float:
        """Get current time in milliseconds"""
        if self._use_perf_counter:
            return time.perf_counter() * 1000.0
        else:
            return float(pygame.time.get_ticks())
    
    def start_cooldown(self, spell_id: str, cooldown_duration: float = 3.0) -> None:
        """
        Start cooldown for a specific spell
        
        Args:
            spell_id: Unique identifier for the spell
            cooldown_duration: Cooldown time in seconds (default 3.0)
        """
        current_time = self._get_current_time()
        end_time = current_time + (cooldown_duration * 1000.0)  # Convert to milliseconds
        
        self._cooldowns[spell_id] = end_time
        
        print(f"🔥 Spell '{spell_id}' cooldown started: {cooldown_duration}s")
    
    def is_ready(self, spell_id: str) -> bool:
        """
        Check if a spell is ready to cast (not on cooldown)
        
        Args:
            spell_id: Spell to check
            
        Returns:
            True if spell is ready, False if on cooldown
        """
        if spell_id not in self._cooldowns:
            return True
        
        current_time = self._get_current_time()
        end_time = self._cooldowns[spell_id]
        
        if current_time >= end_time:
            # Cooldown expired, clean up
            del self._cooldowns[spell_id]
            return True
        
        return False
    
    def time_remaining(self, spell_id: str) -> float:
        """
        Get remaining cooldown time in seconds
        
        Args:
            spell_id: Spell to check
            
        Returns:
            Remaining time in seconds (0.0 if ready)
        """
        if spell_id not in self._cooldowns:
            return 0.0
        
        current_time = self._get_current_time()
        end_time = self._cooldowns[spell_id]
        
        remaining_ms = max(0.0, end_time - current_time)
        return remaining_ms / 1000.0
    
    def progress(self, spell_id: str, total_cooldown: float = 3.0) -> float:
        """
        Get cooldown progress as percentage
        
        Args:
            spell_id: Spell to check
            total_cooldown: Total cooldown duration in seconds
            
        Returns:
            Progress from 0.0 (just started) to 1.0 (ready)
        """
        if self.is_ready(spell_id):
            return 1.0
        
        remaining = self.time_remaining(spell_id)
        if remaining <= 0:
            return 1.0
        
        elapsed = total_cooldown - remaining
        return max(0.0, min(1.0, elapsed / total_cooldown))
    
    def get_all_cooldowns(self) -> Dict[str, float]:
        """
        Get all active cooldowns
        
        Returns:
            Dictionary of spell_id -> remaining_time_seconds
        """
        result = {}
        for spell_id in list(self._cooldowns.keys()):  # Copy keys to avoid dict change during iteration
            remaining = self.time_remaining(spell_id)
            if remaining > 0:
                result[spell_id] = remaining
        
        return result
    
    def clear_cooldown(self, spell_id: str) -> None:
        """
        Immediately clear a spell's cooldown (for testing/debugging)
        
        Args:
            spell_id: Spell to clear
        """
        if spell_id in self._cooldowns:
            del self._cooldowns[spell_id]
            print(f"🚀 Spell '{spell_id}' cooldown cleared")
    
    def clear_all_cooldowns(self) -> None:
        """Clear all active cooldowns (for testing/debugging)"""
        cleared_count = len(self._cooldowns)
        self._cooldowns.clear()
        print(f"🧹 All cooldowns cleared ({cleared_count} spells)")
    
    def update(self) -> None:
        """
        Update the cooldown system (cleanup expired cooldowns)
        Call this regularly in the game loop for efficiency
        """
        current_time = self._get_current_time()
        expired_spells = []
        
        for spell_id, end_time in self._cooldowns.items():
            if current_time >= end_time:
                expired_spells.append(spell_id)
        
        for spell_id in expired_spells:
            del self._cooldowns[spell_id]
