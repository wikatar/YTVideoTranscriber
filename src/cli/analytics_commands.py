"""Enhanced CLI commands for analytics and search functionality."""

import click
import json
from datetime import datetime, date, timedelta
from typing import List, Optional
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from src.core.analytics_engine import analytics_engine
from src.models.enhanced_database import enhanced_db

@click.group()
def analytics():
    """Advanced analytics and search commands."""
    pass

@analytics.command()
@click.option('--keywords', '-k', multiple=True, help='Keywords to search for')
@click.option('--match-all', is_flag=True, help='All keywords must be present (AND logic)')
@click.option('--limit', '-l', default=20, help='Maximum number of results')
@click.option('--format', 'output_format', default='table', type=click.Choice(['table', 'json', 'csv']),
              help='Output format')
@click.option('--export', help='Export results to file')
def search_keywords(keywords, match_all, limit, output_format, export):
    """Search videos by keywords in transcriptions."""
    if not keywords:
        click.echo("Please provide at least one keyword with -k/--keywords")
        return
    
    click.echo(f"Searching for keywords: {', '.join(keywords)}")
    click.echo(f"Match mode: {'ALL keywords' if match_all else 'ANY keyword'}")
    
    results = analytics_engine.search_by_keywords(list(keywords), match_all, limit)
    
    if not results:
        click.echo("No videos found matching the criteria.")
        return
    
    click.echo(f"\nFound {len(results)} videos:")
    
    if output_format == 'table':
        click.echo("-" * 100)
        click.echo(f"{'Title':<40} {'Channel':<20} {'Score':<8} {'Keywords':<30}")
        click.echo("-" * 100)
        
        for result in results:
            video = result['video']
            title = video.title[:37] + "..." if len(video.title) > 40 else video.title
            channel = video.channel_name[:17] + "..." if len(video.channel_name) > 20 else video.channel_name
            score = f"{result['relevance_score']:.2f}"
            matched = ", ".join(result['matched_keywords'][:3])
            
            click.echo(f"{title:<40} {channel:<20} {score:<8} {matched:<30}")
    
    elif output_format in ['json', 'csv']:
        export_data = analytics_engine.export_search_results(results, output_format)
        
        if export:
            with open(export, 'w') as f:
                f.write(export_data)
            click.echo(f"Results exported to {export}")
        else:
            click.echo(export_data)

@analytics.command()
@click.option('--start-date', type=click.DateTime(formats=["%Y-%m-%d"]), 
              help='Start date (YYYY-MM-DD)')
@click.option('--end-date', type=click.DateTime(formats=["%Y-%m-%d"]), 
              help='End date (YYYY-MM-DD)')
@click.option('--channel', multiple=True, help='Channel ID or name to filter by')
@click.option('--limit', '-l', default=50, help='Maximum number of results')
def search_dates(start_date, end_date, channel, limit):
    """Search videos by upload date range and channel."""
    
    # Convert datetime to date
    start_date = start_date.date() if start_date else None
    end_date = end_date.date() if end_date else None
    
    if not start_date and not end_date and not channel:
        click.echo("Please provide at least one filter: --start-date, --end-date, or --channel")
        return
    
    click.echo("Searching videos with filters:")
    if start_date:
        click.echo(f"  Start date: {start_date}")
    if end_date:
        click.echo(f"  End date: {end_date}")
    if channel:
        click.echo(f"  Channels: {', '.join(channel)}")
    
    # For now, use first channel if multiple provided
    channel_ids = list(channel) if channel else None
    
    videos = analytics_engine.search_by_date_and_channel(
        start_date=start_date,
        end_date=end_date,
        channel_ids=channel_ids
    )
    
    if not videos:
        click.echo("No videos found matching the criteria.")
        return
    
    click.echo(f"\nFound {len(videos)} videos:")
    click.echo("-" * 80)
    click.echo(f"{'Title':<40} {'Channel':<20} {'Upload Date':<12} {'Duration':<8}")
    click.echo("-" * 80)
    
    for video in videos[:limit]:
        title = video.title[:37] + "..." if len(video.title) > 40 else video.title
        channel_name = video.channel_name[:17] + "..." if len(video.channel_name) > 20 else video.channel_name
        upload_date = video.upload_date.strftime("%Y-%m-%d") if video.upload_date else "Unknown"
        duration = f"{video.duration_seconds//60}:{video.duration_seconds%60:02d}" if video.duration_seconds else "Unknown"
        
        click.echo(f"{title:<40} {channel_name:<20} {upload_date:<12} {duration:<8}")

@analytics.command()
@click.option('--days', '-d', default=30, help='Number of days to look back')
@click.option('--limit', '-l', default=20, help='Number of trending topics to show')
def trending(days, limit):
    """Show trending topics and keywords."""
    click.echo(f"Trending topics from the last {days} days:")
    
    trends = analytics_engine.get_trending_topics(days_back=days, limit=limit)
    
    if not trends:
        click.echo("No trending topics found.")
        return
    
    click.echo("-" * 70)
    click.echo(f"{'Keyword':<25} {'Frequency':<10} {'Videos':<8} {'Trend Score':<12}")
    click.echo("-" * 70)
    
    for trend in trends:
        keyword = trend['keyword'][:22] + "..." if len(trend['keyword']) > 25 else trend['keyword']
        click.echo(f"{keyword:<25} {trend['frequency']:<10} {trend['video_count']:<8} {trend['trend_score']:.2f}")

@analytics.command()
@click.argument('channel_ids', nargs=-1, required=True)
def compare_channels(channel_ids):
    """Compare analytics across multiple channels."""
    if len(channel_ids) < 2:
        click.echo("Please provide at least 2 channel IDs to compare.")
        return
    
    click.echo(f"Comparing {len(channel_ids)} channels...")
    
    comparison = analytics_engine.get_channel_comparison(list(channel_ids))
    
    # Display comparison table
    click.echo("\nChannel Comparison:")
    click.echo("=" * 100)
    
    headers = ['Metric'] + [f'Channel {i+1}' for i in range(len(channel_ids))]
    click.echo(f"{'Metric':<25} " + " ".join(f"{h:<15}" for h in headers[1:]))
    click.echo("-" * 100)
    
    metrics = [
        ('Video Count', 'video_count'),
        ('Completed', 'completed_count'),
        ('Completion Rate', 'completion_rate'),
        ('Avg Duration (min)', lambda x: f"{x['duration_stats']['average_seconds']/60:.1f}"),
        ('Total Duration (hrs)', lambda x: f"{x['duration_stats']['total_seconds']/3600:.1f}"),
    ]
    
    for metric_name, metric_key in metrics:
        row = f"{metric_name:<25}"
        for channel_id in channel_ids:
            if channel_id in comparison:
                if callable(metric_key):
                    value = metric_key(comparison[channel_id])
                else:
                    value = comparison[channel_id].get(metric_key, 0)
                    if metric_name == 'Completion Rate':
                        value = f"{value:.1%}"
                row += f" {str(value):<15}"
            else:
                row += f" {'N/A':<15}"
        click.echo(row)
    
    # Show top keywords for each channel
    click.echo("\nTop Keywords by Channel:")
    for i, channel_id in enumerate(channel_ids):
        if channel_id in comparison:
            click.echo(f"\nChannel {i+1} ({channel_id}):")
            keywords = comparison[channel_id].get('top_keywords', [])[:5]
            for kw in keywords:
                click.echo(f"  • {kw['keyword']} ({kw['frequency']})")

@analytics.command()
@click.option('--channel', multiple=True, help='Filter by channel ID')
@click.option('--start-date', type=click.DateTime(formats=["%Y-%m-%d"]), 
              help='Start date (YYYY-MM-DD)')
@click.option('--end-date', type=click.DateTime(formats=["%Y-%m-%d"]), 
              help='End date (YYYY-MM-DD)')
@click.option('--export', help='Export report to JSON file')
def report(channel, start_date, end_date, export):
    """Generate comprehensive analytics report."""
    click.echo("Generating analytics report...")
    
    # Convert datetime to date
    date_range = None
    if start_date or end_date:
        date_range = (
            start_date.date() if start_date else None,
            end_date.date() if end_date else None
        )
    
    channel_ids = list(channel) if channel else None
    
    report_data = analytics_engine.generate_analytics_report(
        channel_ids=channel_ids,
        date_range=date_range
    )
    
    if export:
        with open(export, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        click.echo(f"Report exported to {export}")
        return
    
    # Display key metrics
    click.echo("\n" + "="*50)
    click.echo("ANALYTICS REPORT")
    click.echo("="*50)
    
    # Overall stats
    overall = report_data.get('overall_stats', {})
    click.echo("\nOverall Statistics:")
    click.echo("-" * 20)
    
    status_dist = overall.get('status_distribution', {})
    for status, count in status_dist.items():
        click.echo(f"  {status.title()}: {count}")
    
    processing = overall.get('processing_time', {})
    if processing.get('average_seconds'):
        click.echo(f"  Avg Processing Time: {processing['average_seconds']:.1f}s")
    
    quality = overall.get('quality_metrics', {})
    if quality.get('average_confidence'):
        click.echo(f"  Avg Confidence: {quality['average_confidence']:.2f}")
    
    # Trending topics
    trending_topics = report_data.get('trending_topics', [])[:10]
    if trending_topics:
        click.echo("\nTrending Topics:")
        click.echo("-" * 15)
        for topic in trending_topics:
            click.echo(f"  • {topic['keyword']} (score: {topic['trend_score']:.1f})")
    
    # Content insights
    insights = report_data.get('content_insights', {})
    if insights:
        click.echo("\nContent Insights:")
        click.echo("-" * 16)
        click.echo(f"  Total Videos: {insights.get('total_videos', 0)}")
        
        lang_dist = insights.get('language_distribution', {})
        if lang_dist:
            click.echo("  Languages: " + ", ".join(f"{lang}({count})" for lang, count in lang_dist.items()))
        
        duration = insights.get('duration_patterns', {})
        if duration.get('average'):
            click.echo(f"  Avg Duration: {duration['average']/60:.1f} minutes")
        
        speakers = insights.get('speaker_patterns', {})
        if speakers.get('average_speakers'):
            click.echo(f"  Avg Speakers: {speakers['average_speakers']:.1f}")

@analytics.command()
@click.option('--min-speakers', type=int, help='Minimum number of speakers')
@click.option('--max-speakers', type=int, help='Maximum number of speakers')
@click.option('--language', multiple=True, help='Filter by language')
@click.option('--min-confidence', type=float, help='Minimum confidence score (0-1)')
@click.option('--limit', '-l', default=20, help='Maximum number of results')
def search_content(min_speakers, max_speakers, language, min_confidence, limit):
    """Search videos by content characteristics."""
    filters = []
    
    if min_speakers is not None:
        filters.append(f"min speakers: {min_speakers}")
    if max_speakers is not None:
        filters.append(f"max speakers: {max_speakers}")
    if language:
        filters.append(f"languages: {', '.join(language)}")
    if min_confidence is not None:
        filters.append(f"min confidence: {min_confidence}")
    
    if not filters:
        click.echo("Please provide at least one content filter.")
        return
    
    click.echo(f"Searching videos with filters: {', '.join(filters)}")
    
    videos = analytics_engine.search_by_content_type(
        min_speakers=min_speakers,
        max_speakers=max_speakers,
        languages=list(language) if language else None,
        min_confidence=min_confidence
    )
    
    if not videos:
        click.echo("No videos found matching the criteria.")
        return
    
    click.echo(f"\nFound {len(videos)} videos:")
    click.echo("-" * 90)
    click.echo(f"{'Title':<35} {'Channel':<15} {'Language':<8} {'Speakers':<8} {'Confidence':<10}")
    click.echo("-" * 90)
    
    for video in videos[:limit]:
        title = video.title[:32] + "..." if len(video.title) > 35 else video.title
        channel = video.channel_name[:12] + "..." if len(video.channel_name) > 15 else video.channel_name
        
        # Get transcription info
        lang = "Unknown"
        speakers = "Unknown"
        confidence = "Unknown"
        
        if video.transcription:
            lang = video.transcription.language or "Unknown"
            speakers = str(video.transcription.speaker_count) if video.transcription.speaker_count else "Unknown"
            confidence = f"{video.transcription.confidence_score:.2f}" if video.transcription.confidence_score else "Unknown"
        
        click.echo(f"{title:<35} {channel:<15} {lang:<8} {speakers:<8} {confidence:<10}")

if __name__ == '__main__':
    analytics()
