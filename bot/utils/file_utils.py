import os
import asyncio
import aiofiles
import hashlib
import mimetypes
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def get_file_hash(file_path: str) -> str:
    """Calculate SHA256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def get_file_size(file_path: str) -> int:
    """Return file size in bytes."""
    return os.path.getsize(file_path)


def format_file_size(size_bytes: int) -> str:
    """Format file size to human readable."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def format_duration(seconds: int) -> str:
    """Format duration seconds to HH:MM:SS or MM:SS."""
    if seconds is None:
        return "غير معروف"
    seconds = int(seconds)
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def format_number(n: int) -> str:
    """Format large numbers."""
    if n is None:
        return "غير معروف"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


def get_mime_type(file_path: str) -> str:
    """Get MIME type of a file."""
    mime, _ = mimetypes.guess_type(file_path)
    return mime or "application/octet-stream"


def is_video(file_path: str) -> bool:
    mime = get_mime_type(file_path)
    return mime and mime.startswith("video/")


def is_audio(file_path: str) -> bool:
    mime = get_mime_type(file_path)
    return mime and mime.startswith("audio/")


def is_image(file_path: str) -> bool:
    mime = get_mime_type(file_path)
    return mime and mime.startswith("image/")


async def safe_remove(file_path: str):
    """Safely remove a file."""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        logger.warning(f"Failed to remove file {file_path}: {e}")


async def safe_remove_dir(dir_path: str):
    """Safely remove a directory and its contents."""
    import shutil
    try:
        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)
    except Exception as e:
        logger.warning(f"Failed to remove dir {dir_path}: {e}")


def ensure_dir(path: str):
    """Create directory if it doesn't exist."""
    Path(path).mkdir(parents=True, exist_ok=True)


def get_temp_path(filename: str, temp_dir: str) -> str:
    """Get a temporary file path."""
    ensure_dir(temp_dir)
    return os.path.join(temp_dir, filename)
