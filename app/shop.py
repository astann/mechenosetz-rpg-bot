from __future__ import annotations

import random
from typing import Any

from app import db
from app.game import now_ts
from app.game.shop_catalog import ARMOR_BY_ACT, ITEMS_BY_ACT, WEAPONS_BY_ACT


def today_utc() -> str:
    import time

    return time.strftime("%Y-%m-%d", time.gmtime(now_ts()))


def _pick(rng: random.Random, pool: list[dict[str, Any]], n: int) -> list[dict[str, Any]]:
    return [dict(x) for x in rng.sample(pool, min(n, len(pool)))]


def generate_shop_stock(*, day_key: str) -> list[dict[str, Any]]:
    """18 позиций: по 2 оружия/брони/предмета на каждый акт."""
    rng = random.Random(f"mechenosetz_shop_{day_key}")

    slots: list[dict[str, Any]] = []
    idx = 0
    for act in (1, 2, 3):
        for x in _pick(rng, WEAPONS_BY_ACT[act], 2):
            slots.append({**x, "act": act, "slot": idx})
            idx += 1
        for x in _pick(rng, ARMOR_BY_ACT[act], 2):
            slots.append({**x, "act": act, "slot": idx})
            idx += 1
        for x in _pick(rng, ITEMS_BY_ACT[act], 2):
            slots.append({**x, "act": act, "slot": idx})
            idx += 1
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


def effective_act_for_shop(u: dict[str, Any]) -> int:
    selected = int(u.get("selected_act", 1) or 1)
    max_open = (
        4
        if bool(u.get("fourth_act_unlocked"))
        else 3
        if bool(u.get("third_act_unlocked"))
        else 2
        if bool(u.get("next_act_unlocked"))
        else 1
    )
    if selected < 1:
        selected = 1
    return min(selected, max_open)


def filter_shop_items_for_act(items: list[dict[str, Any]], act: int) -> list[dict[str, Any]]:
    return [x for x in items if int(x.get("act", 1)) == int(act)]


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
