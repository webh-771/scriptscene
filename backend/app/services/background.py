"""Background video source. Supports BOTH:
  1. Local files dropped in assets/backgrounds/ (e.g. gameplay loops)
  2. Royalty-free b-roll auto-fetched from Pexels / Pixabay (free, copyright-clean)

Returns a path to a usable mp4. compose.py handles crop/loop to duration.
"""
import logging
import random
from pathlib import Path
from typing import List, Optional

import requests

from ..config import settings, BACKGROUNDS_DIR, WORK_DIR

logger = logging.getLogger(__name__)

_VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".webm"}


def _local_backgrounds() -> list:
    return [p for p in BACKGROUNDS_DIR.iterdir()
            if p.is_file() and p.suffix.lower() in _VIDEO_EXTS]


def _fetch_pexels(query: str, job_id: str, count: int) -> List[Path]:
    if not settings.PEXELS_API_KEY:
        return []
    r = requests.get(
        "https://api.pexels.com/videos/search",
        headers={"Authorization": settings.PEXELS_API_KEY},
        params={"query": query, "per_page": max(count, 8), "orientation": "portrait"},
        timeout=20,
    )
    r.raise_for_status()
    videos = r.json().get("videos", [])
    random.shuffle(videos)
    paths = []
    for i, vid in enumerate(videos[:count]):
        files = sorted(vid["video_files"], key=lambda f: f.get("width", 0) or 0, reverse=True)
        if files:
            paths.append(_download(files[0]["link"], f"{job_id}_{i}"))
    return paths


def _fetch_pixabay(query: str, job_id: str, count: int) -> List[Path]:
    if not settings.PIXABAY_API_KEY:
        return []
    r = requests.get(
        "https://pixabay.com/api/videos/",
        params={"key": settings.PIXABAY_API_KEY, "q": query, "per_page": max(count, 8)},
        timeout=20,
    )
    r.raise_for_status()
    hits = r.json().get("hits", [])
    random.shuffle(hits)
    paths = []
    for i, hit in enumerate(hits[:count]):
        v = hit["videos"]
        url = v.get("large", v.get("medium"))["url"]
        paths.append(_download(url, f"{job_id}_{i}"))
    return paths


def _download(url: str, tag: str) -> Path:
    dest = WORK_DIR / f"{tag}_bg.mp4"
    with requests.get(url, stream=True, timeout=60) as resp:
        resp.raise_for_status()
        with open(dest, "wb") as fh:
            for chunk in resp.iter_content(chunk_size=1 << 16):
                fh.write(chunk)
    return dest


def resolve_backgrounds(job_id: str, query: str, prefer_file: Optional[str] = None,
                        count: int = 5) -> List[Path]:
    """Return a LIST of background clips to cut between (keeps interest).
    Priority: explicit file -> local files -> royalty-free b-roll fetch."""
    if prefer_file:
        p = BACKGROUNDS_DIR / prefer_file
        if p.exists():
            logger.info("Using requested background file: %s", prefer_file)
            return [p]
        logger.warning("Requested background '%s' not found; falling back", prefer_file)

    locals_ = _local_backgrounds()
    if locals_:
        random.shuffle(locals_)
        logger.info("Using %d local background(s)", min(count, len(locals_)))
        return locals_[:count]

    for fetcher in (_fetch_pexels, _fetch_pixabay):
        try:
            got = fetcher(query, job_id, count)
            if got:
                logger.info("Fetched %d royalty-free clips for '%s' via %s",
                            len(got), query, fetcher.__name__)
                return got
        except Exception as e:  # noqa: BLE001
            logger.warning("%s failed: %s", fetcher.__name__, e)

    raise RuntimeError(
        "No background available: add a video to assets/backgrounds/ "
        "or set PEXELS_API_KEY / PIXABAY_API_KEY"
    )
