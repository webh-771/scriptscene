# ScriptScene 🎬

**Free, faceless YouTube Shorts generator.** Give one topic → the app writes an
original script, narrates it, adds word-by-word captions over a background video,
renders a vertical 9:16 Short, and (optionally) uploads it straight to YouTube.

Built to run on a **$0 stack** with copyright-clean, monetizable output.

## Pipeline

```
topic + niche
  → Groq LLM writes original script + title + hashtags   (free)
  → edge-tts neural voiceover (gTTS fallback)             (free, no key)
  → faster-whisper word-level caption timing              (free, local)
  → background: local file OR royalty-free b-roll         (free)
  → moviepy stitch (bg + karaoke captions + audio)        → 9:16 mp4
  → optional: YouTube Data API upload as a Short          (free, quota-limited)
```

## Why original content

Scraped Reddit text + copyrighted gameplay = flagged "unoriginal" → demonetized.
This generates **original** scripts and uses **royalty-free / your own** backgrounds,
so output is eligible for monetization on YouTube/TikTok/Reels.

## Architecture (modular)

```
backend/
  app/
    main.py            FastAPI app + router wiring
    config.py          all env + paths (single source of truth)
    models.py          pydantic schemas
    db.py              SQLite job store (no external DB)
    api/               thin routes: videos.py, publish.py
    services/
      story.py         Groq script/title/hashtag generation
      tts.py           edge-tts (+gTTS fallback)
      captions.py      faster-whisper timing + caption render
      background.py    local files + Pexels/Pixabay b-roll
      compose.py       moviepy stitch → mp4
      pipeline.py      orchestrates the stages
      publishers/
        youtube.py     Shorts upload (OAuth refresh token)
  assets/{fonts,backgrounds,music}/
  scripts/youtube_auth.py   one-time YouTube token helper
frontend/              React UI (topic form + library)
```

## Setup

### Backend
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # fill in keys (see below)
uvicorn app.main:app --reload --port 8000
```

Requires **ffmpeg** on PATH (`brew install ffmpeg`).

### Keys (all free)
| Var | Where | Required? |
|-----|-------|-----------|
| `GROQ_API_KEY` | console.groq.com | yes (script gen) |
| `PEXELS_API_KEY` / `PIXABAY_API_KEY` | pexels.com/api · pixabay.com/api | optional (skip if you supply local backgrounds) |
| `YT_*` | run `python scripts/youtube_auth.py` | only for auto-upload |

TTS and captions need **no keys**.

### Backgrounds
Drop any vertical video(s) into `backend/assets/backgrounds/` to use your own
loops, **or** leave empty and set a Pexels/Pixabay key to auto-fetch b-roll.
Drop `.mp3` files into `assets/music/` for background music.

### Frontend
```bash
cd frontend
npm install
echo "REACT_APP_BACKEND_URL=http://localhost:8000" > .env
npm start
```

## API

- `POST /api/videos/generate` — `{topic, niche, voice?, music?, publish_youtube?}`
- `GET  /api/videos/{job_id}/status`
- `GET  /api/videos/{job_id}/download`
- `GET  /api/videos` — list jobs
- `POST /api/publish/{job_id}/youtube` — upload an existing video
- `GET  /api/health` — which integrations are configured

## YouTube upload notes

- A 9:16 video ≤3 min with `#Shorts` is auto-classified as a Short.
- `videos.insert` costs **1600 quota units**; default daily quota 10,000 →
  **~6 uploads/day**. Request a quota increase for more.
- Set the OAuth consent screen to **Production** to avoid 7-day token expiry.
