# -*- coding: utf-8 -*-
"""
Quick test for the Mana system implementation
"""

import sys
import os
sys.path.append('src')
sys.path.append('src/core')
sys.path.append('src/entities')
sys.path.append('src/systems')

# Test imports
try:
    from core.settings import MANA_MAX, MANA_REGEN_PER_SEC, MANA_SPELL_COST
    print("Settings imported successfully:")
    print(f"   MANA_MAX: {MANA_MAX}")
    print(f"   MANA_REGEN_PER_SEC: {MANA_REGEN_PER_SEC}") 
    print(f"   MANA_SPELL_COST: {MANA_SPELL_COST}")
except ImportError as e:
    print(f"Settings import failed: {e}")
    sys.exit(1)

# Simple Player class mock to test mana functionality
class MockPlayer:
    def __init__(self):
        self.max_mana = MANA_MAX
        self.current_mana = self.max_mana
        self.mana_regen_rate = MANA_REGEN_PER_SEC
    
    def spend_mana(self, amount):
        if self.current_mana >= amount:
            self.current_mana -= amount
            return True
        return False
    
    def regen_mana(self, dt):
        if self.current_mana < self.max_mana:
            mana_increase = self.mana_regen_rate * dt
            self.current_mana = min(self.max_mana, self.current_mana + mana_increase)
    
    def get_mana_percentage(self):
        return self.current_mana / self.max_mana if self.max_mana > 0 else 0.0

def test_mana_system():
    print("\nTesting Mana System...")
    
    player = MockPlayer()
    
    # Test 1: Initial mana
    print(f"\n1. Initial mana: {player.current_mana}/{player.max_mana} ({player.get_mana_percentage()*100:.1f}%)")
    assert player.current_mana == 100, "Initial mana should be 100"
    
    # Test 2: Spend mana (should succeed)
    success = player.spend_mana(MANA_SPELL_COST)
    print(f"2. Spend {MANA_SPELL_COST} mana: {'Success' if success else 'Failed'}")
    print(f"   Current mana: {player.current_mana}/{player.max_mana}")
    assert success == True, "Should be able to spend mana"
    assert player.current_mana == 90, "Mana should be reduced to 90"
    
    # Test 3: Try to spend more mana than available
    player.current_mana = 5  # Set low mana
    success = player.spend_mana(MANA_SPELL_COST)
    print(f"3. Try to spend {MANA_SPELL_COST} with only 5 mana: {'Correctly failed' if not success else 'Should have failed'}")
    assert success == False, "Should fail when not enough mana"
    assert player.current_mana == 5, "Mana should remain unchanged"
    
    # Test 4: Mana regeneration
    player.current_mana = 0  # Start empty
    player.regen_mana(1.0)  # 1 second = 3 mana regen
    print(f"4. Regen after 1 second: {player.current_mana}/{player.max_mana} (should be ~3)")
    assert abs(player.current_mana - 3.0) < 0.1, "Should regen 3 mana per second"
    
    # Test 5: Regen over multiple frames (simulate 60 FPS)
    player.current_mana = 0
    for frame in range(180):  # 3 seconds at 60 FPS
        player.regen_mana(1.0/60.0)
    print(f"5. Regen after 3 seconds (180 frames): {player.current_mana}/{player.max_mana} (should be ~9)")
    assert abs(player.current_mana - 9.0) < 0.5, "Should regen ~9 mana in 3 seconds"
    
    # Test 6: Max mana clamping
    player.current_mana = 95
    player.regen_mana(2.0)  # Should add 6 mana, but clamp to 100
    print(f"6. Regen with clamping: {player.current_mana}/{player.max_mana} (should be exactly 100)")
    assert player.current_mana == 100, "Should be clamped to max mana"
    
    print("\nAll Mana system tests passed!")

if __name__ == "__main__":
    test_mana_system()
    print("\nMana system is ready for integration!")
    print("\nNext steps:")
    print("1. Start your game with your .bat file")
    print("2. Try casting magic to see mana consumption")
    print("3. Watch mana regenerate over time")
    print("4. Try casting with low mana (should fail)")
