"""FastAPI backend for the Video Transcription System Web UI."""

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, date
import json

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from src.utils.logging_config import setup_logging
from src.core.optimized_orchestrator import optimized_orchestrator
from src.core.analytics_engine import analytics_engine
from src.models.database import db
from src.models.enhanced_database import enhanced_db
from src.utils.config import config

# Setup logging
logger = setup_logging()

# Create FastAPI app
app = FastAPI(
    title="Video Transcription System API",
    description="API for managing YouTube channel monitoring and video transcription",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for API
class ChannelAdd(BaseModel):
    url: str

class VideoProcess(BaseModel):
    url: str

class SearchRequest(BaseModel):
    keywords: Optional[List[str]] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    channel_id: Optional[str] = None
    limit: int = 20

class SystemStatus(BaseModel):
    is_running: bool
    channels: Dict[str, int]
    videos: Dict[str, int]
    storage: Dict[str, Any]
    performance: Dict[str, Any]

# API Routes

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Video Transcription System API", "version": "1.0.0"}

@app.get("/status", response_model=SystemStatus)
async def get_system_status():
    """Get comprehensive system status."""
    try:
        status_data = optimized_orchestrator.get_optimized_system_status()
        
        if 'error' in status_data:
            raise HTTPException(status_code=500, detail=status_data['error'])
        
        return SystemStatus(
            is_running=status_data['system']['is_running'],
            channels=status_data['channels'],
            videos=status_data['videos'],
            storage=status_data.get('storage_optimization', {}),
            performance=status_data.get('performance', {})
        )
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/channels")
async def get_channels():
    """Get all monitored channels."""
    try:
        channels = db.get_active_channels()
        return [
            {
                "id": channel.id,
                "channel_id": channel.channel_id,
                "channel_name": channel.channel_name,
                "channel_url": channel.channel_url,
                "is_active": channel.is_active,
                "last_checked": channel.last_checked.isoformat() if channel.last_checked else None,
                "created_at": channel.created_at.isoformat() if channel.created_at else None
            }
            for channel in channels
        ]
    except Exception as e:
        logger.error(f"Error getting channels: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/channels")
async def add_channel(channel: ChannelAdd):
    """Add a new channel to monitor."""
    try:
        success = optimized_orchestrator.add_channel(channel.url)
        if success:
            return {"message": "Channel added successfully", "url": channel.url}
        else:
            raise HTTPException(status_code=400, detail="Failed to add channel")
    except Exception as e:
        logger.error(f"Error adding channel: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/videos")
async def get_videos(limit: int = 50, status: Optional[str] = None):
    """Get recent videos with optional status filter."""
    try:
        with db.get_session() as session:
            query = session.query(db.Video).order_by(db.Video.discovered_at.desc())
            
            if status:
                query = query.filter(db.Video.status == status)
            
            videos = query.limit(limit).all()
            
            return [
                {
                    "id": video.id,
                    "video_id": video.video_id,
                    "title": video.title,
                    "channel_name": video.channel_name,
                    "url": video.url,
                    "duration_seconds": video.duration_seconds,
                    "upload_date": video.upload_date.isoformat() if video.upload_date else None,
                    "status": video.status,
                    "discovered_at": video.discovered_at.isoformat() if video.discovered_at else None,
                    "transcribed_at": video.transcribed_at.isoformat() if video.transcribed_at else None
                }
                for video in videos
            ]
    except Exception as e:
        logger.error(f"Error getting videos: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/videos/{video_id}/transcription")
async def get_transcription(video_id: str):
    """Get transcription for a specific video."""
    try:
        transcription = db.get_transcription(video_id)
        if not transcription:
            raise HTTPException(status_code=404, detail="Transcription not found")
        
        return {
            "video_id": transcription.video_id,
            "full_text": transcription.full_text,
            "segments": json.loads(transcription.segments_json) if transcription.segments_json else [],
            "speakers": json.loads(transcription.speakers_json) if transcription.speakers_json else {},
            "language": transcription.language,
            "confidence_score": transcription.confidence_score,
            "word_count": transcription.word_count,
            "speaker_count": transcription.speaker_count,
            "created_at": transcription.created_at.isoformat() if transcription.created_at else None
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting transcription: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/videos/process")
async def process_video(video: VideoProcess, background_tasks: BackgroundTasks):
    """Process a single video."""
    try:
        # Add to background tasks to avoid blocking
        background_tasks.add_task(
            optimized_orchestrator.process_single_video_optimized,
            video.url
        )
        return {"message": "Video processing started", "url": video.url}
    except Exception as e:
        logger.error(f"Error starting video processing: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/monitoring/start")
async def start_monitoring(background_tasks: BackgroundTasks):
    """Start the monitoring system."""
    try:
        if optimized_orchestrator.is_running:
            return {"message": "Monitoring is already running"}
        
        # Start monitoring in background
        background_tasks.add_task(optimized_orchestrator.start_monitoring)
        return {"message": "Monitoring started"}
    except Exception as e:
        logger.error(f"Error starting monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/monitoring/stop")
async def stop_monitoring():
    """Stop the monitoring system."""
    try:
        optimized_orchestrator.stop_monitoring()
        return {"message": "Monitoring stopped"}
    except Exception as e:
        logger.error(f"Error stopping monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/monitoring/cycle")
async def run_cycle(background_tasks: BackgroundTasks):
    """Run a single monitoring cycle."""
    try:
        background_tasks.add_task(optimized_orchestrator.run_optimized_cycle)
        return {"message": "Monitoring cycle started"}
    except Exception as e:
        logger.error(f"Error running cycle: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search")
async def search_videos(search: SearchRequest):
    """Search videos with various filters."""
    try:
        if search.keywords:
            # Keyword search
            results = analytics_engine.search_by_keywords(
                search.keywords, 
                match_all=False, 
                limit=search.limit
            )
            return [
                {
                    "video": {
                        "video_id": result['video'].video_id,
                        "title": result['video'].title,
                        "channel_name": result['video'].channel_name,
                        "url": result['video'].url,
                        "upload_date": result['video'].upload_date.isoformat() if result['video'].upload_date else None
                    },
                    "relevance_score": result['relevance_score'],
                    "matched_keywords": result['matched_keywords']
                }
                for result in results
            ]
        else:
            # Date/channel search
            videos = analytics_engine.search_by_date_and_channel(
                start_date=search.start_date,
                end_date=search.end_date,
                channel_ids=[search.channel_id] if search.channel_id else None
            )
            return [
                {
                    "video": {
                        "video_id": video.video_id,
                        "title": video.title,
                        "channel_name": video.channel_name,
                        "url": video.url,
                        "upload_date": video.upload_date.isoformat() if video.upload_date else None,
                        "duration_seconds": video.duration_seconds
                    },
                    "relevance_score": 1.0,
                    "matched_keywords": []
                }
                for video in videos[:search.limit]
            ]
    except Exception as e:
        logger.error(f"Error searching videos: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics/trending")
async def get_trending_topics(days: int = 30, limit: int = 20):
    """Get trending topics."""
    try:
        trends = analytics_engine.get_trending_topics(days_back=days, limit=limit)
        return trends
    except Exception as e:
        logger.error(f"Error getting trending topics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/storage")
async def get_storage_status():
    """Get storage usage information."""
    try:
        from src.core.optimized_transcription_engine import optimized_transcription_engine
        storage_stats = optimized_transcription_engine.get_storage_stats()
        return storage_stats
    except Exception as e:
        logger.error(f"Error getting storage status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/storage/cleanup")
async def cleanup_storage(force: bool = False):
    """Clean up temporary storage."""
    try:
        if force:
            result = optimized_orchestrator.emergency_storage_cleanup()
        else:
            from src.core.optimized_transcription_engine import optimized_transcription_engine
            optimized_transcription_engine.cleanup_temp_files()
            result = {"message": "Storage cleanup completed"}
        
        return result
    except Exception as e:
        logger.error(f"Error cleaning up storage: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
