# -*- coding: utf-8 -*-
"""
Save Game System for the Alchemist Game
Handles saving and loading game progress
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from core.settings import ROOT_DIR

class SaveGameManager:
    """Manages game save/load functionality"""
    
    MAX_SLOTS = 5  # Slots 1..5
    
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
        """Get information about all save slots (1..MAX_SLOTS)."""
        slots_info = []
        
        # Regular slots (1..MAX_SLOTS)
        for slot_number in range(1, self.MAX_SLOTS + 1):
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
                    slot_name = f"Beschädigter Spielstand {slot_number}"
                    slots_info.append({
                        "slot": slot_number,
                        "name": slot_name,
                        "date": "Fehler",
                        "level": "Unbekannt",
                        "exists": True
                    })
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

    def _load_slot_timestamp(self, slot_number: int) -> float:
        """Return a sortable timestamp for the given slot. Fallback to file mtime."""
        save_file = os.path.join(self.save_dir, f"save_slot_{slot_number}.json")
        if not os.path.exists(save_file):
            return 0.0
        try:
            with open(save_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            ts = data.get("timestamp")
            if ts:
                return datetime.fromisoformat(ts).timestamp()
        except Exception:
            pass
        try:
            return os.path.getmtime(save_file)
        except Exception:
            return 0.0

    def get_next_free_slot(self) -> Optional[int]:
        """Return first empty slot number in 1..MAX_SLOTS, else None."""
        for slot in range(1, self.MAX_SLOTS + 1):
            save_file = os.path.join(self.save_dir, f"save_slot_{slot}.json")
            if not os.path.exists(save_file):
                return slot
        return None

    def get_oldest_slot(self) -> Optional[int]:
        """Return the slot number with the oldest timestamp in 1..MAX_SLOTS, or None if none exist."""
        timestamps = []
        for slot in range(1, self.MAX_SLOTS + 1):
            save_file = os.path.join(self.save_dir, f"save_slot_{slot}.json")
            if os.path.exists(save_file):
                timestamps.append((self._load_slot_timestamp(slot), slot))
        if not timestamps:
            return None
        timestamps.sort(key=lambda x: x[0])
        return timestamps[0][1]

    def save_auto(self, game_data: Dict[str, Any]) -> Optional[int]:
        """Save to first free slot 1..MAX_SLOTS, otherwise overwrite the oldest. Returns used slot or None on failure."""
        try:
            slot = self.get_next_free_slot()
            if slot is None:
                slot = self.get_oldest_slot()
            if slot is None:
                # No slots available? Should not happen, but guard.
                print("❌ No available save slots")
                return None
            ok = self.save_game(slot, game_data)
            return slot if ok else None
        except Exception as e:
            print(f"❌ Error in save_auto: {e}")
            return None
    
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
