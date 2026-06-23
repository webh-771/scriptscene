"""Word-level caption timing via faster-whisper, rendered as karaoke-style
TextClips. Transcribes the generated narration to get per-word timestamps —
the defining look of short-form story videos.
"""
import logging
import string
from pathlib import Path
from typing import List, Dict

from ..config import settings, CAPTION_FONT

_PUNCT = set(string.punctuation)

logger = logging.getLogger(__name__)

_models = {}  # lazy singletons keyed by model name; load is expensive


def _get_model(name: str):
    if name not in _models:
        from faster_whisper import WhisperModel
        logger.info("Loading whisper model: %s", name)
        _models[name] = WhisperModel(
            name, device=settings.WHISPER_DEVICE, compute_type=settings.WHISPER_COMPUTE,
        )
    return _models[name]


def _model_for(language: str) -> str:
    # base is fast and fine for English; non-English (esp. Hindi/Urdu) needs a
    # bigger model to get the correct native script instead of boxes.
    if language and language != "en":
        return settings.WHISPER_MODEL_MULTILINGUAL
    return settings.WHISPER_MODEL


def transcribe_words(audio_path: Path, language: str = None) -> List[Dict]:
    """Return [{word, start, end}, ...] with timestamps in seconds."""
    segments, _ = _get_model(_model_for(language)).transcribe(
        str(audio_path), word_timestamps=True, language=language)
    words: List[Dict] = []
    for seg in segments:
        for w in (seg.words or []):
            token = w.word.strip()
            if token:
                words.append({"word": token, "start": float(w.start), "end": float(w.end)})
    logger.info("Transcribed %d words", len(words))
    return words


def _clean(words: List[Dict]) -> List[Dict]:
    """Merge punctuation-only tokens into the previous word; strip trailing
    punctuation from display so commas/periods don't land on their own line."""
    out: List[Dict] = []
    for w in words:
        tok = w["word"].strip()
        if tok and all(c in _PUNCT for c in tok):
            if out:
                out[-1]["end"] = w["end"]
            continue
        out.append({"word": tok.strip(string.punctuation), "start": w["start"], "end": w["end"]})
    return [w for w in out if w["word"]]


def group_words(words: List[Dict], per_group: int = 3, uppercase: bool = True) -> List[Dict]:
    """Chunk words into short on-screen groups (1-5 words at a time)."""
    words = _clean(words)
    groups = []
    for i in range(0, len(words), per_group):
        chunk = words[i:i + per_group]
        if not chunk:
            continue
        text = " ".join(w["word"] for w in chunk)
        groups.append({
            "text": text.upper() if uppercase else text,
            "start": chunk[0]["start"],
            "end": chunk[-1]["end"],
        })
    return groups


# Preset -> default highlight/accent color (matches the named looks).
PRESET_ACCENT = {
    "storytime": "#FF6FB5", "top5": "#22D3EE", "didyouknow": "#22C55E",
    "hottake": "#F97316", "explainer": "#38BDF8", "tutorial": "#8B5CF6",
    "mythbuster": "#EF4444", "casestudy": "#F59E0B",
}


def _ypos(position: str, clip_h: int, video_h: int):
    """Top-left y so text stays fully on-frame (with_position anchors top-left).
    Always clamped to a safe band so captions can never clip off-screen."""
    margin = int(video_h * 0.08)
    if position == "top":
        y = margin
    elif position == "bottom":
        y = video_h - clip_h - margin
    else:                                      # middle
        y = (video_h - clip_h) // 2
    # clamp so the whole clip (incl. stroke padding) stays on-frame
    return max(margin, min(y, video_h - clip_h - margin))


def build_caption_clips(words: List[Dict], video_w: int, video_h: int, style=None,
                        font=None):
    """Return moviepy TextClips styled per CaptionStyle (or sensible defaults).
    `font` overrides the caption font (used for non-Latin scripts)."""
    from moviepy import TextClip

    font = str(font or CAPTION_FONT)

    # style is a pydantic CaptionStyle or None
    color = getattr(style, "color", "#FFFFFF")
    highlight = getattr(style, "highlight", None) or PRESET_ACCENT.get(
        getattr(style, "preset", "storytime"), "#FFFFFF")
    position = getattr(style, "position", "middle")
    font_scale = getattr(style, "font_scale", 1.0)
    per_chunk = getattr(style, "words_per_chunk", 3)
    stroke_w = getattr(style, "stroke_width", 6)
    stroke_c = getattr(style, "stroke_color", "#000000")
    pill = getattr(style, "pill", "none")
    upper = getattr(style, "uppercase", True)

    font_size = int(video_w * 0.066 * font_scale)   # a touch smaller -> more breathing room
    box_w = int(video_w * 0.80)                      # wrap earlier, never touch frame edges
    bg_color = highlight if pill == "filled" else None

    clips = []
    for g in group_words(words, per_chunk, upper):
        duration = max(0.3, g["end"] - g["start"])
        kwargs = dict(
            font=font, text=g["text"], font_size=font_size,
            color=color, stroke_color=stroke_c, stroke_width=stroke_w,
            method="caption", size=(box_w, None), text_align="center",
            # transparent padding so the stroke on the last line isn't clipped
            # by the clip's own auto-sized canvas
            margin=(stroke_w + 8, stroke_w + 8),
        )
        if bg_color:
            kwargs["bg_color"] = bg_color
        txt = TextClip(**kwargs)
        # reserve stroke padding in the height used for placement so nothing clips
        eff_h = txt.h + 2 * stroke_w
        ypos = _ypos(position, eff_h, video_h)
        txt = (txt.with_start(g["start"]).with_duration(duration)
               .with_position(("center", ypos)))
        clips.append(txt)
    return clips
