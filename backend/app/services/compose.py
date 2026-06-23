"""Stitch background + word captions + narration (+ optional music) into a
vertical 9:16 mp4 ready for Shorts/Reels.
"""
import logging
import random
from pathlib import Path
from typing import List, Optional

from ..config import settings, MUSIC_DIR, OUTPUT_DIR
from . import captions as captions_svc

logger = logging.getLogger(__name__)


def _fit_vertical(clip, duration: float, w: int, h: int):
    """Loop/trim to `duration`, then cover-crop to exactly w x h."""
    from moviepy import concatenate_videoclips

    clip = clip.without_audio()

    # Loop to cover the needed duration
    if clip.duration < duration:
        loops = int(duration // clip.duration) + 1
        clip = concatenate_videoclips([clip] * loops)

    # Random start window, then trim
    max_start = max(0, clip.duration - duration)
    start = random.uniform(0, max_start) if max_start > 0 else 0
    clip = clip.subclipped(start, start + duration)

    # Cover-crop: scale so it fills, then center-crop
    scale = max(w / clip.w, h / clip.h)
    clip = clip.resized((round(clip.w * scale), round(clip.h * scale)))
    clip = clip.cropped(width=w, height=h, x_center=clip.w / 2, y_center=clip.h / 2)
    return clip


def _pick_music() -> Optional[Path]:
    tracks = [p for p in MUSIC_DIR.glob("*.mp3")]
    return random.choice(tracks) if tracks else None


def compose_video(
    job_id: str,
    background_path: Path,
    narration_path: Path,
    words: List[dict],
    with_music: bool = True,
) -> Path:
    from moviepy import VideoFileClip, AudioFileClip, CompositeVideoClip, CompositeAudioClip

    w, h, fps = settings.WIDTH, settings.HEIGHT, settings.FPS

    narration = AudioFileClip(str(narration_path))
    duration = narration.duration

    bg = VideoFileClip(str(background_path))
    base = _fit_vertical(bg, duration, w, h)

    caption_clips = captions_svc.build_caption_clips(words, w, h)
    video = CompositeVideoClip([base, *caption_clips], size=(w, h)).with_duration(duration)

    # Audio: narration + optional ducked background music
    audio = narration
    if with_music:
        track = _pick_music()
        if track:
            music = AudioFileClip(str(track)).with_volume_scaled(0.12)
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

    for c in (narration, bg, video):
        try:
            c.close()
        except Exception:  # noqa: BLE001
            pass

    logger.info("Composed video: %s (%.1fs)", out_path.name, duration)
    return out_path
