# ScriptScene 🎬

**AI-Powered Video Generation Platform**

ScriptScene is a full-stack web application that transforms text scripts into engaging videos using AI. Simply provide a script, and the platform automatically generates voiceovers, fetches relevant stock media, adds subtitles, and produces a professional video ready for social media.

## ✨ Features

- **🎙️ AI Voiceover Generation** - High-quality text-to-speech using ElevenLabs
- **🖼️ Automated Media Sourcing** - Intelligent keyword extraction and stock image fetching from Pexels
- **📝 Subtitle Generation** - Automatic subtitle timing and placement
- **🎵 Background Music** - Optional background music with automatic mixing
- **📱 Multiple Formats** - Support for vertical (9:16) and horizontal (16:9) video formats
- **📚 Video Library** - Manage and download all your generated videos
- **⚡ Real-time Progress** - Live status updates during video generation
- **🎨 Modern UI** - Beautiful dark-mode interface with glassmorphism effects

## 🏗️ Architecture

### Backend (FastAPI)
- **`server.py`** - Main FastAPI application with CORS and MongoDB integration
- **`video_generator.py`** - Core video generation logic with AI integrations
- **`media_service.py`** - Media file management and serving
- **`music_service.py`** - Background music handling

### Frontend (React)
- **`HomePage.js`** - Landing page with feature showcase
- **`VideoGeneratorPage.js`** - Main video creation interface
- **`VideoLibraryPage.js`** - Video project management
- Built with **shadcn/ui** components and **Tailwind CSS**
- Smooth animations using **Framer Motion**

## 🚀 Getting Started

### Prerequisites

- **Node.js** (v16 or higher)
- **Python** (v3.9 or higher)
- **MongoDB** (local or cloud instance)
- **API Keys**:
  - ElevenLabs API key
  - Google Gemini API key
  - Pexels API key (optional, for stock images)

### Installation

#### 1. Clone the Repository
```bash
git clone <repository-url>
cd scriptscene
```

#### 2. Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
```

**Configure `.env` file:**
```env
MONGO_URL=mongodb://localhost:27017
DB_NAME=scriptscene
ELEVENLABS_API_KEY=your_elevenlabs_key
GEMINI_API_KEY=your_gemini_key
PEXELS_API_KEY=your_pexels_key
CORS_ORIGINS=http://localhost:3000
```

#### 3. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install
# or
yarn install
```

### Running the Application

#### Start Backend Server
```bash
cd backend
uvicorn server:app --reload --port 8000
```

The API will be available at `http://localhost:8000`

#### Start Frontend Development Server
```bash
cd frontend
npm start
# or
yarn start
```

The application will open at `http://localhost:3000`

## 📖 API Documentation

Once the backend is running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Key Endpoints

#### Video Generation
- `POST /api/video/generate` - Start video generation job
- `GET /api/video/status/{job_id}` - Check generation status
- `GET /api/video/download/{job_id}` - Download completed video
- `GET /api/video/projects` - List all video projects

#### Media Management
- `POST /api/media/upload` - Upload custom media files
- `GET /api/media/list` - List available media

#### Music
- `GET /api/music/list` - List available background music tracks

## 🎨 Design System

ScriptScene follows the **"Performance Pro"** design archetype with:

- **Typography**: Space Grotesk (headings) + Manrope (body)
- **Color Scheme**: Dark mode with indigo/violet accents
- **Visual Effects**: Glassmorphism, neon glows, smooth gradients
- **Layout**: Bento grids with generous spacing
- **Animations**: Micro-interactions using Framer Motion

See [`design_guidelines.json`](design_guidelines.json) for complete design specifications.

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest backend_test.py
```

### Frontend Tests
```bash
cd frontend
npm test
```

Test results are logged in `test_result.md` following the testing protocol.

## 📁 Project Structure

```
scriptscene/
├── backend/
│   ├── server.py              # FastAPI main application
│   ├── video_generator.py     # Video generation service
│   ├── media_service.py       # Media management
│   ├── music_service.py       # Music handling
│   ├── requirements.txt       # Python dependencies
│   ├── audio_files/           # Generated voiceovers
│   ├── generated_videos/      # Output videos
│   └── temp_media/            # Temporary processing files
├── frontend/
│   ├── src/
│   │   ├── pages/             # React pages
│   │   ├── components/        # UI components
│   │   ├── hooks/             # Custom React hooks
│   │   └── lib/               # Utilities
│   ├── public/                # Static assets
│   └── package.json           # Node dependencies
├── design_guidelines.json     # Design system specifications
├── test_result.md            # Testing protocol and results
└── README.md                 # This file
```

## 🔧 Configuration

### Video Generation Settings

- **Video Formats**: Vertical (1080x1920) or Horizontal (1920x1080)
- **Frame Rate**: 30 FPS
- **Video Codec**: H.264 (libx264)
- **Audio Codec**: AAC
- **Bitrate**: 5000k
- **Image Duration**: 0.5-1 second per image (dynamic based on script length)

### Voice Options

Currently using ElevenLabs with the "Adam" voice (ID: `pNInz6obpgDQGcFmaJgB`). Additional voices can be configured in `video_generator.py`.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- **ElevenLabs** - AI voice generation
- **Google Gemini** - AI content analysis
- **Pexels** - Stock imagery
- **shadcn/ui** - UI component library
- **MoviePy** - Video processing

## 📧 Support

For issues and questions, please open an issue on GitHub.

---

**Built with ❤️ using AI-powered tools**
