from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List, Dict


def build_youtube_video_keyboard(video_id: str, formats: List[Dict]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for fmt in formats:
        label = f"🎬 {fmt['quality']}"
        if fmt.get("size"):
            label += f" ({fmt['size']})"
        builder.button(
            text=label,
            callback_data=f"yt_video:{video_id}:{fmt['format_id']}"
        )
    builder.button(text="🎵 MP3 128kbps", callback_data=f"yt_audio:{video_id}:128")
    builder.button(text="🎵 MP3 192kbps", callback_data=f"yt_audio:{video_id}:192")
    builder.button(text="🎵 MP3 320kbps", callback_data=f"yt_audio:{video_id}:320")
    builder.button(text="❌ إلغاء", callback_data="cancel")
    builder.adjust(2, 2, 3, 1)
    return builder.as_markup()


def build_force_sub_keyboard(channels: List[Dict]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for ch in channels:
        builder.button(
            text=f"📢 {ch.get('title', ch['channel_id'])}",
            url=ch.get("invite_link", f"https://t.me/{ch['channel_id'].lstrip('@')}")
        )
    builder.button(text="✅ تحقق من الاشتراك", callback_data="check_sub")
    builder.adjust(1)
    return builder.as_markup()


def build_media_actions_keyboard(url: str, platform: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if platform in ("instagram", "tiktok", "twitter", "pinterest"):
        builder.button(text="🎬 تحميل فيديو", callback_data=f"dl_video:{url[:200]}")
        builder.button(text="🎵 تحميل MP3", callback_data=f"dl_audio:{url[:200]}")
    builder.adjust(2)
    return builder.as_markup()


def build_cancel_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ إلغاء", callback_data="cancel")
    return builder.as_markup()


def build_admin_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📊 الإحصائيات", callback_data="admin_stats")
    builder.button(text="👥 المستخدمون", callback_data="admin_users")
    builder.button(text="📋 السجلات", callback_data="admin_logs")
    builder.button(text="📢 إرسال جماعي", callback_data="admin_broadcast")
    builder.adjust(2)
    return builder.as_markup()


def build_confirm_keyboard(action: str, data: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ تأكيد", callback_data=f"confirm:{action}:{data}")
    builder.button(text="❌ إلغاء", callback_data="cancel")
    builder.adjust(2)
    return builder.as_markup()


def build_back_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 رجوع", callback_data="back_main")
    return builder.as_markup()
