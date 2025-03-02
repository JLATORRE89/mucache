import http.server
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
from pathlib import Path

def setup_logging(cache_dir):
    """Set up logging to redirect output to log files."""
    logs_dir = cache_dir / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    logger = logging.getLogger('app')
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(logs_dir / 'app.log')
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    
    return logger

def safe_log(logger, level, message):
    """Log messages safely, handling non-ASCII characters."""
    try:
        if level == 'info': logger.info(message)
        elif level == 'warning': logger.warning(message)
        elif level == 'error': logger.error(message)
    except UnicodeEncodeError:
        # Sanitize the message
        safe_message = "".join(c if ord(c) < 128 else '?' for c in message)
        if level == 'info': logger.info(safe_message)
        elif level == 'warning': logger.warning(safe_message)
        elif level == 'error': logger.error(safe_message)

def sanitize_filename(filename):
    """Replace special characters with spaces for Windows compatibility."""
    # Replace non-ASCII characters with spaces
    safe_name = ""
    for c in filename:
        if ord(c) < 128:
            safe_name += c
        else:
            safe_name += " "
    
    # Replace Windows invalid characters
    for char in '<>:"|?*\\':
        safe_name = safe_name.replace(char, " ")
    
    # Collapse multiple spaces
    while "  " in safe_name:
        safe_name = safe_name.replace("  ", " ")
    
    return safe_name.strip()

class VideoManager:
    def __init__(self, cache_dir):
        self.cache_dir = cache_dir
        self.playlist_file = cache_dir / 'playlist.json'
        self.redownload_file = cache_dir / 'redownload_queue.json'
        self.videos = json.load(open(self.playlist_file)) if self.playlist_file.exists() else {}
        self.redownload_queue = json.load(open(self.redownload_file)) if self.redownload_file.exists() else {}

    def add_video(self, url, title, filename):
        self.videos[url] = {'title': title, 'filename': filename}
        json.dump(self.videos, open(self.playlist_file, 'w'))

    def remove_video(self, url, logger=None):
        """Remove a video from the playlist and try to delete the file."""
        if url in self.videos:
            filename = self.videos[url]['filename']
            # Remove from playlist first
            video_info = self.videos[url].copy()
            del self.videos[url]
            json.dump(self.videos, open(self.playlist_file, 'w'))
            
            # Try to delete file with both original and sanitized names
            file_paths = [
                self.cache_dir / filename,
                self.cache_dir / sanitize_filename(filename)
            ]
            
            deleted = False
            for file_path in file_paths:
                try:
                    if file_path.exists():
                        if logger: safe_log(logger, 'info', f"Attempting to delete: {file_path}")
                        file_path.unlink()
                        deleted = True
                        if logger: safe_log(logger, 'info', f"Successfully deleted: {file_path}")
                        break
                except Exception as e:
                    if logger: safe_log(logger, 'error', f"Error deleting file {file_path}: {str(e)}")
            
            if not deleted and logger:
                safe_log(logger, 'warning', f"Could not delete any version of the file: {filename}")
            
            return True
        return False

    def add_to_redownload_queue(self, url, title, original_filename, logger=None):
        self.redownload_queue[url] = {
            'title': title, 
            'original_filename': original_filename,
            'timestamp': datetime.datetime.now().isoformat()
        }
        if logger: safe_log(logger, 'info', f"Added to redownload queue: {title}")
        json.dump(self.redownload_queue, open(self.redownload_file, 'w'))

    def get_redownload_queue(self):
        return self.redownload_queue

    def remove_from_redownload_queue(self, url):
        if url in self.redownload_queue:
            del self.redownload_queue[url]
            json.dump(self.redownload_queue, open(self.redownload_file, 'w'))
            return True
        return False

    def get_sorted_videos(self):
        return sorted(
            [{'url': url, **data} for url, data in self.videos.items()],
            key=lambda x: x['title'].lower()
        )

def download_twitter_video(url, cache_dir, manager, logger=None):
    """Download Twitter/X videos."""
    try:
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
        response = requests.get(twitter_url, headers=headers)
        
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
                    if logger: safe_log(logger, 'info', f"Found video URL: {video_url}")
                    
                    video_response = requests.get(video_url, stream=True)
                    if video_response.status_code == 200:
                        with open(file_path, 'wb') as f:
                            for chunk in video_response.iter_content(chunk_size=8192):
                                f.write(chunk)
                        
                        if file_path.exists() and file_path.stat().st_size > 10000:
                            manager.add_video(url, safe_title, safe_filename)
                            return safe_filename, False
        
        if logger: safe_log(logger, 'error', "Twitter video download failed")
        return None, False
    
    except Exception as e:
        if logger: safe_log(logger, 'error', f"Twitter download error: {str(e)}")
        return None, False

def download_video(url, cache_dir, manager, logger=None):
    """Main download function with special handling for Twitter/X."""
    try:
        # Check if already cached
        if url in manager.videos:
            filename = manager.videos[url]['filename']
            file_path = cache_dir / filename
            if file_path.exists():
                if logger: safe_log(logger, 'info', f"Using cached video: {filename}")
                return filename, True
            else:
                if logger: safe_log(logger, 'warning', f"Cached file not found: {filename}")
        
        # Special handling for Twitter/X
        if "twitter.com" in url or "x.com" in url:
            if logger: safe_log(logger, 'info', f"Detected Twitter/X URL")
            return download_twitter_video(url, cache_dir, manager, logger)
        
        # Handle YouTube videos
        current_dir = os.getcwd()
        os.chdir(str(cache_dir))
        
        try:
            # Get info and title
            with yt_dlp.YoutubeDL({
                'skip_download': True,
                'quiet': True
            }) as ydl:
                info = ydl.extract_info(url, download=False)
                title = info.get('title', 'unknown')
            
            # Track files before download
            before_files = set(f.name for f in cache_dir.iterdir() if f.is_file())
            
            # Download the video
            with yt_dlp.YoutubeDL({
                'format': 'best',
                'outtmpl': '%(title)s.%(ext)s',
                'quiet': True
            }) as ydl:
                ydl.download([url])
            
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
                    if "." in new_filename and not safe_name.endswith(".mp4"):
                        ext = new_filename.split(".")[-1]
                        safe_name = f"{safe_name}.{ext}"
                    
                    # Rename file
                    new_path = cache_dir / new_filename
                    safe_path = cache_dir / safe_name
                    
                    try:
                        new_path.rename(safe_path)
                        new_filename = safe_name
                    except Exception as e:
                        if logger: safe_log(logger, 'error', f"Error renaming: {str(e)}")
                
                manager.add_video(url, title, new_filename)
                return new_filename, False
            
            # Fallback: look for recent files
            recent_time = datetime.datetime.now() - datetime.timedelta(minutes=2)
            recent_files = [f for f in cache_dir.iterdir() 
                           if f.is_file() and f.stat().st_mtime > recent_time.timestamp()]
            
            if recent_files:
                recent_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
                newest_file = recent_files[0]
                manager.add_video(url, title, newest_file.name)
                return newest_file.name, False
            
            return None, False
            
        finally:
            os.chdir(current_dir)
            
    except Exception as e:
        if logger: safe_log(logger, 'error', f"Error downloading video: {str(e)}")
        return None, False

class RequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, video_manager=None, shutdown_event=None, logger=None, **kwargs):
        self.video_manager = video_manager
        self.shutdown_event = shutdown_event
        self.logger = logger
        super().__init__(*args, **kwargs)
        
    def log_message(self, format, *args):
        """Override default logging to use our custom logger"""
        if self.logger:
            try:
                self.logger.info("%s - %s" % (self.address_string(), format % args))
            except UnicodeEncodeError:
                # Create a safe version of the message
                message = format % args
                safe_message = sanitize_filename(message)
                self.logger.info("%s - %s" % (self.address_string(), safe_message))

    def serve_file(self, path, content_type):
        """Serve a static file"""
        with open(path, 'rb') as f:
            self.send_response(200)
            self.send_header('Content-type', content_type)
            self.end_headers()
            self.wfile.write(f.read())

    def get_file_stats(self, filename):
        """Get file stats (creation time, size)."""
        try:
            file_path = self.video_manager.cache_dir / filename
            if file_path.exists():
                stats = file_path.stat()
                created = datetime.datetime.fromtimestamp(stats.st_ctime).isoformat()
                modified = datetime.datetime.fromtimestamp(stats.st_mtime).isoformat()
                return {
                    'created': created,
                    'modified': modified,
                    'size': stats.st_size,
                    'exists': True
                }
            else:
                return {'exists': False}
        except Exception as e:
            if self.logger: safe_log(self.logger, 'error', f"Error getting file stats: {str(e)}")
            return {'exists': False, 'error': str(e)}
    
    def handle_file_stats(self):
        """Handle file stats requests."""
        try:
            query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            filename = query.get('filename', [''])[0]
            if filename:
                stats = self.get_file_stats(filename)
                self.send_json(stats)
            else:
                self.send_json({'exists': False})
        except Exception as e:
            if self.logger: safe_log(self.logger, 'error', f"File stats error: {str(e)}")
            self.send_json({'error': str(e), 'exists': False})

    def do_GET(self):
        try:
            # API endpoints
            if self.path == '/':
                self.serve_file(Path(__file__).parent / "player.html", 'text/html')
            elif self.path == '/manual':
                self.serve_file(Path(__file__).parent / "manual.html", 'text/html')
            elif self.path == '/playlist':
                self.send_json(self.video_manager.get_sorted_videos())
            elif self.path == '/redownload_queue':
                self.send_json(self.video_manager.get_redownload_queue())
            elif self.path.startswith('/download'):
                self.handle_download()
            elif self.path.startswith('/filestats'):
                self.handle_file_stats()
            elif self.path == '/heartbeat':
                self.send_response(200)
                self.end_headers()
            
            # Serve videos
            elif self.path.startswith('/mucache/'):
                filename = urllib.parse.unquote(self.path.split('/', 2)[-1])
                file_path = self.video_manager.cache_dir / filename
                
                if file_path.exists():
                    try:
                        with open(file_path, 'rb') as f:
                            fs = os.fstat(f.fileno())
                            self.send_response(200)
                            self.send_header('Content-Type', 'video/mp4')
                            self.send_header('Content-Length', str(fs[6]))
                            self.send_header('Last-Modified', self.date_time_string(fs.st_mtime))
                            self.send_header('Cache-Control', 'no-cache')
                            self.end_headers()
                            
                            chunk_size = 1024 * 1024  # 1MB chunks
                            while True:
                                chunk = f.read(chunk_size)
                                if not chunk: break
                                try:
                                    self.wfile.write(chunk)
                                except:
                                    break
                    except Exception as e:
                        if self.logger: safe_log(self.logger, 'error', f"Error reading video: {str(e)}")
                        self.send_error(500, f"Error reading video")
                else:
                    # File not found - check for special characters in filename
                    safe_filename = sanitize_filename(filename)
                    safe_path = self.video_manager.cache_dir / safe_filename
                    
                    if safe_path.exists():
                        # We found a safe version - redirect to it
                        self.send_response(302)
                        self.send_header('Location', f'/mucache/{urllib.parse.quote(safe_filename)}')
                        self.end_headers()
                    else:
                        # Add to redownload queue if it's in the playlist
                        for url, data in self.video_manager.videos.items():
                            if data['filename'] == filename:
                                if self.logger: safe_log(self.logger, 'warning', f"Adding missing file to redownload queue: {filename}")
                                self.video_manager.add_to_redownload_queue(url, data['title'], filename, self.logger)
                                break
                        
                        self.send_error(404, f"File not found")
            else:
                super().do_GET()
                
        except Exception as e:
            if self.logger: safe_log(self.logger, 'error', f"GET handler error: {str(e)}")
            self.send_error(500, f"Internal error")

    def do_POST(self):
        try:
            if self.path.startswith('/remove'):
                url = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).get('url', [''])[0]
                success = self.video_manager.remove_video(url) if url else False
                self.send_response(200 if success else 400)
                self.end_headers()
            elif self.path.startswith('/redownload'):
                url = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).get('url', [''])[0]
                # Redownload logic here
                self.send_response(200)
                self.end_headers()
            elif self.path == '/shutdown' and self.shutdown_event:
                self.send_response(200)
                self.end_headers()
                threading.Timer(0.5, self.shutdown_event.set).start()
            else:
                self.send_response(404)
                self.end_headers()
        except Exception as e:
            if self.logger: safe_log(self.logger, 'error', f"POST error: {str(e)}")

    def handle_download(self):
        try:
            url = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).get('url', [''])[0]
            if not url:
                self.send_json({'error': 'No URL provided'})
                return
                
            filename, from_cache = download_video(url, self.video_manager.cache_dir, self.video_manager, self.logger)
            
            if filename:
                # Get additional file information
                file_info = {}
                file_path = self.video_manager.cache_dir / filename
                
                if file_path.exists():
                    file_info['size'] = file_path.stat().st_size
                    file_info['created'] = datetime.datetime.fromtimestamp(file_path.stat().st_ctime).isoformat()
                    
                self.send_json({
                    'filename': filename, 
                    'fromCache': from_cache,
                    'fileInfo': file_info,
                    'status': 'success'
                })
            else:
                self.send_json({
                    'error': 'Download failed',
                    'details': 'Unable to download or locate the video file.',
                    'status': 'error'
                })
        except Exception as e:
            if self.logger: safe_log(self.logger, 'error', f"Download error: {str(e)}")
            self.send_json({'error': str(e)})

    def send_json(self, data):
        try:
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())
        except Exception as e:
            if self.logger: safe_log(self.logger, 'error', f"Error sending JSON: {str(e)}")

def main():
    cache_dir = Path.home() / "Downloads" / "mucache" / "data"
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    logger = setup_logging(cache_dir)
    logger.info("=== Mucache Player Starting ===")
    
    video_manager = VideoManager(cache_dir)
    logger.info(f"Loaded {len(video_manager.videos)} videos from playlist")
    
    os.chdir(cache_dir.parent)
    shutdown_event = threading.Event()
    
    server = socketserver.ThreadingTCPServer(("", 8000), 
                            lambda *args: RequestHandler(*args, 
                                                      video_manager=video_manager,
                                                      shutdown_event=shutdown_event,
                                                      logger=logger))
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    
    logger.info("Server started at http://localhost:8000")
    webbrowser.open("http://localhost:8000")
    
    try:
        while not shutdown_event.is_set():
            shutdown_event.wait(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        logger.info("Shutting down server...")
        server.shutdown()
        server.server_close()
        logger.info("=== Mucache Player Stopped ===")

if __name__ == "__main__": 
    main()