@echo off
echo ========================================
echo   Marine Engine AI Chatbot - Setup
echo ========================================

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed!
    echo Please install Python 3.9+ from https://python.org
    pause
    exit /b 1
)

echo [1/4] Python found!

:: Create virtual environment if not exists
if not exist "venv" (
    echo [2/4] Creating virtual environment...
    python -m venv venv
) else (
    echo [2/4] Virtual environment already exists.
)

:: Activate virtual environment
echo [3/4] Activating virtual environment...
call venv\Scripts\activate

:: Install requirements
echo [4/4] Installing dependencies...
pip install -r requirements.txt --quiet

echo.
echo ========================================
echo   Starting Chatbot...
echo ========================================
echo.
echo Access the chatbot at: http://localhost:8000
echo Press CTRL+C to stop the server
echo.

:: Run the chatbot
cd src\templates
python botmarch11.py

pause
