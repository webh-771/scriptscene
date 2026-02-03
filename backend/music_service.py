from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
import logging

logger = logging.getLogger(__name__)
music_router = APIRouter()

class MusicTrack(BaseModel):
    id: str
    title: str
    artist: str
    duration: int  # in seconds
    url: str
    genre: str

class MusicListResponse(BaseModel):
    tracks: List[MusicTrack]

# Free copyright-free music URLs from various sources
FREE_MUSIC_TRACKS = [
    {
        "id": "1",
        "title": "Sunny Day",
        "artist": "Free Music Archive",
        "duration": 180,
        "url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
        "genre": "upbeat"
    },
    {
        "id": "2",
        "title": "Calm Waves",
        "artist": "Free Music Archive",
        "duration": 165,
        "url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3",
        "genre": "ambient"
    },
    {
        "id": "3",
        "title": "Corporate Success",
        "artist": "Free Music Archive",
        "duration": 120,
        "url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3",
        "genre": "corporate"
    },
    {
        "id": "4",
        "title": "Tech Innovation",
        "artist": "Free Music Archive",
        "duration": 145,
        "url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-4.mp3",
        "genre": "electronic"
    },
    {
        "id": "5",
        "title": "Inspiring Journey",
        "artist": "Free Music Archive",
        "duration": 200,
        "url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-5.mp3",
        "genre": "inspirational"
    },
    {
        "id": "6",
        "title": "Gentle Piano",
        "artist": "Free Music Archive",
        "duration": 155,
        "url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-6.mp3",
        "genre": "piano"
    },
    {
        "id": "7",
        "title": "Happy Go Lucky",
        "artist": "Free Music Archive",
        "duration": 130,
        "url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-7.mp3",
        "genre": "cheerful"
    },
    {
        "id": "8",
        "title": "Cinematic Epic",
        "artist": "Free Music Archive",
        "duration": 220,
        "url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-8.mp3",
        "genre": "cinematic"
    }
]

@music_router.get("/list", response_model=MusicListResponse)
async def list_music_tracks(genre: str = None):
    """List available copyright-free music tracks"""
    tracks = FREE_MUSIC_TRACKS
    
    if genre:
        tracks = [t for t in tracks if t['genre'].lower() == genre.lower()]
    
    return MusicListResponse(tracks=[MusicTrack(**t) for t in tracks])

@music_router.get("/genres")
async def list_genres():
    """List available music genres"""
    genres = list(set(t['genre'] for t in FREE_MUSIC_TRACKS))
    return {"genres": genres}