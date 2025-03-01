# Mucache Player

A local web application for downloading and playing online videos. This application allows you to:
- Download videos from supported online platforms in highest quality
- Cache videos locally for superior playback quality
- Maintain an automatically sorted playlist
- Play videos with loop functionality
- Works on Windows, Linux, and macOS

## Features

- Simple, clean interface
- Automatic video caching in best available quality
- Superior audio playback from cached files
- Alphabetically sorted playlist
- Persistent playlist management
- Video looping support
- Cross-platform compatibility

## Prerequisites

- Python 3.6 or higher
- pip (Python package installer)

## Installation

1. Clone or download this repository
2. Install the required dependency:
```bash
pip install yt-dlp
```

## Usage

1. Run the application:
```bash
python cache.py
```

2. The application will:
   - Create a cache directory in your Downloads folder
   - Start a local web server
   - Open your default web browser to the application interface

3. To add videos:
   - Paste a supported video URL into the input field
   - Click "Download"
   - Wait for download completion
   - Videos are automatically downloaded in highest quality

4. Features:
   - Videos are cached locally for optimal playback
   - Playlist automatically sorts alphabetically
   - Click any video in the playlist to play
   - Toggle video looping with the checkbox
   - Remove videos from playlist with the Remove button
   - Application closes cleanly when browser window is closed

## Cache Location

Videos are stored in:
- Windows: `%USERPROFILE%\Downloads\mucache`
- Linux/macOS: `~/Downloads\mucache`

## Quality Benefits

The application provides superior playback quality because:
- Downloads are always in highest available quality
- Local playback eliminates streaming quality variations
- No re-compression during playback
- Direct file access for optimal audio performance

## Files

- `cache.py`: Main application file
- `manual.html`: User manual with detailed instructions
- `README.md`: This file

## Technical Details

- Built with Python and HTML5
- Uses yt-dlp for high-quality video downloads
- Local server runs on port 8000
- Videos stored in MP4 format
- Playlist data stored in JSON
- Threaded server for better performance
- Heartbeat mechanism for clean shutdown

## Legal Notice

Users of this software are solely responsible for ensuring they have appropriate rights and permissions for any content they download, modify, or redistribute. The software is provided "as is", and the providers of this software assume no liability for any damages arising from its use or misuse. Users must comply with all applicable laws and platform terms of service in their jurisdiction.