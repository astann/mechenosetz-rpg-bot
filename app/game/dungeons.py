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
    Dungeon("forest", "Темнолесье", 1, 30, 1.0, 55, 90, 6, 13),
    Dungeon("crypt", "Склеп Безымянных", 1, 30, 5.0, 100, 160, 14, 30),
    Dungeon("lair", "Логово Теней", 1, 30, 10, 170, 270, 28, 58),
    # Акт II
    Dungeon("dead_suburb", "Мертвый Пригород", 2, 30, 12, 250, 360, 40, 80),
    Dungeon("gloom_slums", "Сумрачные Трущобы", 2, 30, 16, 330, 470, 59, 114),
    Dungeon("abyss_cathedral", "Собор Бездны", 2, 30, 20, 430, 620, 75, 140),
    # Акт III
    Dungeon("whispering_wasteland", "Шепчущая Пустошь", 3, 30, 24, 450, 650, 100, 180),
    Dungeon("ridge_dead_echo", "Хребет Мертвого Эха", 3, 30, 30, 600, 850, 130, 230),
    Dungeon("black_wall", "Черная Стена", 3, 30, 40, 760, 1080, 175, 295),
)


def dungeon_by_id(did: str) -> Dungeon | None:
    for d in DUNGEONS:
        if d.id == did:
            return d
    return None
