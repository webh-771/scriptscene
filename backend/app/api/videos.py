"""Video generation routes — thin: validate, enqueue, report. No logic here."""
import uuid

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse

from ..config import OUTPUT_DIR, WORK_DIR
from ..db import create_job, get_job, list_jobs, delete_job as db_delete_job
from ..models import GenerateRequest, GenerateResponse, JobStatus
from ..services.pipeline import run_pipeline

router = APIRouter(prefix="/videos", tags=["videos"])


@router.post("/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    create_job(job_id, topic=req.topic, niche=req.niche)
    background_tasks.add_task(run_pipeline, job_id, req)
    return GenerateResponse(job_id=job_id, status="queued",
                            message="Generation started")


@router.get("/{job_id}/status", response_model=JobStatus)
async def status(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return JobStatus(**{k: job.get(k) for k in JobStatus.model_fields})


@router.get("/{job_id}/download")
async def download(job_id: str):
    path = OUTPUT_DIR / f"{job_id}.mp4"
    if not path.exists():
        raise HTTPException(404, "Video not ready")
    return FileResponse(path, media_type="video/mp4", filename=f"{job_id}.mp4")


@router.get("")
async def projects():
    return list_jobs()


@router.delete("/{job_id}")
async def delete(job_id: str):
    if not get_job(job_id):
        raise HTTPException(404, "Job not found")
    # remove the rendered video + any scratch files for this job
    (OUTPUT_DIR / f"{job_id}.mp4").unlink(missing_ok=True)
    for f in WORK_DIR.glob(f"{job_id}*"):
        f.unlink(missing_ok=True)
    db_delete_job(job_id)
    return {"deleted": job_id}
