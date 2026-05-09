"""Серия забегов по выбранному подземелью с фиксированным билдом.

Короткий формат:
  python -m sim.run_dungeon_series 5 3 4 2 50
  где: level attack_bonus defense_bonus dungeon_number runs
"""

from __future__ import annotations

import argparse
import json
import random
import statistics
from typing import Any

import app.game.expedition as exp_mod
from app.game import create_expedition, finish_rewards, hp_max_for_level, process_event
from app.game.expedition import scaled_equipment_stats
from app.game.dungeons import DUNGEONS, Dungeon
from app.game.monsters import final_boss_for_dungeon


def _dungeon_by_number(number: int) -> Dungeon:
    if number < 1 or number > len(DUNGEONS):
        raise ValueError(f"dungeon-number must be in 1..{len(DUNGEONS)}")
    return DUNGEONS[number - 1]


def _simulate_one_run(
    *,
    dungeon: Dungeon,
    level: int,
    attack_bonus: int,
    defense_bonus: int,
    seed: int,
) -> dict[str, Any]:
    random.seed(seed)
    sim_now = 0.0
    hp_max = hp_max_for_level(level)
    hp = hp_max

    prev_now = exp_mod.now_ts
    try:
        exp_mod.now_ts = lambda: sim_now  # type: ignore[assignment]
        expedition = create_expedition(dungeon, hp=hp)
    finally:
        exp_mod.now_ts = prev_now  # type: ignore[assignment]

    while True:
        end_ts = float(expedition["end_ts"])
        next_event_ts = float(expedition["next_event_ts"])
        if sim_now >= end_ts:
            break
        sim_now = max(sim_now + 1.0, next_event_ts)
        prev_now = exp_mod.now_ts
        try:
            exp_mod.now_ts = lambda: sim_now  # type: ignore[assignment]
            df_s, wm_s = scaled_equipment_stats(
                max(0, defense_bonus), max(0, attack_bonus)
            )
            expedition, _ = process_event(
                expedition=expedition,
                level=level,
                defense_flat=df_s,
                weapon_attack=wm_s,
            )
        finally:
            exp_mod.now_ts = prev_now  # type: ignore[assignment]

        hp = int(expedition["hp"])
        if hp <= 0:
            return {
                "won": False,
                "hp_left": 0,
                "encounters": int(expedition["encounters"]),
                "xp": 0,
                "gold": 0,
                "duration_sec": int(sim_now),
            }

        if bool(expedition.get("boss_done")) and final_boss_for_dungeon(dungeon.id):
            sim_now = float(expedition["end_ts"])
            break

    hp_left = max(1, int(expedition["hp"]))
    rewards = finish_rewards(
        dungeon=dungeon,
        level=level,
        hp=hp_left,
        hp_max=hp_max,
        loot_boost=float(expedition.get("loot_boost", 0.0)),
    )
    return {
        "won": True,
        "hp_left": hp_left,
        "encounters": int(expedition["encounters"]),
        "xp": int(rewards["xp"]) + int(expedition.get("bonus_xp", 0)),
        "gold": int(rewards["gold"]) + int(expedition.get("bonus_gold", 0)),
        "duration_sec": int(sim_now),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run repeated runs on one dungeon")
    parser.add_argument("level", type=int, help="Hero level")
    parser.add_argument("attack_bonus", type=int, help="Flat attack reduction bonus")
    parser.add_argument("defense_bonus", type=int, help="Flat defense reduction bonus")
    parser.add_argument("dungeon_number", type=int, help="Dungeon number from ordered list")
    parser.add_argument("runs", type=int, help="Number of runs")
    parser.add_argument("--seed", type=int, default=42, help="Base random seed")
    args = parser.parse_args()

    if args.level < 1:
        raise ValueError("level must be >= 1")
    if args.runs < 1:
        raise ValueError("runs must be >= 1")

    dungeon = _dungeon_by_number(args.dungeon_number)

    rows: list[dict[str, Any]] = []
    for i in range(args.runs):
        rows.append(
            _simulate_one_run(
                dungeon=dungeon,
                level=args.level,
                attack_bonus=args.attack_bonus,
                defense_bonus=args.defense_bonus,
                seed=args.seed + i,
            )
        )

    wins = [r for r in rows if bool(r["won"])]
    summary = {
        "dungeon_number": args.dungeon_number,
        "dungeon_id": dungeon.id,
        "dungeon_title": dungeon.title,
        "runs": args.runs,
        "level": args.level,
        "attack_bonus": args.attack_bonus,
        "defense_bonus": args.defense_bonus,
        "win_rate": round(len(wins) / args.runs, 4),
        "avg_duration_sec": int(statistics.mean(int(r["duration_sec"]) for r in rows)),
        "avg_encounters": round(statistics.mean(int(r["encounters"]) for r in rows), 2),
        "avg_hp_left_on_win": round(statistics.mean(int(r["hp_left"]) for r in wins), 2) if wins else 0.0,
        "avg_xp_on_win": round(statistics.mean(int(r["xp"]) for r in wins), 2) if wins else 0.0,
        "avg_gold_on_win": round(statistics.mean(int(r["gold"]) for r in wins), 2) if wins else 0.0,
        "deaths": args.runs - len(wins),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

