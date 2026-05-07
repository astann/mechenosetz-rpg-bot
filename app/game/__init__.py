"""Игровая логика (подземелья, поход, награды). Импортируйте из `app.game` как раньше."""

from app.game.dungeons import DUNGEONS, Dungeon, dungeon_by_id
from app.game.expedition import (
    create_expedition,
    expedition_travel_flavor,
    finish_rewards,
    hp_max_for_level,
    now_ts,
    process_event,
    xp_for_next_level,
)

__all__ = [
    "DUNGEONS",
    "Dungeon",
    "create_expedition",
    "dungeon_by_id",
    "expedition_travel_flavor",
    "finish_rewards",
    "hp_max_for_level",
    "now_ts",
    "process_event",
    "xp_for_next_level",
]
