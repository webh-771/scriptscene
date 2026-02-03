from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import os
import logging
from datetime import datetime, timezone
from pathlib import Path
import uuid
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import json
import google.generativeai as genai
from moviepy import VideoFileClip, ImageClip, TextClip, CompositeVideoClip, concatenate_videoclips, AudioFileClip, CompositeAudioClip, concatenate_audioclips
from moviepy.audio import fx as afx
import requests
from PIL import Image, ImageDraw, ImageFont
from elevenlabs import ElevenLabs
import io
import wave
import re
import base64
import time

logger = logging.getLogger(__name__)
video_router = APIRouter()

# MongoDB connection (optional)
try:
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    client = AsyncIOMotorClient(mongo_url, serverSelectionTimeoutMS=2000)
    client.admin.command('ping')
    db = client[os.environ.get('DB_NAME', 'scriptscene')]
    logger.info("MongoDB connected in video_generator")
except Exception as e:
    logger.warning(f"MongoDB not available in video_generator: {e}")
    client = None
    db = None

# Configure Gemini
gemini_api_key = os.environ.get('GEMINI_API_KEY', '')
if gemini_api_key:
    genai.configure(api_key=gemini_api_key)

ROOT_DIR = Path(__file__).parent
GENERATED_VIDEOS_DIR = ROOT_DIR / 'generated_videos'
AUDIO_FILES_DIR = ROOT_DIR / 'audio_files'
TEMP_MEDIA_DIR = ROOT_DIR / 'temp_media'

# Ensure directories exist
for directory in [GENERATED_VIDEOS_DIR, AUDIO_FILES_DIR, TEMP_MEDIA_DIR]:
    directory.mkdir(exist_ok=True)
video_router = APIRouter()

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Configure Gemini
gemini_api_key = os.environ.get('GEMINI_API_KEY', '')
if gemini_api_key:
    genai.configure(api_key=gemini_api_key)

ROOT_DIR = Path(__file__).parent
GENERATED_VIDEOS_DIR = ROOT_DIR / 'generated_videos'
AUDIO_FILES_DIR = ROOT_DIR / 'audio_files'
TEMP_MEDIA_DIR = ROOT_DIR / 'temp_media'

# Ensure directories exist
for directory in [GENERATED_VIDEOS_DIR, AUDIO_FILES_DIR, TEMP_MEDIA_DIR]:
    directory.mkdir(exist_ok=True)

class VideoGenerateRequest(BaseModel):
    script: str = Field(..., min_length=10, max_length=5000)
    music_url: Optional[str] = None
    voice_style: str = Field(default="Joanna")
    include_subtitles: bool = True
    video_duration: Optional[int] = None
    video_format: str = Field(default="vertical")  # "vertical" (9:16) or "horizontal" (16:9)

class VideoGenerateResponse(BaseModel):
    job_id: str
    status: str
    message: str

class VideoStatus(BaseModel):
    job_id: str
    status: str
    progress: int
    message: str
    video_url: Optional[str] = None
    error: Optional[str] = None

class VideoProject(BaseModel):
    job_id: str
    script: str
    created_at: str
    status: str
    video_url: Optional[str] = None

# In-memory job storage (in production, use Redis or database)
jobs_storage = {}

def split_script_into_sentences(script: str) -> List[str]:
    """Split script into sentences for processing"""
    sentences = re.split(r'[.!?]+', script)
    return [s.strip() for s in sentences if s.strip()]

def generate_voiceover_elevenlabs(script: str, voice_style: str = "Joanna") -> tuple:
    """Generate voiceover using ElevenLabs TTS"""
    try:
        elevenlabs_api_key = os.environ.get('ELEVENLABS_API_KEY', '')
        if not elevenlabs_api_key:
            raise Exception("ElevenLabs API key not found in environment")
        
        client = ElevenLabs(api_key=elevenlabs_api_key)
        
        audio_id = str(uuid.uuid4())
        audio_path = AUDIO_FILES_DIR / f"{audio_id}.mp3"
        
        # Generate audio using ElevenLabs
        logger.info(f"Generating voiceover with ElevenLabs...")
        audio_generator = client.text_to_speech.convert(
            text=script,
            voice_id="pNInz6obpgDQGcFmaJgB",  # Adam voice (default)
            model_id="eleven_turbo_v2_5"  # Updated to free tier compatible model
        )
        
        # Write audio to file
        with open(audio_path, 'wb') as f:
            for chunk in audio_generator:
                f.write(chunk)
        
        # Get audio duration
        audio_clip = AudioFileClip(str(audio_path))
        duration = audio_clip.duration
        audio_clip.close()
        
        logger.info(f"ElevenLabs TTS generated: {duration:.1f}s")
        return str(audio_path), duration
        
    except Exception as e:
        logger.error(f"ElevenLabs TTS error: {str(e)}")
        raise
def generate_subtitles_from_script(script: str, duration: float) -> List[Dict]:
    """Generate subtitle segments with timing"""
    sentences = split_script_into_sentences(script)
    if not sentences:
        return []
    
    time_per_sentence = duration / len(sentences)
    subtitles = []
    
    current_time = 0
    for sentence in sentences:
        if sentence:
            subtitles.append({
                'start': current_time,
                'end': current_time + time_per_sentence,
                'text': sentence
            })
            current_time += time_per_sentence
    
    return subtitles

def fetch_stock_images(keywords: List[str], count: int = 5) -> List[str]:
    """Fetch attention-grabbing stock images from Pexels"""
    pexels_api_key = os.environ.get('PEXELS_API_KEY', '')
    
    if not pexels_api_key:
        logger.warning("No Pexels API key found, using placeholders")
        return ["placeholder"] * count
    
    # Try Pexels API with improved search
    images = []
    for keyword in keywords[:count]:
        try:
            # Search with multiple results to pick the best one
            response = requests.get(
                "https://api.pexels.com/v1/search",
                headers={"Authorization": pexels_api_key},
                params={
                    "query": keyword, 
                    "per_page": 3,  # Get top 3 to pick the most engaging
                    "orientation": "portrait",
                    "size": "large",
                    "color": "vibrant"  # Prefer colorful, eye-catching images
                },
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                if data.get('photos') and len(data['photos']) > 0:
                    # Pick the first photo (Pexels sorts by popularity/relevance)
                    # Use original for highest quality
                    best_photo = data['photos'][0]
                    images.append(best_photo['src']['large2x'])
                    logger.info(f"Fetched engaging image for: '{keyword}' (photographer: {best_photo.get('photographer', 'unknown')})") 
                else:
                    logger.warning(f"No Pexels photos found for: {keyword}")
                    # Try a simpler search without the keyword
                    images.append("placeholder")
            else:
                logger.error(f"Pexels API error {response.status_code}: {response.text}")
                images.append("placeholder")
        except Exception as e:
            logger.error(f"Pexels API error for keyword '{keyword}': {str(e)}")
            images.append("placeholder")
    
    # Fill remaining with placeholders if we didn't get enough
    while len(images) < count:
        images.append("placeholder")
    
    real_count = len([i for i in images if i != 'placeholder'])
    logger.info(f"Fetched {real_count}/{count} real images, {count - real_count} placeholders")
    return images[:count]

def extract_keywords_from_script(script: str) -> List[str]:
    """Extract meaningful, contextual keywords from script for image search"""
    # Split into sentences to maintain context
    sentences = re.split(r'[.!?]+', script)
    
    # Enhanced stop words list
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
        'of', 'with', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should',
        'can', 'could', 'may', 'might', 'must', 'this', 'that', 'these', 'those',
        'your', 'our', 'just', 'now', 'get', 'make', 'take', 'use', 'see', 'know',
        'very', 'more', 'most', 'also', 'here', 'there', 'when', 'where', 'what'
    }
    
    # Extract keywords from each sentence for better context
    all_keywords = []
    for sentence in sentences:
        if not sentence.strip():
            continue
        
        words = re.findall(r'\b\w+\b', sentence.lower())
        # Get nouns, verbs, adjectives (words > 3 chars)
        meaningful = [w for w in words if w not in stop_words and len(w) > 3]
        
        # Take top 2-3 words per sentence for variety
        all_keywords.extend(meaningful[:3])
    
    # Remove duplicates while preserving order
    seen = set()
    unique_keywords = []
    for kw in all_keywords:
        if kw not in seen:
            seen.add(kw)
            unique_keywords.append(kw)
    
    # Add engaging visual modifiers to make images more attention-grabbing
    enhanced_keywords = []
    visual_enhancers = ['vibrant', 'dynamic', 'stunning', 'powerful', 'dramatic']
    
    for i, kw in enumerate(unique_keywords):
        # Every few keywords, add a visual enhancer for more engaging images
        if i % 3 == 0 and i < len(visual_enhancers):
            enhanced_keywords.append(f"{visual_enhancers[i % len(visual_enhancers)]} {kw}")
        else:
            enhanced_keywords.append(kw)
    
    # If we don't have enough, add engaging generic keywords
    if len(enhanced_keywords) < 8:
        engaging_keywords = [
            'stunning technology', 'dynamic business', 'vibrant innovation',
            'powerful success', 'creative future', 'dramatic growth',
            'modern lifestyle', 'inspiring achievement'
        ]
        enhanced_keywords.extend(engaging_keywords[:12 - len(enhanced_keywords)])
    
    logger.info(f"Extracted {len(enhanced_keywords)} contextual keywords: {enhanced_keywords[:5]}...")
    return enhanced_keywords

def create_placeholder_image(width: int, height: int, color: tuple, text: str = "") -> str:
    """Create a solid color placeholder image with optional text"""
    img = Image.new('RGB', (width, height), color)
    
    if text:
        draw = ImageDraw.Draw(img)
        try:
            # Try to use a nice font
            font = ImageFont.truetype("arial.ttf", 60)
        except Exception:
            # Fallback to default font
            font = ImageFont.load_default()
        
        # Get text size and center it
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        
        draw.text((x, y), text, fill='white', font=font)
    
    # Save to temp file
    temp_id = str(uuid.uuid4())
    img_path = TEMP_MEDIA_DIR / f"placeholder_{temp_id}.jpg"
    img.save(img_path, 'JPEG', quality=85)
    return str(img_path)

def create_subtitle_clip(subtitle_text: str, duration: float, video_size: tuple):
    """Create a subtitle text clip with styling - centered, smaller text"""
    try:
        from moviepy.video.VideoClip import TextClip
        
        # Use the Montserrat font with absolute path
        font_path = str(ROOT_DIR / "font" / "Montserrat-ExtraBold.ttf")
        
        # Create text clip - smaller font, centered position
        txt_clip = TextClip(
            text=subtitle_text,
            font=font_path,
            font_size=50,  # Smaller text
            color='white',
            stroke_color='black',  # Black outline for readability
            stroke_width=2,
            method='caption',
            size=(video_size[0] - 150, None)  # Width for text wrapping
        )
        
        # Position in CENTER of screen
        txt_clip = txt_clip.with_duration(duration).with_position('center')
        
        return txt_clip
    except Exception as e:
        logger.warning(f"TextClip creation failed: {e}. Skipping subtitles.")
        return None


async def generate_video_job(job_id: str, script: str, music_url: Optional[str], voice_style: str, include_subtitles: bool, video_format: str = "vertical"):
    """Background task to generate video"""
    try:
        # Set video dimensions based on format
        if video_format == "vertical":
            video_width, video_height = 1080, 1920  # 9:16 for YouTube Shorts
        else:
            video_width, video_height = 1920, 1080  # 16:9 for standard
        
        # Update status
        jobs_storage[job_id]['status'] = 'processing'
        jobs_storage[job_id]['progress'] = 10
        jobs_storage[job_id]['message'] = 'Generating voiceover...'
        
        audio_path, audio_duration = generate_voiceover_elevenlabs(script, voice_style)
        
        jobs_storage[job_id]['progress'] = 30
        jobs_storage[job_id]['message'] = 'Fetching stock media...'
        
        # Extract keywords and fetch images - MORE images for dynamic feel (2 per second)
        keywords = extract_keywords_from_script(script)
        # Calculate images needed: 2 images per second for fast-paced video
        images_needed = max(int(audio_duration * 2), 20)  # At least 20 images, 2 per second
        images_needed = min(images_needed, 100)  # Cap at 100 to prevent slowness
        
        # Use all unique keywords, repeat if needed for more images
        expanded_keywords = keywords.copy()
        while len(expanded_keywords) < images_needed:
            expanded_keywords.extend(keywords)
        
        # Use the first images_needed keywords
        image_urls = fetch_stock_images(expanded_keywords[:images_needed], count=images_needed)
        logger.info(f"Fetching {images_needed} images (2/sec) using {len(keywords)} keywords for {audio_duration:.1f}s video")
        
        jobs_storage[job_id]['progress'] = 50
        jobs_storage[job_id]['message'] = 'Creating video...'
        
        # Download images or create placeholders
        image_clips = []
        colors = [
            (255, 87, 87),   # Red
            (87, 255, 87),   # Green  
            (87, 87, 255),   # Blue
            (255, 255, 87),  # Yellow
            (255, 87, 255),  # Magenta
        ]
        
        for idx, img_url in enumerate(image_urls):
            if img_url == "placeholder":
                # Create placeholder image
                color = colors[idx % len(colors)]
                keyword = keywords[idx] if idx < len(keywords) else f"Scene {idx + 1}"
                img_path = create_placeholder_image(video_width, video_height, color, keyword.title())
                image_clips.append(img_path)
            else:
                # Download real image
                try:
                    response = requests.get(img_url, timeout=10)
                    img_path = TEMP_MEDIA_DIR / f"{job_id}_img_{idx}.jpg"
                    with open(img_path, 'wb') as f:
                        f.write(response.content)
                    image_clips.append(str(img_path))
                except Exception as e:
                    logger.error(f"Failed to download image: {str(e)}")
                    # Create placeholder as fallback
                    color = colors[idx % len(colors)]
                    keyword = keywords[idx] if idx < len(keywords) else f"Scene {idx + 1}"
                    img_path = create_placeholder_image(video_width, video_height, color, keyword.title())
                    image_clips.append(img_path)
        
        if not image_clips:
            raise Exception("Failed to fetch any images")
        
        jobs_storage[job_id]['progress'] = 55
        jobs_storage[job_id]['message'] = f'Processing {len(image_clips)} images...'
        logger.info(f"Downloaded {len(image_clips)} images, creating video clips...")
        
        # Create video from images with quick transitions (0.5-1 sec per image)
        clips = []
        clip_duration = max(0.5, audio_duration / len(image_clips))  # At least 0.5s per image
        
        logger.info(f"Creating video: {len(image_clips)} images, {clip_duration:.2f}s each")
        
        for idx, img_path in enumerate(image_clips):
            try:
                # Update progress for each image processed
                if idx % 5 == 0:  # Update every 5 images
                    progress = 55 + int((idx / len(image_clips)) * 10)
                    jobs_storage[job_id]['progress'] = progress
                    jobs_storage[job_id]['message'] = f'Creating clips... ({idx}/{len(image_clips)})'
                
                # Load image and resize to cover the frame (crop to fit)
                clip = ImageClip(img_path, duration=clip_duration)
                
                # Calculate resize to cover (crop center)
                img_aspect = clip.w / clip.h
                target_aspect = video_width / video_height
                
                if img_aspect > target_aspect:
                    # Image is wider, fit height and crop width
                    new_height = video_height
                    new_width = int(new_height * img_aspect)
                    clip = clip.resized(height=new_height)
                else:
                    # Image is taller, fit width and crop height
                    new_width = video_width
                    new_height = int(new_width / img_aspect)
                    clip = clip.resized(width=new_width)
                
                # Crop to exact size from center
                clip = clip.cropped(
                    x_center=clip.w/2, 
                    y_center=clip.h/2, 
                    width=video_width, 
                    height=video_height
                )
                clips.append(clip)
            except Exception as e:
                logger.error(f"Failed to process image {idx}: {str(e)}")
                # Continue with other images
                continue
        
        if not clips:
            raise Exception("No valid image clips created")
        
        jobs_storage[job_id]['progress'] = 65
        jobs_storage[job_id]['message'] = 'Composing video...'
        logger.info(f"Concatenating {len(clips)} clips...")
        
        video = concatenate_videoclips(clips, method="compose")
        
        # Add audio
        jobs_storage[job_id]['progress'] = 68
        jobs_storage[job_id]['message'] = 'Adding voiceover...'
        audio_clip = AudioFileClip(audio_path)
        video = video.with_audio(audio_clip)
        
        jobs_storage[job_id]['progress'] = 72
        jobs_storage[job_id]['message'] = 'Adding subtitles...'
        logger.info("Starting subtitle generation...")
        
        # Add subtitles
        if include_subtitles:
            try:
                subtitles = generate_subtitles_from_script(script, audio_duration)
                logger.info(f"Generated {len(subtitles)} subtitle segments")
                subtitle_clips = []
                
                for i, subtitle in enumerate(subtitles):
                    try:
                        txt_clip = create_subtitle_clip(
                            subtitle['text'],
                            subtitle['end'] - subtitle['start'],
                            (video_width, video_height)
                        )
                        if txt_clip:  # Only add if not None
                            txt_clip = txt_clip.with_start(subtitle['start'])
                            subtitle_clips.append(txt_clip)
                            logger.info(f"Created subtitle {i+1}/{len(subtitles)}: '{subtitle['text'][:30]}...'")
                    except Exception as e:
                        logger.warning(f"Failed to create subtitle {i+1}: {str(e)}")
                        continue
                
                if subtitle_clips:
                    logger.info(f"Compositing {len(subtitle_clips)} subtitle clips...")
                    jobs_storage[job_id]['progress'] = 75
                    jobs_storage[job_id]['message'] = f'Compositing {len(subtitle_clips)} subtitles...'
                    video = CompositeVideoClip([video] + subtitle_clips)
                    logger.info("Subtitles added successfully")
                else:
                    logger.warning("No subtitle clips created - skipping subtitles")
            except Exception as e:
                logger.error(f"Failed to add subtitles: {str(e)}")
                # Continue without subtitles
        else:
            logger.info("Subtitles disabled by user")
        
        jobs_storage[job_id]['progress'] = 85
        jobs_storage[job_id]['message'] = 'Adding background music...'
        
        # Add background music if provided
        if music_url:
            try:
                music_response = requests.get(music_url, timeout=30)
                music_path = TEMP_MEDIA_DIR / f"{job_id}_music.mp3"
                with open(music_path, 'wb') as f:
                    f.write(music_response.content)
                
                music_clip = AudioFileClip(str(music_path)).with_effects([afx.MultiplyVolume(0.3)])
                # Trim or loop music to match video duration
                if music_clip.duration > video.duration:
                    music_clip = music_clip.subclipped(0, video.duration)
                else:
                    # Loop music
                    loops = int(video.duration / music_clip.duration) + 1
                    music_clip = concatenate_audioclips([music_clip] * loops).subclipped(0, video.duration)
                
                # Mix audio
                final_audio = CompositeAudioClip([video.audio, music_clip])
                video = video.with_audio(final_audio)
            except Exception as e:
                logger.error(f"Failed to add music: {str(e)}")
        
        jobs_storage[job_id]['progress'] = 95
        jobs_storage[job_id]['message'] = 'Exporting video...'
        
        # Export video with optimized settings for speed
        output_path = GENERATED_VIDEOS_DIR / f"{job_id}.mp4"
        video.write_videofile(
            str(output_path),
            fps=24,  # Lower FPS for faster export
            codec='libx264',
            preset='ultrafast',  # Fastest encoding preset
            audio_codec='aac',
            threads=4,  # Limit threads to prevent overload
            temp_audiofile=str(TEMP_MEDIA_DIR / f"{job_id}_temp_audio.m4a"),
            remove_temp=True,
            logger=None  # Suppress moviepy logs
        )
        
        # Cleanup
        for img_path in image_clips:
            try:
                os.remove(img_path)
            except Exception:
                pass
        
        # Update job status
        jobs_storage[job_id]['status'] = 'completed'
        jobs_storage[job_id]['progress'] = 100
        jobs_storage[job_id]['message'] = 'Video generated successfully!'
        jobs_storage[job_id]['video_url'] = f"/api/video/download/{job_id}"
        
        # Save to database (if available)
        if db is not None:
            await db.video_projects.update_one(
                {"job_id": job_id},
                {"$set": {
                    "status": "completed",
                    "video_url": f"/api/video/download/{job_id}",
                    "completed_at": datetime.now(timezone.utc).isoformat()
                }}
            )
        
    except Exception as e:
        logger.error(f"Video generation failed for job {job_id}: {str(e)}")
        jobs_storage[job_id]['status'] = 'failed'
        jobs_storage[job_id]['error'] = str(e)
        jobs_storage[job_id]['message'] = f'Failed: {str(e)}'
        
        if db is not None:
            await db.video_projects.update_one(
                {"job_id": job_id},
                {"$set": {
                    "status": "failed",
                    "error": str(e)
                }}
            )

@video_router.post("/generate", response_model=VideoGenerateResponse)
async def generate_video(request: VideoGenerateRequest, background_tasks: BackgroundTasks):
    """Start video generation job"""
    job_id = str(uuid.uuid4())
    
    # Initialize job
    jobs_storage[job_id] = {
        'status': 'queued',
        'progress': 0,
        'message': 'Video generation queued',
        'video_url': None,
        'error': None
    }
    
    # Save to database (if available)
    if db is not None:
        project_doc = {
            "job_id": job_id,
            "script": request.script,
            "music_url": request.music_url,
            "voice_style": request.voice_style,
            "include_subtitles": request.include_subtitles,
            "video_format": request.video_format,
            "status": "queued",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.video_projects.insert_one(project_doc)
    
    # Start background task
    background_tasks.add_task(
        generate_video_job,
        job_id,
        request.script,
        request.music_url,
        request.voice_style,
        request.include_subtitles,
        request.video_format
    )
    
    return VideoGenerateResponse(
        job_id=job_id,
        status='queued',
        message='Video generation started'
    )

@video_router.get("/status/{job_id}", response_model=VideoStatus)
async def get_video_status(job_id: str):
    """Get video generation status"""
    if job_id not in jobs_storage:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs_storage[job_id]
    return VideoStatus(
        job_id=job_id,
        status=job['status'],
        progress=job['progress'],
        message=job['message'],
        video_url=job.get('video_url'),
        error=job.get('error')
    )

@video_router.get("/download/{job_id}")
async def download_video(job_id: str):
    """Download generated video"""
    video_path = GENERATED_VIDEOS_DIR / f"{job_id}.mp4"
    
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video not found")
    
    return FileResponse(
        path=str(video_path),
        media_type="video/mp4",
        filename=f"video_{job_id}.mp4"
    )

@video_router.get("/projects", response_model=List[VideoProject])
async def list_projects():
    """List all video projects"""
    if db is None:
        return []
    projects = await db.video_projects.find({}, {"_id": 0}).sort("created_at", -1).limit(50).to_list(50)
    return projects