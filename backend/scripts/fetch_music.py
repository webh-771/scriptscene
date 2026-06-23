"""Populate assets/music with copyright-free (CC-BY / CC-BY-SA) tracks from
Jamendo. Run once to build a library; the app also auto-fetches on demand.

Usage:
  python scripts/fetch_music.py [mood] [count]
  mood: scary | motivation | facts | finance | default   (default: default)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services import music   # noqa: E402


def main():
    mood = sys.argv[1] if len(sys.argv) > 1 else "default"
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    paths = music.fetch_music(mood, count)
    print(f"Downloaded {len(paths)} track(s) into assets/music:")
    for p in paths:
        print("  ", p.name)


if __name__ == "__main__":
    main()
