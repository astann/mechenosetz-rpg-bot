"""Часовня / Священник Братства: благословения во 2 и 3 актах."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery

from app import db
from app.bot.keyboards import kb_chapel
from app.bot.ui_state import chapel_enabled, chapel_nav_title
from app.game.chapel import (
    CHAPEL_COST_DEFENSE,
    CHAPEL_COST_HEAL,
    CHAPEL_COST_LOOT,
    CHAPEL_COST_STRENGTH,
    blessing_active,
    chapel_state,
)
from app.game.mercenary_order import effective_hp_max_for_user

router = Router()


def _chapel_text(u: dict) -> str:
    chapel = dict(u.get("chapel") or {})
    title = chapel_nav_title(u)

    def line(key: str) -> str:
        return "да" if blessing_active(chapel, key) else "нет"

    strength_line = line("strength")
    defense_line = line("defense")
    loot_line = line("loot")
    return (
        f"⛪ <b>{title}</b>\n\n"
        "Здесь можно купить редкие благословения (остаются с героем навсегда).\n"
        f"• Благословение силы — {CHAPEL_COST_STRENGTH} 💰 (+атака)\n"
        f"• Дар исцеления — {CHAPEL_COST_HEAL} 💰 (мгновенно восстанавливает HP)\n"
        f"• Просьба о защите — {CHAPEL_COST_DEFENSE} 💰 (+защита)\n"
        f"• Благодать богатств — {CHAPEL_COST_LOOT} 💰 (+шанс трофея)\n\n"
        f"Получено:\nСила: {strength_line}\nЗащита: {defense_line}\nБогатства: {loot_line}\n\n"
        f"Золото: {int(u.get('gold', 0))}"
    )


@router.callback_query(F.data == "nav:chapel")
async def nav_chapel(cq: CallbackQuery) -> None:
    u = await db.ensure_user(cq.from_user.id, cq.from_user.username)
    if not chapel_enabled(u):
        await cq.answer("Доступно только во 2 и 3 актах.", show_alert=True)
        return
    if u.get("expedition"):
        await cq.answer("Во время экспедиции часовня недоступна.", show_alert=True)
        return
    if u.get("rest"):
        await cq.answer("Герой отдыхает. Часовня будет доступна после пробуждения.", show_alert=True)
        return
    if u.get("fishing"):
        await cq.answer("Герой на рыбалке. Вернитесь позже.", show_alert=True)
        return
    if cq.message:
        await cq.message.edit_text(_chapel_text(u), reply_markup=kb_chapel())
    await cq.answer()


@router.callback_query(F.data.startswith("chapel:buy:"))
async def chapel_buy(cq: CallbackQuery) -> None:
    u = await db.ensure_user(cq.from_user.id, cq.from_user.username)
    if not chapel_enabled(u):
        await cq.answer("Доступно только во 2 и 3 актах.", show_alert=True)
        return
    if u.get("expedition") or u.get("rest") or u.get("fishing"):
        await cq.answer("Сейчас нельзя купить благословение.", show_alert=True)
        return
    kind = str((cq.data or "").split(":")[-1])
    gold = int(u["gold"])
    chapel = dict(u.get("chapel") or chapel_state())

    if kind == "strength":
        if blessing_active(chapel, "strength"):
            await cq.answer("Это благословение уже ваше.", show_alert=True)
            return
        if gold < CHAPEL_COST_STRENGTH:
            await cq.answer("Недостаточно золота.", show_alert=True)
            return
        chapel["strength"] = True
        await db.update_user(
            u["user_id"],
            gold=gold - CHAPEL_COST_STRENGTH,
            chapel=chapel,
        )
        await cq.answer("Благословение силы ниспослано.")
    elif kind == "heal":
        if gold < CHAPEL_COST_HEAL:
            await cq.answer("Недостаточно золота.", show_alert=True)
            return
        await db.update_user(
            u["user_id"],
            gold=gold - CHAPEL_COST_HEAL,
            hp_current=effective_hp_max_for_user(u),
        )
        await cq.answer("Дар исцеления принят.")
    elif kind == "defense":
        if blessing_active(chapel, "defense"):
            await cq.answer("Это благословение уже ваше.", show_alert=True)
            return
        if gold < CHAPEL_COST_DEFENSE:
            await cq.answer("Недостаточно золота.", show_alert=True)
            return
        chapel["defense"] = True
        await db.update_user(
            u["user_id"],
            gold=gold - CHAPEL_COST_DEFENSE,
            chapel=chapel,
        )
        await cq.answer("Просьба о защите услышана.")
    elif kind == "wealth":
        if blessing_active(chapel, "loot"):
            await cq.answer("Это благословение уже ваше.", show_alert=True)
            return
        if gold < CHAPEL_COST_LOOT:
            await cq.answer("Недостаточно золота.", show_alert=True)
            return
        chapel["loot"] = True
        await db.update_user(
            u["user_id"],
            gold=gold - CHAPEL_COST_LOOT,
            chapel=chapel,
        )
        await cq.answer("Благодать богатств ниспослана.")
    else:
        await cq.answer("Неизвестное благословение.", show_alert=True)
        return

    nu = await db.get_user(u["user_id"])
    if cq.message and nu:
        await cq.message.edit_text(_chapel_text(nu), reply_markup=kb_chapel())

