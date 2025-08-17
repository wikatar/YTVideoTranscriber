#!/usr/bin/env python3
"""
Example usage of the Video Transcription System

This script demonstrates how to use the system programmatically.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.utils.logging_config import setup_logging
from src.core.orchestrator import orchestrator
from src.models.database import db

def main():
    """Example usage of the transcription system."""
    
    # Setup logging
    logger = setup_logging()
    logger.info("Starting example usage")
    
    # Example 1: Add a channel
    print("Example 1: Adding a YouTube channel")
    channel_url = "https://www.youtube.com/@TEDx"  # Example channel
    success = orchestrator.add_channel(channel_url)
    if success:
        print(f"✓ Successfully added channel: {channel_url}")
    else:
        print(f"✗ Failed to add channel: {channel_url}")
    
    # Example 2: Check for new videos
    print("\nExample 2: Checking for new videos")
    new_videos = orchestrator.check_for_new_videos()
    print(f"Found {len(new_videos)} new videos")
    for video in new_videos[:3]:  # Show first 3
        print(f"  • {video.title} ({video.channel_name})")
    
    # Example 3: Get system status
    print("\nExample 3: System status")
    status = orchestrator.get_system_status()
    print(f"Channels: {status['channels']['active']} active")
    print(f"Videos: {status['videos']['total']} total, {status['videos']['pending']} pending")
    
    # Example 4: Process a single video (commented out to avoid actual processing)
    """
    print("\nExample 4: Processing a single video")
    video_url = "https://www.youtube.com/watch?v=EXAMPLE"
    result = orchestrator.process_single_video(video_url)
    if 'error' not in result:
        print(f"✓ Processed: {result['title']}")
        print(f"  Language: {result['language']}")
        print(f"  Confidence: {result['confidence_score']:.2f}")
    else:
        print(f"✗ Error: {result['error']}")
    """
    
    # Example 5: List recent videos
    print("\nExample 5: Recent videos in database")
    with db.get_session() as session:
        videos = session.query(db.Video).order_by(db.Video.discovered_at.desc()).limit(5).all()
        for video in videos:
            print(f"  • {video.title[:50]}... ({video.status})")
    
    print("\nExample completed!")

if __name__ == "__main__":
    main()
