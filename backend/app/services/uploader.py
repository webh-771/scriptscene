"""Shared YouTube upload orchestration: AI-optimize metadata, append the music
credit, upload, and track upload_status on the job. Used by both the manual
publish route and the auto-upload step of the pipeline.
"""
import logging
from typing import Optional

from ..config import OUTPUT_DIR
from ..db import get_job, update_job
from . import story as story_svc
from .publishers import youtube as yt_svc

logger = logging.getLogger(__name__)


def upload_job(job_id: str, optimize: bool = True, privacy: str = "public",
               title: Optional[str] = None, description: Optional[str] = None,
               tags: Optional[list] = None) -> str:
    """Optimize (optional) + upload the job's video. Updates upload_status and
    raises on failure (caller records the error)."""
    job = get_job(job_id) or {}
    title = title or job.get("title") or job.get("topic", "Short")
    description = description or job.get("description", "")
    tags = tags or job.get("hashtags", [])

    if optimize:
        update_job(job_id, upload_status="optimizing")
        context = job.get("script") or job.get("topic", "")
        meta = story_svc.optimize_metadata(context, title, description)
        title, description, tags = meta["title"], meta["description"], meta["tags"]
        update_job(job_id, title=title, description=description, hashtags=tags)

    credit = job.get("music_credit")
    if credit and credit not in description:
        description = f"{description}\n\n{credit}".strip()

    update_job(job_id, upload_status="uploading")
    url = yt_svc.upload_short(
        OUTPUT_DIR / f"{job_id}.mp4", title=title, description=description,
        hashtags=tags, privacy=privacy,
    )
    update_job(job_id, upload_status="uploaded", youtube_url=url, upload_error=None)
    logger.info("[%s] uploaded -> %s", job_id, url)
    return url
