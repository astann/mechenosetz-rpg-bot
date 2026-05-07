"""Точка входа: Telegram-бот, polling, фоновый воркер походов."""

from __future__ import annotations

import asyncio
import contextlib
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app import db
from app.bot.handlers import router
from app.bot.worker import expedition_worker
from app.config import BOT_TOKEN

logging.basicConfig(level=logging.INFO)


async def _run() -> None:
    if not BOT_TOKEN:
        print("Set BOT_TOKEN in .env", file=sys.stderr)
        raise SystemExit(1)
    await db.init_db()
    bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_router(router)
    worker = asyncio.create_task(expedition_worker(bot))
    try:
        await dp.start_polling(bot)
    finally:
        worker.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await worker


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()
