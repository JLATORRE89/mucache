@echo off
echo Starting Mucache Player...
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.6+ from https://python.org
    pause
    exit /b 1
)

echo Checking and installing dependencies...

REM Check if requirements.txt exists
if exist requirements.txt (
    echo Installing dependencies from requirements.txt...
    python -m pip install --upgrade -r requirements.txt
) else (
    echo requirements.txt not found, installing dependencies manually...
    python -m pip install --upgrade yt-dlp requests
)

echo.
echo Dependencies installed successfully!
echo Starting Mucache Player...
echo.

REM Start the application
python cache.py

REM Keep window open if there's an error
if errorlevel 1 (
    echo.
    echo Application ended with an error. Check the messages above.
    pause
)