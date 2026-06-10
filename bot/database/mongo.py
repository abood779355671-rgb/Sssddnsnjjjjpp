import logging
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional
from bot.config import config

logger = logging.getLogger(__name__)

_client: Optional[AsyncIOMotorClient] = None
_db: Optional[AsyncIOMotorDatabase] = None


async def init_db() -> AsyncIOMotorDatabase:
    global _client, _db
    _client = AsyncIOMotorClient(
        config.MONGO_URI,
        serverSelectionTimeoutMS=5000,
        maxPoolSize=50,
        minPoolSize=5,
    )
    _db = _client[config.MONGO_DB]
    await _create_indexes()
    logger.info("MongoDB connected successfully.")
    return _db


async def get_db() -> AsyncIOMotorDatabase:
    global _db
    if _db is None:
        await init_db()
    return _db


async def close_db():
    global _client
    if _client:
        _client.close()
        logger.info("MongoDB connection closed.")


async def ping_db() -> bool:
    try:
        db = await get_db()
        await db.command("ping")
        return True
    except Exception:
        return False


async def _create_indexes():
    db = await get_db()
    # Users
    await db.users.create_index("user_id", unique=True)
    await db.users.create_index("username")
    await db.users.create_index("is_banned")
    await db.users.create_index("created_at")

    # Downloads
    await db.downloads.create_index("user_id")
    await db.downloads.create_index("platform")
    await db.downloads.create_index("created_at")
    await db.downloads.create_index("url_hash")

    # Force sub channels
    await db.force_subs.create_index("channel_id", unique=True)

    # Settings
    await db.settings.create_index("key", unique=True)

    # Error logs
    await db.error_logs.create_index("created_at")
    await db.error_logs.create_index("user_id")

    logger.info("MongoDB indexes created.")
