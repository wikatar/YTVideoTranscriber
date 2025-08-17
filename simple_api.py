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
async def get_videos(limit: int = 50, status: str = None):
    """Get videos from memory store."""
    filtered_videos = videos_store
    if status:
        filtered_videos = [v for v in videos_store if v.get("status") == status]
    return filtered_videos[:limit]

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
    """Process video (stores in memory for demo)."""
    url = video_data.get("url", "")
    if url:
        # Extract video ID from URL for demo
        video_id = url.split("v=")[-1].split("&")[0] if "v=" in url else f"vid_{len(videos_store)}"
        title = f"Video from {url.split('/')[-1][:20]}..." if "/" in url else "Demo Video"
        
        video = {
            "id": len(videos_store) + 1,
            "video_id": video_id,
            "title": title,
            "channel_name": "Demo Channel",
            "url": url,
            "duration_seconds": 300,  # 5 minutes demo
            "upload_date": "2024-01-01T00:00:00",
            "status": "pending",
            "discovered_at": "2024-01-01T00:00:00",
            "transcribed_at": None
        }
        videos_store.append(video)
        return {"message": f"Video processing started: {title}", "url": url}
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

@app.get("/videos/{video_id}/transcription")
async def get_transcription(video_id: str):
    """Get transcription for a video (mock data)."""
    return {
        "video_id": video_id,
        "full_text": "This is a demo transcription for testing the web UI. In the real system, this would contain the actual transcribed text from the video.",
        "segments": [
            {"start": 0, "end": 5, "text": "Hello and welcome to this demo video.", "speaker": "Speaker 1"},
            {"start": 5, "end": 10, "text": "This is just sample transcription data.", "speaker": "Speaker 1"},
            {"start": 10, "end": 15, "text": "The real system would have actual transcribed content.", "speaker": "Speaker 1"}
        ],
        "speakers": {"has_speaker_info": True, "total_speakers": 1, "speakers": ["Speaker 1"]},
        "language": "en",
        "confidence_score": 0.95,
        "word_count": 25,
        "speaker_count": 1,
        "created_at": "2024-01-01T00:00:00"
    }

if __name__ == "__main__":
    print("🚀 Starting Simple Video Transcription System API Server")
    print("=" * 55)
    print("API will be available at: http://localhost:8000")
    print("API docs will be available at: http://localhost:8000/docs")
    print("Press Ctrl+C to stop")
    print()
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
