#!/usr/bin/env python3
"""
Daily YouTube Channel Monitoring Setup

This script helps you easily set up automated daily monitoring of YouTube channels.
Just input the channel URLs and the system will automatically:
1. Check for new uploads daily
2. Download and transcribe new videos
3. Save transcriptions with timestamps and speaker identification
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.utils.logging_config import setup_logging
from src.core.optimized_orchestrator import optimized_orchestrator
from src.models.database import db
from src.utils.config import config

def setup_daily_monitoring():
    """Interactive setup for daily YouTube channel monitoring."""
    
    # Setup logging
    logger = setup_logging()
    
    print("🎥 YOUTUBE CHANNEL DAILY MONITORING SETUP")
    print("=" * 60)
    print()
    print("This will set up automated daily monitoring of YouTube channels.")
    print("The system will:")
    print("  • Check for new uploads every day (or custom interval)")
    print("  • Download audio-only (minimal storage)")
    print("  • Transcribe with timestamps and speaker identification")
    print("  • Automatically clean up temporary files")
    print("  • Save complete transcriptions with metadata")
    print()
    
    # Get channels from user
    channels = []
    print("📺 STEP 1: Add YouTube Channels")
    print("-" * 30)
    print("Enter YouTube channel URLs (one per line).")
    print("Supported formats:")
    print("  • https://www.youtube.com/@channelname")
    print("  • https://www.youtube.com/c/channelname")
    print("  • https://www.youtube.com/channel/UC...")
    print("  • https://www.youtube.com/user/username")
    print()
    print("Enter channels (press Enter twice when done):")
    
    while True:
        channel_url = input("Channel URL: ").strip()
        if not channel_url:
            break
        
        if 'youtube.com' in channel_url:
            channels.append(channel_url)
            print(f"  ✓ Added: {channel_url}")
        else:
            print(f"  ✗ Invalid URL: {channel_url}")
    
    if not channels:
        print("No channels added. Exiting.")
        return
    
    print(f"\n📋 Total channels to monitor: {len(channels)}")
    
    # Add channels to system
    print("\n🔧 STEP 2: Adding Channels to System")
    print("-" * 40)
    
    added_channels = []
    for channel_url in channels:
        print(f"Adding: {channel_url}")
        success = optimized_orchestrator.add_channel(channel_url)
        if success:
            print(f"  ✅ Successfully added!")
            added_channels.append(channel_url)
        else:
            print(f"  ❌ Failed to add channel")
    
    print(f"\n✅ Successfully added {len(added_channels)} channels")
    
    # Configuration options
    print("\n⚙️  STEP 3: Configuration")
    print("-" * 25)
    
    print(f"Current settings:")
    print(f"  • Check interval: {config.check_interval_minutes} minutes")
    print(f"  • Max video length: {config.max_video_length_minutes} minutes")
    print(f"  • Whisper model: {config.whisper_model}")
    print(f"  • Device: {config.device}")
    print(f"  • Optimization: ENABLED (immediate cleanup)")
    print()
    
    # Ask about check interval
    while True:
        try:
            interval_choice = input("Check interval (1=hourly, 2=daily, 3=custom, Enter=keep current): ").strip()
            
            if not interval_choice:
                break
            elif interval_choice == "1":
                new_interval = 60  # 1 hour
                break
            elif interval_choice == "2":
                new_interval = 1440  # 24 hours (daily)
                break
            elif interval_choice == "3":
                new_interval = int(input("Enter custom interval in minutes: "))
                break
            else:
                print("Please enter 1, 2, 3, or press Enter")
                continue
        except ValueError:
            print("Please enter a valid number")
    
    # Show final setup
    print("\n🎯 STEP 4: Setup Complete!")
    print("-" * 30)
    print("Your daily monitoring system is ready!")
    print()
    print("📊 Summary:")
    print(f"  • Channels monitored: {len(added_channels)}")
    print(f"  • Check interval: {config.check_interval_minutes} minutes")
    print(f"  • Optimization: ENABLED")
    print(f"  • Timestamps: YES (precise timing)")
    print(f"  • Speaker identification: YES")
    print(f"  • Automatic cleanup: YES")
    print()
    
    print("🚀 How to start monitoring:")
    print("  1. Start continuous monitoring:")
    print("     python main.py start-monitoring --optimized")
    print()
    print("  2. Run one-time check:")
    print("     python main.py run-cycle --optimized")
    print()
    print("  3. Check system status:")
    print("     python main.py storage-status")
    print()
    
    # Ask if user wants to start monitoring now
    start_now = input("Start monitoring now? (y/n): ").strip().lower()
    if start_now in ['y', 'yes']:
        print("\n🔄 Starting optimized monitoring...")
        print("Press Ctrl+C to stop")
        try:
            optimized_orchestrator.start_monitoring()
        except KeyboardInterrupt:
            print("\n✋ Monitoring stopped by user")
    else:
        print("\n✅ Setup complete! Use the commands above to start monitoring.")

def show_timestamp_example():
    """Show example of timestamp output format."""
    print("\n⏰ TIMESTAMP INFORMATION")
    print("=" * 40)
    print("YES! You get detailed timestamps in multiple formats:")
    print()
    
    print("📄 1. JSON Format (precise timestamps):")
    print("""
{
  "segments": [
    {
      "start": 0.0,
      "end": 4.2,
      "text": "Welcome to today's video",
      "speaker": "SPEAKER_00"
    },
    {
      "start": 4.2,
      "end": 8.5,
      "text": "Today we'll be discussing AI",
      "speaker": "SPEAKER_00"
    },
    {
      "start": 8.5,
      "end": 12.1,
      "text": "That sounds fascinating",
      "speaker": "SPEAKER_01"
    }
  ]
}""")
    
    print("\n📝 2. Human-Readable Format:")
    print("""
[00:00] Speaker SPEAKER_00: Welcome to today's video
[00:04] Speaker SPEAKER_00: Today we'll be discussing AI
[00:08] Speaker SPEAKER_01: That sounds fascinating
[00:12] Speaker SPEAKER_00: Let's dive into the details
""")
    
    print("🎬 3. SRT Subtitle Format:")
    print("""
1
00:00:00,000 --> 00:00:04,200
[SPEAKER_00] Welcome to today's video

2
00:00:04,200 --> 00:00:08,500
[SPEAKER_00] Today we'll be discussing AI

3
00:00:08,500 --> 00:00:12,100
[SPEAKER_01] That sounds fascinating
""")
    
    print("✨ Features:")
    print("  • Precise timestamps (down to milliseconds)")
    print("  • Speaker identification (who said what)")
    print("  • Multiple output formats")
    print("  • Word-level timing (in JSON)")
    print("  • Standard subtitle compatibility")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--timestamps":
        show_timestamp_example()
    else:
        setup_daily_monitoring()
