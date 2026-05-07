"""Рыбалка вне экспедиции: 2 ч до улова."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery

from app import db
from app.bot.keyboards import kb_fishing_stop_confirm, kb_main
from app.bot.texts import status_text
from app.game import now_ts
from app.game.hero_fishing import new_fishing_state

router = Router()
_FISHING_STOP_CONFIRM_SUFFIX = (
    "\n\n⚠️ <b>Вернуться сейчас?</b>\n"
    "Если прервать рыбалку раньше времени, улова не будет."
)


@router.callback_query(F.data == "fish:start")
async def fishing_start(cq: CallbackQuery) -> None:
    u = await db.ensure_user(cq.from_user.id, cq.from_user.username)
    if u.get("expedition"):
        await cq.answer("Во время экспедиции рыбалка недоступна.", show_alert=True)
        return
    if u.get("rest"):
        await cq.answer("Герой отдыхает. Сначала разбудите его.", show_alert=True)
        return
    if u.get("fishing"):
        await cq.answer("Герой уже на рыбалке.", show_alert=True)
        return
    fishing = new_fishing_state(now_ts=now_ts())
    await db.update_user(u["user_id"], fishing=fishing)
    nu = await db.get_user(u["user_id"])
    if cq.message and nu:
        await cq.message.edit_text(
            status_text(nu),
            reply_markup=kb_main(nu.get("expedition"), nu.get("rest"), nu.get("fishing")),
        )
    await cq.answer("Герой ушёл на рыбалку.")


@router.callback_query(F.data == "fish:stop")
async def fishing_stop(cq: CallbackQuery) -> None:
    u = await db.ensure_user(cq.from_user.id, cq.from_user.username)
    fishing = u.get("fishing")
    if not fishing:
        await cq.answer("Герой не на рыбалке.", show_alert=True)
        return
    if cq.message:
        await cq.message.edit_text(
            status_text(u) + _FISHING_STOP_CONFIRM_SUFFIX,
            reply_markup=kb_fishing_stop_confirm(),
        )
    await cq.answer()


@router.callback_query(F.data == "fish:stop:yes")
async def fishing_stop_confirm(cq: CallbackQuery) -> None:
    u = await db.ensure_user(cq.from_user.id, cq.from_user.username)
    fishing = u.get("fishing")
    if not fishing:
        await cq.answer("Рыбалка уже завершена.", show_alert=True)
        if cq.message:
            nu = await db.get_user(u["user_id"])
            if nu:
                await cq.message.edit_text(
                    status_text(nu),
                    reply_markup=kb_main(nu.get("expedition"), nu.get("rest"), nu.get("fishing")),
                )
        return
    await db.update_user(u["user_id"], clear_fishing=True)
    nu = await db.get_user(u["user_id"])
    if cq.message:
        await cq.message.edit_text(
            "🎣 Герой вернулся с берега раньше времени. Улов не пойман.",
            reply_markup=None,
        )
    if nu:
        await cq.bot.send_message(
            nu["user_id"],
            status_text(nu),
            reply_markup=kb_main(nu.get("expedition"), nu.get("rest"), nu.get("fishing")),
        )
    await cq.answer()

