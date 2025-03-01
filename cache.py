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

def download_video(url, cache_dir, manager, logger=None):
    try:
        if url in manager.videos:
            filename = manager.videos[url]['filename']
            file_path = cache_dir / filename
            if file_path.exists():
                if logger: logger.info(f"Using cached video: {filename}")
                return filename, True
            else:
                if logger: logger.warning(f"Cached file not found: {file_path}, downloading fresh copy")
        
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
        if logger: logger.error(f"Error downloading video: {e}")
        else: print(f"Error downloading video: {e}")
        return None, False

html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>Mucache Player</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/react/18.2.0/umd/react.production.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/react-dom/18.2.0/umd/react-dom.production.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/babel-standalone/7.23.5/babel.min.js"></script>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    <style>
        body {font-family:Arial;margin:0;padding:20px}
        .legal-notice {position:fixed;bottom:0;left:0;right:0;background:rgba(0,0,0,0.8);color:white;padding:15px;
        text-align:center;z-index:1000;display:flex;justify-content:center;align-items:center;gap:20px}
        .transform.translate-x-4 {transform:translateX(1rem)}
        .transition-transform {transition-property:transform;transition-timing-function:cubic-bezier(0.4,0,0.2,1);
        transition-duration:150ms}
    </style>
</head>
<body>
    <div id="root"></div>
    <div id="legalNotice" class="legal-notice">
        <span>This software is provided as-is; users are responsible for compliance with applicable laws and rights for downloaded content. | 
        This application stores necessary data locally as required for functionality (GDPR Art. 6(1)(f)).</span>
        <button class="px-4 py-2 bg-blue-500 text-white rounded" onclick="this.parentElement.style.display='none'">OK</button>
    </div>
    <script type="text/babel">
        const VideoPlayer = () => {
            const [videos, setVideos] = React.useState([]);
            const [currentIndex, setCurrentIndex] = React.useState(0);
            const [isLooping, setIsLooping] = React.useState(false);
            const [isContinuous, setIsContinuous] = React.useState(false);
            const [status, setStatus] = React.useState('');
            const [url, setUrl] = React.useState('');
            const videoRef = React.useRef(null);
            
            // Function to open the manual
            const openManual = () => {
                window.open('/manual', '_blank');
            };
            
            // Enhanced shutdown handling
            const sendShutdownRequest = () => {
                try {
                    // Use synchronous XMLHttpRequest to ensure completion before page unload
                    const xhr = new XMLHttpRequest();
                    xhr.open('POST', '/shutdown', false); // false makes this synchronous
                    xhr.send();
                    return "Application shutting down...";
                } catch (e) {
                    console.error("Error during shutdown:", e);
                }
            };
            
            React.useEffect(() => {
                const heartbeatInterval = setInterval(async () => {
                    try { 
                        const response = await fetch('/heartbeat');
                        if (!response.ok) {
                            clearInterval(heartbeatInterval);
                            console.log("Heartbeat failed, server may be down");
                        }
                    } catch { 
                        clearInterval(heartbeatInterval);
                    }
                }, 5000);
                
                // Use beforeunload for shutdown request
                window.addEventListener('beforeunload', sendShutdownRequest);
                
                return () => {
                    clearInterval(heartbeatInterval);
                    window.removeEventListener('beforeunload', sendShutdownRequest);
                };
            }, []);
            
            React.useEffect(() => { loadPlaylist(); }, []);
            
            const loadPlaylist = async () => {
                try {
                    const response = await fetch('/playlist');
                    const data = await response.json();
                    setVideos(data);
                } catch (error) { console.error('Error loading playlist:', error); }
            };
            
            const downloadVideo = async () => {
                if (!url) return;
                setStatus('Processing...');
                try {
                    const response = await fetch(`/download?url=${encodeURIComponent(url)}`);
                    const data = await response.json();
                    if (data.filename) {
                        setStatus(data.fromCache ? '[CACHE] Retrieved' : '[NEW] Downloaded');
                        await loadPlaylist();
                        const newVideoIndex = videos.findIndex(v => v.filename === data.filename);
                        if (newVideoIndex !== -1) { setCurrentIndex(newVideoIndex); }
                        setUrl('');
                        setTimeout(() => setStatus(''), 3000);
                    }
                } catch (error) { setStatus('Error: ' + error.message); }
            };
            
            const playVideo = (filename) => {
                const index = videos.findIndex(v => v.filename === filename);
                if (index !== -1) { setCurrentIndex(index); }
            };
            
            const removeVideo = async (url, e) => {
                e.stopPropagation();
                try {
                    const response = await fetch(`/remove?url=${encodeURIComponent(url)}`, { method: 'POST' });
                    if (response.ok) {
                        const removedIndex = videos.findIndex(v => v.url === url);
                        if (removedIndex === currentIndex && videos.length > 1) {
                            setCurrentIndex(prevIndex => prevIndex >= videos.length - 1 ? 0 : prevIndex);
                        } else if (removedIndex < currentIndex) {
                            setCurrentIndex(prevIndex => prevIndex - 1);
                        }
                        await loadPlaylist();
                    }
                } catch (error) { console.error('Error removing video:', error); }
            };
            
            const handleVideoEnd = () => {
                if (isLooping) {
                    if (videoRef.current) { videoRef.current.currentTime = 0; videoRef.current.play(); }
                } else if (isContinuous && videos.length > 1) { playNextVideo(); }
            };
            
            const playNextVideo = () => {
                if (videos.length > 1) {
                    const nextIndex = (currentIndex + 1) % videos.length;
                    setCurrentIndex(nextIndex);
                }
            };
            
            React.useEffect(() => {
                if (videoRef.current) {
                    videoRef.current.load();
                    videoRef.current.play().catch(e => console.warn('Play error:', e));
                }
            }, [currentIndex]);
            
            return (
                <div className="w-full max-w-6xl mx-auto pb-24">
                    <div className="flex justify-between items-center mb-6">
                        <div className="text-3xl font-bold">Mucache Player</div>
                        <button onClick={openManual} className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition">
                            User Manual
                        </button>
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <div className="md:col-span-2">
                            <div className="bg-white rounded-lg shadow-md p-4 mb-6">
                                <div className="flex flex-col md:flex-row gap-4 mb-4">
                                    <input
                                        type="text" className="flex-grow p-3 border rounded" placeholder="Enter video URL"
                                        value={url} onChange={(e) => setUrl(e.target.value)}
                                        onKeyDown={(e) => e.key === 'Enter' && downloadVideo()}
                                    />
                                    <button onClick={downloadVideo} className="px-6 py-3 bg-blue-600 text-white rounded hover:bg-blue-700 transition">
                                        Download
                                    </button>
                                </div>
                                
                                {status && (<div className="mb-4 p-2 bg-gray-100 rounded text-sm">{status}</div>)}
                                
                                {videos.length > 0 && videos[currentIndex] && (
                                    <div>
                                        <div className="text-xl font-semibold mb-2">{videos[currentIndex].title}</div>
                                        <video ref={videoRef} controls className="w-full rounded" onEnded={handleVideoEnd}>
                                            <source src={`/mucache/${videos[currentIndex].filename}`} type="video/mp4" />
                                            Your browser does not support the video tag.
                                        </video>
                                        
                                        <div className="flex flex-wrap gap-3 mt-4">
                                            <div className="flex items-center gap-2">
                                                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                                    <path d="M17 2l4 4-4 4"></path><path d="M3 11v-1a4 4 0 0 1 4-4h14"></path>
                                                    <path d="M7 22l-4-4 4-4"></path><path d="M21 13v1a4 4 0 0 1-4 4H3"></path>
                                                </svg>
                                                <span>Loop</span>
                                                <label className="inline-flex items-center cursor-pointer">
                                                    <div className="relative">
                                                        <input type="checkbox" className="sr-only" checked={isLooping} onChange={() => setIsLooping(!isLooping)} />
                                                        <div className={`block w-10 h-6 rounded-full ${isLooping ? 'bg-blue-600' : 'bg-gray-300'}`}></div>
                                                        <div className={`absolute left-1 top-1 bg-white w-4 h-4 rounded-full transition-transform ${isLooping ? 'transform translate-x-4' : ''}`}></div>
                                                    </div>
                                                </label>
                                            </div>
                                            
                                            <div className="flex items-center gap-2">
                                                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                                    <path d="M9 18V5l12-2v13"></path>
                                                    <circle cx="6" cy="18" r="3"></circle>
                                                    <circle cx="18" cy="16" r="3"></circle>
                                                </svg>
                                                <span>Continuous Play</span>
                                                <label className={`inline-flex items-center cursor-pointer ${videos.length <= 1 ? 'opacity-50' : ''}`}>
                                                    <div className="relative">
                                                        <input type="checkbox" className="sr-only" checked={isContinuous}
                                                            onChange={() => setIsContinuous(!isContinuous)} disabled={videos.length <= 1} />
                                                        <div className={`block w-10 h-6 rounded-full ${isContinuous ? 'bg-green-600' : 'bg-gray-300'}`}></div>
                                                        <div className={`absolute left-1 top-1 bg-white w-4 h-4 rounded-full transition-transform ${isContinuous ? 'transform translate-x-4' : ''}`}></div>
                                                    </div>
                                                </label>
                                            </div>
                                            
                                            <button onClick={playNextVideo} className="flex items-center gap-2 px-4 py-2 bg-gray-200 hover:bg-gray-300 rounded transition"
                                                disabled={videos.length <= 1}>
                                                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                                    <polygon points="5 4 15 12 5 20 5 4"></polygon>
                                                    <line x1="19" y1="5" x2="19" y2="19"></line>
                                                </svg>
                                                Next
                                            </button>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                        
                        <div className="bg-white rounded-lg shadow-md p-4 h-fit">
                            <div className="text-xl font-semibold mb-4">Playlist</div>
                            {videos.length === 0 ? (
                                <div className="text-gray-500">No videos in playlist</div>
                            ) : (
                                <div className="flex flex-col gap-2 max-h-96 overflow-y-auto">
                                    {videos.map((video, index) => (
                                        <div
                                            key={video.url} onClick={() => playVideo(video.filename)}
                                            className={`p-3 rounded cursor-pointer transition ${
                                                index === currentIndex 
                                                    ? 'bg-blue-100 border-l-4 border-blue-500' 
                                                    : 'hover:bg-gray-100 border-l-4 border-transparent'
                                            }`}
                                        >
                                            <div className="flex justify-between items-center gap-2">
                                                <div className="truncate">{video.title}</div>
                                                <button onClick={(e) => removeVideo(video.url, e)}
                                                    className="px-2 py-1 bg-red-500 hover:bg-red-600 text-white rounded text-xs transition">
                                                    Remove
                                                </button>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            );
        };

        const rootElement = document.getElementById('root');
        const root = ReactDOM.createRoot(rootElement);
        root.render(<VideoPlayer />);
    </script>
</body>
</html>
"""

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

    def do_GET(self):
        routes = {
            '/download': lambda: self.handle_download(),
            '/playlist': lambda: self.send_json(self.video_manager.get_sorted_videos()),
            '/': lambda: self.send_html(html_content),
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

    def send_html(self, content):
        try:
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(content.encode())
        except Exception as e:
            if self.logger: self.logger.error(f"Error sending HTML: {e}")

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