"""Общий каталог магазинных товаров без зависимостей от БД."""

from __future__ import annotations

from typing import Any

WEAPONS_BY_ACT: dict[int, list[dict[str, Any]]] = {
    1: [
        {"kind": "weapon", "name": "Крестьянский меч", "price": 55, "attack": 2},
        {"kind": "weapon", "name": "Короткий меч дружинника", "price": 80, "attack": 3},
        {"kind": "weapon", "name": "Пехотный меч", "price": 105, "attack": 4},
    ],
    2: [
        {"kind": "weapon", "name": "Армейский меч", "price": 140, "attack": 5},
        {"kind": "weapon", "name": "Полуторный меч", "price": 170, "attack": 6},
        {"kind": "weapon", "name": "Закаленный меч", "price": 200, "attack": 7},
    ],
    3: [
        {"kind": "weapon", "name": "Рыцарский меч", "price": 250, "attack": 8},
        {"kind": "weapon", "name": "Двуручный меч", "price": 300, "attack": 10},
        {"kind": "weapon", "name": "Турнирный меч", "price": 275, "attack": 9},
    ],
}

ARMOR_BY_ACT: dict[int, list[dict[str, Any]]] = {
    1: [
        {"kind": "armor", "name": "Стеганка", "price": 50, "defense": 2},
        {"kind": "armor", "name": "Кожаный доспех", "price": 75, "defense": 3},
        {"kind": "armor", "name": "Кольчужная рубаха", "price": 105, "defense": 4},
    ],
    2: [
        {"kind": "armor", "name": "Кольчуга с наплечниками", "price": 140, "defense": 6},
        {"kind": "armor", "name": "Бригантина", "price": 170, "defense": 7},
        {"kind": "armor", "name": "Латная кираса", "price": 205, "defense": 8},
    ],
    3: [
        {"kind": "armor", "name": "Полный латный доспех", "price": 255, "defense": 10},
        {"kind": "armor", "name": "Гвардейские латы", "price": 295, "defense": 12},
        {"kind": "armor", "name": "Осадный доспех", "price": 335, "defense": 14},
    ],
}

ITEMS_BY_ACT: dict[int, list[dict[str, Any]]] = {
    1: [
        {"kind": "item", "name": "Перевязочный набор", "price": 18, "effect": "heal", "value": 12},
        {"kind": "item", "name": "Сухпаек", "price": 24, "effect": "heal", "value": 16},
        {"kind": "item", "name": "Фляга воды", "price": 20, "effect": "heal", "value": 14},
    ],
    2: [
        {"kind": "item", "name": "Травяная мазь", "price": 32, "effect": "heal", "value": 22},
        {"kind": "item", "name": "Полевой паек", "price": 36, "effect": "heal", "value": 25},
        {"kind": "item", "name": "Бульон в котелке", "price": 34, "effect": "heal", "value": 24},
    ],
    3: [
        {"kind": "item", "name": "Хирургический набор", "price": 48, "effect": "heal", "value": 34},
        {"kind": "item", "name": "Крепкий мясной паек", "price": 44, "effect": "heal", "value": 31},
        {"kind": "item", "name": "Настой из трав", "price": 46, "effect": "heal", "value": 33},
    ],
}

