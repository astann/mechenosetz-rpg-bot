"""Побег из подземелья."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery

from app import db
from app.bot.keyboards import kb_flee_confirm, kb_main
from app.bot.texts import status_text
from app.bot.ui_state import chapel_enabled, chapel_nav_title, order_enabled
from app.game.mercenary_order import effective_hp_max_for_user

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
                    reply_markup=kb_main(
                        nu.get("expedition"),
                        nu.get("rest"),
                        nu.get("fishing"),
                        chapel_enabled(nu),
                        order_enabled(nu),
                        chapel_title=chapel_nav_title(nu),
                    ),
                )
        return
    hp_cap = effective_hp_max_for_user(u)
    hp_exp = max(1, min(hp_cap, int(exp["hp"])))
    merc_heal = max(0, int(exp.get("merc_heal_after_run", 0) or 0))
    hp_exp = min(hp_cap, hp_exp + merc_heal)
    await db.update_user(u["user_id"], hp_current=hp_exp, clear_expedition=True)
    nu = await db.get_user(u["user_id"])
    if cq.message:
        await cq.message.edit_text(
            "🏃 Герой сбежал из похода. Награды нет.",
            reply_markup=None,
        )
    if nu:
        if merc_heal > 0:
            await cq.bot.send_message(
                nu["user_id"],
                f"🩹 Наёмник подлатал отряд после отступления: +{merc_heal} HP.",
            )
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
