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
from src.models.database import db
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
def start_monitoring():
    """Start continuous monitoring (runs indefinitely)."""
    click.echo(f"Starting continuous monitoring...")
    click.echo(f"Check interval: {config.check_interval_minutes} minutes")
    click.echo("Press Ctrl+C to stop")
    
    try:
        orchestrator.start_monitoring()
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
def process_video(video_url):
    """Process a single video immediately."""
    click.echo(f"Processing video: {video_url}")
    
    with click.progressbar(length=100, label='Processing') as bar:
        bar.update(25)  # Starting
        result = orchestrator.process_single_video(video_url)
        bar.update(100)  # Complete
    
    if 'error' in result:
        click.echo(click.style(f"✗ Error: {result['error']}", fg='red'))
        sys.exit(1)
    
    click.echo(click.style("✓ Video processed successfully!", fg='green'))
    click.echo(f"  Title: {result['title']}")
    click.echo(f"  Language: {result['language']}")
    click.echo(f"  Confidence: {result['confidence_score']:.2f}")
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

if __name__ == '__main__':
    cli()
