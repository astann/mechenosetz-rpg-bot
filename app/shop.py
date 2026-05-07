from __future__ import annotations

import random
from typing import Any

from app import db
from app.game import now_ts


def today_utc() -> str:
    import time

    return time.strftime("%Y-%m-%d", time.gmtime(now_ts()))


def _pick(rng: random.Random, pool: list[dict[str, Any]], n: int) -> list[dict[str, Any]]:
    return [dict(x) for x in rng.sample(pool, min(n, len(pool)))]


def generate_shop_stock(*, day_key: str) -> list[dict[str, Any]]:
    """9 позиций: 3 оружия, 3 брони, 3 предмета. Стабильно от дня UTC."""
    rng = random.Random(f"mechenosetz_shop_{day_key}")

    weapons_pool = [
        {"kind": "weapon", "name": "Кинжал теней", "price": 45, "attack": 1},
        {"kind": "weapon", "name": "Короткий меч", "price": 70, "attack": 2},
        {"kind": "weapon", "name": "Боевой топор", "price": 95, "attack": 2},
        {"kind": "weapon", "name": "Копьё стража", "price": 110, "attack": 3},
        {"kind": "weapon", "name": "Посох грома", "price": 130, "attack": 3},
        {"kind": "weapon", "name": "Клинок заката", "price": 160, "attack": 4},
    ]
    armor_pool = [
        {"kind": "armor", "name": "Кожаная куртка", "price": 50, "defense": 2},
        {"kind": "armor", "name": "Кольчуга", "price": 85, "defense": 4},
        {"kind": "armor", "name": "Латы наёмника", "price": 120, "defense": 6},
        {"kind": "armor", "name": "Плащ из шкуры", "price": 65, "defense": 3},
        {"kind": "armor", "name": "Латный нагрудник", "price": 140, "defense": 7},
        {"kind": "armor", "name": "Мантия архивара", "price": 100, "defense": 5},
    ]
    item_pool = [
        {"kind": "item", "name": "Мазь целителя", "price": 35, "effect": "heal", "value": 25},
        {"kind": "item", "name": "Сильное зелье", "price": 55, "effect": "heal", "value": 45},
        {"kind": "item", "name": "Сухпаёк", "price": 20, "effect": "heal", "value": 12},
        {"kind": "item", "name": "Оберег удачи", "price": 40, "effect": "heal", "value": 18},
        {"kind": "item", "name": "Эликсир бодрости", "price": 48, "effect": "heal", "value": 30},
        {"kind": "item", "name": "Святая вода", "price": 32, "effect": "heal", "value": 22},
    ]

    w = _pick(rng, weapons_pool, 3)
    a = _pick(rng, armor_pool, 3)
    it = _pick(rng, item_pool, 3)

    slots: list[dict[str, Any]] = []
    idx = 0
    for x in w + a + it:
        row = {**x, "slot": idx}
        idx += 1
        slots.append(row)
    return slots


def equipment_bonuses(equipped: dict[str, Any]) -> tuple[int, int]:
    """(defense_flat, weapon_attack)"""
    defense = 0
    mit = 0
    w = equipped.get("weapon")
    a = equipped.get("armor")
    if isinstance(w, dict):
        mit = int(w["attack"])
    if isinstance(a, dict):
        defense = int(a["defense"])
    return defense, mit


async def ensure_shop_today() -> tuple[str, list[dict[str, Any]]]:
    """Ассортимент на календарный день UTC; при смене дня — новый набор."""
    day_now = today_utc()
    day, items = await db.get_shop_state()
    if day != day_now:
        stock = generate_shop_stock(day_key=day_now)
        await db.set_shop_state(day_now, stock)
        return day_now, stock
    if not items:
        stock = generate_shop_stock(day_key=day_now)
        await db.set_shop_state(day_now, stock)
        return day_now, stock
    return day_now, items


def shop_message_text(
    day: str,
    items: list[dict[str, Any]],
    *,
    gold: int | None = None,
    equipped: dict[str, Any] | None = None,
) -> str:
    lines = [f"🏪 <b>Магазин</b> (витрина на {day} UTC)\n"]
    if gold is not None:
        lines.append(f"💰 <b>Твоё золото:</b> {gold}")
    if equipped is not None:
        w = equipped.get("weapon")
        a = equipped.get("armor")
        if isinstance(w, dict):
            w_txt = f"{w['name']} (+{int(w['attack'])} ат)"
        else:
            w_txt = "нет"
        if isinstance(a, dict):
            a_txt = f"{a['name']} (+{int(a['defense'])} защ)"
        else:
            a_txt = "нет"
        lines.append(f"⚔️ <b>На герое:</b> {w_txt}")
        lines.append(f"🛡 <b>Броня:</b> {a_txt}")
    if gold is not None or equipped is not None:
        lines.append("")
    return "\n".join(lines)
