import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Types
export interface SystemStatus {
  is_running: boolean;
  channels: {
    total: number;
    active: number;
  };
  videos: {
    total: number;
    pending: number;
    completed: number;
    failed: number;
  };
  storage: {
    immediate_cleanup: boolean;
    audio_only_downloads: boolean;
    compressed_format: string;
    estimated_storage_saved_mb: number;
  };
  performance: {
    average_processing_time: number;
    videos_per_hour: number;
  };
}

export interface Channel {
  id: number;
  channel_id: string;
  channel_name: string;
  channel_url: string;
  is_active: boolean;
  last_checked: string | null;
  created_at: string | null;
}

export interface Video {
  id: number;
  video_id: string;
  title: string;
  channel_name: string;
  url: string;
  duration_seconds: number | null;
  upload_date: string | null;
  status: string;
  discovered_at: string | null;
  transcribed_at: string | null;
}

export interface Transcription {
  video_id: string;
  full_text: string;
  segments: Array<{
    start: number;
    end: number;
    text: string;
    speaker?: string;
  }>;
  speakers: {
    has_speaker_info: boolean;
    total_speakers?: number;
    speakers?: string[];
  };
  language: string;
  confidence_score: number;
  word_count: number;
  speaker_count: number;
  created_at: string;
}

export interface SearchResult {
  video: Video;
  relevance_score: number;
  matched_keywords: string[];
}

export interface TrendingTopic {
  keyword: string;
  frequency: number;
  video_count: number;
  trend_score: number;
}

// API functions
export const apiClient = {
  // System
  getStatus: (): Promise<SystemStatus> => 
    api.get('/status').then(res => res.data),

  // Channels
  getChannels: (): Promise<Channel[]> => 
    api.get('/channels').then(res => res.data),
  
  addChannel: (url: string): Promise<{ message: string; url: string }> => 
    api.post('/channels', { url }).then(res => res.data),

  // Videos
  getVideos: (limit = 50, status?: string): Promise<Video[]> => 
    api.get('/videos', { params: { limit, status } }).then(res => res.data),
  
  getTranscription: (videoId: string): Promise<Transcription> => 
    api.get(`/videos/${videoId}/transcription`).then(res => res.data),
  
  processVideo: (url: string): Promise<{ message: string; url: string }> => 
    api.post('/videos/process', { url }).then(res => res.data),

  // Monitoring
  startMonitoring: (): Promise<{ message: string }> => 
    api.post('/monitoring/start').then(res => res.data),
  
  stopMonitoring: (): Promise<{ message: string }> => 
    api.post('/monitoring/stop').then(res => res.data),
  
  runCycle: (): Promise<{ message: string }> => 
    api.post('/monitoring/cycle').then(res => res.data),

  // Search
  searchVideos: (params: {
    keywords?: string[];
    start_date?: string;
    end_date?: string;
    channel_id?: string;
    limit?: number;
  }): Promise<SearchResult[]> => 
    api.post('/search', params).then(res => res.data),

  // Analytics
  getTrendingTopics: (days = 30, limit = 20): Promise<TrendingTopic[]> => 
    api.get('/analytics/trending', { params: { days, limit } }).then(res => res.data),

  // Storage
  getStorageStatus: (): Promise<any> => 
    api.get('/storage').then(res => res.data),
  
  cleanupStorage: (force = false): Promise<{ message: string }> => 
    api.post('/storage/cleanup', { force }).then(res => res.data),
};
