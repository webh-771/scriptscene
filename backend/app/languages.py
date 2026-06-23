"""Language registry: default voices per engine, whisper hint, and the font
script needed to render captions (non-Latin scripts need their own font).
"""
from .config import FONTS_DIR

# script -> caption font file (must live in assets/fonts)
SCRIPT_FONTS = {
    "latin": "Montserrat-ExtraBold.ttf",
    "devanagari": "NotoSansDevanagari-Bold.ttf",
    "cjk": "NotoSansCJK-Bold.ttf",
    "arabic": "NotoNaskhArabic-Bold.ttf",
}

# code -> config. kokoro_lang/kokoro_voice are None when Kokoro lacks that language
# (the pipeline then forces the edge engine).
# `prompt` is the exact phrasing handed to the LLM for the script language.
# Non-English uses the bigger whisper model (see pipeline) so the captions come
# out in the correct native script (e.g. Devanagari for Hindi, not Urdu/boxes).
LANGUAGES = {
    "en": dict(name="English",            whisper="en", kokoro_lang="en-us",
               kokoro="am_michael", piper="en_US-ryan-medium",
               script="latin", prompt="English"),
    "hi": dict(name="Hindi",              whisper="hi", kokoro_lang="hi",
               kokoro="hm_omega", piper="hi_IN-pratham-medium", script="devanagari",
               prompt="Hindi in its native Devanagari script — not romanized/transliterated"),
    "es": dict(name="Spanish",            whisper="es", kokoro_lang="es",
               kokoro="em_alex", script="latin", prompt="Spanish"),
    "fr": dict(name="French",             whisper="fr", kokoro_lang="fr-fr",
               kokoro="ff_siwis", script="latin", prompt="French"),
    "pt": dict(name="Portuguese",         whisper="pt", kokoro_lang="pt-br",
               kokoro="pm_alex", script="latin", prompt="Portuguese"),
    "it": dict(name="Italian",            whisper="it", kokoro_lang="it",
               kokoro="im_nicola", script="latin", prompt="Italian"),
}

DEFAULT = "en"


def get(code: str) -> dict:
    return LANGUAGES.get(code, LANGUAGES[DEFAULT])


def font_path(code: str):
    """Caption font for the language's script. Falls back to Latin if the
    script font isn't installed."""
    script = get(code)["script"]
    f = FONTS_DIR / SCRIPT_FONTS.get(script, SCRIPT_FONTS["latin"])
    if f.exists():
        return f
    return FONTS_DIR / SCRIPT_FONTS["latin"]
