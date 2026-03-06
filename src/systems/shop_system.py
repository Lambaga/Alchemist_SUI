# -*- coding: utf-8 -*-
"""
Shop System – Upgrade-Definitionen, Preise und Kauf-Logik.

Upgrades werden dauerhaft auf den Spieler angewendet und bleiben
über Map-Wechsel hinweg erhalten.  Jedes Upgrade kann mehrere Stufen
haben (Tier 1 → Tier 2 → …), wobei der Preis pro Stufe steigt.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Upgrade-Definitionen
# ---------------------------------------------------------------------------

@dataclass
class UpgradeTier:
    """Eine einzelne Stufe eines Upgrades."""
    cost: int
    label: str            # z.B. "+20 Max-HP"
    stat_key: str         # Welcher Stat wird verändert (z.B. 'max_health')
    stat_delta: float     # Um wie viel (absolut oder Faktor, je nach apply_mode)
    apply_mode: str = "add"  # "add" | "multiply"


@dataclass
class UpgradeDefinition:
    """Komplettes Upgrade mit Name, Icon-Hinweis und Stufen-Kette."""
    id: str
    name: str
    description: str
    icon_char: str        # Emoji für die UI
    tiers: List[UpgradeTier] = field(default_factory=list)


# Alle verfügbaren Upgrades
SHOP_UPGRADES: List[UpgradeDefinition] = [
    UpgradeDefinition(
        id="hp_boost",
        name="Lebenskraft",
        description="Erhöht dein maximales Leben",
        icon_char="❤️",
        tiers=[
            UpgradeTier(cost=10, label="+20 Max-HP",  stat_key="max_health",  stat_delta=20),
            UpgradeTier(cost=25, label="+30 Max-HP",  stat_key="max_health",  stat_delta=30),
            UpgradeTier(cost=50, label="+50 Max-HP",  stat_key="max_health",  stat_delta=50),
        ],
    ),
    UpgradeDefinition(
        id="mana_boost",
        name="Mana-Reservoir",
        description="Erhöht dein maximales Mana",
        icon_char="🔮",
        tiers=[
            UpgradeTier(cost=10, label="+20 Max-Mana", stat_key="max_mana",   stat_delta=20),
            UpgradeTier(cost=25, label="+30 Max-Mana", stat_key="max_mana",   stat_delta=30),
            UpgradeTier(cost=50, label="+50 Max-Mana", stat_key="max_mana",   stat_delta=50),
        ],
    ),
    UpgradeDefinition(
        id="mana_regen",
        name="Mana-Fluss",
        description="Erhöht deine Mana-Regeneration",
        icon_char="✨",
        tiers=[
            UpgradeTier(cost=15, label="+1 Mana/s",   stat_key="mana_regen_rate", stat_delta=1),
            UpgradeTier(cost=30, label="+2 Mana/s",   stat_key="mana_regen_rate", stat_delta=2),
            UpgradeTier(cost=60, label="+3 Mana/s",   stat_key="mana_regen_rate", stat_delta=3),
        ],
    ),
    UpgradeDefinition(
        id="damage_boost",
        name="Schlagkraft",
        description="Erhöht deinen Basis-Schaden",
        icon_char="⚔️",
        tiers=[
            UpgradeTier(cost=15, label="+5 Schaden",   stat_key="base_attack_damage", stat_delta=5),
            UpgradeTier(cost=35, label="+10 Schaden",  stat_key="base_attack_damage", stat_delta=10),
            UpgradeTier(cost=70, label="+15 Schaden",  stat_key="base_attack_damage", stat_delta=15),
        ],
    ),
    UpgradeDefinition(
        id="speed_boost",
        name="Schnelligkeit",
        description="Erhöht deine Bewegungsgeschwindigkeit",
        icon_char="💨",
        tiers=[
            UpgradeTier(cost=12, label="+1 Speed",     stat_key="speed", stat_delta=1),
            UpgradeTier(cost=30, label="+1 Speed",     stat_key="speed", stat_delta=1),
            UpgradeTier(cost=55, label="+2 Speed",     stat_key="speed", stat_delta=2),
        ],
    ),
    UpgradeDefinition(
        id="armor_boost",
        name="Rüstung",
        description="Reduziert erlittenen Schaden",
        icon_char="🛡️",
        tiers=[
            UpgradeTier(cost=20, label="−10% Schaden", stat_key="damage_reduction", stat_delta=0.10),
            UpgradeTier(cost=45, label="−15% Schaden", stat_key="damage_reduction", stat_delta=0.15),
            UpgradeTier(cost=80, label="−20% Schaden", stat_key="damage_reduction", stat_delta=0.20),
        ],
    ),
]


# ---------------------------------------------------------------------------
# Shop Manager
# ---------------------------------------------------------------------------

class ShopManager:
    """Verwaltet den Kauf-Zustand aller Upgrades."""

    def __init__(self):
        # upgrade_id → aktuelle Stufe (0 = noch nicht gekauft, 1 = Tier 1 gekauft, …)
        self.purchased_tiers: Dict[str, int] = {u.id: 0 for u in SHOP_UPGRADES}

    # --- Abfragen --------------------------------------------------------
    def get_upgrade_defs(self) -> List[UpgradeDefinition]:
        return SHOP_UPGRADES

    def get_current_tier(self, upgrade_id: str) -> int:
        return self.purchased_tiers.get(upgrade_id, 0)

    def get_next_tier(self, upgrade_id: str) -> Optional[UpgradeTier]:
        """Gibt die nächste verfügbare Stufe zurück (oder None wenn max)."""
        defn = self._find_def(upgrade_id)
        if not defn:
            return None
        idx = self.get_current_tier(upgrade_id)
        if idx >= len(defn.tiers):
            return None
        return defn.tiers[idx]

    def is_maxed(self, upgrade_id: str) -> bool:
        defn = self._find_def(upgrade_id)
        if not defn:
            return True
        return self.get_current_tier(upgrade_id) >= len(defn.tiers)

    # --- Kaufen -----------------------------------------------------------
    def try_purchase(self, upgrade_id: str, player) -> Tuple[bool, str]:
        """Versucht ein Upgrade zu kaufen.

        Returns:
            (success, message)
        """
        defn = self._find_def(upgrade_id)
        if not defn:
            return False, "Upgrade nicht gefunden."

        tier = self.get_next_tier(upgrade_id)
        if tier is None:
            return False, "Bereits auf Maximum!"

        if player.coins < tier.cost:
            return False, f"Nicht genug Münzen! ({player.coins}/{tier.cost})"

        # Kauf durchführen
        player.coins -= tier.cost
        self._apply_upgrade(tier, player)
        self.purchased_tiers[upgrade_id] = self.get_current_tier(upgrade_id) + 1

        print(f"🛒 Upgrade gekauft: {defn.name} Stufe {self.purchased_tiers[upgrade_id]} "
              f"({tier.label}) für {tier.cost} Münzen")
        return True, f"{defn.name}: {tier.label}"

    # --- Intern -----------------------------------------------------------
    def _find_def(self, upgrade_id: str) -> Optional[UpgradeDefinition]:
        for u in SHOP_UPGRADES:
            if u.id == upgrade_id:
                return u
        return None

    @staticmethod
    def _apply_upgrade(tier: UpgradeTier, player) -> None:
        """Wendet eine Upgrade-Stufe auf den Spieler an."""
        key = tier.stat_key

        if key == "damage_reduction":
            # Speziell: damage_reduction ist ein Gesamt-Prozentsatz (kumulativ)
            current = getattr(player, 'damage_reduction', 0.0)
            # Kumulativ: 1 - (1-alt)*(1-neu) für abnehmende Erträge
            new_val = 1.0 - (1.0 - current) * (1.0 - tier.stat_delta)
            player.damage_reduction = new_val
        elif tier.apply_mode == "add":
            current = getattr(player, key, 0)
            setattr(player, key, current + int(tier.stat_delta))
            # Synchronisiere abhängige Werte
            if key == "max_health":
                player.base_max_health = player.max_health
                player.current_health = min(player.current_health + int(tier.stat_delta), player.max_health)
            elif key == "max_mana":
                player.current_mana = min(player.current_mana + int(tier.stat_delta), player.max_mana)
            elif key == "base_attack_damage":
                # Recalc attack_damage mit Level-Multiplikator
                mult = getattr(player, 'get_damage_multiplier', lambda: 1.0)()
                player.attack_damage = int(player.base_attack_damage * mult)
            elif key == "speed":
                player.base_speed = player.speed
        elif tier.apply_mode == "multiply":
            current = getattr(player, key, 1)
            setattr(player, key, int(current * tier.stat_delta))

    def reset(self) -> None:
        """Setzt alle Käufe zurück (z.B. bei neuem Spiel)."""
        self.purchased_tiers = {u.id: 0 for u in SHOP_UPGRADES}
