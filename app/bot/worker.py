"""Фоновый воркер: события похода, финиш, дорожные реплики."""

from __future__ import annotations

import asyncio
import logging

from aiogram import Bot

from app import db
from app.bot.keyboards import kb_main
from app.bot.texts import status_text
from app.game import (
    dungeon_by_id,
    expedition_travel_flavor,
    finish_rewards,
    hp_max_for_level,
    now_ts,
    process_event,
    xp_for_next_level,
)
from app.shop import equipment_bonuses

_FLAVOR_GAP_SEC = 6.0
_FLAVOR_MIN_BEFORE_EVENT_SEC = 4.0


async def process_rests(bot: Bot) -> None:
    now = now_ts()
    for u in await db.users_with_rest_finished(now):
        uid = int(u["user_id"])
        hp_max = int(u["hp_max"])
        await db.update_user(uid, hp_current=hp_max, clear_rest=True)
        await bot.send_message(
            uid,
            "☀️ Герой выспался. HP полностью восстановлено.",
        )
        nu = await db.get_user(uid)
        if nu:
            await bot.send_message(
                uid,
                status_text(nu),
                reply_markup=kb_main(nu.get("expedition"), nu.get("rest")),
            )


async def process_expeditions(bot: Bot) -> None:
    users = await db.users_with_active_expedition()
    now = now_ts()
    for u in users:
        exp = u.get("expedition")
        if not exp:
            continue
        d = dungeon_by_id(str(exp["dungeon_id"]))
        if not d:
            await db.update_user(u["user_id"], clear_expedition=True)
            continue

        if now >= float(exp["next_event_ts"]) and now < float(exp["end_ts"]):
            df, wm = equipment_bonuses(u.get("equipped") or {})
            exp, text = process_event(
                expedition=exp,
                level=int(u["level"]),
                defense_flat=df,
                weapon_attack=wm,
            )
            exp["last_flavor_ts"] = now_ts()
            hp = int(exp["hp"])
            await db.update_user(
                u["user_id"],
                hp_current=max(1, hp),
                expedition=exp,
            )
            await bot.send_message(
                u["user_id"],
                f"🕯 <b>{d.title}</b>\n{text}",
            )
            if hp <= 0:
                await db.update_user(
                    u["user_id"],
                    hp_current=1,
                    clear_expedition=True,
                )
                await bot.send_message(
                    u["user_id"],
                    "☠️ Герой пал в экспедиции и вернулся раненым. Добыча потеряна.",
                )
                nu = await db.get_user(u["user_id"])
                if nu:
                    await bot.send_message(
                        nu["user_id"],
                        status_text(nu),
                        reply_markup=kb_main(nu.get("expedition"), nu.get("rest")),
                    )
            continue

        if now >= float(exp["end_ts"]):
            hp_left = max(1, int(exp["hp"]))
            rewards = finish_rewards(
                dungeon=d,
                level=int(u["level"]),
                hp=hp_left,
                hp_max=int(u["hp_max"]),
            )
            xp = int(u["xp"]) + int(rewards["xp"])
            level = int(u["level"])
            while xp >= xp_for_next_level(level):
                xp -= xp_for_next_level(level)
                level += 1
            gold = int(u["gold"]) + int(rewards["gold"])
            hp_max_new = hp_max_for_level(level)
            hp_after = min(hp_max_new, hp_left)
            await db.update_user(
                u["user_id"],
                level=level,
                xp=xp,
                gold=gold,
                hp_max=hp_max_new,
                hp_current=hp_after,
                clear_expedition=True,
            )
            loot_text = "Найден редкий трофей." if rewards["loot"] else "Редкого трофея нет."
            await bot.send_message(
                u["user_id"],
                (
                    f"🏁 Герой вернулся из <b>{d.title}</b>.\n"
                    f"+{rewards['xp']} опыта, +{rewards['gold']} золота.\n"
                    f"{loot_text}\n"
                    f"HP сейчас: {hp_after}/{hp_max_new}."
                ),
            )
            nu = await db.get_user(u["user_id"])
            if nu:
                await bot.send_message(
                    nu["user_id"],
                    status_text(nu),
                    reply_markup=kb_main(nu.get("expedition"), nu.get("rest")),
                )
            continue

        next_ev = float(exp["next_event_ts"])
        end_ts = float(exp["end_ts"])
        if now < next_ev and now < end_ts:
            last_fl = float(exp["last_flavor_ts"])
            if (
                now - last_fl >= _FLAVOR_GAP_SEC
                and next_ev - now > _FLAVOR_MIN_BEFORE_EVENT_SEC
            ):
                exp_f = dict(exp)
                exp_f["last_flavor_ts"] = now
                await db.update_user(u["user_id"], expedition=exp_f)
                await bot.send_message(
                    u["user_id"],
                    f"🚶 <b>{d.title}</b>\n{expedition_travel_flavor()}",
                )


async def expedition_worker(bot: Bot) -> None:
    while True:
        try:
            await process_expeditions(bot)
            await process_rests(bot)
        except Exception:
            logging.exception("Expedition worker failed")
        await asyncio.sleep(6)
