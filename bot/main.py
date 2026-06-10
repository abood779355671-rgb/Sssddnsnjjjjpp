import asyncio
import logging
import sys
import os
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import config
from bot.database.mongo import init_db, close_db
from bot.cache.redis_cache import init_redis, close_redis
from bot.queue.task_queue import download_queue
from bot.middlewares.user_register import UserRegisterMiddleware
from bot.middlewares.ban_check import BanCheckMiddleware
from bot.middlewares.anti_spam import AntiSpamMiddleware
from bot.middlewares.force_sub import ForceSubMiddleware
from bot.handlers import start, download, youtube, admin, force_sub
from bot.utils.file_utils import ensure_dir

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL, logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(config.LOG_FILE, encoding="utf-8"),
    ]
)
logger = logging.getLogger(__name__)


async def on_startup(bot: Bot):
    logger.info("Starting bot...")
    ensure_dir(config.TEMP_DIR)
    await init_db()
    await init_redis()
    await download_queue.start()
    me = await bot.get_me()
    logger.info(f"Bot started: @{me.username} ({me.id})")


async def on_shutdown(bot: Bot):
    logger.info("Shutting down bot...")
    await download_queue.stop()
    await close_db()
    await close_redis()
    logger.info("Bot stopped.")


async def main():
    if not config.BOT_TOKEN:
        logger.critical("BOT_TOKEN is not set. Please set it in .env file.")
        sys.exit(1)

    if not config.ADMIN_IDS:
        logger.warning("ADMIN_IDS is not set. Admin commands will be inaccessible.")

    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Register startup/shutdown
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Middlewares (order matters)
    dp.message.middleware(UserRegisterMiddleware())
    dp.message.middleware(BanCheckMiddleware())
    dp.message.middleware(AntiSpamMiddleware())
    dp.message.middleware(ForceSubMiddleware())
    dp.callback_query.middleware(UserRegisterMiddleware())
    dp.callback_query.middleware(BanCheckMiddleware())

    # Routers
    dp.include_router(start.router)
    dp.include_router(force_sub.router)
    dp.include_router(admin.router)
    dp.include_router(youtube.router)
    dp.include_router(download.router)

    logger.info("Starting polling...")
    await dp.start_polling(bot, allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    asyncio.run(main())
