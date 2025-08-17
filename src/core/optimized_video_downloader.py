"""Optimized video downloader with minimal storage footprint and smart management."""

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

class OptimizedVideoDownloader:
    """Optimized video downloader with minimal storage usage and smart management."""
    
    def __init__(self):
        self.download_path = config.download_path
        self.max_concurrent = config.max_concurrent_downloads
        
        # Optimization settings
        self.audio_only = True  # Only download audio for transcription
        self.compress_audio = True  # Use compressed audio format
        self.immediate_processing = True  # Process immediately after download
        self.max_file_size_mb = 100  # Skip very large files
        
        # Optimized yt-dlp options for minimal storage
        self.base_ydl_opts = {
            # Audio-only download with compression
            'format': 'bestaudio[filesize<100M]/bestaudio[ext=m4a]/bestaudio/best',
            'outtmpl': str(self.download_path / '%(uploader)s/%(title)s_%(id)s.%(ext)s'),
            
            # Audio processing
            'extractaudio': True,
            'audioformat': 'mp3',  # Use MP3 for smaller file size (vs WAV)
            'audioquality': '128K',  # Lower quality for smaller files (still good for transcription)
            
            # Optimization flags
            'writesubtitles': False,
            'writeautomaticsub': False,
            'writedescription': False,
            'writeinfojson': False,  # We store metadata in database instead
            'writethumbnail': False,
            
            # Error handling
            'ignoreerrors': True,
            'no_warnings': False,
            'retries': 3,
            
            # Performance
            'concurrent_fragment_downloads': 4,
        }
        
        logger.info(f"Optimized downloader initialized - Audio only: {self.audio_only}, Compress: {self.compress_audio}")
    
    def get_safe_filename(self, title: str, video_id: str) -> str:
        """Generate a safe filename from video title and ID."""
        # Remove or replace problematic characters
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_title = safe_title[:50]  # Shorter limit for storage efficiency
        return f"{safe_title}_{video_id}"
    
    def estimate_download_size(self, video_url: str) -> Optional[Dict[str, Any]]:
        """Estimate download size before actually downloading."""
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'format': self.base_ydl_opts['format'],
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                
                # Find the best audio format
                formats = info.get('formats', [])
                best_audio = None
                
                for fmt in formats:
                    if fmt.get('acodec') != 'none' and fmt.get('vcodec') == 'none':  # Audio only
                        if not best_audio or (fmt.get('filesize', 0) > 0 and 
                                            (best_audio.get('filesize', 0) == 0 or 
                                             fmt.get('abr', 0) > best_audio.get('abr', 0))):
                            best_audio = fmt
                
                if best_audio:
                    estimated_size = best_audio.get('filesize', 0)
                    bitrate = best_audio.get('abr', 0)
                    
                    # If no filesize, estimate from duration and bitrate
                    if not estimated_size and bitrate and info.get('duration'):
                        estimated_size = int((info['duration'] * bitrate * 1000) / 8)  # Convert to bytes
                    
                    return {
                        'estimated_size_bytes': estimated_size,
                        'estimated_size_mb': estimated_size / (1024**2) if estimated_size else 0,
                        'bitrate': bitrate,
                        'format': best_audio.get('ext', 'unknown'),
                        'duration': info.get('duration', 0)
                    }
                
        except Exception as e:
            logger.warning(f"Could not estimate download size for {video_url}: {e}")
        
        return None
    
    def download_video_optimized(self, video: Video) -> Optional[str]:
        """Download a single video with optimized settings and immediate processing."""
        logger.info(f"Starting optimized download: {video.title}")
        
        try:
            # Update status to downloading
            db.update_video_status(video.video_id, 'downloading')
            
            # Estimate download size first
            size_info = self.estimate_download_size(video.url)
            if size_info:
                estimated_mb = size_info['estimated_size_mb']
                logger.info(f"Estimated download size: {estimated_mb:.1f}MB")
                
                # Skip if too large
                if estimated_mb > self.max_file_size_mb:
                    error_msg = f"Video too large: {estimated_mb:.1f}MB (max: {self.max_file_size_mb}MB)"
                    logger.warning(error_msg)
                    db.update_video_status(video.video_id, 'failed', error_message=error_msg)
                    return None
            
            # Create channel-specific directory
            channel_dir = self.download_path / video.channel_name.replace('/', '_')
            channel_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate safe filename
            safe_filename = self.get_safe_filename(video.title, video.video_id)
            output_path = channel_dir / f"{safe_filename}.mp3"
            
            # Configure yt-dlp options for this download
            ydl_opts = self.base_ydl_opts.copy()
            ydl_opts['outtmpl'] = str(output_path.with_suffix('.%(ext)s'))
            
            # Add progress hook for monitoring
            download_start_time = time.time()
            last_progress_time = download_start_time
            
            def progress_hook(d):
                nonlocal last_progress_time
                current_time = time.time()
                
                if d['status'] == 'downloading':
                    # Log progress every 10 seconds to avoid spam
                    if current_time - last_progress_time > 10:
                        if 'total_bytes' in d:
                            percent = (d['downloaded_bytes'] / d['total_bytes']) * 100
                            speed = d.get('speed', 0)
                            speed_mb = speed / (1024**2) if speed else 0
                            logger.info(f"Download progress: {percent:.1f}% ({speed_mb:.1f}MB/s) - {video.title[:30]}...")
                        last_progress_time = current_time
                        
                elif d['status'] == 'finished':
                    download_time = current_time - download_start_time
                    file_size_mb = Path(d['filename']).stat().st_size / (1024**2)
                    logger.info(f"Download completed: {file_size_mb:.1f}MB in {download_time:.1f}s - {Path(d['filename']).name}")
            
            ydl_opts['progress_hooks'] = [progress_hook]
            
            # Download the video
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video.url])
            
            # Find the actual downloaded file
            downloaded_file = None
            for ext in ['.mp3', '.m4a', '.webm', '.wav']:
                potential_file = output_path.with_suffix(ext)
                if potential_file.exists():
                    downloaded_file = potential_file
                    break
            
            if downloaded_file and downloaded_file.exists():
                file_size_mb = downloaded_file.stat().st_size / (1024**2)
                
                # Update database with successful download
                db.update_video_status(
                    video.video_id, 
                    'downloaded', 
                    download_path=str(downloaded_file)
                )
                
                logger.info(f"✅ Successfully downloaded: {video.title} -> {downloaded_file.name} ({file_size_mb:.1f}MB)")
                return str(downloaded_file)
            else:
                raise Exception("Downloaded file not found")
                
        except Exception as e:
            error_msg = f"Download failed for {video.title}: {str(e)}"
            logger.error(error_msg)
            db.update_video_status(video.video_id, 'failed', error_message=error_msg)
            return None
    
    def download_and_process_immediately(self, video: Video, transcription_engine) -> Dict[str, Any]:
        """Download and immediately process video to minimize storage usage."""
        logger.info(f"Starting download-and-process pipeline: {video.title}")
        
        download_start = time.time()
        
        # Step 1: Download
        download_path = self.download_video_optimized(video)
        if not download_path:
            return {'success': False, 'error': 'Download failed'}
        
        download_time = time.time() - download_start
        
        # Step 2: Immediately transcribe
        transcription_start = time.time()
        transcription = transcription_engine.transcribe_with_immediate_cleanup(video)
        transcription_time = time.time() - transcription_start
        
        total_time = time.time() - download_start
        
        if transcription:
            logger.info(f"✅ Complete pipeline finished: {video.title}")
            logger.info(f"   Download: {download_time:.1f}s, Transcription: {transcription_time:.1f}s, Total: {total_time:.1f}s")
            
            return {
                'success': True,
                'video_id': video.video_id,
                'title': video.title,
                'download_time': download_time,
                'transcription_time': transcription_time,
                'total_time': total_time,
                'language': transcription.language,
                'confidence_score': transcription.confidence_score,
                'transcription_path': video.transcription_path
            }
        else:
            return {'success': False, 'error': 'Transcription failed'}
    
    def download_videos_batch_optimized(self, videos: List[Video], transcription_engine) -> Dict[str, Any]:
        """Download and process multiple videos with optimized storage management."""
        if not videos:
            return {'results': [], 'summary': {'successful': 0, 'failed': 0}}
        
        logger.info(f"Starting optimized batch processing of {len(videos)} videos")
        
        results = []
        successful = 0
        failed = 0
        
        # Process videos one by one to minimize concurrent storage usage
        for i, video in enumerate(videos, 1):
            logger.info(f"Processing video {i}/{len(videos)}: {video.title}")
            
            try:
                result = self.download_and_process_immediately(video, transcription_engine)
                results.append(result)
                
                if result['success']:
                    successful += 1
                else:
                    failed += 1
                    
            except Exception as e:
                logger.error(f"Unexpected error processing {video.title}: {e}")
                results.append({
                    'success': False,
                    'video_id': video.video_id,
                    'title': video.title,
                    'error': str(e)
                })
                failed += 1
        
        summary = {
            'total_videos': len(videos),
            'successful': successful,
            'failed': failed,
            'success_rate': successful / len(videos) if videos else 0
        }
        
        logger.info(f"Batch processing completed: {successful}/{len(videos)} successful ({summary['success_rate']:.1%})")
        
        return {
            'results': results,
            'summary': summary
        }
    
    def get_storage_usage(self) -> Dict[str, Any]:
        """Get current storage usage statistics."""
        try:
            total_files = 0
            total_size = 0
            file_types = {}
            
            if self.download_path.exists():
                for file_path in self.download_path.rglob('*'):
                    if file_path.is_file():
                        total_files += 1
                        file_size = file_path.stat().st_size
                        total_size += file_size
                        
                        ext = file_path.suffix.lower()
                        if ext not in file_types:
                            file_types[ext] = {'count': 0, 'size': 0}
                        file_types[ext]['count'] += 1
                        file_types[ext]['size'] += file_size
            
            return {
                'total_files': total_files,
                'total_size_bytes': total_size,
                'total_size_mb': total_size / (1024**2),
                'total_size_gb': total_size / (1024**3),
                'file_types': {
                    ext: {
                        'count': info['count'],
                        'size_mb': info['size'] / (1024**2)
                    }
                    for ext, info in file_types.items()
                },
                'download_path': str(self.download_path),
                'optimization_settings': {
                    'audio_only': self.audio_only,
                    'compress_audio': self.compress_audio,
                    'max_file_size_mb': self.max_file_size_mb,
                    'immediate_processing': self.immediate_processing
                }
            }
        except Exception as e:
            logger.error(f"Error getting storage usage: {e}")
            return {'error': str(e)}
    
    def emergency_cleanup(self) -> Dict[str, Any]:
        """Emergency cleanup of all temporary files."""
        logger.warning("Starting emergency cleanup of all temporary files")
        
        cleaned_count = 0
        freed_bytes = 0
        errors = []
        
        try:
            if self.download_path.exists():
                for file_path in self.download_path.rglob('*'):
                    if file_path.is_file():
                        try:
                            file_size = file_path.stat().st_size
                            file_path.unlink()
                            cleaned_count += 1
                            freed_bytes += file_size
                        except Exception as e:
                            errors.append(f"Could not delete {file_path}: {e}")
                
                # Remove empty directories
                for dir_path in self.download_path.rglob('*'):
                    if dir_path.is_dir() and not any(dir_path.iterdir()):
                        try:
                            dir_path.rmdir()
                        except Exception as e:
                            errors.append(f"Could not remove directory {dir_path}: {e}")
            
            freed_mb = freed_bytes / (1024**2)
            logger.info(f"Emergency cleanup completed: {cleaned_count} files, {freed_mb:.1f}MB freed")
            
            return {
                'cleaned_files': cleaned_count,
                'freed_bytes': freed_bytes,
                'freed_mb': freed_mb,
                'errors': errors
            }
            
        except Exception as e:
            logger.error(f"Error during emergency cleanup: {e}")
            return {'error': str(e)}

# Global optimized downloader instance
optimized_downloader = OptimizedVideoDownloader()
