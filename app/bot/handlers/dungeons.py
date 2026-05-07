"""Выбор подземелья и старт похода (callback run:*)."""

from __future__ import annotations

from aiogram import Router
from aiogram.types import CallbackQuery

from app import db
from app.bot.keyboards import kb_main
from app.game import (
    create_expedition,
    dungeon_by_id,
    expedition_travel_flavor,
    now_ts,
)

router = Router()


@router.callback_query(lambda c: c.data and c.data.startswith("run:"))
async def run_start(cq: CallbackQuery) -> None:
    assert cq.data is not None
    did = cq.data.split(":", 1)[1]
    d = dungeon_by_id(did)
    if not d:
        await cq.answer("Неизвестное подземелье.", show_alert=True)
        return
    u = await db.ensure_user(cq.from_user.id, cq.from_user.username)
    if u.get("expedition"):
        await cq.answer("Герой уже в экспедиции.", show_alert=True)
        return
    if u.get("rest"):
        await cq.answer("Герой отдыхает. Сначала разбудите его.", show_alert=True)
        return
    expedition = create_expedition(d, hp=int(u["hp_current"]))
    await db.update_user(u["user_id"], expedition=expedition)
    if cq.message:
        mins = max(1, (d.duration_seconds + 59) // 60)
        await cq.message.edit_text(
            f"🚶 Герой отправился в <b>{d.title}</b> (~{mins} мин).\n"
            "Я буду присылать новости о столкновениях и решениях по ходу похода.",
            reply_markup=kb_main(expedition, None),
        )
        await cq.message.answer(
            f"🚶 <b>{d.title}</b>\n{expedition_travel_flavor()}",
        )
        expedition["last_flavor_ts"] = now_ts()
        await db.update_user(u["user_id"], expedition=expedition)
    await cq.answer("Экспедиция началась.")
