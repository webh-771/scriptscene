# 🪟 ScriptScene — Windows from-scratch setup

Fresh PC, nothing installed? This gets you from zero to a running app.

There are two ways:

- **A. Automatic** — run `setup.bat` (installs everything for you).
- **B. Manual** — do each step yourself.

---

## A. Automatic (recommended)

1. Install **Git** if you don't have it (needed just to clone):
   - Download: https://git-scm.com/download/win → run installer (defaults are fine).
   - *Or* download the repo as a ZIP from GitHub and extract it.
2. Get the project onto the PC:
   ```bat
   git clone <your-repo-url> scriptscene
   cd scriptscene
   ```
3. Double-click **`setup.bat`** (or run it in a terminal).
   - It uses **winget** to install Python, Node.js, Git, and ffmpeg if missing,
     then builds the backend venv and frontend packages.
   - If a tool was *just* installed, PATH may not be live in that window —
     close it, open a **new** terminal, and run `setup.bat` again. Safe to re-run.
4. Edit `backend\.env` and set `GROQ_API_KEY` (free from https://console.groq.com).
5. Start it (two terminals):
   ```bat
   REM terminal 1 - backend
   cd backend
   venv\Scripts\activate
   uvicorn app.main:app --reload --port 8000
   ```
   ```bat
   REM terminal 2 - frontend
   cd frontend
   npm start
   ```
6. Browser opens **http://localhost:3000**. Done.

> `setup.bat` needs **winget** (ships with Windows 11 and Windows 10 1809+ via the
> "App Installer" from the Microsoft Store). If winget is missing, use the manual
> steps below.

---

## B. Manual

### 1. Install the toolchain
| Tool | Get it | Check |
|------|--------|-------|
| **Python 3.10+** | https://www.python.org/downloads/ — **tick "Add python.exe to PATH"** in the installer | `python --version` |
| **Node.js LTS (18+)** | https://nodejs.org | `node --version` |
| **Git** | https://git-scm.com/download/win | `git --version` |
| **ffmpeg** | `winget install Gyan.FFmpeg` — or download from https://www.gyan.dev/ffmpeg/builds/ and add its `bin` to PATH | `ffmpeg -version` |

Open a **new** terminal after installing so PATH updates take effect.

### 2. Get the code
```bat
git clone <your-repo-url> scriptscene
cd scriptscene
```

### 3. Backend
```bat
cd backend
python -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
copy .env.example .env
```
Open `backend\.env` and set at minimum `GROQ_API_KEY`. Then run:
```bat
uvicorn app.main:app --reload --port 8000
```
> First run downloads the Whisper caption model (~one-time, a minute or two).

### 4. Frontend (new terminal)
```bat
cd frontend
npm install
echo REACT_APP_BACKEND_URL=http://localhost:8000> .env
npm start
```
Opens **http://localhost:3000**.

---

## Keys (all free, all optional except Groq)
| Var | Where | Needed for |
|-----|-------|-----------|
| `GROQ_API_KEY` | https://console.groq.com | script generation (**required**) |
| `PEXELS_API_KEY` / `PIXABAY_API_KEY` | pexels.com/api · pixabay.com/api | auto b-roll (skip if you drop your own vertical mp4s into `backend\assets\backgrounds\`) |
| `JAMENDO_CLIENT_ID` | devportal.jamendo.com | background music (blank = shared demo key) |
| `YT_CLIENT_ID` / `YT_CLIENT_SECRET` / `YT_REFRESH_TOKEN` | run `python scripts\youtube_auth.py` | YouTube auto-upload |

TTS and captions need **no keys**.

> ⚠️ **Never commit real keys.** `.env` is gitignored; only `.env.example`
> (with blank values) is tracked. Keep it that way.

## YouTube upload (optional, one-time)
1. Google Cloud → enable **YouTube Data API v3**.
2. OAuth consent screen → **External** → **Production**, add scope `youtube.upload`.
3. Create a **Desktop** OAuth client → save JSON as `backend\scripts\client_secret.json`.
4. In the activated backend venv: `python scripts\youtube_auth.py` → paste the printed
   `YT_*` values into `backend\.env`.

## Sanity check
With the backend running:
```bat
curl http://localhost:8000/api/health
```
Expect: `{"status":"ok","groq":true,...}`

## Troubleshooting
- **`'python' is not recognized`** — reinstall Python with "Add to PATH", or open a new terminal.
- **`ffmpeg not found` / render fails** — `ffmpeg -version` must work; install via winget and reopen the terminal.
- **pip build errors on faster-whisper / numpy** — make sure you're on Python 3.10–3.12 (3.13 wheels may lag).
- **PATH not updated after winget install** — close the window, open a fresh one.
