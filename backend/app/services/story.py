"""Original content generation via Groq (free tier).

Produces: narration script + YouTube title + description + hashtags.
All original text -> copyright-clean -> monetizable.
"""
import json
import logging
from typing import Optional

from ..config import settings

logger = logging.getLogger(__name__)

_NICHE_HINTS = {
    "scary": "a tense, first-person horror micro-story with a twist ending",
    "motivation": "a punchy, uplifting motivational monologue",
    "facts": "a fast-paced list of surprising 'did you know' facts",
    "finance": "a clear, practical money/finance tip explained simply",
}

_SYSTEM = (
    "You write scripts for faceless vertical short-form videos (YouTube Shorts / Reels). "
    "Output must be ORIGINAL, copyright-free, and spoken-word friendly. "
    "Hook the viewer in the first sentence. No stage directions, no emojis in the script body, "
    "no markdown. The script MUST run AT LEAST 60 seconds when read aloud — roughly "
    "190-240 words. Never write less than a minute of narration; keep the tension/value "
    "going the whole way through with a strong payoff at the end."
)


def _client():
    from groq import Groq
    if not settings.GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY not set — required for content generation")
    return Groq(api_key=settings.GROQ_API_KEY)


def generate_content(topic: str, niche: str = "scary", language: str = "English") -> dict:
    """Return {script, title, description, hashtags, background_query}.
    `language` is the full instruction phrase for the script language."""
    style = _NICHE_HINTS.get(niche, _NICHE_HINTS["scary"])
    prompt = (
        f"Topic: {topic}\nStyle: {style}\n"
        f"Write the script AND title in {language}. Natural and idiomatic, "
        f"not translated-sounding. At least 60 seconds of narration (~190-240 words). "
        f"Keep hashtags and background_query in English.\n\n"
        "Return STRICT JSON with keys: "
        "script (string, the narration only), "
        "title (string, <=90 chars, catchy, include a hook), "
        "description (string, 1-2 sentences), "
        "hashtags (array of 5-8 short tags without the # symbol), "
        "background_query (string, 1-3 words describing fitting royalty-free b-roll)."
    )
    resp = _client().chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": prompt},
        ],
        temperature=0.9,
        response_format={"type": "json_object"},
    )
    data = json.loads(resp.choices[0].message.content)

    # Normalize / guard
    data.setdefault("script", topic)
    data.setdefault("title", topic[:90])
    data.setdefault("description", "")
    tags = data.get("hashtags") or []
    if isinstance(tags, str):
        tags = [t.strip().lstrip("#") for t in tags.split(",") if t.strip()]
    data["hashtags"] = [str(t).lstrip("#") for t in tags][:8] + ["Shorts"]
    data.setdefault("background_query", niche)
    logger.info("Generated script (%d chars) for niche=%s", len(data["script"]), niche)
    return data
