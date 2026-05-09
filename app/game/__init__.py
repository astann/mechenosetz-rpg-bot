"""Игровая логика (подземелья, поход, награды). Импортируйте из `app.game` как раньше."""

from app.game.dungeons import DUNGEONS, Dungeon, dungeon_by_id
from app.game.expedition import (
    EQUIPMENT_ARMOR_COEFF,
    EQUIPMENT_WEAPON_COEFF,
    LEVEL_DAMAGE_COEFF,
    create_expedition,
    finish_rewards,
    hp_max_for_level,
    now_ts,
    process_event,
    scaled_equipment_stats,
    xp_for_next_level,
)
from app.game.travel_flavor import expedition_travel_flavor

__all__ = [
    "DUNGEONS",
    "Dungeon",
    "EQUIPMENT_ARMOR_COEFF",
    "EQUIPMENT_WEAPON_COEFF",
    "LEVEL_DAMAGE_COEFF",
    "create_expedition",
    "dungeon_by_id",
    "expedition_travel_flavor",
    "finish_rewards",
    "hp_max_for_level",
    "now_ts",
    "process_event",
    "scaled_equipment_stats",
    "xp_for_next_level",
]
