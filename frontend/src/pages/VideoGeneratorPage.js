import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Progress } from '@/components/ui/progress';
import { toast } from 'sonner';
import { ArrowLeft, Play, Download, Loader2, Music, Mic, Type } from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const VideoGeneratorPage = () => {
  const navigate = useNavigate();
  const [script, setScript] = useState('');
  const [voiceStyle, setVoiceStyle] = useState('Puck');
  const [selectedMusic, setSelectedMusic] = useState('');
  const [includeSubtitles, setIncludeSubtitles] = useState(true);
  const [videoFormat, setVideoFormat] = useState('vertical');
  const [musicTracks, setMusicTracks] = useState([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [jobId, setJobId] = useState(null);
  const [progress, setProgress] = useState(0);
  const [statusMessage, setStatusMessage] = useState('');
  const [videoUrl, setVideoUrl] = useState(null);

  useEffect(() => {
    fetchMusicTracks();
  }, []);

  useEffect(() => {
    if (jobId && isGenerating) {
      const interval = setInterval(() => {
        checkVideoStatus();
      }, 2000);
      return () => clearInterval(interval);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [jobId, isGenerating]);

  const fetchMusicTracks = async () => {
    try {
      const response = await axios.get(`${API}/music/list`);
      setMusicTracks(response.data.tracks);
      if (response.data.tracks.length > 0) {
        setSelectedMusic(response.data.tracks[0].url);
      }
    } catch (error) {
      console.error('Failed to fetch music:', error);
    }
  };

  const checkVideoStatus = async () => {
    try {
      const response = await axios.get(`${API}/video/status/${jobId}`);
      const status = response.data;

      setProgress(status.progress);
      setStatusMessage(status.message);

      if (status.status === 'completed') {
        setIsGenerating(false);
        setVideoUrl(status.video_url);
        toast.success('Video generated successfully!');
      } else if (status.status === 'failed') {
        setIsGenerating(false);
        toast.error(status.error || 'Video generation failed');
      }
    } catch (error) {
      console.error('Failed to check status:', error);
    }
  };

  const handleGenerate = async () => {
    if (!script.trim()) {
      toast.error('Please enter a script');
      return;
    }

    if (script.length < 10) {
      toast.error('Script must be at least 10 characters');
      return;
    }

    setIsGenerating(true);
    setProgress(0);
    setVideoUrl(null);

    try {
      const response = await axios.post(`${API}/video/generate`, {
        script: script,
        music_url: selectedMusic,
        voice_style: voiceStyle,
        include_subtitles: includeSubtitles,
        video_format: videoFormat
      });

      setJobId(response.data.job_id);
      toast.success('Video generation started!');
    } catch (error) {
      setIsGenerating(false);
      toast.error(error.response?.data?.detail || 'Failed to start video generation');
    }
  };

  const handleDownload = () => {
    if (videoUrl) {
      window.open(`${BACKEND_URL}${videoUrl}`, '_blank');
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b-4 border-black bg-[#FFE66D]">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <Button
            data-testid="back-button"
            onClick={() => navigate('/')}
            className="brutal-button bg-white text-black hover:bg-white px-6"
          >
            <ArrowLeft className="h-5 w-5 mr-2" />
            BACK
          </Button>
          <h1 className="text-3xl font-black uppercase">VIDEO GENERATOR</h1>
          <div className="w-28" />
        </div>
      </header>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-6 py-12">
        <div className="grid lg:grid-cols-2 gap-8">
          {/* Left: Input Panel */}
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            animate={{ opacity: 1, x: 0 }}
            className="space-y-6"
          >
            {/* Script Input */}
            <div className="brutal-card bg-[#4ECDC4] p-6">
              <div className="mb-4">
                <h3 className="text-2xl font-black uppercase flex items-center gap-2">
                  <Type className="h-6 w-6" />
                  YOUR SCRIPT
                </h3>
                <p className="text-sm font-bold mt-1">WRITE YOUR VIDEO SCRIPT</p>
              </div>
              <div>
                <textarea
                  data-testid="script-input"
                  placeholder="Enter your script here... Example: Create viral content now! AI makes video creation super easy and fast!"
                  value={script}
                  onChange={(e) => setScript(e.target.value)}
                  rows={12}
                  maxLength={5000}
                  className="brutal-input w-full p-4 resize-none text-black placeholder:text-gray-600"
                />
                <div className="mt-2 text-sm font-bold">
                  {script.length} / 5000 CHARACTERS
                </div>
              </div>
            </div>

            {/* Voice Settings */}
            <div className="brutal-card bg-[#FF6B6B] p-6">
              <div className="mb-4">
                <h3 className="text-2xl font-black uppercase flex items-center gap-2">
                  <Mic className="h-6 w-6" />
                  VOICE SETTINGS
                </h3>
              </div>
              <div>
                <label className="text-sm font-black mb-2 block uppercase">Voice Style</label>
                <select
                  data-testid="voice-select"
                  value={voiceStyle}
                  onChange={(e) => setVoiceStyle(e.target.value)}
                  className="brutal-input w-full p-3 font-bold"
                >
                  <option value="Joanna">Joanna</option>
                  <option value="Matthew">Matthew</option>
                  <option value="Salli">Salli</option>
                </select>
              </div>
            </div>

            {/* Music Selection */}
            <div className="brutal-card bg-[#FFE66D] p-6">
              <div className="mb-4">
                <h3 className="text-2xl font-black uppercase flex items-center gap-2">
                  <Music className="h-6 w-6" />
                  MUSIC
                </h3>
              </div>
              <div>
                <select
                  data-testid="music-select"
                  value={selectedMusic}
                  onChange={(e) => setSelectedMusic(e.target.value)}
                  className="brutal-input w-full p-3 font-bold"
                >
                  {musicTracks.map((track) => (
                    <option key={track.id} value={track.url}>
                      {track.title.toUpperCase()} - {track.genre.toUpperCase()}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Video Format */}
            <div className="brutal-card bg-[#FF6B6B] p-6">
              <div className="mb-4">
                <h3 className="text-2xl font-black uppercase flex items-center gap-2">
                  <Play className="h-6 w-6" />
                  FORMAT
                </h3>
              </div>
              <div>
                <select
                  data-testid="format-select"
                  value={videoFormat}
                  onChange={(e) => setVideoFormat(e.target.value)}
                  className="brutal-input w-full p-3 font-bold"
                >
                  <option value="vertical">VERTICAL (9:16) - YOUTUBE SHORTS</option>
                  <option value="horizontal">HORIZONTAL (16:9) - STANDARD</option>
                </select>
              </div>
            </div>

            {/* Subtitle Toggle */}
            <div className="brutal-card bg-white p-6">
              <label className="flex items-center gap-4 cursor-pointer">
                <input
                  data-testid="subtitles-toggle"
                  type="checkbox"
                  checked={includeSubtitles}
                  onChange={(e) => setIncludeSubtitles(e.target.checked)}
                  className="w-6 h-6 border-3 border-black"
                />
                <span className="text-xl font-black uppercase">INCLUDE SUBTITLES</span>
              </label>
            </div>

            {/* Generate Button */}
            <button
              data-testid="generate-button"
              onClick={handleGenerate}
              disabled={isGenerating || !script.trim()}
              className="brutal-button w-full h-20 bg-black text-white hover:bg-black disabled:opacity-50 disabled:cursor-not-allowed text-2xl"
            >
              {isGenerating ? (
                <>
                  <Loader2 className="mr-3 h-7 w-7 animate-spin inline" />
                  GENERATING...
                </>
              ) : (
                <>
                  <Play className="mr-3 h-7 w-7 inline" />
                  GENERATE VIDEO NOW
                </>
              )}
            </button>
          </motion.div>

          {/* Right: Preview Panel */}
          <motion.div
            initial={{ opacity: 0, x: 30 }}
            animate={{ opacity: 1, x: 0 }}
            className="space-y-6"
          >
            <div className="brutal-card bg-white p-6">
              <div className="mb-4">
                <h2 className="text-2xl font-black uppercase">VIDEO PREVIEW</h2>
                <p className="text-sm font-bold mt-1">YOUR GENERATED VIDEO APPEARS HERE</p>
              </div>
              <div>
                {/* Video Player */}
                <div className={`${videoFormat === 'vertical' ? 'aspect-[9/16] max-w-md mx-auto' : 'aspect-video'} bg-black border-4 border-black box-shadow-[8px_8px_0_0_black] mb-6`}>
                  {videoUrl ? (
                    <video
                      data-testid="video-player"
                      controls
                      className="w-full h-full"
                      src={`${BACKEND_URL}${videoUrl}`}
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center bg-gray-100">
                      <div className="text-center">
                        <Play className="h-16 w-16 mx-auto mb-4" />
                        <p className="font-bold uppercase">VIDEO PREVIEW</p>
                        <p className="text-sm font-bold mt-2">
                          {videoFormat === 'vertical' ? 'VERTICAL (9:16)' : 'HORIZONTAL (16:9)'}
                        </p>
                      </div>
                    </div>
                  )}
                </div>

                {/* Progress */}
                {isGenerating && (
                  <div data-testid="progress-container" className="space-y-3 brutal-card bg-[#FFE66D] p-4">
                    <div className="w-full bg-white border-3 border-black h-8 relative overflow-hidden">
                      <div
                        className="h-full bg-black transition-all duration-300"
                        style={{ width: `${progress}%` }}
                      />
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="font-black uppercase text-sm">{statusMessage}</span>
                      <span className="font-black text-lg">{progress}%</span>
                    </div>
                  </div>
                )}

                {/* Download Button */}
                {videoUrl && (
                  <button
                    data-testid="download-button"
                    onClick={handleDownload}
                    className="brutal-button w-full h-14 bg-[#4ECDC4] text-black hover:bg-[#4ECDC4] mt-4 text-xl"
                  >
                    <Download className="mr-2 h-6 w-6 inline" />
                    DOWNLOAD VIDEO
                  </button>
                )}
              </div>
            </div>

            {/* Tips Card */}
            <div className="brutal-card bg-[#FF6B6B] p-6">
              <h3 className="text-xl font-black mb-4 uppercase">TIPS FOR BEST RESULTS</h3>
              <ul className="space-y-2 text-sm font-bold">
                <li>• KEEP SENTENCES CLEAR</li>
                <li>• USE PUNCTUATION FOR PAUSES</li>
                <li>• 100-500 WORDS WORKS BEST</li>
                <li>• GENERATION TAKES 1-3 MIN</li>
                <li>• VERTICAL = SHORTS/TIKTOK</li>
                <li>• HORIZONTAL = YOUTUBE</li>
              </ul>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
};

export default VideoGeneratorPage;