# Mucache Player Startup Script (PowerShell)
Write-Host "Starting Mucache Player..." -ForegroundColor Green
Write-Host ""

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.6+ from https://python.org" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Checking and installing dependencies..." -ForegroundColor Yellow

# Install dependencies
try {
    if (Test-Path "requirements.txt") {
        Write-Host "Installing dependencies from requirements.txt..." -ForegroundColor Cyan
        python -m pip install --upgrade -r requirements.txt
    } else {
        Write-Host "requirements.txt not found, installing dependencies manually..." -ForegroundColor Cyan
        python -m pip install --upgrade yt-dlp requests
    }

    Write-Host ""
    Write-Host "Dependencies installed successfully!" -ForegroundColor Green
    Write-Host "Starting Mucache Player..." -ForegroundColor Green
    Write-Host ""

    # Start the application
    python cache.py

} catch {
    Write-Host ""
    Write-Host "ERROR: Failed to install dependencies or start application" -ForegroundColor Red
    Write-Host "Error details: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Keep window open if there's an error
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Application ended with an error. Check the messages above." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
}