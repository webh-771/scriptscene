"""Upload a finished vertical mp4 to YouTube as a Short.

Auth: OAuth 2.0 refresh-token (set up once, headless forever).
A 9:16 video <=3 min with #Shorts is auto-classified as a Short by YouTube.

Quota note: videos.insert costs 1600 units; default daily quota 10,000
=> ~6 uploads/day. Request a quota increase for more.
"""
import logging
from pathlib import Path
from typing import List

from ...config import settings

logger = logging.getLogger(__name__)


def _service():
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    if not (settings.YT_CLIENT_ID and settings.YT_CLIENT_SECRET and settings.YT_REFRESH_TOKEN):
        raise RuntimeError(
            "YouTube not configured. Set YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN "
            "(run scripts/youtube_auth.py once to get a refresh token)."
        )
    creds = Credentials(
        token=None,
        refresh_token=settings.YT_REFRESH_TOKEN,
        client_id=settings.YT_CLIENT_ID,
        client_secret=settings.YT_CLIENT_SECRET,
        token_uri="https://oauth2.googleapis.com/token",
        scopes=["https://www.googleapis.com/auth/youtube.upload"],
    )
    return build("youtube", "v3", credentials=creds, cache_discovery=False)


def upload_short(video_path: Path, title: str, description: str,
                 hashtags: List[str], privacy: str = "public") -> str:
    """Upload and return the watch URL."""
    from googleapiclient.http import MediaFileUpload

    tags = [t.lstrip("#") for t in hashtags]
    tag_line = " ".join(f"#{t}" for t in tags if t)
    full_desc = f"{description}\n\n{tag_line}".strip()
    if "#Shorts" not in full_desc:
        full_desc += " #Shorts"

    body = {
        "snippet": {"title": title[:100], "description": full_desc[:4900], "tags": tags[:15]},
        "status": {"privacyStatus": privacy, "selfDeclaredMadeForKids": False},
    }
    media = MediaFileUpload(str(video_path), chunksize=-1, resumable=True, mimetype="video/mp4")
    request = _service().videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        _status, response = request.next_chunk()

    video_id = response["id"]
    url = f"https://youtube.com/shorts/{video_id}"
    logger.info("Uploaded to YouTube: %s", url)
    return url
