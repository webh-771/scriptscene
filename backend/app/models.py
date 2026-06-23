"""Pydantic request/response schemas."""
from typing import Optional
from pydantic import BaseModel, Field


class CaptionStyle(BaseModel):
    preset: str = "storytime"                    # named look; sets sensible defaults
    color: str = "#FFFFFF"                       # current-word / base color
    highlight: Optional[str] = None              # active-word accent (defaults per preset)
    position: str = "middle"                     # top | middle | bottom
    font_scale: float = Field(default=1.0, ge=0.5, le=2.0)
    words_per_chunk: int = Field(default=3, ge=1, le=5)
    stroke_width: int = Field(default=6, ge=0, le=20)
    stroke_color: str = "#000000"
    pill: str = "none"                           # none | filled | outline
    uppercase: bool = True


class GenerateRequest(BaseModel):
    # --- content source (one of) ---
    topic: Optional[str] = Field(default=None, min_length=3, max_length=300)
    reddit_url: Optional[str] = None             # paste a Reddit post URL -> pull story
    script: Optional[str] = None                 # bring your own script verbatim

    niche: str = "scary"                         # scary | motivation | facts | finance
    language: str = "en"                         # en | hi | es | fr | de | pt | it | ja | ar

    # --- voice ---
    tts_engine: Optional[str] = None             # edge | kokoro (default from settings)
    voice: Optional[str] = None                  # engine-specific voice id

    # --- background ---
    background_type: str = "broll"               # broll | gameplay | gradient | solid | audiogram
    background_query: Optional[str] = None       # b-roll search term
    background_file: Optional[str] = None         # specific file in assets/backgrounds
    gradient: str = "aurora"                     # aurora | sunset | mint | violet | noir
    solid_color: str = "#101418"

    # --- format ---
    aspect: str = "9:16"                         # 9:16 | 1:1 | 16:9
    captions: CaptionStyle = Field(default_factory=CaptionStyle)
    music: bool = True
    music_volume: float = Field(default=0.12, ge=0.0, le=1.0)   # relative to narration

    publish_youtube: bool = False


class GenerateResponse(BaseModel):
    job_id: str
    status: str
    message: str


class JobStatus(BaseModel):
    job_id: str
    status: str            # queued | running | done | error
    progress: int          # 0-100
    stage: str
    script: Optional[str] = None
    title: Optional[str] = None
    video_url: Optional[str] = None
    youtube_url: Optional[str] = None
    error: Optional[str] = None
    created_at: str
