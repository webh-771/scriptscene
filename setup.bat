@echo off
REM ============================================================
REM  ScriptScene - one-shot Windows setup
REM  Installs Python, Node, Git, ffmpeg (via winget) then
REM  builds the backend venv + frontend node_modules.
REM
REM  Usage:  double-click, or run  setup.bat  in a terminal.
REM  Re-run safe: skips anything already installed.
REM ============================================================
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo.
echo ============================================
echo   ScriptScene setup  (%cd%)
echo ============================================
echo.

REM ---- 0. winget present? -------------------------------------------------
where winget >nul 2>&1
if errorlevel 1 (
  echo [!] winget not found. Install "App Installer" from the Microsoft Store,
  echo     or upgrade to Windows 10 1809+ / Windows 11, then re-run this script.
  pause
  exit /b 1
)

REM ---- 1. system dependencies --------------------------------------------
call :ensure python  "Python.Python.3.12"
call :ensure node    "OpenJS.NodeJS.LTS"
call :ensure git     "Git.Git"
call :ensure ffmpeg  "Gyan.FFmpeg"

echo.
echo [i] If any tool was just installed, its PATH may not be live in THIS
echo     window. If the steps below fail with "not recognized", close this
echo     window, open a NEW terminal, and run setup.bat again.
echo.

REM ---- 2. backend ---------------------------------------------------------
echo === Backend ===
cd backend
if not exist venv (
  echo [i] Creating Python virtualenv...
  python -m venv venv
)
call venv\Scripts\activate.bat
echo [i] Upgrading pip...
python -m pip install --upgrade pip
echo [i] Installing Python packages (this can take a few minutes)...
pip install -r requirements.txt
if not exist .env (
  copy .env.example .env >nul
  echo [i] Created backend\.env  -- open it and set GROQ_API_KEY (minimum).
) else (
  echo [i] backend\.env already exists, leaving it.
)
call venv\Scripts\deactivate.bat
cd ..

REM ---- 3. frontend --------------------------------------------------------
echo.
echo === Frontend ===
cd frontend
echo [i] Installing npm packages...
call npm install
if not exist .env (
  echo REACT_APP_BACKEND_URL=http://localhost:8000> .env
  echo [i] Created frontend\.env
) else (
  echo [i] frontend\.env already exists, leaving it.
)
cd ..

echo.
echo ============================================
echo   Done.
echo ============================================
echo.
echo Next:
echo   1. Edit  backend\.env   and set GROQ_API_KEY  (free: console.groq.com)
echo   2. Start backend:
echo        cd backend ^&^& venv\Scripts\activate ^&^& uvicorn app.main:app --reload --port 8000
echo   3. Start frontend (new terminal):
echo        cd frontend ^&^& npm start
echo   4. Open  http://localhost:3000
echo.
pause
exit /b 0

REM ---- helper: ensure a command exists, else winget install ---------------
:ensure
where %1 >nul 2>&1
if errorlevel 1 (
  echo [i] Installing %1 ...
  winget install --id %2 -e --accept-source-agreements --accept-package-agreements
) else (
  echo [ok] %1 already installed.
)
exit /b 0
