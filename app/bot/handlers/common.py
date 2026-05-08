"""Старт, статус, навигация на главный экран и список подземелий."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message

from app import db
from app.bot.name_filter import has_bad_words
from app.bot.keyboards import kb_debug, kb_dungeons, kb_main
from app.bot.texts import status_text
from app.game import hp_max_for_level, xp_for_next_level

router = Router()
_AWAITING_NAME: set[int] = set()
_DBG_RESTS: dict[int, int] = {}
_DBG_FISHINGS: dict[int, int] = {}
_DBG_REST_HOURS = 6
_DBG_FISHING_HOURS = 2


def _dbg_counts(user_id: int) -> tuple[int, int]:
    return int(_DBG_RESTS.get(user_id, 0)), int(_DBG_FISHINGS.get(user_id, 0))


def _dbg_hours(rests: int, fishings: int) -> int:
    return rests * _DBG_REST_HOURS + fishings * _DBG_FISHING_HOURS


def _dbg_markup(user_id: int):
    rests, fishings = _dbg_counts(user_id)
    return kb_debug(rests=rests, fishings=fishings, hours_total=_dbg_hours(rests, fishings))


def dungeons_title(act: int) -> str:
    return f"Выбери подземелье\n<b>Акт {act}</b>"


def _max_open_act(u: dict) -> int:
    return (
        4
        if bool(u.get("fourth_act_unlocked"))
        else 3
        if bool(u.get("third_act_unlocked"))
        else 2
        if bool(u.get("next_act_unlocked"))
        else 1
    )


def _effective_act(u: dict) -> int:
    act = int(u.get("selected_act", 1) or 1)
    if act < 1:
        act = 1
    return min(act, _max_open_act(u))


async def send_menu_screen(message: Message) -> None:
    u = await db.ensure_user(message.from_user.id, message.from_user.username)
    if not str(u.get("player_name") or "").strip():
        _AWAITING_NAME.add(message.from_user.id)
        await message.answer("Введите имя героя (2-24 символа):")
        return
    await message.answer(
        status_text(u),
        reply_markup=kb_main(u.get("expedition"), u.get("rest"), u.get("fishing")),
    )


@router.message(CommandStart())
async def start(message: Message) -> None:
    u = await db.ensure_user(message.from_user.id, message.from_user.username)
    if not str(u.get("player_name") or "").strip():
        _AWAITING_NAME.add(message.from_user.id)
        await message.answer(
            "Добро пожаловать, меченосец.\nВведите имя героя (2-24 символа):",
            reply_markup=_dbg_markup(message.from_user.id),
        )
        return
    await message.answer(
        "Герой готов к походам.",
        reply_markup=_dbg_markup(message.from_user.id),
    )
    await message.answer(
        status_text(u),
        reply_markup=kb_main(u.get("expedition"), u.get("rest"), u.get("fishing")),
    )


@router.message(Command("status"))
async def cmd_status(message: Message) -> None:
    await send_menu_screen(message)


@router.message(Command("dungeons"))
async def cmd_dungeons(message: Message) -> None:
    u = await db.ensure_user(message.from_user.id, message.from_user.username)
    if not str(u.get("player_name") or "").strip():
        _AWAITING_NAME.add(message.from_user.id)
        await message.answer("Сначала введите имя героя через /start.")
        return
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
    if u.get("fishing"):
        await message.answer(
            "Герой на рыбалке. Подземелья будут доступны после возвращения."
        )
        return
    act = _effective_act(u)
    if int(u.get("selected_act", 1) or 1) != act:
        await db.update_user(u["user_id"], selected_act=act)
    await message.answer(
        dungeons_title(act),
        reply_markup=kb_dungeons(
            act,
            bool(u.get("next_act_unlocked")),
            bool(u.get("third_act_unlocked")),
            bool(u.get("fourth_act_unlocked")),
        ),
    )


@router.callback_query(F.data.in_(("nav:main", "nav:status")))
async def nav_main(cq: CallbackQuery) -> None:
    u = await db.ensure_user(cq.from_user.id, cq.from_user.username)
    if not str(u.get("player_name") or "").strip():
        _AWAITING_NAME.add(cq.from_user.id)
        await cq.answer("Сначала введите имя героя через /start.", show_alert=True)
        return
    if cq.message:
        await cq.message.edit_text(
            status_text(u),
            reply_markup=kb_main(u.get("expedition"), u.get("rest"), u.get("fishing")),
        )
    await cq.answer()


@router.callback_query(F.data == "nav:dungeons")
async def nav_dungeons(cq: CallbackQuery) -> None:
    u = await db.ensure_user(cq.from_user.id, cq.from_user.username)
    if not str(u.get("player_name") or "").strip():
        _AWAITING_NAME.add(cq.from_user.id)
        await cq.answer("Сначала введите имя героя через /start.", show_alert=True)
        return
    if u.get("expedition"):
        await cq.answer("Герой уже в экспедиции.", show_alert=True)
        return
    if u.get("rest"):
        await cq.answer("Герой отдыхает. Сначала разбудите его.", show_alert=True)
        return
    if u.get("fishing"):
        await cq.answer("Герой на рыбалке. Сначала верните его.", show_alert=True)
        return
    act = _effective_act(u)
    if int(u.get("selected_act", 1) or 1) != act:
        await db.update_user(u["user_id"], selected_act=act)
    if cq.message:
        await cq.message.edit_text(
            dungeons_title(act),
            reply_markup=kb_dungeons(
                act,
                bool(u.get("next_act_unlocked")),
                bool(u.get("third_act_unlocked")),
                bool(u.get("fourth_act_unlocked")),
            ),
        )
    await cq.answer()


@router.callback_query(F.data == "act:locked")
async def act_locked(cq: CallbackQuery) -> None:
    await cq.answer("Сначала завершите текущий акт, чтобы открыть следующий.", show_alert=True)


@router.callback_query(F.data.startswith("act:view:"))
async def act_view(cq: CallbackQuery) -> None:
    assert cq.data is not None
    try:
        act = int(cq.data.split(":")[2])
    except (IndexError, ValueError):
        await cq.answer("Неизвестный акт.", show_alert=True)
        return
    u = await db.ensure_user(cq.from_user.id, cq.from_user.username)
    if not str(u.get("player_name") or "").strip():
        _AWAITING_NAME.add(cq.from_user.id)
        await cq.answer("Сначала введите имя героя через /start.", show_alert=True)
        return
    max_open_act = _max_open_act(u)
    if act < 1 or act > 4:
        await cq.answer("Неизвестный акт.", show_alert=True)
        return
    if act > max_open_act:
        await cq.answer("Путь пока закрыт.", show_alert=True)
        return
    await db.update_user(u["user_id"], selected_act=act)
    if cq.message:
        await cq.message.edit_text(
            dungeons_title(act),
            reply_markup=kb_dungeons(
                act,
                bool(u.get("next_act_unlocked")),
                bool(u.get("third_act_unlocked")),
                bool(u.get("fourth_act_unlocked")),
            ),
        )
    await cq.answer()


@router.callback_query(F.data == "act:empty")
async def act_empty(cq: CallbackQuery) -> None:
    await cq.answer("Подземелья этого акта скоро появятся.", show_alert=True)


@router.message(lambda m: m.from_user and m.from_user.id in _AWAITING_NAME)
async def capture_player_name(message: Message) -> None:
    text = (message.text or "").strip()
    if not text or text.startswith("/") or len(text) < 2 or len(text) > 24:
        await message.answer("Введите корректное имя героя (2-24 символа).")
        return
    if has_bad_words(text):
        await message.answer("Это имя недопустимо. Выберите другое без оскорбительных слов.")
        return
    await db.update_user(message.from_user.id, player_name=text)
    _AWAITING_NAME.discard(message.from_user.id)
    await message.answer(f"Имя героя: <b>{text}</b>.")
    await send_menu_screen(message)


@router.message(F.text.startswith("😴 Отдых ("))
async def dbg_rest(message: Message) -> None:
    u = await db.ensure_user(message.from_user.id, message.from_user.username)
    hp_max = int(u["hp_max"])
    await db.update_user(u["user_id"], hp_current=hp_max)
    _DBG_RESTS[u["user_id"]] = int(_DBG_RESTS.get(u["user_id"], 0)) + 1
    await message.answer("Отдых завершён мгновенно. HP восстановлено.", reply_markup=_dbg_markup(u["user_id"]))
    await send_menu_screen(message)


@router.message(F.text.startswith("🎣 Рыбалка ("))
async def dbg_fishing(message: Message) -> None:
    u = await db.ensure_user(message.from_user.id, message.from_user.username)
    inv = list(u.get("inventory") or [])
    # Отладочная рыбалка мгновенная: 1-2 рыбы.
    import random

    got = random.randint(1, 2)
    for _ in range(got):
        inv.append(
            {
                "kind": "item",
                "name": "Свежая рыба",
                "effect": "heal",
                "value": random.randint(10, 22),
            }
        )
    await db.update_user(u["user_id"], inventory=inv)
    _DBG_FISHINGS[u["user_id"]] = int(_DBG_FISHINGS.get(u["user_id"], 0)) + 1
    await message.answer(
        f"Рыбалка завершена мгновенно. Поймано: {got}.",
        reply_markup=_dbg_markup(u["user_id"]),
    )
    await send_menu_screen(message)


@router.message(F.text == "💰 +100 золота")
async def dbg_gold(message: Message) -> None:
    u = await db.ensure_user(message.from_user.id, message.from_user.username)
    await db.update_user(u["user_id"], gold=int(u["gold"]) + 100)
    await message.answer("+100 золота.")
    await send_menu_screen(message)


@router.message(F.text == "⭐ +100 опыта")
async def dbg_xp(message: Message) -> None:
    u = await db.ensure_user(message.from_user.id, message.from_user.username)
    xp = int(u["xp"]) + 100
    level = int(u["level"])
    while xp >= xp_for_next_level(level):
        xp -= xp_for_next_level(level)
        level += 1
    hp_max_new = hp_max_for_level(level)
    hp_current_new = min(hp_max_new, int(u["hp_current"]))
    await db.update_user(
        u["user_id"],
        level=level,
        xp=xp,
        hp_max=hp_max_new,
        hp_current=hp_current_new,
    )
    await message.answer("+100 опыта.")
    await send_menu_screen(message)


@router.message(F.text == "♻️ Сбросить")
async def dbg_reset(message: Message) -> None:
    u = await db.ensure_user(message.from_user.id, message.from_user.username)
    await db.update_user(
        u["user_id"],
        level=1,
        xp=0,
        gold=0,
        hp_max=100,
        hp_current=100,
        clear_expedition=True,
        clear_rest=True,
        clear_fishing=True,
        inventory=[],
        equipped={},
        next_act_unlocked=False,
        third_act_unlocked=False,
        fourth_act_unlocked=False,
        selected_act=1,
        player_name=None,
    )
    _DBG_RESTS[u["user_id"]] = 0
    _DBG_FISHINGS[u["user_id"]] = 0
    _AWAITING_NAME.discard(message.from_user.id)
    await message.answer("Прогресс героя сброшен. Введите новое имя.", reply_markup=_dbg_markup(u["user_id"]))
    await send_menu_screen(message)


@router.message(F.text.startswith("🕒 Часы: "))
async def dbg_hours_noop(message: Message) -> None:
    u = await db.ensure_user(message.from_user.id, message.from_user.username)
    await message.answer("Это индикатор отладочного времени.", reply_markup=_dbg_markup(u["user_id"]))
