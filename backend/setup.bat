@echo off
echo ========================================
echo ScriptScene Backend Setup
echo ========================================
echo.

echo [1/4] Creating virtual environment...
python -m venv venv
if %errorlevel% neq 0 (
    echo ERROR: Failed to create virtual environment
    echo Please ensure Python 3.9+ is installed
    pause
    exit /b 1
)

echo [2/4] Activating virtual environment...
call venv\Scripts\activate.bat

echo [3/4] Installing dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo [4/4] Checking environment configuration...
if not exist .env (
    echo WARNING: .env file not found!
    echo Please copy .env.example to .env and add your API keys
    echo.
    echo Creating .env from template...
    copy .env.example .env
    echo.
    echo IMPORTANT: Edit .env file and add your API keys:
    echo   - ELEVENLABS_API_KEY
    echo   - GEMINI_API_KEY
    echo   - PEXELS_API_KEY (optional)
    echo.
)

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Edit .env file and add your API keys
echo 2. Ensure MongoDB is running
echo 3. Run: uvicorn server:app --reload --port 8000
echo.
pause
