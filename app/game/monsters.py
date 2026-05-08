"""Пул монстров и генерация боевых встреч."""

from __future__ import annotations

import random
from collections import OrderedDict
from dataclasses import dataclass


@dataclass(frozen=True)
class Monster:
    id: str
    title: str
    emoji: str
    difficulty: float


MONSTERS: tuple[Monster, ...] = (
    Monster("bone_rat", "Костяная Крыса", "🐀", 0.55),
    Monster("blood_bat", "Кровавый Нетопырь", "🦇", 0.65),
    Monster("bone_guard", "Костяной Страж", "💀", 0.9),
    Monster("ghoul", "Упырь", "🧟", 1.1),
    Monster("shadow_wolf", "Сумрачный Волк", "🐺", 1.35),
    Monster("cultist", "Культист", "🕯️", 1.55),
    Monster("wraith", "Плачущий Призрак", "👻", 2.3),
    Monster("shadow_spawn", "Порождение Тени", "🗿", 3.7),
    Monster("sorcerer", "Колдун", "🔮", 7),
    # Акт II
    Monster("corpse_hound", "Трупная Гончая", "🦴", 3.6),
    Monster("gloom_bandit", "Сумрачный Бандит", "🗡️", 4.1),
    Monster("void_deacon", "Дьякон Пустоты", "🕍", 5.4),
    Monster("fallen_guard", "Павший Ополченец", "🔪", 3.8),
    Monster("slum_scavenger", "Нищий Падальщик", "🪓", 4.0),
    Monster("cathedral_guard", "Соборный Страж", "🛡️", 4.8),
    Monster("cathedral_warden", "Караульный Свода", "⚔️", 5.2),
    # Акт III
    Monster("ashen_revenant", "Пепельный Ревенант", "🔥", 6.0),
    Monster("black_mountain_marauder", "Мародер с Черной Горы", "📯", 6.7),
    Monster("wall_sentinel", "Дозорный Стены", "🛡️", 7.5),
    Monster("abyss_spawn", "Порождение Бездны", "🕳️", 6.2),
    Monster("black_wall_boss", "Черная Стена", "⬛", 8.8),
)

MONSTER_BY_ID: dict[str, Monster] = {m.id: m for m in MONSTERS}

# Пулы монстров по подземельям.
MONSTERS_BY_DUNGEON: dict[str, tuple[str, ...]] = {
    "forest": ("bone_rat", "blood_bat", "shadow_wolf", "ghoul"),
    "crypt": ("bone_guard", "ghoul", "wraith", "cultist"),
    "lair": ("cultist", "wraith", "shadow_spawn"),
    "dead_suburb": ("ghoul", "wraith", "corpse_hound", "cultist", "slum_scavenger"),
    "gloom_slums": (
        "gloom_bandit",
        "fallen_guard",
        "slum_scavenger",
        "corpse_hound",
    ),
    "abyss_cathedral": (
        "cathedral_guard",
        "cathedral_warden",
        "void_deacon",
        "sorcerer",
    ),
    "whispering_wasteland": (
        "ashen_revenant",
        "wraith",
        "black_mountain_marauder",
        "shadow_wolf",
    ),
    "ridge_dead_echo": (
        "black_mountain_marauder",
        "ashen_revenant",
        "wall_sentinel",
        "sorcerer",
    ),
    "black_wall": ("wall_sentinel", "ashen_revenant", "gloom_bandit", "sorcerer"),
}

BOSS_BY_DUNGEON: dict[str, str] = {
    "lair": "sorcerer",
    "abyss_cathedral": "abyss_spawn",
    "black_wall": "black_wall_boss",
}


def _pick_weighted(candidates: list[Monster], target: float) -> Monster:
    weights: list[float] = []
    for m in candidates:
        # Небольшой приоритет тем, кто ближе к целевой сложности.
        delta = abs(m.difficulty - target)
        weights.append(1.0 / (0.45 + delta))
    return random.choices(candidates, weights=weights, k=1)[0]


def sample_encounter(total_difficulty: float, dungeon_id: str | None = None) -> list[Monster]:
    """Вернуть 1 монстра или группу с суммарной сложностью около бюджета."""
    budget = max(0.9, float(total_difficulty))
    pool_ids = MONSTERS_BY_DUNGEON.get(dungeon_id or "")
    if pool_ids:
        pool = [MONSTER_BY_ID[mid] for mid in pool_ids if mid in MONSTER_BY_ID]
    else:
        pool = list(MONSTERS)
    if not pool:
        pool = list(MONSTERS)

    group: list[Monster] = []
    remaining = budget
    max_size = 4
    for _ in range(max_size):
        soft_cap = max(0.9, remaining + 0.6)
        candidates = [m for m in pool if m.difficulty <= soft_cap]
        if not candidates:
            break
        chosen = _pick_weighted(candidates, target=max(0.9, remaining))
        group.append(chosen)
        # Часть сложности «съедается», оставляя шанс на группу из мелочи.
        remaining -= chosen.difficulty * random.uniform(0.65, 0.95)
        if remaining <= 0.25 and len(group) >= 2:
            break

    return group or [pool[0]]


def encounter_difficulty(encounter: list[Monster]) -> float:
    return sum(m.difficulty for m in encounter)


def encounter_title(encounter: list[Monster]) -> str:
    """Формат: '🐀 Крысоед, 💀 Костяк x2'."""
    counts: "OrderedDict[str, tuple[Monster, int]]" = OrderedDict()
    for m in encounter:
        if m.id in counts:
            prev = counts[m.id]
            counts[m.id] = (prev[0], prev[1] + 1)
        else:
            counts[m.id] = (m, 1)
    parts: list[str] = []
    for mon, n in counts.values():
        if n > 1:
            parts.append(f"{mon.emoji} {mon.title} x{n}")
        else:
            parts.append(f"{mon.emoji} {mon.title}")
    return ", ".join(parts)


def final_boss_for_dungeon(dungeon_id: str) -> Monster | None:
    mid = BOSS_BY_DUNGEON.get(dungeon_id)
    if not mid:
        return None
    return MONSTER_BY_ID.get(mid)
