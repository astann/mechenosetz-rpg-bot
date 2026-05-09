"""Братство Меча: наёмники (3 акта)."""

from __future__ import annotations

import random
import uuid
from collections import Counter
from typing import Any

# Шанс, что конкретный наёмник принимает смертельный удар вместо героя (один спасает за событие).
MERC_SACRIFICE_CHANCE = 0.38

# id, имя, цена, поля эффекта (стакаются при нескольких наймах одного типа)
MERCENARY_OFFERS: tuple[dict[str, Any], ...] = (
    {
        "id": "brotherhood_blade",
        "title": "Клинок",
        "price": 760,
        "attack": 8,
        "defense": 8,
        "hp_bonus": 12,
    },
    {
        "id": "brotherhood_healer",
        "title": "Лекарь",
        "price": 980,
        "attack": 0,
        "defense": 0,
        "heal_after_run": 28,
        "hp_bonus": 18,
    },
    {
        "id": "brotherhood_chronicler",
        "title": "Летописец",
        "price": 1120,
        "attack": 0,
        "defense": 0,
        "xp_bonus_run": 14,
        "hp_bonus": 10,
    },
)


def offer_by_id(oid: str) -> dict[str, Any] | None:
    for o in MERCENARY_OFFERS:
        if str(o["id"]) == oid:
            return dict(o)
    return None


def mercenary_state_from_offer(offer: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {
        "slot": str(uuid.uuid4()),
        "id": str(offer["id"]),
        "title": str(offer["title"]),
        "attack": int(offer["attack"]),
        "defense": int(offer["defense"]),
        "price": int(offer["price"]),
    }
    if "heal_after_run" in offer:
        out["heal_after_run"] = int(offer["heal_after_run"])
    if "xp_bonus_run" in offer:
        out["xp_bonus_run"] = int(offer["xp_bonus_run"])
    if "hp_bonus" in offer:
        out["hp_bonus"] = int(offer["hp_bonus"])
    return out


def mercenary_effects_text(offer: dict[str, Any]) -> str:
    parts: list[str] = []
    a = int(offer.get("attack", 0) or 0)
    d = int(offer.get("defense", 0) or 0)
    if a or d:
        parts.append(f"+{a} ат, +{d} защ")
    heal = int(offer.get("heal_after_run", 0) or 0)
    if heal > 0:
        parts.append(f"лечение после забега +{heal} HP")
    xp_b = int(offer.get("xp_bonus_run", 0) or 0)
    if xp_b > 0:
        parts.append(f"+{xp_b} опыта за успешный поход")
    hp_b = int(offer.get("hp_bonus", 0) or 0)
    if hp_b > 0:
        parts.append(f"+{hp_b} макс. HP")
    return ", ".join(parts)


def aggregate_mercenary_stats(roster: list[dict[str, Any]]) -> dict[str, int]:
    atk = defense = heal = xp_b = hp_b = 0
    for m in roster:
        atk += int(m.get("attack", 0) or 0)
        defense += int(m.get("defense", 0) or 0)
        heal += int(m.get("heal_after_run", 0) or 0)
        xp_b += int(m.get("xp_bonus_run", 0) or 0)
        hp_b += int(m.get("hp_bonus", 0) or 0)
    return {
        "attack": atk,
        "defense": defense,
        "heal_after_run": heal,
        "xp_bonus_run": xp_b,
        "hp_bonus": hp_b,
    }


def sync_expedition_mercenary_snapshot(expedition: dict[str, Any]) -> None:
    roster = expedition.get("mercenary_roster") or []
    agg = aggregate_mercenary_stats(roster)
    expedition["merc_attack"] = agg["attack"]
    expedition["merc_defense"] = agg["defense"]
    expedition["merc_heal_after_run"] = agg["heal_after_run"]
    expedition["merc_xp_bonus"] = agg["xp_bonus_run"]
    expedition["merc_hp_bonus"] = agg["hp_bonus"]


def effective_hp_max(base_hp_max: int, roster: list[dict[str, Any]] | None) -> int:
    """Макс. HP героя = база из уровня + сумма hp_bonus наёмников."""
    bonus = aggregate_mercenary_stats(roster or [])["hp_bonus"]
    return max(1, int(base_hp_max) + bonus)


def effective_hp_max_for_user(u: dict[str, Any]) -> int:
    """В походе — по живым наёмникам в экспедиции; иначе — по отряду в городе."""
    base = int(u["hp_max"])
    exp = u.get("expedition")
    if isinstance(exp, dict):
        r = exp.get("mercenary_roster")
        if isinstance(r, list):
            return effective_hp_max(base, r)
    return effective_hp_max(base, u.get("mercenaries"))
def try_mercenary_sacrifice(roster: list[dict[str, Any]]) -> tuple[bool, str]:
    """Один наёмник может погибнуть вместо героя; HP героя как до этого удара."""
    if not roster:
        return False, ""
    candidates = roster[:]
    random.shuffle(candidates)
    for dead in candidates:
        if random.random() > MERC_SACRIFICE_CHANCE:
            continue
        slot = dead.get("slot")
        if slot:
            sid = str(slot)
            roster[:] = [m for m in roster if str(m.get("slot", "")) != sid]
        else:
            try:
                roster.remove(dead)
            except ValueError:
                continue
        return True, str(dead.get("title", "Соратник"))
    return False, ""


def roster_summary_lines(roster: list[dict[str, Any]]) -> list[str]:
    if not roster:
        return []
    by_id = Counter(str(m.get("id", "?")) for m in roster)
    lines: list[str] = []
    for oid, n in by_id.items():
        offer = offer_by_id(oid)
        label = offer["title"] if offer else oid
        lines.append(f"{label} ×{n}")
    return lines
