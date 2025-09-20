# -*- coding: utf-8 -*-
"""
Unit Tests for Spell Cooldown Manager
"""

import sys
import os
import time

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'systems'))

# Initialize pygame (required for timing)
import pygame
pygame.init()

from src.systems.spell_cooldown_manager import SpellCooldownManager


def test_basic_functionality():
    """Test basic cooldown functionality"""
    print("=== Test: Basic Functionality ===")
    
    manager = SpellCooldownManager()
    
    # Test 1: Spell should be ready initially
    assert manager.is_ready("fireball"), "Spell should be ready initially"
    assert manager.time_remaining("fireball") == 0.0, "No time should remain initially"
    assert manager.progress("fireball") == 1.0, "Progress should be 100% when ready"
    
    # Test 2: Start cooldown
    manager.start_cooldown("fireball", 0.1)  # 0.1 second for quick test
    assert not manager.is_ready("fireball"), "Spell should not be ready after starting cooldown"
    assert manager.time_remaining("fireball") > 0, "Time should remain after starting cooldown"
    assert manager.progress("fireball", 0.1) < 1.0, "Progress should be less than 100% during cooldown"
    
    print("✅ Basic functionality tests passed")


def test_cooldown_expiration():
    """Test cooldown expiration"""
    print("=== Test: Cooldown Expiration ===")
    
    manager = SpellCooldownManager()
    
    # Start a very short cooldown
    manager.start_cooldown("healing", 0.05)  # 50ms
    
    # Should not be ready immediately
    assert not manager.is_ready("healing"), "Should not be ready immediately"
    
    # Wait for cooldown to expire
    time.sleep(0.1)  # 100ms wait
    
    # Should be ready now
    assert manager.is_ready("healing"), "Should be ready after expiration"
    assert manager.time_remaining("healing") == 0.0, "No time should remain after expiration"
    
    print("✅ Cooldown expiration test passed")


def test_multiple_spells():
    """Test multiple spells independently"""
    print("=== Test: Multiple Spells ===")
    
    manager = SpellCooldownManager()
    
    # Start cooldowns for different spells
    manager.start_cooldown("fireball", 0.2)
    manager.start_cooldown("healing", 0.1)
    manager.start_cooldown("shield", 0.3)
    
    # All should be on cooldown
    assert not manager.is_ready("fireball")
    assert not manager.is_ready("healing")
    assert not manager.is_ready("shield")
    
    # Check all_cooldowns
    all_cooldowns = manager.get_all_cooldowns()
    assert len(all_cooldowns) == 3, "Should have 3 active cooldowns, got {}".format(len(all_cooldowns))
    
    # Wait for healing to expire (shortest cooldown)
    time.sleep(0.15)
    
    # Healing should be ready, others still on cooldown
    assert manager.is_ready("healing"), "Healing should be ready"
    assert not manager.is_ready("fireball"), "Fireball should still be on cooldown"
    assert not manager.is_ready("shield"), "Shield should still be on cooldown"
    
    print("✅ Multiple spells test passed")


def test_progress_calculation():
    """Test progress calculation accuracy"""
    print("=== Test: Progress Calculation ===")
    
    manager = SpellCooldownManager()
    
    # Start cooldown
    cooldown_time = 0.2  # 200ms
    manager.start_cooldown("test_spell", cooldown_time)
    
    # Check progress immediately (should be near 0%)
    initial_progress = manager.progress("test_spell", cooldown_time)
    assert 0.0 <= initial_progress <= 0.1, "Initial progress should be near 0%, got {}".format(initial_progress)
    
    # Wait halfway
    time.sleep(cooldown_time / 2)
    halfway_progress = manager.progress("test_spell", cooldown_time)
    assert 0.4 <= halfway_progress <= 0.6, "Halfway progress should be ~50%, got {}".format(halfway_progress)
    
    # Wait for completion
    time.sleep(cooldown_time / 2 + 0.05)  # A bit extra to be sure
    final_progress = manager.progress("test_spell", cooldown_time)
    assert final_progress == 1.0, "Final progress should be 100%, got {}".format(final_progress)
    
    print("✅ Progress calculation test passed")


def test_edge_cases():
    """Test edge cases and error conditions"""
    print("=== Test: Edge Cases ===")
    
    manager = SpellCooldownManager()
    
    # Test with non-existent spell
    assert manager.is_ready("nonexistent"), "Non-existent spell should be ready"
    assert manager.time_remaining("nonexistent") == 0.0, "Non-existent spell should have 0 remaining time"
    assert manager.progress("nonexistent") == 1.0, "Non-existent spell should have 100% progress"
    
    # Test clearing cooldowns
    manager.start_cooldown("test1", 1.0)
    manager.start_cooldown("test2", 1.0)
    
    assert not manager.is_ready("test1")
    assert not manager.is_ready("test2")
    
    # Clear specific cooldown
    manager.clear_cooldown("test1")
    assert manager.is_ready("test1"), "test1 should be ready after clearing"
    assert not manager.is_ready("test2"), "test2 should still be on cooldown"
    
    # Clear all cooldowns
    manager.clear_all_cooldowns()
    assert manager.is_ready("test2"), "test2 should be ready after clearing all"
    
    print("✅ Edge cases test passed")


def run_all_tests():
    """Run all unit tests"""
    print("🧪 Starting Spell Cooldown Manager Unit Tests\n")
    
    try:
        test_basic_functionality()
        test_cooldown_expiration()
        test_multiple_spells()
        test_progress_calculation()
        test_edge_cases()
        
        print("\n✅ ALL TESTS PASSED! ✅")
        print("SpellCooldownManager is working correctly.")
        
    except AssertionError as e:
        print("\n❌ TEST FAILED: {}".format(e))
        return False
    except Exception as e:
        print("\n💥 UNEXPECTED ERROR: {}".format(e))
        return False
    
    return True


if __name__ == "__main__":
    success = run_all_tests()
    pygame.quit()
    sys.exit(0 if success else 1)
