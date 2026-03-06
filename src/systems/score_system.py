# -*- coding: utf-8 -*-
"""
Score System – Verfolgt Spieler-Statistiken und berechnet den Endpunktestand.

Gewichtung:
  - Zeit (50%): Schneller = besser
  - Kills (25%): Mehr besiegte Gegner = besser
  - Schaden (25%): Weniger erhaltener Schaden = besser

Ränge: S (Meister), A (Exzellent), B (Gut), C (Durchschnitt), D (Anfänger)
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class ScoreData:
    """Unveränderliche Endwertung nach Spielabschluss."""
    total_time: float          # Sekunden
    total_kills: int
    total_damage_taken: int
    time_score: int            # 0..10000
    kill_score: int            # 0..10000
    damage_score: int          # 0..10000
    final_score: int           # 0..10000 (gewichtet)
    grade: str                 # S / A / B / C / D


class ScoreTracker:
    """Verfolgt Spielstatistiken in Echtzeit."""

    def __init__(self):
        self._start_time: float = 0.0
        self._end_time: float = 0.0
        self._running: bool = False
        self.total_kills: int = 0
        self.total_damage_taken: int = 0

    # ------------------------------------------------------------------
    # Timer
    # ------------------------------------------------------------------
    def start(self) -> None:
        """Startet die Zeitmessung (einmalig beim Spielstart)."""
        if not self._running:
            self._start_time = time.monotonic()
            self._running = True
            self.total_kills = 0
            self.total_damage_taken = 0

    def stop(self) -> None:
        """Stoppt die Zeitmessung (beim Finale)."""
        if self._running:
            self._end_time = time.monotonic()
            self._running = False

    @property
    def elapsed(self) -> float:
        """Verstrichene Zeit in Sekunden."""
        if self._running:
            return time.monotonic() - self._start_time
        return self._end_time - self._start_time

    # ------------------------------------------------------------------
    # Tracking
    # ------------------------------------------------------------------
    def add_kill(self) -> None:
        self.total_kills += 1

    def add_damage(self, amount: int) -> None:
        self.total_damage_taken += amount

    # ------------------------------------------------------------------
    # Berechnung
    # ------------------------------------------------------------------
    def calculate(self) -> ScoreData:
        """Berechnet den Endpunktestand.

        Zeit-Score:   10 000 bei ≤5 min, 0 bei ≥30 min (linear)
        Kill-Score:   100 Punkte pro Kill, gedeckelt bei 10 000
        Damage-Score: 10 000 bei 0 Schaden, 0 bei ≥1000 Schaden
        """
        total_time = max(self.elapsed, 1.0)

        # --- Zeit (wichtigster Faktor) ---
        # 5 Minuten = perfekt, 30 Minuten = 0
        min_time = 5 * 60    # 300s
        max_time = 30 * 60   # 1800s
        if total_time <= min_time:
            time_score = 10000
        elif total_time >= max_time:
            time_score = 0
        else:
            ratio = (total_time - min_time) / (max_time - min_time)
            time_score = int(10000 * (1.0 - ratio))

        # --- Kills ---
        kill_score = min(10000, self.total_kills * 100)

        # --- Schaden (weniger = besser) ---
        max_damage = 1000
        if self.total_damage_taken <= 0:
            damage_score = 10000
        elif self.total_damage_taken >= max_damage:
            damage_score = 0
        else:
            damage_score = int(10000 * (1.0 - self.total_damage_taken / max_damage))

        # --- Gewichteter Gesamtscore ---
        final_score = int(
            time_score * 0.50 +
            kill_score * 0.25 +
            damage_score * 0.25
        )

        # --- Rang ---
        if final_score >= 9000:
            grade = 'S'
        elif final_score >= 7000:
            grade = 'A'
        elif final_score >= 5000:
            grade = 'B'
        elif final_score >= 3000:
            grade = 'C'
        else:
            grade = 'D'

        return ScoreData(
            total_time=total_time,
            total_kills=self.total_kills,
            total_damage_taken=self.total_damage_taken,
            time_score=time_score,
            kill_score=kill_score,
            damage_score=damage_score,
            final_score=final_score,
            grade=grade,
        )

    # ------------------------------------------------------------------
    # Hilfsfunktionen
    # ------------------------------------------------------------------
    @staticmethod
    def format_time(seconds: float) -> str:
        """Formatiert Sekunden als MM:SS."""
        m = int(seconds) // 60
        s = int(seconds) % 60
        return f"{m:02d}:{s:02d}"
