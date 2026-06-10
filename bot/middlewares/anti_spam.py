import logging
from typing import Any, Callable, Dict, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from bot.utils.rate_limiter import RateLimiter, FloodControl
from bot.utils.messages import Messages
from bot.config import config

logger = logging.getLogger(__name__)

_rate_limiter = RateLimiter(
    max_requests=config.RATE_LIMIT_MESSAGES,
    window_seconds=config.RATE_LIMIT_WINDOW,
)
_flood_control = FloodControl(max_warnings=5, ban_duration=120)


class AntiSpamMiddleware(BaseMiddleware):
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

        is_temp_banned, remaining = await _flood_control.check(user_id)
        if is_temp_banned:
            if isinstance(event, Message):
                await event.answer(Messages.FLOOD_WAIT.format(seconds=remaining))
            return

        allowed, wait = await _rate_limiter.is_allowed(user_id)
        if not allowed:
            await _flood_control.warn(user_id)
            if isinstance(event, Message):
                await event.answer(Messages.RATE_LIMIT.format(seconds=wait))
            elif isinstance(event, CallbackQuery):
                await event.answer(f"⏳ انتظر {wait} ثانية", show_alert=True)
            return

        return await handler(event, data)
