# Mucache Player

A local web application for downloading and playing online videos, plus archiving webpages for research and documentation. This application allows you to:
- Download videos from supported online platforms in highest quality
- Archive entire webpages as MHTML files with full content preservation
- Cache all content locally for superior playback quality and offline access
- Maintain organized playlists with unified search across videos and webpages
- Play videos with loop and continuous playback functionality
- Generate academic citations for both videos and archived webpages
- Works on Windows, Linux, and macOS

## Features

### Content Archiving
- **Video Downloads**: Support for YouTube, Twitter/X, Reddit, CNN, C-SPAN, Archive.org, and generic HTML5 videos
- **Webpage Archiving**: Complete webpage preservation as MHTML files with full content and metadata
- **Unified Storage**: Organized file system with separate directories for videos and webpages
- **Automatic Metadata**: Extraction of titles, dates, file sizes, and platform/domain information

### Search & Organization
- **Universal Search**: Search across both videos and archived webpages simultaneously
- **Smart Filtering**: Platform-based filtering for videos, domain-based filtering for webpages
- **Advanced Sorting**: Sort by date, title, platform/domain, or file size in ascending/descending order
- **Tab Interface**: Switch between Videos and Articles/Webpages views with item counts
- **Real-time Search**: Instant results with type indicators for videos vs. articles

### Playback & Access
- **Superior Video Playback**: High-quality local playback from cached files
- **Archived Content Access**: View preserved webpages with complete formatting and resources
- **Source Access**: Direct links to original videos and webpages
- **Continuous Playback**: Loop and continuous playback support for videos

### Research & Documentation
- **Academic Citations**: Generate properly formatted citations (APA, MLA, Chicago, Harvard, IEEE, Vancouver, BibTeX)
- **Evidence Reports**: Court-admissible documentation for legal and research purposes
- **Comprehensive Metadata**: Detailed information for both videos and webpages
- **Cross-platform Compatibility**: Works on Windows, Linux, and macOS

### Security & Privacy
- **Secure Content Storage**: Optional encryption for sensitive videos and webpages
- **Separate Encrypted Directory**: Isolated storage to protect sensitive content from corruption
- **Session-Only Passwords**: Encryption passwords are never saved or logged
- **Content Labeling**: Encrypted content is clearly marked as "🔒 Sensitive" in search results
- **Advanced Settings**: Configurable download quality and security options

## Prerequisites

- Python 3.6 or higher
- pip (Python package installer)

## Installation

1. Clone or download this repository
2. Install the required dependencies:
```bash
pip install yt-dlp requests
```

3. (Optional) For enhanced functionality, install additional dependencies:
```bash
# For generic HTML5 video support
pip install beautifulsoup4

# For webpage archiving (MHTML preservation)
pip install playwright
playwright install chromium
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
   - Paste a supported video URL into the input field (YouTube, Twitter/X, Reddit, CNN, C-SPAN, etc.)
   - Click "Download"
   - Wait for download completion
   - Videos are automatically downloaded in highest quality

4. Features:
   - Videos are cached locally for optimal playback
   - Filter playlist by platform (All, YouTube, Twitter/X, Reddit, CNN, C-SPAN, Archive.org)
   - Click any video in the playlist to play
   - View detailed video information with "Show Details" button
   - Open original source URLs directly from the playlist
   - Toggle video looping with the checkbox
   - Enable continuous playlist playback
   - Remove videos from playlist with the Remove button
   - Application closes cleanly when browser window is closed

5. Advanced Settings:
   - Access advanced options by clicking the "Advanced Settings" button
   - Configure download quality preferences for videos
   - Set up optional encryption for sensitive content
   - Encrypted content is stored in a separate directory for security
   - All encrypted content appears with "🔒 Sensitive" labels in search results

## Cache Location

Videos and webpages are stored in:
- **Regular Content**:
  - Windows: `%USERPROFILE%\Downloads\mucache\data`
  - Linux/macOS: `~/Downloads/mucache/data`
- **Encrypted Content** (when encryption is enabled):
  - Windows: `%USERPROFILE%\Downloads\mucache\data_encrypted`
  - Linux/macOS: `~/Downloads/mucache/data_encrypted`

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
- Reddit video support with automatic post ID detection
- CNN video support with HLS/DASH stream handling
- C-SPAN video support with JWPlayer stream extraction
- File metadata API for detailed information
- Local server runs on port 8000
- Videos stored in MP4 format
- Playlist data stored in JSON
- Tailwind CSS for styling
- Threaded server for better performance
- Heartbeat mechanism for clean shutdown
- Comprehensive logging system

## Supported Platforms

The application supports downloading videos from:

- **YouTube**: Full video downloads with quality options
  - Example: `https://www.youtube.com/watch?v=dQw4w9WgXcQ`
- **Twitter/X**: Native video extraction from tweets
  - Example: `https://twitter.com/username/status/1234567890`
- **Reddit**: Video posts from any subreddit
  - Example: `https://www.reddit.com/r/videos/comments/abc123/example_video_post/`
- **CNN**: News videos and segments from CNN.com
  - Example: `https://www.cnn.com/videos/politics/2024/01/01/example-news-segment.cnn`
- **C-SPAN**: Congressional proceedings and political events
  - Example: `https://www.c-span.org/video/?123456-1/example-hearing`
- **Archive.org**: Historical video content with enhanced metadata
  - Example: `https://archive.org/details/example_video`
- **Generic HTML5 Videos**: Direct video downloads from websites with HTML5 `<video>` tags
  - Automatically attempts HTML5 fallback when yt-dlp extraction fails
  - Supports direct media files (`.mp4`, `.webm`, `.ogg`, `.avi`, `.mov`, `.mkv`, `.m4v`)
  - Excludes blob URLs (which require yt-dlp extractors)
  - Example: `https://example.com/page-with-video.html` (containing `<video src="video.mp4">`)

## Usage Examples

### Unified Search & Organization

**Cross-Media Search Examples:**
- Search **"CNN"** → Returns both CNN videos and archived CNN articles
- Search **"climate change"** → Finds videos and webpages containing this phrase
- Search **"youtube.com"** → Shows all YouTube videos in your collection
- Search **"nytimes.com"** → Displays archived New York Times articles

**Sorting Examples:**
- **Date Added (Newest → Oldest)** → Most recently downloaded videos and archived webpages first
- **Platform/Domain (A → Z)** → Groups CNN videos with cnn.com articles, YouTube videos together, etc.
- **File Size (Largest → Smallest)** → Useful for finding high-quality videos or comprehensive webpage archives

**Workflow Examples:**
1. **Research Project**: Archive both video interviews and news articles about a topic, then search across all content
2. **Content Curation**: Download videos from multiple platforms, archive related articles, organize by date or topic
3. **Documentation**: Save video evidence alongside supporting webpage documentation with proper citations

### Academic & Professional Use

**Citation Generation:**
- Download a research video → Generate APA/MLA citations automatically
- Archive a news article → Create proper website citations with access dates
- Mixed content research → Get consistent citation formatting across media types

**Evidence Collection:**
- Legal cases: Preserve video evidence with webpage documentation
- Academic research: Maintain complete citation trails for both video and text sources
- Journalism: Archive source materials with automatic metadata preservation

### Security & Sensitive Content

**Encryption Setup:**
- Enable encryption for sensitive research materials through Advanced Settings
- Set a strong password for your encrypted directory (not saved by the application)
- All encrypted content is automatically isolated from regular content
- Search across both encrypted and regular content with clear "🔒 Sensitive" labeling

**Security Workflow:**
1. **Research Sensitive Topics**: Use encryption for controversial or sensitive subject matter
2. **Legal Documentation**: Protect confidential evidence with encrypted storage
3. **Academic Work**: Secure preliminary research and unpublished materials
4. **Mixed Collections**: Maintain both public and sensitive content with unified search

## Legal Notice

Users of this software are solely responsible for ensuring they have appropriate rights and permissions for any content they download, modify, or redistribute. The software is provided "as is", and the providers of this software assume no liability for any damages arising from its use or misuse. Users must comply with all applicable laws and platform terms of service in their jurisdiction.