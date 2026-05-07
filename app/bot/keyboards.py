"""Inline-клавиатуры Telegram (разметка кнопок), без запросов к БД."""

from __future__ import annotations

from typing import Any

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.game.dungeons import DUNGEONS


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


def kb_main(
    expedition: dict | None = None,
    rest: dict[str, Any] | None = None,
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
    else:
        rows.append(
            [InlineKeyboardButton(text="Подземелья", callback_data="nav:dungeons")]
        )
        rows.append([InlineKeyboardButton(text="Магазин", callback_data="nav:shop")])
        rows.append([InlineKeyboardButton(text="Инвентарь", callback_data="nav:inv")])
        rows.append(
            [InlineKeyboardButton(text="Отдых (6 ч)", callback_data="rest:start")]
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)


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
            InlineKeyboardButton(text="Инвентарь", callback_data="shop:inv"),
            InlineKeyboardButton(text="Назад", callback_data="nav:main"),
        ]
    )
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
    if inv_back == "main":
        rows.append([InlineKeyboardButton(text="Назад", callback_data="nav:main")])
    else:
        rows.append([InlineKeyboardButton(text="К магазину", callback_data="nav:shop")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def kb_dungeons() -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for d in DUNGEONS:
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"{d.title} (~{(d.duration_seconds + 59) // 60} мин)",
                    callback_data=f"run:{d.id}",
                )
            ]
        )
    rows.append([InlineKeyboardButton(text="Назад", callback_data="nav:main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
