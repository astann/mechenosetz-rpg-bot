"""Побег из подземелья."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery

from app import db
from app.bot.keyboards import kb_flee_confirm, kb_main
from app.bot.texts import status_text

router = Router()

_FLEE_CONFIRM_SUFFIX = (
    "\n\n⚠️ <b>Побег без награды.</b>\n"
    "Опыт и золото за подземелье не будут начислены. Подтвердить?"
)


@router.callback_query(F.data == "expedition:flee")
async def expedition_flee_ask(cq: CallbackQuery) -> None:
    u = await db.ensure_user(cq.from_user.id, cq.from_user.username)
    exp = u.get("expedition")
    if not exp:
        await cq.answer("Экспедиция не активна.", show_alert=True)
        return
    if cq.message:
        await cq.message.edit_text(
            status_text(u) + _FLEE_CONFIRM_SUFFIX,
            reply_markup=kb_flee_confirm(),
        )
    await cq.answer()


@router.callback_query(F.data == "expedition:flee:yes")
async def expedition_flee_confirm(cq: CallbackQuery) -> None:
    u = await db.ensure_user(cq.from_user.id, cq.from_user.username)
    exp = u.get("expedition")
    if not exp:
        await cq.answer("Экспедиция уже не активна.", show_alert=True)
        if cq.message:
            nu = await db.get_user(u["user_id"])
            if nu:
                await cq.message.edit_text(
                    status_text(nu),
                    reply_markup=kb_main(nu.get("expedition"), nu.get("rest"), nu.get("fishing")),
                )
        return
    hp_exp = max(1, min(int(u["hp_max"]), int(exp["hp"])))
    await db.update_user(u["user_id"], hp_current=hp_exp, clear_expedition=True)
    nu = await db.get_user(u["user_id"])
    if cq.message:
        await cq.message.edit_text(
            "🏃 Герой сбежал из похода. Награды нет.",
            reply_markup=None,
        )
    if nu:
        await cq.bot.send_message(
            nu["user_id"],
            status_text(nu),
            reply_markup=kb_main(nu.get("expedition"), nu.get("rest"), nu.get("fishing")),
        )
    await cq.answer()
