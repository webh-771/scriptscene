# 🚀 ScriptScene Quick Start Guide

## Prerequisites Checklist

Before starting, ensure you have:
- [ ] **Python 3.9+** installed ([Download](https://www.python.org/downloads/))
- [ ] **Node.js 16+** installed ([Download](https://nodejs.org/))
- [ ] **MongoDB** running (local or cloud)
- [ ] **API Keys** ready:
  - ElevenLabs API key ([Get it here](https://elevenlabs.io/))
  - Google Gemini API key ([Get it here](https://makersuite.google.com/app/apikey))
  - Pexels API key - Optional ([Get it here](https://www.pexels.com/api/))

## Setup Instructions

### Step 1: Backend Setup

1. **Navigate to backend folder:**
   ```bash
   cd backend
   ```

2. **Run the setup script:**
   ```bash
   setup.bat
   ```
   This will:
   - Create a Python virtual environment
   - Install all dependencies
   - Create a `.env` file from template

3. **Configure your API keys:**
   - Open `backend\.env` in a text editor
   - Add your API keys:
     ```env
     ELEVENLABS_API_KEY=your_actual_key_here
     GEMINI_API_KEY=your_actual_key_here
     PEXELS_API_KEY=your_actual_key_here
     ```

4. **Start the backend server:**
   ```bash
   start.bat
   ```
   - Server will run at: `http://localhost:8000`
   - API docs at: `http://localhost:8000/docs`

### Step 2: Frontend Setup

1. **Open a new terminal and navigate to frontend folder:**
   ```bash
   cd frontend
   ```

2. **Run the setup script:**
   ```bash
   setup.bat
   ```
   This will install all Node.js dependencies.

3. **Start the frontend server:**
   ```bash
   start.bat
   ```
   - App will open at: `http://localhost:3000`

## Verification

### Test the Application

1. **Open your browser** to `http://localhost:3000`
2. **Navigate to** "Generate Video" page
3. **Enter a test script:**
   ```
   Welcome to ScriptScene! This is an amazing AI-powered video generation platform that transforms your text into engaging videos.
   ```
4. **Click "Generate Video"**
5. **Monitor progress** - you should see:
   - ✅ Generating voiceover...
   - ✅ Fetching stock media...
   - ✅ Creating video...
   - ✅ Video generated successfully!

## Troubleshooting

### Backend Issues

**Error: "Module not found"**
- Solution: Run `setup.bat` again in the backend folder

**Error: "MongoDB connection failed"**
- Solution: Ensure MongoDB is running
- For local MongoDB: `mongod --dbpath C:\data\db`
- Or use MongoDB Atlas (cloud)

**Error: "401 Unauthorized" from ElevenLabs**
- Solution: Check your `ELEVENLABS_API_KEY` in `.env` file
- Ensure you're using a valid API key

### Frontend Issues

**Error: "Cannot connect to backend"**
- Solution: Ensure backend server is running on port 8000
- Check `http://localhost:8000/api/` returns a response

**Error: "Dependencies not installed"**
- Solution: Run `setup.bat` in the frontend folder

## What Was Fixed

### ElevenLabs API Update
The application has been updated to use the **`eleven_turbo_v2_5`** model instead of the deprecated `eleven_monolingual_v1` model. This new model:
- ✅ Works with free tier accounts
- ✅ Provides faster generation
- ✅ Offers better quality output

## Next Steps

Once everything is running:
1. **Explore the Video Library** to see your generated videos
2. **Experiment with different scripts** and settings
3. **Try different video formats** (vertical vs horizontal)
4. **Add background music** to your videos

## Need Help?

- Check the [README.md](../README.md) for detailed documentation
- Review API docs at `http://localhost:8000/docs`
- Ensure all API keys are correctly configured in `.env`

---

**Happy video creating! 🎬**
