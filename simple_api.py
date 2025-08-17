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
    active_channels = len([c for c in channels_store if c.get("is_active", True)])
    return {
        "is_running": len(channels_store) > 0,
        "channels": {"total": len(channels_store), "active": active_channels},
        "videos": {"total": len(videos_store), "pending": 0, "completed": 0, "failed": 0},
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
    """Get channels from memory store."""
    return channels_store

@app.get("/videos")
async def get_videos():
    """Get videos (empty for now)."""
    return []

# Simple in-memory storage for demo
channels_store = []
videos_store = []

@app.post("/channels")
async def add_channel(channel_data: dict):
    """Add channel (stores in memory for demo)."""
    url = channel_data.get("url", "")
    if url:
        # Extract channel name from URL for demo
        channel_name = url.split("/")[-1].replace("@", "")
        channel_id = f"UC{len(channels_store):010d}"
        
        channel = {
            "id": len(channels_store) + 1,
            "channel_id": channel_id,
            "channel_name": channel_name,
            "channel_url": url,
            "is_active": True,
            "last_checked": None,
            "created_at": "2024-01-01T00:00:00"
        }
        channels_store.append(channel)
        return {"message": f"Channel '{channel_name}' added successfully", "url": url}
    return {"message": "Invalid channel URL", "url": url}

@app.post("/videos/process")
async def process_video(video_data: dict):
    """Process video (mock response)."""
    url = video_data.get("url", "")
    if url:
        return {"message": f"Video processing started for: {url}", "url": url}
    return {"message": "Invalid video URL", "url": url}

@app.post("/monitoring/start")
async def start_monitoring():
    """Start monitoring (realistic response)."""
    if not channels_store:
        return {"message": "Cannot start monitoring: No channels added yet. Please add some YouTube channels first."}
    return {"message": f"Monitoring started for {len(channels_store)} channel(s)"}

@app.post("/monitoring/stop")
async def stop_monitoring():
    """Stop monitoring (realistic response)."""
    return {"message": "Monitoring stopped"}

@app.post("/monitoring/cycle")
async def run_cycle():
    """Run cycle (realistic response)."""
    if not channels_store:
        return {"message": "Nothing to monitor: No channels added yet"}
    return {"message": f"Checking {len(channels_store)} channel(s) for new videos..."}

@app.post("/search")
async def search_videos(search_data: dict):
    """Search videos (mock response)."""
    return []

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

@app.post("/storage/cleanup")
async def cleanup_storage(cleanup_data: dict = None):
    """Cleanup storage (mock response)."""
    return {"message": "Storage cleanup would run in full system"}

if __name__ == "__main__":
    print("🚀 Starting Simple Video Transcription System API Server")
    print("=" * 55)
    print("API will be available at: http://localhost:8000")
    print("API docs will be available at: http://localhost:8000/docs")
    print("Press Ctrl+C to stop")
    print()
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
