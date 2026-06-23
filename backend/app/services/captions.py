"""Word-level caption timing via faster-whisper, rendered as karaoke-style
TextClips. Transcribes the generated narration to get per-word timestamps —
the defining look of short-form story videos.
"""
import logging
from pathlib import Path
from typing import List, Dict

from ..config import settings, CAPTION_FONT

logger = logging.getLogger(__name__)

_model = None  # lazy singleton; model load is expensive


def _get_model():
    global _model
    if _model is None:
        from faster_whisper import WhisperModel
        logger.info("Loading whisper model: %s", settings.WHISPER_MODEL)
        _model = WhisperModel(
            settings.WHISPER_MODEL,
            device=settings.WHISPER_DEVICE,
            compute_type=settings.WHISPER_COMPUTE,
        )
    return _model


def transcribe_words(audio_path: Path) -> List[Dict]:
    """Return [{word, start, end}, ...] with timestamps in seconds."""
    segments, _ = _get_model().transcribe(str(audio_path), word_timestamps=True)
    words: List[Dict] = []
    for seg in segments:
        for w in (seg.words or []):
            token = w.word.strip()
            if token:
                words.append({"word": token, "start": float(w.start), "end": float(w.end)})
    logger.info("Transcribed %d words", len(words))
    return words


def group_words(words: List[Dict], per_group: int = 3) -> List[Dict]:
    """Chunk words into short on-screen groups (1-3 words at a time)."""
    groups = []
    for i in range(0, len(words), per_group):
        chunk = words[i:i + per_group]
        if not chunk:
            continue
        groups.append({
            "text": " ".join(w["word"] for w in chunk).upper(),
            "start": chunk[0]["start"],
            "end": chunk[-1]["end"],
        })
    return groups


def build_caption_clips(words: List[Dict], video_w: int, video_h: int):
    """Return a list of moviepy TextClips positioned center-screen."""
    from moviepy import TextClip

    clips = []
    for g in group_words(words):
        duration = max(0.3, g["end"] - g["start"])
        txt = TextClip(
            font=str(CAPTION_FONT),
            text=g["text"],
            font_size=int(video_w * 0.10),
            color="white",
            stroke_color="black",
            stroke_width=8,
            method="caption",
            size=(int(video_w * 0.85), None),
            text_align="center",
        ).with_start(g["start"]).with_duration(duration).with_position(("center", "center"))
        clips.append(txt)
    return clips
