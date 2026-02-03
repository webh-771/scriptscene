@echo off
echo ========================================
echo ScriptScene Frontend Setup
echo ========================================
echo.

echo [1/2] Installing dependencies...
call npm install
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    echo Please ensure Node.js is installed
    pause
    exit /b 1
)

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Ensure backend server is running on http://localhost:8000
echo 2. Run: npm start
echo.
pause
