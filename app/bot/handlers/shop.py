"""Магазин: витрина, покупка, переход в инвентарь с экрана магазина."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery

from app import db
from app.bot.handlers.inventory import open_inventory_screen
from app.bot.keyboards import kb_shop
from app.shop import ensure_shop_today, shop_message_text

router = Router()


@router.callback_query(F.data == "nav:shop")
async def nav_shop(cq: CallbackQuery) -> None:
    u = await db.ensure_user(cq.from_user.id, cq.from_user.username)
    if u.get("expedition"):
        await cq.answer(
            "Во время похода магазин недоступен. Заверши экспедицию или нажми «Сбежать».",
            show_alert=True,
        )
        return
    if u.get("rest"):
        await cq.answer("Герой отдыхает. Магазин будет доступен после пробуждения.", show_alert=True)
        return
    day, items = await ensure_shop_today()
    if cq.message:
        await cq.message.edit_text(
            shop_message_text(
                day,
                items,
                gold=int(u["gold"]),
                equipped=dict(u.get("equipped") or {}),
            ),
            reply_markup=kb_shop(items),
        )
    await cq.answer()


@router.callback_query(F.data.startswith("shop:b:"))
async def shop_buy(cq: CallbackQuery) -> None:
    u = await db.ensure_user(cq.from_user.id, cq.from_user.username)
    if u.get("rest"):
        await cq.answer("Герой отдыхает.", show_alert=True)
        return
    try:
        slot = int(cq.data.split(":", 2)[2])
    except (IndexError, ValueError):
        await cq.answer("Неверный слот.", show_alert=True)
        return
    day, items = await ensure_shop_today()
    by_slot = {int(x["slot"]): x for x in items}
    offer = by_slot.get(slot)
    if not offer:
        await cq.answer("Товара нет.", show_alert=True)
        return
    if offer.get("sold"):
        await cq.answer("Уже продано.", show_alert=True)
        return
    price = int(offer.get("price", 0))
    if int(u["gold"]) < price:
        await cq.answer("Не хватает золота.", show_alert=True)
        return
    kind = str(offer.get("kind", ""))
    bought = {k: v for k, v in offer.items() if k != "slot"}
    eq = dict(u.get("equipped") or {})
    inv = list(u.get("inventory") or [])
    if kind == "weapon":
        old = eq.get("weapon")
        if isinstance(old, dict):
            inv.append(old)
        eq["weapon"] = bought
    elif kind == "armor":
        old = eq.get("armor")
        if isinstance(old, dict):
            inv.append(old)
        eq["armor"] = bought
    elif kind == "item":
        inv.append(bought)
    else:
        await cq.answer("Неизвестный тип товара.", show_alert=True)
        return
    await db.update_user(
        u["user_id"],
        gold=int(u["gold"]) - price,
        inventory=inv,
        equipped=eq,
    )
    updated_items: list[dict] = []
    for row in items:
        cloned = dict(row)
        if int(cloned.get("slot", -1)) == slot:
            cloned["sold"] = True
        updated_items.append(cloned)
    day_state, _ = await db.get_shop_state()
    persist_day = day_state or day
    await db.set_shop_state(persist_day, updated_items)
    await cq.answer(f"Куплено: {bought.get('name', '?')}")
    day2, items2 = await ensure_shop_today()
    nu = await db.get_user(u["user_id"])
    if cq.message and nu:
        await cq.message.edit_text(
            shop_message_text(
                day2,
                items2,
                gold=int(nu["gold"]),
                equipped=dict(nu.get("equipped") or {}),
            ),
            reply_markup=kb_shop(items2),
        )


@router.callback_query(F.data.startswith("shop:sold:"))
async def shop_sold(cq: CallbackQuery) -> None:
    await cq.answer("Эта позиция уже продана.", show_alert=True)


@router.callback_query(F.data == "shop:inv")
async def shop_inventory_from_shop(cq: CallbackQuery) -> None:
    u = await db.ensure_user(cq.from_user.id, cq.from_user.username)
    if u.get("rest"):
        await cq.answer("Герой отдыхает.", show_alert=True)
        return
    await open_inventory_screen(cq, inv_back="shop")
