"""Братство Меча: наём нескольких соратников (3 акт)."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery

from app import db
from app.bot.keyboards import kb_mercenary_order
from app.bot.ui_state import order_enabled
from app.game.mercenary_order import (
    MERCENARY_OFFERS,
    effective_hp_max,
    mercenary_effects_text,
    mercenary_state_from_offer,
    offer_by_id,
    roster_summary_lines,
)

router = Router()


def _order_screen_text(*, gold: int, roster: list[dict]) -> str:
    lines = [
        "⚔️ <b>Братство Меча</b>\n",
        "Нанимай соратников <b>навсегда</b>: можно несколько одного типа. "
        "В походе каждый может принять смертельный удар — герой остаётся с тем же HP, что до удара.\n",
        f"💰 <b>Твоё золото:</b> {gold}\n",
    ]
    if roster:
        lines.append("<b>В отряде:</b>")
        for s in roster_summary_lines(roster):
            lines.append(f"• {s}")
        refund = sum(int(m.get("price", 0) or 0) for m in roster)
        lines.append(f"<i>Возврат при отставке всех: {refund} 💰</i>\n")
    lines.append("Нанять ещё:")
    for o in MERCENARY_OFFERS:
        lines.append(
            f"• {o['title']}: {mercenary_effects_text(o)} — {o['price']} 💰"
        )
    return "\n".join(lines)


@router.callback_query(F.data == "nav:order")
async def nav_order(cq: CallbackQuery) -> None:
    u = await db.ensure_user(cq.from_user.id, cq.from_user.username)
    if not order_enabled(u):
        await cq.answer("Братство доступно только во 3 акте.", show_alert=True)
        return
    if u.get("expedition"):
        await cq.answer("Во время похода наём недоступен.", show_alert=True)
        return
    if u.get("rest") or u.get("fishing"):
        await cq.answer("Сначала завершите отдых или рыбалку.", show_alert=True)
        return
    roster = list(u.get("mercenaries") or [])
    if cq.message:
        await cq.message.edit_text(
            _order_screen_text(gold=int(u["gold"]), roster=roster),
            reply_markup=kb_mercenary_order(has_roster=bool(roster)),
        )
    await cq.answer()


@router.callback_query(F.data.startswith("order:h:"))
async def order_hire(cq: CallbackQuery) -> None:
    u = await db.ensure_user(cq.from_user.id, cq.from_user.username)
    if not order_enabled(u):
        await cq.answer("Братство доступно только во 3 акте.", show_alert=True)
        return
    if u.get("expedition") or u.get("rest") or u.get("fishing"):
        await cq.answer("Сейчас нельзя нанять соратника.", show_alert=True)
        return
    oid = str((cq.data or "").split(":")[-1])
    offer = offer_by_id(oid)
    if not offer:
        await cq.answer("Неизвестный контракт.", show_alert=True)
        return
    price = int(offer["price"])
    gold = int(u["gold"])
    if gold < price:
        await cq.answer("Не хватает золота.", show_alert=True)
        return
    roster = list(u.get("mercenaries") or [])
    new_merc = mercenary_state_from_offer(offer)
    added_hp = int(new_merc.get("hp_bonus", 0) or 0)
    roster.append(new_merc)
    base = int(u["hp_max"])
    eff = effective_hp_max(base, roster)
    hp_cur = min(eff, int(u["hp_current"]) + added_hp)
    await db.update_user(
        u["user_id"],
        gold=gold - price,
        mercenary=roster,
        hp_current=hp_cur,
    )
    nu = await db.get_user(u["user_id"])
    if cq.message and nu:
        r = list(nu.get("mercenaries") or [])
        await cq.message.edit_text(
            _order_screen_text(gold=int(nu["gold"]), roster=r),
            reply_markup=kb_mercenary_order(has_roster=bool(r)),
        )
    await cq.answer(f"Нанят: {offer['title']}.")


@router.callback_query(F.data == "order:cancel")
async def order_cancel(cq: CallbackQuery) -> None:
    u = await db.ensure_user(cq.from_user.id, cq.from_user.username)
    if not order_enabled(u):
        await cq.answer("Братство доступно только во 3 акте.", show_alert=True)
        return
    roster = list(u.get("mercenaries") or [])
    if not roster:
        await cq.answer("В отряде никого нет.", show_alert=True)
        return
    refund = sum(int(m.get("price", 0) or 0) for m in roster)
    base_max = int(u["hp_max"])
    hp_cur = min(int(u["hp_current"]), base_max)
    await db.update_user(
        u["user_id"],
        gold=int(u["gold"]) + refund,
        hp_current=hp_cur,
        clear_mercenary=True,
    )
    nu = await db.get_user(u["user_id"])
    if cq.message and nu:
        await cq.message.edit_text(
            _order_screen_text(gold=int(nu["gold"]), roster=[]),
            reply_markup=kb_mercenary_order(has_roster=False),
        )
    await cq.answer(f"Отряд распущен. Возврат: {refund} 💰.")
