"""Небоевые случайные события экспедиции."""

from __future__ import annotations

import random
from typing import TypedDict


class NonCombatState(TypedDict):
    risk: float
    hp: int
    bonus_gold: int
    bonus_xp: int
    loot_boost: float
    next_fight_bonus: float
    text: str


def apply_noncombat_event(
    *,
    dungeon_id: str,
    risk: float,
    hp: int,
    hp_cap: int,
    bonus_gold: int,
    bonus_xp: int,
    loot_boost: float,
    next_fight_bonus: float,
) -> NonCombatState:
    text: str
    roll = random.random()
    if roll < 0.35:
        found = random.randint(10, 40)
        bonus_gold += found
        text = f"💰 Найден тайник: +{found} золота."
    elif roll < 0.60:
        heal = random.randint(4, 12)
        hp = min(hp + heal, hp_cap)
        text = f"🔥 Короткая передышка у костра: +{heal} HP. Текущее HP: {hp}."
    elif roll < 0.80:
        dmg = random.randint(4, 10)
        hp = max(1, hp - dmg)
        text = f"🪤 Ловушка в проходе: -{dmg} HP. Текущее HP: {hp}."
    elif roll < 0.95:
        if random.random() < 0.5:
            risk = min(2.5, risk + random.uniform(0.08, 0.2))
            text = "🧭 Развилка: герой выбирает более глубокий путь."
        else:
            risk = max(-0.6, risk - random.uniform(0.06, 0.16))
            text = "🛡 Развилка: герой обходит опасный участок."
    else:
        next_fight_bonus = 0.22
        text = "👣 Свежие следы врага рядом — следующее столкновение почти неизбежно."

    # Локационно-уникальные эффекты и сообщения.
    local_roll = random.random()
    if dungeon_id == "forest" and local_roll < 0.18:
        add = random.randint(2, 6)
        hp = min(hp + add, hp_cap)
        text += f"\n🌿 Лесная передышка у ручья: +{add} HP."
    elif dungeon_id == "crypt" and local_roll < 0.18:
        loss = random.randint(2, 7)
        hp = max(1, hp - loss)
        text += f"\n🕯 Могильный холод пронизывает кости: -{loss} HP."
    elif dungeon_id == "lair" and local_roll < 0.18:
        heal = random.randint(3, 8)
        hp = min(hp + heal, hp_cap)
        text += f"\n⚫ Во мраке у вас открывается второе дыхание: +{heal} HP."
    elif dungeon_id == "dead_suburb" and local_roll < 0.18:
        found = random.randint(18, 46)
        bonus_gold += found
        text += f"\n🏚 В заброшенном доме найден схрон: +{found} золота."
    elif dungeon_id == "gloom_slums" and local_roll < 0.18:
        risk = min(2.5, risk + random.uniform(0.08, 0.18))
        next_fight_bonus = max(next_fight_bonus, 0.2)
        text += "\n🕳 Трущобы шумят вокруг — засада может начаться в любой миг."
    elif dungeon_id == "abyss_cathedral" and local_roll < 0.18:
        bonus_xp += random.randint(6, 14)
        loot_boost = min(0.35, loot_boost + 0.08)
        text += "\n⛪ Шепот бездны открывает тайные знания: опыт и шанс трофея растут."

    return {
        "risk": risk,
        "hp": hp,
        "bonus_gold": bonus_gold,
        "bonus_xp": bonus_xp,
        "loot_boost": loot_boost,
        "next_fight_bonus": next_fight_bonus,
        "text": text,
    }
