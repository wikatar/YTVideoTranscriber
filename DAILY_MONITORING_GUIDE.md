# Daily YouTube Channel Monitoring Guide

## 🎯 **Quick Setup - Just Input Channel Links!**

### **Super Simple Setup**
```bash
# Run the interactive setup script
python setup_daily_monitoring.py

# Or manually add channels
python main.py add-channel "https://www.youtube.com/@TechChannel"
python main.py add-channel "https://www.youtube.com/@AIResearch"
python main.py add-channel "https://www.youtube.com/@PodcastShow"

# Start daily monitoring with optimization
python main.py start-monitoring --optimized
```

**That's it!** The system will now automatically:
1. ✅ Check for new uploads daily (or custom interval)
2. ✅ Download audio-only (minimal storage)
3. ✅ Transcribe with timestamps and speaker ID
4. ✅ Clean up files immediately after processing
5. ✅ Save complete transcriptions with metadata

## ⏰ **YES - You Get Detailed Timestamps!**

### **Multiple Timestamp Formats**

**1. Precise JSON Format:**
```json
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
}
```

**2. Human-Readable Format:**
```
[00:00] Speaker SPEAKER_00: Welcome to today's video
[00:04] Speaker SPEAKER_00: Today we'll be discussing AI
[00:08] Speaker SPEAKER_01: That sounds fascinating
[00:12] Speaker SPEAKER_00: Let's dive into the details
```

**3. SRT Subtitle Format:**
```
1
00:00:00,000 --> 00:00:04,200
[SPEAKER_00] Welcome to today's video

2
00:00:04,200 --> 00:00:08,500
[SPEAKER_00] Today we'll be discussing AI
```

## 🔄 **How Daily Monitoring Works**

### **Automated Workflow**
```
Every X minutes (configurable):
├── 1. Check all monitored channels via RSS feeds
├── 2. Detect new video uploads
├── 3. Add new videos to processing queue
├── 4. Download audio-only (5-15MB vs 50-200MB)
├── 5. Transcribe with Whisper + WhisperX
├── 6. Extract timestamps and speaker info
├── 7. Save transcription files with metadata
└── 8. Delete audio files immediately (90% storage saved)
```

### **Channel URL Formats Supported**
- `https://www.youtube.com/@channelname`
- `https://www.youtube.com/c/channelname`
- `https://www.youtube.com/channel/UC...`
- `https://www.youtube.com/user/username`

## 🚀 **Complete Setup Example**

### **Step 1: Add Your Channels**
```bash
# Interactive setup (recommended)
python setup_daily_monitoring.py

# Or add manually
python main.py add-channel "https://www.youtube.com/@lexfridman"
python main.py add-channel "https://www.youtube.com/@hubermanlab"
python main.py add-channel "https://www.youtube.com/@veritasium"
```

### **Step 2: Configure Settings (Optional)**
Edit `.env` file to customize:
```bash
# Check every 24 hours (daily)
CHECK_INTERVAL_MINUTES=1440

# Skip videos longer than 3 hours
MAX_VIDEO_LENGTH_MINUTES=180

# Use base model (good balance of speed/accuracy)
WHISPER_MODEL=base
WHISPERX_MODEL=base
```

### **Step 3: Start Monitoring**
```bash
# Start optimized daily monitoring
python main.py start-monitoring --optimized

# The system shows:
# 🚀 Optimization features:
#   • Immediate file cleanup after transcription
#   • Audio-only downloads (MP3 @ 128K)
#   • Minimal storage footprint
#   • Smart storage management
# Check interval: 1440 minutes
# Press Ctrl+C to stop
```

## 📊 **What You Get for Each Video**

### **Complete Output Structure**
```
transcriptions/
├── ChannelName/
│   └── VideoTitle_VideoID/
│       ├── transcription.json    # Complete data with timestamps
│       ├── transcript.txt        # Human-readable with metadata
│       └── subtitles.srt        # Standard subtitle format
```

### **Rich Metadata Included**
- ✅ **Video URL** - Direct link to original
- ✅ **Title & Description** - Full video information
- ✅ **Channel Info** - Name, ID, URL
- ✅ **Duration** - Video length in seconds
- ✅ **Upload Date** - When video was published
- ✅ **View/Like Counts** - Engagement metrics
- ✅ **Processing Timestamps** - When discovered/processed
- ✅ **Language Detection** - Auto-detected language
- ✅ **Speaker Count** - Number of speakers identified
- ✅ **Confidence Score** - Transcription quality (0-1)
- ✅ **Word Count** - Total words transcribed

## 🎮 **Daily Usage Commands**

### **Monitoring Commands**
```bash
# Start daily monitoring (runs forever)
python main.py start-monitoring --optimized

# Run one-time check for new videos
python main.py run-cycle --optimized

# Check what new videos were found
python main.py check-videos
```

### **Status & Management**
```bash
# Check system status
python main.py status

# Check storage usage (should be minimal!)
python main.py storage-status

# Clean up any temporary files
python main.py cleanup-storage

# List all monitored channels
python main.py list-channels
```

### **Search Your Transcriptions**
```bash
# Find videos by keyword
python main.py search keywords -k "artificial intelligence"

# Find videos from specific date range
python main.py search dates --start-date 2024-01-01 --end-date 2024-01-31

# Show trending topics
python main.py trending --days 30
```

## ⚙️ **Configuration Options**

### **Check Intervals**
- **Hourly**: `CHECK_INTERVAL_MINUTES=60`
- **Daily**: `CHECK_INTERVAL_MINUTES=1440` (recommended)
- **Twice daily**: `CHECK_INTERVAL_MINUTES=720`
- **Custom**: Any number of minutes

### **Quality vs Speed**
```bash
# Fast processing (good for daily monitoring)
WHISPER_MODEL=tiny
WHISPERX_MODEL=tiny

# Balanced (recommended)
WHISPER_MODEL=base
WHISPERX_MODEL=base

# High quality (slower)
WHISPER_MODEL=small
WHISPERX_MODEL=small
```

### **Storage Limits**
```bash
# Skip very long videos
MAX_VIDEO_LENGTH_MINUTES=180

# Maximum concurrent downloads
MAX_CONCURRENT_DOWNLOADS=3
```

## 📈 **Performance & Storage**

### **Daily Monitoring Performance**
- **10 channels**: ~5-15 new videos/day
- **Processing time**: ~1-3 minutes per video
- **Storage usage**: ~100-500MB total (with optimization)
- **Bandwidth**: ~50-150MB/day (audio-only downloads)

### **Storage Optimization**
- **Traditional**: 50-200MB per video (kept for days)
- **Optimized**: 5-15MB during processing, 1-5MB permanent
- **Savings**: 90%+ storage reduction
- **Cleanup**: Immediate after successful transcription

## 🔧 **Troubleshooting**

### **Common Issues**
```bash
# If monitoring stops
python main.py status  # Check system status
python main.py cleanup-storage  # Clean up if needed
python main.py start-monitoring --optimized  # Restart

# If storage fills up
python main.py storage-status  # Check usage
python main.py cleanup-storage --force  # Emergency cleanup

# If channels aren't being checked
python main.py list-channels  # Verify channels are active
python main.py check-videos  # Manual check
```

### **Logs & Debugging**
- **Log file**: `logs/transcription.log`
- **Verbose output**: Set `LOG_LEVEL=DEBUG` in `.env`
- **Status monitoring**: `python main.py storage-status`

## 🎉 **Example Daily Workflow**

### **Morning Setup**
```bash
# Add your favorite channels
python main.py add-channel "https://www.youtube.com/@TechChannel"
python main.py add-channel "https://www.youtube.com/@NewsChannel"

# Start daily monitoring
python main.py start-monitoring --optimized
```

### **System Runs Automatically**
- Checks channels every 24 hours
- Downloads new videos (audio-only)
- Transcribes with timestamps and speakers
- Saves complete transcriptions
- Cleans up temporary files
- Logs all activity

### **Evening Review**
```bash
# Check what was processed today
python main.py search dates --start-date 2024-01-15

# Find interesting topics
python main.py trending --days 1

# Check system health
python main.py storage-status
```

**Result**: Complete automated transcription system that monitors your channels daily and gives you searchable, timestamped transcriptions with minimal storage usage! 🚀
