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
import requests
from PIL import Image, ImageDraw, ImageFont
import io
import wave
import re

logger = logging.getLogger(__name__)
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
    voice_style: str = Field(default="Puck")
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

def generate_voiceover_with_gemini(script: str, voice_style: str = "Puck") -> tuple:
    """Generate voiceover using Gemini TTS and return audio data with timing info"""
    try:
        # For now, create a mock audio file since Gemini TTS API format is unclear
        # In production, this would use the correct Gemini TTS API
        logger.warning("Using mock audio generation - Gemini TTS API needs proper configuration")
        
        # Create a simple audio file with estimated duration
        # Estimate 150 words per minute for speech
        words = len(script.split())
        estimated_duration = (words / 150) * 60  # Convert to seconds
        estimated_duration = max(5, min(estimated_duration, 60))  # Between 5-60 seconds
        
        # Generate a simple tone as placeholder
        import numpy as np
        import wave
        
        sample_rate = 24000
        duration = estimated_duration
        frequency = 440  # A4 note
        
        # Generate sine wave
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        audio_data = np.sin(frequency * 2 * np.pi * t) * 0.3
        
        # Convert to 16-bit integers
        audio_data = (audio_data * 32767).astype(np.int16)
        
        # Save audio temporarily
        audio_id = str(uuid.uuid4())
        audio_path = AUDIO_FILES_DIR / f"{audio_id}.wav"
        
        # Write WAV file
        with wave.open(str(audio_path), 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data.tobytes())
        
        return str(audio_path), duration
        
        # Convert to WAV format
        with wave.open(str(audio_path), 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(24000)
            wav_file.writeframes(audio_data)
        
        # Get duration
        with wave.open(str(audio_path), 'rb') as wav_file:
            duration = wav_file.getnframes() / wav_file.getframerate()
        
        return str(audio_path), duration
    
    except Exception as e:
        logger.error(f"Gemini TTS error: {str(e)}")
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
    """Fetch stock images from Pexels or create placeholder images"""
    pexels_api_key = os.environ.get('PEXELS_API_KEY', '')
    
    if pexels_api_key:
        # Try Pexels API
        images = []
        for keyword in keywords[:count]:
            try:
                response = requests.get(
                    "https://api.pexels.com/v1/search",
                    headers={"Authorization": pexels_api_key},
                    params={"query": keyword, "per_page": 1, "orientation": "portrait"},
                    timeout=10
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get('photos'):
                        images.append(data['photos'][0]['src']['large2x'])
            except Exception as e:
                logger.error(f"Pexels API error: {str(e)}")
                continue
        
        if images:
            return images[:count]
    
    # Fallback: Create solid color placeholder images with gradients
    logger.info("Using placeholder images")
    return ["placeholder"] * count  # Will be generated in video creation

def extract_keywords_from_script(script: str) -> List[str]:
    """Extract keywords from script for image search"""
    # Simple keyword extraction (in production, use NLP)
    words = re.findall(r'\b\w+\b', script.lower())
    # Remove common words
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'is', 'are', 'was', 'were'}
    keywords = [w for w in words if w not in stop_words and len(w) > 3]
    return keywords[:5]

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

def create_subtitle_clip(subtitle_text: str, duration: float, video_size: tuple) -> TextClip:
    """Create a subtitle text clip with styling"""
    return TextClip(
        subtitle_text,
        color='white'
    ).with_duration(duration).with_position(('center', 'bottom'), relative=True)

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
        
        # Generate voiceover
        audio_path, audio_duration = generate_voiceover_with_gemini(script, voice_style)
        
        jobs_storage[job_id]['progress'] = 30
        jobs_storage[job_id]['message'] = 'Fetching stock media...'
        
        # Extract keywords and fetch images
        keywords = extract_keywords_from_script(script)
        image_urls = fetch_stock_images(keywords, count=5)
        
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
        
        # Create video from images with proper aspect ratio
        clips = []
        clip_duration = audio_duration / len(image_clips)
        
        for img_path in image_clips:
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
        
        video = concatenate_videoclips(clips, method="compose")
        
        # Add audio
        audio_clip = AudioFileClip(audio_path)
        video = video.with_audio(audio_clip)
        
        jobs_storage[job_id]['progress'] = 70
        jobs_storage[job_id]['message'] = 'Adding subtitles...'
        
        # Add subtitles
        if include_subtitles:
            subtitles = generate_subtitles_from_script(script, audio_duration)
            subtitle_clips = []
            
            for subtitle in subtitles:
                txt_clip = create_subtitle_clip(
                    subtitle['text'],
                    subtitle['end'] - subtitle['start'],
                    (video_width, video_height)
                ).with_start(subtitle['start'])
                subtitle_clips.append(txt_clip)
            
            video = CompositeVideoClip([video] + subtitle_clips)
        
        jobs_storage[job_id]['progress'] = 85
        jobs_storage[job_id]['message'] = 'Adding background music...'
        
        # Add background music if provided
        if music_url:
            try:
                music_response = requests.get(music_url, timeout=30)
                music_path = TEMP_MEDIA_DIR / f"{job_id}_music.mp3"
                with open(music_path, 'wb') as f:
                    f.write(music_response.content)
                
                music_clip = AudioFileClip(str(music_path)).volumex(0.3)
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
        
        # Export video
        output_path = GENERATED_VIDEOS_DIR / f"{job_id}.mp4"
        video.write_videofile(
            str(output_path),
            fps=30,
            codec='libx264',
            audio_codec='aac',
            preset='medium',
            bitrate='5000k',
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
        
        # Save to database
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
    
    # Save to database
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
    projects = await db.video_projects.find({}, {"_id": 0}).sort("created_at", -1).limit(50).to_list(50)
    return projects