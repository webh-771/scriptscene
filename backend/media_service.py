from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import List, Optional
import requests
import os
import logging

logger = logging.getLogger(__name__)
media_router = APIRouter()

class MediaItem(BaseModel):
    id: str
    type: str  # 'image' or 'video'
    url: str
    thumbnail_url: str
    photographer: Optional[str] = None
    source: str  # 'pexels', 'unsplash', 'pixabay'

class MediaSearchResponse(BaseModel):
    items: List[MediaItem]
    total: int

@media_router.get("/search", response_model=MediaSearchResponse)
async def search_media(
    query: str = Query(..., min_length=1),
    media_type: str = Query("image", regex="^(image|video)$"),
    per_page: int = Query(10, ge=1, le=30)
):
    """Search for stock media from free APIs"""
    items = []
    
    if media_type == "image":
        # Try Unsplash (no API key needed for basic usage)
        try:
            unsplash_items = await search_unsplash(query, per_page)
            items.extend(unsplash_items)
        except Exception as e:
            logger.error(f"Unsplash search error: {str(e)}")
        
        # Try Pexels if API key is available
        pexels_api_key = os.environ.get('PEXELS_API_KEY')
        if pexels_api_key:
            try:
                pexels_items = await search_pexels_images(query, per_page, pexels_api_key)
                items.extend(pexels_items)
            except Exception as e:
                logger.error(f"Pexels search error: {str(e)}")
    
    elif media_type == "video":
        # Try Pexels videos
        pexels_api_key = os.environ.get('PEXELS_API_KEY')
        if pexels_api_key:
            try:
                video_items = await search_pexels_videos(query, per_page, pexels_api_key)
                items.extend(video_items)
            except Exception as e:
                logger.error(f"Pexels video search error: {str(e)}")
    
    return MediaSearchResponse(items=items[:per_page], total=len(items))

async def search_unsplash(query: str, per_page: int) -> List[MediaItem]:
    """Search Unsplash for images"""
    # Using Unsplash Source API (no key required)
    items = []
    
    # Generate multiple images with different parameters
    for i in range(min(per_page, 10)):
        img_url = f"https://source.unsplash.com/1920x1080/?{query.replace(' ', ',')}&sig={i}"
        items.append(MediaItem(
            id=f"unsplash_{i}",
            type="image",
            url=img_url,
            thumbnail_url=img_url,
            source="unsplash"
        ))
    
    return items

async def search_pexels_images(query: str, per_page: int, api_key: str) -> List[MediaItem]:
    """Search Pexels for images"""
    try:
        response = requests.get(
            "https://api.pexels.com/v1/search",
            headers={"Authorization": api_key},
            params={
                "query": query,
                "per_page": per_page,
                "orientation": "landscape"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            items = []
            
            for photo in data.get('photos', []):
                items.append(MediaItem(
                    id=str(photo['id']),
                    type="image",
                    url=photo['src']['large2x'],
                    thumbnail_url=photo['src']['medium'],
                    photographer=photo.get('photographer'),
                    source="pexels"
                ))
            
            return items
        
        return []
    
    except Exception as e:
        logger.error(f"Pexels API error: {str(e)}")
        return []

async def search_pexels_videos(query: str, per_page: int, api_key: str) -> List[MediaItem]:
    """Search Pexels for videos"""
    try:
        response = requests.get(
            "https://api.pexels.com/videos/search",
            headers={"Authorization": api_key},
            params={
                "query": query,
                "per_page": per_page,
                "orientation": "landscape"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            items = []
            
            for video in data.get('videos', []):
                # Get HD video file
                video_files = video.get('video_files', [])
                hd_file = next((f for f in video_files if f.get('quality') == 'hd'), video_files[0] if video_files else None)
                
                if hd_file:
                    items.append(MediaItem(
                        id=str(video['id']),
                        type="video",
                        url=hd_file['link'],
                        thumbnail_url=video.get('image', ''),
                        photographer=video.get('user', {}).get('name'),
                        source="pexels"
                    ))
            
            return items
        
        return []
    
    except Exception as e:
        logger.error(f"Pexels video API error: {str(e)}")
        return []