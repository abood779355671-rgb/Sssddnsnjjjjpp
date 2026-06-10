import os
import asyncio
import logging
import tempfile
import uuid
from typing import Optional, Dict, Any, List
import yt_dlp
from bot.config import config
from bot.utils.file_utils import ensure_dir, format_file_size, format_duration, format_number

logger = logging.getLogger(__name__)


def _get_ydl_base_opts(temp_dir: str, extra: Dict = None) -> Dict:
    opts = {
        "outtmpl": os.path.join(temp_dir, "%(id)s.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
        "socket_timeout": config.DOWNLOAD_TIMEOUT,
        "retries": 3,
        "fragment_retries": 3,
        "concurrent_fragment_downloads": 4,
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        },
        "noplaylist": True,
    }
    if extra:
        opts.update(extra)
    return opts


class YouTubeService:
    async def get_info(self, url: str) -> Optional[Dict[str, Any]]:
        opts = _get_ydl_base_opts(config.TEMP_DIR)
        opts["skip_download"] = True

        loop = asyncio.get_event_loop()
        try:
            info = await loop.run_in_executor(None, lambda: self._extract_info(url, opts))
            return self._parse_info(info)
        except Exception as e:
            logger.error(f"YouTube info error: {e}")
            return None

    def _extract_info(self, url: str, opts: Dict) -> Dict:
        with yt_dlp.YoutubeDL(opts) as ydl:
            return ydl.extract_info(url, download=False)

    def _parse_info(self, info: Dict) -> Dict:
        formats = []
        seen_qualities = set()
        quality_map = {
            "144": "144p", "240": "240p", "360": "360p",
            "480": "480p", "720": "720p HD", "1080": "1080p FHD",
            "1440": "1440p 2K", "2160": "2160p 4K",
        }
        for fmt in info.get("formats", []):
            if fmt.get("vcodec") == "none":
                continue
            height = fmt.get("height")
            if not height:
                continue
            quality_key = str(height)
            label = quality_map.get(quality_key, f"{height}p")
            if label in seen_qualities:
                continue
            seen_qualities.add(label)
            filesize = fmt.get("filesize") or fmt.get("filesize_approx")
            formats.append({
                "format_id": fmt["format_id"],
                "quality": label,
                "height": height,
                "size": format_file_size(filesize) if filesize else "غير معروف",
                "ext": fmt.get("ext", "mp4"),
            })

        formats.sort(key=lambda x: x["height"])
        return {
            "video_id": info.get("id"),
            "title": info.get("title", "فيديو")[:60],
            "duration": format_duration(info.get("duration")),
            "views": format_number(info.get("view_count")),
            "thumbnail": info.get("thumbnail"),
            "uploader": info.get("uploader", "غير معروف"),
            "formats": formats,
            "url": info.get("webpage_url", ""),
        }

    async def download_video(self, url: str, format_id: str, temp_dir: str) -> Optional[str]:
        ensure_dir(temp_dir)
        uid = uuid.uuid4().hex[:8]
        out_tmpl = os.path.join(temp_dir, f"{uid}.%(ext)s")
        opts = _get_ydl_base_opts(temp_dir, {
            "outtmpl": out_tmpl,
            "format": f"{format_id}+bestaudio/best[height<={format_id}]/best",
            "merge_output_format": "mp4",
        })
        loop = asyncio.get_event_loop()
        try:
            result_path = await loop.run_in_executor(None, lambda: self._download(url, opts, temp_dir, uid))
            return result_path
        except Exception as e:
            logger.error(f"YouTube video download error: {e}")
            return None

    async def download_audio(self, url: str, bitrate: str, temp_dir: str) -> Optional[str]:
        ensure_dir(temp_dir)
        uid = uuid.uuid4().hex[:8]
        out_tmpl = os.path.join(temp_dir, f"{uid}.%(ext)s")
        opts = _get_ydl_base_opts(temp_dir, {
            "outtmpl": out_tmpl,
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": bitrate,
            }],
        })
        loop = asyncio.get_event_loop()
        try:
            result_path = await loop.run_in_executor(None, lambda: self._download(url, opts, temp_dir, uid, ext="mp3"))
            return result_path
        except Exception as e:
            logger.error(f"YouTube audio download error: {e}")
            return None

    def _download(self, url: str, opts: Dict, temp_dir: str, uid: str, ext: str = None) -> Optional[str]:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
        # Find downloaded file
        for fname in os.listdir(temp_dir):
            if fname.startswith(uid):
                fpath = os.path.join(temp_dir, fname)
                if ext and not fpath.endswith(f".{ext}"):
                    continue
                return fpath
        return None


class InstagramService:
    async def download(self, url: str, temp_dir: str) -> List[str]:
        ensure_dir(temp_dir)
        uid = uuid.uuid4().hex[:8]
        opts = _get_ydl_base_opts(temp_dir, {
            "outtmpl": os.path.join(temp_dir, f"{uid}_%(autonumber)s.%(ext)s"),
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "merge_output_format": "mp4",
        })
        loop = asyncio.get_event_loop()
        try:
            files = await loop.run_in_executor(None, lambda: self._download_all(url, opts, temp_dir, uid))
            return files
        except Exception as e:
            logger.error(f"Instagram download error: {e}")
            return []

    async def download_audio(self, url: str, temp_dir: str) -> Optional[str]:
        ensure_dir(temp_dir)
        uid = uuid.uuid4().hex[:8]
        opts = _get_ydl_base_opts(temp_dir, {
            "outtmpl": os.path.join(temp_dir, f"{uid}.%(ext)s"),
            "format": "bestaudio/best",
            "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}],
        })
        loop = asyncio.get_event_loop()
        try:
            return await loop.run_in_executor(None, lambda: self._download_single(url, opts, temp_dir, uid, "mp3"))
        except Exception as e:
            logger.error(f"Instagram audio error: {e}")
            return None

    def _download_all(self, url: str, opts: Dict, temp_dir: str, uid: str) -> List[str]:
        before = set(os.listdir(temp_dir))
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
        after = set(os.listdir(temp_dir))
        new_files = [os.path.join(temp_dir, f) for f in after - before if f.startswith(uid)]
        return sorted(new_files)

    def _download_single(self, url: str, opts: Dict, temp_dir: str, uid: str, ext: str) -> Optional[str]:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
        for fname in os.listdir(temp_dir):
            if fname.startswith(uid) and fname.endswith(f".{ext}"):
                return os.path.join(temp_dir, fname)
        return None


class TikTokService:
    async def download(self, url: str, temp_dir: str) -> Optional[str]:
        ensure_dir(temp_dir)
        uid = uuid.uuid4().hex[:8]
        opts = _get_ydl_base_opts(temp_dir, {
            "outtmpl": os.path.join(temp_dir, f"{uid}.%(ext)s"),
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "merge_output_format": "mp4",
        })
        loop = asyncio.get_event_loop()
        try:
            return await loop.run_in_executor(None, lambda: self._download(url, opts, temp_dir, uid))
        except Exception as e:
            logger.error(f"TikTok download error: {e}")
            return None

    async def download_audio(self, url: str, temp_dir: str) -> Optional[str]:
        ensure_dir(temp_dir)
        uid = uuid.uuid4().hex[:8]
        opts = _get_ydl_base_opts(temp_dir, {
            "outtmpl": os.path.join(temp_dir, f"{uid}.%(ext)s"),
            "format": "bestaudio/best",
            "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}],
        })
        loop = asyncio.get_event_loop()
        try:
            return await loop.run_in_executor(None, lambda: self._download(url, opts, temp_dir, uid, "mp3"))
        except Exception as e:
            logger.error(f"TikTok audio error: {e}")
            return None

    def _download(self, url: str, opts: Dict, temp_dir: str, uid: str, ext: str = None) -> Optional[str]:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
        for fname in os.listdir(temp_dir):
            if fname.startswith(uid):
                if ext and not fname.endswith(f".{ext}"):
                    continue
                return os.path.join(temp_dir, fname)
        return None


class TwitterService:
    async def download(self, url: str, temp_dir: str) -> Optional[str]:
        ensure_dir(temp_dir)
        uid = uuid.uuid4().hex[:8]
        opts = _get_ydl_base_opts(temp_dir, {
            "outtmpl": os.path.join(temp_dir, f"{uid}.%(ext)s"),
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "merge_output_format": "mp4",
        })
        loop = asyncio.get_event_loop()
        try:
            return await loop.run_in_executor(None, lambda: self._download(url, opts, temp_dir, uid))
        except Exception as e:
            logger.error(f"Twitter download error: {e}")
            return None

    async def download_photos(self, url: str, temp_dir: str) -> List[str]:
        ensure_dir(temp_dir)
        uid = uuid.uuid4().hex[:8]
        opts = _get_ydl_base_opts(temp_dir, {
            "outtmpl": os.path.join(temp_dir, f"{uid}_%(autonumber)s.%(ext)s"),
            "format": "best",
            "write_all_thumbnails": False,
        })
        loop = asyncio.get_event_loop()
        try:
            before = set(os.listdir(temp_dir))
            await loop.run_in_executor(None, lambda: self._run_ydl(url, opts))
            after = set(os.listdir(temp_dir))
            new_files = [os.path.join(temp_dir, f) for f in after - before if f.startswith(uid)]
            return sorted(new_files)
        except Exception as e:
            logger.error(f"Twitter photos error: {e}")
            return []

    async def download_audio(self, url: str, temp_dir: str) -> Optional[str]:
        ensure_dir(temp_dir)
        uid = uuid.uuid4().hex[:8]
        opts = _get_ydl_base_opts(temp_dir, {
            "outtmpl": os.path.join(temp_dir, f"{uid}.%(ext)s"),
            "format": "bestaudio/best",
            "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}],
        })
        loop = asyncio.get_event_loop()
        try:
            return await loop.run_in_executor(None, lambda: self._download(url, opts, temp_dir, uid, "mp3"))
        except Exception as e:
            logger.error(f"Twitter audio error: {e}")
            return None

    def _run_ydl(self, url: str, opts: Dict):
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])

    def _download(self, url: str, opts: Dict, temp_dir: str, uid: str, ext: str = None) -> Optional[str]:
        self._run_ydl(url, opts)
        for fname in os.listdir(temp_dir):
            if fname.startswith(uid):
                if ext and not fname.endswith(f".{ext}"):
                    continue
                return os.path.join(temp_dir, fname)
        return None


class SoundCloudService:
    async def download(self, url: str, temp_dir: str) -> Optional[Dict]:
        ensure_dir(temp_dir)
        uid = uuid.uuid4().hex[:8]
        info_opts = _get_ydl_base_opts(temp_dir, {"skip_download": True})
        dl_opts = _get_ydl_base_opts(temp_dir, {
            "outtmpl": os.path.join(temp_dir, f"{uid}.%(ext)s"),
            "format": "bestaudio/best",
            "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}],
            "writethumbnail": True,
        })
        loop = asyncio.get_event_loop()
        try:
            info = await loop.run_in_executor(None, lambda: self._extract_info(url, info_opts))
            await loop.run_in_executor(None, lambda: self._run_ydl(url, dl_opts))

            audio_file = None
            thumb_file = None
            for fname in os.listdir(temp_dir):
                if fname.startswith(uid):
                    fpath = os.path.join(temp_dir, fname)
                    if fname.endswith(".mp3"):
                        audio_file = fpath
                    elif any(fname.endswith(ext) for ext in (".jpg", ".jpeg", ".png", ".webp")):
                        thumb_file = fpath

            return {
                "audio_file": audio_file,
                "thumb_file": thumb_file,
                "title": info.get("title", "مقطع صوتي"),
                "artist": info.get("uploader", "غير معروف"),
                "duration": format_duration(info.get("duration")),
            }
        except Exception as e:
            logger.error(f"SoundCloud download error: {e}")
            return None

    def _extract_info(self, url: str, opts: Dict) -> Dict:
        with yt_dlp.YoutubeDL(opts) as ydl:
            return ydl.extract_info(url, download=False)

    def _run_ydl(self, url: str, opts: Dict):
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])


class PinterestService:
    async def download(self, url: str, temp_dir: str) -> List[str]:
        ensure_dir(temp_dir)
        uid = uuid.uuid4().hex[:8]
        opts = _get_ydl_base_opts(temp_dir, {
            "outtmpl": os.path.join(temp_dir, f"{uid}_%(autonumber)s.%(ext)s"),
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "merge_output_format": "mp4",
        })
        loop = asyncio.get_event_loop()
        try:
            before = set(os.listdir(temp_dir))
            await loop.run_in_executor(None, lambda: self._run_ydl(url, opts))
            after = set(os.listdir(temp_dir))
            new_files = [os.path.join(temp_dir, f) for f in after - before if f.startswith(uid)]
            return sorted(new_files)
        except Exception as e:
            logger.error(f"Pinterest download error: {e}")
            return []

    async def download_audio(self, url: str, temp_dir: str) -> Optional[str]:
        ensure_dir(temp_dir)
        uid = uuid.uuid4().hex[:8]
        opts = _get_ydl_base_opts(temp_dir, {
            "outtmpl": os.path.join(temp_dir, f"{uid}.%(ext)s"),
            "format": "bestaudio/best",
            "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}],
        })
        loop = asyncio.get_event_loop()
        try:
            return await loop.run_in_executor(None, lambda: self._download_single(url, opts, temp_dir, uid, "mp3"))
        except Exception as e:
            logger.error(f"Pinterest audio error: {e}")
            return None

    def _run_ydl(self, url: str, opts: Dict):
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])

    def _download_single(self, url: str, opts: Dict, temp_dir: str, uid: str, ext: str) -> Optional[str]:
        self._run_ydl(url, opts)
        for fname in os.listdir(temp_dir):
            if fname.startswith(uid) and fname.endswith(f".{ext}"):
                return os.path.join(temp_dir, fname)
        return None


# Service instances
youtube_service = YouTubeService()
instagram_service = InstagramService()
tiktok_service = TikTokService()
twitter_service = TwitterService()
soundcloud_service = SoundCloudService()
pinterest_service = PinterestService()
