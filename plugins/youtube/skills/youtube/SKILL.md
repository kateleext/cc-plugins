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

Deepgram API key is configured at the top of `script.py`.

## Usage

```bash
# Basic transcription (stdout)
python script.py --url "https://youtube.com/watch?v=VIDEO_ID"

# Save to file
python script.py --url "https://youtube.com/watch?v=VIDEO_ID" --output transcript.md

# With timestamps
python script.py --url "https://youtube.com/watch?v=VIDEO_ID" --output transcript.md --timestamps

# Force method
python script.py --url "URL" --method captions   # Free, instant
python script.py --url "URL" --method deepgram   # Paid, high quality

# Check config
python script.py --check-config
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
