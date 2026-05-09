"""Инвентарь и использование расходников."""

from __future__ import annotations

from html import escape

from aiogram import F, Router
from aiogram.types import CallbackQuery

from app import db
from app.game.mercenary_order import effective_hp_max_for_user
from app.bot.keyboards import kb_inventory
from app.bot.texts import inventory_text

router = Router()


async def open_inventory_screen(cq: CallbackQuery, *, inv_back: str) -> None:
    u = await db.ensure_user(cq.from_user.id, cq.from_user.username)
    inv = list(u.get("inventory") or [])
    eq = dict(u.get("equipped") or {})
    if cq.message:
        await cq.message.edit_text(
            inventory_text(inv, eq),
            reply_markup=kb_inventory(inv, inv_back=inv_back),
        )
    await cq.answer()


@router.callback_query(F.data == "nav:inv")
async def inventory_from_main(cq: CallbackQuery) -> None:
    await open_inventory_screen(cq, inv_back="main")


@router.callback_query(F.data.startswith("inv:u:"))
async def inv_use(cq: CallbackQuery) -> None:
    u = await db.ensure_user(cq.from_user.id, cq.from_user.username)
    parts = cq.data.split(":")
    inv_back = "shop"
    try:
        if len(parts) >= 4 and parts[0] == "inv" and parts[1] == "u":
            idx = int(parts[2])
            inv_back = parts[3] if parts[3] in ("shop", "main") else "shop"
        elif len(parts) == 3 and parts[0] == "inv" and parts[1] == "u":
            idx = int(parts[2])
        else:
            raise ValueError
    except (IndexError, ValueError):
        await cq.answer("Неверный индекс.", show_alert=True)
        return
    inv = list(u.get("inventory") or [])
    if idx < 0 or idx >= len(inv):
        await cq.answer("Предмета нет.", show_alert=True)
        return
    it = inv[idx]
    if it.get("kind") != "item" or it.get("effect") != "heal":
        await cq.answer("Это нельзя использовать так.", show_alert=True)
        return
    heal = int(it.get("value", 0))
    hp_cap = effective_hp_max_for_user(u)
    hp = min(hp_cap, int(u["hp_current"]) + heal)
    inv.pop(idx)
    exp = u.get("expedition")
    if isinstance(exp, dict):
        exp = dict(exp)
        exp["hp"] = min(hp_cap, int(exp["hp"]) + heal)
        await db.update_user(
            u["user_id"], hp_current=hp, inventory=inv, expedition=exp
        )
    else:
        await db.update_user(u["user_id"], hp_current=hp, inventory=inv)
    nu = await db.get_user(u["user_id"])
    if cq.message and nu:
        inv2 = list(nu.get("inventory") or [])
        eq2 = dict(nu.get("equipped") or {})
        item_name = escape(str(it.get("name", "Расходник")))
        feedback = (
            f"🧪 Использовано: <b>{item_name}</b>.\n"
            f"+{heal} HP — сейчас {hp} / {hp_cap}.\n\n"
        )
        await cq.message.edit_text(
            feedback + inventory_text(inv2, eq2),
            reply_markup=kb_inventory(inv2, inv_back=inv_back),
            parse_mode="HTML",
        )
    await cq.answer()


@router.callback_query(F.data.startswith("inv:e:"))
async def inv_equip(cq: CallbackQuery) -> None:
    u = await db.ensure_user(cq.from_user.id, cq.from_user.username)
    parts = cq.data.split(":")
    inv_back = "shop"
    try:
        if len(parts) >= 4 and parts[0] == "inv" and parts[1] == "e":
            idx = int(parts[2])
            inv_back = parts[3] if parts[3] in ("shop", "main") else "shop"
        elif len(parts) == 3 and parts[0] == "inv" and parts[1] == "e":
            idx = int(parts[2])
        else:
            raise ValueError
    except (IndexError, ValueError):
        await cq.answer("Неверный индекс.", show_alert=True)
        return

    inv = list(u.get("inventory") or [])
    eq = dict(u.get("equipped") or {})
    if idx < 0 or idx >= len(inv):
        await cq.answer("Предмета нет.", show_alert=True)
        return
    it = inv[idx]
    kind = str(it.get("kind", ""))
    if kind not in ("weapon", "armor"):
        await cq.answer("Этот предмет нельзя надеть.", show_alert=True)
        return

    inv.pop(idx)
    old = eq.get(kind)
    if isinstance(old, dict):
        inv.append(old)
    eq[kind] = it
    await db.update_user(u["user_id"], inventory=inv, equipped=eq)

    nu = await db.get_user(u["user_id"])
    if cq.message and nu:
        inv2 = list(nu.get("inventory") or [])
        eq2 = dict(nu.get("equipped") or {})
        item_name = escape(str(it.get("name", "Предмет")))
        await cq.message.edit_text(
            f"⚔️ Экипировано: <b>{item_name}</b>.\n\n" + inventory_text(inv2, eq2),
            reply_markup=kb_inventory(inv2, inv_back=inv_back),
            parse_mode="HTML",
        )
    await cq.answer()
