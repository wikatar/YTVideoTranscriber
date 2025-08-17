"""Optimized orchestrator with minimal storage usage and immediate cleanup."""

import time
import logging
import schedule
from datetime import datetime
from typing import List, Dict, Any

from src.core.youtube_monitor import YouTubeMonitor
from src.core.optimized_video_downloader import OptimizedVideoDownloader
from src.core.optimized_transcription_engine import OptimizedTranscriptionEngine
from src.models.database import db, Video
from src.utils.config import config

logger = logging.getLogger(__name__)

class OptimizedTranscriptionOrchestrator:
    """Optimized orchestrator with minimal storage footprint and immediate processing."""
    
    def __init__(self):
        self.youtube_monitor = YouTubeMonitor()
        self.video_downloader = OptimizedVideoDownloader()
        self.transcription_engine = OptimizedTranscriptionEngine()
        self.is_running = False
        
        # Enhanced statistics
        self.stats = {
            'videos_discovered': 0,
            'videos_downloaded': 0,
            'videos_transcribed': 0,
            'errors': 0,
            'last_run': None,
            'total_storage_saved_mb': 0,
            'total_processing_time': 0,
            'average_file_size_mb': 0
        }
        
        logger.info("Optimized orchestrator initialized with immediate cleanup enabled")
    
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
    
    def process_pending_videos_optimized(self) -> Dict[str, Any]:
        """Process all pending videos with optimized storage management."""
        logger.info("Starting optimized processing of pending videos")
        
        # Get pending videos
        pending_videos = db.get_pending_videos()
        if not pending_videos:
            logger.info("No pending videos to process")
            return {
                'total_videos': 0,
                'successful': 0,
                'failed': 0,
                'processing_time': 0,
                'storage_saved_mb': 0
            }
        
        logger.info(f"Found {len(pending_videos)} pending videos")
        
        # Check storage before starting
        storage_info = self.transcription_engine.check_storage_space()
        if storage_info['cleanup_needed']:
            logger.info("Performing pre-processing cleanup...")
            self.transcription_engine.cleanup_temp_files()
        
        # Process videos with optimized pipeline
        start_time = time.time()
        batch_result = self.video_downloader.download_videos_batch_optimized(
            pending_videos, 
            self.transcription_engine
        )
        processing_time = time.time() - start_time
        
        # Update statistics
        summary = batch_result['summary']
        self.stats['videos_downloaded'] += summary['successful']
        self.stats['videos_transcribed'] += summary['successful']
        self.stats['errors'] += summary['failed']
        self.stats['total_processing_time'] += processing_time
        
        # Calculate storage savings (estimate)
        estimated_storage_saved = 0
        for result in batch_result['results']:
            if result['success']:
                # Estimate ~30MB saved per video (typical audio file size)
                estimated_storage_saved += 30
        
        self.stats['total_storage_saved_mb'] += estimated_storage_saved
        
        final_result = {
            'total_videos': len(pending_videos),
            'successful': summary['successful'],
            'failed': summary['failed'],
            'success_rate': summary['success_rate'],
            'processing_time': processing_time,
            'average_time_per_video': processing_time / len(pending_videos) if pending_videos else 0,
            'storage_saved_mb': estimated_storage_saved,
            'results': batch_result['results']
        }
        
        logger.info(f"Optimized processing completed:")
        logger.info(f"  ✅ Successful: {summary['successful']}/{len(pending_videos)} ({summary['success_rate']:.1%})")
        logger.info(f"  ⏱️  Total time: {processing_time:.1f}s ({final_result['average_time_per_video']:.1f}s per video)")
        logger.info(f"  💾 Storage saved: ~{estimated_storage_saved}MB (immediate cleanup)")
        
        return final_result
    
    def check_for_new_videos(self) -> List[Video]:
        """Check all channels for new videos."""
        logger.info("Checking for new videos")
        
        try:
            new_videos = self.youtube_monitor.check_all_channels()
            self.stats['videos_discovered'] += len(new_videos)
            
            if new_videos:
                logger.info(f"Discovered {len(new_videos)} new videos")
                for video in new_videos:
                    logger.info(f"  📹 {video.title} ({video.channel_name})")
                    if video.duration_seconds:
                        duration_min = video.duration_seconds / 60
                        logger.info(f"      Duration: {duration_min:.1f} minutes")
            else:
                logger.info("No new videos found")
            
            return new_videos
        except Exception as e:
            logger.error(f"Error checking for new videos: {e}")
            self.stats['errors'] += 1
            return []
    
    def run_optimized_cycle(self) -> Dict[str, Any]:
        """Run a complete optimized cycle with minimal storage usage."""
        logger.info("Starting optimized processing cycle")
        start_time = time.time()
        
        try:
            # Step 1: Check for new videos
            new_videos = self.check_for_new_videos()
            
            # Step 2: Process all pending videos with optimization
            processing_results = self.process_pending_videos_optimized()
            
            # Step 3: Final cleanup (just in case)
            cleanup_stats = self.transcription_engine.get_storage_stats()
            temp_storage = cleanup_stats['temporary_storage']
            
            if temp_storage['cleanup_needed']:
                logger.info("Performing post-processing cleanup...")
                self.transcription_engine.cleanup_temp_files()
            
            cycle_time = time.time() - start_time
            self.stats['last_run'] = datetime.utcnow()
            
            results = {
                'new_videos_found': len(new_videos),
                'processing_results': processing_results,
                'cycle_time_seconds': cycle_time,
                'timestamp': self.stats['last_run'].isoformat(),
                'storage_optimization': {
                    'immediate_cleanup_enabled': True,
                    'temp_storage_mb': temp_storage['total_size_gb'] * 1024,
                    'cleanup_performed': temp_storage['cleanup_needed'],
                    'estimated_storage_saved_mb': processing_results.get('storage_saved_mb', 0)
                }
            }
            
            logger.info(f"✅ Optimized cycle completed in {cycle_time:.1f} seconds")
            logger.info(f"   📊 New videos: {len(new_videos)}, Processed: {processing_results['successful']}")
            logger.info(f"   💾 Storage optimized: ~{processing_results.get('storage_saved_mb', 0)}MB saved")
            
            return results
            
        except Exception as e:
            logger.error(f"Error in optimized cycle: {e}")
            self.stats['errors'] += 1
            return {'error': str(e)}
    
    def start_monitoring(self):
        """Start the optimized monitoring system."""
        if self.is_running:
            logger.warning("Monitoring is already running")
            return
        
        logger.info(f"Starting optimized monitoring system")
        logger.info(f"  🔄 Check interval: {config.check_interval_minutes} minutes")
        logger.info(f"  💾 Immediate cleanup: ENABLED")
        logger.info(f"  🎵 Audio-only downloads: ENABLED")
        logger.info(f"  📦 Compressed format: MP3 @ 128K")
        
        # Schedule regular checks
        schedule.every(config.check_interval_minutes).minutes.do(self.run_optimized_cycle)
        
        # Run initial cycle
        self.run_optimized_cycle()
        
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
        logger.info("Stopping optimized monitoring system")
        self.is_running = False
    
    def get_optimized_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status with storage optimization details."""
        try:
            # Database stats
            with db.get_session() as session:
                total_channels = session.query(db.Channel).count()
                active_channels = session.query(db.Channel).filter(db.Channel.is_active == True).count()
                total_videos = session.query(Video).count()
                pending_videos = session.query(Video).filter(Video.status == 'pending').count()
                completed_videos = session.query(Video).filter(Video.status == 'completed').count()
                failed_videos = session.query(Video).filter(Video.status == 'failed').count()
            
            # Storage stats
            downloader_stats = self.video_downloader.get_storage_usage()
            transcription_stats = self.transcription_engine.get_storage_stats()
            
            return {
                'system': {
                    'is_running': self.is_running,
                    'last_run': self.stats['last_run'].isoformat() if self.stats['last_run'] else None,
                    'check_interval_minutes': config.check_interval_minutes,
                    'optimization_mode': 'ENABLED',
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
                'storage_optimization': {
                    'immediate_cleanup': True,
                    'audio_only_downloads': True,
                    'compressed_format': 'MP3 @ 128K',
                    'estimated_storage_saved_mb': self.stats['total_storage_saved_mb'],
                    'current_temp_storage': downloader_stats,
                    'transcription_storage': transcription_stats,
                },
                'performance': {
                    'total_processing_time': self.stats['total_processing_time'],
                    'average_processing_time': (
                        self.stats['total_processing_time'] / self.stats['videos_transcribed'] 
                        if self.stats['videos_transcribed'] > 0 else 0
                    ),
                    'videos_per_hour': (
                        self.stats['videos_transcribed'] / (self.stats['total_processing_time'] / 3600)
                        if self.stats['total_processing_time'] > 0 else 0
                    )
                },
                'config': {
                    'whisper_model': config.whisper_model,
                    'whisperx_model': config.whisperx_model,
                    'device': config.device,
                    'max_video_length_minutes': config.max_video_length_minutes,
                    'max_concurrent_downloads': config.max_concurrent_downloads,
                }
            }
        except Exception as e:
            logger.error(f"Error getting optimized system status: {e}")
            return {'error': str(e)}
    
    def process_single_video_optimized(self, video_url: str) -> Dict[str, Any]:
        """Process a single video with optimized pipeline."""
        logger.info(f"Processing single video with optimization: {video_url}")
        
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
            
            # Process with optimized pipeline (download + transcribe + cleanup)
            start_time = time.time()
            result = self.video_downloader.download_and_process_immediately(
                video, 
                self.transcription_engine
            )
            total_time = time.time() - start_time
            
            if result['success']:
                return {
                    'success': True,
                    'video_id': video.video_id,
                    'title': video.title,
                    'url': video_url,
                    'duration_seconds': video.duration_seconds,
                    'channel_name': video.channel_name,
                    'transcription_path': result['transcription_path'],
                    'language': result['language'],
                    'confidence_score': result['confidence_score'],
                    'processing_time': {
                        'download': result['download_time'],
                        'transcription': result['transcription_time'],
                        'total': total_time
                    },
                    'optimization': {
                        'immediate_cleanup': True,
                        'storage_saved': True,
                        'audio_only_download': True
                    }
                }
            else:
                return {'error': result.get('error', 'Processing failed')}
            
        except Exception as e:
            logger.error(f"Error processing single video: {e}")
            return {'error': str(e)}
    
    def emergency_storage_cleanup(self) -> Dict[str, Any]:
        """Perform emergency cleanup of all temporary storage."""
        logger.warning("Performing emergency storage cleanup")
        
        try:
            # Cleanup temporary downloads
            downloader_cleanup = self.video_downloader.emergency_cleanup()
            
            # Cleanup transcription engine temp files
            self.transcription_engine.cleanup_temp_files(force=True)
            
            # Get final storage stats
            final_stats = self.video_downloader.get_storage_usage()
            
            return {
                'cleanup_performed': True,
                'downloader_cleanup': downloader_cleanup,
                'final_storage_usage': final_stats,
                'message': 'Emergency cleanup completed'
            }
            
        except Exception as e:
            logger.error(f"Error during emergency cleanup: {e}")
            return {'error': str(e)}

# Global optimized orchestrator instance
optimized_orchestrator = OptimizedTranscriptionOrchestrator()
