# -*- coding: utf-8 -*-
"""
Save Game System for the Alchemist Game
Handles saving and loading game progress
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from settings import ROOT_DIR

class SaveGameManager:
    """Manages game save/load functionality"""
    
    def __init__(self):
        self.save_dir = os.path.join(ROOT_DIR, "saves")
        self.ensure_save_directory()
    
    def ensure_save_directory(self):
        """Create saves directory if it doesn't exist"""
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
            print(f"📁 Created saves directory: {self.save_dir}")
    
    def save_game(self, slot_number: int, game_data: Dict[str, Any]) -> bool:
        """Save game to specified slot"""
        try:
            save_file = os.path.join(self.save_dir, f"save_slot_{slot_number}.json")
            
            # Add timestamp to save data
            save_data = {
                "timestamp": datetime.now().isoformat(),
                "save_version": "1.0",
                "game_data": game_data
            }
            
            with open(save_file, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Game saved to slot {slot_number}")
            return True
            
        except Exception as e:
            print(f"❌ Error saving game: {e}")
            return False
    
    def load_game(self, slot_number: int) -> Optional[Dict[str, Any]]:
        """Load game from specified slot"""
        try:
            save_file = os.path.join(self.save_dir, f"save_slot_{slot_number}.json")
            
            if not os.path.exists(save_file):
                print(f"📭 No save file found for slot {slot_number}")
                return None
            
            with open(save_file, 'r', encoding='utf-8') as f:
                save_data = json.load(f)
            
            print(f"📂 Game loaded from slot {slot_number}")
            return save_data.get("game_data", {})
            
        except Exception as e:
            print(f"❌ Error loading game: {e}")
            return None
    
    def get_save_slots_info(self) -> List[Dict[str, str]]:
        """Get information about all save slots"""
        slots_info = []
        
        # Include auto-save slot (slot 0) and regular slots (1-5)
        for slot_number in range(0, 6):  # 0 for auto-save, 1-5 for manual saves
            save_file = os.path.join(self.save_dir, f"save_slot_{slot_number}.json")
            
            if os.path.exists(save_file):
                try:
                    with open(save_file, 'r', encoding='utf-8') as f:
                        save_data = json.load(f)
                    
                    timestamp = save_data.get("timestamp", "")
                    if timestamp:
                        # Format timestamp for display
                        dt = datetime.fromisoformat(timestamp)
                        formatted_date = dt.strftime("%d.%m.%Y %H:%M")
                    else:
                        formatted_date = "Unbekannt"
                    
                    game_data = save_data.get("game_data", {})
                    level_info = game_data.get("level_info", "Level 1")
                    
                    if slot_number == 0:
                        player_name = "Auto-Save"
                    else:
                        player_name = game_data.get("player_name", f"Spielstand {slot_number}")
                    
                    slots_info.append({
                        "slot": slot_number,
                        "name": player_name,
                        "date": formatted_date,
                        "level": level_info,
                        "exists": True
                    })
                    
                except Exception as e:
                    print(f"⚠️ Error reading save slot {slot_number}: {e}")
                    slot_name = "Auto-Save (Beschädigt)" if slot_number == 0 else f"Beschädigter Spielstand {slot_number}"
                    slots_info.append({
                        "slot": slot_number,
                        "name": slot_name,
                        "date": "Fehler",
                        "level": "Unbekannt",
                        "exists": True
                    })
            else:
                if slot_number == 0:
                    slot_name = "Auto-Save (Leer)"
                else:
                    slot_name = f"Leerer Slot {slot_number}"
                
                slots_info.append({
                    "slot": slot_number,
                    "name": slot_name,
                    "date": "",
                    "level": "",
                    "exists": False
                })
        
        return slots_info
    
    def delete_save(self, slot_number: int) -> bool:
        """Delete save from specified slot"""
        try:
            save_file = os.path.join(self.save_dir, f"save_slot_{slot_number}.json")
            
            if os.path.exists(save_file):
                os.remove(save_file)
                print(f"🗑️ Save slot {slot_number} deleted")
                return True
            else:
                print(f"📭 No save file found for slot {slot_number}")
                return False
                
        except Exception as e:
            print(f"❌ Error deleting save: {e}")
            return False
    
    def export_save_data(self, game_logic) -> Dict[str, Any]:
        """Export current game state to saveable format"""
        if not game_logic:
            return {}
        
        save_data = {
            "player_name": "Alchemist",  # Could be customizable
            "level_info": "Level 1",     # Current level info
            "player_data": {
                "position": (game_logic.player.rect.centerx, game_logic.player.rect.centery),
                "health": getattr(game_logic.player, 'current_health', 100),
                "max_health": getattr(game_logic.player, 'max_health', 100)
            },
            "game_progress": {
                "score": game_logic.score,
                "active_ingredients": game_logic.aktive_zutaten.copy(),
                "last_brew_result": game_logic.last_brew_result
            },
            "alchemy_data": {
                "discovered_recipes": []  # Could track discovered recipes
            },
            "timestamp": datetime.now().isoformat()
        }
        
        return save_data
    
    def apply_save_data(self, game_logic, save_data: Dict[str, Any]) -> bool:
        """Apply loaded save data to game state"""
        try:
            if not game_logic or not save_data:
                return False
            
            # Restore player data
            player_data = save_data.get("player_data", {})
            if "position" in player_data:
                pos = player_data["position"]
                game_logic.player.rect.centerx = pos[0]
                game_logic.player.rect.centery = pos[1]
                game_logic.player.update_hitbox()
            
            # Restore game progress
            game_progress = save_data.get("game_progress", {})
            game_logic.score = game_progress.get("score", 0)
            game_logic.aktive_zutaten = game_progress.get("active_ingredients", [])
            game_logic.last_brew_result = game_progress.get("last_brew_result", "Spiel geladen")
            
            print("✅ Save data applied successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error applying save data: {e}")
            return False

# Global save manager instance
save_manager = SaveGameManager()
