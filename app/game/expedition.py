"""Правила похода: время, события, награды, «дорожные» реплики. Без Telegram."""

from __future__ import annotations

import random
import time
from typing import Any

from app.game.dungeons import Dungeon, dungeon_by_id


def xp_for_next_level(level: int) -> int:
    return 50 + level * 30


def hp_max_for_level(level: int) -> int:
    return 100 + max(0, level - 1) * 5


def now_ts() -> float:
    return time.time()


def expedition_event_interval_seconds(dungeon: Dungeon) -> tuple[int, int]:
    sec = dungeon.duration_seconds
    lo = max(6, sec // 8)
    hi = max(lo + 5, (sec * 2) // 10)
    hi = min(hi, max(lo + 8, sec // 3))
    return lo, hi


def _schedule_next_event_ts(expedition: dict[str, Any], dungeon: Dungeon) -> float:
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


_EXPEDITION_TRAVEL_LINES: tuple[str, ...] = (
    "Герой пробирается вперёд по узкому проходу…",
    "Под ногами хрустят камешки; в темноте трудно держать направление.",
    "Свет факела прыгает по мокрым стенам.",
    "Герой замирает, вслушиваясь — впереди что-то капает.",
    "Короткая передышка: герой поправляет ремень и снова в путь.",
    "Проход извивается; кажется, лабиринт нарочно ведёт кругами.",
    "Из-за поворота тянет холодом — герой шагает осторожнее.",
    "На стене видны старые царапины… кто-то уже проходил здесь раньше.",
    "Герой перепрыгивает трещину в полу и продолжает путь.",
    "Тишина давит на уши; только эхо собственных шагов.",
    "Воздух становится тяжелее — близко глубина или древняя магия.",
    "Герой пригибается под низким сводом и выбирается в следующий зал.",
    "Мимо скользит тень — то ли игра света, то ли нечто живое.",
    "Путь уводит вниз по крутым ступеням, в неведомую глубину.",
    "Герой отмечает метку на стене, чтобы не заблудиться при отступлении.",
    "Слышен далёкий гул — ветер в расщелине или зверь?",
    "Под ногой хрустает сухая кость. Герой не задерживается.",
    "Проход расширяется; на миг кажется, что тьма отступила.",
    "Герой переводит дух и сжимает рукоять крепче.",
    "Впереди мерцает отблеск — вода, кристаллы или обман глаз?",
    "Камень под ногой шатается; герой делает шаг в сторону.",
    "Запах плесени и железа — здесь давно не ступала нога живого.",
    "Узкий лаз: приходится протискиваться плечом вперёд.",
    "Герой пересекает ручей по влажным камням, чуть не поскользнувшись.",
    "Свод над головой уходит в темноту — не видно, где потолок.",
)


def expedition_travel_flavor() -> str:
    return random.choice(_EXPEDITION_TRAVEL_LINES)


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

    fight_chance = max(0.45, min(0.92, 0.68 + risk * 0.1))
    if random.random() < fight_chance:
        base = 6 + level * 1.4
        risk_damage_mult = 1.0 + max(-0.18, min(0.45, risk * 0.16))
        raw = (random.randint(3, 9) + base * random.uniform(0.2, 0.55)) * risk_damage_mult
        # danger=1.0 как база; выше — сильнее удар (совпадает с идеей «опасности» локации)
        enemy_power = 1.0 + max(0.0, d.danger - 1.0) * 0.75
        raw *= enemy_power
        dmg = int(max(1, raw - wa - df))
        hp = max(0, hp - dmg)
        expedition["encounters"] = int(expedition["encounters"]) + 1
        bonus = ""
        if wa or df:
            bonus = f" (с учётом экипировки: −{wa} атаки, −{df} брони)"
        text = f"⚔️ Столкновение с врагами. Потеряно {dmg} HP.{bonus}\nТекущее HP: {hp}."
    else:
        if random.random() < 0.5:
            risk = min(2.5, risk + random.uniform(0.08, 0.2))
            text = "🧭 Герой решает углубиться в неизведанный тоннель (риск выше)."
        else:
            risk = max(-0.6, risk - random.uniform(0.06, 0.16))
            text = "🛡 Герой выбирает осторожный путь и обходит опасную зону."

    expedition["hp"] = hp
    expedition["risk"] = risk
    expedition["next_event_ts"] = _schedule_next_event_ts(expedition, d)
    return expedition, text


def finish_rewards(*, dungeon: Dungeon, level: int, hp: int, hp_max: int) -> dict[str, Any]:
    hp_ratio = max(0.1, hp / max(1, hp_max))
    level_mult = 1.0 + level * 0.03

    xp = int(random.randint(dungeon.xp_min, dungeon.xp_max) * hp_ratio)
    gold = int(random.randint(dungeon.gold_min, dungeon.gold_max) * level_mult)
    loot = random.random() < (0.18 + dungeon.danger * 0.08)
    return {"xp": max(1, xp), "gold": max(1, gold), "loot": loot}
