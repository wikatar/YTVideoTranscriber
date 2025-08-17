"""Video downloading functionality using yt-dlp."""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
import yt_dlp
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from src.models.database import db, Video
from src.utils.config import config

logger = logging.getLogger(__name__)

class VideoDownloader:
    """Download videos from YouTube and other platforms."""
    
    def __init__(self):
        self.download_path = config.download_path
        self.max_concurrent = config.max_concurrent_downloads
        
        # Base yt-dlp options
        self.base_ydl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio/best',  # Prefer audio-only for transcription
            'outtmpl': str(self.download_path / '%(uploader)s/%(title)s.%(ext)s'),
            'writesubtitles': False,
            'writeautomaticsub': False,
            'ignoreerrors': True,
            'no_warnings': False,
            'extractaudio': True,
            'audioformat': 'wav',  # Convert to WAV for better compatibility with Whisper
            'audioquality': '192K',
        }
    
    def get_safe_filename(self, title: str, video_id: str) -> str:
        """Generate a safe filename from video title and ID."""
        # Remove or replace problematic characters
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_title = safe_title[:100]  # Limit length
        return f"{safe_title}_{video_id}"
    
    def download_video(self, video: Video) -> Optional[str]:
        """Download a single video and return the path to the downloaded file."""
        logger.info(f"Starting download: {video.title}")
        
        try:
            # Update status to downloading
            db.update_video_status(video.video_id, 'downloading')
            
            # Create channel-specific directory
            channel_dir = self.download_path / video.channel_name.replace('/', '_')
            channel_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate safe filename
            safe_filename = self.get_safe_filename(video.title, video.video_id)
            output_path = channel_dir / f"{safe_filename}.wav"
            
            # Configure yt-dlp options for this download
            ydl_opts = self.base_ydl_opts.copy()
            ydl_opts['outtmpl'] = str(output_path.with_suffix('.%(ext)s'))
            
            # Add progress hook
            def progress_hook(d):
                if d['status'] == 'downloading':
                    if 'total_bytes' in d:
                        percent = (d['downloaded_bytes'] / d['total_bytes']) * 100
                        logger.debug(f"Download progress for {video.title}: {percent:.1f}%")
                elif d['status'] == 'finished':
                    logger.info(f"Download completed: {d['filename']}")
            
            ydl_opts['progress_hooks'] = [progress_hook]
            
            # Download the video
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video.url])
            
            # Find the actual downloaded file (yt-dlp might change the extension)
            downloaded_file = None
            for ext in ['.wav', '.m4a', '.mp3', '.webm', '.mp4']:
                potential_file = output_path.with_suffix(ext)
                if potential_file.exists():
                    downloaded_file = potential_file
                    break
            
            if downloaded_file and downloaded_file.exists():
                # Update database with successful download
                db.update_video_status(
                    video.video_id, 
                    'downloaded', 
                    download_path=str(downloaded_file)
                )
                logger.info(f"Successfully downloaded: {video.title} -> {downloaded_file}")
                return str(downloaded_file)
            else:
                raise Exception("Downloaded file not found")
                
        except Exception as e:
            error_msg = f"Download failed for {video.title}: {str(e)}"
            logger.error(error_msg)
            db.update_video_status(video.video_id, 'failed', error_message=error_msg)
            return None
    
    def download_videos_batch(self, videos: List[Video]) -> Dict[str, Optional[str]]:
        """Download multiple videos concurrently."""
        if not videos:
            return {}
        
        logger.info(f"Starting batch download of {len(videos)} videos")
        results = {}
        
        with ThreadPoolExecutor(max_workers=self.max_concurrent) as executor:
            # Submit all download tasks
            future_to_video = {
                executor.submit(self.download_video, video): video 
                for video in videos
            }
            
            # Process completed downloads
            for future in as_completed(future_to_video):
                video = future_to_video[future]
                try:
                    result = future.result()
                    results[video.video_id] = result
                except Exception as e:
                    logger.error(f"Unexpected error downloading {video.title}: {e}")
                    results[video.video_id] = None
        
        successful_downloads = sum(1 for result in results.values() if result is not None)
        logger.info(f"Batch download completed: {successful_downloads}/{len(videos)} successful")
        
        return results
    
    def get_video_info(self, url: str) -> Optional[Dict[str, Any]]:
        """Get video information without downloading."""
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return {
                    'title': info.get('title'),
                    'duration': info.get('duration'),
                    'uploader': info.get('uploader'),
                    'upload_date': info.get('upload_date'),
                    'view_count': info.get('view_count'),
                    'like_count': info.get('like_count'),
                    'description': info.get('description'),
                    'formats': len(info.get('formats', [])),
                }
        except Exception as e:
            logger.error(f"Error getting video info for {url}: {e}")
            return None
    
    def cleanup_old_downloads(self, days_old: int = 7):
        """Clean up downloaded files older than specified days."""
        try:
            cutoff_time = time.time() - (days_old * 24 * 60 * 60)
            cleaned_count = 0
            
            for file_path in self.download_path.rglob('*'):
                if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                    try:
                        file_path.unlink()
                        cleaned_count += 1
                        logger.debug(f"Cleaned up old file: {file_path}")
                    except Exception as e:
                        logger.warning(f"Could not delete {file_path}: {e}")
            
            logger.info(f"Cleaned up {cleaned_count} old download files")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def get_download_stats(self) -> Dict[str, Any]:
        """Get statistics about downloads."""
        try:
            total_files = 0
            total_size = 0
            
            for file_path in self.download_path.rglob('*'):
                if file_path.is_file():
                    total_files += 1
                    total_size += file_path.stat().st_size
            
            return {
                'total_files': total_files,
                'total_size_mb': total_size / (1024 * 1024),
                'download_path': str(self.download_path),
            }
        except Exception as e:
            logger.error(f"Error getting download stats: {e}")
            return {}

# Global downloader instance
downloader = VideoDownloader()
