#!/usr/bin/env python3
"""
Advanced Usage Examples - Demonstrating the Enhanced Data Structure

This script shows how to leverage the powerful analytics and search capabilities
of the enhanced video transcription system.
"""

import sys
from pathlib import Path
from datetime import datetime, date, timedelta

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.utils.logging_config import setup_logging
from src.core.analytics_engine import analytics_engine
from src.models.enhanced_database import enhanced_db

def example_keyword_search():
    """Example: Advanced keyword searching with relevance ranking."""
    print("🔍 KEYWORD SEARCH EXAMPLE")
    print("=" * 50)
    
    # Search for AI/ML content
    keywords = ["artificial intelligence", "machine learning", "neural networks"]
    results = analytics_engine.search_by_keywords(keywords, match_all=False, limit=10)
    
    print(f"Found {len(results)} videos about AI/ML:")
    for i, result in enumerate(results[:5], 1):
        video = result['video']
        print(f"{i}. {video.title}")
        print(f"   Channel: {video.channel_name}")
        print(f"   Relevance: {result['relevance_score']:.2f}")
        print(f"   Matched: {', '.join(result['matched_keywords'])}")
        print()

def example_date_channel_filtering():
    """Example: Filter videos by date range and channel."""
    print("📅 DATE & CHANNEL FILTERING EXAMPLE")
    print("=" * 50)
    
    # Get videos from last 30 days
    end_date = date.today()
    start_date = end_date - timedelta(days=30)
    
    videos = analytics_engine.search_by_date_and_channel(
        start_date=start_date,
        end_date=end_date
    )
    
    print(f"Videos from last 30 days: {len(videos)}")
    
    # Group by channel
    by_channel = {}
    for video in videos:
        channel = video.channel_name
        if channel not in by_channel:
            by_channel[channel] = []
        by_channel[channel].append(video)
    
    print("\nBreakdown by channel:")
    for channel, channel_videos in by_channel.items():
        print(f"  {channel}: {len(channel_videos)} videos")

def example_trending_analysis():
    """Example: Analyze trending topics and keywords."""
    print("📈 TRENDING TOPICS EXAMPLE")
    print("=" * 50)
    
    # Get trending topics from last 7 days
    trends = analytics_engine.get_trending_topics(days_back=7, limit=15)
    
    print("Top trending topics this week:")
    for i, trend in enumerate(trends[:10], 1):
        print(f"{i:2d}. {trend['keyword']}")
        print(f"     Frequency: {trend['frequency']}, Videos: {trend['video_count']}")
        print(f"     Trend Score: {trend['trend_score']:.1f}")
        print()

def example_channel_comparison():
    """Example: Compare multiple channels across metrics."""
    print("⚖️  CHANNEL COMPARISON EXAMPLE")
    print("=" * 50)
    
    # Get all channels for comparison
    with enhanced_db.get_session() as session:
        channels = session.query(enhanced_db.Channel).limit(3).all()
        channel_ids = [ch.channel_id for ch in channels]
    
    if len(channel_ids) < 2:
        print("Need at least 2 channels for comparison")
        return
    
    comparison = analytics_engine.get_channel_comparison(channel_ids)
    
    print(f"Comparing {len(channel_ids)} channels:")
    print()
    
    # Display metrics
    metrics = [
        ('Video Count', 'video_count'),
        ('Completion Rate', 'completion_rate'),
        ('Avg Duration (min)', lambda x: x['duration_stats']['average_seconds']/60),
        ('Total Hours', lambda x: x['duration_stats']['total_seconds']/3600),
    ]
    
    for metric_name, metric_key in metrics:
        print(f"{metric_name}:")
        for i, channel_id in enumerate(channel_ids):
            if channel_id in comparison:
                if callable(metric_key):
                    value = metric_key(comparison[channel_id])
                    if 'Rate' in metric_name:
                        print(f"  Channel {i+1}: {value:.1%}")
                    else:
                        print(f"  Channel {i+1}: {value:.1f}")
                else:
                    value = comparison[channel_id].get(metric_key, 0)
                    print(f"  Channel {i+1}: {value}")
        print()

def example_content_insights():
    """Example: Analyze content patterns and characteristics."""
    print("🧠 CONTENT INSIGHTS EXAMPLE")
    print("=" * 50)
    
    # Get insights for all videos
    insights = analytics_engine.get_content_insights()
    
    if not insights:
        print("No content insights available yet")
        return
    
    print(f"Analysis of {insights.get('total_videos', 0)} videos:")
    print()
    
    # Language distribution
    lang_dist = insights.get('language_distribution', {})
    if lang_dist:
        print("Language Distribution:")
        for lang, count in sorted(lang_dist.items(), key=lambda x: x[1], reverse=True):
            print(f"  {lang}: {count} videos")
        print()
    
    # Duration patterns
    duration = insights.get('duration_patterns', {})
    if duration:
        print("Duration Patterns:")
        print(f"  Average: {duration.get('average', 0)/60:.1f} minutes")
        print(f"  Range: {duration.get('min', 0)/60:.1f} - {duration.get('max', 0)/60:.1f} minutes")
        print()
    
    # Speaker patterns
    speakers = insights.get('speaker_patterns', {})
    if speakers:
        print("Speaker Patterns:")
        print(f"  Average speakers per video: {speakers.get('average_speakers', 0):.1f}")
        print(f"  Most common speaker count: {speakers.get('most_common_count', 0)}")
        
        dist = speakers.get('distribution', {})
        if dist:
            print("  Distribution:")
            for count, videos in sorted(dist.items()):
                print(f"    {count} speakers: {videos} videos")
        print()
    
    # Quality metrics
    quality = insights.get('quality_metrics', {})
    if quality:
        print("Quality Metrics:")
        print(f"  Average confidence: {quality.get('average_confidence', 0):.2f}")
        print(f"  Range: {quality.get('min_confidence', 0):.2f} - {quality.get('max_confidence', 0):.2f}")
        print()

def example_advanced_search():
    """Example: Complex multi-criteria search."""
    print("🎯 ADVANCED SEARCH EXAMPLE")
    print("=" * 50)
    
    # Complex search with multiple criteria
    filters = {
        'keyword': 'python',
        'start_date': date.today() - timedelta(days=90),  # Last 3 months
        'confidence_min': 0.7,  # High quality transcriptions
        'language': 'en',  # English only
        'sort_by': 'confidence',
        'sort_order': 'desc',
        'limit': 10
    }
    
    videos = enhanced_db.advanced_search(filters)
    
    print(f"High-quality Python videos from last 3 months: {len(videos)}")
    print()
    
    for i, video in enumerate(videos[:5], 1):
        print(f"{i}. {video.title}")
        print(f"   Channel: {video.channel_name}")
        print(f"   Upload: {video.upload_date.strftime('%Y-%m-%d') if video.upload_date else 'Unknown'}")
        if video.transcription:
            print(f"   Language: {video.transcription.language}")
            print(f"   Confidence: {video.transcription.confidence_score:.2f}")
            print(f"   Speakers: {video.transcription.speaker_count}")
        print()

def example_data_export():
    """Example: Export data for external analysis."""
    print("📤 DATA EXPORT EXAMPLE")
    print("=" * 50)
    
    # Export recent high-quality videos
    filters = {
        'start_date': date.today() - timedelta(days=30),
        'confidence_min': 0.8,
        'limit': 50
    }
    
    export_data = enhanced_db.export_videos_to_json(filters)
    
    print(f"Exported {len(export_data)} high-quality videos from last month")
    
    if export_data:
        sample = export_data[0]
        print("\nSample export structure:")
        for key in sample.keys():
            print(f"  {key}: {type(sample[key]).__name__}")
        
        # Show transcription structure if available
        if 'transcription' in sample and sample['transcription']:
            print("\nTranscription data includes:")
            for key in sample['transcription'].keys():
                print(f"    {key}: {type(sample['transcription'][key]).__name__}")

def example_analytics_report():
    """Example: Generate comprehensive analytics report."""
    print("📊 ANALYTICS REPORT EXAMPLE")
    print("=" * 50)
    
    # Generate report for last month
    date_range = (
        date.today() - timedelta(days=30),
        date.today()
    )
    
    report = analytics_engine.generate_analytics_report(date_range=date_range)
    
    print("Generated comprehensive analytics report")
    print("\nReport sections:")
    for section in report.keys():
        if section != 'parameters':
            print(f"  • {section}")
    
    # Show overall stats
    overall = report.get('overall_stats', {})
    if overall:
        print(f"\nOverall Statistics:")
        status_dist = overall.get('status_distribution', {})
        for status, count in status_dist.items():
            print(f"  {status.title()}: {count}")

def main():
    """Run all examples."""
    # Setup logging
    logger = setup_logging()
    
    print("🎥 ADVANCED VIDEO TRANSCRIPTION SYSTEM")
    print("Enhanced Data Structure & Analytics Examples")
    print("=" * 60)
    print()
    
    examples = [
        example_keyword_search,
        example_date_channel_filtering,
        example_trending_analysis,
        example_channel_comparison,
        example_content_insights,
        example_advanced_search,
        example_data_export,
        example_analytics_report,
    ]
    
    for i, example_func in enumerate(examples, 1):
        try:
            example_func()
            if i < len(examples):
                print("\n" + "─" * 60 + "\n")
        except Exception as e:
            print(f"Example failed: {e}")
            print()
    
    print("🎉 All examples completed!")
    print("\nThe enhanced data structure enables:")
    print("  ✓ Lightning-fast keyword search with relevance ranking")
    print("  ✓ Flexible date and channel filtering")
    print("  ✓ Trending topic analysis and insights")
    print("  ✓ Multi-channel comparison and benchmarking")
    print("  ✓ Content pattern analysis and speaker insights")
    print("  ✓ Complex multi-criteria searches")
    print("  ✓ Data export for external analysis tools")
    print("  ✓ Comprehensive analytics reporting")

if __name__ == "__main__":
    main()
