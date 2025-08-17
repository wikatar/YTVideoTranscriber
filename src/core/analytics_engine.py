"""Advanced analytics and search engine for video transcription data."""

import json
import re
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional, Tuple, Set
from collections import Counter, defaultdict
import logging

from sqlalchemy import func, or_, desc
from src.models.enhanced_database import enhanced_db, Video, Transcription, VideoKeyword

logger = logging.getLogger(__name__)

class AnalyticsEngine:
    """Advanced analytics engine for video transcription data."""
    
    def __init__(self):
        self.db = enhanced_db
    
    # ==================== KEYWORD EXTRACTION & ANALYSIS ====================
    
    def extract_keywords_from_text(self, text: str, video_id: str) -> List[Dict[str, Any]]:
        """Extract keywords and phrases from transcription text."""
        if not text:
            return []
        
        keywords = []
        
        # Simple keyword extraction (can be enhanced with NLP libraries)
        # Remove common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before', 'after',
            'above', 'below', 'between', 'among', 'is', 'are', 'was', 'were', 'be', 'been',
            'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those',
            'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'
        }
        
        # Extract single words (frequency > 2)
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        word_freq = Counter(word for word in words if word not in stop_words)
        
        for word, freq in word_freq.items():
            if freq >= 3:  # Only include words that appear multiple times
                keywords.append({
                    'keyword': word,
                    'type': 'word',
                    'frequency': freq,
                    'relevance_score': min(freq / 10.0, 1.0)  # Normalize to 0-1
                })
        
        # Extract phrases (2-3 words)
        sentences = re.split(r'[.!?]+', text)
        phrases = []
        for sentence in sentences:
            words_in_sentence = re.findall(r'\b[a-zA-Z]+\b', sentence.lower())
            for i in range(len(words_in_sentence) - 1):
                if words_in_sentence[i] not in stop_words and words_in_sentence[i+1] not in stop_words:
                    phrase = f"{words_in_sentence[i]} {words_in_sentence[i+1]}"
                    phrases.append(phrase)
        
        phrase_freq = Counter(phrases)
        for phrase, freq in phrase_freq.items():
            if freq >= 2:
                keywords.append({
                    'keyword': phrase,
                    'type': 'phrase',
                    'frequency': freq,
                    'relevance_score': min(freq / 5.0, 1.0)
                })
        
        # Technical terms (words with specific patterns)
        tech_patterns = [
            r'\b[A-Z]{2,}\b',  # Acronyms
            r'\b\w+\.\w+\b',   # Domain-like terms
            r'\b\w+_\w+\b',    # Underscore terms
            r'\b\d+\w+\b',     # Number-word combinations
        ]
        
        for pattern in tech_patterns:
            matches = re.findall(pattern, text)
            for match in set(matches):  # Remove duplicates
                if len(match) > 2:
                    keywords.append({
                        'keyword': match,
                        'type': 'technical_term',
                        'frequency': text.count(match),
                        'relevance_score': 0.8  # Technical terms are often important
                    })
        
        return keywords
    
    def update_video_keywords(self, video_id: str, transcription_text: str):
        """Extract and store keywords for a video."""
        keywords = self.extract_keywords_from_text(transcription_text, video_id)
        
        with self.db.get_session() as session:
            # Remove existing keywords
            session.query(VideoKeyword).filter(VideoKeyword.video_id == video_id).delete()
            
            # Add new keywords
            for kw_data in keywords:
                keyword = VideoKeyword(
                    video_id=video_id,
                    keyword=kw_data['keyword'],
                    keyword_type=kw_data['type'],
                    frequency=kw_data['frequency'],
                    relevance_score=kw_data['relevance_score']
                )
                session.add(keyword)
            
            session.commit()
    
    # ==================== SEARCH FUNCTIONALITY ====================
    
    def search_by_keywords(self, keywords: List[str], match_all: bool = False, 
                          limit: int = 100) -> List[Dict[str, Any]]:
        """Search videos by keywords with ranking."""
        with self.db.get_session() as session:
            # Build query
            query = session.query(Video).join(Transcription, Video.video_id == Transcription.video_id)
            
            if match_all:
                # All keywords must be present
                for keyword in keywords:
                    query = query.filter(Transcription.full_text.contains(keyword))
            else:
                # Any keyword can match
                keyword_filters = [Transcription.full_text.contains(kw) for kw in keywords]
                query = query.filter(or_(*keyword_filters))
            
            videos = query.limit(limit * 2).all()  # Get more for ranking
            
            # Rank results by keyword relevance
            ranked_results = []
            for video in videos:
                if video.transcription:
                    score = self._calculate_keyword_relevance_score(
                        video.transcription.full_text, keywords
                    )
                    ranked_results.append({
                        'video': video,
                        'relevance_score': score,
                        'matched_keywords': self._find_matched_keywords(
                            video.transcription.full_text, keywords
                        )
                    })
            
            # Sort by relevance and return top results
            ranked_results.sort(key=lambda x: x['relevance_score'], reverse=True)
            return ranked_results[:limit]
    
    def _calculate_keyword_relevance_score(self, text: str, keywords: List[str]) -> float:
        """Calculate how relevant a text is to given keywords."""
        if not text or not keywords:
            return 0.0
        
        text_lower = text.lower()
        total_score = 0.0
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            count = text_lower.count(keyword_lower)
            
            if count > 0:
                # Base score from frequency
                freq_score = min(count / 10.0, 1.0)
                
                # Bonus for exact word matches vs partial matches
                word_matches = len(re.findall(r'\b' + re.escape(keyword_lower) + r'\b', text_lower))
                exact_bonus = word_matches / max(count, 1) * 0.5
                
                total_score += freq_score + exact_bonus
        
        return total_score / len(keywords)  # Average across keywords
    
    def _find_matched_keywords(self, text: str, keywords: List[str]) -> List[str]:
        """Find which keywords actually match in the text."""
        text_lower = text.lower()
        matched = []
        
        for keyword in keywords:
            if keyword.lower() in text_lower:
                matched.append(keyword)
        
        return matched
    
    def search_by_date_and_channel(self, start_date: Optional[date] = None,
                                  end_date: Optional[date] = None,
                                  channel_ids: Optional[List[str]] = None,
                                  channel_names: Optional[List[str]] = None) -> List[Video]:
        """Search videos by date range and/or channels."""
        filters = {}
        
        if start_date:
            filters['start_date'] = start_date
        if end_date:
            filters['end_date'] = end_date
        if channel_ids:
            filters['channel_id'] = channel_ids[0]  # For now, single channel
        
        return self.db.advanced_search(filters)
    
    def search_by_content_type(self, min_speakers: Optional[int] = None,
                              max_speakers: Optional[int] = None,
                              languages: Optional[List[str]] = None,
                              min_confidence: Optional[float] = None) -> List[Video]:
        """Search videos by content characteristics."""
        filters = {}
        
        if min_confidence:
            filters['confidence_min'] = min_confidence
        if languages:
            filters['language'] = languages[0]  # For now, single language
        
        return self.db.advanced_search(filters)
    
    # ==================== ANALYTICS & INSIGHTS ====================
    
    def get_trending_topics(self, days_back: int = 30, limit: int = 20) -> List[Dict[str, Any]]:
        """Get trending topics/keywords from recent videos."""
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        with self.db.get_session() as session:
            # Get keywords from recent videos
            trending = session.query(
                VideoKeyword.keyword,
                func.count(VideoKeyword.id).label('frequency'),
                func.avg(VideoKeyword.relevance_score).label('avg_relevance'),
                func.count(func.distinct(VideoKeyword.video_id)).label('video_count')
            ).join(Video, VideoKeyword.video_id == Video.video_id).filter(
                Video.upload_date >= cutoff_date
            ).group_by(VideoKeyword.keyword).having(
                func.count(VideoKeyword.id) >= 3  # Minimum frequency
            ).order_by(desc('frequency')).limit(limit).all()
            
            return [{
                'keyword': keyword,
                'frequency': frequency,
                'avg_relevance': avg_relevance,
                'video_count': video_count,
                'trend_score': frequency * avg_relevance * video_count
            } for keyword, frequency, avg_relevance, video_count in trending]
    
    def get_channel_comparison(self, channel_ids: List[str]) -> Dict[str, Any]:
        """Compare multiple channels across various metrics."""
        comparison = {}
        
        for channel_id in channel_ids:
            analytics = self.db.get_channel_analytics(channel_id)
            
            # Get top keywords for this channel
            with self.db.get_session() as session:
                top_keywords = session.query(
                    VideoKeyword.keyword,
                    func.count(VideoKeyword.id).label('frequency')
                ).join(Video).filter(
                    Video.channel_id == channel_id
                ).group_by(VideoKeyword.keyword).order_by(
                    desc('frequency')
                ).limit(10).all()
                
                analytics['top_keywords'] = [
                    {'keyword': kw, 'frequency': freq} 
                    for kw, freq in top_keywords
                ]
            
            comparison[channel_id] = analytics
        
        return comparison
    
    def get_content_insights(self, video_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get insights about content patterns and characteristics."""
        with self.db.get_session() as session:
            base_query = session.query(Video).join(Transcription)
            
            if video_ids:
                base_query = base_query.filter(Video.video_id.in_(video_ids))
            
            videos = base_query.all()
            
            if not videos:
                return {}
            
            # Analyze patterns
            insights = {
                'total_videos': len(videos),
                'language_distribution': {},
                'duration_patterns': {},
                'speaker_patterns': {},
                'quality_metrics': {},
                'upload_patterns': {},
                'common_themes': []
            }
            
            # Language distribution
            languages = [v.transcription.language for v in videos if v.transcription and v.transcription.language]
            insights['language_distribution'] = dict(Counter(languages))
            
            # Duration patterns
            durations = [v.duration_seconds for v in videos if v.duration_seconds]
            if durations:
                insights['duration_patterns'] = {
                    'average': sum(durations) / len(durations),
                    'median': sorted(durations)[len(durations)//2],
                    'min': min(durations),
                    'max': max(durations)
                }
            
            # Speaker patterns
            speaker_counts = [v.transcription.speaker_count for v in videos 
                            if v.transcription and v.transcription.speaker_count]
            if speaker_counts:
                insights['speaker_patterns'] = {
                    'average_speakers': sum(speaker_counts) / len(speaker_counts),
                    'most_common_count': Counter(speaker_counts).most_common(1)[0][0],
                    'distribution': dict(Counter(speaker_counts))
                }
            
            # Quality metrics
            confidence_scores = [v.transcription.confidence_score for v in videos 
                               if v.transcription and v.transcription.confidence_score]
            if confidence_scores:
                insights['quality_metrics'] = {
                    'average_confidence': sum(confidence_scores) / len(confidence_scores),
                    'min_confidence': min(confidence_scores),
                    'max_confidence': max(confidence_scores)
                }
            
            # Upload patterns (by day of week)
            upload_days = [v.upload_date.weekday() for v in videos if v.upload_date]
            day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            insights['upload_patterns'] = {
                day_names[day]: count for day, count in Counter(upload_days).items()
            }
            
            return insights
    
    # ==================== DATA EXPORT & REPORTING ====================
    
    def export_search_results(self, search_results: List[Dict[str, Any]], 
                            format: str = 'json') -> str:
        """Export search results in various formats."""
        if format == 'json':
            export_data = []
            for result in search_results:
                video = result['video']
                export_data.append({
                    'video_id': video.video_id,
                    'title': video.title,
                    'channel_name': video.channel_name,
                    'upload_date': video.upload_date.isoformat() if video.upload_date else None,
                    'duration_seconds': video.duration_seconds,
                    'relevance_score': result.get('relevance_score', 0),
                    'matched_keywords': result.get('matched_keywords', []),
                    'url': video.url,
                    'transcription_preview': (video.transcription.full_text[:200] + '...' 
                                           if video.transcription and video.transcription.full_text 
                                           else None)
                })
            return json.dumps(export_data, indent=2)
        
        elif format == 'csv':
            # Simple CSV export
            lines = ['video_id,title,channel_name,upload_date,duration_seconds,relevance_score,url']
            for result in search_results:
                video = result['video']
                lines.append(f"{video.video_id},{video.title},{video.channel_name},"
                           f"{video.upload_date or ''},{video.duration_seconds or 0},"
                           f"{result.get('relevance_score', 0)},{video.url}")
            return '\n'.join(lines)
        
        return str(search_results)
    
    def generate_analytics_report(self, channel_ids: Optional[List[str]] = None,
                                date_range: Optional[Tuple[date, date]] = None) -> Dict[str, Any]:
        """Generate a comprehensive analytics report."""
        report = {
            'generated_at': datetime.utcnow().isoformat(),
            'parameters': {
                'channel_ids': channel_ids,
                'date_range': [d.isoformat() if d else None for d in (date_range or (None, None))]
            }
        }
        
        # Overall stats
        report['overall_stats'] = self.db.get_processing_stats()
        
        # Channel-specific analytics
        if channel_ids:
            report['channel_analytics'] = {}
            for channel_id in channel_ids:
                report['channel_analytics'][channel_id] = self.db.get_channel_analytics(channel_id)
        
        # Trending topics
        report['trending_topics'] = self.get_trending_topics()
        
        # Content insights
        filters = {}
        if channel_ids:
            filters['channel_id'] = channel_ids[0]  # For now, single channel
        if date_range:
            filters['start_date'], filters['end_date'] = date_range
        
        matching_videos = self.db.advanced_search(filters)
        video_ids = [v.video_id for v in matching_videos]
        report['content_insights'] = self.get_content_insights(video_ids)
        
        return report

# Global analytics engine instance
analytics_engine = AnalyticsEngine()
