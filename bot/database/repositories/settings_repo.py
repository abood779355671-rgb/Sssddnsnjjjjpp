import logging
from typing import Optional, List, Dict, Any
from bot.database.mongo import get_db

logger = logging.getLogger(__name__)


async def get_setting(key: str, default=None) -> Any:
    db = await get_db()
    doc = await db.settings.find_one({"key": key})
    return doc["value"] if doc else default


async def set_setting(key: str, value: Any):
    db = await get_db()
    await db.settings.update_one(
        {"key": key},
        {"$set": {"key": key, "value": value}},
        upsert=True
    )


async def add_force_sub_channel(channel_id: str, title: str, invite_link: str) -> bool:
    db = await get_db()
    try:
        await db.force_subs.update_one(
            {"channel_id": channel_id},
            {"$set": {"channel_id": channel_id, "title": title, "invite_link": invite_link}},
            upsert=True
        )
        return True
    except Exception as e:
        logger.error(f"Error adding force sub channel: {e}")
        return False


async def remove_force_sub_channel(channel_id: str) -> bool:
    db = await get_db()
    result = await db.force_subs.delete_one({"channel_id": channel_id})
    return result.deleted_count > 0


async def get_force_sub_channels() -> List[Dict]:
    db = await get_db()
    cursor = db.force_subs.find({})
    return await cursor.to_list(length=None)


async def log_error(user_id: Optional[int], error: str, context: str = ""):
    db = await get_db()
    from datetime import datetime, timezone
    await db.error_logs.insert_one({
        "user_id": user_id,
        "error": str(error)[:2000],
        "context": context[:500],
        "created_at": datetime.now(timezone.utc),
    })


async def get_recent_errors(limit: int = 20) -> List[Dict]:
    db = await get_db()
    cursor = db.error_logs.find({}).sort("created_at", -1).limit(limit)
    return await cursor.to_list(length=limit)
