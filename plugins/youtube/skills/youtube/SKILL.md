---
name: "youtube"
description: "Transcribe YouTube videos to markdown. Use when user shares a YouTube URL or asks to transcribe a video. Supports YouTube captions (instant, free) and Deepgram API (high quality)."
---

# YouTube Transcribe

Transcribe YouTube videos to markdown.

## Setup (one-time)

```bash
pip install -r requirements.txt
```

Deepgram API key is configured at the top of the youtube script.

## Usage

```bash
# Basic transcription (stdout)
youtube --url "https://youtube.com/watch?v=VIDEO_ID"

# Save to file
youtube --url "https://youtube.com/watch?v=VIDEO_ID" --output transcript.md

# With timestamps
youtube --url "https://youtube.com/watch?v=VIDEO_ID" --output transcript.md --timestamps

# Force method
youtube --url "URL" --method captions   # Free, instant
youtube --url "URL" --method deepgram   # Paid, high quality

# Check config
youtube --check-config
```

## Options

| Option | Description |
|--------|-------------|
| `--url` | YouTube video URL (required) |
| `--output` | Save to file instead of stdout |
| `--timestamps` | Include timestamped transcript |
| `--method` | `auto`, `captions`, or `deepgram` |
| `--json` | Output as JSON |
| `--check-config` | Check available methods |

## Methods

| Method | Cost | Quality | Speed |
|--------|------|---------|-------|
| `captions` | Free | Varies | Instant |
| `deepgram` | ~$0.26/hr | High | Minutes |
