import logging
from typing import Any, Callable, Dict, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from bot.database.repositories.user_repo import upsert_user

logger = logging.getLogger(__name__)


class UserRegisterMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: Dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        if user and not user.is_bot:
            try:
                await upsert_user(
                    user_id=user.id,
                    username=user.username or "",
                    full_name=user.full_name or "",
                    language_code=user.language_code or "ar",
                )
            except Exception as e:
                logger.error(f"User register middleware error: {e}")
        return await handler(event, data)
