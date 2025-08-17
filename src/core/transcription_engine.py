"""Transcription engine using Whisper and WhisperX for speaker identification."""

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

class TranscriptionEngine:
    """Handle audio transcription using Whisper and WhisperX."""
    
    def __init__(self):
        self.device = config.device
        self.compute_type = config.compute_type
        self.whisper_model_name = config.whisper_model
        self.whisperx_model_name = config.whisperx_model
        self.output_path = config.output_path
        
        # Initialize models (lazy loading)
        self._whisper_model = None
        self._whisperx_model = None
        self._whisperx_align_model = None
        self._diarize_model = None
        
        logger.info(f"Transcription engine initialized - Device: {self.device}, Whisper: {self.whisper_model_name}")
    
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
                    use_auth_token=None,  # You might need to set this for some models
                    device=self.device
                )
            except Exception as e:
                logger.warning(f"Could not load diarization model: {e}")
                self._diarize_model = None
        return self._diarize_model
    
    def transcribe_with_whisper(self, audio_path: str) -> Dict[str, Any]:
        """Transcribe audio using standard Whisper."""
        logger.info(f"Transcribing with Whisper: {audio_path}")
        
        try:
            start_time = time.time()
            result = self.whisper_model.transcribe(audio_path)
            processing_time = time.time() - start_time
            
            return {
                'text': result['text'],
                'segments': result['segments'],
                'language': result['language'],
                'processing_time': processing_time
            }
        except Exception as e:
            logger.error(f"Whisper transcription failed: {e}")
            raise
    
    def transcribe_with_whisperx(self, audio_path: str) -> Dict[str, Any]:
        """Transcribe audio using WhisperX with speaker identification."""
        logger.info(f"Transcribing with WhisperX: {audio_path}")
        
        try:
            start_time = time.time()
            
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
            
            processing_time = time.time() - start_time
            
            return {
                'text': ' '.join([segment.get('text', '') for segment in result['segments']]),
                'segments': result['segments'],
                'language': result.get('language', 'unknown'),
                'speakers_info': speakers_info,
                'processing_time': processing_time
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
    
    def save_transcription_files(self, video: Video, transcription_data: Dict) -> str:
        """Save transcription to various file formats."""
        # Create output directory for this video
        safe_title = "".join(c for c in video.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_title = safe_title[:50]  # Limit length
        
        video_dir = self.output_path / video.channel_name.replace('/', '_') / f"{safe_title}_{video.video_id}"
        video_dir.mkdir(parents=True, exist_ok=True)
        
        # Save JSON with full data
        json_path = video_dir / "transcription.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump({
                'video_id': video.video_id,
                'title': video.title,
                'channel': video.channel_name,
                'transcription_date': datetime.utcnow().isoformat(),
                'language': transcription_data.get('language'),
                'processing_time': transcription_data.get('processing_time'),
                'speakers_info': transcription_data.get('speakers_info', {}),
                'segments': transcription_data.get('segments', []),
                'full_text': transcription_data.get('text', '')
            }, f, indent=2, ensure_ascii=False)
        
        # Save readable transcript
        txt_path = video_dir / "transcript.txt"
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(f"Video: {video.title}\n")
            f.write(f"Channel: {video.channel_name}\n")
            f.write(f"Language: {transcription_data.get('language', 'unknown')}\n")
            f.write(f"Transcribed: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("-" * 50 + "\n\n")
            
            formatted_text = self.format_transcript_text(
                transcription_data.get('segments', []),
                include_speakers=transcription_data.get('speakers_info', {}).get('has_speaker_info', False)
            )
            f.write(formatted_text)
        
        # Save SRT subtitle file
        srt_path = video_dir / "subtitles.srt"
        self.save_srt_file(transcription_data.get('segments', []), srt_path)
        
        logger.info(f"Transcription files saved to: {video_dir}")
        return str(json_path)
    
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
    
    def transcribe_video(self, video: Video) -> Optional[Transcription]:
        """Transcribe a video using the best available method."""
        if not video.download_path or not Path(video.download_path).exists():
            logger.error(f"Audio file not found for video: {video.title}")
            return None
        
        logger.info(f"Starting transcription: {video.title}")
        
        try:
            # Update status
            db.update_video_status(video.video_id, 'transcribing')
            
            # Try WhisperX first (better speaker identification)
            try:
                transcription_data = self.transcribe_with_whisperx(video.download_path)
                model_used = f"whisperx-{self.whisperx_model_name}"
            except Exception as e:
                logger.warning(f"WhisperX failed, falling back to Whisper: {e}")
                transcription_data = self.transcribe_with_whisper(video.download_path)
                transcription_data['speakers_info'] = {'has_speaker_info': False, 'reason': 'whisperx_failed'}
                model_used = f"whisper-{self.whisper_model_name}"
            
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
                processing_time=transcription_data.get('processing_time', 0),
                whisper_model=self.whisper_model_name,
                whisperx_model=self.whisperx_model_name
            )
            
            # Update video status
            db.update_video_status(
                video.video_id, 
                'completed', 
                transcription_path=transcription_path
            )
            
            logger.info(f"Transcription completed: {video.title} (confidence: {confidence_score:.2f})")
            return transcription
            
        except Exception as e:
            error_msg = f"Transcription failed for {video.title}: {str(e)}"
            logger.error(error_msg)
            db.update_video_status(video.video_id, 'failed', error_message=error_msg)
            return None
    
    def get_transcription_stats(self) -> Dict[str, Any]:
        """Get statistics about transcriptions."""
        try:
            with db.get_session() as session:
                total_transcriptions = session.query(Transcription).count()
                
                # Get language distribution
                languages = session.query(Transcription.language).all()
                language_counts = {}
                for (lang,) in languages:
                    language_counts[lang] = language_counts.get(lang, 0) + 1
                
                # Get average confidence
                confidences = [t.confidence_score for t in session.query(Transcription).all() if t.confidence_score]
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                
                return {
                    'total_transcriptions': total_transcriptions,
                    'language_distribution': language_counts,
                    'average_confidence': avg_confidence,
                    'output_path': str(self.output_path)
                }
        except Exception as e:
            logger.error(f"Error getting transcription stats: {e}")
            return {}

# Global transcription engine instance
transcription_engine = TranscriptionEngine()
