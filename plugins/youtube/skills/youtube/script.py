#!/usr/bin/env python3
"""
YouTube Transcribe MCP Server / CLI Tool
Fast YouTube transcription using Deepgram API with YouTube caption fallback

Usage as CLI:
  python server.py --url "https://youtube.com/watch?v=xxx" --output transcript.md
  python server.py --url "..." --timestamps --method captions

Usage as MCP Server:
  python server.py  (no arguments)
"""

import os
import sys
import json
import re
import asyncio
import argparse
import aiohttp
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from urllib.parse import urlparse, parse_qs
# ============================================================================
# CONFIGURATION - Set your API key here
# ============================================================================
DEEPGRAM_API_KEY = "c]$2Jc)]x)_2K}[S0Ek{#Q#8d0t~&0@zs8J_0z@#"  # For high-quality transcription
# ============================================================================

# Fallback to environment variable if not set above
if not DEEPGRAM_API_KEY or DEEPGRAM_API_KEY.startswith("your_"):
    from dotenv import load_dotenv
    root_env = Path(__file__).parent.parent.parent.parent / '.env'
    load_dotenv(root_env)
    DEEPGRAM_API_KEY = os.getenv('DEEPGRAM_API_KEY')
CACHE_DIR = Path(__file__).parent / 'cache'
CACHE_DURATION_DAYS = 30

# Ensure cache directory exists
CACHE_DIR.mkdir(exist_ok=True)

def extract_video_id(url: str) -> Optional[str]:
    """Extract video ID from various YouTube URL formats"""
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)',
        r'youtube\.com\/v\/([^&\n?#]+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    # Try parsing as standard URL
    parsed = urlparse(url)
    if parsed.hostname in ['www.youtube.com', 'youtube.com']:
        params = parse_qs(parsed.query)
        if 'v' in params:
            return params['v'][0]

    return None

def get_cache_path(video_id: str) -> Path:
    """Get cache file path for a video ID"""
    return CACHE_DIR / f"{video_id}.json"

def is_cache_valid(cache_path: Path) -> bool:
    """Check if cache file exists and is still valid"""
    if not cache_path.exists():
        return False

    # Check age of cache
    cache_age = datetime.now() - datetime.fromtimestamp(cache_path.stat().st_mtime)
    return cache_age < timedelta(days=CACHE_DURATION_DAYS)

async def get_youtube_captions(video_id: str) -> Optional[Dict]:
    """Extract captions directly from YouTube"""
    try:
        # Dynamic import to avoid dependency if not installed
        from youtube_transcript_api import YouTubeTranscriptApi

        # Get available transcripts
        transcript_list = YouTubeTranscriptApi().list(video_id)

        # Try to get English transcript (manual first, then auto-generated)
        transcript = None
        is_auto_generated = True

        try:
            # Try manual transcript first
            transcript = transcript_list.find_manually_created_transcript(['en'])
            is_auto_generated = False
        except:
            try:
                # Fall back to auto-generated
                transcript = transcript_list.find_generated_transcript(['en'])
            except:
                # Try any available transcript
                for t in transcript_list:
                    transcript = t
                    is_auto_generated = t.is_generated
                    break

        if not transcript:
            return None

        # Fetch the transcript data
        data = transcript.fetch()

        # Format as continuous text with timestamps
        # Handle both old dict format and new FetchedTranscriptSnippet objects
        def get_text(entry):
            return entry.text if hasattr(entry, 'text') else entry['text']

        def get_start(entry):
            return entry.start if hasattr(entry, 'start') else entry['start']

        full_text = ' '.join([get_text(entry) for entry in data])

        # Also create timestamped version
        timestamped = []
        for entry in data:
            time = str(timedelta(seconds=int(get_start(entry))))
            timestamped.append(f"[{time}] {get_text(entry)}")

        return {
            "text": full_text,
            "timestamped": timestamped,
            "is_auto_generated": is_auto_generated,
            "language": transcript.language_code,
            "source": "youtube_captions"
        }

    except ImportError:
        # youtube-transcript-api not installed
        return None
    except Exception as e:
        print(f"Error getting YouTube captions: {e}", file=sys.stderr)
        return None

async def get_video_metadata(video_id: str) -> Dict:
    """Get video metadata using yt-dlp"""
    try:
        import yt_dlp

        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'skip_download': True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://youtube.com/watch?v={video_id}", download=False)

            return {
                'title': info.get('title', 'Unknown'),
                'channel': info.get('uploader', 'Unknown'),
                'duration': info.get('duration', 0),
                'upload_date': info.get('upload_date', ''),
                'description': info.get('description', ''),
                'view_count': info.get('view_count', 0),
                'url': f"https://youtube.com/watch?v={video_id}"
            }
    except Exception as e:
        print(f"Error getting video metadata: {e}", file=sys.stderr)
        return {
            'title': 'Unknown',
            'channel': 'Unknown',
            'url': f"https://youtube.com/watch?v={video_id}"
        }

async def transcribe_with_deepgram(video_id: str) -> Optional[Dict]:
    """Transcribe using Deepgram API"""
    if not DEEPGRAM_API_KEY:
        return None

    try:
        import yt_dlp
        import tempfile

        # Download audio to temp file
        temp_dir = Path(tempfile.gettempdir())
        audio_path = temp_dir / f"{video_id}.m4a"

        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'format': 'bestaudio/best',
            'outtmpl': str(audio_path),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'm4a',
            }],
        }

        print(f"Downloading audio for {video_id}...", file=sys.stderr)
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([f"https://youtube.com/watch?v={video_id}"])

        # Read audio file
        with open(audio_path, 'rb') as f:
            audio_data = f.read()

        print(f"Sending {len(audio_data)} bytes to Deepgram...", file=sys.stderr)

        # Send to Deepgram with audio data
        headers = {
            'Authorization': f'Token {DEEPGRAM_API_KEY}',
            'Content-Type': 'audio/m4a'
        }

        params = {
            'model': 'nova-2',
            'smart_format': 'true',
            'punctuate': 'true',
            'paragraphs': 'true',
            'utterances': 'true',
            'language': 'en',
            'diarize': 'true'
        }

        async with aiohttp.ClientSession() as session:
            url = 'https://api.deepgram.com/v1/listen?' + '&'.join(f"{k}={v}" for k, v in params.items())
            async with session.post(url, headers=headers, data=audio_data) as response:
                if response.status != 200:
                    error_text = await response.text()
                    print(f"Deepgram API error: {error_text}", file=sys.stderr)
                    return None

                result = await response.json()

                # Clean up temp file
                audio_path.unlink(missing_ok=True)

                # Extract transcript
                transcript = result['results']['channels'][0]['alternatives'][0]['transcript']
                paragraphs = result['results']['channels'][0]['alternatives'][0].get('paragraphs', {})

                # Format with timestamps if available
                timestamped = []
                if 'utterances' in result['results']:
                    for utterance in result['results']['utterances']:
                        start_time = str(timedelta(seconds=int(utterance['start'])))
                        speaker = f"Speaker {utterance.get('speaker', 0)}"
                        text = utterance['transcript']
                        timestamped.append(f"[{start_time}] {speaker}: {text}")

                return {
                    "text": transcript,
                    "timestamped": timestamped,
                    "confidence": result['results']['channels'][0]['alternatives'][0].get('confidence', 0),
                    "duration": result['metadata'].get('duration', 0),
                    "source": "deepgram",
                    "paragraphs": paragraphs
                }

    except Exception as e:
        print(f"Error with Deepgram transcription: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return {"error": str(e), "traceback": traceback.format_exc()}

def format_markdown(transcript_data: Dict, metadata: Dict, include_timestamps: bool = True) -> str:
    """Format transcript data as markdown"""
    # Format upload date
    upload_date = metadata.get('upload_date', '')
    if upload_date and len(upload_date) == 8:
        upload_date = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:]}"

    # Build markdown
    markdown = f"""# {metadata.get('title', 'Untitled')}

**Channel**: {metadata.get('channel', 'Unknown')}
**Date**: {upload_date}
**URL**: {metadata.get('url', '')}
**Duration**: {str(timedelta(seconds=metadata.get('duration', 0)))}
**Views**: {metadata.get('view_count', 0):,}
**Transcribed**: {datetime.now().strftime('%Y-%m-%d')}
**Source**: {transcript_data.get('source', 'unknown')}

---

## Transcript

{transcript_data.get('text', '')}

---

"""

    # Add timestamped version if available and requested
    if include_timestamps and transcript_data.get('timestamped') and len(transcript_data['timestamped']) > 1:
        markdown += f"""## Timestamped Transcript

{chr(10).join(transcript_data['timestamped'])}

---

"""

    # Add metadata footer
    source = transcript_data.get('source', 'unknown')
    if source == 'deepgram':
        markdown += f"*Transcribed using Deepgram API (Nova-2 model)*"
        if 'confidence' in transcript_data:
            markdown += f"  \n*Confidence: {transcript_data['confidence']:.2%}*"
    elif source == 'youtube_captions':
        caption_type = "Auto-generated" if transcript_data.get('is_auto_generated') else "Manual"
        markdown += f"*Extracted from YouTube {caption_type} captions*"

    return markdown


# ============================================================================
# Core transcription function (used by both CLI and MCP)
# ============================================================================

async def transcribe_video(
    url: str,
    force_method: Optional[str] = None,  # "captions", "deepgram", or None for auto
    save_to_knowledge: bool = True,
    include_timestamps: bool = False
) -> dict:
    """
    Transcribe a YouTube video using the fastest available method.

    Args:
        url: YouTube video URL
        force_method: Force specific transcription method
        save_to_knowledge: Whether to save to knowledge base
        include_timestamps: Include timestamped version in response

    Returns:
        Dict with transcript, metadata, and method used
    """

    # Extract video ID
    video_id = extract_video_id(url)
    if not video_id:
        return {
            "success": False,
            "error": "Invalid YouTube URL"
        }

    # Check cache first
    cache_path = get_cache_path(video_id)
    if is_cache_valid(cache_path) and not force_method:
        with open(cache_path, 'r') as f:
            cached = json.load(f)
            return {
                "success": True,
                "cached": True,
                **cached
            }

    # Get video metadata
    metadata = await get_video_metadata(video_id)

    # Try transcription methods in order
    transcript_data = None

    if force_method != "deepgram":
        # Try YouTube captions first (instant)
        transcript_data = await get_youtube_captions(video_id)
        if transcript_data and force_method == "captions":
            pass  # Use captions even if available
        elif not transcript_data and force_method == "captions":
            return {
                "success": False,
                "error": "No YouTube captions available for this video"
            }

    if not transcript_data and force_method != "captions":
        # Try Deepgram API (fast, costs money)
        transcript_data = await transcribe_with_deepgram(video_id)

    # Check for Deepgram error response (returns dict with "error" key on failure)
    if isinstance(transcript_data, dict) and "error" in transcript_data:
        return {
            "success": False,
            "error": f"Deepgram error: {transcript_data['error']}",
            "details": transcript_data.get('traceback')
        }

    if not transcript_data:
        return {
            "success": False,
            "error": "No transcription method available. Please install youtube-transcript-api or configure Deepgram API."
        }

    # Format as markdown
    markdown = format_markdown(transcript_data, metadata, include_timestamps=include_timestamps)

    # Save to knowledge base if requested
    saved_path = None
    if save_to_knowledge:
        # Get project root
        project_root = Path(__file__).parent.parent.parent.parent

        # Create folder name from title
        folder_name = re.sub(r'[^\w\s-]', '', metadata.get('title', 'untitled'))
        folder_name = re.sub(r'[-\s]+', '-', folder_name)[:100]

        # Save to knowledge/_inbox
        save_dir = project_root / 'knowledge' / '_inbox' / folder_name
        save_dir.mkdir(parents=True, exist_ok=True)

        # Save transcript
        transcript_path = save_dir / 'transcript.md'
        with open(transcript_path, 'w', encoding='utf-8') as f:
            f.write(markdown)

        saved_path = str(transcript_path.relative_to(project_root))

    # Prepare response
    response = {
        "success": True,
        "video_id": video_id,
        "title": metadata.get('title'),
        "channel": metadata.get('channel'),
        "duration": metadata.get('duration'),
        "method": transcript_data.get('source'),
        "transcript": transcript_data.get('text'),
        "markdown": markdown,
        "saved_to": saved_path
    }

    # Include timestamps if requested
    if include_timestamps and transcript_data.get('timestamped'):
        response['timestamped'] = transcript_data.get('timestamped')

    # Cache the result
    with open(cache_path, 'w') as f:
        json.dump(response, f, indent=2)

    return response


async def search_transcript(
    url: str,
    query: str,
    context_lines: int = 2
) -> dict:
    """
    Search within a video transcript for specific content.

    Args:
        url: YouTube video URL
        query: Search query
        context_lines: Number of context lines around matches

    Returns:
        Dict with search results and context
    """

    # Get transcript first
    result = await transcribe_video(url, save_to_knowledge=False, include_timestamps=True)

    if not result.get('success'):
        return result

    # Search in transcript
    transcript = result.get('transcript', '')
    timestamped = result.get('timestamped', [])

    # Simple search (could be enhanced with regex or fuzzy matching)
    query_lower = query.lower()
    matches = []

    # Search in timestamped version for better context
    for i, line in enumerate(timestamped):
        if query_lower in line.lower():
            # Get context
            start = max(0, i - context_lines)
            end = min(len(timestamped), i + context_lines + 1)
            context = timestamped[start:end]

            matches.append({
                "line_number": i,
                "match": line,
                "context": context
            })

    return {
        "success": True,
        "query": query,
        "video_title": result.get('title'),
        "matches_found": len(matches),
        "matches": matches[:10]  # Limit to first 10 matches
    }


async def get_video_summary(
    url: str,
    max_length: int = 500
) -> dict:
    """
    Get a summary of a YouTube video.

    Args:
        url: YouTube video URL
        max_length: Maximum summary length in words

    Returns:
        Dict with video summary
    """

    # Get transcript
    result = await transcribe_video(url, save_to_knowledge=False)

    if not result.get('success'):
        return result

    transcript = result.get('transcript', '')

    # Simple extractive summary (first and last parts)
    # In production, you'd use Deepgram's summarization or an LLM
    words = transcript.split()

    if len(words) <= max_length:
        summary = transcript
    else:
        # Take first 40%, middle 20%, and last 40% of max_length
        first_part = ' '.join(words[:int(max_length * 0.4)])
        middle_start = len(words) // 2 - int(max_length * 0.1)
        middle_part = ' '.join(words[middle_start:middle_start + int(max_length * 0.2)])
        last_part = ' '.join(words[-int(max_length * 0.4):])

        summary = f"{first_part}... {middle_part}... {last_part}"

    return {
        "success": True,
        "video_title": result.get('title'),
        "channel": result.get('channel'),
        "duration": result.get('duration'),
        "method": result.get('method'),
        "summary": summary,
        "full_transcript_available": True
    }


async def batch_transcribe(
    urls: List[str],
    force_method: Optional[str] = None
) -> dict:
    """
    Transcribe multiple YouTube videos efficiently.

    Args:
        urls: List of YouTube video URLs
        force_method: Force specific transcription method for all videos

    Returns:
        Dict with results for each video
    """

    results = {
        "success": True,
        "total": len(urls),
        "completed": [],
        "failed": [],
        "cached": 0,
        "methods_used": {}
    }

    for url in urls:
        result = await transcribe_video(url, force_method=force_method)

        if result.get('success'):
            results['completed'].append({
                'url': url,
                'title': result.get('title'),
                'method': result.get('method'),
                'cached': result.get('cached', False)
            })

            if result.get('cached'):
                results['cached'] += 1

            method = result.get('method', 'unknown')
            results['methods_used'][method] = results['methods_used'].get(method, 0) + 1
        else:
            results['failed'].append({
                'url': url,
                'error': result.get('error')
            })

    results['summary'] = {
        'transcribed': len(results['completed']),
        'failed': len(results['failed']),
        'from_cache': results['cached'],
        'methods': results['methods_used']
    }

    return results


async def clear_cache(video_id: Optional[str] = None) -> dict:
    """
    Clear transcript cache.

    Args:
        video_id: Specific video ID to clear, or None to clear all

    Returns:
        Dict with cleared cache info
    """

    if video_id:
        cache_path = get_cache_path(video_id)
        if cache_path.exists():
            cache_path.unlink()
            return {
                "success": True,
                "message": f"Cleared cache for video {video_id}"
            }
        else:
            return {
                "success": False,
                "message": f"No cache found for video {video_id}"
            }
    else:
        # Clear all cache
        count = 0
        for cache_file in CACHE_DIR.glob("*.json"):
            cache_file.unlink()
            count += 1

        return {
            "success": True,
            "message": f"Cleared {count} cached transcripts"
        }


async def check_configuration() -> dict:
    """
    Check current configuration and available transcription methods.

    Returns:
        Dict with configuration status
    """

    # Check available methods
    methods = []

    # Check YouTube captions
    try:
        import youtube_transcript_api
        methods.append({
            "name": "youtube_captions",
            "available": True,
            "speed": "instant",
            "cost": "free",
            "quality": "good (varies)"
        })
    except ImportError:
        methods.append({
            "name": "youtube_captions",
            "available": False,
            "install": "pip install youtube-transcript-api"
        })

    # Check Deepgram
    if DEEPGRAM_API_KEY:
        methods.append({
            "name": "deepgram",
            "available": True,
            "speed": "fast (1-2 min/hour)",
            "cost": "$0.26/hour",
            "quality": "excellent"
        })
    else:
        methods.append({
            "name": "deepgram",
            "available": False,
            "setup": "Add DEEPGRAM_API_KEY to .env file"
        })

    # Check yt-dlp (required for Deepgram)
    try:
        import yt_dlp
        yt_dlp_available = True
    except ImportError:
        yt_dlp_available = False
        if DEEPGRAM_API_KEY:
            methods.append({
                "warning": "yt-dlp required for Deepgram",
                "install": "pip install yt-dlp"
            })

    # Cache status
    cache_files = list(CACHE_DIR.glob("*.json"))
    cache_size = sum(f.stat().st_size for f in cache_files) / 1024 / 1024  # MB

    return {
        "success": True,
        "methods": methods,
        "cache": {
            "enabled": True,
            "location": str(CACHE_DIR),
            "files": len(cache_files),
            "size_mb": round(cache_size, 2),
            "duration_days": CACHE_DURATION_DAYS
        },
        "dependencies": {
            "youtube_transcript_api": any(m["name"] == "youtube_captions" and m.get("available") for m in methods),
            "deepgram": bool(DEEPGRAM_API_KEY),
            "yt_dlp": yt_dlp_available
        },
        "recommendation": "Install youtube-transcript-api for instant free transcripts" if not any(m["name"] == "youtube_captions" and m.get("available") for m in methods) else "All methods configured correctly"
    }


# ============================================================================
# CLI Interface
# ============================================================================

def run_cli():
    """Run the CLI interface"""
    parser = argparse.ArgumentParser(
        description='Transcribe YouTube videos to markdown',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic transcription (outputs to stdout)
  python server.py --url "https://youtube.com/watch?v=xxx"

  # Save to specific file
  python server.py --url "https://youtube.com/watch?v=xxx" --output transcript.md

  # Include timestamps in output
  python server.py --url "https://youtube.com/watch?v=xxx" --timestamps

  # Force specific method
  python server.py --url "https://youtube.com/watch?v=xxx" --method captions
  python server.py --url "https://youtube.com/watch?v=xxx" --method deepgram

  # Check configuration
  python server.py --check-config
        """
    )

    parser.add_argument(
        '--url',
        type=str,
        help='YouTube video URL to transcribe'
    )

    parser.add_argument(
        '--output', '-o',
        type=str,
        help='Output file path for markdown transcript (default: stdout)'
    )

    parser.add_argument(
        '--timestamps',
        action='store_true',
        help='Include timestamped transcript section'
    )

    parser.add_argument(
        '--method',
        type=str,
        choices=['auto', 'captions', 'deepgram'],
        default='auto',
        help='Transcription method: auto (default), captions (YouTube), or deepgram'
    )

    parser.add_argument(
        '--no-cache',
        action='store_true',
        help='Bypass cache and force fresh transcription'
    )

    parser.add_argument(
        '--json',
        action='store_true',
        help='Output as JSON instead of markdown'
    )

    parser.add_argument(
        '--check-config',
        action='store_true',
        help='Check configuration and available methods'
    )

    args = parser.parse_args()

    # Check config mode
    if args.check_config:
        result = asyncio.run(check_configuration())
        print(json.dumps(result, indent=2))
        return

    # Require URL for transcription
    if not args.url:
        parser.print_help()
        sys.exit(1)

    # Map method arg
    force_method = None if args.method == 'auto' else args.method

    # Run transcription
    result = asyncio.run(transcribe_video(
        url=args.url,
        force_method=force_method,
        save_to_knowledge=False,  # CLI mode doesn't auto-save to knowledge base
        include_timestamps=args.timestamps
    ))

    if not result.get('success'):
        print(f"Error: {result.get('error')}", file=sys.stderr)
        if result.get('details'):
            print(f"Details: {result.get('details')}", file=sys.stderr)
        sys.exit(1)

    # Output result
    if args.json:
        output = json.dumps(result, indent=2)
    else:
        output = result.get('markdown', result.get('transcript', ''))

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"Transcript saved to: {output_path}", file=sys.stderr)
        print(f"Title: {result.get('title')}", file=sys.stderr)
        print(f"Method: {result.get('method')}", file=sys.stderr)
    else:
        print(output)


# ============================================================================
# MCP Server Interface
# ============================================================================

def run_mcp_server():
    """Run as MCP server"""
    from mcp.server.fastmcp import FastMCP

    mcp = FastMCP("youtube-transcribe")

    # Register tools with MCP
    @mcp.tool()
    async def mcp_transcribe_video(
        url: str,
        force_method: Optional[str] = None,
        save_to_knowledge: bool = True,
        include_timestamps: bool = False
    ) -> dict:
        """
        Transcribe a YouTube video using the fastest available method.

        Args:
            url: YouTube video URL
            force_method: Force specific transcription method ("captions", "deepgram", or None for auto)
            save_to_knowledge: Whether to save to knowledge base
            include_timestamps: Include timestamped version in response

        Returns:
            Dict with transcript, metadata, and method used
        """
        return await transcribe_video(url, force_method, save_to_knowledge, include_timestamps)

    @mcp.tool()
    async def mcp_search_transcript(
        url: str,
        query: str,
        context_lines: int = 2
    ) -> dict:
        """
        Search within a video transcript for specific content.

        Args:
            url: YouTube video URL
            query: Search query
            context_lines: Number of context lines around matches

        Returns:
            Dict with search results and context
        """
        return await search_transcript(url, query, context_lines)

    @mcp.tool()
    async def mcp_get_video_summary(
        url: str,
        max_length: int = 500
    ) -> dict:
        """
        Get a summary of a YouTube video.

        Args:
            url: YouTube video URL
            max_length: Maximum summary length in words

        Returns:
            Dict with video summary
        """
        return await get_video_summary(url, max_length)

    @mcp.tool()
    async def mcp_batch_transcribe(
        urls: List[str],
        force_method: Optional[str] = None
    ) -> dict:
        """
        Transcribe multiple YouTube videos efficiently.

        Args:
            urls: List of YouTube video URLs
            force_method: Force specific transcription method for all videos

        Returns:
            Dict with results for each video
        """
        return await batch_transcribe(urls, force_method)

    @mcp.tool()
    async def mcp_clear_cache(video_id: Optional[str] = None) -> dict:
        """
        Clear transcript cache.

        Args:
            video_id: Specific video ID to clear, or None to clear all

        Returns:
            Dict with cleared cache info
        """
        return await clear_cache(video_id)

    @mcp.tool()
    async def mcp_check_configuration() -> dict:
        """
        Check current configuration and available transcription methods.

        Returns:
            Dict with configuration status
        """
        return await check_configuration()

    # Run the server
    mcp.run()


# ============================================================================
# Entry Point
# ============================================================================

if __name__ == "__main__":
    # If command line args are provided (beyond script name), run CLI
    # Otherwise, run as MCP server
    if len(sys.argv) > 1:
        run_cli()
    else:
        run_mcp_server()
