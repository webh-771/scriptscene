"""One-time helper: obtain a YouTube refresh token for headless uploads.

Prereqs (Google Cloud Console):
  1. Enable "YouTube Data API v3"
  2. OAuth consent screen -> External -> set to Production (avoids 7-day token expiry)
     -> add scope: .../auth/youtube.upload
  3. Create OAuth client (type: Desktop) -> download client_secret.json next to this file

Run:  python scripts/youtube_auth.py
Then copy the printed values into backend/.env:
  YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN
"""
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
SECRET = Path(__file__).parent / "client_secret.json"


def main():
    if not SECRET.exists():
        raise SystemExit(f"Missing {SECRET}. Download OAuth Desktop client JSON there first.")
    flow = InstalledAppFlow.from_client_secrets_file(str(SECRET), SCOPES)
    creds = flow.run_local_server(port=0)
    print("\n--- add these to backend/.env ---")
    print(f"YT_CLIENT_ID={creds.client_id}")
    print(f"YT_CLIENT_SECRET={creds.client_secret}")
    print(f"YT_REFRESH_TOKEN={creds.refresh_token}")


if __name__ == "__main__":
    main()
