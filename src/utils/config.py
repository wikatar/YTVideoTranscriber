"""Configuration management for the video transcription system."""

import os
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for the transcription system."""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent.parent
        
        # YouTube API
        self.youtube_api_key: Optional[str] = os.getenv('YOUTUBE_API_KEY')
        
        # Database
        self.database_url: str = os.getenv('DATABASE_URL', 'sqlite:///transcriptions.db')
        
        # Transcription settings
        self.whisper_model: str = os.getenv('WHISPER_MODEL', 'base')
        self.whisperx_model: str = os.getenv('WHISPERX_MODEL', 'base')
        self.device: str = os.getenv('DEVICE', 'cpu')
        self.compute_type: str = os.getenv('COMPUTE_TYPE', 'int8')
        
        # Paths
        self.download_path: Path = Path(os.getenv('DOWNLOAD_PATH', self.base_dir / 'downloads'))
        self.output_path: Path = Path(os.getenv('OUTPUT_PATH', self.base_dir / 'transcriptions'))
        self.log_path: Path = self.base_dir / 'logs'
        
        # Download settings
        self.max_concurrent_downloads: int = int(os.getenv('MAX_CONCURRENT_DOWNLOADS', '3'))
        
        # Monitoring settings
        self.check_interval_minutes: int = int(os.getenv('CHECK_INTERVAL_MINUTES', '60'))
        self.max_video_length_minutes: int = int(os.getenv('MAX_VIDEO_LENGTH_MINUTES', '180'))
        
        # Logging
        self.log_level: str = os.getenv('LOG_LEVEL', 'INFO')
        self.log_file: str = os.getenv('LOG_FILE', 'transcription.log')
        
        # Ensure directories exist
        self._create_directories()
    
    def _create_directories(self):
        """Create necessary directories if they don't exist."""
        for path in [self.download_path, self.output_path, self.log_path]:
            path.mkdir(parents=True, exist_ok=True)
    
    @property
    def channels_config_path(self) -> Path:
        """Path to the channels configuration file."""
        return self.base_dir / 'channels.json'
    
    def get_log_file_path(self) -> Path:
        """Get the full path to the log file."""
        return self.log_path / self.log_file

# Global config instance
config = Config()
