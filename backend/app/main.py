"""FastAPI entrypoint — app, CORS, router wiring only. No business logic."""
import logging

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from .config import settings
from .api import videos, publish

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

app = FastAPI(title="ScriptScene — Faceless Shorts Generator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(videos.router, prefix="/api")
app.include_router(publish.router, prefix="/api")


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "groq": bool(settings.GROQ_API_KEY),
        "youtube": bool(settings.YT_REFRESH_TOKEN),
        "broll": bool(settings.PEXELS_API_KEY or settings.PIXABAY_API_KEY),
    }
