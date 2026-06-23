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
LANGUAGES = {
    "en": dict(name="English",    edge="en-US-AndrewNeural",  whisper="en",
               kokoro_lang="en-us", kokoro="am_michael", script="latin"),
    "hi": dict(name="Hindi",      edge="hi-IN-MadhurNeural",  whisper="hi",
               kokoro_lang="hi",    kokoro="hm_omega",   script="devanagari"),
    "es": dict(name="Spanish",    edge="es-ES-AlvaroNeural",  whisper="es",
               kokoro_lang="es",    kokoro="em_alex",    script="latin"),
    "fr": dict(name="French",     edge="fr-FR-HenriNeural",   whisper="fr",
               kokoro_lang="fr-fr", kokoro="ff_siwis",   script="latin"),
    "de": dict(name="German",     edge="de-DE-ConradNeural",  whisper="de",
               kokoro_lang=None,    kokoro=None,         script="latin"),
    "pt": dict(name="Portuguese", edge="pt-BR-AntonioNeural", whisper="pt",
               kokoro_lang="pt-br", kokoro="pm_alex",    script="latin"),
    "it": dict(name="Italian",    edge="it-IT-DiegoNeural",   whisper="it",
               kokoro_lang="it",    kokoro="im_nicola",  script="latin"),
    "ja": dict(name="Japanese",   edge="ja-JP-KeitaNeural",   whisper="ja",
               kokoro_lang="ja",    kokoro="jm_kumo",    script="cjk"),
    "ar": dict(name="Arabic",     edge="ar-SA-HamedNeural",   whisper="ar",
               kokoro_lang=None,    kokoro=None,         script="arabic"),
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
