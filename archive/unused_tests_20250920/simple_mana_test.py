import sys
import os
sys.path.append('src')
sys.path.append('src/core')

try:
    from core.settings import MANA_MAX, MANA_REGEN_PER_SEC, MANA_SPELL_COST
    print("Settings imported successfully")
    print("MANA_MAX:", MANA_MAX)
    print("MANA_REGEN_PER_SEC:", MANA_REGEN_PER_SEC)
    print("MANA_SPELL_COST:", MANA_SPELL_COST)
    
    # Test basic mana functionality
    class TestPlayer:
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
    
    player = TestPlayer()
    print("\nTesting mana system:")
    print("Initial mana:", player.current_mana)
    
    # Test spending mana
    success = player.spend_mana(10)
    print("Spend 10 mana:", "Success" if success else "Failed")
    print("Current mana:", player.current_mana)
    
    # Test regeneration
    player.regen_mana(1.0)  # 1 second
    print("After 1 second regen:", player.current_mana)
    
    print("\nMana system test completed successfully!")
    
except ImportError as e:
    print("Import error:", e)
    sys.exit(1)
