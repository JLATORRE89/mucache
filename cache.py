# cache.py - A module for managing video downloads, caching, and metadata handling
import socketserver
import webbrowser
import json
import urllib.parse
import yt_dlp
import os
import threading
import logging
import sys
import datetime
import re
import requests
import subprocess
import shutil
import http.server
from pathlib import Path
import traceback

# Debug mode flag - set to True to show all messages including heartbeat
DEBUG_MODE = False

# Import our new modules with error handling
try:
    from evidence_generator import EvidenceGenerator
    from citation_generator import CitationGenerator
    EVIDENCE_CITATION_AVAILABLE = True
except ImportError as e:
    if DEBUG_MODE:
        print(f"Warning: Evidence/Citation generators not available: {e}")
    EvidenceGenerator = None
    CitationGenerator = None
    EVIDENCE_CITATION_AVAILABLE = False

def setup_logging(cache_dir):
    """Set up logging to redirect output to log files with error handling."""
    try:
        logs_dir = cache_dir / "logs"
        logs_dir.mkdir(exist_ok=True)
        
        logger = logging.getLogger('app')
        # Clear any existing handlers
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
            
        logger.setLevel(logging.INFO)
        
        # Add console handler for immediate feedback (but filter what shows)
        console_handler = logging.StreamHandler(sys.stdout)
        console_formatter = logging.Formatter('%(message)s')
        console_handler.setFormatter(console_formatter)
        
        # Only show console output in debug mode or for errors
        if DEBUG_MODE:
            console_handler.setLevel(logging.INFO)
        else:
            console_handler.setLevel(logging.ERROR)
        
        logger.addHandler(console_handler)
        
        # Add file handler (detailed logging - always capture everything)
        try:
            file_handler = logging.FileHandler(logs_dir / 'app.log', encoding='utf-8')
            file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            file_handler.setLevel(logging.INFO)  # File gets everything
            logger.addHandler(file_handler)
        except Exception as e:
            if DEBUG_MODE:
                print(f"Warning: Could not create log file: {e}")
        
        # Log detailed startup info 
        logger.info("=== Application Starting ===")
        logger.info(f"Cache directory: {cache_dir}")
        logger.info(f"Python version: {sys.version}")
        
        return logger
    except Exception as e:
        print(f"Critical error setting up logging: {e}")
        traceback.print_exc()
        # Return a basic logger
        logger = logging.getLogger('app')
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        logger.addHandler(handler)
        return logger

def safe_log(logger, level, message, console_only=False):
    """Log messages safely, handling non-ASCII characters with console control."""
    if logger is None:
        if DEBUG_MODE or level in ['error', 'critical']:
            print(f"{level.upper()}: {message}")
        return
        
    try:
        # Always log to file (via the logger)
        if level == 'info': 
            logger.info(message)
        elif level == 'warning': 
            logger.warning(message)
        elif level == 'error': 
            logger.error(message)
        elif level == 'critical': 
            logger.critical(message)
        
        # Console output control for special status messages
        if console_only and not DEBUG_MODE:
            # For clean status messages, print directly (bypass logger)
            print(message)
            
    except UnicodeEncodeError:
        # Sanitize the message
        safe_message = "".join(c if ord(c) < 128 else '?' for c in str(message))
        try:
            if level == 'info': 
                logger.info(safe_message)
            elif level == 'warning': 
                logger.warning(safe_message)
            elif level == 'error': 
                logger.error(safe_message)
            elif level == 'critical': 
                logger.critical(safe_message)
        except Exception:
            if DEBUG_MODE or level in ['error', 'critical']:
                print(f"{level.upper()}: {safe_message}")
    except Exception as e:
        if DEBUG_MODE:
            print(f"Logging error: {e}")

def console_status(message):
    """Display status messages on console only (not in log files)."""
    print(message)

def sanitize_filename(filename):
    """Replace special characters with spaces for Windows compatibility."""
    try:
        # Replace non-ASCII characters with spaces
        safe_name = ""
        for c in filename:
            if ord(c) < 128:
                safe_name += c
            else:
                safe_name += " "
        
        # Replace Windows invalid characters including forward slashes
        for char in '<>:"|?*\\/':
            safe_name = safe_name.replace(char, " ")
        
        # Replace parentheses that can cause issues
        safe_name = safe_name.replace('(', ' ').replace(')', ' ')
        
        # Collapse multiple spaces
        while "  " in safe_name:
            safe_name = safe_name.replace("  ", " ")
        
        return safe_name.strip()
    except Exception as e:
        if DEBUG_MODE:
            print(f"Error sanitizing filename: {e}")
        return "sanitized_filename"

def check_ffmpeg_available():
    """Check if FFmpeg is available on the system."""
    try:
        subprocess.run(['ffmpeg', '-version'], 
                      stdout=subprocess.DEVNULL, 
                      stderr=subprocess.DEVNULL, 
                      check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False
    except Exception as e:
        if DEBUG_MODE:
            print(f"Error checking FFmpeg: {e}")
        return False

def get_quality_preference():
    """Get quality preference from settings file or return default."""
    try:
        settings_file = Path.home() / "Downloads" / "mucache" / "data" / "settings.json"
        if settings_file.exists():
            with open(settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                return settings.get('quality_preference', 'reliable')
    except Exception as e:
        if DEBUG_MODE:
            print(f"Error reading quality preference: {e}")
    return 'reliable'  # Default to reliable (format 18)

def save_quality_preference(preference):
    """Save quality preference to settings file."""
    try:
        settings_file = Path.home() / "Downloads" / "mucache" / "data" / "settings.json"
        settings_file.parent.mkdir(parents=True, exist_ok=True)
        
        settings = {}
        if settings_file.exists():
            try:
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
            except Exception as e:
                if DEBUG_MODE:
                    print(f"Warning: Could not read existing settings: {e}")
        
        settings['quality_preference'] = preference
        with open(settings_file, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2)
        return True
    except Exception as e:
        if DEBUG_MODE:
            print(f"Error saving settings: {e}")
        return False

class FFmpegPlugin:
    """Optional FFmpeg plugin for high-quality downloads with audio/video merging."""
    
    def __init__(self, logger=None):
        self.logger = logger
        try:
            self.available = check_ffmpeg_available()
            if logger and DEBUG_MODE:
                status = "available" if self.available else "not available"
                safe_log(logger, 'info', f"FFmpeg plugin: {status}")
        except Exception as e:
            self.available = False
            if logger:
                safe_log(logger, 'error', f"Error initializing FFmpeg plugin: {e}")
    
    def get_high_quality_formats(self):
        """Get format options when FFmpeg is available."""
        return [
            'best[height<=1080][ext=mp4]+best[ext=m4a]/best[height<=1080][ext=mp4]',  # 1080p with audio merge
            'best[height<=720][ext=mp4]+best[ext=m4a]/best[height<=720][ext=mp4]',   # 720p with audio merge
            'best[height<=480][ext=mp4]+best[ext=m4a]/best[height<=480][ext=mp4]',   # 480p with audio merge
            'best[ext=mp4]',  # Best MP4 format (may require merging)
        ]
    
    def get_ytdl_options(self, base_options):
        """Get yt-dlp options when FFmpeg is available."""
        try:
            if self.available:
                base_options.update({
                    'merge_output_format': 'mp4',
                    'postprocessors': [{
                        'key': 'FFmpegVideoConvertor',
                        'preferedformat': 'mp4',
                    }]
                })
        except Exception as e:
            if self.logger:
                safe_log(self.logger, 'error', f"Error setting FFmpeg options: {e}")
        return base_options

def check_available_formats(url, logger=None):
    """Check what formats are available for a given URL."""
    try:
        with yt_dlp.YoutubeDL({
            'quiet': True,
            'no_warnings': True,
            'listformats': True
        }) as ydl:
            info = ydl.extract_info(url, download=False)
            
            if 'formats' in info:
                available_formats = []
                for fmt in info['formats']:
                    format_info = {
                        'format_id': fmt.get('format_id'),
                        'ext': fmt.get('ext'),
                        'resolution': fmt.get('resolution', 'audio only'),
                        'filesize': fmt.get('filesize'),
                        'vcodec': fmt.get('vcodec', 'none'),
                        'acodec': fmt.get('acodec', 'none')
                    }
                    available_formats.append(format_info)
                
                if logger and DEBUG_MODE:
                    safe_log(logger, 'info', f"Available formats for {url}:")
                    for fmt in available_formats[:5]:  # Log first 5 formats
                        safe_log(logger, 'info', f"  {fmt}")
                
                return available_formats
            
    except Exception as e:
        if logger and DEBUG_MODE: 
            safe_log(logger, 'error', f"Error checking formats: {str(e)}")
        return []

def get_format_options(quality_preference, ffmpeg_plugin):
    """Get format options based on quality preference and FFmpeg availability."""
    try:
        if quality_preference == 'high' and ffmpeg_plugin.available:
            # High quality with FFmpeg
            formats = ffmpeg_plugin.get_high_quality_formats()
            formats.extend([
                '18',  # Fallback to reliable 360p
                'worst[ext=mp4]',
                'best'
            ])
            return formats
        
        elif quality_preference == 'medium':
            # Medium quality - try some higher formats without requiring FFmpeg
            return [
                '22',  # 720p MP4 (if available as combined)
                '18',  # 360p MP4 (reliable)
                'best[height<=720][ext=mp4]',  # 720p MP4 video-only
                'best[height<=480][ext=mp4]',  # 480p MP4 video-only
                'worst[ext=mp4]',
                'best'
            ]
        
        else:  # 'reliable' or default
            # Reliable quality - prioritize formats that always work
            return [
                '18',  # 360p MP4 (most reliable)
                'worst[ext=mp4][height>=360]',  # Lowest quality MP4 that's at least 360p
                'best[height<=480][ext=mp4]',  # 480p fallback
                'worst[ext=mp4]',
                'best'
            ]
    except Exception as e:
        if DEBUG_MODE:
            print(f"Error getting format options: {e}")
        return ['18', 'worst', 'best']  # Safe fallback

class VideoManager:
    def __init__(self, cache_dir):
        try:
            self.cache_dir = cache_dir
            self.playlist_file = cache_dir / 'playlist.json'
            self.redownload_file = cache_dir / 'redownload_queue.json'
            
            # Load playlist with error handling
            self.videos = {}
            if self.playlist_file.exists():
                try:
                    with open(self.playlist_file, 'r', encoding='utf-8') as f:
                        self.videos = json.load(f)
                except Exception as e:
                    if DEBUG_MODE:
                        print(f"Warning: Could not load playlist: {e}")
                    self.videos = {}
            
            # Load redownload queue with error handling
            self.redownload_queue = {}
            if self.redownload_file.exists():
                try:
                    with open(self.redownload_file, 'r', encoding='utf-8') as f:
                        self.redownload_queue = json.load(f)
                except Exception as e:
                    if DEBUG_MODE:
                        print(f"Warning: Could not load redownload queue: {e}")
                    self.redownload_queue = {}
        except Exception as e:
            print(f"Critical error initializing VideoManager: {e}")
            traceback.print_exc()
            self.videos = {}
            self.redownload_queue = {}

    def add_video(self, url, title, filename):
        try:
            self.videos[url] = {'title': title, 'filename': filename}
            with open(self.playlist_file, 'w', encoding='utf-8') as f:
                json.dump(self.videos, f, indent=2, ensure_ascii=False)
        except Exception as e:
            if DEBUG_MODE:
                print(f"Error adding video to playlist: {e}")

    def remove_video(self, url, logger=None):
        """Remove a video from the playlist and try to delete the file."""
        try:
            if url in self.videos:
                filename = self.videos[url]['filename']
                # Remove from playlist first
                video_info = self.videos[url].copy()
                del self.videos[url]
                
                try:
                    with open(self.playlist_file, 'w', encoding='utf-8') as f:
                        json.dump(self.videos, f, indent=2, ensure_ascii=False)
                except Exception as e:
                    if logger: safe_log(logger, 'error', f"Error saving playlist: {e}")
                
                # Try to delete file with both original and sanitized names
                file_paths = [
                    self.cache_dir / filename,
                    self.cache_dir / sanitize_filename(filename)
                ]
                
                deleted = False
                for file_path in file_paths:
                    try:
                        if file_path.exists():
                            if logger and DEBUG_MODE: 
                                safe_log(logger, 'info', f"Attempting to delete: {file_path}")
                            file_path.unlink()
                            deleted = True
                            if logger and DEBUG_MODE: 
                                safe_log(logger, 'info', f"Successfully deleted: {file_path}")
                            break
                    except Exception as e:
                        if logger: safe_log(logger, 'error', f"Error deleting file {file_path}: {str(e)}")
                
                if not deleted and logger and DEBUG_MODE:
                    safe_log(logger, 'warning', f"Could not delete any version of the file: {filename}")
                
                return True
            return False
        except Exception as e:
            if logger: safe_log(logger, 'error', f"Error in remove_video: {e}")
            return False

    def add_to_redownload_queue(self, url, title, original_filename, logger=None):
        try:
            self.redownload_queue[url] = {
                'title': title, 
                'original_filename': original_filename,
                'timestamp': datetime.datetime.now().isoformat()
            }
            if logger and DEBUG_MODE: 
                safe_log(logger, 'info', f"Added to redownload queue: {title}")
            with open(self.redownload_file, 'w', encoding='utf-8') as f:
                json.dump(self.redownload_queue, f, indent=2, ensure_ascii=False)
        except Exception as e:
            if logger: safe_log(logger, 'error', f"Error adding to redownload queue: {e}")

    def get_redownload_queue(self):
        return self.redownload_queue

    def remove_from_redownload_queue(self, url):
        try:
            if url in self.redownload_queue:
                del self.redownload_queue[url]
                with open(self.redownload_file, 'w', encoding='utf-8') as f:
                    json.dump(self.redownload_queue, f, indent=2, ensure_ascii=False)
                return True
            return False
        except Exception as e:
            if DEBUG_MODE:
                print(f"Error removing from redownload queue: {e}")
            return False

    def repair_playlist(self, logger=None):
        """Check playlist integrity and fix filename mismatches."""
        try:
            repaired = False
            for url, video_data in list(self.videos.items()):
                filename = video_data['filename']
                file_path = self.cache_dir / filename
                
                # If file doesn't exist, try to find it with sanitized name
                if not file_path.exists():
                    # Try sanitized version
                    sanitized_filename = sanitize_filename(filename)
                    sanitized_path = self.cache_dir / sanitized_filename
                    
                    if sanitized_path.exists():
                        # Update playlist with correct filename
                        self.videos[url]['filename'] = sanitized_filename
                        repaired = True
                        if logger:
                            safe_log(logger, 'info', f"Repaired playlist entry: {filename} -> {sanitized_filename}")
                    else:
                        # Try to find similar files
                        base_name = filename.rsplit('.', 1)[0] if '.' in filename else filename
                        sanitized_base = sanitize_filename(base_name)
                        
                        for existing_file in self.cache_dir.iterdir():
                            if existing_file.is_file() and existing_file.suffix in ['.mp4', '.webm', '.avi']:
                                existing_base = existing_file.stem
                                if (sanitized_base.lower() in existing_base.lower() or 
                                    existing_base.lower() in sanitized_base.lower() or
                                    base_name.lower() in existing_base.lower()):
                                    self.videos[url]['filename'] = existing_file.name
                                    repaired = True
                                    if logger:
                                        safe_log(logger, 'info', f"Repaired playlist entry: {filename} -> {existing_file.name}")
                                    break
            
            if repaired:
                # Save the repaired playlist
                with open(self.playlist_file, 'w', encoding='utf-8') as f:
                    json.dump(self.videos, f, indent=2, ensure_ascii=False)
                if logger:
                    safe_log(logger, 'info', "Playlist repaired and saved")
                    
        except Exception as e:
            if logger:
                safe_log(logger, 'error', f"Error repairing playlist: {e}")

    def get_sorted_videos(self):
        try:
            return sorted(
                [{'url': url, **data} for url, data in self.videos.items()],
                key=lambda x: x['title'].lower()
            )
        except Exception as e:
            if DEBUG_MODE:
                print(f"Error sorting videos: {e}")
            return []

def download_twitter_video(url, cache_dir, manager, logger=None):
    """Download Twitter/X videos."""
    try:
        if logger: safe_log(logger, 'info', f"Starting Twitter/X video download: {url}")
        
        # Extract tweet ID
        match = re.search(r'status/(\d+)', url)
        if not match:
            if logger: safe_log(logger, 'error', f"Could not extract tweet ID from URL: {url}")
            return None, False
            
        tweet_id = match.group(1)
        safe_title = f"X_Video_{tweet_id}"
        safe_filename = f"{safe_title}.mp4"
        file_path = cache_dir / safe_filename
        
        # Normalize URL
        twitter_url = url.replace("x.com", "twitter.com") if "x.com" in url else url
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        
        # Get the tweet page
        response = requests.get(twitter_url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            html = response.text
            
            # Look for video URLs
            video_patterns = [
                r'(https://video\.twimg\.com/amplify_video/\d+/vid/[^"\'&?]+\.mp4[^"\'\s]*)',
                r'(https://video\.twimg\.com/ext_tw_video/\d+/[^"\'&?]+\.mp4[^"\'\s]*)',
                r'(https://video\.twimg\.com/tweet_video/[^"\'&?]+\.mp4[^"\'\s]*)',
                r'(https://video\.twimg\.com/[^"\'&?]+\.mp4[^"\'\s]*)'
            ]
            
            for pattern in video_patterns:
                matches = re.findall(pattern, html)
                if matches:
                    video_url = matches[0]
                    if logger and DEBUG_MODE: 
                        safe_log(logger, 'info', f"Found video URL: {video_url}")
                    
                    video_response = requests.get(video_url, stream=True, timeout=60)
                    if video_response.status_code == 200:
                        with open(file_path, 'wb') as f:
                            for chunk in video_response.iter_content(chunk_size=8192):
                                f.write(chunk)
                        
                        if file_path.exists() and file_path.stat().st_size > 10000:
                            manager.add_video(url, safe_title, safe_filename)
                            if logger: safe_log(logger, 'info', f"Twitter video downloaded successfully: {safe_filename}")
                            return safe_filename, False
        
        if logger: safe_log(logger, 'error', "Twitter video download failed")
        return None, False
    
    except Exception as e:
        if logger: safe_log(logger, 'error', f"Twitter download error: {str(e)}")
        return None, False

def download_archive_video(url, cache_dir, manager, logger=None):
    """Download videos from archive.org with enhanced metadata capture."""
    try:
        if logger and DEBUG_MODE: 
            safe_log(logger, 'info', f"Processing archive.org URL: {url}")
        
        # Archive.org URLs can be in various formats:
        # https://archive.org/details/VideoName
        # https://archive.org/embed/VideoName
        # Extract the item identifier
        
        item_match = re.search(r'archive\.org/(?:details|embed)/([^/?]+)', url)
        if not item_match:
            if logger: safe_log(logger, 'error', f"Could not extract item ID from archive.org URL: {url}")
            return None, False
            
        item_id = item_match.group(1)
        
        # Get comprehensive metadata from archive.org API
        metadata_url = f"https://archive.org/metadata/{item_id}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        
        enhanced_metadata = {}
        
        try:
            metadata_response = requests.get(metadata_url, headers=headers, timeout=15)
            if metadata_response.status_code != 200:
                if logger: safe_log(logger, 'error', f"Failed to get metadata for {item_id}")
                return None, False
                
            metadata = metadata_response.json()
            meta_info = metadata.get('metadata', {})
            
            # Extract comprehensive metadata
            title = meta_info.get('title', item_id)
            safe_title = sanitize_filename(title)
            
            # Capture additional metadata
            enhanced_metadata = {
                'title': title,
                'description': meta_info.get('description', ''),
                'creator': meta_info.get('creator', ''),
                'date': meta_info.get('date', ''),
                'subject': meta_info.get('subject', []),
                'language': meta_info.get('language', ''),
                'runtime': meta_info.get('runtime', ''),
                'source': meta_info.get('source', ''),
                'collection': meta_info.get('collection', []),
                'identifier': item_id,
                'archive_url': url,
                'uploader': meta_info.get('uploader', ''),
                'upload_date': meta_info.get('addeddate', ''),
                'publicdate': meta_info.get('publicdate', ''),
                'mediatype': meta_info.get('mediatype', ''),
                'backup_location': meta_info.get('backup_location', ''),
            }
            
            # Special handling for YouTube archived videos
            if 'youtube' in item_id.lower() or 'yt' in item_id.lower():
                enhanced_metadata['original_platform'] = 'YouTube (archived)'
                # Try to extract original YouTube ID if present
                yt_id_match = re.search(r'--([a-zA-Z0-9_-]{11})$', item_id)
                if yt_id_match:
                    enhanced_metadata['original_youtube_id'] = yt_id_match.group(1)
                    enhanced_metadata['original_youtube_url'] = f"https://www.youtube.com/watch?v={yt_id_match.group(1)}"
            
            if logger and DEBUG_MODE: 
                safe_log(logger, 'info', f"Archive.org metadata captured: {title}")
                if enhanced_metadata.get('creator'):
                    safe_log(logger, 'info', f"Creator: {enhanced_metadata['creator']}")
                if enhanced_metadata.get('date'):
                    safe_log(logger, 'info', f"Date: {enhanced_metadata['date']}")
                    
        except Exception as e:
            if logger and DEBUG_MODE: 
                safe_log(logger, 'warning', f"Error getting enhanced metadata, using basic info: {str(e)}")
            safe_title = sanitize_filename(item_id)
            enhanced_metadata = {'title': safe_title, 'identifier': item_id}
        
        # Try to find video files in the item
        files_url = f"https://archive.org/metadata/{item_id}/files"
        
        try:
            files_response = requests.get(files_url, headers=headers, timeout=15)
            if files_response.status_code == 200:
                files_data = files_response.json()
                
                # Handle both dict and list responses from Archive.org API
                files_list = []
                if isinstance(files_data, list):
                    files_list = files_data
                elif isinstance(files_data, dict):
                    # If it's a dict, it might have a 'files' key or the dict values might be the files
                    if 'files' in files_data:
                        files_list = files_data['files']
                    elif 'result' in files_data:
                        files_list = files_data['result']
                    else:
                        # Try to extract file objects from the dict values
                        for key, value in files_data.items():
                            if isinstance(value, dict) and 'name' in value:
                                files_list.append(value)
                            elif isinstance(value, list):
                                files_list.extend(value)
                else:
                    if logger: safe_log(logger, 'error', f"Unexpected files data type: {type(files_data)}")
                    return None, False
                
                if logger and DEBUG_MODE: 
                    safe_log(logger, 'info', f"Found {len(files_list)} files in archive")
                
                # Look for video files with enhanced filtering
                video_files = []
                for file_info in files_list:
                    # Skip if file_info is not a dictionary
                    if not isinstance(file_info, dict):
                        if logger and DEBUG_MODE: 
                            safe_log(logger, 'warning', f"Skipping non-dict file info: {type(file_info)} - {file_info}")
                        continue
                    
                    filename = file_info.get('name', '')
                    format_type = file_info.get('format', '').lower()
                    size = file_info.get('size', 0)
                    
                    # Skip thumbnail and very small files
                    if any(skip_word in filename.lower() for skip_word in ['thumb', 'screenshot', '.png', '.jpg', '.gif']):
                        continue
                    
                    # Convert size to int safely
                    try:
                        size_int = int(size) if size else 0
                    except (ValueError, TypeError):
                        size_int = 0
                    
                    if size_int < 1000000:  # Skip files smaller than 1MB
                        continue
                    
                    # Categorize video files by quality/preference
                    if format_type in ['mp4', 'mpeg4'] or filename.lower().endswith('.mp4'):
                        # Prefer HD/high quality versions
                        priority = 1
                        if any(quality in filename.lower() for quality in ['hd', '720', '1080', 'high']):
                            priority = 0
                        video_files.append((filename, 'mp4', size_int, priority, file_info))
                    elif format_type in ['webm'] or filename.lower().endswith('.webm'):
                        video_files.append((filename, 'webm', size_int, 2, file_info))
                    elif format_type in ['avi'] or filename.lower().endswith('.avi'):
                        video_files.append((filename, 'avi', size_int, 3, file_info))
                    elif format_type in ['mkv', 'mov', 'flv'] or any(filename.lower().endswith(ext) for ext in ['.mkv', '.mov', '.flv']):
                        video_files.append((filename, format_type, size_int, 4, file_info))
                
                if not video_files:
                    if logger: safe_log(logger, 'error', f"No suitable video files found for {item_id}")
                    
                    # Debug: Log what files were found
                    if logger and DEBUG_MODE:
                        safe_log(logger, 'info', f"Total files in archive: {len(files_list)}")
                        for i, file_info in enumerate(files_list[:10]):  # Log first 10 files for debugging
                            if isinstance(file_info, dict):
                                name = file_info.get('name', 'unknown')
                                fmt = file_info.get('format', 'unknown')
                                size = file_info.get('size', 'unknown')
                                safe_log(logger, 'info', f"  File {i+1}: {name} (format: {fmt}, size: {size})")
                            else:
                                safe_log(logger, 'warning', f"  File {i+1}: Non-dict object: {type(file_info)} - {str(file_info)[:100]}")
                    
                    return None, False
                
                # Sort by priority (lower is better), then by size (larger is better)
                video_files.sort(key=lambda x: (x[3], -x[2]))
                best_file = video_files[0]
                
                video_filename = best_file[0]
                video_ext = best_file[1]
                video_size = best_file[2]
                file_metadata = best_file[4]
                
                if logger and DEBUG_MODE: 
                    safe_log(logger, 'info', f"Selected video file: {video_filename} ({video_ext}, {video_size} bytes)")
                
                # Add file-specific metadata
                enhanced_metadata['file_format'] = video_ext
                enhanced_metadata['file_size'] = video_size
                enhanced_metadata['original_filename'] = video_filename
                enhanced_metadata['file_md5'] = file_metadata.get('md5', '')
                enhanced_metadata['file_sha1'] = file_metadata.get('sha1', '')
                
                # Download the video file
                download_url = f"https://archive.org/download/{item_id}/{urllib.parse.quote(video_filename)}"
                
                # Create local filename with better naming
                if enhanced_metadata.get('creator') and enhanced_metadata.get('date'):
                    safe_filename = f"{safe_title}_{enhanced_metadata['creator']}_{enhanced_metadata['date']}.{video_ext}"
                else:
                    safe_filename = f"{safe_title}.{video_ext}"
                
                # Apply sanitization twice to ensure Windows compatibility
                safe_filename = sanitize_filename(safe_filename)
                
                # Additional cleanup for problematic characters
                safe_filename = safe_filename.replace('/', ' ').replace('\\', ' ')
                
                # Ensure filename isn't too long (Windows 260 char limit)
                if len(safe_filename) > 200:
                    name_part = safe_filename.rsplit('.', 1)[0][:190]
                    ext_part = safe_filename.rsplit('.', 1)[1] if '.' in safe_filename else video_ext
                    safe_filename = f"{name_part}.{ext_part}"
                
                file_path = cache_dir / safe_filename
                
                if logger and DEBUG_MODE: 
                    safe_log(logger, 'info', f"Local filename: {safe_filename}")
                    safe_log(logger, 'info', f"Full path: {file_path}")
                    safe_log(logger, 'info', f"Downloading: {download_url}")
                    safe_log(logger, 'info', f"File size: {video_size} bytes")
                
                video_response = requests.get(download_url, stream=True, headers=headers, timeout=60)
                if video_response.status_code == 200:
                    total_size = int(video_response.headers.get('content-length', 0))
                    downloaded = 0
                    
                    with open(file_path, 'wb') as f:
                        for chunk in video_response.iter_content(chunk_size=1024*1024):  # 1MB chunks
                            if chunk:
                                f.write(chunk)
                                downloaded += len(chunk)
                                
                                # Log progress for large files
                                if total_size > 50*1024*1024 and downloaded % (10*1024*1024) == 0:  # Every 10MB for files >50MB
                                    progress = (downloaded / total_size) * 100 if total_size else 0
                                    if logger and DEBUG_MODE: 
                                        safe_log(logger, 'info', f"Download progress: {progress:.1f}%")
                    
                    if file_path.exists() and file_path.stat().st_size > 10000:
                        # Store the enhanced metadata with the video entry
                        manager.add_video(url, safe_title, safe_filename)
                        
                        # Save additional metadata to a separate file
                        metadata_file = cache_dir / f"{safe_filename}.metadata.json"
                        try:
                            with open(metadata_file, 'w', encoding='utf-8') as f:
                                json.dump(enhanced_metadata, f, indent=2, ensure_ascii=False)
                            if logger and DEBUG_MODE: 
                                safe_log(logger, 'info', f"Metadata saved to: {metadata_file.name}")
                        except Exception as e:
                            if logger and DEBUG_MODE: 
                                safe_log(logger, 'warning', f"Could not save metadata file: {str(e)}")
                        
                        if logger: safe_log(logger, 'info', f"Successfully downloaded archive.org video: {safe_filename}")
                        return safe_filename, False
                    else:
                        if logger: safe_log(logger, 'error', f"Downloaded file is too small or doesn't exist")
                        return None, False
                else:
                    if logger: safe_log(logger, 'error', f"Failed to download video file: {video_response.status_code}")
                    return None, False
                    
        except Exception as e:
            if logger: safe_log(logger, 'error', f"Error processing archive.org files: {str(e)}")
            return None, False
        
        if logger: safe_log(logger, 'error', "Archive.org video download failed")
        return None, False
    
    except Exception as e:
        if logger: safe_log(logger, 'error', f"Archive.org download error: {str(e)}")
        return None, False

def download_video(url, cache_dir, manager, logger=None, ffmpeg_plugin=None):
    """Main download function with format 18 priority and optional FFmpeg."""
    try:
        safe_log(logger, 'info', "Starting video download...", console_only=True)
        if logger: safe_log(logger, 'info', f"Starting download: {url}")
        
        # Check if already cached
        if url in manager.videos:
            filename = manager.videos[url]['filename']
            file_path = cache_dir / filename
            if file_path.exists():
                title = manager.videos[url]['title']
                safe_log(logger, 'info', f"Video download of '{title}' complete (from cache)", console_only=True)
                if logger: safe_log(logger, 'info', f"Using cached video: {filename}")
                return filename, True
            else:
                if logger and DEBUG_MODE: 
                    safe_log(logger, 'warning', f"Cached file not found: {filename}")
        
        # Special handling for Twitter/X
        if "twitter.com" in url or "x.com" in url:
            if logger and DEBUG_MODE: 
                safe_log(logger, 'info', f"Detected Twitter/X URL")
            result = download_twitter_video(url, cache_dir, manager, logger)
            if result[0]:
                safe_log(logger, 'info', f"Video download of 'Twitter/X Video' complete", console_only=True)
            return result
        
        # Special handling for Archive.org
        if "archive.org" in url:
            if logger and DEBUG_MODE: 
                safe_log(logger, 'info', f"Detected Archive.org URL")
            result = download_archive_video(url, cache_dir, manager, logger)
            if result[0]:
                # Get title from manager for console output
                for video_url, video_data in manager.videos.items():
                    if video_data['filename'] == result[0]:
                        safe_log(logger, 'info', f"Video download of '{video_data['title']}' complete", console_only=True)
                        break
            return result
        
        # Handle YouTube videos with improved format selection
        current_dir = os.getcwd()
        try:
            os.chdir(str(cache_dir))
            
            try:
                # Get info and title first
                with yt_dlp.YoutubeDL({
                    'skip_download': True,
                    'quiet': True,
                    'no_warnings': True
                }) as ydl:
                    info = ydl.extract_info(url, download=False)
                    title = info.get('title', 'unknown')
                
                if logger and DEBUG_MODE: 
                    safe_log(logger, 'info', f"Video title: {title}")
            except Exception as e:
                if logger: safe_log(logger, 'error', f"Error getting video info: {e}")
                title = "unknown"
            
            # Track files before download
            before_files = set(f.name for f in cache_dir.iterdir() if f.is_file())
            
            # Get format options based on quality preference and FFmpeg availability
            quality_preference = get_quality_preference()
            if ffmpeg_plugin is None:
                ffmpeg_plugin = FFmpegPlugin(logger)
            
            format_options = get_format_options(quality_preference, ffmpeg_plugin)
            
            if logger and DEBUG_MODE: 
                safe_log(logger, 'info', f"Quality preference: {quality_preference}")
                safe_log(logger, 'info', f"FFmpeg available: {ffmpeg_plugin.available}")
            
            download_success = False
            used_format = None
            
            for format_selector in format_options:
                try:
                    if logger and DEBUG_MODE: 
                        safe_log(logger, 'info', f"Trying format: {format_selector}")
                    
                    # Base options
                    ytdl_options = {
                        'format': format_selector,
                        'outtmpl': '%(title)s.%(ext)s',
                        'quiet': True,
                        'no_warnings': True,
                        'writeinfojson': False,
                        'writedescription': False,
                        'writesubtitles': False,
                        'writeautomaticsub': False,
                    }
                    
                    # Apply FFmpeg plugin options if available
                    if ffmpeg_plugin and ffmpeg_plugin.available:
                        ytdl_options = ffmpeg_plugin.get_ytdl_options(ytdl_options)
                    
                    # Download the video with current format
                    with yt_dlp.YoutubeDL(ytdl_options) as ydl:
                        ydl.download([url])
                    
                    download_success = True
                    used_format = format_selector
                    if logger and DEBUG_MODE: 
                        safe_log(logger, 'info', f"Download successful with format: {format_selector}")
                    break
                    
                except Exception as format_error:
                    if logger and DEBUG_MODE: 
                        safe_log(logger, 'warning', f"Format {format_selector} failed: {str(format_error)}")
                    continue
            
            if not download_success:
                if logger: safe_log(logger, 'error', "All format options failed")
                return None, False
            
            # Find new files
            after_files = set(f.name for f in cache_dir.iterdir() if f.is_file())
            new_files = after_files - before_files
            
            if new_files:
                # Use the new file
                new_filename = list(new_files)[0]
                
                # Sanitize if needed (has special chars)
                has_special_chars = any(ord(c) >= 128 for c in new_filename)
                if has_special_chars:
                    # Create safe filename
                    safe_name = sanitize_filename(new_filename)
                    
                    # Keep original extension
                    if "." in new_filename and not safe_name.endswith(new_filename.split(".")[-1]):
                        ext = new_filename.split(".")[-1]
                        safe_name = f"{safe_name}.{ext}"
                    
                    # Rename file
                    new_path = cache_dir / new_filename
                    safe_path = cache_dir / safe_name
                    
                    try:
                        new_path.rename(safe_path)
                        new_filename = safe_name  # Update to use the sanitized name
                        if logger and DEBUG_MODE: 
                            safe_log(logger, 'info', f"Renamed file to: {safe_name}")
                    except Exception as e:
                        if logger: safe_log(logger, 'error', f"Error renaming: {str(e)}")
                
                # Add video with the final filename (sanitized if needed)
                manager.add_video(url, title, new_filename)
                safe_log(logger, 'info', f"Video download of '{title}' complete", console_only=True)
                if logger and DEBUG_MODE: 
                    safe_log(logger, 'info', f"Video added with format: {used_format}")
                return new_filename, False
            
            # Fallback: look for recent files
            recent_time = datetime.datetime.now() - datetime.timedelta(minutes=2)
            recent_files = [f for f in cache_dir.iterdir() 
                           if f.is_file() and f.stat().st_mtime > recent_time.timestamp()]
            
            if recent_files:
                recent_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
                newest_file = recent_files[0]
                manager.add_video(url, title, newest_file.name)
                safe_log(logger, 'info', f"Video download of '{title}' complete", console_only=True)
                if logger and DEBUG_MODE: 
                    safe_log(logger, 'info', f"Using recent file: {newest_file.name}")
                return newest_file.name, False
                
        finally:
            try:
                os.chdir(current_dir)
            except Exception as e:
                if logger and DEBUG_MODE: 
                    safe_log(logger, 'warning', f"Error changing back to original directory: {e}")
                
    except Exception as e:
        if logger: safe_log(logger, 'error', f"Error in download_video: {str(e)}")
        if DEBUG_MODE:
            traceback.print_exc()
        return None, False

# HTTP Request Handler with comprehensive error handling
class MucacheHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def log_message(self, format, *args):
        """Override to use our logger with debug control."""
        try:
            if hasattr(self.server, 'logger') and DEBUG_MODE:
                safe_log(self.server.logger, 'info', f"{self.address_string()} - {format % args}")
        except Exception:
            pass

    def do_GET(self):
        try:
            if self.path == '/':
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                try:
                    with open('player.html', 'r', encoding='utf-8') as f:
                        self.wfile.write(f.read().encode('utf-8'))
                except FileNotFoundError:
                    self.wfile.write(b'<h1>Error: player.html not found</h1>')
                return

            elif self.path == '/manual':
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                try:
                    with open('manual.html', 'r', encoding='utf-8') as f:
                        self.wfile.write(f.read().encode('utf-8'))
                except FileNotFoundError:
                    self.wfile.write(b'<h1>Error: manual.html not found</h1>')
                return

            elif self.path == '/playlist':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                try:
                    videos = self.server.video_manager.get_sorted_videos()
                    self.wfile.write(json.dumps(videos).encode('utf-8'))
                except Exception as e:
                    safe_log(self.server.logger, 'error', f"Error getting playlist: {e}")
                    self.wfile.write(b'[]')
                return

            elif self.path == '/heartbeat':
                self.send_response(200)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b'alive')
                # Don't log heartbeat unless in debug mode
                if DEBUG_MODE and hasattr(self.server, 'logger'):
                    safe_log(self.server.logger, 'info', "Heartbeat received")
                return

            elif self.path == '/quality_settings':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                try:
                    settings = {
                        'quality_preference': get_quality_preference(),
                        'ffmpeg_available': check_ffmpeg_available(),
                        'options': {
                            'reliable': 'Always works - 360p quality using format 18',
                            'medium': 'Balanced - attempts 720p with reliable fallbacks',
                            'high': 'Best quality - 1080p with FFmpeg merging (requires FFmpeg)'
                        }
                    }
                    self.wfile.write(json.dumps(settings).encode('utf-8'))
                except Exception as e:
                    safe_log(self.server.logger, 'error', f"Error getting quality settings: {e}")
                    self.wfile.write(b'{"error": "Could not load settings"}')
                return

            elif self.path.startswith('/download?'):
                try:
                    query = urllib.parse.urlparse(self.path).query
                    params = urllib.parse.parse_qs(query)
                    url = params.get('url', [''])[0]
                    
                    if not url:
                        self.send_error(400, "No URL provided")
                        return
                    
                    safe_log(self.server.logger, 'info', f"Download request for: {url}")
                    
                    filename, from_cache = download_video(
                        url, 
                        self.server.cache_dir, 
                        self.server.video_manager, 
                        self.server.logger,
                        self.server.ffmpeg_plugin
                    )
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    
                    if filename:
                        response = {
                            'filename': filename, 
                            'fromCache': from_cache,
                            'success': True
                        }
                    else:
                        response = {
                            'error': 'Download failed',
                            'details': 'Could not download video. Check logs for details.',
                            'suggestion': 'Try a different quality setting or check if the URL is valid',
                            'success': False
                        }
                    
                    self.wfile.write(json.dumps(response).encode('utf-8'))
                except Exception as e:
                    safe_log(self.server.logger, 'error', f"Error in download handler: {e}")
                    self.send_error(500, f"Download error: {str(e)}")
                return

            elif self.path.startswith('/filestats?'):
                try:
                    query = urllib.parse.urlparse(self.path).query
                    params = urllib.parse.parse_qs(query)
                    filename = params.get('filename', [''])[0]
                    
                    if filename:
                        file_path = self.server.cache_dir / filename
                        if file_path.exists():
                            stats = file_path.stat()
                            
                            # Try to load enhanced metadata
                            enhanced_metadata = None
                            metadata_file = self.server.cache_dir / f"{filename}.metadata.json"
                            if metadata_file.exists():
                                try:
                                    with open(metadata_file, 'r', encoding='utf-8') as f:
                                        enhanced_metadata = json.load(f)
                                except Exception as e:
                                    if DEBUG_MODE:
                                        safe_log(self.server.logger, 'warning', f"Could not load metadata for {filename}: {e}")
                            
                            response = {
                                'size': stats.st_size,
                                'created': datetime.datetime.fromtimestamp(stats.st_ctime).isoformat(),
                                'modified': datetime.datetime.fromtimestamp(stats.st_mtime).isoformat(),
                                'enhanced_metadata': enhanced_metadata
                            }
                        else:
                            response = {'error': 'File not found'}
                    else:
                        response = {'error': 'No filename provided'}
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(response).encode('utf-8'))
                except Exception as e:
                    safe_log(self.server.logger, 'error', f"Error getting file stats: {e}")
                    self.send_error(500, str(e))
                return

            elif self.path.startswith('/mucache/'):
                # Serve video files - handle URL encoding and filename mismatches
                try:
                    # Decode the URL-encoded filename
                    encoded_filename = self.path[9:]  # Remove '/mucache/' prefix
                    filename = urllib.parse.unquote(encoded_filename)  # Decode URL encoding
                    
                    safe_log(self.server.logger, 'info', f"Requesting file: {filename} (original: {encoded_filename})")
                    
                    file_path = self.server.cache_dir / filename
                    
                    # If the exact filename doesn't exist, try sanitized version
                    if not file_path.exists():
                        sanitized_filename = sanitize_filename(filename)
                        file_path = self.server.cache_dir / sanitized_filename
                        safe_log(self.server.logger, 'info', f"Trying sanitized: {sanitized_filename}")
                        
                        # Also try without extension and re-add it
                        if not file_path.exists() and '.' in filename:
                            name_part = filename.rsplit('.', 1)[0]
                            ext_part = filename.rsplit('.', 1)[1]
                            sanitized_name = sanitize_filename(name_part)
                            file_path = self.server.cache_dir / f"{sanitized_name}.{ext_part}"
                            safe_log(self.server.logger, 'info', f"Trying name+ext: {sanitized_name}.{ext_part}")
                    
                    # Try to find any file that matches the base name (without extension)
                    if not file_path.exists():
                        base_name = filename.rsplit('.', 1)[0] if '.' in filename else filename
                        sanitized_base = sanitize_filename(base_name)
                        
                        safe_log(self.server.logger, 'info', f"Searching for similar files to: {base_name}")
                        
                        # Look for files with similar names
                        for existing_file in self.server.cache_dir.iterdir():
                            if existing_file.is_file() and existing_file.suffix in ['.mp4', '.webm', '.avi']:
                                existing_base = existing_file.stem
                                existing_name = existing_file.name
                                
                                # Try exact match first
                                if existing_name.lower() == filename.lower():
                                    file_path = existing_file
                                    safe_log(self.server.logger, 'info', f"Found exact match: {existing_name}")
                                    break
                                
                                # Try fuzzy matching
                                if (sanitized_base.lower() in existing_base.lower() or 
                                    existing_base.lower() in sanitized_base.lower() or
                                    base_name.lower() in existing_base.lower() or
                                    existing_base.lower() in base_name.lower()):
                                    file_path = existing_file
                                    safe_log(self.server.logger, 'info', f"Found fuzzy match: {existing_name}")
                                    break
                    
                    if file_path.exists() and file_path.is_file():
                        safe_log(self.server.logger, 'info', f"Serving video file: {file_path.name}")
                        
                        self.send_response(200)
                        self.send_header('Content-type', 'video/mp4')
                        self.send_header('Content-Length', str(file_path.stat().st_size))
                        self.send_header('Accept-Ranges', 'bytes')
                        self.end_headers()
                        
                        with open(file_path, 'rb') as f:
                            shutil.copyfileobj(f, self.wfile)
                    else:
                        safe_log(self.server.logger, 'error', f"Video file not found: {filename}")
                        safe_log(self.server.logger, 'info', f"Available files: {[f.name for f in self.server.cache_dir.iterdir() if f.is_file() and f.suffix in ['.mp4', '.webm', '.avi']]}")
                        self.send_error(404, "Video file not found")
                        
                except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError, OSError) as e:
                    # Normal network disconnection - don't log as error unless in debug mode
                    if DEBUG_MODE:
                        safe_log(self.server.logger, 'info', f"Client disconnected during video serve: {e}")
                    # Otherwise, silently ignore these common network events
                except Exception as e:
                    # Actual errors still get logged
                    safe_log(self.server.logger, 'error', f"Error serving video file: {e}")
                    self.send_error(500, str(e))
                return

            # If we get here, try default file serving
            super().do_GET()

        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError, OSError) as e:
            # Normal network disconnection - don't log as error unless in debug mode
            if DEBUG_MODE:
                safe_log(self.server.logger, 'info', f"Client disconnected during request: {e}")
            # Otherwise, silently ignore these common network events
        except Exception as e:
            safe_log(self.server.logger, 'error', f"Error in do_GET: {e}")
            if DEBUG_MODE:
                traceback.print_exc()
            try:
                self.send_error(500, str(e))
            except Exception:
                pass

    def do_POST(self):
        try:
            if self.path == '/shutdown':
                self.send_response(200)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b'Shutting down...')
                
                safe_log(self.server.logger, 'info', "Shutdown requested")
                console_status("Shutting down application...")
                threading.Thread(target=self.server.shutdown).start()
                return

            elif self.path == '/quality_settings':
                try:
                    content_length = int(self.headers['Content-Length'])
                    post_data = self.rfile.read(content_length)
                    data = json.loads(post_data.decode('utf-8'))
                    
                    quality_preference = data.get('quality_preference')
                    if quality_preference in ['reliable', 'medium', 'high']:
                        success = save_quality_preference(quality_preference)
                        
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        
                        response = {'success': success}
                        if success:
                            console_status(f"Quality preference updated to: {quality_preference}")
                            safe_log(self.server.logger, 'info', f"Quality preference updated to: {quality_preference}")
                        else:
                            response['error'] = 'Failed to save preference'
                        
                        self.wfile.write(json.dumps(response).encode('utf-8'))
                    else:
                        self.send_error(400, "Invalid quality preference")
                except Exception as e:
                    safe_log(self.server.logger, 'error', f"Error setting quality preference: {e}")
                    self.send_error(500, str(e))
                return

            elif self.path.startswith('/remove?'):
                try:
                    query = urllib.parse.urlparse(self.path).query
                    params = urllib.parse.parse_qs(query)
                    url = params.get('url', [''])[0]
                    
                    if url:
                        success = self.server.video_manager.remove_video(url, self.server.logger)
                        
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps({'success': success}).encode('utf-8'))
                    else:
                        self.send_error(400, "No URL provided")
                except Exception as e:
                    safe_log(self.server.logger, 'error', f"Error removing video: {e}")
                    self.send_error(500, str(e))
                return

            elif self.path == '/evidence_reports' and EVIDENCE_CITATION_AVAILABLE:
                try:
                    content_length = int(self.headers['Content-Length'])
                    post_data = self.rfile.read(content_length)
                    data = json.loads(post_data.decode('utf-8'))
                    
                    from evidence_generator import create_evidence_report
                    result = create_evidence_report(
                        self.server.cache_dir,
                        data['video_url'],
                        data['video_filename'],
                        data.get('case_info')
                    )
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(result).encode('utf-8'))
                except Exception as e:
                    safe_log(self.server.logger, 'error', f"Error generating evidence report: {e}")
                    self.send_error(500, str(e))
                return

            elif self.path == '/citations' and EVIDENCE_CITATION_AVAILABLE:
                try:
                    content_length = int(self.headers['Content-Length'])
                    post_data = self.rfile.read(content_length)
                    data = json.loads(post_data.decode('utf-8'))
                    
                    from citation_generator import generate_video_citations
                    result = generate_video_citations(
                        self.server.cache_dir,
                        data['video_url'],
                        data['video_filename'],
                        data.get('custom_info')
                    )
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(result).encode('utf-8'))
                except Exception as e:
                    safe_log(self.server.logger, 'error', f"Error generating citations: {e}")
                    self.send_error(500, str(e))
                return

            # Default POST handling
            self.send_error(404, "Not found")

        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError, OSError) as e:
            # Normal network disconnection - don't log as error unless in debug mode
            if DEBUG_MODE:
                safe_log(self.server.logger, 'info', f"Client disconnected during POST: {e}")
            # Otherwise, silently ignore these common network events
        except Exception as e:
            safe_log(self.server.logger, 'error', f"Error in do_POST: {e}")
            if DEBUG_MODE:
                traceback.print_exc()
            try:
                self.send_error(500, str(e))
            except Exception:
                pass

class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    """Handle requests in a separate thread."""
    daemon_threads = True
    allow_reuse_address = True

def main():
    """Main application entry point with comprehensive error handling."""
    logger = None
    try:
        # Show startup message
        now = datetime.datetime.now()
        console_status(f"Application started at: {now.strftime('%A, %B %d, %Y at %I:%M %p')}")
        
        # Check dependencies
        try:
            import yt_dlp
            import requests
        except ImportError as e:
            print(f"ERROR: Missing required dependency: {e}")
            print("Install with: pip install yt-dlp requests")
            input("Press Enter to exit...")
            return 1
        
        # Initialize cache directory
        try:
            cache_dir = Path.home() / "Downloads" / "mucache" / "data"
            cache_dir.mkdir(parents=True, exist_ok=True)
            
            # Test write permissions
            test_file = cache_dir / ".write_test"
            test_file.write_text("test")
            test_file.unlink()
            
        except PermissionError:
            print("ERROR: Permission denied creating cache directory")
            print(f"Please ensure you have write access to: {Path.home() / 'Downloads'}")
            input("Press Enter to exit...")
            return 1
        except Exception as e:
            print(f"ERROR: Could not create cache directory: {e}")
            input("Press Enter to exit...")
            return 1
        
        # Set up logging
        logger = setup_logging(cache_dir)
        safe_log(logger, 'info', "=== Mucache Player Starting ===")
        safe_log(logger, 'info', f"Cache directory: {cache_dir}")
        safe_log(logger, 'info', f"Python version: {sys.version}")
        
        # Log yt-dlp version
        try:
            safe_log(logger, 'info', f"yt-dlp version: {yt_dlp.version.__version__}")
        except Exception:
            safe_log(logger, 'warning', "Could not determine yt-dlp version")
        
        # Check port availability
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('127.0.0.1', 8000))
            sock.close()
            
            if result == 0:
                safe_log(logger, 'error', "Port 8000 is already in use!")
                print("ERROR: Port 8000 is already in use. Please close any other applications using this port.")
                input("Press Enter to exit...")
                return 1
        except Exception as e:
            if DEBUG_MODE:
                safe_log(logger, 'warning', f"Could not check port availability: {e}")
        
        # Initialize components
        try:
            manager = VideoManager(cache_dir)
            ffmpeg_plugin = FFmpegPlugin(logger)
            
            # Repair playlist if needed (fix filename mismatches)
            manager.repair_playlist(logger)
            
            safe_log(logger, 'info', "Application components initialized successfully")
        except Exception as e:
            safe_log(logger, 'critical', f"Failed to initialize components: {e}")
            print(f"CRITICAL ERROR: Failed to initialize application components: {e}")
            input("Press Enter to exit...")
            return 1
        
        # Start the web server
        try:
            server = ThreadedHTTPServer(("", 8000), MucacheHTTPRequestHandler)
            server.cache_dir = cache_dir
            server.video_manager = manager
            server.ffmpeg_plugin = ffmpeg_plugin
            server.logger = logger
            
            safe_log(logger, 'info', "Starting HTTP server on port 8000...")
            
            # Start server in thread
            server_thread = threading.Thread(target=server.serve_forever)
            server_thread.daemon = True
            server_thread.start()
            
            safe_log(logger, 'info', "Server started successfully")
            
            # Open browser
            try:
                webbrowser.open('http://localhost:8000')
                safe_log(logger, 'info', "Browser opened")
                console_status("Web interface opened in browser at: http://localhost:8000")
            except Exception as e:
                if DEBUG_MODE:
                    safe_log(logger, 'warning', f"Could not open browser: {e}")
                console_status("Could not open browser automatically. Please visit: http://localhost:8000")
            
            console_status("Mucache Player is ready. Paste video URLs to download and cache them.")
            if DEBUG_MODE:
                print("DEBUG MODE: All log messages will be shown")
            print("Press Ctrl+C to stop the server")
            
            # Keep the main thread alive
            try:
                while True:
                    threading.Event().wait(1)
            except KeyboardInterrupt:
                safe_log(logger, 'info', "Shutdown requested by user")
                console_status("Shutting down application...")
            finally:
                try:
                    server.shutdown()
                    safe_log(logger, 'info', "Server shutdown complete")
                except Exception:
                    pass
            
            return 0
            
        except Exception as e:
            safe_log(logger, 'critical', f"Critical server error: {e}")
            print(f"CRITICAL ERROR: Could not start server: {e}")
            if DEBUG_MODE:
                traceback.print_exc()
            input("Press Enter to exit...")
            return 1
    
    except Exception as e:
        if logger:
            safe_log(logger, 'critical', f"Fatal error: {e}")
        print(f"FATAL ERROR: {e}")
        if DEBUG_MODE:
            traceback.print_exc()
        input("Press Enter to exit...")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        print(f"Fatal error in main: {e}")
        if DEBUG_MODE:
            traceback.print_exc()
        input("Press Enter to exit...")
        sys.exit(1)