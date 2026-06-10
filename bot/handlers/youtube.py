import os
import logging
import asyncio
import uuid
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, FSInputFile, BufferedInputFile
from aiogram.exceptions import TelegramBadRequest

from bot.services.downloader import youtube_service
from bot.utils.messages import Messages
from bot.utils.keyboards import build_youtube_video_keyboard
from bot.utils.file_utils import get_file_size, safe_remove, format_file_size
from bot.cache.memory_cache import memory_cache
from bot.database.repositories.user_repo import increment_downloads
from bot.database.repositories.download_repo import log_download
from bot.database.repositories.settings_repo import log_error
from bot.config import config
from bot.queue.task_queue import download_queue

logger = logging.getLogger(__name__)
router = Router(name="youtube")


async def send_youtube_quality_menu(message, url: str, bot: Bot):
    """Analyze YouTube URL and send quality selection menu."""
    status_msg = await message.answer(Messages.YT_ANALYSIS, parse_mode="HTML")

    try:
        info = await youtube_service.get_info(url)
        if not info:
            await status_msg.edit_text(Messages.ERROR_GENERAL, parse_mode="HTML")
            return

        video_id = info["video_id"]
        cache_key = f"yt_info:{video_id}"
        await memory_cache.set(cache_key, {**info, "url": url}, ttl=3600)

        if not info["formats"]:
            await status_msg.edit_text(Messages.ERROR_GENERAL, parse_mode="HTML")
            return

        kb = build_youtube_video_keyboard(video_id, info["formats"])
        caption = Messages.YT_CHOOSE_QUALITY.format(
            title=info["title"],
            duration=info["duration"],
            views=info["views"],
        )

        if info.get("thumbnail"):
            try:
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.get(info["thumbnail"]) as resp:
                        if resp.status == 200:
                            thumb_data = await resp.read()
                            await status_msg.delete()
                            await message.answer_photo(
                                photo=BufferedInputFile(thumb_data, filename="thumb.jpg"),
                                caption=caption,
                                reply_markup=kb,
                                parse_mode="HTML",
                            )
                            return
            except Exception as e:
                logger.warning(f"Could not send thumbnail: {e}")

        await status_msg.edit_text(caption, reply_markup=kb, parse_mode="HTML")

    except Exception as e:
        logger.error(f"YouTube quality menu error: {e}")
        await status_msg.edit_text(Messages.ERROR_GENERAL, parse_mode="HTML")
        await log_error(message.from_user.id, str(e), "youtube_quality_menu")


@router.callback_query(F.data.startswith("yt_video:"))
async def cb_yt_video(call: CallbackQuery, bot: Bot):
    await call.answer()
    parts = call.data.split(":", 2)
    if len(parts) < 3:
        return
    _, video_id, format_id = parts

    cache_key = f"yt_info:{video_id}"
    info = await memory_cache.get(cache_key)
    if not info:
        await call.message.answer(Messages.ERROR_GENERAL, parse_mode="HTML")
        return

    await download_queue.add_task(
        call.from_user.id,
        _download_yt_video,
        call, info, format_id, bot
    )


@router.callback_query(F.data.startswith("yt_audio:"))
async def cb_yt_audio(call: CallbackQuery, bot: Bot):
    await call.answer()
    parts = call.data.split(":", 2)
    if len(parts) < 3:
        return
    _, video_id, bitrate = parts

    cache_key = f"yt_info:{video_id}"
    info = await memory_cache.get(cache_key)
    if not info:
        await call.message.answer(Messages.ERROR_GENERAL, parse_mode="HTML")
        return

    await download_queue.add_task(
        call.from_user.id,
        _download_yt_audio,
        call, info, bitrate, bot
    )


async def _download_yt_video(call: CallbackQuery, info: dict, format_id: str, bot: Bot):
    user_id = call.from_user.id
    url = info["url"]
    temp_dir = os.path.join(config.TEMP_DIR, uuid.uuid4().hex[:8])

    status_msg = await call.message.answer(
        Messages.YT_DOWNLOADING.format(quality=format_id),
        parse_mode="HTML"
    )

    try:
        file_path = await youtube_service.download_video(url, format_id, temp_dir)
        if not file_path or not os.path.exists(file_path):
            await status_msg.edit_text(Messages.ERROR_GENERAL, parse_mode="HTML")
            return

        file_size = get_file_size(file_path)
        if file_size > config.MAX_FILE_SIZE:
            await status_msg.edit_text(Messages.ERROR_SIZE, parse_mode="HTML")
            return

        await status_msg.edit_text(Messages.UPLOADING, parse_mode="HTML")
        file_input = FSInputFile(file_path, filename=f"video_{info['video_id']}.mp4")
        await call.message.answer_video(
            video=file_input,
            caption=f"▶️ <b>{info['title']}</b>",
            parse_mode="HTML",
            supports_streaming=True,
        )
        await status_msg.delete()
        await increment_downloads(user_id)
        await log_download(user_id, "youtube", url, "video", file_size, format_id, True)

    except Exception as e:
        logger.error(f"YT video download task error: {e}")
        await status_msg.edit_text(Messages.ERROR_GENERAL, parse_mode="HTML")
        await log_error(user_id, str(e), "yt_video_download")
    finally:
        from bot.utils.file_utils import safe_remove_dir
        await safe_remove_dir(temp_dir)


async def _download_yt_audio(call: CallbackQuery, info: dict, bitrate: str, bot: Bot):
    user_id = call.from_user.id
    url = info["url"]
    temp_dir = os.path.join(config.TEMP_DIR, uuid.uuid4().hex[:8])

    status_msg = await call.message.answer(
        Messages.YT_AUDIO_DOWNLOADING.format(quality=f"{bitrate}kbps"),
        parse_mode="HTML"
    )

    try:
        file_path = await youtube_service.download_audio(url, bitrate, temp_dir)
        if not file_path or not os.path.exists(file_path):
            await status_msg.edit_text(Messages.ERROR_GENERAL, parse_mode="HTML")
            return

        file_size = get_file_size(file_path)
        if file_size > config.MAX_FILE_SIZE:
            await status_msg.edit_text(Messages.ERROR_SIZE, parse_mode="HTML")
            return

        await status_msg.edit_text(Messages.UPLOADING, parse_mode="HTML")
        file_input = FSInputFile(file_path, filename=f"audio_{info['video_id']}.mp3")
        await call.message.answer_audio(
            audio=file_input,
            title=info["title"],
            caption=f"🎵 <b>{info['title']}</b>\n🔊 جودة: {bitrate}kbps",
            parse_mode="HTML",
        )
        await status_msg.delete()
        await increment_downloads(user_id)
        await log_download(user_id, "youtube", url, "audio", file_size, f"{bitrate}kbps", True)

    except Exception as e:
        logger.error(f"YT audio download task error: {e}")
        await status_msg.edit_text(Messages.ERROR_GENERAL, parse_mode="HTML")
        await log_error(user_id, str(e), "yt_audio_download")
    finally:
        from bot.utils.file_utils import safe_remove_dir
        await safe_remove_dir(temp_dir)
