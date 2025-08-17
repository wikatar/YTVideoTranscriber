"""Enhanced database models with advanced analytics and search capabilities."""

import json
from datetime import datetime, date
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy import (
    create_engine, Column, Integer, String, DateTime, Text, Boolean, Float,
    ForeignKey, Index, func, and_, or_, desc, asc, extract, JSON
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship, Query
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
from src.utils.config import config

Base = declarative_base()

class Channel(Base):
    """Enhanced model for YouTube channels with analytics support."""
    __tablename__ = 'channels'
    
    id = Column(Integer, primary_key=True)
    channel_id = Column(String(50), unique=True, nullable=False, index=True)
    channel_name = Column(String(200), nullable=False, index=True)
    channel_url = Column(String(500), nullable=False)
    
    # Enhanced metadata
    description = Column(Text)
    subscriber_count = Column(Integer)
    video_count = Column(Integer)
    view_count = Column(Integer)
    country = Column(String(10))
    language = Column(String(10))
    
    # Categories and tags for better organization
    category = Column(String(100))  # e.g., "Technology", "Education", "Entertainment"
    tags = Column(Text)  # JSON array of tags
    
    # Monitoring settings
    is_active = Column(Boolean, default=True, index=True)
    priority = Column(Integer, default=1)  # 1=high, 2=medium, 3=low
    last_checked = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Analytics
    total_videos_processed = Column(Integer, default=0)
    total_processing_time = Column(Float, default=0.0)
    average_video_length = Column(Float, default=0.0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    videos = relationship("Video", back_populates="channel_obj", cascade="all, delete-orphan")

class Video(Base):
    """Enhanced model for videos with comprehensive metadata and search capabilities."""
    __tablename__ = 'videos'
    
    id = Column(Integer, primary_key=True)
    video_id = Column(String(50), unique=True, nullable=False, index=True)
    title = Column(String(500), nullable=False, index=True)
    description = Column(Text)  # Full video description
    
    # Channel relationship
    channel_id = Column(String(50), ForeignKey('channels.channel_id'), nullable=False, index=True)
    channel_name = Column(String(200), nullable=False, index=True)
    url = Column(String(500), nullable=False)
    
    # Enhanced video metadata
    duration_seconds = Column(Integer, index=True)
    view_count = Column(Integer)
    like_count = Column(Integer)
    comment_count = Column(Integer)
    
    # Content analysis
    thumbnail_url = Column(String(500))
    tags = Column(Text)  # JSON array of video tags
    category = Column(String(100), index=True)
    
    # Date information with multiple indexes for fast filtering
    upload_date = Column(DateTime, index=True)
    upload_year = Column(Integer, index=True)
    upload_month = Column(Integer, index=True)
    upload_day_of_week = Column(Integer, index=True)  # 0=Monday, 6=Sunday
    
    # Processing status with detailed tracking
    status = Column(String(50), default='pending', index=True)
    download_path = Column(String(1000))
    transcription_path = Column(String(1000))
    
    # Processing timestamps
    discovered_at = Column(DateTime, default=datetime.utcnow, index=True)
    downloaded_at = Column(DateTime, index=True)
    transcribed_at = Column(DateTime, index=True)
    
    # Error handling and quality metrics
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    processing_quality_score = Column(Float)  # Overall quality metric
    
    # File information
    file_size_bytes = Column(Integer)
    audio_format = Column(String(20))
    audio_bitrate = Column(Integer)
    
    # Relationships
    channel_obj = relationship("Channel", back_populates="videos")
    transcription = relationship("Transcription", back_populates="video", uselist=False)
    segments = relationship("TranscriptionSegment", back_populates="video", cascade="all, delete-orphan")
    keywords = relationship("VideoKeyword", back_populates="video", cascade="all, delete-orphan")

class Transcription(Base):
    """Enhanced transcription model with advanced search and analytics."""
    __tablename__ = 'transcriptions'
    
    id = Column(Integer, primary_key=True)
    video_id = Column(String(50), ForeignKey('videos.video_id'), nullable=False, unique=True, index=True)
    
    # Core transcription content
    full_text = Column(Text, index=True)  # Full-text search enabled
    word_count = Column(Integer, index=True)
    character_count = Column(Integer)
    
    # Structured data
    segments_json = Column(Text)  # Detailed segments with timestamps
    speakers_json = Column(Text)  # Speaker information
    
    # Language and quality metrics
    language = Column(String(10), index=True)
    language_confidence = Column(Float)
    confidence_score = Column(Float, index=True)
    processing_time_seconds = Column(Float)
    
    # Model information
    whisper_model = Column(String(50))
    whisperx_model = Column(String(50))
    
    # Content analysis
    sentiment_score = Column(Float)  # -1 to 1, negative to positive
    readability_score = Column(Float)  # Reading difficulty
    topic_categories = Column(Text)  # JSON array of detected topics
    
    # Speaker analytics
    speaker_count = Column(Integer, index=True)
    primary_speaker_percentage = Column(Float)  # % of time primary speaker talks
    speaker_change_frequency = Column(Float)  # How often speakers change
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    video = relationship("Video", back_populates="transcription")

class TranscriptionSegment(Base):
    """Individual transcription segments for granular analysis."""
    __tablename__ = 'transcription_segments'
    
    id = Column(Integer, primary_key=True)
    video_id = Column(String(50), ForeignKey('videos.video_id'), nullable=False, index=True)
    
    # Timing information
    start_time = Column(Float, nullable=False, index=True)
    end_time = Column(Float, nullable=False, index=True)
    duration = Column(Float, index=True)
    
    # Content
    text = Column(Text, nullable=False)
    word_count = Column(Integer)
    
    # Speaker information
    speaker_id = Column(String(50), index=True)
    speaker_confidence = Column(Float)
    
    # Quality metrics
    confidence_score = Column(Float, index=True)
    
    # Sequence information
    segment_index = Column(Integer, nullable=False, index=True)
    
    # Relationships
    video = relationship("Video", back_populates="segments")

class VideoKeyword(Base):
    """Extracted keywords and phrases for advanced search."""
    __tablename__ = 'video_keywords'
    
    id = Column(Integer, primary_key=True)
    video_id = Column(String(50), ForeignKey('videos.video_id'), nullable=False, index=True)
    
    # Keyword information
    keyword = Column(String(200), nullable=False, index=True)
    keyword_type = Column(String(50), index=True)  # 'entity', 'topic', 'phrase', 'technical_term'
    frequency = Column(Integer, default=1)
    relevance_score = Column(Float)  # How relevant this keyword is to the video
    
    # Context
    first_mention_time = Column(Float)  # When first mentioned in video
    context_snippet = Column(Text)  # Surrounding text for context
    
    # Relationships
    video = relationship("Video", back_populates="keywords")

class SearchQuery(Base):
    """Track search queries for analytics and optimization."""
    __tablename__ = 'search_queries'
    
    id = Column(Integer, primary_key=True)
    query_text = Column(String(500), nullable=False, index=True)
    query_type = Column(String(50), index=True)  # 'keyword', 'date_range', 'channel', 'combined'
    
    # Query parameters
    filters_json = Column(Text)  # JSON of applied filters
    results_count = Column(Integer)
    
    # Performance
    execution_time_ms = Column(Float)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

# Database indexes for optimal performance
Index('idx_video_upload_date_channel', Video.upload_date, Video.channel_id)
Index('idx_video_status_date', Video.status, Video.discovered_at)
Index('idx_transcription_language_confidence', Transcription.language, Transcription.confidence_score)
Index('idx_segment_video_time', TranscriptionSegment.video_id, TranscriptionSegment.start_time)
Index('idx_keyword_video_relevance', VideoKeyword.video_id, VideoKeyword.relevance_score)

class EnhancedDatabaseManager:
    """Enhanced database manager with advanced search and analytics capabilities."""
    
    def __init__(self):
        self.engine = create_engine(config.database_url, echo=False)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def get_session(self) -> Session:
        """Get a database session."""
        return self.SessionLocal()
    
    # ==================== ADVANCED SEARCH METHODS ====================
    
    def search_videos_by_keyword(self, keyword: str, limit: int = 100) -> List[Video]:
        """Search videos by keyword in title, description, or transcription."""
        with self.get_session() as session:
            query = session.query(Video).join(Transcription, Video.video_id == Transcription.video_id)
            
            # Search in multiple fields
            search_filter = or_(
                Video.title.contains(keyword),
                Video.description.contains(keyword),
                Transcription.full_text.contains(keyword)
            )
            
            return query.filter(search_filter).limit(limit).all()
    
    def search_videos_by_date_range(self, start_date: date, end_date: date, 
                                   channel_id: Optional[str] = None) -> List[Video]:
        """Search videos by upload date range, optionally filtered by channel."""
        with self.get_session() as session:
            query = session.query(Video).filter(
                Video.upload_date >= start_date,
                Video.upload_date <= end_date
            )
            
            if channel_id:
                query = query.filter(Video.channel_id == channel_id)
            
            return query.order_by(desc(Video.upload_date)).all()
    
    def search_videos_by_duration(self, min_duration: int, max_duration: int) -> List[Video]:
        """Search videos by duration range (in seconds)."""
        with self.get_session() as session:
            return session.query(Video).filter(
                Video.duration_seconds >= min_duration,
                Video.duration_seconds <= max_duration
            ).all()
    
    def search_videos_by_speaker_count(self, min_speakers: int, max_speakers: int) -> List[Video]:
        """Search videos by number of speakers."""
        with self.get_session() as session:
            return session.query(Video).join(Transcription).filter(
                Transcription.speaker_count >= min_speakers,
                Transcription.speaker_count <= max_speakers
            ).all()
    
    def advanced_search(self, filters: Dict[str, Any]) -> List[Video]:
        """Advanced search with multiple filters."""
        with self.get_session() as session:
            query = session.query(Video)
            
            # Join transcription if needed
            needs_transcription = any(key in filters for key in 
                ['keyword', 'language', 'confidence_min', 'speaker_count'])
            if needs_transcription:
                query = query.join(Transcription, Video.video_id == Transcription.video_id)
            
            # Apply filters
            if 'keyword' in filters:
                keyword = filters['keyword']
                query = query.filter(or_(
                    Video.title.contains(keyword),
                    Video.description.contains(keyword),
                    Transcription.full_text.contains(keyword)
                ))
            
            if 'channel_id' in filters:
                query = query.filter(Video.channel_id == filters['channel_id'])
            
            if 'start_date' in filters:
                query = query.filter(Video.upload_date >= filters['start_date'])
            
            if 'end_date' in filters:
                query = query.filter(Video.upload_date <= filters['end_date'])
            
            if 'min_duration' in filters:
                query = query.filter(Video.duration_seconds >= filters['min_duration'])
            
            if 'max_duration' in filters:
                query = query.filter(Video.duration_seconds <= filters['max_duration'])
            
            if 'language' in filters:
                query = query.filter(Transcription.language == filters['language'])
            
            if 'confidence_min' in filters:
                query = query.filter(Transcription.confidence_score >= filters['confidence_min'])
            
            if 'status' in filters:
                query = query.filter(Video.status == filters['status'])
            
            # Sorting
            sort_by = filters.get('sort_by', 'upload_date')
            sort_order = filters.get('sort_order', 'desc')
            
            if sort_by == 'upload_date':
                query = query.order_by(desc(Video.upload_date) if sort_order == 'desc' else asc(Video.upload_date))
            elif sort_by == 'duration':
                query = query.order_by(desc(Video.duration_seconds) if sort_order == 'desc' else asc(Video.duration_seconds))
            elif sort_by == 'confidence':
                query = query.order_by(desc(Transcription.confidence_score) if sort_order == 'desc' else asc(Transcription.confidence_score))
            
            # Limit
            limit = filters.get('limit', 100)
            return query.limit(limit).all()
    
    # ==================== ANALYTICS METHODS ====================
    
    def get_channel_analytics(self, channel_id: str) -> Dict[str, Any]:
        """Get comprehensive analytics for a channel."""
        with self.get_session() as session:
            # Basic stats
            video_count = session.query(Video).filter(Video.channel_id == channel_id).count()
            completed_count = session.query(Video).filter(
                Video.channel_id == channel_id,
                Video.status == 'completed'
            ).count()
            
            # Duration stats
            duration_stats = session.query(
                func.avg(Video.duration_seconds).label('avg_duration'),
                func.min(Video.duration_seconds).label('min_duration'),
                func.max(Video.duration_seconds).label('max_duration'),
                func.sum(Video.duration_seconds).label('total_duration')
            ).filter(Video.channel_id == channel_id).first()
            
            # Language distribution
            language_dist = session.query(
                Transcription.language,
                func.count(Transcription.language).label('count')
            ).join(Video).filter(Video.channel_id == channel_id).group_by(Transcription.language).all()
            
            # Upload patterns (by month)
            upload_pattern = session.query(
                extract('year', Video.upload_date).label('year'),
                extract('month', Video.upload_date).label('month'),
                func.count(Video.id).label('count')
            ).filter(Video.channel_id == channel_id).group_by('year', 'month').all()
            
            return {
                'video_count': video_count,
                'completed_count': completed_count,
                'completion_rate': completed_count / video_count if video_count > 0 else 0,
                'duration_stats': {
                    'average_seconds': duration_stats.avg_duration or 0,
                    'min_seconds': duration_stats.min_duration or 0,
                    'max_seconds': duration_stats.max_duration or 0,
                    'total_seconds': duration_stats.total_duration or 0,
                },
                'language_distribution': {lang: count for lang, count in language_dist},
                'upload_pattern': [{'year': year, 'month': month, 'count': count} 
                                 for year, month, count in upload_pattern]
            }
    
    def get_keyword_trends(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get trending keywords across all videos."""
        with self.get_session() as session:
            return session.query(
                VideoKeyword.keyword,
                func.count(VideoKeyword.id).label('frequency'),
                func.avg(VideoKeyword.relevance_score).label('avg_relevance')
            ).group_by(VideoKeyword.keyword).order_by(
                desc('frequency')
            ).limit(limit).all()
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get overall processing statistics."""
        with self.get_session() as session:
            # Status distribution
            status_dist = session.query(
                Video.status,
                func.count(Video.status).label('count')
            ).group_by(Video.status).all()
            
            # Processing time stats
            time_stats = session.query(
                func.avg(Transcription.processing_time_seconds).label('avg_time'),
                func.min(Transcription.processing_time_seconds).label('min_time'),
                func.max(Transcription.processing_time_seconds).label('max_time')
            ).first()
            
            # Quality stats
            quality_stats = session.query(
                func.avg(Transcription.confidence_score).label('avg_confidence'),
                func.min(Transcription.confidence_score).label('min_confidence'),
                func.max(Transcription.confidence_score).label('max_confidence')
            ).first()
            
            return {
                'status_distribution': {status: count for status, count in status_dist},
                'processing_time': {
                    'average_seconds': time_stats.avg_time or 0,
                    'min_seconds': time_stats.min_time or 0,
                    'max_seconds': time_stats.max_time or 0,
                },
                'quality_metrics': {
                    'average_confidence': quality_stats.avg_confidence or 0,
                    'min_confidence': quality_stats.min_confidence or 0,
                    'max_confidence': quality_stats.max_confidence or 0,
                }
            }
    
    # ==================== DATA EXPORT METHODS ====================
    
    def export_videos_to_json(self, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Export videos with transcriptions to JSON format."""
        videos = self.advanced_search(filters or {})
        
        result = []
        for video in videos:
            video_data = {
                'video_id': video.video_id,
                'title': video.title,
                'description': video.description,
                'channel_name': video.channel_name,
                'channel_id': video.channel_id,
                'url': video.url,
                'duration_seconds': video.duration_seconds,
                'upload_date': video.upload_date.isoformat() if video.upload_date else None,
                'view_count': video.view_count,
                'like_count': video.like_count,
                'category': video.category,
                'status': video.status,
                'discovered_at': video.discovered_at.isoformat() if video.discovered_at else None,
                'transcribed_at': video.transcribed_at.isoformat() if video.transcribed_at else None,
            }
            
            # Add transcription data if available
            if video.transcription:
                video_data['transcription'] = {
                    'full_text': video.transcription.full_text,
                    'language': video.transcription.language,
                    'confidence_score': video.transcription.confidence_score,
                    'word_count': video.transcription.word_count,
                    'speaker_count': video.transcription.speaker_count,
                    'segments': json.loads(video.transcription.segments_json) if video.transcription.segments_json else [],
                    'speakers': json.loads(video.transcription.speakers_json) if video.transcription.speakers_json else {}
                }
            
            result.append(video_data)
        
        return result

# Global enhanced database manager instance
enhanced_db = EnhancedDatabaseManager()
