"""Background video source. Supports BOTH:
  1. Local files dropped in assets/backgrounds/ (e.g. gameplay loops)
  2. Royalty-free b-roll auto-fetched from Pexels / Pixabay (free, copyright-clean)

Returns a path to a usable mp4. compose.py handles crop/loop to duration.
"""
import logging
import random
from pathlib import Path
from typing import Optional

import requests

from ..config import settings, BACKGROUNDS_DIR, WORK_DIR

logger = logging.getLogger(__name__)

_VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".webm"}


def _local_backgrounds() -> list:
    return [p for p in BACKGROUNDS_DIR.iterdir()
            if p.is_file() and p.suffix.lower() in _VIDEO_EXTS]


def _fetch_pexels(query: str, job_id: str) -> Optional[Path]:
    if not settings.PEXELS_API_KEY:
        return None
    r = requests.get(
        "https://api.pexels.com/videos/search",
        headers={"Authorization": settings.PEXELS_API_KEY},
        params={"query": query, "per_page": 10, "orientation": "portrait"},
        timeout=20,
    )
    r.raise_for_status()
    videos = r.json().get("videos", [])
    if not videos:
        return None
    chosen = random.choice(videos)
    files = sorted(chosen["video_files"], key=lambda f: f.get("width", 0) or 0, reverse=True)
    return _download(files[0]["link"], job_id)


def _fetch_pixabay(query: str, job_id: str) -> Optional[Path]:
    if not settings.PIXABAY_API_KEY:
        return None
    r = requests.get(
        "https://pixabay.com/api/videos/",
        params={"key": settings.PIXABAY_API_KEY, "q": query, "per_page": 10},
        timeout=20,
    )
    r.raise_for_status()
    hits = r.json().get("hits", [])
    if not hits:
        return None
    chosen = random.choice(hits)
    url = chosen["videos"].get("large", chosen["videos"]["medium"])["url"]
    return _download(url, job_id)


def _download(url: str, job_id: str) -> Path:
    dest = WORK_DIR / f"{job_id}_bg.mp4"
    with requests.get(url, stream=True, timeout=60) as resp:
        resp.raise_for_status()
        with open(dest, "wb") as fh:
            for chunk in resp.iter_content(chunk_size=1 << 16):
                fh.write(chunk)
    return dest


def resolve_background(job_id: str, query: str, prefer_file: Optional[str] = None) -> Path:
    """Pick a background. Priority: explicit file -> any local file -> b-roll fetch."""
    if prefer_file:
        p = BACKGROUNDS_DIR / prefer_file
        if p.exists():
            logger.info("Using requested background file: %s", prefer_file)
            return p
        logger.warning("Requested background '%s' not found; falling back", prefer_file)

    locals_ = _local_backgrounds()
    if locals_:
        choice = random.choice(locals_)
        logger.info("Using local background: %s", choice.name)
        return choice

    for fetcher in (_fetch_pexels, _fetch_pixabay):
        try:
            got = fetcher(query, job_id)
            if got:
                logger.info("Fetched royalty-free b-roll for '%s' via %s", query, fetcher.__name__)
                return got
        except Exception as e:  # noqa: BLE001
            logger.warning("%s failed: %s", fetcher.__name__, e)

    raise RuntimeError(
        "No background available: add a video to assets/backgrounds/ "
        "or set PEXELS_API_KEY / PIXABAY_API_KEY"
    )
