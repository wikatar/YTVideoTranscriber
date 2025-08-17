#!/usr/bin/env python3
"""
Simple FastAPI server for testing the web UI without complex dependencies.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Create FastAPI app
app = FastAPI(
    title="Video Transcription System API",
    description="Simple API for testing the web UI",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Video Transcription System API", "version": "1.0.0"}

@app.get("/status")
async def get_system_status():
    """Get basic system status."""
    return {
        "is_running": False,
        "channels": {"total": 0, "active": 0},
        "videos": {"total": 0, "pending": 0, "completed": 0, "failed": 0},
        "storage": {
            "immediate_cleanup": True,
            "audio_only_downloads": True,
            "compressed_format": "mp3",
            "estimated_storage_saved_mb": 0
        },
        "performance": {
            "average_processing_time": 0,
            "videos_per_hour": 0
        }
    }

@app.get("/channels")
async def get_channels():
    """Get channels (empty for now)."""
    return []

@app.get("/videos")
async def get_videos():
    """Get videos (empty for now)."""
    return []

@app.post("/channels")
async def add_channel(channel_data: dict):
    """Add channel (mock response)."""
    return {"message": "Channel would be added in full system", "url": channel_data.get("url", "")}

@app.get("/analytics/trending")
async def get_trending_topics():
    """Get trending topics (empty for now)."""
    return []

@app.get("/storage")
async def get_storage_status():
    """Get storage status (mock data)."""
    return {
        "temporary_storage": {"total_size_mb": 0, "total_files": 0},
        "transcription_files": {"size_mb": 0, "count": 0},
        "immediate_cleanup_enabled": True,
        "max_temp_storage_gb": 2
    }

if __name__ == "__main__":
    print("🚀 Starting Simple Video Transcription System API Server")
    print("=" * 55)
    print("API will be available at: http://localhost:8000")
    print("API docs will be available at: http://localhost:8000/docs")
    print("Press Ctrl+C to stop")
    print()
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
