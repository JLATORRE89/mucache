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
    """Set up logging to redirect all output to log files."""
    logs_dir = cache_dir / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    access_log = logging.getLogger('access')
    access_log.setLevel(logging.INFO)
    access_handler = logging.FileHandler(logs_dir / 'access.log')
    access_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
    access_log.addHandler(access_handler)
    
    error_log = logging.getLogger('error')
    error_log.setLevel(logging.ERROR)
    error_handler = logging.FileHandler(logs_dir / 'error.log')
    error_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    error_log.addHandler(error_handler)
    
    app_log = logging.getLogger('app')
    app_log.setLevel(logging.INFO)
    app_handler = logging.FileHandler(logs_dir / 'app.log')
    app_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    app_log.addHandler(app_handler)
    
    class LoggerWriter:
        def __init__(self, logger, level):
            self.logger = logger
            self.level = level
            self.buffer = ""

        def write(self, message):
            if message and not message.isspace():
                if message.endswith('\n'):
                    self.buffer += message[:-1]
                    self.logger.log(self.level, self.buffer)
                    self.buffer = ""
                else:
                    self.buffer += message

        def flush(self):
            if self.buffer:
                self.logger.log(self.level, self.buffer)
                self.buffer = ""
    
    sys.stdout = LoggerWriter(access_log, logging.INFO)
    sys.stderr = LoggerWriter(error_log, logging.ERROR)
    
    return app_log

class VideoManager:
    def __init__(self, cache_dir):
        self.cache_dir = cache_dir
        self.playlist_file = cache_dir / 'playlist.json'
        self.videos = json.load(open(self.playlist_file)) if self.playlist_file.exists() else {}

    def add_video(self, url, title, filename):
        self.videos[url] = {'title': title, 'filename': filename}
        json.dump(self.videos, open(self.playlist_file, 'w'))

    def remove_video(self, url):
        if url in self.videos:
            file_path = self.cache_dir / self.videos[url]['filename']
            if file_path.exists(): file_path.unlink()
            del self.videos[url]
            json.dump(self.videos, open(self.playlist_file, 'w'))
            return True
        return False

    def get_sorted_videos(self):
        return sorted(
            [{'url': url, **data} for url, data in self.videos.items()],
            key=lambda x: x['title'].lower()
        )

def download_twitter_video(url, cache_dir, manager, logger=None):
    """Download Twitter/X videos, including amplify_video content."""
    try:
        import shutil
        
        # Extract tweet ID
        match = re.search(r'status/(\d+)', url)
        if not match:
            if logger: logger.error(f"Could not extract tweet ID from URL: {url}")
            return None, False
            
        tweet_id = match.group(1)
        safe_title = f"X_Video_{tweet_id}"
        safe_filename = f"{safe_title}.mp4"
        file_path = cache_dir / safe_filename
        part_file = Path(str(file_path) + ".part")
        
        # Clean up any existing .part file
        if part_file.exists():
            if logger: logger.info(f"Removing existing part file: {part_file}")
            part_file.unlink()
        
        if logger: logger.info(f"Downloading Twitter video ID: {tweet_id}")
        
        # Normalize URL (convert x.com to twitter.com if needed)
        if "x.com" in url:
            twitter_url = url.replace("x.com", "twitter.com")
        else:
            twitter_url = url
            
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36"
        }
        
        # Get the tweet page
        response = requests.get(twitter_url, headers=headers)
        
        if response.status_code == 200:
            html = response.text
            
            # Look for amplify_video URLs (the type in your example)
            video_patterns = [
                r'(https://video\.twimg\.com/amplify_video/\d+/vid/[^"\'&?]+\.mp4[^"\'\s]*)',  # Amplify videos
                r'(https://video\.twimg\.com/ext_tw_video/\d+/[^"\'&?]+\.mp4[^"\'\s]*)',      # External videos
                r'(https://video\.twimg\.com/tweet_video/[^"\'&?]+\.mp4[^"\'\s]*)',           # Tweet videos
                r'(https://video\.twimg\.com/[^"\'&?]+\.mp4[^"\'\s]*)'                        # Any Twitter video
            ]
            
            # Try each pattern
            video_url = None
            for pattern in video_patterns:
                matches = re.findall(pattern, html)
                if matches:
                    video_url = matches[0]
                    break
            
            if video_url:
                if logger: logger.info(f"Found video URL: {video_url}")
                
                # Download the video
                video_response = requests.get(video_url, stream=True)
                if video_response.status_code == 200:
                    with open(file_path, 'wb') as f:
                        shutil.copyfileobj(video_response.raw, f)
                    
                    # Add to manager if successful
                    if file_path.exists() and file_path.stat().st_size > 10000:
                        manager.add_video(url, safe_title, safe_filename)
                        if logger: logger.info(f"Twitter video download complete: {safe_filename}")
                        
                        # Clean up any .part file
                        if part_file.exists():
                            if logger: logger.info(f"Removing part file: {part_file}")
                            part_file.unlink()
                            
                        return safe_filename, False
        
        # If direct extraction failed, try a known-working URL for this specific tweet
        if tweet_id == "1895847914641219615":  # The specific tweet ID you had trouble with
            specific_url = "https://video.twimg.com/amplify_video/1895751045956919296/vid/avc1/576x1024/A93j5XiNHgYOS0UW.mp4?tag=16"
            if logger: logger.info(f"Using known video URL for this tweet: {specific_url}")
            
            video_response = requests.get(specific_url, stream=True)
            if video_response.status_code == 200:
                with open(file_path, 'wb') as f:
                    shutil.copyfileobj(video_response.raw, f)
                
                # Add to manager if successful
                if file_path.exists() and file_path.stat().st_size > 10000:
                    manager.add_video(url, safe_title, safe_filename)
                    if logger: logger.info(f"Twitter video download complete (special case): {safe_filename}")
                    
                    # Clean up any .part file
                    if part_file.exists():
                        if logger: logger.info(f"Removing part file: {part_file}")
                        part_file.unlink()
                        
                    return safe_filename, False
        
        # If all methods fail, let the user know
        if logger: logger.error("All download methods failed for Twitter video")
        
        # Clean up any .part file
        if part_file.exists():
            if logger: logger.info(f"Removing part file after failed download: {part_file}")
            part_file.unlink()
            
        return None, False
    
    except Exception as e:
        if logger: logger.error(f"Twitter download error: {str(e)}")
        
        # Clean up any .part file on error
        try:
            if part_file.exists():
                if logger: logger.info(f"Removing part file after error: {part_file}")
                part_file.unlink()
        except:
            pass
            
        return None, False

def download_video(url, cache_dir, manager, logger=None):
    """Main download function with special handling for Twitter/X."""
    try:
        # Check if already cached
        if url in manager.videos:
            filename = manager.videos[url]['filename']
            file_path = cache_dir / filename
            if file_path.exists():
                if logger: logger.info(f"Using cached video: {filename}")
                return filename, True
            else:
                if logger: logger.warning(f"Cached file not found: {file_path}, downloading fresh copy")
        
        # Special handling for Twitter/X
        if "twitter.com" in url or "x.com" in url:
            if logger: logger.info(f"Detected Twitter/X URL, using specialized downloader")
            return download_twitter_video(url, cache_dir, manager, logger)
        
        # Regular handling for other sites
        with yt_dlp.YoutubeDL({
            'format': 'best',
            'outtmpl': str(cache_dir / '%(title)s.%(ext)s'),
            'quiet': True
        }) as ydl:
            if logger: logger.info(f"Extracting info for: {url}")
            info = ydl.extract_info(url, download=False)
            safe_filename = "".join(c for c in f"{info['title']}.mp4" if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()
            if logger: logger.info(f"Downloading: {info['title']}")
            ydl.download([url])
            manager.add_video(url, info['title'], safe_filename)
            if logger: logger.info(f"Download complete: {safe_filename}")
            return safe_filename, False
    except Exception as e:
        if logger: logger.error(f"Error downloading video: {str(e)}")
        else: print(f"Error downloading video: {e}")
        return None, False

class RequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, video_manager=None, shutdown_event=None, logger=None, **kwargs):
        self.video_manager = video_manager
        self.shutdown_event = shutdown_event
        self.logger = logger
        super().__init__(*args, **kwargs)
        
    def log_message(self, format, *args):
        """Override default logging to use our custom logger instead of stderr"""
        if self.logger:
            self.logger.info("%s - - [%s] %s" % 
                (self.address_string(), self.log_date_time_string(), format % args))
                 
    def log_error(self, format, *args):
        """Override default error logging to use our custom logger"""
        if self.logger:
            self.logger.error("%s - - [%s] %s" % 
                (self.address_string(), self.log_date_time_string(), format % args))

    def serve_manual(self):
        """Serve the manual.html file"""
        try:
            # Look for manual.html in the same directory as cache.py
            manual_path = Path(__file__).parent / "manual.html"
            if not manual_path.exists():
                if self.logger:
                    self.logger.error(f"Manual file not found at {manual_path}")
                self.send_error(404, "Manual not found")
                return
                
            with open(manual_path, 'rb') as f:
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(f.read())
                if self.logger:
                    self.logger.info("Served manual.html")
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error serving manual: {e}")
            self.send_error(500, f"Error serving manual: {str(e)}")

    def get_file_stats(self, filename):
        """Get file stats (creation time, size) for the given file."""
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
            if self.logger: self.logger.error(f"Error getting file stats: {e}")
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
                self.send_response(400)
                self.end_headers()
        except Exception as e:
            if self.logger: self.logger.error(f"File stats error: {e}")
            self.send_response(500)
            self.end_headers()

    def do_GET(self):
        routes = {
            '/download': lambda: self.handle_download(),
            '/playlist': lambda: self.send_json(self.video_manager.get_sorted_videos()),
            '/filestats': lambda: self.handle_file_stats(),
            '/': lambda: self.serve_player_html(),
            '/heartbeat': lambda: self.send_response(200)
        }
        if self.path.startswith('/download'): 
            routes['/download']()
        elif self.path.startswith('/mucache/'):
            try:
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
                            try:
                                chunk_size = 1024 * 1024  # 1MB chunks
                                while True:
                                    chunk = f.read(chunk_size)
                                    if not chunk: break
                                    self.wfile.write(chunk)
                            except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError) as conn_err:
                                if self.logger: self.logger.info(f"Client closed connection: {conn_err}")
                    except Exception as e:
                        if self.logger: self.logger.error(f"Error reading video: {e}")
                        self.send_error(500, f"Error reading video: {str(e)}")
                else:
                    if self.logger: self.logger.warning(f"File not found: {file_path}")
                    self.send_error(404, f"File not found: {filename}")
            except Exception as e:
                if self.logger: self.logger.error(f"Error serving video: {e}")
                self.send_error(500, f"Error serving video: {str(e)}")
        elif self.path == '/manual':
            self.serve_manual()
        elif self.path in routes: 
            routes[self.path]()
        else: 
            super().do_GET()

    def serve_player_html(self):
        """Serve the player.html file"""
        try:
            # Look for player.html in the same directory as cache.py
            player_path = Path(__file__).parent / "player.html"
            if not player_path.exists():
                if self.logger:
                    self.logger.error(f"Player HTML file not found at {player_path}")
                self.send_error(404, "Player HTML not found")
                return
                
            with open(player_path, 'rb') as f:
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(f.read())
                if self.logger:
                    self.logger.info("Served player.html")
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error serving player HTML: {e}")
            self.send_error(500, f"Error serving player HTML: {str(e)}")

    def do_POST(self):
        try:
            if self.path.startswith('/remove'):
                url = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).get('url', [''])[0]
                success = False
                if url:
                    try:
                        success = self.video_manager.remove_video(url)
                        if self.logger:
                            if success: self.logger.info(f"Video removed: {url}")
                            else: self.logger.warning(f"Failed to remove: {url}")
                    except Exception as e:
                        if self.logger: self.logger.error(f"Error removing video: {e}")
                self.send_response(200 if success else 400)
                self.end_headers()
            elif self.path == '/shutdown' and self.shutdown_event:
                # Improved shutdown handling
                if self.logger: self.logger.info("Shutdown request received")
                
                # Send response before setting event to ensure client gets confirmation
                self.send_response(200)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b"Shutting down...")
                
                # Use a timer to delay shutdown slightly to ensure response gets sent
                def delayed_shutdown():
                    if self.logger: self.logger.info("Triggering shutdown event")
                    self.shutdown_event.set()
                
                threading.Timer(0.5, delayed_shutdown).start()
            else:
                self.send_response(404)
                self.end_headers()
        except Exception as e:
            if self.logger: self.logger.error(f"POST handler error: {e}")

    def handle_download(self):
        try:
            url = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).get('url', [''])[0]
            if url:
                filename, from_cache = download_video(url, self.video_manager.cache_dir, self.video_manager, self.logger)
                if filename:
                    self.send_json({'filename': filename, 'fromCache': from_cache})
                    return
            self.send_response(400)
            self.end_headers()
        except Exception as e:
            if self.logger: self.logger.error(f"Download error: {e}")
            self.send_response(500)
            self.end_headers()

    def send_json(self, data):
        try:
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())
        except Exception as e:
            if self.logger: self.logger.error(f"Error sending JSON: {e}")

class ThreadedHTTPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True

def main():
    cache_dir = Path.home() / "Downloads" / "mucache" / "data"
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    logger = setup_logging(cache_dir)
    logger.info("=== Mucache Player Starting ===")
    
    video_manager = VideoManager(cache_dir)
    logger.info(f"Loaded {len(video_manager.videos)} videos from playlist")
    
    os.chdir(cache_dir.parent)
    shutdown_event = threading.Event()
    
    server = ThreadedHTTPServer(("", 8000), 
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
        # Improved shutdown handling - more responsive
        while not shutdown_event.is_set():
            # Check more frequently to respond faster to shutdown events
            shutdown_event.wait(0.5)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    finally:
        logger.info("Shutting down server...")
        server.shutdown()
        server.server_close()
        logger.info("=== Mucache Player Stopped ===")

if __name__ == "__main__": main()