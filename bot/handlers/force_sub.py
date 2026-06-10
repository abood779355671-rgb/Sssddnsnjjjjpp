import logging
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from bot.middlewares.force_sub import check_user_subscribed
from bot.database.repositories.settings_repo import get_force_sub_channels
from bot.utils.messages import Messages
from bot.cache.memory_cache import memory_cache

logger = logging.getLogger(__name__)
router = Router(name="force_sub")


@router.callback_query(F.data == "check_sub")
async def cb_check_sub(call: CallbackQuery, bot: Bot):
    user_id = call.from_user.id
    channels = await get_force_sub_channels()

    if not channels:
        await call.answer(Messages.FORCE_SUB_SUCCESS, show_alert=True)
        await memory_cache.set(f"subscribed:{user_id}", True, ttl=300)
        await call.message.delete()
        return

    not_subbed = await check_user_subscribed(bot, user_id, channels)
    if not_subbed:
        await call.answer(Messages.FORCE_SUB_FAILED, show_alert=True)
    else:
        await memory_cache.set(f"subscribed:{user_id}", True, ttl=300)
        await call.answer(Messages.FORCE_SUB_SUCCESS, show_alert=True)
        try:
            await call.message.delete()
        except Exception:
            pass
