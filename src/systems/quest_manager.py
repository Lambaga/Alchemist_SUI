# -*- coding: utf-8 -*-
"""
Quest Manager – verwaltet aktive Missionen / Aufträge.

Jede Quest hat:
  - id            : eindeutiger Schlüssel (z.B. 'elara_bruecke')
  - title         : Kurztext, der als Überschrift im HUD erscheint
  - objectives    : Liste von {key, label, done}
  - completed     : Gesamtstatus
  - npc_name      : Name des Auftraggebers
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class QuestObjective:
    key: str           # z.B. 'holzstab'
    label: str         # z.B. 'Holzstab finden'
    done: bool = False


@dataclass
class Quest:
    id: str
    title: str
    npc_name: str
    objectives: List[QuestObjective] = field(default_factory=list)
    completed: bool = False
    visible: bool = True   # im HUD sichtbar
    ready_to_turn_in: bool = False  # Alle Ziele erledigt, Spieler muss zum NPC zurück

    # ------------------------------------------------------------------
    def mark_objective(self, key: str) -> bool:
        """Markiert ein Ziel als erledigt. Gibt True zurück wenn sich etwas geändert hat."""
        for obj in self.objectives:
            if obj.key == key and not obj.done:
                obj.done = True
                # Prüfe ob alle Ziele erledigt → noch NICHT completed,
                # sondern ready_to_turn_in (Spieler muss zum NPC zurück)
                if all(o.done for o in self.objectives):
                    self.ready_to_turn_in = True
                return True
        return False

    @property
    def progress_text(self) -> str:
        done = sum(1 for o in self.objectives if o.done)
        return f"{done}/{len(self.objectives)}"


class QuestManager:
    """Zentrale Verwaltung aller aktiven Quests."""

    def __init__(self):
        self._quests: Dict[str, Quest] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def add_quest(self, quest: Quest) -> None:
        """Fügt eine Quest hinzu (ersetzt ggf. eine bestehende gleicher ID)."""
        self._quests[quest.id] = quest

    def get_quest(self, quest_id: str) -> Optional[Quest]:
        return self._quests.get(quest_id)

    def has_quest(self, quest_id: str) -> bool:
        return quest_id in self._quests

    def remove_quest(self, quest_id: str) -> None:
        self._quests.pop(quest_id, None)

    def get_active_quests(self) -> List[Quest]:
        """Gibt alle sichtbaren, noch nicht abgeschlossenen Quests zurück
        (inkl. solcher die bereit zur Abgabe sind)."""
        return [q for q in self._quests.values() if q.visible and not q.completed]

    def get_all_quests(self) -> List[Quest]:
        return list(self._quests.values())

    def mark_item_collected(self, item_key: str) -> None:
        """Wird aufgerufen wenn ein Gegenstand eingesammelt wird –
        aktualisiert alle Quests, die diesen Gegenstand als Ziel haben."""
        for quest in self._quests.values():
            if not quest.completed:
                quest.mark_objective(item_key)

    def complete_quest(self, quest_id: str) -> None:
        quest = self._quests.get(quest_id)
        if quest:
            quest.completed = True

    def clear(self) -> None:
        self._quests.clear()
