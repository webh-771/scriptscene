"""Publish routes — push an already-generated video to YouTube as a background
job so it never blocks video generation.
"""
import logging
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, HTTPException

from ..config import OUTPUT_DIR
from ..db import get_job, update_job
from ..models import PublishRequest
from ..services import story as story_svc
from ..services.publishers import youtube as yt_svc

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/publish", tags=["publish"])


def _run_upload(job_id: str, req: PublishRequest) -> None:
    try:
        job = get_job(job_id) or {}
        title = req.title or job.get("title") or job.get("topic", "Short")
        description = req.description or job.get("description", "")
        tags = req.tags or job.get("hashtags", [])

        if req.optimize:
            update_job(job_id, upload_status="optimizing")
            context = job.get("script") or job.get("topic", "")
            meta = story_svc.optimize_metadata(context, title, description)
            title, description, tags = meta["title"], meta["description"], meta["tags"]
            update_job(job_id, title=title, description=description, hashtags=tags)

        update_job(job_id, upload_status="uploading")
        url = yt_svc.upload_short(
            OUTPUT_DIR / f"{job_id}.mp4", title=title, description=description,
            hashtags=tags, privacy=req.privacy,
        )
        update_job(job_id, upload_status="uploaded", youtube_url=url, upload_error=None)
        logger.info("[%s] uploaded -> %s", job_id, url)
    except Exception as e:  # noqa: BLE001
        logger.exception("[%s] upload failed", job_id)
        update_job(job_id, upload_status="error", upload_error=str(e))


@router.post("/{job_id}/youtube")
async def publish_youtube(job_id: str, req: PublishRequest, background_tasks: BackgroundTasks):
    job = get_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    if not (OUTPUT_DIR / f"{job_id}.mp4").exists():
        raise HTTPException(404, "Video not generated yet")

    update_job(job_id, upload_status="queued", upload_error=None)
    background_tasks.add_task(_run_upload, job_id, req)
    return {"job_id": job_id, "upload_status": "queued"}


@router.get("/{job_id}/metadata")
async def suggest_metadata(job_id: str):
    """Generate SEO-optimized metadata suggestions to pre-fill the upload form."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    context = job.get("script") or job.get("topic", "")
    try:
        meta = story_svc.optimize_metadata(context, job.get("title", ""), job.get("description", ""))
    except Exception as e:  # noqa: BLE001
        raise HTTPException(400, str(e))
    return meta
