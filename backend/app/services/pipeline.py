"""Orchestrates the full generation: story -> tts -> captions -> background
-> compose -> (optional) publish. Updates job state at each stage.
"""
import logging

from ..config import WORK_DIR
from ..db import update_job
from ..models import GenerateRequest
from . import story as story_svc
from . import tts as tts_svc
from . import captions as captions_svc
from . import background as bg_svc
from . import compose as compose_svc
from .publishers import youtube as yt_svc

logger = logging.getLogger(__name__)


def _stage(job_id: str, progress: int, stage: str, **extra):
    update_job(job_id, status="running", progress=progress, stage=stage, **extra)
    logger.info("[%s] %d%% %s", job_id, progress, stage)


def run_pipeline(job_id: str, req: GenerateRequest) -> None:
    try:
        # 1. Original script + metadata
        _stage(job_id, 10, "writing script")
        content = story_svc.generate_content(req.topic, req.niche)
        update_job(job_id, script=content["script"], title=content["title"])

        # 2. Voiceover
        _stage(job_id, 30, "generating voiceover")
        narration_path = WORK_DIR / f"{job_id}.mp3"
        tts_svc.synthesize(content["script"], narration_path, voice=req.voice)

        # 3. Word-level caption timing
        _stage(job_id, 50, "timing captions")
        words = captions_svc.transcribe_words(narration_path)

        # 4. Background
        _stage(job_id, 65, "fetching background")
        bg_query = req.background_query or content.get("background_query") or req.niche
        background_path = bg_svc.resolve_background(job_id, bg_query, req.background_file)

        # 5. Compose
        _stage(job_id, 80, "rendering video")
        video_path = compose_svc.compose_video(
            job_id, background_path, narration_path, words, with_music=req.music
        )
        video_url = f"/api/videos/{job_id}/download"
        update_job(job_id, video_url=video_url)

        # 6. Optional publish
        youtube_url = None
        if req.publish_youtube:
            _stage(job_id, 90, "uploading to youtube")
            youtube_url = yt_svc.upload_short(
                video_path, content["title"], content["description"], content["hashtags"]
            )

        update_job(job_id, status="done", progress=100, stage="done",
                   video_url=video_url, youtube_url=youtube_url)
        logger.info("[%s] pipeline complete", job_id)

    except Exception as e:  # noqa: BLE001 — surface any failure to the job record
        logger.exception("[%s] pipeline failed", job_id)
        update_job(job_id, status="error", stage="error", error=str(e))
