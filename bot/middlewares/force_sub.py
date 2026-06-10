import logging
from typing import Any, Callable, Dict, Awaitable, List
from aiogram import BaseMiddleware, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest
from bot.database.repositories.settings_repo import get_force_sub_channels, get_setting
from bot.utils.messages import Messages
from bot.utils.keyboards import build_force_sub_keyboard
from bot.cache.memory_cache import memory_cache

logger = logging.getLogger(__name__)


async def check_user_subscribed(bot: Bot, user_id: int, channels: List[Dict]) -> List[Dict]:
    """Returns list of channels user is NOT subscribed to."""
    not_subbed = []
    for ch in channels:
        try:
            member = await bot.get_chat_member(ch["channel_id"], user_id)
            if member.status in ("left", "kicked", "banned"):
                not_subbed.append(ch)
        except (TelegramForbiddenError, TelegramBadRequest) as e:
            logger.warning(f"Cannot check membership for {ch['channel_id']}: {e}")
        except Exception as e:
            logger.error(f"Error checking membership: {e}")
    return not_subbed


class ForceSubMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: Dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        if not user:
            return await handler(event, data)

        bot: Bot = data["bot"]
        user_id = user.id

        # Check if force sub is enabled
        enabled_key = "force_sub_enabled"
        is_enabled = await memory_cache.get(enabled_key)
        if is_enabled is None:
            is_enabled = await get_setting("force_sub_enabled", True)
            await memory_cache.set(enabled_key, is_enabled, ttl=60)

        if not is_enabled:
            return await handler(event, data)

        cache_key = "force_sub_channels"
        channels = await memory_cache.get(cache_key)
        if channels is None:
            channels = await get_force_sub_channels()
            await memory_cache.set(cache_key, channels, ttl=300)

        if not channels:
            return await handler(event, data)

        sub_cache_key = f"subscribed:{user_id}"
        is_subbed = await memory_cache.get(sub_cache_key)

        if not is_subbed:
            not_subbed = await check_user_subscribed(bot, user_id, channels)
            if not_subbed:
                channel_lines = "\n".join(
                    f"• {ch.get('title', ch['channel_id'])}" for ch in not_subbed
                )
                text = Messages.FORCE_SUB.format(channels=channel_lines)
                kb = build_force_sub_keyboard(not_subbed)
                if isinstance(event, Message):
                    await event.answer(text, reply_markup=kb, parse_mode="HTML")
                elif isinstance(event, CallbackQuery):
                    await event.message.answer(text, reply_markup=kb, parse_mode="HTML")
                    await event.answer()
                return
            else:
                await memory_cache.set(sub_cache_key, True, ttl=300)

        return await handler(event, data)
