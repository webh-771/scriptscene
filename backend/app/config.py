"""Single source of truth for configuration and paths.

All env access lives here so services never touch os.environ directly.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BACKEND_DIR / ".env")

# --- Directories ---
ASSETS_DIR = BACKEND_DIR / "assets"
FONTS_DIR = ASSETS_DIR / "fonts"
BACKGROUNDS_DIR = ASSETS_DIR / "backgrounds"      # user-supplied gameplay/loops
MUSIC_DIR = ASSETS_DIR / "music"
OUTPUT_DIR = BACKEND_DIR / "generated_videos"
WORK_DIR = BACKEND_DIR / "temp_media"              # scratch: audio, clips, frames
DB_PATH = BACKEND_DIR / "scriptscene.db"

for _d in (OUTPUT_DIR, WORK_DIR, BACKGROUNDS_DIR, MUSIC_DIR, FONTS_DIR):
    _d.mkdir(parents=True, exist_ok=True)

CAPTION_FONT = FONTS_DIR / "Montserrat-ExtraBold.ttf"


class Settings:
    """Lazily reads env; keeps a flat, typed-ish surface for services."""

    # LLM (Groq)
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
    GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")

    # TTS (Andrew/Ava/Emma/Brian = newer conversational voices, most natural)
    TTS_VOICE = os.environ.get("TTS_VOICE", "en-US-AndrewNeural")

    # Captions
    WHISPER_MODEL = os.environ.get("WHISPER_MODEL", "base")
    WHISPER_DEVICE = os.environ.get("WHISPER_DEVICE", "cpu")
    WHISPER_COMPUTE = os.environ.get("WHISPER_COMPUTE", "int8")

    # Royalty-free b-roll
    PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY", "")
    PIXABAY_API_KEY = os.environ.get("PIXABAY_API_KEY", "")

    # YouTube upload
    YT_CLIENT_ID = os.environ.get("YT_CLIENT_ID", "")
    YT_CLIENT_SECRET = os.environ.get("YT_CLIENT_SECRET", "")
    YT_REFRESH_TOKEN = os.environ.get("YT_REFRESH_TOKEN", "")

    # Video format
    WIDTH = int(os.environ.get("VIDEO_WIDTH", "1080"))
    HEIGHT = int(os.environ.get("VIDEO_HEIGHT", "1920"))
    FPS = int(os.environ.get("VIDEO_FPS", "30"))

    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*").split(",")


settings = Settings()
