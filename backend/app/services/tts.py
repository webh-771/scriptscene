"""Free neural TTS via edge-tts, with gTTS fallback. No API key needed."""
import asyncio
import logging
from pathlib import Path
from typing import Optional

from ..config import settings

logger = logging.getLogger(__name__)


async def _edge_tts(text: str, voice: str, out_path: Path) -> None:
    import edge_tts
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(out_path))


def _gtts_fallback(text: str, out_path: Path) -> None:
    from gtts import gTTS
    gTTS(text=text, lang="en").save(str(out_path))


def synthesize(text: str, out_path: Path, voice: Optional[str] = None) -> Path:
    """Write narration mp3 to out_path. Returns the path."""
    voice = voice or settings.TTS_VOICE
    try:
        asyncio.run(_edge_tts(text, voice, out_path))
        if out_path.exists() and out_path.stat().st_size > 0:
            logger.info("edge-tts voiceover: %s (%s)", out_path.name, voice)
            return out_path
        raise RuntimeError("edge-tts produced empty file")
    except Exception as e:  # noqa: BLE001 — fall back on any edge-tts failure
        logger.warning("edge-tts failed (%s); falling back to gTTS", e)
        _gtts_fallback(text, out_path)
        logger.info("gTTS voiceover: %s", out_path.name)
        return out_path
