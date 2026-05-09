"""Логика благословений Разрушенной Часовни."""

from __future__ import annotations

from typing import Any

CHAPEL_STRENGTH_BONUS = 4
CHAPEL_DEFENSE_BONUS = 4
CHAPEL_LOOT_BOOST = 0.10

CHAPEL_COST_STRENGTH = 480
CHAPEL_COST_HEAL = 320
CHAPEL_COST_DEFENSE = 520
CHAPEL_COST_LOOT = 560


def chapel_state() -> dict[str, Any]:
    return {}


def blessing_active(chapel: dict[str, Any] | None, key: str) -> bool:
    if not chapel:
        return False
    return bool(chapel.get(key))


def active_bonuses(chapel: dict[str, Any] | None) -> tuple[int, int, float]:
    """(bonus_attack, bonus_defense, loot_chance_boost) — активные благословения часовни."""
    if not chapel:
        return 0, 0, 0.0
    atk = CHAPEL_STRENGTH_BONUS if blessing_active(chapel, "strength") else 0
    defense = CHAPEL_DEFENSE_BONUS if blessing_active(chapel, "defense") else 0
    loot = CHAPEL_LOOT_BOOST if blessing_active(chapel, "loot") else 0.0
    return atk, defense, loot

