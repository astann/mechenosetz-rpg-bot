"""Очистка таблицы users и сброс витрины магазина.

Запуск из корня репозитория:
  PYTHONPATH=. python3 scripts/clear_players.py
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import db


async def main() -> None:
    await db.init_db()
    await db.clear_all_players(reset_shop=True)
    print("Готово: все игроки удалены, shop_state сброшен.")


if __name__ == "__main__":
    asyncio.run(main())
