import os
import logging
import uuid
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import Command

from bot.utils.url_detector import detect_platform, extract_urls, is_valid_url, clean_url
from bot.utils.messages import Messages
from bot.utils.keyboards import build_media_actions_keyboard
from bot.utils.file_utils import get_file_size, safe_remove_dir
from bot.services.downloader import (
    instagram_service, tiktok_service, twitter_service,
    soundcloud_service, pinterest_service
)
from bot.handlers.youtube import send_youtube_quality_menu
from bot.database.repositories.user_repo import increment_downloads
from bot.database.repositories.download_repo import log_download
from bot.database.repositories.settings_repo import log_error
from bot.config import config
from bot.queue.task_queue import download_queue

logger = logging.getLogger(__name__)
router = Router(name="download")

PLATFORM_DISPLAY = {
    "instagram": "Instagram 📷",
    "tiktok": "TikTok 🎵",
    "youtube": "YouTube ▶️",
    "twitter": "X (Twitter) 🐦",
    "soundcloud": "SoundCloud 🎧",
    "pinterest": "Pinterest 📌",
}


@router.message(F.text)
async def handle_text_message(message: Message, bot: Bot):
    text = message.text.strip()
    urls = extract_urls(text)

    if not urls:
        return

    url = clean_url(urls[0])
    if not is_valid_url(url):
        await message.answer(Messages.INVALID_URL, parse_mode="HTML")
        return

    platform = detect_platform(url)
    if not platform:
        await message.answer(Messages.UNSUPPORTED_PLATFORM, parse_mode="HTML")
        return

    if platform == "youtube":
        await send_youtube_quality_menu(message, url, bot)
        return

    if platform == "soundcloud":
        await download_queue.add_task(message.from_user.id, _handle_soundcloud, message, url)
        return

    await download_queue.add_task(message.from_user.id, _handle_media, message, url, platform, "video")


@router.callback_query(F.data.startswith("dl_video:"))
async def cb_dl_video(call: CallbackQuery):
    url = call.data[len("dl_video:"):]
    platform = detect_platform(url)
    await call.answer()
    if platform:
        await download_queue.add_task(call.from_user.id, _handle_media, call.message, url, platform, "video", call.from_user.id)


@router.callback_query(F.data.startswith("dl_audio:"))
async def cb_dl_audio(call: CallbackQuery):
    url = call.data[len("dl_audio:"):]
    platform = detect_platform(url)
    await call.answer()
    if platform:
        await download_queue.add_task(call.from_user.id, _handle_media, call.message, url, platform, "audio", call.from_user.id)


async def _handle_media(message: Message, url: str, platform: str, media_type: str, user_id: int = None):
    if user_id is None:
        user_id = message.chat.id

    temp_dir = os.path.join(config.TEMP_DIR, uuid.uuid4().hex[:8])
    status_msg = await message.answer(
        Messages.DOWNLOADING.format(platform=PLATFORM_DISPLAY.get(platform, platform)),
        parse_mode="HTML"
    )

    try:
        files = []
        audio_file = None
        meta = {}

        if platform == "instagram":
            if media_type == "audio":
                audio_file = await instagram_service.download_audio(url, temp_dir)
            else:
                files = await instagram_service.download(url, temp_dir)

        elif platform == "tiktok":
            if media_type == "audio":
                audio_file = await tiktok_service.download_audio(url, temp_dir)
            else:
                f = await tiktok_service.download(url, temp_dir)
                if f:
                    files = [f]

        elif platform == "twitter":
            if media_type == "audio":
                audio_file = await twitter_service.download_audio(url, temp_dir)
            else:
                f = await twitter_service.download(url, temp_dir)
                if f:
                    files = [f]
                else:
                    files = await twitter_service.download_photos(url, temp_dir)

        elif platform == "pinterest":
            if media_type == "audio":
                audio_file = await pinterest_service.download_audio(url, temp_dir)
            else:
                files = await pinterest_service.download(url, temp_dir)

        if not files and not audio_file:
            await status_msg.edit_text(Messages.ERROR_GENERAL, parse_mode="HTML")
            await log_error(user_id, "No files downloaded", f"{platform}:{url[:100]}")
            return

        await status_msg.edit_text(Messages.UPLOADING, parse_mode="HTML")
        total_size = 0

        if audio_file and os.path.exists(audio_file):
            fsize = get_file_size(audio_file)
            if fsize > config.MAX_FILE_SIZE:
                await status_msg.edit_text(Messages.ERROR_SIZE, parse_mode="HTML")
                return
            total_size += fsize
            fi = FSInputFile(audio_file, filename=f"audio_{platform}.mp3")
            await message.answer_audio(audio=fi, caption=f"🎵 {PLATFORM_DISPLAY.get(platform, platform)}")
            await log_download(user_id, platform, url, "audio", fsize, "192kbps", True)
            await increment_downloads(user_id)

        for fpath in files:
            if not os.path.exists(fpath):
                continue
            fsize = get_file_size(fpath)
            if fsize > config.MAX_FILE_SIZE:
                await message.answer(Messages.ERROR_SIZE, parse_mode="HTML")
                continue
            total_size += fsize
            ext = os.path.splitext(fpath)[1].lower()
            if ext in (".mp4", ".mov", ".avi", ".mkv", ".webm"):
                fi = FSInputFile(fpath, filename=f"video_{platform}{ext}")
                await message.answer_video(video=fi, supports_streaming=True)
                await log_download(user_id, platform, url, "video", fsize, "best", True)
            elif ext in (".jpg", ".jpeg", ".png", ".webp"):
                fi = FSInputFile(fpath, filename=f"photo_{platform}{ext}")
                await message.answer_photo(photo=fi)
                await log_download(user_id, platform, url, "photo", fsize, "original", True)
            else:
                fi = FSInputFile(fpath)
                await message.answer_document(document=fi)
                await log_download(user_id, platform, url, "file", fsize, "original", True)
            await increment_downloads(user_id)

        await status_msg.delete()

    except Exception as e:
        logger.error(f"Media download error [{platform}]: {e}")
        try:
            await status_msg.edit_text(Messages.ERROR_GENERAL, parse_mode="HTML")
        except Exception:
            pass
        await log_error(user_id, str(e), f"{platform}:{url[:100]}")
    finally:
        await safe_remove_dir(temp_dir)


async def _handle_soundcloud(message: Message, url: str):
    user_id = message.from_user.id
    temp_dir = os.path.join(config.TEMP_DIR, uuid.uuid4().hex[:8])

    status_msg = await message.answer(Messages.DOWNLOADING.format(platform="SoundCloud 🎧"), parse_mode="HTML")

    try:
        result = await soundcloud_service.download(url, temp_dir)
        if not result or not result.get("audio_file"):
            await status_msg.edit_text(Messages.ERROR_GENERAL, parse_mode="HTML")
            return

        await status_msg.edit_text(
            Messages.SC_INFO.format(
                title=result["title"],
                artist=result["artist"],
                duration=result["duration"],
            ),
            parse_mode="HTML"
        )

        audio_file = result["audio_file"]
        thumb_file = result.get("thumb_file")

        if not os.path.exists(audio_file):
            await status_msg.edit_text(Messages.ERROR_GENERAL, parse_mode="HTML")
            return

        fsize = get_file_size(audio_file)
        if fsize > config.MAX_FILE_SIZE:
            await status_msg.edit_text(Messages.ERROR_SIZE, parse_mode="HTML")
            return

        thumb_input = None
        if thumb_file and os.path.exists(thumb_file):
            thumb_input = FSInputFile(thumb_file)

        fi = FSInputFile(audio_file, filename=f"{result['title'][:40]}.mp3")
        await message.answer_audio(
            audio=fi,
            title=result["title"],
            performer=result["artist"],
            thumbnail=thumb_input,
            caption=f"🎧 <b>{result['title']}</b>\n👤 {result['artist']}\n⏱️ {result['duration']}",
            parse_mode="HTML",
        )
        await status_msg.delete()
        await increment_downloads(user_id)
        await log_download(user_id, "soundcloud", url, "audio", fsize, "192kbps", True)

    except Exception as e:
        logger.error(f"SoundCloud error: {e}")
        try:
            await status_msg.edit_text(Messages.ERROR_GENERAL, parse_mode="HTML")
        except Exception:
            pass
        await log_error(user_id, str(e), f"soundcloud:{url[:100]}")
    finally:
        await safe_remove_dir(temp_dir)
