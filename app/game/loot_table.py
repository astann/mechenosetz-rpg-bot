"""Таблица лута по актам: обычный / редкий / эпический."""

from __future__ import annotations

import random
from typing import Any

_RARITY_WEIGHTS: tuple[tuple[str, int], ...] = (
    ("common", 74),
    ("rare", 21),
    ("epic", 5),
)

_LOOT_BY_ACT: dict[int, dict[str, tuple[dict[str, Any], ...]]] = {
    1: {
        "common": (
            {"kind": "weapon", "name": "Старый меч стражи", "attack": 2},
            {"kind": "weapon", "name": "Меч ополченца", "attack": 3},
            {"kind": "weapon", "name": "Казарменный клинок", "attack": 4},
            {"kind": "armor", "name": "Подбитый гамбезон", "defense": 2},
            {"kind": "armor", "name": "Кожаный панцирь", "defense": 3},
            {"kind": "armor", "name": "Усиленная куртка", "defense": 4},
            {"kind": "item", "name": "Походные бинты", "effect": "heal", "value": 12},
            {"kind": "item", "name": "Солонина в мешке", "effect": "heal", "value": 14},
            {"kind": "item", "name": "Крепкий бульон", "effect": "heal", "value": 16},
        ),
        "rare": (
            {"kind": "weapon", "name": "Клинок дозорного", "attack": 4},
            {"kind": "weapon", "name": "Меч сотника", "attack": 5},
            {"kind": "weapon", "name": "Длинный меч караула", "attack": 6},
            {"kind": "armor", "name": "Кольчужный жилет", "defense": 4},
            {"kind": "armor", "name": "Укрепленная куртка стражи", "defense": 5},
            {"kind": "armor", "name": "Стражная кольчуга", "defense": 6},
            {"kind": "item", "name": "Набор хирурга-ученика", "effect": "heal", "value": 20},
            {"kind": "item", "name": "Полевой узел перевязки", "effect": "heal", "value": 22},
            {"kind": "item", "name": "Сундук с припасами", "effect": "heal", "value": 24},
        ),
        "epic": (
            {"kind": "weapon", "name": "Меч старого капитана", "attack": 6},
            {"kind": "weapon", "name": "Длинный меч арсенала", "attack": 7},
            {"kind": "weapon", "name": "Клинок воеводы", "attack": 8},
            {"kind": "armor", "name": "Панцирь ветерана", "defense": 6},
            {"kind": "armor", "name": "Капитанская бригантина", "defense": 7},
            {"kind": "armor", "name": "Латы сотенного", "defense": 8},
            {"kind": "item", "name": "Большой полевой набор", "effect": "heal", "value": 28},
            {"kind": "item", "name": "Сумка военного лекаря", "effect": "heal", "value": 30},
            {"kind": "item", "name": "Армейский медицинский ящик", "effect": "heal", "value": 32},
        ),
    },
    2: {
        "common": (
            {"kind": "weapon", "name": "Кавалерийский меч", "attack": 7},
            {"kind": "weapon", "name": "Сабля гарнизона", "attack": 8},
            {"kind": "weapon", "name": "Меч ротного", "attack": 9},
            {"kind": "armor", "name": "Укрепленная кольчуга", "defense": 8},
            {"kind": "armor", "name": "Бригантина дозора", "defense": 9},
            {"kind": "armor", "name": "Пластинчатый жилет", "defense": 11},
            {"kind": "item", "name": "Медицинская сумка", "effect": "heal", "value": 29},
            {"kind": "item", "name": "Котелок питательного отвара", "effect": "heal", "value": 32},
            {"kind": "item", "name": "Плотный рацион", "effect": "heal", "value": 35},
        ),
        "rare": (
            {"kind": "weapon", "name": "Полуторный меч рейтара", "attack": 9},
            {"kind": "weapon", "name": "Меч караульного офицера", "attack": 11},
            {"kind": "weapon", "name": "Клинок фортификаций", "attack": 12},
            {"kind": "armor", "name": "Заклепанная бригантина", "defense": 11},
            {"kind": "armor", "name": "Латы дозорной сотни", "defense": 12},
            {"kind": "armor", "name": "Кираса бастиона", "defense": 13},
            {"kind": "item", "name": "Полевой лекарский набор", "effect": "heal", "value": 40},
            {"kind": "item", "name": "Сундук перевязок", "effect": "heal", "value": 45},
            {"kind": "item", "name": "Набор военного врача", "effect": "heal", "value": 51},
        ),
        "epic": (
            {"kind": "weapon", "name": "Командирский меч", "attack": 13},
            {"kind": "weapon", "name": "Меч бастионного маршала", "attack": 15},
            {"kind": "weapon", "name": "Клеймор штурмового полка", "attack": 16},
            {"kind": "armor", "name": "Грудной латный доспех", "defense": 15},
            {"kind": "armor", "name": "Маршальская кираса", "defense": 16},
            {"kind": "armor", "name": "Панцирь полководца", "defense": 17},
            {"kind": "item", "name": "Хирургический набор мастера", "effect": "heal", "value": 56},
            {"kind": "item", "name": "Лекарский ящик коменданта", "effect": "heal", "value": 61},
            {"kind": "item", "name": "Мобильный лазарет", "effect": "heal", "value": 67},
        ),
    },
    3: {
        "common": (
            {"kind": "weapon", "name": "Рыцарский клинок", "attack": 16},
            {"kind": "weapon", "name": "Меч бастионного сержанта", "attack": 18},
            {"kind": "weapon", "name": "Осадный фламберг", "attack": 20},
            {"kind": "armor", "name": "Тяжелый латный доспех", "defense": 20},
            {"kind": "armor", "name": "Пластинчатые латы гарнизона", "defense": 24},
            {"kind": "armor", "name": "Панцирь штурмовой сотни", "defense": 28},
            {"kind": "item", "name": "Осадный медицинский набор", "effect": "heal", "value": 62},
            {"kind": "item", "name": "Плотный армейский рацион", "effect": "heal", "value": 66},
            {"kind": "item", "name": "Крепостной набор снабжения", "effect": "heal", "value": 70},
        ),
        "rare": (
            {"kind": "weapon", "name": "Двуручный меч гвардии", "attack": 22},
            {"kind": "weapon", "name": "Клеймор черной стражи", "attack": 24},
            {"kind": "weapon", "name": "Штурмовой эспадон", "attack": 26},
            {"kind": "armor", "name": "Гвардейские латы бастиона", "defense": 28},
            {"kind": "armor", "name": "Латы командира стены", "defense": 30},
            {"kind": "armor", "name": "Чернопластинчатая кираса", "defense": 32},
            {"kind": "item", "name": "Комплект полевого хирурга", "effect": "heal", "value": 88},
            {"kind": "item", "name": "Сумка крепостного медика", "effect": "heal", "value": 96},
            {"kind": "item", "name": "Военно-медицинский сундук", "effect": "heal", "value": 104},
        ),
        "epic": (
            {"kind": "weapon", "name": "Клеймор Черной Горы", "attack": 30},
            {"kind": "weapon", "name": "Меч палача бастиона", "attack": 32},
            {"kind": "weapon", "name": "Черностальной двуручник", "attack": 34},
            {"kind": "armor", "name": "Осадный панцирь маршала", "defense": 36},
            {"kind": "armor", "name": "Черностальной комплект", "defense": 40},
            {"kind": "armor", "name": "Латы верховного воеводы", "defense": 44},
            {"kind": "item", "name": "Комплект военного лазарета", "effect": "heal", "value": 116},
            {"kind": "item", "name": "Полковой набор выживания", "effect": "heal", "value": 128},
            {"kind": "item", "name": "Экстренный комплект цитадели", "effect": "heal", "value": 140},
        ),
    },
}


def _pick_rarity(rng: random.Random) -> str:
    names = [name for name, _ in _RARITY_WEIGHTS]
    weights = [w for _, w in _RARITY_WEIGHTS]
    return str(rng.choices(names, weights=weights, k=1)[0])


def roll_loot(*, act: int, rng: random.Random | None = None) -> dict[str, Any]:
    r = rng or random.Random()
    table = _LOOT_BY_ACT.get(act) or _LOOT_BY_ACT[1]
    rarity = _pick_rarity(r)
    entry = dict(r.choice(table[rarity]))
    entry["rarity"] = rarity
    return entry

