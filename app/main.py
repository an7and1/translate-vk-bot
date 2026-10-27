"""Точка входа VK-бота-переводчика."""
import asyncio
import logging

from vkbottle.bot import Bot

from app.bot.handlers import register_handlers
from app.config import get_settings
from app.db.session import init_db


async def run() -> None:
    settings = get_settings()
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    log = logging.getLogger(__name__)

    await init_db()

    bot = Bot(token=settings.vk_token)
    register_handlers(bot)

    log.info("Translate VK Bot is starting ...")
    await bot.run_polling()


if __name__ == "__main__":
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("\nБот остановлен.")