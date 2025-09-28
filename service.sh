#!/bin/bash

# Mucache Player Service Management Script
# Usage: ./service.sh {start|stop|restart|status|logs|debug|backup|restore|list-backups}
#
# Manages the Mucache Player application:
# - Video caching and download server
# - Web interface for video management
# - Debug and logging capabilities

# =============================================================================
# CONFIGURATION
# =============================================================================

# Application identification
APP_NAME="mucache-player"
APP_DESCRIPTION="Mucache Player - Local video caching and playback application"

# Directories and files
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="$APP_DIR/data"
PID_DIR="$DATA_DIR/logs"
LOG_DIR="$DATA_DIR/logs"
CACHE_DIR="$DATA_DIR"

# PID files
MUCACHE_PID="$PID_DIR/mucache_server.pid"

# Log files
SERVICE_LOG="$LOG_DIR/service.log"
MUCACHE_LOG="$LOG_DIR/app.log"
DEBUG_LOG="$LOG_DIR/debug.log"

# Python virtual environment (optional)
VIRTUAL_ENV_NAME="venv"
VENV_PATH="$APP_DIR/$VIRTUAL_ENV_NAME"

# Server configuration
MUCACHE_SCRIPT="cache.py"

# Ports
MUCACHE_PORT=8000

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Ensure required directories exist
mkdir -p "$LOG_DIR" "$CACHE_DIR"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$SERVICE_LOG"
}

# Check if process is running
is_running() {
    local pid_file="$1"
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0
        else
            # PID file exists but process is dead
            rm -f "$pid_file"
            return 1
        fi
    fi
    return 1
}

# Get process status
get_process_status() {
    local service_name="$1"
    local pid_file="$2"

    if is_running "$pid_file"; then
        local pid=$(cat "$pid_file")
        echo -e "${GREEN}Running${NC} (PID: $pid)"
        return 0
    else
        echo -e "${RED}Stopped${NC}"
        return 1
    fi
}

# Check Python dependencies
check_dependencies() {
    echo "Checking Python dependencies..."

    # Check for Python
    if ! command -v python3 >/dev/null 2>&1 && ! command -v python >/dev/null 2>&1; then
        echo -e "${RED}Error: Python not found${NC}"
        echo "Please install Python 3.6+ from https://python.org"
        return 1
    fi

    # Use python3 if available, otherwise python
    local python_cmd="python3"
    if ! command -v python3 >/dev/null 2>&1; then
        python_cmd="python"
    fi

    # Check for required modules
    local missing_deps=()

    if ! $python_cmd -c "import yt_dlp" 2>/dev/null; then
        missing_deps+=("yt-dlp")
    fi

    if ! $python_cmd -c "import requests" 2>/dev/null; then
        missing_deps+=("requests")
    fi

    if [ ${#missing_deps[@]} -gt 0 ]; then
        echo -e "${YELLOW}Missing dependencies: ${missing_deps[*]}${NC}"
        echo "Installing dependencies..."

        for dep in "${missing_deps[@]}"; do
            echo "Installing $dep..."
            $python_cmd -m pip install --upgrade "$dep"
        done

        echo -e "${GREEN}Dependencies installed successfully${NC}"
    else
        echo -e "${GREEN}All dependencies satisfied${NC}"
    fi

    return 0
}

# Activate virtual environment if it exists
activate_venv() {
    if [ -d "$VENV_PATH" ]; then
        echo "Activating virtual environment..."
        source "$VENV_PATH/bin/activate"
        return 0
    else
        echo "No virtual environment found - using system Python"
        return 0
    fi
}

# Start Mucache server
start_server() {
    echo "Starting Mucache Player server..."

    if is_running "$MUCACHE_PID"; then
        echo -e "${YELLOW}Mucache Player is already running${NC}"
        return 0
    fi

    # Change to app directory
    cd "$APP_DIR" || {
        echo -e "${RED}Error: Cannot change to app directory${NC}"
        return 1
    }

    # Check dependencies
    if ! check_dependencies; then
        return 1
    fi

    # Activate virtual environment if available
    activate_venv

    # Determine Python command
    local python_cmd="python3"
    if ! command -v python3 >/dev/null 2>&1; then
        python_cmd="python"
    fi

    # Start the server
    echo "Starting server on port $MUCACHE_PORT..."
    nohup $python_cmd "$MUCACHE_SCRIPT" > "$MUCACHE_LOG" 2>&1 < /dev/null &
    local server_pid=$!
    echo "$server_pid" > "$MUCACHE_PID"

    # Wait a moment and check if it's still running
    sleep 3
    if is_running "$MUCACHE_PID"; then
        log "Mucache Player started successfully (PID: $server_pid)"
        echo -e "${GREEN}Mucache Player started successfully${NC}"
        return 0
    else
        log "Failed to start Mucache Player"
        echo -e "${RED}Failed to start Mucache Player${NC}"
        echo "Check log: $MUCACHE_LOG"
        return 1
    fi
}

# Stop Mucache server
stop_server() {
    if ! is_running "$MUCACHE_PID"; then
        echo -e "${YELLOW}Mucache Player is not running${NC}"
        return 0
    fi

    local pid=$(cat "$MUCACHE_PID")
    echo "Stopping Mucache Player (PID: $pid)..."
    log "Stopping Mucache Player (PID: $pid)"

    # Try graceful shutdown first
    kill -TERM "$pid" 2>/dev/null

    # Wait up to 10 seconds for graceful shutdown
    for i in {1..10}; do
        if ! is_running "$MUCACHE_PID"; then
            log "Mucache Player stopped gracefully"
            echo -e "${GREEN}Mucache Player stopped successfully${NC}"
            return 0
        fi
        sleep 1
    done

    # Force kill if graceful shutdown failed
    echo "Graceful shutdown failed, forcing stop..."
    kill -KILL "$pid" 2>/dev/null
    rm -f "$MUCACHE_PID"

    sleep 2
    if ! is_running "$MUCACHE_PID"; then
        log "Mucache Player force stopped"
        echo -e "${GREEN}Mucache Player stopped (forced)${NC}"
        return 0
    else
        log "Failed to stop Mucache Player"
        echo -e "${RED}Failed to stop Mucache Player${NC}"
        return 1
    fi
}

# =============================================================================
# MAIN FUNCTIONS
# =============================================================================

# Start service
start() {
    echo "Starting Mucache Player..."
    log "Starting Mucache Player"

    if start_server; then
        echo ""
        echo -e "${GREEN}🎬 Mucache Player started successfully!${NC}"
        echo ""
        echo "🏠 LOCAL ACCESS:"
        echo "   Web Interface: http://localhost:$MUCACHE_PORT"
        echo ""
        echo "🌐 REMOTE ACCESS (share with others):"
        local local_ip=$(hostname -I | awk '{print $1}' 2>/dev/null || ip route get 1 | awk '{print $NF;exit}' 2>/dev/null || echo "Your-IP-Address")
        echo "   Share this URL: http://$local_ip:$MUCACHE_PORT"
        echo ""
        echo "📁 CACHE LOCATION:"
        echo "   Videos: $CACHE_DIR"
        echo "   Logs: $LOG_DIR"
        echo ""
        echo "🔧 CONTROLS:"
        echo "   Status: ./service.sh status"
        echo "   Logs: ./service.sh logs"
        echo "   Debug: ./service.sh debug"
        echo "   Stop: ./service.sh stop"
        echo ""
        return 0
    else
        echo -e "${RED}Failed to start Mucache Player${NC}"
        return 1
    fi
}

# Stop service
stop() {
    echo "Stopping Mucache Player..."
    log "Stopping Mucache Player"

    stop_server
    echo -e "${GREEN}Mucache Player stopped${NC}"
}

# Restart service
restart() {
    echo "Restarting Mucache Player..."
    stop
    sleep 3
    start
}

# Show status
status() {
    echo "=== Mucache Player Service Status ==="
    echo ""

    echo -n "Mucache Server: "
    get_process_status "Mucache Server" "$MUCACHE_PID"

    echo ""

    # Show port status
    echo "=== Port Status ==="
    echo "Checking server connectivity..."

    if command -v curl >/dev/null 2>&1; then
        if curl -s http://localhost:$MUCACHE_PORT >/dev/null 2>&1; then
            echo -e "Mucache Server ($MUCACHE_PORT): ${GREEN}Responding${NC}"
        else
            echo -e "Mucache Server ($MUCACHE_PORT): ${RED}Not responding${NC}"
        fi
    elif command -v wget >/dev/null 2>&1; then
        if wget -q --spider http://localhost:$MUCACHE_PORT 2>/dev/null; then
            echo -e "Mucache Server ($MUCACHE_PORT): ${GREEN}Responding${NC}"
        else
            echo -e "Mucache Server ($MUCACHE_PORT): ${RED}Not responding${NC}"
        fi
    else
        echo "curl/wget not available - cannot check port status"
    fi

    # Show cache status
    echo ""
    echo "=== Cache Status ==="
    if [ -d "$CACHE_DIR" ]; then
        local video_count=$(find "$CACHE_DIR" -name "*.mp4" -o -name "*.webm" -o -name "*.mkv" 2>/dev/null | wc -l)
        local cache_size=$(du -sh "$CACHE_DIR" 2>/dev/null | cut -f1)
        echo "Video files: $video_count"
        echo "Cache size: $cache_size"

        if [ -f "$CACHE_DIR/playlist.json" ]; then
            echo "Playlist: Available"
        else
            echo "Playlist: Not created yet"
        fi
    else
        echo "Cache directory not found"
    fi

    # Show recent activity
    if is_running "$MUCACHE_PID"; then
        echo ""
        echo "=== Recent Activity ==="
        if [ -f "$MUCACHE_LOG" ]; then
            echo "Application Log (last 5 lines):"
            tail -5 "$MUCACHE_LOG" 2>/dev/null | sed 's/^/  /' || echo "  No recent activity"
        fi
    fi
}

# Show logs
logs() {
    local service="$2"
    local lines="${3:-30}"

    case "$service" in
        app|mucache|server)
            echo "=== Mucache Application Log ==="
            tail -"$lines" "$MUCACHE_LOG" 2>/dev/null || echo "No log found"
            ;;
        debug)
            echo "=== Debug Log ==="
            tail -"$lines" "$DEBUG_LOG" 2>/dev/null || echo "No debug log found"
            ;;
        service)
            echo "=== Service Management Log ==="
            tail -"$lines" "$SERVICE_LOG" 2>/dev/null || echo "No log found"
            ;;
        follow|tail)
            echo "=== Following Application Log (Ctrl+C to stop) ==="
            tail -f "$MUCACHE_LOG" 2>/dev/null || echo "No log found"
            ;;
        *)
            echo "=== All Recent Logs ==="
            echo ""
            echo "Service Management:"
            tail -10 "$SERVICE_LOG" 2>/dev/null | sed 's/^/  /' || echo "  No log found"

            echo ""
            echo "Application:"
            tail -15 "$MUCACHE_LOG" 2>/dev/null | sed 's/^/  /' || echo "  No log found"

            if [ -f "$DEBUG_LOG" ]; then
                echo ""
                echo "Debug (last session):"
                tail -10 "$DEBUG_LOG" 2>/dev/null | sed 's/^/  /' || echo "  No debug log found"
            fi
            ;;
    esac
}

# Debug mode - enhanced logging and troubleshooting
debug() {
    echo "=== Mucache Player Debug Information ==="
    echo ""

    echo "System Information:"
    echo "  OS: $(uname -s) $(uname -r)"
    echo "  Architecture: $(uname -m)"
    echo "  Date: $(date)"
    echo ""

    echo "Python Information:"
    if command -v python3 >/dev/null 2>&1; then
        echo "  Python3: $(python3 --version)"
        echo "  Python3 Path: $(which python3)"
    fi
    if command -v python >/dev/null 2>&1; then
        echo "  Python: $(python --version)"
        echo "  Python Path: $(which python)"
    fi
    echo ""

    echo "Dependencies:"
    local python_cmd="python3"
    if ! command -v python3 >/dev/null 2>&1; then
        python_cmd="python"
    fi

    if $python_cmd -c "import yt_dlp; print('  yt-dlp:', yt_dlp.version.__version__)" 2>/dev/null; then
        :
    else
        echo "  yt-dlp: NOT INSTALLED"
    fi

    if $python_cmd -c "import requests; print('  requests:', requests.__version__)" 2>/dev/null; then
        :
    else
        echo "  requests: NOT INSTALLED"
    fi
    echo ""

    echo "Application Status:"
    echo "  App Directory: $APP_DIR"
    echo "  Cache Directory: $CACHE_DIR"
    echo "  Log Directory: $LOG_DIR"
    echo "  Port: $MUCACHE_PORT"
    echo ""

    if is_running "$MUCACHE_PID"; then
        local pid=$(cat "$MUCACHE_PID")
        echo "  Server Status: Running (PID: $pid)"
        echo "  Memory Usage: $(ps -o pid,ppid,%mem,cmd -p $pid 2>/dev/null | tail -1)"
    else
        echo "  Server Status: Stopped"
    fi
    echo ""

    echo "Network Status:"
    if command -v netstat >/dev/null 2>&1; then
        if netstat -ln | grep ":$MUCACHE_PORT " >/dev/null 2>&1; then
            echo "  Port $MUCACHE_PORT: Listening"
        else
            echo "  Port $MUCACHE_PORT: Not listening"
        fi
    else
        echo "  netstat not available"
    fi
    echo ""

    echo "Recent Errors:"
    if [ -f "$MUCACHE_LOG" ]; then
        grep -i "error\|exception\|failed" "$MUCACHE_LOG" | tail -5 | sed 's/^/  /' || echo "  No recent errors found"
    else
        echo "  No application log found"
    fi
}

# Create backup
backup() {
    local backup_dir="$APP_DIR/backups"
    local backup_file="mucache_backup_$(date +%Y%m%d_%H%M%S).tar.gz"

    mkdir -p "$backup_dir"

    echo "Creating backup..."

    # Backup playlist, settings, and logs (but not video files due to size)
    cd "$APP_DIR" || return 1

    tar -czf "$backup_dir/$backup_file" \
        --exclude="data/*.mp4" \
        --exclude="data/*.webm" \
        --exclude="data/*.mkv" \
        --exclude="data/*.avi" \
        data/ \
        *.py \
        *.html \
        *.bat \
        *.ps1 \
        requirements.txt \
        README.md 2>/dev/null

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Backup created: $backup_dir/$backup_file${NC}"
        echo "Note: Video files excluded due to size - only settings and logs backed up"
        log "Backup created: $backup_file"
    else
        echo -e "${RED}Backup failed${NC}"
        return 1
    fi
}

# List backups
list_backups() {
    local backup_dir="$APP_DIR/backups"

    if [ -d "$backup_dir" ]; then
        echo "Available backups:"
        ls -lah "$backup_dir"/mucache_backup_*.tar.gz 2>/dev/null | while read -r line; do
            echo "  $line"
        done
    else
        echo "No backups found"
    fi
}

# Restore backup
restore() {
    local backup_file="$2"
    local backup_dir="$APP_DIR/backups"

    if [ -z "$backup_file" ]; then
        echo "Usage: $0 restore <backup_file>"
        echo ""
        list_backups
        return 1
    fi

    if [ ! -f "$backup_dir/$backup_file" ]; then
        echo -e "${RED}Backup file not found: $backup_dir/$backup_file${NC}"
        return 1
    fi

    echo "Restoring from backup: $backup_file"
    echo -e "${YELLOW}Warning: This will overwrite current settings and logs${NC}"
    read -p "Continue? (y/N): " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Stop service if running
        if is_running "$MUCACHE_PID"; then
            echo "Stopping service..."
            stop_server
        fi

        # Extract backup
        cd "$APP_DIR" || return 1
        tar -xzf "$backup_dir/$backup_file"

        if [ $? -eq 0 ]; then
            echo -e "${GREEN}Restore completed successfully${NC}"
            log "Restored from backup: $backup_file"
        else
            echo -e "${RED}Restore failed${NC}"
            return 1
        fi
    else
        echo "Restore cancelled"
    fi
}

# =============================================================================
# MAIN SCRIPT LOGIC
# =============================================================================

case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    status)
        status
        ;;
    logs)
        logs "$@"
        ;;
    debug)
        debug
        ;;
    backup)
        backup
        ;;
    restore)
        restore "$@"
        ;;
    list-backups)
        list_backups
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs|debug|backup|restore|list-backups}"
        echo ""
        echo "$APP_DESCRIPTION"
        echo ""
        echo "Commands:"
        echo "  start              - Start Mucache Player server"
        echo "  stop               - Stop Mucache Player server"
        echo "  restart            - Restart Mucache Player server"
        echo "  status             - Show service status and cache information"
        echo "  logs [type] [lines] - Show logs (app|debug|service|follow|all)"
        echo "  debug              - Show detailed debug information"
        echo "  backup             - Create backup of settings and logs"
        echo "  restore <file>     - Restore from backup"
        echo "  list-backups       - List available backups"
        echo ""
        echo "Examples:"
        echo "  $0 start           # Start the server"
        echo "  $0 logs app 50     # Show last 50 app log lines"
        echo "  $0 logs follow     # Follow live logs"
        echo "  $0 debug           # Show debug information"
        echo ""
        echo "Configuration:"
        echo "  App Directory: $APP_DIR"
        echo "  Cache Directory: $CACHE_DIR"
        echo "  Port: $MUCACHE_PORT"
        echo "  Log Directory: $LOG_DIR"
        echo ""
        echo "URLs:"
        echo "  Local: http://localhost:$MUCACHE_PORT"
        echo "  Remote: http://[your-ip]:$MUCACHE_PORT"
        exit 1
        ;;
esac

exit $?