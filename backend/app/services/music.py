"""Copyright-free background music via the Jamendo API.

Only commercially-usable licenses are requested (ccnc=false, ccnd=false) ->
CC-BY / CC-BY-SA, so output stays monetizable (attribution belongs in the
video description). Downloaded tracks are cached in assets/music and reused.
"""
import logging

import requests

from ..config import settings, MUSIC_DIR

logger = logging.getLogger(__name__)

_API = "https://api.jamendo.com/v3.0/tracks/"

# niche -> Jamendo tag query for a fitting mood
MOOD_TAGS = {
    "scary": "dark+ambient",
    "motivation": "epic+inspiring",
    "facts": "ambient+corporate",
    "finance": "corporate+calm",
    "default": "ambient+instrumental",
}


def fetch_music(mood: str = "default", count: int = 3) -> list:
    """Download up to `count` mood-fitting CC tracks into MUSIC_DIR; return paths."""
    cid = settings.JAMENDO_CLIENT_ID
    if not cid:
        raise RuntimeError("JAMENDO_CLIENT_ID not set")
    tags = MOOD_TAGS.get(mood, MOOD_TAGS["default"])
    r = requests.get(_API, params={
        "client_id": cid, "format": "json", "limit": count,
        "audioformat": "mp32", "tags": tags,
        "ccnc": "false", "ccnd": "false",          # commercial-usable only
        "order": "popularity_total", "vocalinstrumental": "instrumental",
    }, timeout=20)
    r.raise_for_status()
    tracks = r.json().get("results", [])
    paths = []
    for t in tracks:
        dest = MUSIC_DIR / f"jamendo_{t['id']}.mp3"
        if not dest.exists():
            try:
                _download(t["audio"], dest)
            except Exception as e:  # noqa: BLE001
                logger.warning("music download failed (%s): %s", t.get("name"), e)
                continue
        paths.append(dest)
    logger.info("Fetched %d music track(s) for mood=%s", len(paths), mood)
    return paths


def ensure_music(mood: str = "default") -> None:
    """If the music library is empty, pull a few tracks so music can play."""
    if any(MUSIC_DIR.glob("*.mp3")):
        return
    try:
        fetch_music(mood, 3)
    except Exception as e:  # noqa: BLE001
        logger.warning("could not auto-fetch music: %s", e)


def _download(url: str, dest) -> None:
    with requests.get(url, stream=True, timeout=60) as resp:
        resp.raise_for_status()
        with open(dest, "wb") as fh:
            for chunk in resp.iter_content(chunk_size=1 << 16):
                fh.write(chunk)
