# 🚀 ScriptScene Quick Start

Generate a free, faceless YouTube Short from a single topic.

## Prerequisites
- [ ] **Python 3.10+**
- [ ] **Node.js 16+**
- [ ] **ffmpeg** on PATH — `brew install ffmpeg`
- [ ] **Groq API key** (free) — https://console.groq.com
- [ ] *(optional)* Pexels/Pixabay key for auto b-roll, OR your own background videos
- [ ] *(optional)* Google Cloud project for YouTube auto-upload

No MongoDB. No ElevenLabs. No paid keys.

## 1. Backend
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # set GROQ_API_KEY (minimum)
uvicorn app.main:app --reload --port 8000
```
First run downloads the whisper model (~one-time).

Backgrounds: drop vertical mp4s into `assets/backgrounds/`, **or** set
`PEXELS_API_KEY` / `PIXABAY_API_KEY` in `.env` to auto-fetch.

## 2. Frontend
```bash
cd frontend
npm install
echo "REACT_APP_BACKEND_URL=http://localhost:8000" > .env
npm start            # opens http://localhost:3000
```

## 3. Generate
1. Open the app → **Shorts Generator**
2. Type a **topic**, pick a **niche** + **voice**
3. *(optional)* toggle **Auto-upload to YouTube**
4. Hit **Generate** — watch progress, download or view on YouTube

## YouTube upload (optional, one-time)
1. Google Cloud → enable **YouTube Data API v3**
2. OAuth consent screen → **External** → **Production**, add scope `youtube.upload`
3. Create **Desktop** OAuth client → save JSON as `backend/scripts/client_secret.json`
4. `python scripts/youtube_auth.py` → paste printed `YT_*` values into `.env`

Quota: ~6 uploads/day on the default 10,000 units.

## Sanity check
```bash
curl localhost:8000/api/health
# {"status":"ok","groq":true,"youtube":false,"broll":true}
```
