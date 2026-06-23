"""Pydantic request/response schemas."""
from typing import Optional
from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    # Few inputs -> full video. Everything else is auto.
    topic: str = Field(..., min_length=3, max_length=300,
                       description="What the video is about, e.g. 'a creepy story about an abandoned subway station'")
    niche: str = Field(default="scary", description="scary | motivation | facts | finance")
    voice: Optional[str] = None                 # edge-tts voice; falls back to settings
    background_query: Optional[str] = None      # b-roll search term; default derived from niche
    background_file: Optional[str] = None        # filename in assets/backgrounds to use instead of b-roll
    music: bool = True
    publish_youtube: bool = False               # if False -> save local only


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
