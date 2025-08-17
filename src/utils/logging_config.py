"""Logging configuration for the video transcription system."""

import logging
import logging.handlers
from pathlib import Path
from src.utils.config import config

def setup_logging():
    """Set up logging configuration."""
    
    # Create logs directory if it doesn't exist
    config.log_path.mkdir(parents=True, exist_ok=True)
    
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, config.log_level.upper()))
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '%(levelname)s - %(message)s'
    )
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        config.get_log_file_path(),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, config.log_level.upper()))
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)
    
    # Set specific logger levels
    logging.getLogger('yt_dlp').setLevel(logging.WARNING)
    logging.getLogger('whisper').setLevel(logging.WARNING)
    logging.getLogger('whisperx').setLevel(logging.WARNING)
    logging.getLogger('torch').setLevel(logging.WARNING)
    logging.getLogger('transformers').setLevel(logging.WARNING)
    
    return logger
