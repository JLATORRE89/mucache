# diagnostic.py - Run this to identify why your application is crashing
import sys
import os
import json
import logging
from pathlib import Path
import traceback

# Global logger for diagnostic output
diagnostic_logger = None

def setup_diagnostic_logging():
    """Set up logging to write to both console and diagnostic.log file."""
    global diagnostic_logger
    
    try:
        # Create cache directory and logs directory
        cache_dir = Path.home() / "Downloads" / "mucache" / "data"
        logs_dir = cache_dir / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up logger
        diagnostic_logger = logging.getLogger('diagnostic')
        diagnostic_logger.setLevel(logging.INFO)
        
        # Clear any existing handlers
        for handler in diagnostic_logger.handlers[:]:
            diagnostic_logger.removeHandler(handler)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_formatter = logging.Formatter('%(message)s')
        console_handler.setFormatter(console_formatter)
        diagnostic_logger.addHandler(console_handler)
        
        # File handler
        file_handler = logging.FileHandler(logs_dir / 'diagnostic.log', mode='w', encoding='utf-8')
        file_formatter = logging.Formatter('%(asctime)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        diagnostic_logger.addHandler(file_handler)
        
        return True
    except Exception as e:
        print(f"Error setting up diagnostic logging: {e}")
        # Fallback to print statements
        return False

def log_message(message):
    """Log message to both console and file."""
    if diagnostic_logger:
        diagnostic_logger.info(message)
    else:
        print(message)

def check_dependencies():
    """Check if all required dependencies are installed."""
    log_message("Checking dependencies...")
    missing_deps = []
    
    try:
        import yt_dlp
        log_message("✓ yt-dlp is installed")
    except ImportError:
        missing_deps.append("yt-dlp")
        log_message("✗ yt-dlp is missing")
    
    try:
        import requests
        log_message("✓ requests is installed")
    except ImportError:
        missing_deps.append("requests")
        log_message("✗ requests is missing")
    
    if missing_deps:
        log_message(f"Missing dependencies: {', '.join(missing_deps)}")
        log_message("Install with: pip install " + " ".join(missing_deps))
        return False
    
    return True

def check_cache_directory():
    """Check if cache directory can be created and is writable."""
    log_message("")
    log_message("Checking cache directory...")
    
    try:
        cache_dir = Path.home() / "Downloads" / "mucache" / "data"
        log_message(f"Cache directory: {cache_dir}")
        
        # Try to create directory
        cache_dir.mkdir(parents=True, exist_ok=True)
        log_message("✓ Cache directory created/exists")
        
        # Test write permissions
        test_file = cache_dir / "test_write.txt"
        test_file.write_text("test")
        test_file.unlink()
        log_message("✓ Directory is writable")
        
        return cache_dir
        
    except Exception as e:
        log_message(f"✗ Cache directory error: {e}")
        return None

def check_port_availability():
    """Check if port 8000 is available."""
    log_message("")
    log_message("Checking port availability...")
    
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', 8000))
        sock.close()
        
        if result == 0:
            log_message("✗ Port 8000 is already in use")
            return False
        else:
            log_message("✓ Port 8000 is available")
            return True
            
    except Exception as e:
        log_message(f"✗ Port check error: {e}")
        return False

def test_logging_setup():
    """Test if logging can be set up properly."""
    log_message("")
    log_message("Testing logging setup...")
    
    try:
        cache_dir = Path.home() / "Downloads" / "mucache" / "data"
        logs_dir = cache_dir / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Test basic logging
        logger = logging.getLogger('test_logger')
        logger.setLevel(logging.INFO)
        
        # Remove any existing handlers
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Add file handler
        handler = logging.FileHandler(logs_dir / 'test_logging.log')
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
        
        # Test logging
        logger.info("Diagnostic logging test successful")
        log_message("✓ Logging setup successful")
        
        return True
        
    except Exception as e:
        log_message(f"✗ Logging setup error: {e}")
        traceback.print_exc()
        return False

def test_imports():
    """Test importing the main modules."""
    log_message("")
    log_message("Testing module imports...")
    
    try:
        # Test if the main cache.py file can be imported (basic syntax check)
        import ast
        
        if os.path.exists('cache.py'):
            with open('cache.py', 'r', encoding='utf-8') as f:
                source = f.read()
            
            # Basic syntax check
            ast.parse(source)
            log_message("✓ cache.py syntax is valid")
        else:
            log_message("✗ cache.py file not found")
            return False
            
    except SyntaxError as e:
        log_message(f"✗ Syntax error in cache.py: {e}")
        return False
    except Exception as e:
        log_message(f"✗ Import test error: {e}")
        return False
    
    return True

def test_minimal_server():
    """Test if a minimal HTTP server can start."""
    log_message("")
    log_message("Testing minimal server...")
    
    try:
        import http.server
        import socketserver
        import threading
        import time
        
        # Try to start a minimal server
        class TestHandler(http.server.SimpleHTTPRequestHandler):
            def log_message(self, format, *args):
                pass  # Suppress output
        
        with socketserver.TCPServer(("", 8000), TestHandler) as httpd:
            log_message("✓ Minimal server can start on port 8000")
            
            # Start server in thread and stop it quickly
            server_thread = threading.Thread(target=httpd.serve_forever)
            server_thread.daemon = True
            server_thread.start()
            
            time.sleep(0.1)  # Brief test
            httpd.shutdown()
            log_message("✓ Server can be started and stopped")
            
        return True
        
    except Exception as e:
        log_message(f"✗ Minimal server test failed: {e}")
        return False

def run_safe_cache_test():
    """Try to run cache.py in a safe way to catch startup errors."""
    log_message("")
    log_message("Testing cache.py startup...")
    
    try:
        import subprocess
        import sys
        
        # Run cache.py with timeout to catch immediate crashes
        result = subprocess.run(
            [sys.executable, 'cache.py', '--test-mode'], 
            capture_output=True, 
            text=True, 
            timeout=5
        )
        
        if result.returncode == 0:
            log_message("✓ cache.py started successfully")
            return True
        else:
            log_message(f"✗ cache.py failed with return code {result.returncode}")
            if result.stderr:
                log_message(f"Error output: {result.stderr}")
            if result.stdout:
                log_message(f"Standard output: {result.stdout}")
            return False
            
    except subprocess.TimeoutExpired:
        log_message("✓ cache.py started (timed out after 5s, which is expected)")
        return True
    except FileNotFoundError:
        log_message("✗ cache.py file not found")
        return False
    except Exception as e:
        log_message(f"✗ Error testing cache.py: {e}")
        return False

def main():
    """Run all diagnostic tests."""
    # Set up logging first
    logging_ok = setup_diagnostic_logging()
    
    log_message("=== Mucache Player Diagnostic Tool ===")
    log_message("")
    
    tests = [
        ("Dependencies", check_dependencies),
        ("Cache Directory", lambda: check_cache_directory() is not None),
        ("Port Availability", check_port_availability),
        ("Logging Setup", test_logging_setup),
        ("Module Imports", test_imports),
        ("Minimal Server", test_minimal_server),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            log_message(f"✗ {test_name} test crashed: {e}")
            traceback.print_exc()
            results[test_name] = False
    
    log_message("")
    log_message("=== DIAGNOSTIC SUMMARY ===")
    all_passed = True
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        log_message(f"{test_name}: {status}")
        if not passed:
            all_passed = False
    
    log_message("")
    if all_passed:
        log_message("✓ All tests passed. The issue might be in the application logic.")
        log_message("Try running: python cache.py")
        log_message("If it still crashes, check the log file in:")
        log_message(f"  {Path.home() / 'Downloads' / 'mucache' / 'data' / 'logs' / 'app.log'}")
    else:
        log_message("✗ Some tests failed. Fix the failed items before running cache.py")
    
    log_message("")
    log_message("If the application starts but crashes during use, check these common issues:")
    log_message("1. Invalid video URLs")
    log_message("2. Network connectivity issues")
    log_message("3. yt-dlp version compatibility (try: pip install --upgrade yt-dlp)")
    log_message("4. Permissions issues in the cache directory")
    log_message("5. Browser compatibility (try a different browser)")
    
    # Final summary for the log file
    log_message("")
    log_message("=== DIAGNOSTIC COMPLETE ===")
    log_message(f"Overall Result: {'PASS' if all_passed else 'FAIL'}")
    log_message(f"Total Tests: {len(tests)}")
    log_message(f"Passed: {sum(1 for passed in results.values() if passed)}")
    log_message(f"Failed: {sum(1 for passed in results.values() if not passed)}")
    
    if diagnostic_logger:
        log_message("")
        log_message(f"Full diagnostic log saved to: {Path.home() / 'Downloads' / 'mucache' / 'data' / 'logs' / 'diagnostic.log'}")

if __name__ == "__main__":
    main()