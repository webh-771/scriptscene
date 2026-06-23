"""Pull a story from a Reddit post URL via the public .json endpoint (no auth).

Returns cleaned narration-ready text + a title. Trims the typical Reddit
throat-clearing so the hook lands early.
"""
import logging
import re

import requests

logger = logging.getLogger(__name__)

# Reddit blocks generic/datacenter UAs. A browser UA works from most
# residential IPs; for reliable/high-volume use, switch to the OAuth API (PRAW).
_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")


def fetch_story(url: str) -> dict:
    """Return {title, script} from a Reddit submission URL."""
    clean = url.split("?")[0].rstrip("/")
    api = clean + ".json"
    r = requests.get(api, headers={"User-Agent": _UA}, timeout=20)
    r.raise_for_status()
    data = r.json()

    post = data[0]["data"]["children"][0]["data"]
    title = post.get("title", "").strip()
    body = post.get("selftext", "").strip()

    if not body:
        raise RuntimeError("Reddit post has no text body (link/image post?)")

    body = _clean(body)
    script = f"{title}. {body}" if title else body
    logger.info("Fetched Reddit story: '%s' (%d chars)", title[:60], len(script))
    return {"title": title or "Reddit Story", "script": script}


def _clean(text: str) -> str:
    text = re.sub(r"http\S+", "", text)                 # strip links
    text = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", text)      # markdown links -> text
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"\bEDIT:.*$", "", text, flags=re.I | re.M)   # drop edits
    text = re.sub(r"\bTL;?DR:?.*$", "", text, flags=re.I | re.M)
    text = re.sub(r"\s+", " ", text).strip()
    return text
