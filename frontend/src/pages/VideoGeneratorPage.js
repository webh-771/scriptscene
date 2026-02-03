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
      <header className="border-b border-white/10 bg-black/40 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <Button
            data-testid="back-button"
            variant="ghost"
            onClick={() => navigate('/')}
            className="flex items-center gap-2"
          >
            <ArrowLeft className="h-4 w-4" />
            Back
          </Button>
          <h1 className="text-2xl font-heading font-bold">Video Generator</h1>
          <div className="w-20" />
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
            <Card className="glass border-white/10">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Type className="h-5 w-5 text-primary" />
                  Your Script
                </CardTitle>
                <CardDescription>Write or paste the script for your video</CardDescription>
              </CardHeader>
              <CardContent>
                <Textarea
                  data-testid="script-input"
                  placeholder="Enter your script here... For example: Welcome to our amazing product demo. Today we'll show you how to create stunning videos in minutes. Our AI-powered platform makes video creation simple and fast."
                  value={script}
                  onChange={(e) => setScript(e.target.value)}
                  rows={12}
                  maxLength={5000}
                  className="bg-black/20 border-white/10 focus:border-primary/50 resize-none"
                />
                <div className="mt-2 text-xs text-gray-400">
                  {script.length} / 5000 characters
                </div>
              </CardContent>
            </Card>

            {/* Voice Settings */}
            <Card className="glass border-white/10">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Mic className="h-5 w-5 text-primary" />
                  Voice Settings
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">Voice Style</label>
                  <Select value={voiceStyle} onValueChange={setVoiceStyle}>
                    <SelectTrigger data-testid="voice-select" className="bg-black/20 border-white/10">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Puck">Puck (Default)</SelectItem>
                      <SelectItem value="Charon">Charon (Deep)</SelectItem>
                      <SelectItem value="Kore">Kore (Alternative)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </CardContent>
            </Card>

            {/* Music Selection */}
            <Card className="glass border-white/10">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Music className="h-5 w-5 text-primary" />
                  Background Music
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Select value={selectedMusic} onValueChange={setSelectedMusic}>
                  <SelectTrigger data-testid="music-select" className="bg-black/20 border-white/10">
                    <SelectValue placeholder="Select music" />
                  </SelectTrigger>
                  <SelectContent>
                    {musicTracks.map((track) => (
                      <SelectItem key={track.id} value={track.url}>
                        {track.title} - {track.genre}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </CardContent>
            </Card>

            {/* Video Format Selection */}
            <Card className="glass border-white/10">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Play className="h-5 w-5 text-primary" />
                  Video Format
                </CardTitle>
                <CardDescription>Choose format for your video</CardDescription>
              </CardHeader>
              <CardContent>
                <Select value={videoFormat} onValueChange={setVideoFormat}>
                  <SelectTrigger data-testid="format-select" className="bg-black/20 border-white/10">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="vertical">Vertical (9:16) - YouTube Shorts, TikTok, Reels</SelectItem>
                    <SelectItem value="horizontal">Horizontal (16:9) - Standard YouTube</SelectItem>
                  </SelectContent>
                </Select>
              </CardContent>
            </Card>

            {/* Subtitle Toggle */}
            <Card className="glass border-white/10">
              <CardContent className="pt-6">
                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    data-testid="subtitles-toggle"
                    type="checkbox"
                    checked={includeSubtitles}
                    onChange={(e) => setIncludeSubtitles(e.target.checked)}
                    className="w-5 h-5 rounded border-white/10 text-primary focus:ring-primary"
                  />
                  <span className="text-sm font-medium">Include Subtitles</span>
                </label>
              </CardContent>
            </Card>

            {/* Generate Button */}
            <Button
              data-testid="generate-button"
              onClick={handleGenerate}
              disabled={isGenerating || !script.trim()}
              className="w-full h-14 rounded-full bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white font-semibold shadow-lg neon-glow"
            >
              {isGenerating ? (
                <>
                  <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                  <Play className="mr-2 h-5 w-5" />
                  Generate Video
                </>
              )}
            </Button>
          </motion.div>

          {/* Right: Preview Panel */}
          <motion.div
            initial={{ opacity: 0, x: 30 }}
            animate={{ opacity: 1, x: 0 }}
            className="space-y-6"
          >
            <Card className="glass border-white/10">
              <CardHeader>
                <CardTitle>Video Preview</CardTitle>
                <CardDescription>Your generated video will appear here</CardDescription>
              </CardHeader>
              <CardContent>
                {/* Video Player */}
                <div className={`${videoFormat === 'vertical' ? 'aspect-[9/16] max-w-md mx-auto' : 'aspect-video'} bg-black rounded-lg overflow-hidden mb-6`}>
                  {videoUrl ? (
                    <video
                      data-testid="video-player"
                      controls
                      className="w-full h-full"
                      src={`${BACKEND_URL}${videoUrl}`}
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center bg-black/60">
                      <div className="text-center text-gray-500">
                        <Play className="h-16 w-16 mx-auto mb-4 opacity-50" />
                        <p>Video preview will appear here</p>
                        <p className="text-sm mt-2">
                          Format: {videoFormat === 'vertical' ? 'Vertical (9:16)' : 'Horizontal (16:9)'}
                        </p>
                      </div>
                    </div>
                  )}
                </div>

                {/* Progress */}
                {isGenerating && (
                  <div data-testid="progress-container" className="space-y-3">
                    <Progress value={progress} className="h-2" />
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-gray-400">{statusMessage}</span>
                      <span className="text-primary font-medium">{progress}%</span>
                    </div>
                  </div>
                )}

                {/* Download Button */}
                {videoUrl && (
                  <Button
                    data-testid="download-button"
                    onClick={handleDownload}
                    className="w-full h-12 rounded-full mt-4"
                    variant="outline"
                  >
                    <Download className="mr-2 h-4 w-4" />
                    Download Video
                  </Button>
                )}
              </CardContent>
            </Card>

            {/* Tips Card */}
            <Card className="glass border-white/10">
              <CardHeader>
                <CardTitle className="text-lg">Tips for Best Results</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2 text-sm text-gray-400">
                  <li>• Keep sentences clear and concise</li>
                  <li>• Use punctuation for natural pauses</li>
                  <li>• Scripts between 100-500 words work best</li>
                  <li>• Video generation takes 1-3 minutes</li>
                  <li>• Choose music that matches your content tone</li>
                </ul>
              </CardContent>
            </Card>
          </motion.div>
        </div>
      </div>
    </div>
  );
};

export default VideoGeneratorPage;