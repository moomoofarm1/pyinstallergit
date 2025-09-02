"""
Diarization Server

This module implements a FastAPI server for speaker diarization using pyannote.audio.
The server provides REST API endpoints for processing audio files and returning
diarization results in RTTM format.

The server is designed to run in its own virtual environment with pyannote.audio
and related dependencies installed.
"""

import os
import sys
from pathlib import Path
import logging
import tempfile
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Add the parent directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from communication.json_protocol import JsonProtocol, MessageType, ProcessingStatus
from diarization.pipeline import DiarizationPipeline
from diarization.rttm_handler import RTTMHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Pydantic models for request/response
class DiarizationRequest(BaseModel):
    """Request model for diarization processing."""
    
    audio_file_path: str
    min_speakers: Optional[int] = 1
    max_speakers: Optional[int] = 10
    clustering_method: Optional[str] = "spectral"
    output_format: Optional[str] = "rttm"
    job_id: Optional[str] = None

class DiarizationResponse(BaseModel):
    """Response model for diarization processing."""
    
    job_id: str
    status: str
    message: str
    output_files: List[str] = []
    num_speakers: Optional[int] = None
    total_speech_time: Optional[float] = None
    processing_time_seconds: Optional[float] = None

class HealthResponse(BaseModel):
    """Response model for health check."""
    
    status: str
    service: str
    version: str
    uptime_seconds: float

# Global variables for server state
app = FastAPI(
    title="ALF Diarization Server",
    description="Speaker diarization service using pyannote.audio",
    version="0.2.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
json_protocol: Optional[JsonProtocol] = None
diarization_pipeline: Optional[DiarizationPipeline] = None
rttm_handler: Optional[RTTMHandler] = None
server_start_time: float = 0.0
active_jobs: Dict[str, Dict[str, Any]] = {}

@app.on_event("startup")
async def startup_event():
    """Initialize server components on startup."""
    global json_protocol, diarization_pipeline, rttm_handler, server_start_time
    
    logger.info("Starting ALF Diarization Server...")
    server_start_time = datetime.now().timestamp()
    
    try:
        # Initialize communication protocol
        json_protocol = JsonProtocol()
        logger.info("JSON protocol initialized")
        
        # Initialize RTTM handler
        rttm_handler = RTTMHandler()
        logger.info("RTTM handler initialized")
        
        # Initialize diarization pipeline
        diarization_pipeline = DiarizationPipeline()
        await diarization_pipeline.initialize()
        logger.info("Diarization pipeline initialized")
        
        logger.info("Diarization server startup completed")
        
    except Exception as e:
        logger.error(f"Server startup failed: {e}")
        sys.exit(1)

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    logger.info("Shutting down ALF Diarization Server...")
    
    if diarization_pipeline:
        await diarization_pipeline.cleanup()
    
    logger.info("Diarization server shutdown completed")

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        HealthResponse: Server health status
    """
    uptime = datetime.now().timestamp() - server_start_time
    
    return HealthResponse(
        status="healthy",
        service="diarization",
        version="0.2.0",
        uptime_seconds=uptime
    )

@app.post("/diarize", response_model=DiarizationResponse)
async def process_diarization(
    request: DiarizationRequest,
    background_tasks: BackgroundTasks
):
    """
    Process an audio file for speaker diarization.
    
    Args:
        request (DiarizationRequest): Diarization request parameters
        background_tasks (BackgroundTasks): FastAPI background tasks
        
    Returns:
        DiarizationResponse: Processing response
    """
    if not diarization_pipeline:
        raise HTTPException(status_code=503, detail="Diarization pipeline not initialized")
    
    # Validate input file
    audio_path = Path(request.audio_file_path)
    if not audio_path.exists():
        raise HTTPException(
            status_code=400, 
            detail=f"Audio file not found: {request.audio_file_path}"
        )
    
    # Generate job ID if not provided
    job_id = request.job_id or f"diarize_{int(datetime.now().timestamp())}"
    
    try:
        # Track the job
        active_jobs[job_id] = {
            'status': 'processing',
            'start_time': datetime.now().timestamp(),
            'request': request.dict()
        }
        
        logger.info(f"Starting diarization job: {job_id}")
        
        # Process in background
        background_tasks.add_task(
            process_diarization_background,
            job_id,
            request
        )
        
        return DiarizationResponse(
            job_id=job_id,
            status="processing",
            message="Diarization started successfully"
        )
        
    except Exception as e:
        logger.error(f"Diarization processing failed for job {job_id}: {e}")
        active_jobs[job_id] = {
            'status': 'failed',
            'error': str(e),
            'end_time': datetime.now().timestamp()
        }
        
        raise HTTPException(
            status_code=500,
            detail=f"Diarization processing failed: {e}"
        )

async def process_diarization_background(job_id: str, request: DiarizationRequest):
    """
    Background task for processing diarization.
    
    Args:
        job_id (str): Job identifier
        request (DiarizationRequest): Diarization request parameters
    """
    try:
        logger.info(f"Background processing started for job: {job_id}")
        
        # Run diarization pipeline
        result = await diarization_pipeline.process_audio(
            audio_file_path=request.audio_file_path,
            min_speakers=request.min_speakers,
            max_speakers=request.max_speakers,
            clustering_method=request.clustering_method
        )
        
        # Generate output files
        output_files = []
        
        if request.output_format == "rttm":
            rttm_file = await rttm_handler.create_rttm_file(
                diarization_result=result,
                audio_file_path=request.audio_file_path,
                job_id=job_id
            )
            output_files.append(str(rttm_file))
        
        # Update job status
        active_jobs[job_id].update({
            'status': 'completed',
            'end_time': datetime.now().timestamp(),
            'result': result,
            'output_files': output_files
        })
        
        logger.info(f"Diarization job completed successfully: {job_id}")
        
    except Exception as e:
        logger.error(f"Background diarization failed for job {job_id}: {e}")
        
        active_jobs[job_id].update({
            'status': 'failed',
            'error': str(e),
            'end_time': datetime.now().timestamp()
        })

@app.get("/job/{job_id}")
async def get_job_status(job_id: str):
    """
    Get the status of a diarization job.
    
    Args:
        job_id (str): Job identifier
        
    Returns:
        Dict: Job status information
    """
    if job_id not in active_jobs:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    
    job_info = active_jobs[job_id].copy()
    
    # Calculate processing time if completed
    if 'end_time' in job_info and 'start_time' in job_info:
        job_info['processing_time_seconds'] = job_info['end_time'] - job_info['start_time']
    
    return job_info

@app.get("/jobs")
async def list_jobs():
    """
    List all jobs with their status.
    
    Returns:
        Dict: Dictionary of all jobs
    """
    return active_jobs

@app.delete("/job/{job_id}")
async def cancel_job(job_id: str):
    """
    Cancel a running job.
    
    Args:
        job_id (str): Job identifier
        
    Returns:
        Dict: Cancellation result
    """
    if job_id not in active_jobs:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    
    job_info = active_jobs[job_id]
    
    if job_info['status'] not in ['processing']:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot cancel job in status: {job_info['status']}"
        )
    
    # Mark job as cancelled
    active_jobs[job_id].update({
        'status': 'cancelled',
        'end_time': datetime.now().timestamp()
    })
    
    logger.info(f"Job cancelled: {job_id}")
    
    return {"message": f"Job {job_id} cancelled successfully"}

@app.post("/upload")
async def upload_audio(file: UploadFile = File(...)):
    """
    Upload an audio file for processing.
    
    Args:
        file (UploadFile): Uploaded audio file
        
    Returns:
        Dict: Upload result with file path
    """
    try:
        # Validate file type
        allowed_extensions = ['.wav', '.mp3', '.flac', '.m4a']
        file_extension = Path(file.filename).suffix.lower()
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file_extension}. Allowed: {allowed_extensions}"
            )
        
        # Create upload directory
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)
        
        # Save uploaded file
        file_path = upload_dir / file.filename
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        logger.info(f"File uploaded successfully: {file.filename}")
        
        return {
            "message": "File uploaded successfully",
            "filename": file.filename,
            "file_path": str(file_path),
            "size_bytes": len(content)
        }
        
    except Exception as e:
        logger.error(f"File upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")

@app.get("/")
async def root():
    """Root endpoint with server information."""
    return {
        "service": "ALF Diarization Server",
        "version": "0.2.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "diarize": "/diarize",
            "jobs": "/jobs",
            "upload": "/upload"
        }
    }

# Main entry point
if __name__ == "__main__":
    # Get server configuration from environment variables
    host = os.getenv("ALF_SERVER_HOST", "127.0.0.1")
    port = int(os.getenv("ALF_SERVER_PORT", "9091"))
    
    logger.info(f"Starting diarization server on {host}:{port}")
    
    uvicorn.run(
        "server:app",
        host=host,
        port=port,
        reload=False,
        log_level="info"
    )