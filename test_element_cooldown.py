# -*- coding: utf-8 -*-
"""
Element Mixer Cooldown Test
Tests the cooldown system to ensure spells cannot be cast while on cooldown
"""

import sys
import os

# Add src directory to path
current_dir = os.path.dirname(__file__)
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

import pygame
from systems.spell_cooldown_manager import SpellCooldownManager
from ui.element_mixer import ElementMixer

def test_cooldown_system():
    """Test that cooldown system properly prevents spell casting"""
    print("🧪 Testing Element Mixer Cooldown System...")
    
    # Initialize pygame for font support
    pygame.init()
    pygame.font.init()
    
    # Create cooldown manager and element mixer
    cooldown_manager = SpellCooldownManager()
    element_mixer = ElementMixer(cooldown_manager)
    
    print("\n1️⃣ Testing Fire + Fire = Fireball combination...")
    
    # Select fire twice
    success1 = element_mixer.handle_element_press("fire")
    success2 = element_mixer.handle_element_press("fire")
    
    if success1 and success2:
        print("✅ Fire + Fire combination ready: {}".format(element_mixer.current_combination["display_name"]))
        
        # First cast should succeed
        cast_success1 = element_mixer.handle_cast_spell()
        if cast_success1:
            print("✅ First cast successful - cooldown started")
            
            # Prepare same combination again
            element_mixer.handle_element_press("fire")
            element_mixer.handle_element_press("fire")
            
            # Second cast should fail (on cooldown)
            cast_success2 = element_mixer.handle_cast_spell()
            if not cast_success2:
                print("✅ Second cast properly blocked by cooldown!")
                
                # Check cooldown status
                spell_id = "fireball"
                remaining = cooldown_manager.time_remaining(spell_id)
                print("⏳ Remaining cooldown: {:.1f}s".format(remaining))
                
                if remaining > 0:
                    print("✅ COOLDOWN TEST PASSED! 🎉")
                    return True
                else:
                    print("❌ COOLDOWN TEST FAILED - no remaining time")
            else:
                print("❌ COOLDOWN TEST FAILED - second cast should be blocked")
        else:
            print("❌ First cast failed unexpectedly")
    else:
        print("❌ Could not create Fire + Fire combination")
    
    return False

if __name__ == "__main__":
    try:
        success = test_cooldown_system()
        if success:
            print("\n🎉 All cooldown tests passed!")
        else:
            print("\n❌ Cooldown tests failed!")
    except Exception as e:
        print("❌ Test error: {}".format(e))
        import traceback
        traceback.print_exc()
