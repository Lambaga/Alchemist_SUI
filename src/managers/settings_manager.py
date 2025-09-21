# -*- coding: utf-8 -*-
"""
Settings Manager - loads/saves user-adjustable settings (e.g., volumes).
"""

import json
import os
from typing import Any, Dict

try:
    from core.settings import ROOT_DIR
except Exception:
    ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


class SettingsManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return

        self._file_path = os.path.join(ROOT_DIR, 'saves', 'settings.json')
        self._settings: Dict[str, Any] = {
            'music_volume': 0.7,
            'sound_volume': 0.8,
            'master_volume': 1.0,
            'master_mute': False,
            'fullscreen': False,
            'show_fps': True,
            'difficulty': 'Normal',
        }
        self.load()
        self._initialized = True

    # Basic dict-like accessors
    def get(self, key: str, default: Any = None) -> Any:
        return self._settings.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._settings[key] = value

    # Properties for common settings
    @property
    def music_volume(self) -> float:
        return float(self._settings.get('music_volume', 0.7))

    @music_volume.setter
    def music_volume(self, value: float) -> None:
        v = max(0.0, min(1.0, float(value)))
        self._settings['music_volume'] = v

    @property
    def sound_volume(self) -> float:
        return float(self._settings.get('sound_volume', 0.8))

    @sound_volume.setter
    def sound_volume(self, value: float) -> None:
        v = max(0.0, min(1.0, float(value)))
        self._settings['sound_volume'] = v

    @property
    def master_volume(self) -> float:
        return float(self._settings.get('master_volume', 1.0))

    @master_volume.setter
    def master_volume(self, value: float) -> None:
        v = max(0.0, min(1.0, float(value)))
        self._settings['master_volume'] = v

    @property
    def master_mute(self) -> bool:
        return bool(self._settings.get('master_mute', False))

    @master_mute.setter
    def master_mute(self, value: bool) -> None:
        self._settings['master_mute'] = bool(value)

    def load(self) -> None:
        try:
            if os.path.exists(self._file_path):
                with open(self._file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    self._settings.update(data)
        except Exception:
            # Non-fatal: keep defaults
            pass

    def save(self) -> None:
        try:
            os.makedirs(os.path.dirname(self._file_path), exist_ok=True)
            with open(self._file_path, 'w', encoding='utf-8') as f:
                json.dump(self._settings, f, ensure_ascii=False, indent=2)
        except Exception:
            # Non-fatal: skip
            pass
