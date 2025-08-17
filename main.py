#!/usr/bin/env python3
"""
Video Transcription System - Main CLI Interface

A comprehensive system for automatically downloading and transcribing videos from YouTube channels
using Whisper and WhisperX for speaker identification.
"""

import click
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.utils.logging_config import setup_logging
from src.core.orchestrator import orchestrator
from src.core.optimized_orchestrator import optimized_orchestrator
from src.models.database import db
from src.models.enhanced_database import enhanced_db
from src.core.analytics_engine import analytics_engine
from src.utils.config import config

# Setup logging
logger = setup_logging()

@click.group()
@click.version_option(version='1.0.0')
def cli():
    """Video Transcription System - Automatically transcribe YouTube videos with speaker identification."""
    pass

@cli.command()
@click.argument('channel_url')
def add_channel(channel_url):
    """Add a YouTube channel to monitor for new videos."""
    click.echo(f"Adding channel: {channel_url}")
    
    success = orchestrator.add_channel(channel_url)
    if success:
        click.echo(click.style("✓ Channel added successfully!", fg='green'))
    else:
        click.echo(click.style("✗ Failed to add channel", fg='red'))
        sys.exit(1)

@cli.command()
def list_channels():
    """List all monitored channels."""
    channels = db.get_active_channels()
    
    if not channels:
        click.echo("No channels are currently being monitored.")
        return
    
    click.echo(f"\nMonitored Channels ({len(channels)}):")
    click.echo("-" * 50)
    
    for channel in channels:
        click.echo(f"• {channel.channel_name}")
        click.echo(f"  ID: {channel.channel_id}")
        click.echo(f"  URL: {channel.channel_url}")
        click.echo(f"  Last checked: {channel.last_checked}")
        click.echo()

@cli.command()
def check_videos():
    """Check all channels for new videos (one-time check)."""
    click.echo("Checking for new videos...")
    
    new_videos = orchestrator.check_for_new_videos()
    
    if new_videos:
        click.echo(click.style(f"✓ Found {len(new_videos)} new videos!", fg='green'))
        for video in new_videos:
            click.echo(f"  • {video.title} ({video.channel_name})")
    else:
        click.echo("No new videos found.")

@cli.command()
def process_pending():
    """Process all pending videos (download and transcribe)."""
    click.echo("Processing pending videos...")
    
    with click.progressbar(length=100, label='Processing') as bar:
        results = orchestrator.process_pending_videos()
        bar.update(100)
    
    click.echo(f"\nResults:")
    click.echo(f"  Downloaded: {results['downloaded']}")
    click.echo(f"  Transcribed: {results['transcribed']}")
    click.echo(f"  Failed: {results['failed']}")

@cli.command()
def run_cycle():
    """Run a complete cycle: check for new videos and process them."""
    click.echo("Running full processing cycle...")
    
    results = orchestrator.run_full_cycle()
    
    if 'error' in results:
        click.echo(click.style(f"✗ Error: {results['error']}", fg='red'))
        sys.exit(1)
    
    click.echo(click.style("✓ Cycle completed!", fg='green'))
    click.echo(f"  New videos found: {results['new_videos_found']}")
    click.echo(f"  Downloaded: {results['processing_results']['downloaded']}")
    click.echo(f"  Transcribed: {results['processing_results']['transcribed']}")
    click.echo(f"  Failed: {results['processing_results']['failed']}")
    click.echo(f"  Cycle time: {results['cycle_time_seconds']:.1f} seconds")

@cli.command()
@click.option('--optimized', is_flag=True, help='Use optimized mode with immediate cleanup')
def start_monitoring(optimized):
    """Start continuous monitoring (runs indefinitely)."""
    if optimized:
        click.echo(f"Starting OPTIMIZED continuous monitoring...")
        click.echo("🚀 Optimization features:")
        click.echo("  • Immediate file cleanup after transcription")
        click.echo("  • Audio-only downloads (MP3 @ 128K)")
        click.echo("  • Minimal storage footprint")
        click.echo("  • Smart storage management")
        orchestrator_to_use = optimized_orchestrator
    else:
        click.echo(f"Starting standard continuous monitoring...")
        orchestrator_to_use = orchestrator
    
    click.echo(f"Check interval: {config.check_interval_minutes} minutes")
    click.echo("Press Ctrl+C to stop")
    
    try:
        orchestrator_to_use.start_monitoring()
    except KeyboardInterrupt:
        click.echo("\nMonitoring stopped.")

@cli.command()
def status():
    """Show system status and statistics."""
    status_data = orchestrator.get_system_status()
    
    if 'error' in status_data:
        click.echo(click.style(f"Error getting status: {status_data['error']}", fg='red'))
        return
    
    # System status
    click.echo("System Status:")
    click.echo("-" * 20)
    click.echo(f"Running: {'Yes' if status_data['system']['is_running'] else 'No'}")
    click.echo(f"Last run: {status_data['system']['last_run'] or 'Never'}")
    click.echo(f"Check interval: {status_data['system']['check_interval_minutes']} minutes")
    click.echo()
    
    # Channels
    click.echo("Channels:")
    click.echo("-" * 20)
    click.echo(f"Total: {status_data['channels']['total']}")
    click.echo(f"Active: {status_data['channels']['active']}")
    click.echo()
    
    # Videos
    click.echo("Videos:")
    click.echo("-" * 20)
    click.echo(f"Total: {status_data['videos']['total']}")
    click.echo(f"Pending: {status_data['videos']['pending']}")
    click.echo(f"Completed: {status_data['videos']['completed']}")
    click.echo(f"Failed: {status_data['videos']['failed']}")
    click.echo()
    
    # Processing stats
    stats = status_data['processing_stats']
    click.echo("Processing Statistics:")
    click.echo("-" * 20)
    click.echo(f"Videos discovered: {stats['videos_discovered']}")
    click.echo(f"Videos downloaded: {stats['videos_downloaded']}")
    click.echo(f"Videos transcribed: {stats['videos_transcribed']}")
    click.echo(f"Errors: {stats['errors']}")
    click.echo()
    
    # Storage
    if 'downloads' in status_data['storage']:
        downloads = status_data['storage']['downloads']
        click.echo("Storage:")
        click.echo("-" * 20)
        click.echo(f"Download files: {downloads.get('total_files', 0)}")
        click.echo(f"Download size: {downloads.get('total_size_mb', 0):.1f} MB")
        click.echo(f"Transcriptions: {status_data['storage']['transcriptions'].get('total_transcriptions', 0)}")

@cli.command()
@click.argument('video_url')
@click.option('--optimized', is_flag=True, help='Use optimized mode with immediate cleanup')
def process_video(video_url, optimized):
    """Process a single video immediately."""
    if optimized:
        click.echo(f"Processing video with OPTIMIZATION: {video_url}")
        click.echo("🚀 Using: Audio-only download + Immediate cleanup")
        orchestrator_to_use = optimized_orchestrator
        process_func = orchestrator_to_use.process_single_video_optimized
    else:
        click.echo(f"Processing video: {video_url}")
        orchestrator_to_use = orchestrator
        process_func = orchestrator_to_use.process_single_video
    
    with click.progressbar(length=100, label='Processing') as bar:
        bar.update(25)  # Starting
        result = process_func(video_url)
        bar.update(100)  # Complete
    
    if 'error' in result:
        click.echo(click.style(f"✗ Error: {result['error']}", fg='red'))
        sys.exit(1)
    
    click.echo(click.style("✓ Video processed successfully!", fg='green'))
    click.echo(f"  Title: {result['title']}")
    click.echo(f"  URL: {result['url']}")
    click.echo(f"  Duration: {result['duration_seconds']//60}:{result['duration_seconds']%60:02d}")
    click.echo(f"  Channel: {result['channel_name']}")
    click.echo(f"  Language: {result['language']}")
    click.echo(f"  Confidence: {result['confidence_score']:.2f}")
    
    if optimized and 'processing_time' in result:
        times = result['processing_time']
        click.echo(f"  Download time: {times['download']:.1f}s")
        click.echo(f"  Transcription time: {times['transcription']:.1f}s")
        click.echo(f"  Total time: {times['total']:.1f}s")
        click.echo(click.style("  💾 Audio file automatically cleaned up!", fg='green'))
    
    click.echo(f"  Output: {result['transcription_path']}")

@cli.command()
@click.option('--format', 'output_format', default='json', type=click.Choice(['json', 'table']),
              help='Output format')
def list_videos(output_format):
    """List all videos in the database."""
    with db.get_session() as session:
        videos = session.query(db.Video).order_by(db.Video.discovered_at.desc()).limit(50).all()
    
    if not videos:
        click.echo("No videos found.")
        return
    
    if output_format == 'json':
        video_data = []
        for video in videos:
            video_data.append({
                'video_id': video.video_id,
                'title': video.title,
                'channel': video.channel_name,
                'status': video.status,
                'discovered_at': video.discovered_at.isoformat() if video.discovered_at else None,
                'duration_seconds': video.duration_seconds
            })
        click.echo(json.dumps(video_data, indent=2))
    else:
        click.echo(f"\nRecent Videos ({len(videos)}):")
        click.echo("-" * 80)
        for video in videos:
            status_color = {
                'completed': 'green',
                'failed': 'red',
                'pending': 'yellow',
                'downloading': 'blue',
                'transcribing': 'blue'
            }.get(video.status, 'white')
            
            click.echo(f"• {video.title[:50]}...")
            click.echo(f"  Channel: {video.channel_name}")
            click.echo(f"  Status: {click.style(video.status, fg=status_color)}")
            click.echo(f"  Discovered: {video.discovered_at}")
            click.echo()

@cli.command()
def setup():
    """Initial setup and configuration check."""
    click.echo("Video Transcription System Setup")
    click.echo("=" * 40)
    
    # Check directories
    click.echo("Checking directories...")
    for path_name, path in [
        ("Downloads", config.download_path),
        ("Transcriptions", config.output_path),
        ("Logs", config.log_path)
    ]:
        if path.exists():
            click.echo(f"  ✓ {path_name}: {path}")
        else:
            path.mkdir(parents=True, exist_ok=True)
            click.echo(f"  ✓ Created {path_name}: {path}")
    
    # Check database
    click.echo("\nChecking database...")
    try:
        with db.get_session() as session:
            channel_count = session.query(db.Channel).count()
            video_count = session.query(db.Video).count()
        click.echo(f"  ✓ Database connected")
        click.echo(f"  ✓ Channels: {channel_count}")
        click.echo(f"  ✓ Videos: {video_count}")
    except Exception as e:
        click.echo(f"  ✗ Database error: {e}")
    
    # Show configuration
    click.echo("\nConfiguration:")
    click.echo(f"  Whisper model: {config.whisper_model}")
    click.echo(f"  WhisperX model: {config.whisperx_model}")
    click.echo(f"  Device: {config.device}")
    click.echo(f"  Check interval: {config.check_interval_minutes} minutes")
    click.echo(f"  Max video length: {config.max_video_length_minutes} minutes")
    
    click.echo("\nSetup complete! You can now:")
    click.echo("  1. Add channels: python main.py add-channel <URL>")
    click.echo("  2. Start monitoring: python main.py start-monitoring")
    click.echo("  3. Check status: python main.py status")
    click.echo("  4. Use optimized mode: python main.py start-monitoring --optimized")

# ==================== OPTIMIZED COMMANDS ====================

@cli.command()
def storage_status():
    """Show detailed storage usage and optimization status."""
    click.echo("📊 STORAGE STATUS")
    click.echo("=" * 50)
    
    try:
        # Get optimized system status
        status_data = optimized_orchestrator.get_optimized_system_status()
        
        if 'error' in status_data:
            click.echo(click.style(f"Error: {status_data['error']}", fg='red'))
            return
        
        # Storage optimization info
        storage_opt = status_data.get('storage_optimization', {})
        click.echo("Storage Optimization:")
        click.echo(f"  Mode: {'ENABLED' if storage_opt.get('immediate_cleanup') else 'DISABLED'}")
        click.echo(f"  Audio-only downloads: {'YES' if storage_opt.get('audio_only_downloads') else 'NO'}")
        click.echo(f"  Format: {storage_opt.get('compressed_format', 'Standard')}")
        click.echo(f"  Estimated storage saved: {storage_opt.get('estimated_storage_saved_mb', 0):.1f} MB")
        
        # Current storage usage
        temp_storage = storage_opt.get('current_temp_storage', {})
        if temp_storage and 'total_size_mb' in temp_storage:
            click.echo(f"\nCurrent Temporary Storage:")
            click.echo(f"  Files: {temp_storage.get('total_files', 0)}")
            click.echo(f"  Size: {temp_storage.get('total_size_mb', 0):.1f} MB")
            
            file_types = temp_storage.get('file_types', {})
            if file_types:
                click.echo("  File types:")
                for ext, info in file_types.items():
                    click.echo(f"    {ext}: {info['count']} files ({info['size_mb']:.1f} MB)")
        
        # Transcription storage
        trans_storage = storage_opt.get('transcription_storage', {})
        if trans_storage and 'transcription_files' in trans_storage:
            trans_files = trans_storage['transcription_files']
            click.echo(f"\nTranscription Storage:")
            click.echo(f"  Files: {trans_files.get('count', 0)}")
            click.echo(f"  Size: {trans_files.get('size_mb', 0):.1f} MB")
        
        # Performance stats
        perf = status_data.get('performance', {})
        if perf:
            click.echo(f"\nPerformance:")
            click.echo(f"  Average processing time: {perf.get('average_processing_time', 0):.1f}s per video")
            click.echo(f"  Processing rate: {perf.get('videos_per_hour', 0):.1f} videos/hour")
        
    except Exception as e:
        click.echo(click.style(f"Error getting storage status: {e}", fg='red'))

@cli.command()
@click.option('--force', is_flag=True, help='Force cleanup even if not needed')
def cleanup_storage(force):
    """Clean up temporary storage files."""
    click.echo("🧹 STORAGE CLEANUP")
    click.echo("=" * 30)
    
    if force:
        click.echo("Performing EMERGENCY cleanup of all temporary files...")
        result = optimized_orchestrator.emergency_storage_cleanup()
    else:
        click.echo("Performing smart cleanup of old temporary files...")
        # Use the transcription engine's cleanup
        from src.core.optimized_transcription_engine import optimized_transcription_engine
        optimized_transcription_engine.cleanup_temp_files()
        result = {'cleanup_performed': True, 'message': 'Smart cleanup completed'}
    
    if 'error' in result:
        click.echo(click.style(f"✗ Error: {result['error']}", fg='red'))
    else:
        click.echo(click.style("✓ Cleanup completed!", fg='green'))
        
        if 'downloader_cleanup' in result:
            cleanup_info = result['downloader_cleanup']
            click.echo(f"  Files cleaned: {cleanup_info.get('cleaned_files', 0)}")
            click.echo(f"  Space freed: {cleanup_info.get('freed_mb', 0):.1f} MB")

@cli.command()
@click.option('--optimized', is_flag=True, help='Use optimized processing mode')
def process_pending(optimized):
    """Process all pending videos (download and transcribe)."""
    if optimized:
        click.echo("Processing pending videos with OPTIMIZATION...")
        click.echo("🚀 Features: Immediate cleanup + Audio-only + Compressed format")
        orchestrator_to_use = optimized_orchestrator
        process_func = orchestrator_to_use.process_pending_videos_optimized
    else:
        click.echo("Processing pending videos...")
        orchestrator_to_use = orchestrator
        process_func = orchestrator_to_use.process_pending_videos
    
    with click.progressbar(length=100, label='Processing') as bar:
        results = process_func()
        bar.update(100)
    
    if optimized and 'error' not in results:
        click.echo(f"\n🎉 Optimized Results:")
        click.echo(f"  Total videos: {results['total_videos']}")
        click.echo(f"  Successful: {results['successful']}")
        click.echo(f"  Failed: {results['failed']}")
        click.echo(f"  Success rate: {results['success_rate']:.1%}")
        click.echo(f"  Total time: {results['processing_time']:.1f}s")
        click.echo(f"  Avg time per video: {results['average_time_per_video']:.1f}s")
        click.echo(click.style(f"  💾 Storage saved: ~{results['storage_saved_mb']}MB", fg='green'))
    else:
        click.echo(f"\nResults:")
        click.echo(f"  Downloaded: {results.get('downloaded', 0)}")
        click.echo(f"  Transcribed: {results.get('transcribed', 0)}")
        click.echo(f"  Failed: {results.get('failed', 0)}")

@cli.command()
@click.option('--optimized', is_flag=True, help='Use optimized processing mode')
def run_cycle(optimized):
    """Run a complete cycle: check for new videos and process them."""
    if optimized:
        click.echo("Running OPTIMIZED full processing cycle...")
        orchestrator_to_use = optimized_orchestrator
        cycle_func = orchestrator_to_use.run_optimized_cycle
    else:
        click.echo("Running full processing cycle...")
        orchestrator_to_use = orchestrator
        cycle_func = orchestrator_to_use.run_full_cycle
    
    results = cycle_func()
    
    if 'error' in results:
        click.echo(click.style(f"✗ Error: {results['error']}", fg='red'))
        sys.exit(1)
    
    click.echo(click.style("✓ Cycle completed!", fg='green'))
    click.echo(f"  New videos found: {results['new_videos_found']}")
    
    processing = results['processing_results']
    if optimized:
        click.echo(f"  Processed: {processing['successful']}/{processing['total_videos']} ({processing['success_rate']:.1%})")
        click.echo(f"  Processing time: {processing['processing_time']:.1f}s")
        
        storage_opt = results.get('storage_optimization', {})
        if storage_opt:
            click.echo(f"  💾 Storage saved: ~{storage_opt.get('estimated_storage_saved_mb', 0)}MB")
            click.echo(f"  🧹 Cleanup performed: {'Yes' if storage_opt.get('cleanup_performed') else 'No'}")
    else:
        click.echo(f"  Downloaded: {processing['downloaded']}")
        click.echo(f"  Transcribed: {processing['transcribed']}")
        click.echo(f"  Failed: {processing['failed']}")
    
    click.echo(f"  Cycle time: {results['cycle_time_seconds']:.1f} seconds")

# ==================== ANALYTICS COMMANDS ====================

@cli.group()
def search():
    """Advanced search and analytics commands."""
    pass

@search.command()
@click.option('--keywords', '-k', multiple=True, help='Keywords to search for')
@click.option('--match-all', is_flag=True, help='All keywords must be present (AND logic)')
@click.option('--limit', '-l', default=20, help='Maximum number of results')
@click.option('--export', help='Export results to file')
def keywords(keywords, match_all, limit, export):
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
    
    if export:
        export_data = analytics_engine.export_search_results(results, 'json')
        with open(export, 'w') as f:
            f.write(export_data)
        click.echo(f"Results exported to {export}")

@search.command()
@click.option('--start-date', type=click.DateTime(formats=["%Y-%m-%d"]), 
              help='Start date (YYYY-MM-DD)')
@click.option('--end-date', type=click.DateTime(formats=["%Y-%m-%d"]), 
              help='End date (YYYY-MM-DD)')
@click.option('--channel', help='Channel ID to filter by')
@click.option('--limit', '-l', default=50, help='Maximum number of results')
def dates(start_date, end_date, channel, limit):
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
        click.echo(f"  Channel: {channel}")
    
    channel_ids = [channel] if channel else None
    
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

@cli.command()
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

@cli.command()
@click.argument('channel_ids', nargs=-1, required=True)
def compare(channel_ids):
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

@cli.command()
@click.option('--channel', multiple=True, help='Filter by channel ID')
@click.option('--start-date', type=click.DateTime(formats=["%Y-%m-%d"]), 
              help='Start date (YYYY-MM-DD)')
@click.option('--end-date', type=click.DateTime(formats=["%Y-%m-%d"]), 
              help='End date (YYYY-MM-DD)')
@click.option('--export', help='Export report to JSON file')
def analytics_report(channel, start_date, end_date, export):
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

if __name__ == '__main__':
    cli()
