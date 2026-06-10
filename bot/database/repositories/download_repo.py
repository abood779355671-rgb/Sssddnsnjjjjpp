import hashlib
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, List
from bot.database.mongo import get_db

logger = logging.getLogger(__name__)


def _hash_url(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()


async def log_download(user_id: int, platform: str, url: str, media_type: str,
                        file_size: int = 0, quality: str = "", success: bool = True) -> str:
    db = await get_db()
    doc = {
        "user_id": user_id,
        "platform": platform,
        "url": url,
        "url_hash": _hash_url(url),
        "media_type": media_type,
        "file_size": file_size,
        "quality": quality,
        "success": success,
        "created_at": datetime.now(timezone.utc),
    }
    result = await db.downloads.insert_one(doc)
    return str(result.inserted_id)


async def get_download_count() -> int:
    db = await get_db()
    return await db.downloads.count_documents({})


async def get_today_download_count() -> int:
    db = await get_db()
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    return await db.downloads.count_documents({"created_at": {"$gte": today}})


async def get_platform_stats() -> Dict[str, int]:
    db = await get_db()
    pipeline = [
        {"$group": {"_id": "$platform", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    cursor = db.downloads.aggregate(pipeline)
    results = await cursor.to_list(length=None)
    return {r["_id"]: r["count"] for r in results}


async def get_top_platform() -> str:
    stats = await get_platform_stats()
    if not stats:
        return "لا يوجد"
    return max(stats, key=stats.get)


async def get_cached_file_id(url_hash: str) -> Optional[str]:
    """Get cached Telegram file_id for a URL."""
    db = await get_db()
    doc = await db.file_cache.find_one({"url_hash": url_hash})
    return doc.get("file_id") if doc else None


async def cache_file_id(url_hash: str, file_id: str, platform: str):
    db = await get_db()
    await db.file_cache.update_one(
        {"url_hash": url_hash},
        {"$set": {"file_id": file_id, "platform": platform, "cached_at": datetime.now(timezone.utc)}},
        upsert=True
    )
