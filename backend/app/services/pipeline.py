"""Orchestrates generation: source -> tts -> captions -> background -> compose
-> (optional) publish. Updates job state at each stage.
"""
import logging
import math

from ..config import WORK_DIR, dims_for
from ..db import update_job
from ..languages import get as get_lang, font_path
from ..models import GenerateRequest
from . import story as story_svc
from . import reddit as reddit_svc
from . import tts as tts_svc
from . import captions as captions_svc
from . import background as bg_svc
from . import music as music_svc
from . import compose as compose_svc
from . import uploader as uploader_svc

logger = logging.getLogger(__name__)


def _stage(job_id: str, progress: int, stage: str, **extra):
    update_job(job_id, status="running", progress=progress, stage=stage, **extra)
    logger.info("[%s] %d%% %s", job_id, progress, stage)


def _resolve_content(req: GenerateRequest) -> dict:
    """Produce {script, title, description, hashtags, background_query}."""
    if req.reddit_url:
        story = reddit_svc.fetch_story(req.reddit_url)
        return {
            "script": story["script"], "title": story["title"],
            "description": "", "hashtags": [req.niche, "Shorts"],
            "background_query": req.niche,
        }
    if req.script:
        return {
            "script": req.script, "title": req.script[:80],
            "description": "", "hashtags": [req.niche, "Shorts"],
            "background_query": req.niche,
        }
    if req.topic:
        lang_prompt = get_lang(req.language)["prompt"]
        return story_svc.generate_content(req.topic, req.niche, language=lang_prompt)
    raise RuntimeError("Provide one of: topic, reddit_url, or script")


def _resolve_background(job_id: str, req: GenerateRequest, content: dict,
                        target_clips: int = 5) -> dict:
    spec = {"type": req.background_type}
    if req.background_type in ("broll", "gameplay"):
        if req.background_query:
            query = req.background_query           # explicit user override
        else:
            # derive scene keywords from the actual script so footage matches it
            query = story_svc.scene_keywords(content["script"], count=min(target_clips, 8)) \
                or content.get("background_query") or req.niche
        spec["paths"] = bg_svc.resolve_backgrounds(
            job_id, query, req.background_file, count=target_clips)
    elif req.background_type == "gradient":
        spec["gradient"] = req.gradient
    elif req.background_type == "solid":
        spec["solid"] = req.solid_color
    return spec


def run_pipeline(job_id: str, req: GenerateRequest) -> None:
    try:
        w, h = dims_for(req.aspect)

        # 1. Content
        _stage(job_id, 10, "preparing script")
        content = _resolve_content(req)
        update_job(job_id, script=content["script"], title=content["title"])

        # 2. Voiceover
        _stage(job_id, 30, "generating voiceover")
        narration_path = tts_svc.synthesize(
            content["script"], WORK_DIR / f"{job_id}.mp3",
            engine=req.tts_engine, voice=req.voice, language=req.language,
        )

        # 3. Word-level caption timing
        _stage(job_id, 50, "timing captions")
        # English uses the fast 'base' model; every other language (incl. romanized
        # Hindi) uses the bigger 'small' model for accuracy.
        model_name = "base" if req.language == "en" else "small"
        words = captions_svc.transcribe_words(
            narration_path, language=get_lang(req.language)["whisper"],
            model_name=model_name)

        # 4. Background — fetch enough UNIQUE clips to cover the narration
        # (~one new clip every ~4.5s) so the timeline never repeats a clip.
        _stage(job_id, 65, "preparing background")
        approx_dur = words[-1]["end"] if words else 60.0
        target_clips = max(4, min(12, math.ceil(approx_dur / 4.5)))
        bg_spec = _resolve_background(job_id, req, content, target_clips)

        # 5. Compose (auto-fetch copyright-free music if library is empty)
        music_track, music_credit = None, None
        if req.music and req.music_volume > 0:
            music_svc.ensure_music(req.niche)
            music_track = music_svc.pick_track()
            music_credit = music_svc.attribution(music_track)
            if music_credit:
                update_job(job_id, music_credit=music_credit)
        _stage(job_id, 80, "rendering video")
        video_path = compose_svc.compose_video(
            job_id, bg_spec, narration_path, words, w, h,
            style=req.captions, font=font_path(req.language),
            with_music=req.music, music_volume=req.music_volume, music_track=music_track,
        )
        video_url = f"/api/videos/{job_id}/download"
        update_job(job_id, video_url=video_url)

        # 6. Optional auto-publish — AI-optimize title/description first
        youtube_url = None
        update_job(job_id, status="done", progress=100, stage="done", video_url=video_url)
        if req.publish_youtube:
            _stage(job_id, 95, "uploading to youtube")
            try:
                youtube_url = uploader_svc.upload_job(job_id, optimize=True)
            except Exception as e:  # noqa: BLE001
                logger.exception("[%s] auto-upload failed", job_id)
                update_job(job_id, upload_status="error", upload_error=str(e))

        update_job(job_id, status="done", progress=100, stage="done",
                   video_url=video_url, youtube_url=youtube_url)
        logger.info("[%s] pipeline complete", job_id)

    except Exception as e:  # noqa: BLE001
        logger.exception("[%s] pipeline failed", job_id)
        update_job(job_id, status="error", stage="error", error=str(e))
