"""Подземелья: карточки локаций и поиск по id (без Telegram, без таймеров)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Dungeon:
    id: str
    title: str
    act: int
    duration_seconds: int  # реальное время похода
    danger: float
    xp_min: int
    xp_max: int
    gold_min: int
    gold_max: int


DUNGEONS: tuple[Dungeon, ...] = (
    # Акт I
    Dungeon("forest", "Темнолесье", 1, 1 * 60, 1.0, 30, 60, 25, 60),
    Dungeon("crypt", "Склеп Безымянных", 1, 1 * 60, 2.4, 70, 130, 60, 140),
    Dungeon("lair", "Логово Теней", 1, 1 * 60, 5.9, 180, 320, 160, 360),
    # Акт II
    Dungeon("dead_suburb", "Мертвый Пригород", 2, 1 * 60, 6.8, 260, 420, 220, 460),
    Dungeon("gloom_slums", "Сумрачные Трущобы", 2, 1 * 60, 8.1, 360, 560, 320, 620),
    Dungeon("abyss_cathedral", "Собор Бездны", 2, 1 * 60, 9.6, 520, 820, 470, 900),
    # Акт III
    Dungeon("whispering_wasteland", "Шепчущая Пустошь", 3, 1 * 60, 10.8, 760, 1120, 700, 1300),
    Dungeon("ridge_dead_echo", "Хребет Мертвого Эха", 3, 1 * 60, 12.2, 980, 1420, 900, 1660),
    Dungeon("black_wall", "Черная Стена", 3, 1 * 60, 14.0, 1300, 1900, 1200, 2300),
)


def dungeon_by_id(did: str) -> Dungeon | None:
    for d in DUNGEONS:
        if d.id == did:
            return d
    return None
