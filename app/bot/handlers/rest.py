"""Отдых вне экспедиции: 6 ч — полное HP; досрочное пробуждение без лечения."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery

from app import db
from app.bot.keyboards import kb_main
from app.bot.texts import status_text
from app.bot.ui_state import chapel_enabled, chapel_nav_title, order_enabled
from app.game import now_ts
from app.game.mercenary_order import effective_hp_max_for_user
from app.game.hero_rest import new_rest_state

router = Router()


@router.callback_query(F.data == "rest:start")
async def rest_start(cq: CallbackQuery) -> None:
    u = await db.ensure_user(cq.from_user.id, cq.from_user.username)
    if u.get("expedition"):
        await cq.answer("Во время экспедиции отдых недоступен.", show_alert=True)
        return
    if u.get("fishing"):
        await cq.answer("Во время рыбалки отдых недоступен.", show_alert=True)
        return
    if u.get("rest"):
        await cq.answer("Герой уже отдыхает.", show_alert=True)
        return
    if int(u["hp_current"]) >= effective_hp_max_for_user(u):
        await cq.answer("HP уже полное — отдых не нужен.", show_alert=True)
        return
    rest = new_rest_state(now_ts=now_ts())
    await db.update_user(u["user_id"], rest=rest)
    nu = await db.get_user(u["user_id"])
    if cq.message and nu:
        await cq.message.edit_text(
            status_text(nu),
            reply_markup=kb_main(
                nu.get("expedition"),
                nu.get("rest"),
                nu.get("fishing"),
                chapel_enabled(nu),
                order_enabled(nu),
                chapel_title=chapel_nav_title(nu),
            ),
        )
    await cq.answer("Герой лёг отдыхать.")


@router.callback_query(F.data == "rest:wake")
async def rest_wake(cq: CallbackQuery) -> None:
    u = await db.ensure_user(cq.from_user.id, cq.from_user.username)
    rest = u.get("rest")
    if not rest:
        await cq.answer("Герой не на отдыхе.", show_alert=True)
        return
    await db.update_user(u["user_id"], clear_rest=True)
    nu = await db.get_user(u["user_id"])
    if cq.message:
        await cq.message.edit_text(
            "⏰ Герой проснулся раньше времени. HP не изменились.",
            reply_markup=None,
        )
    if nu:
        await cq.bot.send_message(
            nu["user_id"],
            status_text(nu),
            reply_markup=kb_main(
                nu.get("expedition"),
                nu.get("rest"),
                nu.get("fishing"),
                chapel_enabled(nu),
                order_enabled(nu),
                chapel_title=chapel_nav_title(nu),
            ),
        )
    await cq.answer()
