import re
from typing import Optional, Tuple
from urllib.parse import urlparse

PLATFORM_PATTERNS = {
    "instagram": [
        r"(?:https?://)?(?:www\.)?instagram\.com/(?:reel|p|tv)/[\w-]+",
        r"(?:https?://)?instagr\.am/(?:reel|p|tv)/[\w-]+",
        r"(?:https?://)?(?:www\.)?instagram\.com/stories/[\w.]+/\d+",
    ],
    "tiktok": [
        r"(?:https?://)?(?:www\.|vm\.|m\.)?tiktok\.com/@[\w.]+/video/\d+",
        r"(?:https?://)?(?:www\.|vm\.)?tiktok\.com/[\w]+",
        r"(?:https?://)?(?:www\.)?tiktok\.com/t/[\w]+",
    ],
    "youtube": [
        r"(?:https?://)?(?:www\.)?youtube\.com/watch\?v=[\w-]+",
        r"(?:https?://)?(?:www\.)?youtube\.com/shorts/[\w-]+",
        r"(?:https?://)?youtu\.be/[\w-]+",
        r"(?:https?://)?(?:www\.)?youtube\.com/embed/[\w-]+",
        r"(?:https?://)?(?:www\.)?youtube\.com/v/[\w-]+",
    ],
    "twitter": [
        r"(?:https?://)?(?:www\.|mobile\.)?twitter\.com/\w+/status/\d+",
        r"(?:https?://)?(?:www\.)?x\.com/\w+/status/\d+",
        r"(?:https?://)?t\.co/[\w]+",
    ],
    "soundcloud": [
        r"(?:https?://)?(?:www\.|m\.)?soundcloud\.com/[\w-]+/[\w-]+",
        r"(?:https?://)?on\.soundcloud\.com/[\w]+",
    ],
    "pinterest": [
        r"(?:https?://)?(?:www\.|[a-z]{2}\.)?pinterest\.com/pin/\d+",
        r"(?:https?://)?(?:www\.)?pinterest\.com/\w+/\w+",
        r"(?:https?://)?pin\.it/[\w]+",
    ],
}


def detect_platform(url: str) -> Optional[str]:
    """Detect platform from URL."""
    url = url.strip()
    for platform, patterns in PLATFORM_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return platform
    return None


def extract_urls(text: str) -> list:
    """Extract all URLs from text."""
    url_pattern = r'https?://[^\s<>"\'{}|\\^`\[\]]+'
    return re.findall(url_pattern, text)


def is_valid_url(url: str) -> bool:
    """Basic URL validation."""
    try:
        result = urlparse(url)
        return all([result.scheme in ("http", "https"), result.netloc])
    except Exception:
        return False


def clean_url(url: str) -> str:
    """Clean URL from tracking parameters."""
    try:
        parsed = urlparse(url)
        # Remove common tracking params
        import urllib.parse as up
        params = up.parse_qs(parsed.query)
        clean_params = {k: v for k, v in params.items() if k not in (
            "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
            "fbclid", "gclid", "si", "feature", "ref"
        )}
        new_query = up.urlencode(clean_params, doseq=True)
        clean = parsed._replace(query=new_query)
        return up.urlunparse(clean)
    except Exception:
        return url
