"""Фоновый воркер: события похода, финиш, дорожные реплики."""

from __future__ import annotations

import asyncio
import logging
import random

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
from app.game.monsters import final_boss_for_dungeon
from app.shop import equipment_bonuses

_FLAVOR_GAP_SEC = 6.0
_FLAVOR_MIN_BEFORE_EVENT_SEC = 4.0
_BLACK_WALL_BOSS_HP = 300


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
                reply_markup=kb_main(nu.get("expedition"), nu.get("rest"), nu.get("fishing")),
            )


async def process_fishing(bot: Bot) -> None:
    now = now_ts()
    for u in await db.users_with_fishing_finished(now):
        uid = int(u["user_id"])
        catch_n = random.randint(1, 2)
        inv = list(u.get("inventory") or [])
        for _ in range(catch_n):
            inv.append(
                {
                    "kind": "item",
                    "name": "Свежая рыба",
                    "effect": "heal",
                    "value": random.randint(10, 22),
                }
            )
        await db.update_user(uid, inventory=inv, clear_fishing=True)
        await bot.send_message(
            uid,
            f"🎣 Герой вернулся с рыбалки. Поймано рыбы: {catch_n}.",
        )
        nu = await db.get_user(uid)
        if nu:
            await bot.send_message(
                uid,
                status_text(nu),
                reply_markup=kb_main(nu.get("expedition"), nu.get("rest"), nu.get("fishing")),
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

        boss = final_boss_for_dungeon(d.id)
        boss_pending_after_end = (
            boss is not None
            and not bool(exp.get("boss_done"))
            and now >= float(exp["end_ts"])
        )
        if (now >= float(exp["next_event_ts"]) and now < float(exp["end_ts"])) or boss_pending_after_end:
            df, wm = equipment_bonuses(u.get("equipped") or {})
            was_boss_done = bool(exp.get("boss_done"))
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
            if (
                not was_boss_done
                and bool(exp.get("boss_done"))
                and int(exp.get("hp", 0)) > 0
            ):
                if d.id == "lair" and not bool(u.get("next_act_unlocked")):
                    await db.update_user(u["user_id"], next_act_unlocked=True)
                    await bot.send_message(
                        u["user_id"],
                        (
                            "📜 Победа над Колдуном разорвала древнюю печать.\n"
                            "Открыт путь во 2 акт."
                        ),
                    )
                    u["next_act_unlocked"] = True
                elif d.id == "abyss_cathedral" and not bool(u.get("third_act_unlocked")):
                    await db.update_user(u["user_id"], third_act_unlocked=True)
                    await bot.send_message(
                        u["user_id"],
                        (
                            "📜 Порождение Бездны повержено, и Черная Стена дрогнула.\n"
                            "Открыт путь в 3 акт."
                        ),
                    )
                    u["third_act_unlocked"] = True
                elif d.id == "black_wall":
                    hp_left_global = await db.damage_black_wall(_BLACK_WALL_BOSS_HP)
                    if hp_left_global > 0:
                        await bot.send_message(
                            u["user_id"],
                            (
                                f"🧱 Черная Стена дрогнула, но устояла. "
                                f"Снято {_BLACK_WALL_BOSS_HP} общего HP "
                                f"(осталось: {hp_left_global}).\n"
                                "Ищите помощи других меченосцев."
                            ),
                        )
                    else:
                        await db.unlock_act4_for_all()
                        for uid in await db.all_user_ids():
                            try:
                                await bot.send_message(
                                    uid,
                                    (
                                        "🧱 Черная Стена рухнула под натиском меченосцев.\n"
                                        "Открыт путь в 4 акт."
                                    ),
                                )
                            except Exception:
                                logging.exception("Failed to notify user %s about act 4", uid)
                        u["fourth_act_unlocked"] = True
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
                        reply_markup=kb_main(nu.get("expedition"), nu.get("rest"), nu.get("fishing")),
                    )
            continue

        if now >= float(exp["end_ts"]):
            hp_left = max(1, int(exp["hp"]))
            bonus_gold = int(exp.get("bonus_gold", 0))
            bonus_xp = int(exp.get("bonus_xp", 0))
            loot_boost = float(exp.get("loot_boost", 0.0))
            rewards = finish_rewards(
                dungeon=d,
                level=int(u["level"]),
                hp=hp_left,
                hp_max=int(u["hp_max"]),
                loot_boost=loot_boost,
            )
            xp_gain = int(rewards["xp"]) + bonus_xp
            gold_gain = int(rewards["gold"]) + bonus_gold
            xp = int(u["xp"]) + xp_gain
            level = int(u["level"])
            while xp >= xp_for_next_level(level):
                xp -= xp_for_next_level(level)
                level += 1
            gold = int(u["gold"]) + gold_gain
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
                    f"+{xp_gain} опыта, +{gold_gain} золота.\n"
                    f"{loot_text}\n"
                    f"HP сейчас: {hp_after}/{hp_max_new}."
                ),
            )
            nu = await db.get_user(u["user_id"])
            if nu:
                await bot.send_message(
                    nu["user_id"],
                    status_text(nu),
                    reply_markup=kb_main(nu.get("expedition"), nu.get("rest"), nu.get("fishing")),
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
                    f"🚶 <b>{d.title}</b>\n{expedition_travel_flavor(d.id)}",
                )


async def expedition_worker(bot: Bot) -> None:
    while True:
        try:
            await process_expeditions(bot)
            await process_rests(bot)
            await process_fishing(bot)
        except Exception:
            logging.exception("Expedition worker failed")
        await asyncio.sleep(6)
