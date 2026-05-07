"""Симуляция прогрессии игрока до открытия Черной Стены.

Запуск:
  python -m sim.run_sim --runs 500 --seed 42
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import statistics
from pathlib import Path
from typing import Any

import app.game.expedition as exp_mod
from app.game import (
    create_expedition,
    dungeon_by_id,
    finish_rewards,
    hp_max_for_level,
    process_event,
    xp_for_next_level,
)
from app.game.monsters import final_boss_for_dungeon

DAY_SECONDS = 24 * 3600
ACTIVE_SECONDS_PER_DAY = 16 * 3600

WEAPON_TIERS: tuple[tuple[int, int], ...] = (
    (0, 0),
    (70, 2),
    (110, 3),
    (160, 4),
    (260, 5),
    (420, 6),
)

ARMOR_TIERS: tuple[tuple[int, int], ...] = (
    (0, 0),
    (85, 4),
    (120, 6),
    (140, 7),
    (260, 9),
    (420, 11),
)


def _choose_target_dungeon(state: dict[str, Any]) -> str:
    level = int(state["level"])
    if not state["next_act_unlocked"]:
        if level < 3:
            return "forest"
        if level < 7:
            return "crypt"
        return "lair"
    if not state["third_act_unlocked"]:
        if level < 11:
            return "dead_suburb"
        if level < 16:
            return "gloom_slums"
        return "abyss_cathedral"
    return "black_wall"


def _buy_upgrades(state: dict[str, Any]) -> None:
    # Покупаем только следующий тир, если хватает золота.
    while state["weapon_tier"] + 1 < len(WEAPON_TIERS):
        nxt = state["weapon_tier"] + 1
        price, _ = WEAPON_TIERS[nxt]
        if state["gold"] < price:
            break
        state["gold"] -= price
        state["weapon_tier"] = nxt
    while state["armor_tier"] + 1 < len(ARMOR_TIERS):
        nxt = state["armor_tier"] + 1
        price, _ = ARMOR_TIERS[nxt]
        if state["gold"] < price:
            break
        state["gold"] -= price
        state["armor_tier"] = nxt


def _align_to_active_window(sim_now: float) -> float:
    day_pos = int(sim_now) % DAY_SECONDS
    if day_pos >= ACTIVE_SECONDS_PER_DAY:
        return float((int(sim_now) // DAY_SECONDS + 1) * DAY_SECONDS)
    return sim_now


def _do_fishing(state: dict[str, Any], sim_now: float) -> float:
    # 2 часа на рыбалку, улов 1-2 рыбы.
    sim_now += 2 * 3600
    for _ in range(random.randint(1, 2)):
        state["fish_heals"].append(random.randint(10, 22))
    return sim_now


def _consume_fish_if_needed(state: dict[str, Any], threshold_ratio: float) -> None:
    hp = int(state["hp_current"])
    hp_max = int(state["hp_max"])
    if hp >= int(hp_max * threshold_ratio):
        return
    heals = list(state["fish_heals"])
    if not heals:
        return
    heals.sort(reverse=True)
    while heals and hp < int(hp_max * threshold_ratio):
        hp = min(hp_max, hp + heals.pop(0))
        state["fish_used"] += 1
    state["fish_heals"] = heals
    state["hp_current"] = hp


def _consume_fish_to_full(state: dict[str, Any]) -> None:
    hp = int(state["hp_current"])
    hp_max = int(state["hp_max"])
    if hp >= hp_max:
        return
    heals = list(state["fish_heals"])
    if not heals:
        return
    heals.sort(reverse=True)
    while heals and hp < hp_max:
        hp = min(hp_max, hp + heals.pop(0))
        state["fish_used"] += 1
    state["fish_heals"] = heals
    state["hp_current"] = hp


def _consume_fish_to_threshold(state: dict[str, Any], threshold_ratio: float) -> None:
    hp = int(state["hp_current"])
    hp_max = int(state["hp_max"])
    target = int(hp_max * threshold_ratio)
    if hp >= target:
        return
    heals = list(state["fish_heals"])
    if not heals:
        return
    heals.sort(reverse=True)
    while heals and hp < target:
        hp = min(hp_max, hp + heals.pop(0))
        state["fish_used"] += 1
    state["fish_heals"] = heals
    state["hp_current"] = hp


def _run_expedition(state: dict[str, Any], dungeon_id: str, sim_now: float) -> tuple[dict[str, Any], float]:
    d = dungeon_by_id(dungeon_id)
    if not d:
        raise ValueError(f"Unknown dungeon {dungeon_id!r}")

    # Подменяем now_ts, чтобы игровая логика жила в виртуальном времени.
    prev_now = exp_mod.now_ts
    try:
        exp_mod.now_ts = lambda: sim_now  # type: ignore[assignment]
        expedition = create_expedition(d, hp=int(state["hp_current"]))
    finally:
        exp_mod.now_ts = prev_now  # type: ignore[assignment]

    while True:
        end_ts = float(expedition["end_ts"])
        next_event_ts = float(expedition["next_event_ts"])
        if sim_now >= end_ts:
            break
        # Внутри подземелья лечимся рыбой только при заметной просадке HP.
        _consume_fish_to_threshold(state, 0.60)
        expedition["hp"] = int(state["hp_current"])
        # Гарантируем ход времени минимум на 1 сек, чтобы не застревать на одном timestamp.
        sim_now = max(sim_now + 1.0, next_event_ts)
        prev_now = exp_mod.now_ts
        try:
            exp_mod.now_ts = lambda: sim_now  # type: ignore[assignment]
            expedition, _ = process_event(
                expedition=expedition,
                level=int(state["level"]),
                defense_flat=int(ARMOR_TIERS[int(state["armor_tier"])][1]),
                weapon_attack=int(WEAPON_TIERS[int(state["weapon_tier"])][1]),
            )
        finally:
            exp_mod.now_ts = prev_now  # type: ignore[assignment]

        hp = int(expedition["hp"])
        state["hp_current"] = max(1, hp)
        if hp <= 0:
            state["deaths"] += 1
            state["hp_current"] = 1
            return state, sim_now

        # После финального босса в этом данже больше событий не ждём.
        if bool(expedition.get("boss_done")) and final_boss_for_dungeon(d.id):
            sim_now = float(expedition["end_ts"])
            break

    hp_left = max(1, int(expedition["hp"]))
    bonus_gold = int(expedition.get("bonus_gold", 0))
    bonus_xp = int(expedition.get("bonus_xp", 0))
    loot_boost = float(expedition.get("loot_boost", 0.0))
    rewards = finish_rewards(
        dungeon=d,
        level=int(state["level"]),
        hp=hp_left,
        hp_max=int(state["hp_max"]),
        loot_boost=loot_boost,
    )
    xp_gain = int(rewards["xp"]) + bonus_xp
    gold_gain = int(rewards["gold"]) + bonus_gold
    xp = int(state["xp"]) + xp_gain
    level = int(state["level"])
    while xp >= xp_for_next_level(level):
        xp -= xp_for_next_level(level)
        level += 1
    hp_max_new = hp_max_for_level(level)
    state["level"] = level
    state["xp"] = xp
    state["gold"] = int(state["gold"]) + gold_gain
    state["hp_max"] = hp_max_new
    state["hp_current"] = min(hp_max_new, hp_left)
    _buy_upgrades(state)

    # Разблокировка актов как в воркере.
    if bool(expedition.get("boss_done")) and hp_left > 0:
        if d.id == "lair":
            state["next_act_unlocked"] = True
        elif d.id == "abyss_cathedral":
            state["third_act_unlocked"] = True
        elif d.id == "black_wall":
            state["black_wall_win_at"] = sim_now
            state["completed"] = True

    return state, sim_now


def _simulate_one(seed: int) -> dict[str, Any]:
    random.seed(seed)
    sim_now = 0.0
    state: dict[str, Any] = {
        "level": 1,
        "xp": 0,
        "gold": 0,
        "hp_max": 100,
        "hp_current": 100,
        "next_act_unlocked": False,
        "third_act_unlocked": False,
        "deaths": 0,
        "rests": 0,
        "runs": 0,
        "act1_unlocked_at": 0.0,
        "act2_unlocked_at": None,
        "act3_unlocked_at": None,
        "consecutive_deaths": 0,
        "successes": 0,
        "completed": False,
        "black_wall_win_at": None,
        "weapon_tier": 0,
        "armor_tier": 0,
        "fish_heals": [],
        "fish_used": 0,
        "fishing_trips": 0,
    }

    while state["runs"] < 2000:
        sim_now = _align_to_active_window(sim_now)
        if state["completed"]:
            break

        # Консервативная политика выживания.
        rest_threshold = 0.92 if state["third_act_unlocked"] else 0.75
        _consume_fish_if_needed(state, rest_threshold)
        # Если рыбы нет и HP низкое, сначала пробуем рыбалку.
        fish_threshold = 0.88 if state["third_act_unlocked"] else 0.68
        if (
            state["hp_current"] < int(state["hp_max"] * fish_threshold)
            and not state["fish_heals"]
        ):
            state["fishing_trips"] += 1
            sim_now = _do_fishing(state, sim_now)
            _consume_fish_if_needed(state, rest_threshold)
        # Если есть рыба, не идем в отдых — лечимся ей до капа.
        if state["fish_heals"]:
            _consume_fish_to_full(state)
        if state["hp_current"] < int(state["hp_max"] * rest_threshold):
            state["rests"] += 1
            sim_now += 6 * 3600
            state["hp_current"] = state["hp_max"]

        dungeon_id = _choose_target_dungeon(state)
        if state["consecutive_deaths"] >= 3:
            # После серии смертей делаем шаг назад, чтобы набрать уровни.
            if not state["next_act_unlocked"]:
                dungeon_id = "crypt" if state["level"] >= 3 else "forest"
            elif not state["third_act_unlocked"] or state["level"] < 18:
                dungeon_id = "gloom_slums" if state["level"] >= 11 else "dead_suburb"
            else:
                dungeon_id = "ridge_dead_echo"

        deaths_before = int(state["deaths"])
        state["runs"] += 1
        state, sim_now = _run_expedition(state, dungeon_id, sim_now)
        if int(state["deaths"]) > deaths_before:
            state["consecutive_deaths"] += 1
        else:
            state["consecutive_deaths"] = 0
            state["successes"] += 1

        if state["next_act_unlocked"] and state["act2_unlocked_at"] is None:
            state["act2_unlocked_at"] = sim_now
        if state["third_act_unlocked"] and state["act3_unlocked_at"] is None:
            state["act3_unlocked_at"] = sim_now

    return {
        "time_to_black_wall_sec": int(sim_now),
        "time_to_first_black_wall_win_sec": int(state["black_wall_win_at"] or sim_now),
        "act1_time_sec": int(state["act2_unlocked_at"] or sim_now),
        "act2_time_sec": int((state["act3_unlocked_at"] or sim_now) - (state["act2_unlocked_at"] or 0)),
        "deaths": int(state["deaths"]),
        "rests": int(state["rests"]),
        "runs": int(state["runs"]),
        "final_level": int(state["level"]),
        "completed": bool(state["completed"]),
        "weapon_tier": int(state["weapon_tier"]),
        "armor_tier": int(state["armor_tier"]),
        "fishing_trips": int(state["fishing_trips"]),
        "fish_used": int(state["fish_used"]),
        "fish_left": len(state["fish_heals"]),
    }


def _percentile(values: list[int], q: float) -> int:
    if not values:
        return 0
    vs = sorted(values)
    idx = int((len(vs) - 1) * q)
    return int(vs[idx])


def _format_duration(seconds: int) -> str:
    d, rem = divmod(seconds, DAY_SECONDS)
    h, rem = divmod(rem, 3600)
    m, s = divmod(rem, 60)
    if d > 0:
        return f"{d}d {h:02d}:{m:02d}:{s:02d}"
    return f"{h:02d}:{m:02d}:{s:02d}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulate progress to Black Wall unlock")
    parser.add_argument("--runs", type=int, default=300, help="Number of simulated players")
    parser.add_argument("--seed", type=int, default=42, help="Base random seed")
    parser.add_argument("--out-dir", type=str, default="sim/results", help="Output directory")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    for i in range(args.runs):
        rows.append(_simulate_one(args.seed + i))

    csv_path = out_dir / "runs.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    completed_rows = [r for r in rows if bool(r["completed"])]
    base_rows = completed_rows if completed_rows else rows
    t = [int(r["time_to_black_wall_sec"]) for r in base_rows]
    bw_win = [int(r["time_to_first_black_wall_win_sec"]) for r in base_rows]
    a1 = [int(r["act1_time_sec"]) for r in base_rows]
    a2 = [int(r["act2_time_sec"]) for r in base_rows]
    summary = {
        "runs": args.runs,
        "completed_runs": len(completed_rows),
        "time_to_black_wall_sec": {
            "mean": int(statistics.mean(t)),
            "p50": _percentile(t, 0.50),
            "p75": _percentile(t, 0.75),
            "p90": _percentile(t, 0.90),
        },
        "time_to_first_black_wall_win_sec": {
            "mean": int(statistics.mean(bw_win)),
            "p50": _percentile(bw_win, 0.50),
            "p75": _percentile(bw_win, 0.75),
            "p90": _percentile(bw_win, 0.90),
        },
        "act1_time_sec": {
            "mean": int(statistics.mean(a1)),
            "p50": _percentile(a1, 0.50),
            "p75": _percentile(a1, 0.75),
            "p90": _percentile(a1, 0.90),
        },
        "act2_time_sec": {
            "mean": int(statistics.mean(a2)),
            "p50": _percentile(a2, 0.50),
            "p75": _percentile(a2, 0.75),
            "p90": _percentile(a2, 0.90),
        },
        "deaths_mean": round(statistics.mean(int(r["deaths"]) for r in rows), 2),
        "rests_mean": round(statistics.mean(int(r["rests"]) for r in rows), 2),
        "fishing_trips_mean": round(statistics.mean(int(r["fishing_trips"]) for r in rows), 2),
        "fish_used_mean": round(statistics.mean(int(r["fish_used"]) for r in rows), 2),
        "runs_mean": round(statistics.mean(int(r["runs"]) for r in rows), 2),
    }
    summary["time_to_black_wall_human"] = {
        k: _format_duration(int(v))
        for k, v in summary["time_to_black_wall_sec"].items()
    }
    summary["time_to_first_black_wall_win_human"] = {
        k: _format_duration(int(v))
        for k, v in summary["time_to_first_black_wall_win_sec"].items()
    }
    summary["act1_time_human"] = {
        k: _format_duration(int(v))
        for k, v in summary["act1_time_sec"].items()
    }
    summary["act2_time_human"] = {
        k: _format_duration(int(v))
        for k, v in summary["act2_time_sec"].items()
    }

    json_path = out_dir / "summary.json"
    json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Saved: {csv_path}")
    print(f"Saved: {json_path}")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
