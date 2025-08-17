"""YouTube channel monitoring system."""

import re
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from urllib.parse import urlparse, parse_qs
import requests
import feedparser
from bs4 import BeautifulSoup
import yt_dlp

from src.models.database import db, Channel, Video
from src.utils.config import config

logger = logging.getLogger(__name__)

class YouTubeMonitor:
    """Monitor YouTube channels for new videos."""
    
    def __init__(self):
        self.ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
        }
    
    def extract_channel_id(self, channel_url: str) -> Optional[str]:
        """Extract channel ID from various YouTube URL formats."""
        try:
            # Handle different URL formats
            if 'youtube.com/channel/' in channel_url:
                return channel_url.split('/channel/')[1].split('/')[0]
            elif 'youtube.com/c/' in channel_url or 'youtube.com/user/' in channel_url:
                # For custom URLs, we need to resolve to channel ID
                with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                    info = ydl.extract_info(channel_url, download=False)
                    return info.get('channel_id')
            elif 'youtube.com/@' in channel_url:
                # Handle new @username format
                with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                    info = ydl.extract_info(channel_url, download=False)
                    return info.get('channel_id')
            else:
                logger.error(f"Unsupported YouTube URL format: {channel_url}")
                return None
        except Exception as e:
            logger.error(f"Error extracting channel ID from {channel_url}: {e}")
            return None
    
    def get_channel_info(self, channel_url: str) -> Optional[Dict]:
        """Get channel information including name and ID."""
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(channel_url, download=False)
                return {
                    'channel_id': info.get('channel_id'),
                    'channel_name': info.get('channel', info.get('uploader', 'Unknown')),
                    'channel_url': channel_url
                }
        except Exception as e:
            logger.error(f"Error getting channel info for {channel_url}: {e}")
            return None
    
    def add_channel(self, channel_url: str) -> Optional[Channel]:
        """Add a channel to monitor."""
        channel_info = self.get_channel_info(channel_url)
        if not channel_info:
            return None
        
        try:
            channel = db.add_channel(
                channel_id=channel_info['channel_id'],
                channel_name=channel_info['channel_name'],
                channel_url=channel_info['channel_url']
            )
            logger.info(f"Added channel: {channel.channel_name} ({channel.channel_id})")
            return channel
        except Exception as e:
            logger.error(f"Error adding channel to database: {e}")
            return None
    
    def get_recent_videos_rss(self, channel_id: str, hours_back: int = 24) -> List[Dict]:
        """Get recent videos using RSS feed (faster, no API key needed)."""
        try:
            rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
            feed = feedparser.parse(rss_url)
            
            videos = []
            cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
            
            for entry in feed.entries:
                # Parse published date
                published = datetime.strptime(entry.published, '%Y-%m-%dT%H:%M:%S%z').replace(tzinfo=None)
                
                if published > cutoff_time:
                    video_id = entry.yt_videoid
                    videos.append({
                        'video_id': video_id,
                        'title': entry.title,
                        'url': f"https://www.youtube.com/watch?v={video_id}",
                        'published': published,
                        'channel_id': channel_id
                    })
            
            return videos
        except Exception as e:
            logger.error(f"Error fetching RSS feed for channel {channel_id}: {e}")
            return []
    
    def get_recent_videos_ydl(self, channel_url: str, max_videos: int = 10) -> List[Dict]:
        """Get recent videos using yt-dlp (more detailed info)."""
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
                'playlistend': max_videos,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"{channel_url}/videos", download=False)
                
                videos = []
                for entry in info.get('entries', []):
                    if entry:
                        videos.append({
                            'video_id': entry.get('id'),
                            'title': entry.get('title'),
                            'url': entry.get('url', f"https://www.youtube.com/watch?v={entry.get('id')}"),
                            'duration': entry.get('duration'),
                            'upload_date': self._parse_upload_date(entry.get('upload_date')),
                            'channel_id': info.get('channel_id')
                        })
                
                return videos
        except Exception as e:
            logger.error(f"Error fetching videos with yt-dlp for {channel_url}: {e}")
            return []
    
    def _parse_upload_date(self, upload_date_str: Optional[str]) -> Optional[datetime]:
        """Parse upload date string to datetime."""
        if not upload_date_str:
            return None
        try:
            return datetime.strptime(upload_date_str, '%Y%m%d')
        except:
            return None
    
    def check_channel_for_new_videos(self, channel: Channel) -> List[Video]:
        """Check a specific channel for new videos."""
        logger.info(f"Checking channel: {channel.channel_name}")
        
        # First try RSS (faster)
        videos_data = self.get_recent_videos_rss(channel.channel_id)
        
        # If RSS fails or returns no results, try yt-dlp
        if not videos_data:
            videos_data = self.get_recent_videos_ydl(channel.channel_url)
        
        new_videos = []
        for video_data in videos_data:
            # Check if video already exists
            existing_video = None
            with db.get_session() as session:
                existing_video = session.query(Video).filter(
                    Video.video_id == video_data['video_id']
                ).first()
            
            if not existing_video:
                # Check video duration if available
                duration = video_data.get('duration')
                if duration and duration > config.max_video_length_minutes * 60:
                    logger.info(f"Skipping long video: {video_data['title']} ({duration/60:.1f} min)")
                    continue
                
                video = db.add_video(
                    video_id=video_data['video_id'],
                    title=video_data['title'],
                    channel_id=channel.channel_id,
                    channel_name=channel.channel_name,
                    url=video_data['url'],
                    duration_seconds=duration,
                    upload_date=video_data.get('upload_date') or video_data.get('published')
                )
                new_videos.append(video)
                logger.info(f"Found new video: {video.title}")
        
        # Update last checked time
        db.update_channel_last_checked(channel.channel_id)
        
        return new_videos
    
    def check_all_channels(self) -> List[Video]:
        """Check all active channels for new videos."""
        logger.info("Starting channel check for all active channels")
        
        channels = db.get_active_channels()
        all_new_videos = []
        
        for channel in channels:
            try:
                new_videos = self.check_channel_for_new_videos(channel)
                all_new_videos.extend(new_videos)
            except Exception as e:
                logger.error(f"Error checking channel {channel.channel_name}: {e}")
        
        logger.info(f"Found {len(all_new_videos)} new videos across all channels")
        return all_new_videos
    
    def get_video_metadata(self, video_url: str) -> Optional[Dict]:
        """Get detailed metadata for a specific video."""
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                return {
                    'video_id': info.get('id'),
                    'title': info.get('title'),
                    'duration': info.get('duration'),
                    'upload_date': self._parse_upload_date(info.get('upload_date')),
                    'channel_id': info.get('channel_id'),
                    'channel_name': info.get('channel'),
                    'description': info.get('description'),
                    'view_count': info.get('view_count'),
                    'like_count': info.get('like_count'),
                }
        except Exception as e:
            logger.error(f"Error getting video metadata for {video_url}: {e}")
            return None
