"""Регистрация всех Telegram-хендлеров."""

from __future__ import annotations

from aiogram import Router

from app.bot.handlers import common, dungeons, flee, inventory, rest, shop

router = Router()
router.include_router(common.router)
router.include_router(dungeons.router)
router.include_router(shop.router)
router.include_router(inventory.router)
router.include_router(flee.router)
router.include_router(rest.router)

__all__ = ["router"]
