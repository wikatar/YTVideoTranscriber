# Video Transcription System

A comprehensive system for automatically downloading and transcribing videos from YouTube channels using OpenAI's Whisper and WhisperX for advanced speaker identification.

## Features

- 🎥 **Automatic YouTube Channel Monitoring**: Monitor multiple channels for new uploads
- 🔄 **Automated Processing Pipeline**: Download → Transcribe → Store results
- 🗣️ **Speaker Identification**: Uses WhisperX for advanced speaker diarization
- 📝 **Multiple Output Formats**: JSON, TXT, SRT subtitle files
- 🔧 **Robust Error Handling**: Retry mechanisms and comprehensive logging
- 📊 **Progress Tracking**: Database storage with processing status
- ⚡ **Concurrent Processing**: Parallel downloads and processing
- 🎛️ **Configurable Settings**: Flexible configuration for models, paths, and limits

## Installation

1. **Clone the repository**:
```bash
git clone <repository-url>
cd VideoTranscriptionmodel
```

2. **Install Python dependencies**:
```bash
pip install -r requirements.txt
```

3. **Install system dependencies**:
   - **FFmpeg** (required for audio processing):
     - macOS: `brew install ffmpeg`
     - Ubuntu: `sudo apt install ffmpeg`
     - Windows: Download from https://ffmpeg.org/

4. **Initial setup**:
```bash
python main.py setup
```

## Configuration

Copy `config.example.env` to `.env` and customize:

```bash
cp config.example.env .env
```

Key configuration options:

- `WHISPER_MODEL`: Model size (tiny, base, small, medium, large)
- `DEVICE`: Processing device (cpu, cuda)
- `CHECK_INTERVAL_MINUTES`: How often to check for new videos
- `MAX_VIDEO_LENGTH_MINUTES`: Skip videos longer than this
- `DOWNLOAD_PATH`: Where to store downloaded audio files
- `OUTPUT_PATH`: Where to store transcription results

## Quick Start

1. **Add a YouTube channel to monitor**:
```bash
python main.py add-channel "https://www.youtube.com/@channelname"
```

2. **Start continuous monitoring**:
```bash
python main.py start-monitoring
```

3. **Or process videos manually**:
```bash
# Check for new videos
python main.py check-videos

# Process pending videos
python main.py process-pending

# Process a single video
python main.py process-video "https://www.youtube.com/watch?v=VIDEO_ID"
```

## Usage Examples

### Basic Operations

```bash
# Add channels
python main.py add-channel "https://www.youtube.com/@TechChannel"
python main.py add-channel "https://www.youtube.com/c/PodcastChannel"

# List monitored channels
python main.py list-channels

# Check system status
python main.py status

# List recent videos
python main.py list-videos
```

### Processing Workflows

```bash
# Run a complete cycle (check + process)
python main.py run-cycle

# Start continuous monitoring (recommended)
python main.py start-monitoring
```

## Output Structure

The system creates organized output in the `transcriptions/` directory:

```
transcriptions/
├── ChannelName/
│   └── VideoTitle_VideoID/
│       ├── transcription.json    # Full data with timestamps
│       ├── transcript.txt        # Human-readable transcript
│       └── subtitles.srt        # SRT subtitle file
```

### Transcription JSON Format

```json
{
  "video_id": "abc123",
  "title": "Video Title",
  "channel": "Channel Name",
  "language": "en",
  "speakers_info": {
    "has_speaker_info": true,
    "total_speakers": 2,
    "speakers": ["SPEAKER_00", "SPEAKER_01"]
  },
  "segments": [
    {
      "start": 0.0,
      "end": 5.2,
      "text": "Hello and welcome to the show",
      "speaker": "SPEAKER_00"
    }
  ]
}
```

## Advanced Features

### Speaker Identification

The system uses WhisperX for advanced speaker diarization:

- Automatically detects number of speakers
- Assigns speaker labels to segments
- Includes speaker information in all output formats
- Falls back to standard Whisper if speaker identification fails

### Monitoring System

- **RSS-based monitoring**: Fast detection of new uploads
- **Configurable intervals**: Set check frequency
- **Duration filtering**: Skip videos that are too long
- **Automatic retry**: Handles temporary failures

### Database Schema

The system uses SQLite to track:

- **Channels**: Monitored YouTube channels
- **Videos**: Processing status and metadata
- **Transcriptions**: Full transcription results with confidence scores

## CLI Commands Reference

| Command | Description |
|---------|-------------|
| `add-channel <URL>` | Add a YouTube channel to monitor |
| `list-channels` | Show all monitored channels |
| `check-videos` | Check for new videos (one-time) |
| `process-pending` | Process all pending videos |
| `run-cycle` | Complete cycle: check + process |
| `start-monitoring` | Start continuous monitoring |
| `status` | Show system status and statistics |
| `process-video <URL>` | Process a single video immediately |
| `list-videos` | List recent videos in database |
| `setup` | Initial setup and configuration check |

## Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `WHISPER_MODEL` | `base` | Whisper model size |
| `WHISPERX_MODEL` | `base` | WhisperX model size |
| `DEVICE` | `cpu` | Processing device |
| `COMPUTE_TYPE` | `int8` | Computation precision |
| `CHECK_INTERVAL_MINUTES` | `60` | Monitoring interval |
| `MAX_VIDEO_LENGTH_MINUTES` | `180` | Maximum video length |
| `MAX_CONCURRENT_DOWNLOADS` | `3` | Parallel downloads |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

### Model Selection

**Whisper Models** (accuracy vs speed):
- `tiny`: Fastest, least accurate
- `base`: Good balance (recommended)
- `small`: Better accuracy
- `medium`: High accuracy
- `large`: Best accuracy, slowest

**Device Options**:
- `cpu`: Works everywhere, slower
- `cuda`: GPU acceleration (requires CUDA)

## Troubleshooting

### Common Issues

1. **"No module named 'whisperx'"**:
   ```bash
   pip install whisperx
   ```

2. **FFmpeg not found**:
   - Install FFmpeg for your system
   - Ensure it's in your PATH

3. **CUDA out of memory**:
   - Use smaller model size
   - Switch to CPU: `DEVICE=cpu`
   - Reduce batch size in code

4. **YouTube download fails**:
   - Update yt-dlp: `pip install -U yt-dlp`
   - Check if video is available/public

### Performance Optimization

- **GPU Usage**: Set `DEVICE=cuda` if you have a compatible GPU
- **Model Size**: Use larger models for better accuracy
- **Concurrent Downloads**: Adjust `MAX_CONCURRENT_DOWNLOADS` based on bandwidth
- **Storage**: Monitor disk space in download/output directories

### Logging

Logs are stored in `logs/transcription.log` with rotation. Adjust verbosity with `LOG_LEVEL`:

- `DEBUG`: Detailed information
- `INFO`: General information (default)
- `WARNING`: Important warnings
- `ERROR`: Errors only

## System Requirements

- **Python**: 3.8 or higher
- **Memory**: 4GB+ RAM (8GB+ recommended for large models)
- **Storage**: Varies by usage (videos are deleted after processing)
- **Network**: Stable internet for YouTube downloads
- **Optional**: CUDA-compatible GPU for faster processing

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [OpenAI Whisper](https://github.com/openai/whisper) for speech recognition
- [WhisperX](https://github.com/m-bain/whisperX) for speaker diarization
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) for YouTube downloading

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review logs in `logs/transcription.log`
3. Open an issue on GitHub with detailed information
