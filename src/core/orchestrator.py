"""Main orchestrator that coordinates all transcription system components."""

import time
import logging
import schedule
from datetime import datetime
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.core.youtube_monitor import YouTubeMonitor
from src.core.video_downloader import VideoDownloader
from src.core.transcription_engine import TranscriptionEngine
from src.models.database import db, Video
from src.utils.config import config

logger = logging.getLogger(__name__)

class TranscriptionOrchestrator:
    """Main orchestrator for the video transcription system."""
    
    def __init__(self):
        self.youtube_monitor = YouTubeMonitor()
        self.video_downloader = VideoDownloader()
        self.transcription_engine = TranscriptionEngine()
        self.is_running = False
        self.stats = {
            'videos_discovered': 0,
            'videos_downloaded': 0,
            'videos_transcribed': 0,
            'errors': 0,
            'last_run': None
        }
    
    def add_channel(self, channel_url: str) -> bool:
        """Add a new channel to monitor."""
        try:
            channel = self.youtube_monitor.add_channel(channel_url)
            if channel:
                logger.info(f"Successfully added channel: {channel.channel_name}")
                return True
            else:
                logger.error(f"Failed to add channel: {channel_url}")
                return False
        except Exception as e:
            logger.error(f"Error adding channel {channel_url}: {e}")
            return False
    
    def process_pending_videos(self) -> Dict[str, int]:
        """Process all pending videos through the complete pipeline."""
        logger.info("Starting to process pending videos")
        
        # Get pending videos
        pending_videos = db.get_pending_videos()
        if not pending_videos:
            logger.info("No pending videos to process")
            return {'downloaded': 0, 'transcribed': 0, 'failed': 0}
        
        logger.info(f"Found {len(pending_videos)} pending videos")
        
        # Step 1: Download videos
        download_results = self.video_downloader.download_videos_batch(pending_videos)
        
        # Step 2: Get successfully downloaded videos
        downloaded_videos = []
        for video in pending_videos:
            if download_results.get(video.video_id):
                downloaded_videos.append(video)
        
        logger.info(f"Successfully downloaded {len(downloaded_videos)} videos")
        
        # Step 3: Transcribe downloaded videos
        transcribed_count = 0
        failed_count = 0
        
        for video in downloaded_videos:
            try:
                transcription = self.transcription_engine.transcribe_video(video)
                if transcription:
                    transcribed_count += 1
                    self.stats['videos_transcribed'] += 1
                else:
                    failed_count += 1
                    self.stats['errors'] += 1
            except Exception as e:
                logger.error(f"Error transcribing video {video.title}: {e}")
                failed_count += 1
                self.stats['errors'] += 1
        
        # Update stats
        self.stats['videos_downloaded'] += len(downloaded_videos)
        
        results = {
            'downloaded': len(downloaded_videos),
            'transcribed': transcribed_count,
            'failed': failed_count
        }
        
        logger.info(f"Processing completed - Downloaded: {results['downloaded']}, "
                   f"Transcribed: {results['transcribed']}, Failed: {results['failed']}")
        
        return results
    
    def check_for_new_videos(self) -> List[Video]:
        """Check all channels for new videos."""
        logger.info("Checking for new videos")
        
        try:
            new_videos = self.youtube_monitor.check_all_channels()
            self.stats['videos_discovered'] += len(new_videos)
            
            if new_videos:
                logger.info(f"Discovered {len(new_videos)} new videos")
                for video in new_videos:
                    logger.info(f"New video: {video.title} from {video.channel_name}")
            else:
                logger.info("No new videos found")
            
            return new_videos
        except Exception as e:
            logger.error(f"Error checking for new videos: {e}")
            self.stats['errors'] += 1
            return []
    
    def run_full_cycle(self) -> Dict[str, Any]:
        """Run a complete cycle: check for new videos and process pending ones."""
        logger.info("Starting full processing cycle")
        start_time = time.time()
        
        try:
            # Step 1: Check for new videos
            new_videos = self.check_for_new_videos()
            
            # Step 2: Process all pending videos (including newly discovered ones)
            processing_results = self.process_pending_videos()
            
            # Step 3: Cleanup old downloads
            self.video_downloader.cleanup_old_downloads()
            
            cycle_time = time.time() - start_time
            self.stats['last_run'] = datetime.utcnow()
            
            results = {
                'new_videos_found': len(new_videos),
                'processing_results': processing_results,
                'cycle_time_seconds': cycle_time,
                'timestamp': self.stats['last_run'].isoformat()
            }
            
            logger.info(f"Full cycle completed in {cycle_time:.1f} seconds")
            return results
            
        except Exception as e:
            logger.error(f"Error in full cycle: {e}")
            self.stats['errors'] += 1
            return {'error': str(e)}
    
    def start_monitoring(self):
        """Start the monitoring system with scheduled checks."""
        if self.is_running:
            logger.warning("Monitoring is already running")
            return
        
        logger.info(f"Starting monitoring system - checking every {config.check_interval_minutes} minutes")
        
        # Schedule regular checks
        schedule.every(config.check_interval_minutes).minutes.do(self.run_full_cycle)
        
        # Run initial cycle
        self.run_full_cycle()
        
        self.is_running = True
        
        try:
            while self.is_running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute for scheduled tasks
        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")
        finally:
            self.is_running = False
    
    def stop_monitoring(self):
        """Stop the monitoring system."""
        logger.info("Stopping monitoring system")
        self.is_running = False
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        try:
            # Database stats
            with db.get_session() as session:
                total_channels = session.query(db.Channel).count()
                active_channels = session.query(db.Channel).filter(db.Channel.is_active == True).count()
                total_videos = session.query(Video).count()
                pending_videos = session.query(Video).filter(Video.status == 'pending').count()
                completed_videos = session.query(Video).filter(Video.status == 'completed').count()
                failed_videos = session.query(Video).filter(Video.status == 'failed').count()
            
            # System stats
            download_stats = self.video_downloader.get_download_stats()
            transcription_stats = self.transcription_engine.get_transcription_stats()
            
            return {
                'system': {
                    'is_running': self.is_running,
                    'last_run': self.stats['last_run'].isoformat() if self.stats['last_run'] else None,
                    'check_interval_minutes': config.check_interval_minutes,
                },
                'channels': {
                    'total': total_channels,
                    'active': active_channels,
                },
                'videos': {
                    'total': total_videos,
                    'pending': pending_videos,
                    'completed': completed_videos,
                    'failed': failed_videos,
                },
                'processing_stats': self.stats.copy(),
                'storage': {
                    'downloads': download_stats,
                    'transcriptions': transcription_stats,
                },
                'config': {
                    'whisper_model': config.whisper_model,
                    'whisperx_model': config.whisperx_model,
                    'device': config.device,
                    'max_video_length_minutes': config.max_video_length_minutes,
                }
            }
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {'error': str(e)}
    
    def process_single_video(self, video_url: str) -> Dict[str, Any]:
        """Process a single video immediately (for testing/manual processing)."""
        logger.info(f"Processing single video: {video_url}")
        
        try:
            # Get video metadata
            metadata = self.youtube_monitor.get_video_metadata(video_url)
            if not metadata:
                return {'error': 'Could not get video metadata'}
            
            # Check duration
            if metadata.get('duration', 0) > config.max_video_length_minutes * 60:
                return {'error': f'Video too long: {metadata["duration"]/60:.1f} minutes'}
            
            # Add to database
            video = db.add_video(
                video_id=metadata['video_id'],
                title=metadata['title'],
                channel_id=metadata['channel_id'],
                channel_name=metadata['channel_name'],
                url=video_url,
                duration_seconds=metadata.get('duration'),
                upload_date=metadata.get('upload_date')
            )
            
            # Download
            download_path = self.video_downloader.download_video(video)
            if not download_path:
                return {'error': 'Download failed'}
            
            # Transcribe
            transcription = self.transcription_engine.transcribe_video(video)
            if not transcription:
                return {'error': 'Transcription failed'}
            
            return {
                'success': True,
                'video_id': video.video_id,
                'title': video.title,
                'transcription_path': video.transcription_path,
                'language': transcription.language,
                'confidence_score': transcription.confidence_score
            }
            
        except Exception as e:
            logger.error(f"Error processing single video: {e}")
            return {'error': str(e)}

# Global orchestrator instance
orchestrator = TranscriptionOrchestrator()
