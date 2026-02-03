from fastapi import FastAPI, APIRouter, HTTPException, BackgroundTasks, UploadFile, File, Query
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone
import json
import asyncio

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection (optional - app works without it)
try:
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    client = AsyncIOMotorClient(mongo_url, serverSelectionTimeoutMS=2000)
    # Test connection
    client.admin.command('ping')
    db = client[os.environ.get('DB_NAME', 'scriptscene')]
    logger = logging.getLogger(__name__)
    logger.info("MongoDB connected successfully")
except Exception as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"MongoDB connection failed: {e}. App will work without database.")
    client = None
    db = None

# Create the main app without a prefix
app = FastAPI(title="ScriptScene Video Generator API")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Import routers
from video_generator import video_router
from media_service import media_router
from music_service import music_router

# Define Models
class StatusCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StatusCheckCreate(BaseModel):
    client_name: str

# Add your routes to the router
@api_router.get("/")
async def root():
    return {"message": "ScriptScene API - Video Generation Powered by AI"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.model_dump()
    status_obj = StatusCheck(**status_dict)
    
    if db is not None:
        doc = status_obj.model_dump()
        doc['timestamp'] = doc['timestamp'].isoformat()
        _ = await db.status_checks.insert_one(doc)
    
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    if db is None:
        return []
    
    status_checks = await db.status_checks.find({}, {"_id": 0}).to_list(1000)
    
    for check in status_checks:
        if isinstance(check['timestamp'], str):
            check['timestamp'] = datetime.fromisoformat(check['timestamp'])
    
    return status_checks

# Include the routers
api_router.include_router(video_router, prefix="/video", tags=["video"])
api_router.include_router(media_router, prefix="/media", tags=["media"])
api_router.include_router(music_router, prefix="/music", tags=["music"])

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

# Create necessary directories
for directory in ['generated_videos', 'audio_files', 'temp_media']:
    Path(ROOT_DIR / directory).mkdir(exist_ok=True)