"""Правила похода: время, события, награды, «дорожные» реплики. Без Telegram."""

from __future__ import annotations

import random
import time
from typing import Any

from app.game.dungeons import Dungeon, dungeon_by_id
from app.game.monsters import (
    encounter_difficulty,
    encounter_title,
    final_boss_for_dungeon,
    sample_encounter,
)
from app.game.noncombat_events import apply_noncombat_event
from app.game.travel_flavor import expedition_travel_flavor


def xp_for_next_level(level: int) -> int:
    return 50 + level * 30


def hp_max_for_level(level: int) -> int:
    return 100 + max(0, level - 1) * 15


def now_ts() -> float:
    return time.time()


def expedition_event_interval_seconds(dungeon: Dungeon) -> tuple[int, int]:
    sec = dungeon.duration_seconds
    lo = max(2, sec // 15)
    hi = max(lo + 2, sec // 10)
    hi = min(hi, max(lo + 3, sec // 6))
    return lo, hi


def _schedule_next_event_ts(expedition: dict[str, Any], dungeon: Dungeon) -> float:
    if bool(expedition.get("boss_done")) and final_boss_for_dungeon(dungeon.id):
        # После финального босса дополнительных событий быть не должно.
        return float(expedition["end_ts"])
    ev_lo, ev_hi = expedition_event_interval_seconds(dungeon)
    risk = max(-0.6, min(2.5, float(expedition.get("risk", 0.0))))
    # Больше риска -> события происходят чаще; меньше риска -> реже.
    if risk >= 0:
        interval_mult = max(0.5, 1.0 - risk * 0.18)
    else:
        interval_mult = min(1.35, 1.0 + abs(risk) * 0.25)
    ev_lo = max(4, int(ev_lo * interval_mult))
    ev_hi = max(ev_lo + 2, int(ev_hi * interval_mult))
    end = float(expedition["end_ts"])
    t = now_ts()
    remaining = end - t
    if remaining <= ev_lo + 2:
        return end - 1.0
    hi = min(ev_hi, int(remaining) - 5)
    if hi < ev_lo:
        return end - 1.0
    candidate = t + random.randint(ev_lo, hi)
    return min(candidate, end - 1.0)


def create_expedition(dungeon: Dungeon, hp: int) -> dict[str, Any]:
    start = now_ts()
    end = start + dungeon.duration_seconds
    ev_lo, ev_hi = expedition_event_interval_seconds(dungeon)
    first_span = max(ev_lo, min(ev_hi, max(ev_lo + 1, dungeon.duration_seconds // 2)))
    next_ev = start + random.randint(ev_lo, first_span)
    if next_ev >= end:
        next_ev = end - 1.0
    return {
        "dungeon_id": dungeon.id,
        "start_ts": start,
        "end_ts": end,
        "next_event_ts": next_ev,
        "last_flavor_ts": start,
        "hp": hp,
        "risk": 0.0,
        "encounters": 0,
        "boss_done": False,
        "bonus_gold": 0,
        "bonus_xp": 0,
        "loot_boost": 0.0,
        "next_fight_bonus": 0.0,
    }


def process_event(
    *,
    expedition: dict[str, Any],
    level: int,
    defense_flat: int = 0,
    weapon_attack: int = 0,
) -> tuple[dict[str, Any], str]:
    d = dungeon_by_id(str(expedition["dungeon_id"]))
    if not d:
        raise ValueError(f"unknown dungeon {expedition['dungeon_id']!r}")
    text = ""
    risk = float(expedition["risk"])
    hp = int(expedition["hp"])
    df = max(0, int(defense_flat))
    wa = max(0, int(weapon_attack))
    bonus_gold = int(expedition.get("bonus_gold", 0))
    bonus_xp = int(expedition.get("bonus_xp", 0))
    loot_boost = float(expedition.get("loot_boost", 0.0))
    next_fight_bonus = float(expedition.get("next_fight_bonus", 0.0))

    fight_chance = max(0.45, min(0.95, 0.68 + risk * 0.1 + next_fight_bonus))
    boss = final_boss_for_dungeon(d.id)
    boss_due = (
        boss is not None
        and not bool(expedition.get("boss_done"))
        and now_ts() >= float(expedition["end_ts"])
    )
    if boss_due or random.random() < fight_chance:
        next_fight_bonus = 0.0
        if boss_due and boss is not None:
            encounter = [boss]
            expedition["boss_done"] = True
            expedition["next_event_ts"] = float(expedition["end_ts"])
        else:
            encounter_budget = max(0.9, d.danger * 1.3 + max(0.0, risk) * 1.15)
            encounter = sample_encounter(encounter_budget, dungeon_id=d.id)
        monsters_txt = encounter_title(encounter)
        encounter_mult = 0.75 + encounter_difficulty(encounter) / 3.2
        base = 6 + level * 1.4
        risk_damage_mult = 1.0 + max(-0.18, min(0.45, risk * 0.16))
        raw = (
            random.randint(3, 9) + base * random.uniform(0.2, 0.55)
        ) * risk_damage_mult
        raw *= encounter_mult
        dmg = int(max(1, raw - wa - df))
        hp = max(0, hp - dmg)
        expedition["encounters"] = int(expedition["encounters"]) + 1
        if boss_due:
            text = (
                f"👑 Финальный босс: {monsters_txt}. "
                f"Потеряно {dmg} HP.\nТекущее HP: {hp}."
            )
        else:
            text = (
                f"⚔️ Столкновение: {monsters_txt}. "
                f"Потеряно {dmg} HP.\nТекущее HP: {hp}."
            )
    else:
        noncombat = apply_noncombat_event(
            dungeon_id=d.id,
            risk=risk,
            hp=hp,
            hp_cap=hp_max_for_level(level),
            bonus_gold=bonus_gold,
            bonus_xp=bonus_xp,
            loot_boost=loot_boost,
            next_fight_bonus=next_fight_bonus,
        )
        risk = noncombat["risk"]
        hp = noncombat["hp"]
        bonus_gold = noncombat["bonus_gold"]
        bonus_xp = noncombat["bonus_xp"]
        loot_boost = noncombat["loot_boost"]
        next_fight_bonus = noncombat["next_fight_bonus"]
        text = noncombat["text"]

    expedition["hp"] = hp
    expedition["risk"] = risk
    expedition["bonus_gold"] = bonus_gold
    expedition["bonus_xp"] = bonus_xp
    expedition["loot_boost"] = loot_boost
    expedition["next_fight_bonus"] = next_fight_bonus
    expedition["next_event_ts"] = _schedule_next_event_ts(expedition, d)
    return expedition, text


def finish_rewards(
    *, dungeon: Dungeon, level: int, hp: int, hp_max: int, loot_boost: float = 0.0
) -> dict[str, Any]:
    hp_ratio = max(0.1, hp / max(1, hp_max))
    level_mult = 1.0 + level * 0.03

    xp = int(random.randint(dungeon.xp_min, dungeon.xp_max) * hp_ratio)
    gold = int(random.randint(dungeon.gold_min, dungeon.gold_max) * level_mult)
    loot = random.random() < (0.18 + dungeon.danger * 0.08 + max(0.0, loot_boost))
    return {"xp": max(1, xp), "gold": max(1, gold), "loot": loot}
