"""Database models for the video transcription system."""

from datetime import datetime
from pathlib import Path
from typing import Optional, List
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from src.utils.config import config

Base = declarative_base()

class Channel(Base):
    """Model for YouTube channels to monitor."""
    __tablename__ = 'channels'
    
    id = Column(Integer, primary_key=True)
    channel_id = Column(String(50), unique=True, nullable=False)
    channel_name = Column(String(200), nullable=False)
    channel_url = Column(String(500), nullable=False)
    last_checked = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Video(Base):
    """Model for videos and their processing status."""
    __tablename__ = 'videos'
    
    id = Column(Integer, primary_key=True)
    video_id = Column(String(50), unique=True, nullable=False)
    title = Column(String(500), nullable=False)
    channel_id = Column(String(50), nullable=False)
    channel_name = Column(String(200), nullable=False)
    url = Column(String(500), nullable=False)
    duration_seconds = Column(Integer)
    upload_date = Column(DateTime)
    
    # Processing status
    status = Column(String(50), default='pending')  # pending, downloading, downloaded, transcribing, completed, failed
    download_path = Column(String(1000))
    transcription_path = Column(String(1000))
    
    # Timestamps
    discovered_at = Column(DateTime, default=datetime.utcnow)
    downloaded_at = Column(DateTime)
    transcribed_at = Column(DateTime)
    
    # Error handling
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)

class Transcription(Base):
    """Model for transcription results."""
    __tablename__ = 'transcriptions'
    
    id = Column(Integer, primary_key=True)
    video_id = Column(String(50), nullable=False)
    
    # Transcription content
    full_text = Column(Text)
    segments_json = Column(Text)  # JSON string of segments with timestamps
    speakers_json = Column(Text)  # JSON string of speaker information
    
    # Metadata
    language = Column(String(10))
    confidence_score = Column(Float)
    processing_time_seconds = Column(Float)
    
    # Model information
    whisper_model = Column(String(50))
    whisperx_model = Column(String(50))
    
    created_at = Column(DateTime, default=datetime.utcnow)

class DatabaseManager:
    """Database manager for handling all database operations."""
    
    def __init__(self):
        self.engine = create_engine(config.database_url)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def get_session(self) -> Session:
        """Get a database session."""
        return self.SessionLocal()
    
    def add_channel(self, channel_id: str, channel_name: str, channel_url: str) -> Channel:
        """Add a new channel to monitor."""
        with self.get_session() as session:
            existing = session.query(Channel).filter(Channel.channel_id == channel_id).first()
            if existing:
                return existing
            
            channel = Channel(
                channel_id=channel_id,
                channel_name=channel_name,
                channel_url=channel_url
            )
            session.add(channel)
            session.commit()
            session.refresh(channel)
            return channel
    
    def get_active_channels(self) -> List[Channel]:
        """Get all active channels."""
        with self.get_session() as session:
            return session.query(Channel).filter(Channel.is_active == True).all()
    
    def add_video(self, video_id: str, title: str, channel_id: str, 
                  channel_name: str, url: str, duration_seconds: Optional[int] = None,
                  upload_date: Optional[datetime] = None) -> Video:
        """Add a new video to process."""
        with self.get_session() as session:
            existing = session.query(Video).filter(Video.video_id == video_id).first()
            if existing:
                return existing
            
            video = Video(
                video_id=video_id,
                title=title,
                channel_id=channel_id,
                channel_name=channel_name,
                url=url,
                duration_seconds=duration_seconds,
                upload_date=upload_date
            )
            session.add(video)
            session.commit()
            session.refresh(video)
            return video
    
    def get_pending_videos(self) -> List[Video]:
        """Get videos that need to be processed."""
        with self.get_session() as session:
            return session.query(Video).filter(Video.status == 'pending').all()
    
    def update_video_status(self, video_id: str, status: str, 
                           error_message: Optional[str] = None,
                           download_path: Optional[str] = None,
                           transcription_path: Optional[str] = None):
        """Update video processing status."""
        with self.get_session() as session:
            video = session.query(Video).filter(Video.video_id == video_id).first()
            if video:
                video.status = status
                if error_message:
                    video.error_message = error_message
                    video.retry_count += 1
                if download_path:
                    video.download_path = download_path
                    video.downloaded_at = datetime.utcnow()
                if transcription_path:
                    video.transcription_path = transcription_path
                    video.transcribed_at = datetime.utcnow()
                session.commit()
    
    def save_transcription(self, video_id: str, full_text: str, 
                          segments_json: str, speakers_json: str,
                          language: str, confidence_score: float,
                          processing_time: float, whisper_model: str,
                          whisperx_model: str) -> Transcription:
        """Save transcription results."""
        with self.get_session() as session:
            transcription = Transcription(
                video_id=video_id,
                full_text=full_text,
                segments_json=segments_json,
                speakers_json=speakers_json,
                language=language,
                confidence_score=confidence_score,
                processing_time_seconds=processing_time,
                whisper_model=whisper_model,
                whisperx_model=whisperx_model
            )
            session.add(transcription)
            session.commit()
            session.refresh(transcription)
            return transcription
    
    def get_transcription(self, video_id: str) -> Optional[Transcription]:
        """Get transcription for a video."""
        with self.get_session() as session:
            return session.query(Transcription).filter(Transcription.video_id == video_id).first()
    
    def update_channel_last_checked(self, channel_id: str):
        """Update the last checked timestamp for a channel."""
        with self.get_session() as session:
            channel = session.query(Channel).filter(Channel.channel_id == channel_id).first()
            if channel:
                channel.last_checked = datetime.utcnow()
                session.commit()

# Global database manager instance
db = DatabaseManager()
