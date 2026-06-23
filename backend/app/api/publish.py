"""Publish routes — push an already-generated video to a platform."""
from pathlib import Path

from fastapi import APIRouter, HTTPException

from ..config import OUTPUT_DIR
from ..db import get_job, update_job
from ..services.publishers import youtube as yt_svc

router = APIRouter(prefix="/publish", tags=["publish"])


@router.post("/{job_id}/youtube")
async def publish_youtube(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    video_path = OUTPUT_DIR / f"{job_id}.mp4"
    if not video_path.exists():
        raise HTTPException(404, "Video not generated yet")

    try:
        url = yt_svc.upload_short(
            Path(video_path),
            title=job.get("title") or job.get("topic", "Short"),
            description=job.get("description", ""),
            hashtags=job.get("hashtags", []),
        )
    except Exception as e:  # noqa: BLE001
        raise HTTPException(400, str(e))

    update_job(job_id, youtube_url=url)
    return {"job_id": job_id, "youtube_url": url}
