"""Подземелья: карточки локаций и поиск по id (без Telegram, без таймеров)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Dungeon:
    id: str
    title: str
    duration_seconds: int  # реальное время похода
    danger: float
    xp_min: int
    xp_max: int
    gold_min: int
    gold_max: int


DUNGEONS: tuple[Dungeon, ...] = (
    Dungeon("caves", "Забытые пещеры", 1 * 60, 1.0, 30, 60, 25, 60),
    Dungeon("crypt", "Плачущий склеп", 1 * 60, 2.4, 70, 130, 60, 140),
    Dungeon("citadel", "Черная цитадель", 1 * 60, 5.9, 180, 320, 160, 360),
)


def dungeon_by_id(did: str) -> Dungeon | None:
    for d in DUNGEONS:
        if d.id == did:
            return d
    return None
