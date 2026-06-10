import asyncio
import logging
from datetime import datetime, timezone
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from bot.config import config
from bot.utils.messages import Messages
from bot.utils.keyboards import build_admin_keyboard
from bot.database.repositories.user_repo import (
    get_user_count, get_banned_count, ban_user, unban_user,
    get_user, get_all_user_ids
)
from bot.database.repositories.download_repo import get_download_count, get_today_download_count, get_top_platform
from bot.database.repositories.settings_repo import (
    get_recent_errors, add_force_sub_channel, remove_force_sub_channel,
    get_force_sub_channels, get_setting, set_setting
)
from bot.database.mongo import ping_db
from bot.cache.redis_cache import ping_redis
from bot.queue.task_queue import download_queue

logger = logging.getLogger(__name__)
router = Router(name="admin")

_start_time = datetime.now(timezone.utc)


def is_admin(user_id: int) -> bool:
    return user_id in config.ADMIN_IDS


def admin_only(func):
    async def wrapper(message: Message, *args, **kwargs):
        if not is_admin(message.from_user.id):
            await message.answer(Messages.ADMIN_ONLY)
            return
        return await func(message, *args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper


def get_uptime() -> str:
    elapsed = datetime.now(timezone.utc) - _start_time
    h = int(elapsed.total_seconds() // 3600)
    m = int((elapsed.total_seconds() % 3600) // 60)
    return f"{h}h {m}m"


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer(Messages.ADMIN_ONLY)
        return
    await message.answer(
        "🔐 <b>لوحة الإدارة</b>",
        reply_markup=build_admin_keyboard(),
        parse_mode="HTML"
    )


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer(Messages.ADMIN_ONLY)
        return
    await _send_stats(message)


@router.callback_query(F.data == "admin_stats")
async def cb_admin_stats(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer(Messages.ADMIN_ONLY, show_alert=True)
        return
    await _send_stats(call.message)
    await call.answer()


async def _send_stats(message: Message):
    users = await get_user_count()
    downloads = await get_download_count()
    today_dl = await get_today_download_count()
    top_platform = await get_top_platform()
    banned = await get_banned_count()
    mongo_ok = await ping_db()
    redis_ok = await ping_redis()
    uptime = get_uptime()
    active = download_queue.get_active_count()

    text = Messages.STATS_TEMPLATE.format(
        users=users,
        downloads=downloads,
        today_downloads=today_dl,
        top_platform=top_platform,
        banned=banned,
        mongo_status="✅ متصل" if mongo_ok else "❌ منقطع",
        redis_status="✅ متصل" if redis_ok else "❌ منقطع",
        uptime=uptime,
        active_tasks=active,
    )
    await message.answer(text, parse_mode="HTML")


@router.message(Command("users"))
async def cmd_users(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer(Messages.ADMIN_ONLY)
        return
    count = await get_user_count()
    banned = await get_banned_count()
    await message.answer(
        f"👥 <b>المستخدمون</b>\n\n"
        f"• الكلي: {count}\n"
        f"• المحظورون: {banned}\n"
        f"• النشطون: {count - banned}",
        parse_mode="HTML"
    )


@router.message(Command("ban"))
async def cmd_ban(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer(Messages.ADMIN_ONLY)
        return
    args = message.text.split(maxsplit=2)
    if len(args) < 2 or not args[1].isdigit():
        await message.answer("❌ الاستخدام: /ban <user_id> [reason]")
        return
    user_id = int(args[1])
    reason = args[2] if len(args) > 2 else "No reason"
    user = await get_user(user_id)
    if not user:
        await message.answer(Messages.USER_NOT_FOUND)
        return
    success = await ban_user(user_id, reason)
    if success:
        from bot.cache.memory_cache import memory_cache
        await memory_cache.delete(f"banned:{user_id}")
        await message.answer(Messages.BAN_SUCCESS.format(user_id=user_id), parse_mode="HTML")
        try:
            await message.bot.send_message(user_id, Messages.BANNED)
        except Exception:
            pass
    else:
        await message.answer("❌ فشل الحظر.")


@router.message(Command("unban"))
async def cmd_unban(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer(Messages.ADMIN_ONLY)
        return
    args = message.text.split(maxsplit=1)
    if len(args) < 2 or not args[1].isdigit():
        await message.answer("❌ الاستخدام: /unban <user_id>")
        return
    user_id = int(args[1])
    success = await unban_user(user_id)
    if success:
        from bot.cache.memory_cache import memory_cache
        await memory_cache.delete(f"banned:{user_id}")
        await message.answer(Messages.UNBAN_SUCCESS.format(user_id=user_id), parse_mode="HTML")
    else:
        await message.answer(Messages.USER_NOT_FOUND)


@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer(Messages.ADMIN_ONLY)
        return
    text = message.text.split(maxsplit=1)
    if len(text) < 2:
        await message.answer("❌ الاستخدام: /broadcast <النص>")
        return
    broadcast_text = text[1]
    status = await message.answer(Messages.BROADCAST_START)
    user_ids = await get_all_user_ids()

    success = 0
    failed = 0
    for uid in user_ids:
        try:
            await message.bot.send_message(uid, broadcast_text, parse_mode="HTML")
            success += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)

    await status.edit_text(Messages.BROADCAST_DONE.format(success=success, failed=failed))


@router.message(Command("logs"))
async def cmd_logs(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer(Messages.ADMIN_ONLY)
        return
    errors = await get_recent_errors(limit=10)
    if not errors:
        await message.answer("✅ لا توجد أخطاء مسجلة.")
        return
    lines = []
    for e in errors:
        ts = e.get("created_at", "").strftime("%m/%d %H:%M") if e.get("created_at") else "?"
        uid = e.get("user_id", "?")
        err = e.get("error", "")[:80]
        lines.append(f"[{ts}] {uid}: {err}")
    await message.answer(
        "📋 <b>آخر الأخطاء:</b>\n\n" + "\n".join(lines),
        parse_mode="HTML"
    )


@router.message(Command("setforce"))
async def cmd_setforce(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer(Messages.ADMIN_ONLY)
        return
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("❌ الاستخدام: /setforce @channel أو /setforce -100xxxxxxxx")
        return
    channel_id = args[1].strip()
    try:
        chat = await message.bot.get_chat(channel_id)
        invite_link = chat.invite_link or f"https://t.me/{chat.username}" if chat.username else ""
        await add_force_sub_channel(str(chat.id), chat.title, invite_link)
        from bot.cache.memory_cache import memory_cache
        await memory_cache.delete("force_sub_channels")
        await message.answer(Messages.FORCE_SUB_SET.format(channel=chat.title), parse_mode="HTML")
    except Exception as e:
        await message.answer(f"❌ خطأ: {e}")


@router.message(Command("removeforce"))
async def cmd_removeforce(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer(Messages.ADMIN_ONLY)
        return
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("❌ الاستخدام: /removeforce @channel أو /removeforce -100xxxxxxxx")
        return
    channel_id = args[1].strip()
    try:
        chat = await message.bot.get_chat(channel_id)
        removed = await remove_force_sub_channel(str(chat.id))
        from bot.cache.memory_cache import memory_cache
        await memory_cache.delete("force_sub_channels")
        if removed:
            await message.answer(Messages.FORCE_SUB_REMOVED.format(channel=chat.title), parse_mode="HTML")
        else:
            await message.answer("❌ القناة غير موجودة في القائمة.")
    except Exception as e:
        await message.answer(f"❌ خطأ: {e}")


@router.message(Command("forcesubs"))
async def cmd_forcesubs(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer(Messages.ADMIN_ONLY)
        return
    channels = await get_force_sub_channels()
    is_enabled = await get_setting("force_sub_enabled", True)
    status = Messages.FORCE_SUB_STATUS_ON if is_enabled else Messages.FORCE_SUB_STATUS_OFF
    if not channels:
        ch_text = "لا توجد قنوات مُضافة."
    else:
        ch_text = "\n".join(
            f"• {ch.get('title', ch['channel_id'])} — <code>{ch['channel_id']}</code>"
            for ch in channels
        )
    await message.answer(
        Messages.FORCE_SUB_STATUS.format(status=status, channels=ch_text),
        parse_mode="HTML",
        reply_markup=_build_toggle_keyboard(is_enabled),
    )


@router.message(Command("forceon"))
async def cmd_forceon(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer(Messages.ADMIN_ONLY)
        return
    await set_setting("force_sub_enabled", True)
    from bot.cache.memory_cache import memory_cache
    await memory_cache.delete("force_sub_enabled")
    await message.answer(Messages.FORCE_SUB_ENABLED, parse_mode="HTML")


@router.message(Command("forceoff"))
async def cmd_forceoff(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer(Messages.ADMIN_ONLY)
        return
    await set_setting("force_sub_enabled", False)
    from bot.cache.memory_cache import memory_cache
    await memory_cache.delete("force_sub_enabled")
    await message.answer(Messages.FORCE_SUB_DISABLED, parse_mode="HTML")


@router.callback_query(F.data.in_({"toggle_force_on", "toggle_force_off"}))
async def cb_toggle_force(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer(Messages.ADMIN_ONLY, show_alert=True)
        return
    enable = call.data == "toggle_force_on"
    await set_setting("force_sub_enabled", enable)
    from bot.cache.memory_cache import memory_cache
    await memory_cache.delete("force_sub_enabled")
    text = Messages.FORCE_SUB_ENABLED if enable else Messages.FORCE_SUB_DISABLED
    await call.answer(
        "✅ تم التفعيل" if enable else "🔴 تم التعطيل",
        show_alert=True
    )
    await call.message.edit_reply_markup(reply_markup=_build_toggle_keyboard(enable))


def _build_toggle_keyboard(is_enabled: bool):
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    if is_enabled:
        builder.button(text="🔴 تعطيل الاشتراك الإجباري", callback_data="toggle_force_off")
    else:
        builder.button(text="✅ تفعيل الاشتراك الإجباري", callback_data="toggle_force_on")
    builder.adjust(1)
    return builder.as_markup()
