# -*- coding: utf-8 -*-
"""
High-Score Manager - Speichert und lädt High-Scores pro NFC-Tag
"""

import json
import os
from pathlib import Path
from typing import Optional

try:
    from core.settings import VERBOSE_LOGS
except Exception:
    VERBOSE_LOGS = False


class HighScoreManager:
    """Verwaltet High-Scores pro NFC-Tag UID"""
    
    def __init__(self, save_dir: str = "saves"):
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(exist_ok=True)
        self.highscore_file = self.save_dir / "highscores.json"
        self.highscores = self._load_highscores()
    
    def _load_highscores(self) -> dict:
        """Lade High-Score Datenbank"""
        if self.highscore_file.exists():
            try:
                with open(self.highscore_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                if VERBOSE_LOGS:
                    print(f"⚠️ High-Score Load Fehler: {e}")
                return {}
        return {}
    
    def _save_highscores(self):
        """Speichere High-Score Datenbank"""
        try:
            with open(self.highscore_file, 'w', encoding='utf-8') as f:
                json.dump(self.highscores, f, indent=2, ensure_ascii=False)
            if VERBOSE_LOGS:
                print(f"💾 High-Scores gespeichert")
        except Exception as e:
            if VERBOSE_LOGS:
                print(f"❌ High-Score Save Fehler: {e}")
    
    def get_highscore(self, uid: str) -> Optional[int]:
        """Hole High-Score für UID (oder None wenn nicht vorhanden)"""
        # Normalize UID to standard format
        uid_key = self._normalize_uid(uid)
        return self.highscores.get(uid_key)
    
    def set_highscore(self, uid: str, score: int) -> bool:
        """
        Speichere High-Score für UID (nur wenn höher als bisheriger)
        Gibt True zurück wenn neuer High-Score, False wenn nicht höher
        """
        uid_key = self._normalize_uid(uid)
        current_high = self.highscores.get(uid_key, 0)
        
        if score > current_high:
            self.highscores[uid_key] = score
            self._save_highscores()
            if VERBOSE_LOGS:
                print(f"🏆 Neuer High-Score für {uid_key}: {score} (Vorher: {current_high})")
            return True
        else:
            if VERBOSE_LOGS and score != current_high:
                print(f"📊 Score {score} nicht höher als High-Score {current_high}")
            return False
    
    @staticmethod
    def _normalize_uid(uid: str) -> str:
        """Normalisiere UID für Konsistenz"""
        # Remove spaces and colons, convert to lowercase
        uid_clean = uid.replace(" ", "").replace(":", "").lower()
        return uid_clean


# Singleton instance
_highscore_manager = None


def get_highscore_manager() -> HighScoreManager:
    """Hole globale HighScoreManager Instanz"""
    global _highscore_manager
    if _highscore_manager is None:
        _highscore_manager = HighScoreManager()
    return _highscore_manager
