import logging
from typing import Any, Callable, Dict, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, Update
from bot.database.repositories.user_repo import is_banned
from bot.utils.messages import Messages
from bot.cache.memory_cache import memory_cache

logger = logging.getLogger(__name__)


class BanCheckMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: Dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        if not user:
            return await handler(event, data)

        user_id = user.id
        cache_key = f"banned:{user_id}"
        cached = await memory_cache.get(cache_key)

        if cached is None:
            banned = await is_banned(user_id)
            await memory_cache.set(cache_key, banned, ttl=300)
        else:
            banned = cached

        if banned:
            if isinstance(event, Message):
                await event.answer(Messages.BANNED)
            elif isinstance(event, CallbackQuery):
                await event.answer(Messages.BANNED, show_alert=True)
            return

        return await handler(event, data)
