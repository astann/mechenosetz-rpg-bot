"""Inline-клавиатуры Telegram (разметка кнопок), без запросов к БД."""

from __future__ import annotations

from typing import Any

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from app.game.dungeons import DUNGEONS
from app.game.mercenary_order import MERCENARY_OFFERS, mercenary_effects_text


def _dungeon_skulls(danger: float) -> str:
    if danger < 2.0:
        n = 1
    elif danger < 4.0:
        n = 2
    else:
        n = 3
    return "💀" * n


def _shop_button_label(s: dict) -> str:
    sold = bool(s.get("sold"))
    price = int(s.get("price", 0))
    name = str(s.get("name", "?"))
    kind = str(s.get("kind", ""))
    emoji = "⚔️" if kind == "weapon" else "🛡" if kind == "armor" else "🧪"
    if kind == "weapon":
        n = int(s.get("attack", 0))
    elif kind == "armor":
        n = int(s.get("defense", 0))
    else:
        n = int(s.get("value", 0))
    stat = f"+{n}"
    max_name = 24
    if len(name) > max_name:
        name = name[: max_name - 1] + "…"
    if sold:
        label = f"{emoji} {name} {stat} · продано"
    else:
        label = f"{emoji} {name} {stat} · {price} 💰"
    if len(label) > 64:
        label = label[:61] + "…"
    return label


def kb_flee_confirm() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Да, сбежать", callback_data="expedition:flee:yes"
                ),
                InlineKeyboardButton(text="Отмена", callback_data="nav:main"),
            ],
        ]
    )


def kb_fishing_stop_confirm() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Да, вернуться", callback_data="fish:stop:yes"
                ),
                InlineKeyboardButton(text="Отмена", callback_data="nav:main"),
            ],
        ]
    )


def kb_main(
    expedition: dict | None = None,
    rest: dict[str, Any] | None = None,
    fishing: dict[str, Any] | None = None,
    chapel_enabled: bool = False,
    order_enabled: bool = False,
    *,
    chapel_title: str = "Разрушенная Часовня",
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    if expedition:
        rows.append(
            [
                InlineKeyboardButton(text="Инвентарь", callback_data="nav:inv"),
                InlineKeyboardButton(text="Сбежать", callback_data="expedition:flee"),
            ]
        )
    elif rest:
        rows.append(
            [
                InlineKeyboardButton(
                    text="Разбудить героя", callback_data="rest:wake"
                ),
            ]
        )
    elif fishing:
        rows.append(
            [
                InlineKeyboardButton(
                    text="Вернуться с рыбалки", callback_data="fish:stop"
                ),
            ]
        )
    else:
        rows.append(
            [InlineKeyboardButton(text="Подземелья", callback_data="nav:dungeons")]
        )
        rows.append([InlineKeyboardButton(text="Торговец", callback_data="nav:shop")])
        if chapel_enabled:
            rows.append(
                [InlineKeyboardButton(text=chapel_title, callback_data="nav:chapel")]
            )
        if order_enabled:
            rows.append(
                [InlineKeyboardButton(text="Братство Меча", callback_data="nav:order")]
            )
        rows.append([InlineKeyboardButton(text="Инвентарь", callback_data="nav:inv")])
        rows.append(
            [InlineKeyboardButton(text="Рыбалка (2 ч)", callback_data="fish:start")]
        )
        rows.append(
            [InlineKeyboardButton(text="Отдых (6 ч)", callback_data="rest:start")]
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def kb_mercenary_order(*, has_roster: bool) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for o in MERCENARY_OFFERS:
        oid = str(o["id"])
        price = int(o["price"])
        title = str(o["title"])
        label = f"{title} ({mercenary_effects_text(o)}) · {price} 💰"
        if len(label) > 64:
            label = label[:61] + "…"
        rows.append(
            [InlineKeyboardButton(text=label, callback_data=f"order:h:{oid}")]
        )
    bottom: list[InlineKeyboardButton] = [
        InlineKeyboardButton(text="Назад", callback_data="nav:main"),
    ]
    if has_roster:
        bottom.insert(
            0,
            InlineKeyboardButton(text="Распустить отряд", callback_data="order:cancel"),
        )
    rows.append(bottom)
    return InlineKeyboardMarkup(inline_keyboard=rows)


def kb_chapel() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Благословение силы",
                    callback_data="chapel:buy:strength",
                )
            ],
            [InlineKeyboardButton(text="Дар исцеления", callback_data="chapel:buy:heal")],
            [InlineKeyboardButton(text="Просьба о защите", callback_data="chapel:buy:defense")],
            [InlineKeyboardButton(text="Благодать богатств", callback_data="chapel:buy:wealth")],
            [InlineKeyboardButton(text="Назад", callback_data="nav:main")],
        ]
    )


def kb_debug(*, rests: int = 0, fishings: int = 0, hours_total: int = 0) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=f"😴 Отдых ({max(0, rests)})"),
                KeyboardButton(text=f"🎣 Рыбалка ({max(0, fishings)})"),
            ],
            [KeyboardButton(text=f"🕒 Часы: {max(0, hours_total)}")],
            [
                KeyboardButton(text="💰 +100 золота"),
                KeyboardButton(text="⭐ +100 опыта"),
                KeyboardButton(text="♻️ Сбросить"),
            ],
        ],
        resize_keyboard=True,
    )


def kb_shop(items: list[dict]) -> InlineKeyboardMarkup:
    by_slot = sorted(items, key=lambda x: int(x.get("slot", 0)))
    rows: list[list[InlineKeyboardButton]] = []
    for s in by_slot:
        i = int(s["slot"])
        sold = bool(s.get("sold"))
        rows.append(
            [
                InlineKeyboardButton(
                    text=_shop_button_label(s),
                    callback_data=(f"shop:sold:{i}" if sold else f"shop:b:{i}"),
                )
            ]
        )
    rows.append(
        [
            InlineKeyboardButton(text="Продать", callback_data="shop:sell"),
            InlineKeyboardButton(text="Инвентарь", callback_data="shop:inv"),
            InlineKeyboardButton(text="Назад", callback_data="nav:main"),
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def kb_sell_inventory(inv: list[dict]) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for idx, it in enumerate(inv):
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"Продать: {str(it.get('name', '?'))[:22]}",
                    callback_data=f"shop:s:{idx}",
                )
            ]
        )
    rows.append([InlineKeyboardButton(text="Назад к витрине", callback_data="shop:sell:back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def kb_inventory(inv: list[dict], *, inv_back: str = "shop") -> InlineKeyboardMarkup:
    """inv_back: \"shop\" — к магазину; \"main\" — на главный экран (в походе)."""
    rows: list[list[InlineKeyboardButton]] = []
    for idx, it in enumerate(inv):
        if it.get("kind") == "item" and it.get("effect") == "heal":
            rows.append(
                [
                    InlineKeyboardButton(
                        text=f"Выпить: {it.get('name', '?')[:24]}",
                        callback_data=f"inv:u:{idx}:{inv_back}",
                    )
                ]
            )
        elif it.get("kind") == "weapon":
            rows.append(
                [
                    InlineKeyboardButton(
                        text=f"Надеть меч: {it.get('name', '?')[:20]}",
                        callback_data=f"inv:e:{idx}:{inv_back}",
                    )
                ]
            )
        elif it.get("kind") == "armor":
            rows.append(
                [
                    InlineKeyboardButton(
                        text=f"Надеть броню: {it.get('name', '?')[:19]}",
                        callback_data=f"inv:e:{idx}:{inv_back}",
                    )
                ]
            )
    if inv_back == "main":
        rows.append([InlineKeyboardButton(text="Назад", callback_data="nav:main")])
    else:
        rows.append([InlineKeyboardButton(text="К магазину", callback_data="nav:shop")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def kb_dungeons(
    current_act: int = 1,
    next_act_unlocked: bool = False,
    third_act_unlocked: bool = False,
    fourth_act_unlocked: bool = False,
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    if current_act not in (1, 2, 3):
        current_act = 1
    max_open_act = (
        4
        if fourth_act_unlocked
        else 3
        if third_act_unlocked
        else 2
        if next_act_unlocked
        else 1
    )
    for d in DUNGEONS:
        if d.act != current_act:
            continue
        if d.act > max_open_act:
            continue
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"{d.title} {_dungeon_skulls(d.danger)}",
                    callback_data=f"run:{d.id}",
                )
            ]
        )
    nav: list[InlineKeyboardButton] = []
    if current_act > 1:
        nav.append(
            InlineKeyboardButton(
                text=f"← Акт {current_act - 1}",
                callback_data=f"act:view:{current_act - 1}",
            )
        )
    if current_act < max_open_act:
        nav.append(
            InlineKeyboardButton(
                text=f"Акт {current_act + 1} →",
                callback_data=f"act:view:{current_act + 1}",
            )
        )
    elif current_act == max_open_act and max_open_act < 3:
        nav.append(
            InlineKeyboardButton(
                text=f"Акт {max_open_act + 1} 🔒",
                callback_data="act:locked",
            )
        )
    if nav:
        rows.append(nav)
    if current_act == 4:
        rows.append([InlineKeyboardButton(text="Подземелья акта IV пока недоступны", callback_data="act:empty")])
    rows.append([InlineKeyboardButton(text="Назад", callback_data="nav:main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
