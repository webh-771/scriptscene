"""Text-to-speech with pluggable engines.

  edge   - edge-tts cloud neural voices (free, no key, default)
  kokoro - Kokoro-82M local ONNX (most natural; needs model files in assets/models)

gTTS is the last-resort fallback if edge fails.
"""
import asyncio
import logging
from pathlib import Path
from typing import Optional

from ..config import settings

logger = logging.getLogger(__name__)

_kokoro = None  # lazy singleton — model load is expensive


# --- edge ---
async def _edge_async(text: str, voice: str, out_path: Path) -> None:
    import edge_tts
    await edge_tts.Communicate(text, voice).save(str(out_path))


def _edge(text: str, voice: str, out_path: Path) -> Path:
    asyncio.run(_edge_async(text, voice, out_path))
    if not (out_path.exists() and out_path.stat().st_size > 0):
        raise RuntimeError("edge-tts produced empty file")
    return out_path


def _gtts(text: str, out_path: Path) -> Path:
    from gtts import gTTS
    gTTS(text=text, lang="en").save(str(out_path))
    return out_path


# --- kokoro ---
def _get_kokoro():
    global _kokoro
    if _kokoro is None:
        from kokoro_onnx import Kokoro
        if not (settings.KOKORO_MODEL.exists() and settings.KOKORO_VOICES.exists()):
            raise RuntimeError(
                "Kokoro model files missing. Download kokoro-v1.0.onnx and "
                "voices-v1.0.bin into assets/models/ (see README)."
            )
        logger.info("Loading Kokoro model")
        _kokoro = Kokoro(str(settings.KOKORO_MODEL), str(settings.KOKORO_VOICES))
    return _kokoro


def _kokoro_tts(text: str, voice: str, out_path: Path) -> Path:
    import soundfile as sf
    samples, sr = _get_kokoro().create(text, voice=voice, speed=1.0, lang="en-us")
    wav_path = out_path.with_suffix(".wav")
    sf.write(str(wav_path), samples, sr)
    logger.info("Kokoro voiceover: %s (%s)", wav_path.name, voice)
    return wav_path


# --- public ---
def synthesize(text: str, out_path: Path, engine: Optional[str] = None,
               voice: Optional[str] = None) -> Path:
    """Write narration audio; returns the actual path (mp3 or wav)."""
    engine = engine or settings.TTS_ENGINE

    if engine == "kokoro":
        return _kokoro_tts(text, voice or settings.KOKORO_VOICE, out_path)

    # default: edge with gTTS fallback
    try:
        result = _edge(text, voice or settings.TTS_VOICE, out_path)
        logger.info("edge-tts voiceover: %s", result.name)
        return result
    except Exception as e:  # noqa: BLE001
        logger.warning("edge-tts failed (%s); falling back to gTTS", e)
        return _gtts(text, out_path)
