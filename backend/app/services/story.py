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
    "history": "a gripping retelling of a little-known historical event or figure",
    "truecrime": "a chilling true-crime-style case told with suspense (original/fictional)",
    "psychology": "a fascinating psychology fact or mind trick about human behavior",
    "space": "an awe-inspiring astronomy/space fact that reframes how we see the universe",
    "tech": "a surprising technology or AI insight explained for a general audience",
    "business": "a sharp business/startup lesson or case study with a takeaway",
    "health": "a practical, sensible health or fitness tip with the reasoning",
    "relationships": "a relatable dating/relationship insight or short story",
    "mystery": "an eerie unsolved mystery or unexplained phenomenon",
    "philosophy": "a thought-provoking philosophical idea made simple and vivid",
    "lifehacks": "a clever life hack that saves time, money, or effort",
    "comedy": "a witty, dry-humor take or absurd short story with a punchline",
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


_SEO_SYSTEM = (
    "You are a YouTube SEO expert for faceless short-form channels. Optimize "
    "metadata for maximum reach and click-through. Titles are punchy and "
    "keyword-rich (front-load the hook). Descriptions are 2-3 sentences with a "
    "soft call-to-action. Tags are high-intent search keywords."
)


def optimize_metadata(context: str, title: str = "", description: str = "") -> dict:
    """Return SEO-optimized {title, description, tags} for a YouTube Short."""
    prompt = (
        f"Video context / script:\n{context[:1500]}\n\n"
        f"Draft title: {title}\nDraft description: {description}\n\n"
        "Return STRICT JSON with keys: "
        "title (<=90 chars, hooky, keyword-rich), "
        "description (2-3 sentences + soft CTA, include 3-5 hashtags at the end), "
        "tags (array of 10-15 high-intent search keywords, no # symbol)."
    )
    resp = _client().chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[
            {"role": "system", "content": _SEO_SYSTEM},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
        response_format={"type": "json_object"},
    )
    data = json.loads(resp.choices[0].message.content)
    data.setdefault("title", title or "Short")
    data.setdefault("description", description or "")
    tags = data.get("tags") or []
    if isinstance(tags, str):
        tags = [t.strip().lstrip("#") for t in tags.split(",") if t.strip()]
    data["tags"] = [str(t).lstrip("#") for t in tags][:15] or ["Shorts"]
    logger.info("Optimized metadata: '%s' (%d tags)", data["title"][:50], len(data["tags"]))
    return data
