"""Stitch background + word captions + narration (+ optional music) into a
vertical 9:16 mp4 ready for Shorts/Reels.
"""
import logging
import random
from pathlib import Path
from typing import List, Optional

from ..config import settings, MUSIC_DIR, OUTPUT_DIR
from . import captions as captions_svc
from . import visuals as visuals_svc

logger = logging.getLogger(__name__)


def _cover_crop(clip, w: int, h: int):
    """Scale to fill then center-crop to exactly w x h (9:16)."""
    scale = max(w / clip.w, h / clip.h)
    clip = clip.resized((round(clip.w * scale), round(clip.h * scale)))
    return clip.cropped(width=w, height=h, x_center=clip.w / 2, y_center=clip.h / 2)


def _segment_of_length(src, length: float):
    """A `length`-second piece of src: random window if long enough, else loop
    the clip onto itself (never reuses a *different* video)."""
    from moviepy import concatenate_videoclips
    if src.duration >= length:
        start = random.uniform(0, src.duration - length)
        return src.subclipped(start, start + length)
    loops = int(length // src.duration) + 1
    return concatenate_videoclips([src] * loops).subclipped(0, length)


def _build_background(paths: List[Path], duration: float, w: int, h: int):
    """Stitch the background so EACH clip is shown exactly once, in order —
    never repeating a clip. Segment length = duration / number of clips."""
    from moviepy import concatenate_videoclips
    from moviepy import VideoFileClip

    sources = [VideoFileClip(str(p)).without_audio() for p in paths]
    n = max(1, len(sources))
    seg_len = duration / n

    segments = []
    for src in sources:
        seg = _segment_of_length(src, seg_len)
        segments.append(_cover_crop(seg, w, h))

    bg = concatenate_videoclips(segments).subclipped(0, duration)
    return bg, sources


def _pick_music() -> Optional[Path]:
    tracks = [p for p in MUSIC_DIR.glob("*.mp3")]
    return random.choice(tracks) if tracks else None


def _build_base(spec: dict, narration_path: Path, duration: float, w: int, h: int):
    """Return (base_clip, sources_to_close) for the requested background type."""
    btype = spec.get("type", "broll")
    if btype in ("broll", "gameplay") and spec.get("paths"):
        return _build_background(spec["paths"], duration, w, h)
    if btype == "gradient":
        return visuals_svc.gradient_clip(spec.get("gradient", "aurora"), duration, w, h), []
    if btype == "solid":
        return visuals_svc.solid_clip(spec.get("solid", "#101418"), duration, w, h), []
    if btype == "audiogram":
        return visuals_svc.audiogram_clip(narration_path, duration, w, h), []
    # fallback: solid
    return visuals_svc.solid_clip("#101418", duration, w, h), []


def compose_video(
    job_id: str,
    bg_spec: dict,
    narration_path: Path,
    words: List[dict],
    w: int,
    h: int,
    style=None,
    font=None,
    with_music: bool = True,
    music_volume: float = 0.12,
    music_track=None,
) -> Path:
    from moviepy import AudioFileClip, CompositeVideoClip, CompositeAudioClip

    fps = settings.FPS

    narration = AudioFileClip(str(narration_path))
    duration = narration.duration

    base, bg_sources = _build_base(bg_spec, narration_path, duration, w, h)

    caption_clips = captions_svc.build_caption_clips(words, w, h, style, font=font)
    video = CompositeVideoClip([base, *caption_clips], size=(w, h)).with_duration(duration)

    # Audio: narration + optional ducked background music
    audio = narration
    if with_music and music_volume > 0:
        track = music_track or _pick_music()
        if track:
            music = AudioFileClip(str(track)).with_volume_scaled(music_volume)
            if music.duration < duration:
                music = music.with_duration(music.duration)  # keep as-is; short music ok
            else:
                music = music.subclipped(0, duration)
            audio = CompositeAudioClip([narration, music])

    video = video.with_audio(audio)

    out_path = OUTPUT_DIR / f"{job_id}.mp4"
    video.write_videofile(
        str(out_path),
        fps=fps,
        codec="libx264",
        audio_codec="aac",
        bitrate="5000k",
        threads=4,
        logger=None,
    )

    for c in [narration, video, *bg_sources]:
        try:
            c.close()
        except Exception:  # noqa: BLE001
            pass

    logger.info("Composed video: %s (%.1fs)", out_path.name, duration)
    return out_path
