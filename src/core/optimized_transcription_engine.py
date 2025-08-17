"""Optimized transcription engine with immediate cleanup and minimal storage usage."""

import os
import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import torch
import whisper
import whisperx
from datetime import datetime

from src.models.database import db, Video, Transcription
from src.utils.config import config

logger = logging.getLogger(__name__)

class OptimizedTranscriptionEngine:
    """Optimized transcription engine with immediate cleanup and storage management."""
    
    def __init__(self):
        self.device = config.device
        self.compute_type = config.compute_type
        self.whisper_model_name = config.whisper_model
        self.whisperx_model_name = config.whisperx_model
        self.output_path = config.output_path
        
        # Storage optimization settings
        self.immediate_cleanup = True  # Delete audio files immediately after transcription
        self.keep_failed_files = False  # Don't keep files from failed transcriptions
        self.max_temp_storage_gb = 2.0  # Maximum temporary storage allowed
        
        # Initialize models (lazy loading)
        self._whisper_model = None
        self._whisperx_model = None
        self._whisperx_align_model = None
        self._diarize_model = None
        
        logger.info(f"Optimized transcription engine initialized - Immediate cleanup: {self.immediate_cleanup}")
    
    @property
    def whisper_model(self):
        """Lazy load Whisper model."""
        if self._whisper_model is None:
            logger.info(f"Loading Whisper model: {self.whisper_model_name}")
            self._whisper_model = whisper.load_model(self.whisper_model_name, device=self.device)
        return self._whisper_model
    
    @property
    def whisperx_model(self):
        """Lazy load WhisperX model."""
        if self._whisperx_model is None:
            logger.info(f"Loading WhisperX model: {self.whisperx_model_name}")
            self._whisperx_model = whisperx.load_model(
                self.whisperx_model_name, 
                device=self.device, 
                compute_type=self.compute_type
            )
        return self._whisperx_model
    
    def get_alignment_model(self, language_code: str):
        """Get alignment model for specific language."""
        if self._whisperx_align_model is None:
            logger.info(f"Loading alignment model for language: {language_code}")
            self._whisperx_align_model = whisperx.load_align_model(
                language_code=language_code, 
                device=self.device
            )
        return self._whisperx_align_model
    
    def get_diarization_model(self):
        """Get speaker diarization model."""
        if self._diarize_model is None:
            logger.info("Loading speaker diarization model")
            try:
                self._diarize_model = whisperx.DiarizationPipeline(
                    use_auth_token=None,
                    device=self.device
                )
            except Exception as e:
                logger.warning(f"Could not load diarization model: {e}")
                self._diarize_model = None
        return self._diarize_model
    
    def check_storage_space(self) -> Dict[str, Any]:
        """Check current storage usage and available space."""
        download_path = Path(config.download_path)
        
        total_size = 0
        file_count = 0
        
        if download_path.exists():
            for file_path in download_path.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
                    file_count += 1
        
        total_size_gb = total_size / (1024**3)
        
        return {
            'total_files': file_count,
            'total_size_bytes': total_size,
            'total_size_gb': total_size_gb,
            'max_allowed_gb': self.max_temp_storage_gb,
            'space_available': total_size_gb < self.max_temp_storage_gb,
            'cleanup_needed': total_size_gb > (self.max_temp_storage_gb * 0.8)  # 80% threshold
        }
    
    def cleanup_temp_files(self, force: bool = False):
        """Clean up temporary audio files to free space."""
        download_path = Path(config.download_path)
        
        if not download_path.exists():
            return
        
        storage_info = self.check_storage_space()
        
        if not force and not storage_info['cleanup_needed']:
            return
        
        logger.info("Starting temporary file cleanup...")
        cleaned_count = 0
        freed_bytes = 0
        
        # Get all audio files sorted by modification time (oldest first)
        audio_files = []
        for file_path in download_path.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in ['.wav', '.mp3', '.m4a', '.webm']:
                audio_files.append((file_path, file_path.stat().st_mtime))
        
        audio_files.sort(key=lambda x: x[1])  # Sort by modification time
        
        # Clean up oldest files first
        for file_path, _ in audio_files:
            try:
                file_size = file_path.stat().st_size
                file_path.unlink()
                cleaned_count += 1
                freed_bytes += file_size
                logger.debug(f"Cleaned up: {file_path}")
                
                # Check if we've freed enough space
                current_storage = self.check_storage_space()
                if not current_storage['cleanup_needed']:
                    break
                    
            except Exception as e:
                logger.warning(f"Could not delete {file_path}: {e}")
        
        freed_mb = freed_bytes / (1024**2)
        logger.info(f"Cleanup completed: {cleaned_count} files, {freed_mb:.1f}MB freed")
    
    def transcribe_with_immediate_cleanup(self, video: Video) -> Optional[Transcription]:
        """Transcribe video with immediate cleanup of audio file."""
        audio_path = video.download_path
        
        if not audio_path or not Path(audio_path).exists():
            logger.error(f"Audio file not found for video: {video.title}")
            return None
        
        logger.info(f"Starting optimized transcription: {video.title}")
        
        try:
            # Update status
            db.update_video_status(video.video_id, 'transcribing')
            
            # Check storage before processing
            storage_info = self.check_storage_space()
            if storage_info['cleanup_needed']:
                self.cleanup_temp_files()
            
            # Transcribe using the best available method
            start_time = time.time()
            
            try:
                transcription_data = self.transcribe_with_whisperx(audio_path)
                model_used = f"whisperx-{self.whisperx_model_name}"
            except Exception as e:
                logger.warning(f"WhisperX failed, falling back to Whisper: {e}")
                transcription_data = self.transcribe_with_whisper(audio_path)
                transcription_data['speakers_info'] = {'has_speaker_info': False, 'reason': 'whisperx_failed'}
                model_used = f"whisper-{self.whisper_model_name}"
            
            processing_time = time.time() - start_time
            
            # Calculate confidence score
            confidence_score = self.calculate_confidence_score(transcription_data.get('segments', []))
            
            # Save transcription files
            transcription_path = self.save_transcription_files(video, transcription_data)
            
            # Save to database
            transcription = db.save_transcription(
                video_id=video.video_id,
                full_text=transcription_data.get('text', ''),
                segments_json=json.dumps(transcription_data.get('segments', [])),
                speakers_json=json.dumps(transcription_data.get('speakers_info', {})),
                language=transcription_data.get('language', 'unknown'),
                confidence_score=confidence_score,
                processing_time=processing_time,
                whisper_model=self.whisper_model_name,
                whisperx_model=self.whisperx_model_name
            )
            
            # Update video status
            db.update_video_status(
                video.video_id, 
                'completed', 
                transcription_path=transcription_path
            )
            
            # IMMEDIATE CLEANUP: Delete audio file right after successful transcription
            if self.immediate_cleanup:
                try:
                    audio_file = Path(audio_path)
                    if audio_file.exists():
                        file_size_mb = audio_file.stat().st_size / (1024**2)
                        audio_file.unlink()
                        logger.info(f"✅ Immediately cleaned up audio file: {audio_file.name} ({file_size_mb:.1f}MB)")
                        
                        # Update database to reflect file deletion
                        db.update_video_status(video.video_id, 'completed', download_path=None)
                        
                except Exception as e:
                    logger.warning(f"Could not delete audio file {audio_path}: {e}")
            
            logger.info(f"Transcription completed: {video.title} (confidence: {confidence_score:.2f}, time: {processing_time:.1f}s)")
            return transcription
            
        except Exception as e:
            error_msg = f"Transcription failed for {video.title}: {str(e)}"
            logger.error(error_msg)
            
            # Clean up failed file if configured to do so
            if not self.keep_failed_files:
                try:
                    audio_file = Path(audio_path)
                    if audio_file.exists():
                        audio_file.unlink()
                        logger.info(f"Cleaned up failed transcription file: {audio_file.name}")
                except Exception as cleanup_error:
                    logger.warning(f"Could not clean up failed file: {cleanup_error}")
            
            db.update_video_status(video.video_id, 'failed', error_message=error_msg)
            return None
    
    def transcribe_with_whisper(self, audio_path: str) -> Dict[str, Any]:
        """Transcribe audio using standard Whisper."""
        logger.debug(f"Transcribing with Whisper: {Path(audio_path).name}")
        
        try:
            result = self.whisper_model.transcribe(audio_path)
            return {
                'text': result['text'],
                'segments': result['segments'],
                'language': result['language']
            }
        except Exception as e:
            logger.error(f"Whisper transcription failed: {e}")
            raise
    
    def transcribe_with_whisperx(self, audio_path: str) -> Dict[str, Any]:
        """Transcribe audio using WhisperX with speaker identification."""
        logger.debug(f"Transcribing with WhisperX: {Path(audio_path).name}")
        
        try:
            # Step 1: Transcribe with WhisperX
            audio = whisperx.load_audio(audio_path)
            result = self.whisperx_model.transcribe(audio, batch_size=16)
            
            # Step 2: Align whisper output
            if result['segments']:
                language_code = result['language']
                align_model, metadata = self.get_alignment_model(language_code)
                result = whisperx.align(
                    result['segments'], 
                    align_model, 
                    metadata, 
                    audio, 
                    self.device, 
                    return_char_alignments=False
                )
            
            # Step 3: Speaker diarization (if model available)
            speakers_info = {}
            if result['segments']:
                diarize_model = self.get_diarization_model()
                if diarize_model:
                    try:
                        diarize_segments = diarize_model(audio_path)
                        result = whisperx.assign_word_speakers(diarize_segments, result)
                        
                        # Extract speaker information
                        speakers = set()
                        for segment in result['segments']:
                            if 'speaker' in segment:
                                speakers.add(segment['speaker'])
                        
                        speakers_info = {
                            'total_speakers': len(speakers),
                            'speakers': list(speakers),
                            'has_speaker_info': True
                        }
                    except Exception as e:
                        logger.warning(f"Speaker diarization failed: {e}")
                        speakers_info = {'has_speaker_info': False, 'error': str(e)}
                else:
                    speakers_info = {'has_speaker_info': False, 'reason': 'No diarization model'}
            
            return {
                'text': ' '.join([segment.get('text', '') for segment in result['segments']]),
                'segments': result['segments'],
                'language': result.get('language', 'unknown'),
                'speakers_info': speakers_info
            }
            
        except Exception as e:
            logger.error(f"WhisperX transcription failed: {e}")
            raise
    
    def calculate_confidence_score(self, segments: List[Dict]) -> float:
        """Calculate average confidence score from segments."""
        if not segments:
            return 0.0
        
        total_confidence = 0.0
        count = 0
        
        for segment in segments:
            if 'words' in segment:
                for word in segment['words']:
                    if 'score' in word:
                        total_confidence += word['score']
                        count += 1
            elif 'score' in segment:
                total_confidence += segment['score']
                count += 1
        
        return total_confidence / count if count > 0 else 0.0
    
    def save_transcription_files(self, video: Video, transcription_data: Dict) -> str:
        """Save transcription to various file formats."""
        # Create output directory for this video
        safe_title = "".join(c for c in video.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_title = safe_title[:50]  # Limit length
        
        video_dir = self.output_path / video.channel_name.replace('/', '_') / f"{safe_title}_{video.video_id}"
        video_dir.mkdir(parents=True, exist_ok=True)
        
        # Save JSON with full data including ALL metadata
        json_path = video_dir / "transcription.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump({
                # Video metadata
                'video_id': video.video_id,
                'title': video.title,
                'description': getattr(video, 'description', None),
                'url': video.url,
                'channel_name': video.channel_name,
                'channel_id': video.channel_id,
                'duration_seconds': video.duration_seconds,
                'upload_date': video.upload_date.isoformat() if video.upload_date else None,
                'view_count': getattr(video, 'view_count', None),
                'like_count': getattr(video, 'like_count', None),
                
                # Processing metadata
                'transcription_date': datetime.utcnow().isoformat(),
                'discovered_at': video.discovered_at.isoformat() if video.discovered_at else None,
                'downloaded_at': video.downloaded_at.isoformat() if video.downloaded_at else None,
                'transcribed_at': datetime.utcnow().isoformat(),
                
                # Transcription data
                'language': transcription_data.get('language'),
                'speakers_info': transcription_data.get('speakers_info', {}),
                'segments': transcription_data.get('segments', []),
                'full_text': transcription_data.get('text', ''),
                
                # Quality metrics
                'confidence_score': self.calculate_confidence_score(transcription_data.get('segments', [])),
                'word_count': len(transcription_data.get('text', '').split()),
                'segment_count': len(transcription_data.get('segments', [])),
                
                # Technical details
                'whisper_model': self.whisper_model_name,
                'whisperx_model': self.whisperx_model_name,
                'processing_device': self.device,
                'immediate_cleanup_enabled': self.immediate_cleanup
            }, f, indent=2, ensure_ascii=False)
        
        # Save readable transcript with metadata header
        txt_path = video_dir / "transcript.txt"
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("VIDEO TRANSCRIPTION REPORT\n")
            f.write("=" * 80 + "\n\n")
            
            f.write(f"Title: {video.title}\n")
            f.write(f"URL: {video.url}\n")
            f.write(f"Channel: {video.channel_name}\n")
            f.write(f"Duration: {video.duration_seconds//60}:{video.duration_seconds%60:02d}\n" if video.duration_seconds else "Duration: Unknown\n")
            f.write(f"Upload Date: {video.upload_date.strftime('%Y-%m-%d') if video.upload_date else 'Unknown'}\n")
            f.write(f"Language: {transcription_data.get('language', 'unknown')}\n")
            f.write(f"Transcribed: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            speakers_info = transcription_data.get('speakers_info', {})
            if speakers_info.get('has_speaker_info'):
                f.write(f"Speakers: {speakers_info.get('total_speakers', 0)}\n")
            
            f.write("\n" + "-" * 80 + "\n")
            f.write("TRANSCRIPT\n")
            f.write("-" * 80 + "\n\n")
            
            formatted_text = self.format_transcript_text(
                transcription_data.get('segments', []),
                include_speakers=speakers_info.get('has_speaker_info', False)
            )
            f.write(formatted_text)
        
        # Save SRT subtitle file
        srt_path = video_dir / "subtitles.srt"
        self.save_srt_file(transcription_data.get('segments', []), srt_path)
        
        logger.info(f"Transcription files saved to: {video_dir}")
        return str(json_path)
    
    def format_transcript_text(self, segments: List[Dict], include_speakers: bool = True, 
                             include_timestamps: bool = True) -> str:
        """Format segments into readable transcript text."""
        lines = []
        
        for segment in segments:
            line_parts = []
            
            # Add timestamp
            if include_timestamps and 'start' in segment:
                start_time = segment['start']
                minutes = int(start_time // 60)
                seconds = int(start_time % 60)
                line_parts.append(f"[{minutes:02d}:{seconds:02d}]")
            
            # Add speaker
            if include_speakers and 'speaker' in segment:
                line_parts.append(f"Speaker {segment['speaker']}:")
            
            # Add text
            text = segment.get('text', '').strip()
            if text:
                line_parts.append(text)
            
            if line_parts:
                lines.append(' '.join(line_parts))
        
        return '\n'.join(lines)
    
    def save_srt_file(self, segments: List[Dict], srt_path: Path):
        """Save segments as SRT subtitle file."""
        try:
            with open(srt_path, 'w', encoding='utf-8') as f:
                for i, segment in enumerate(segments, 1):
                    if 'start' in segment and 'end' in segment and 'text' in segment:
                        start_time = self.seconds_to_srt_time(segment['start'])
                        end_time = self.seconds_to_srt_time(segment['end'])
                        text = segment['text'].strip()
                        
                        # Add speaker info if available
                        if 'speaker' in segment:
                            text = f"[{segment['speaker']}] {text}"
                        
                        f.write(f"{i}\n")
                        f.write(f"{start_time} --> {end_time}\n")
                        f.write(f"{text}\n\n")
        except Exception as e:
            logger.warning(f"Could not save SRT file: {e}")
    
    def seconds_to_srt_time(self, seconds: float) -> str:
        """Convert seconds to SRT time format (HH:MM:SS,mmm)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get comprehensive storage statistics."""
        storage_info = self.check_storage_space()
        
        # Count transcription files
        transcription_count = 0
        transcription_size = 0
        
        if self.output_path.exists():
            for file_path in self.output_path.rglob('*'):
                if file_path.is_file():
                    transcription_count += 1
                    transcription_size += file_path.stat().st_size
        
        return {
            'temporary_storage': storage_info,
            'transcription_files': {
                'count': transcription_count,
                'size_bytes': transcription_size,
                'size_mb': transcription_size / (1024**2)
            },
            'immediate_cleanup_enabled': self.immediate_cleanup,
            'keep_failed_files': self.keep_failed_files,
            'max_temp_storage_gb': self.max_temp_storage_gb
        }

# Global optimized transcription engine instance
optimized_transcription_engine = OptimizedTranscriptionEngine()
