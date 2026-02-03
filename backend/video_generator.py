from fastapi import APIRouter, HTTPException, BackgroundTasks
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
from moviepy import *
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
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Generate audio
        response = model.generate_content(
            script,
            generation_config=genai.GenerationConfig(
                response_modalities=["AUDIO"],
                speech_config={"voice_config": {"prebuilt_voice_config": {"voice_name": voice_style}}}
            )
        )
        
        audio_data = response.parts[0].inline_data.data
        
        # Save audio temporarily
        audio_id = str(uuid.uuid4())
        audio_path = AUDIO_FILES_DIR / f"{audio_id}.wav"
        
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
    """Fetch stock images from Pexels"""
    pexels_api_key = os.environ.get('PEXELS_API_KEY', '')
    
    if not pexels_api_key:
        # Use Unsplash as fallback (no API key needed for basic usage)
        images = []
        for keyword in keywords[:count]:
            try:
                url = f"https://source.unsplash.com/1920x1080/?{keyword.replace(' ', ',')}"
                images.append(url)
            except:
                continue
        return images[:count]
    
    # Pexels implementation
    images = []
    for keyword in keywords[:count]:
        try:
            response = requests.get(
                f"https://api.pexels.com/v1/search",
                headers={"Authorization": pexels_api_key},
                params={"query": keyword, "per_page": 1, "orientation": "landscape"}
            )
            if response.status_code == 200:
                data = response.json()
                if data.get('photos'):
                    images.append(data['photos'][0]['src']['large'])
        except Exception as e:
            logger.error(f"Pexels API error: {str(e)}")
            continue
    
    return images

def extract_keywords_from_script(script: str) -> List[str]:
    """Extract keywords from script for image search"""
    # Simple keyword extraction (in production, use NLP)
    words = re.findall(r'\b\w+\b', script.lower())
    # Remove common words
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'is', 'are', 'was', 'were'}
    keywords = [w for w in words if w not in stop_words and len(w) > 3]
    return keywords[:5]

def create_subtitle_clip(subtitle_text: str, duration: float, video_size: tuple) -> TextClip:
    """Create a subtitle text clip with styling"""
    return TextClip(
        subtitle_text,
        fontsize=48,
        color='white',
        font='Arial-Bold',
        stroke_color='black',
        stroke_width=2,
        method='caption',
        size=(video_size[0] * 0.9, None),
        align='center'
    ).set_duration(duration).set_position(('center', 0.85), relative=True)

async def generate_video_job(job_id: str, script: str, music_url: Optional[str], voice_style: str, include_subtitles: bool):
    """Background task to generate video"""
    try:
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
        
        # Download images
        image_clips = []
        for idx, img_url in enumerate(image_urls):
            try:
                response = requests.get(img_url, timeout=10)
                img_path = TEMP_MEDIA_DIR / f"{job_id}_img_{idx}.jpg"
                with open(img_path, 'wb') as f:
                    f.write(response.content)
                image_clips.append(str(img_path))
            except Exception as e:
                logger.error(f"Failed to download image: {str(e)}")
                continue
        
        if not image_clips:
            raise Exception("Failed to fetch any images")
        
        # Create video from images
        clips = []
        clip_duration = audio_duration / len(image_clips)
        
        for img_path in image_clips:
            clip = ImageClip(img_path).set_duration(clip_duration).resize((1920, 1080))
            clips.append(clip)
        
        video = concatenate_videoclips(clips, method="compose")
        
        # Add audio
        audio_clip = AudioFileClip(audio_path)
        video = video.set_audio(audio_clip)
        
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
                    (1920, 1080)
                ).set_start(subtitle['start'])
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
                    music_clip = music_clip.subclip(0, video.duration)
                else:
                    # Loop music
                    loops = int(video.duration / music_clip.duration) + 1
                    music_clip = concatenate_audioclips([music_clip] * loops).subclip(0, video.duration)
                
                # Mix audio
                final_audio = CompositeAudioClip([video.audio, music_clip])
                video = video.set_audio(final_audio)
            except Exception as e:
                logger.error(f"Failed to add music: {str(e)}")
        
        jobs_storage[job_id]['progress'] = 95
        jobs_storage[job_id]['message'] = 'Exporting video...'
        
        # Export video
        output_path = GENERATED_VIDEOS_DIR / f"{job_id}.mp4"
        video.write_videofile(
            str(output_path),
            fps=24,
            codec='libx264',
            audio_codec='aac',
            temp_audiofile=str(TEMP_MEDIA_DIR / f"{job_id}_temp_audio.m4a"),
            remove_temp=True
        )
        
        # Cleanup
        for img_path in image_clips:
            try:
                os.remove(img_path)
            except:
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
        request.include_subtitles
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