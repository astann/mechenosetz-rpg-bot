"""Старт, статус, навигация на главный экран и список подземелий."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove

from app import db
from app.bot.keyboards import kb_dungeons, kb_main
from app.bot.texts import status_text

router = Router()


async def send_menu_screen(message: Message) -> None:
    u = await db.ensure_user(message.from_user.id, message.from_user.username)
    await message.answer(
        status_text(u),
        reply_markup=kb_main(u.get("expedition"), u.get("rest")),
    )


@router.message(CommandStart())
async def start(message: Message) -> None:
    u = await db.ensure_user(message.from_user.id, message.from_user.username)
    await message.answer(
        "Герой готов к походам.",
        reply_markup=ReplyKeyboardRemove(remove_keyboard=True),
    )
    await message.answer(
        status_text(u),
        reply_markup=kb_main(u.get("expedition"), u.get("rest")),
    )


@router.message(Command("status"))
async def cmd_status(message: Message) -> None:
    await send_menu_screen(message)


@router.message(Command("dungeons"))
async def cmd_dungeons(message: Message) -> None:
    u = await db.ensure_user(message.from_user.id, message.from_user.username)
    if u.get("expedition"):
        await message.answer(
            "Герой уже в экспедиции. Прервать поход можно кнопкой «Сбежать» на главном экране."
        )
        return
    if u.get("rest"):
        await message.answer(
            "Герой отдыхает. Подземелья будут доступны после пробуждения или окончания отдыха."
        )
        return
    await message.answer("Выбери подземелье:", reply_markup=kb_dungeons())


@router.callback_query(F.data.in_(("nav:main", "nav:status")))
async def nav_main(cq: CallbackQuery) -> None:
    u = await db.ensure_user(cq.from_user.id, cq.from_user.username)
    if cq.message:
        await cq.message.edit_text(
            status_text(u),
            reply_markup=kb_main(u.get("expedition"), u.get("rest")),
        )
    await cq.answer()


@router.callback_query(F.data == "nav:dungeons")
async def nav_dungeons(cq: CallbackQuery) -> None:
    u = await db.ensure_user(cq.from_user.id, cq.from_user.username)
    if u.get("expedition"):
        await cq.answer("Герой уже в экспедиции.", show_alert=True)
        return
    if u.get("rest"):
        await cq.answer("Герой отдыхает. Сначала разбудите его.", show_alert=True)
        return
    if cq.message:
        await cq.message.edit_text("Выбери подземелье:", reply_markup=kb_dungeons())
    await cq.answer()
