import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from bot.database.mongo import get_db

logger = logging.getLogger(__name__)


async def get_user(user_id: int) -> Optional[Dict]:
    db = await get_db()
    return await db.users.find_one({"user_id": user_id})


async def upsert_user(user_id: int, username: str, full_name: str, language_code: str = "ar") -> Dict:
    db = await get_db()
    now = datetime.now(timezone.utc)
    result = await db.users.find_one_and_update(
        {"user_id": user_id},
        {
            "$set": {
                "username": username,
                "full_name": full_name,
                "language_code": language_code,
                "last_seen": now,
            },
            "$setOnInsert": {
                "user_id": user_id,
                "created_at": now,
                "is_banned": False,
                "total_downloads": 0,
                "ban_reason": None,
            }
        },
        upsert=True,
        return_document=True
    )
    return result


async def ban_user(user_id: int, reason: str = "No reason") -> bool:
    db = await get_db()
    result = await db.users.update_one(
        {"user_id": user_id},
        {"$set": {"is_banned": True, "ban_reason": reason, "banned_at": datetime.now(timezone.utc)}}
    )
    return result.matched_count > 0


async def unban_user(user_id: int) -> bool:
    db = await get_db()
    result = await db.users.update_one(
        {"user_id": user_id},
        {"$set": {"is_banned": False, "ban_reason": None}}
    )
    return result.matched_count > 0


async def is_banned(user_id: int) -> bool:
    db = await get_db()
    user = await db.users.find_one({"user_id": user_id, "is_banned": True})
    return user is not None


async def get_all_users(skip: int = 0, limit: int = 100) -> List[Dict]:
    db = await get_db()
    cursor = db.users.find({}, {"user_id": 1, "username": 1, "full_name": 1, "is_banned": 1}).skip(skip).limit(limit)
    return await cursor.to_list(length=limit)


async def get_user_count() -> int:
    db = await get_db()
    return await db.users.count_documents({})


async def get_banned_count() -> int:
    db = await get_db()
    return await db.users.count_documents({"is_banned": True})


async def increment_downloads(user_id: int):
    db = await get_db()
    await db.users.update_one(
        {"user_id": user_id},
        {"$inc": {"total_downloads": 1}}
    )


async def get_all_user_ids() -> List[int]:
    db = await get_db()
    cursor = db.users.find({"is_banned": False}, {"user_id": 1})
    docs = await cursor.to_list(length=None)
    return [d["user_id"] for d in docs]
