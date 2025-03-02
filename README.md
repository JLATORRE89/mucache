# Mucache Player

A local web application for downloading and playing online videos. This application allows you to:
- Download videos from supported online platforms in highest quality
- Cache videos locally for superior playback quality
- Maintain an automatically sorted playlist with filtering options
- Play videos with loop and continuous playback functionality
- Works on Windows, Linux, and macOS

## Features

- Simple, clean interface with tabbed playlist organization
- Automatic video caching in best available quality
- Twitter/X video support with specialized extraction
- Superior audio and video playback from cached files
- Detailed video information with file statistics
- Alphabetically sorted playlist with platform filtering
- Persistent playlist management
- Video looping and continuous playback support
- Show/hide detailed video information
- Direct access to source URLs
- Cross-platform compatibility

## Prerequisites

- Python 3.6 or higher
- pip (Python package installer)

## Installation

1. Clone or download this repository
2. Install the required dependencies:
```bash
pip install yt-dlp requests
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
   - Paste a supported video URL into the input field (YouTube, Twitter/X, etc.)
   - Click "Download"
   - Wait for download completion
   - Videos are automatically downloaded in highest quality

4. Features:
   - Videos are cached locally for optimal playback
   - Filter playlist by platform (All, YouTube, Twitter/X)
   - Click any video in the playlist to play
   - View detailed video information with "Show Details" button
   - Open original source URLs directly from the playlist
   - Toggle video looping with the checkbox
   - Enable continuous playlist playback
   - Remove videos from playlist with the Remove button
   - Application closes cleanly when browser window is closed

## Cache Location

Videos are stored in:
- Windows: `%USERPROFILE%\Downloads\mucache\data`
- Linux/macOS: `~/Downloads/mucache/data`

## Quality Benefits

The application provides superior playback quality because:
- Downloads are always in highest available quality
- Local playback eliminates streaming quality variations
- No re-compression during playback
- Direct file access for optimal audio performance

## Files

- `cache.py`: Main application file
- `player.html`: UI interface and React components
- `manual.html`: User manual with detailed instructions
- `README.md`: This file

## Technical Details

- Built with Python and React
- Uses yt-dlp for high-quality video downloads
- Specialized Twitter/X video extraction
- File metadata API for detailed information
- Local server runs on port 8000
- Videos stored in MP4 format
- Playlist data stored in JSON
- Tailwind CSS for styling
- Threaded server for better performance
- Heartbeat mechanism for clean shutdown
- Comprehensive logging system

## Legal Notice

Users of this software are solely responsible for ensuring they have appropriate rights and permissions for any content they download, modify, or redistribute. The software is provided "as is", and the providers of this software assume no liability for any damages arising from its use or misuse. Users must comply with all applicable laws and platform terms of service in their jurisdiction.