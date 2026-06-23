import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { ArrowLeft, Play, Download, Loader2, Mic, Type, Sparkles, Youtube } from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const NICHES = [
  { value: 'scary', label: 'SCARY / HORROR' },
  { value: 'motivation', label: 'MOTIVATION' },
  { value: 'facts', label: 'DID-YOU-KNOW FACTS' },
  { value: 'finance', label: 'MONEY / FINANCE' },
];

const VOICES = [
  { value: 'en-US-AndrewNeural', label: 'ANDREW (M, NATURAL)' },
  { value: 'en-US-AvaNeural', label: 'AVA (F, NATURAL)' },
  { value: 'en-US-EmmaNeural', label: 'EMMA (F, NATURAL)' },
  { value: 'en-US-BrianNeural', label: 'BRIAN (M, NATURAL)' },
  { value: 'en-GB-RyanNeural', label: 'RYAN (M, UK)' },
];

const VideoGeneratorPage = () => {
  const navigate = useNavigate();
  const [topic, setTopic] = useState('');
  const [niche, setNiche] = useState('scary');
  const [voice, setVoice] = useState('en-US-AndrewNeural');
  const [music, setMusic] = useState(true);
  const [publishYoutube, setPublishYoutube] = useState(false);

  const [isGenerating, setIsGenerating] = useState(false);
  const [jobId, setJobId] = useState(null);
  const [progress, setProgress] = useState(0);
  const [stage, setStage] = useState('');
  const [videoUrl, setVideoUrl] = useState(null);
  const [youtubeUrl, setYoutubeUrl] = useState(null);
  const [title, setTitle] = useState('');

  useEffect(() => {
    if (jobId && isGenerating) {
      const interval = setInterval(checkStatus, 2000);
      return () => clearInterval(interval);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [jobId, isGenerating]);

  const checkStatus = async () => {
    try {
      const { data } = await axios.get(`${API}/videos/${jobId}/status`);
      setProgress(data.progress || 0);
      setStage((data.stage || '').toUpperCase());
      if (data.title) setTitle(data.title);

      if (data.status === 'done') {
        setIsGenerating(false);
        setVideoUrl(data.video_url);
        setYoutubeUrl(data.youtube_url);
        toast.success('Video ready!');
      } else if (data.status === 'error') {
        setIsGenerating(false);
        toast.error(data.error || 'Generation failed');
      }
    } catch (e) {
      console.error('status check failed', e);
    }
  };

  const handleGenerate = async () => {
    if (topic.trim().length < 3) {
      toast.error('Enter a topic (3+ chars)');
      return;
    }
    setIsGenerating(true);
    setProgress(0);
    setVideoUrl(null);
    setYoutubeUrl(null);
    setTitle('');
    try {
      const { data } = await axios.post(`${API}/videos/generate`, {
        topic,
        niche,
        voice,
        music,
        publish_youtube: publishYoutube,
      });
      setJobId(data.job_id);
      toast.success('Generation started!');
    } catch (e) {
      setIsGenerating(false);
      toast.error(e.response?.data?.detail || 'Failed to start');
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b-4 border-black bg-[#FFE66D]">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <button onClick={() => navigate('/')} className="brutal-button bg-white text-black px-6 flex items-center">
            <ArrowLeft className="h-5 w-5 mr-2" /> BACK
          </button>
          <h1 className="text-3xl font-black uppercase">SHORTS GENERATOR</h1>
          <div className="w-28" />
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-6 py-12">
        <div className="grid lg:grid-cols-2 gap-8">
          {/* Inputs */}
          <motion.div initial={{ opacity: 0, x: -30 }} animate={{ opacity: 1, x: 0 }} className="space-y-6">
            <div className="brutal-card bg-[#4ECDC4] p-6">
              <h3 className="text-2xl font-black uppercase flex items-center gap-2 mb-1">
                <Type className="h-6 w-6" /> TOPIC
              </h3>
              <p className="text-sm font-bold mb-4">ONE LINE — THE AI WRITES THE REST</p>
              <input
                data-testid="topic-input"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                maxLength={300}
                placeholder="e.g. a creepy story about the last subway train"
                className="brutal-input w-full p-4 text-black placeholder:text-gray-600"
              />
            </div>

            <div className="brutal-card bg-[#FFE66D] p-6">
              <h3 className="text-xl font-black uppercase flex items-center gap-2 mb-3">
                <Sparkles className="h-5 w-5" /> NICHE
              </h3>
              <select value={niche} onChange={(e) => setNiche(e.target.value)} className="brutal-input w-full p-3 font-bold">
                {NICHES.map((n) => <option key={n.value} value={n.value}>{n.label}</option>)}
              </select>
            </div>

            <div className="brutal-card bg-[#FF6B6B] p-6">
              <h3 className="text-xl font-black uppercase flex items-center gap-2 mb-3">
                <Mic className="h-5 w-5" /> VOICE
              </h3>
              <select value={voice} onChange={(e) => setVoice(e.target.value)} className="brutal-input w-full p-3 font-bold">
                {VOICES.map((v) => <option key={v.value} value={v.value}>{v.label}</option>)}
              </select>
            </div>

            <div className="brutal-card bg-white p-6 space-y-4">
              <label className="flex items-center gap-4 cursor-pointer">
                <input type="checkbox" checked={music} onChange={(e) => setMusic(e.target.checked)} className="w-6 h-6 border-3 border-black" />
                <span className="text-lg font-black uppercase">BACKGROUND MUSIC</span>
              </label>
              <label className="flex items-center gap-4 cursor-pointer">
                <input data-testid="publish-toggle" type="checkbox" checked={publishYoutube} onChange={(e) => setPublishYoutube(e.target.checked)} className="w-6 h-6 border-3 border-black" />
                <span className="text-lg font-black uppercase flex items-center gap-2"><Youtube className="h-5 w-5" /> AUTO-UPLOAD TO YOUTUBE</span>
              </label>
            </div>

            <button
              data-testid="generate-button"
              onClick={handleGenerate}
              disabled={isGenerating || topic.trim().length < 3}
              className="brutal-button w-full h-20 bg-black text-white disabled:opacity-50 text-2xl"
            >
              {isGenerating
                ? <><Loader2 className="mr-3 h-7 w-7 animate-spin inline" /> GENERATING...</>
                : <><Play className="mr-3 h-7 w-7 inline" /> GENERATE SHORT</>}
            </button>
          </motion.div>

          {/* Preview */}
          <motion.div initial={{ opacity: 0, x: 30 }} animate={{ opacity: 1, x: 0 }} className="space-y-6">
            <div className="brutal-card bg-white p-6">
              <h2 className="text-2xl font-black uppercase mb-1">PREVIEW</h2>
              {title && <p className="text-sm font-bold mb-4">{title}</p>}
              <div className="aspect-[9/16] max-w-md mx-auto bg-black border-4 border-black mb-6">
                {videoUrl ? (
                  <video data-testid="video-player" controls className="w-full h-full" src={`${BACKEND_URL}${videoUrl}`} />
                ) : (
                  <div className="w-full h-full flex items-center justify-center bg-gray-100">
                    <div className="text-center">
                      <Play className="h-16 w-16 mx-auto mb-4" />
                      <p className="font-bold uppercase">9:16 SHORT</p>
                    </div>
                  </div>
                )}
              </div>

              {isGenerating && (
                <div className="space-y-3 brutal-card bg-[#FFE66D] p-4">
                  <div className="w-full bg-white border-3 border-black h-8 overflow-hidden">
                    <div className="h-full bg-black transition-all duration-300" style={{ width: `${progress}%` }} />
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="font-black uppercase text-sm">{stage}</span>
                    <span className="font-black text-lg">{progress}%</span>
                  </div>
                </div>
              )}

              {videoUrl && (
                <button onClick={() => window.open(`${BACKEND_URL}${videoUrl}`, '_blank')} className="brutal-button w-full h-14 bg-[#4ECDC4] text-black mt-4 text-xl">
                  <Download className="mr-2 h-6 w-6 inline" /> DOWNLOAD
                </button>
              )}
              {youtubeUrl && (
                <a href={youtubeUrl} target="_blank" rel="noreferrer" className="brutal-button w-full h-14 bg-[#FF6B6B] text-black mt-4 text-xl flex items-center justify-center">
                  <Youtube className="mr-2 h-6 w-6 inline" /> VIEW ON YOUTUBE
                </a>
              )}
            </div>

            <div className="brutal-card bg-[#FF6B6B] p-6">
              <h3 className="text-xl font-black mb-4 uppercase">HOW IT WORKS</h3>
              <ul className="space-y-2 text-sm font-bold">
                <li>• AI WRITES ORIGINAL SCRIPT (COPYRIGHT-CLEAN)</li>
                <li>• FREE NEURAL VOICEOVER</li>
                <li>• WORD-BY-WORD CAPTIONS</li>
                <li>• ROYALTY-FREE / LOCAL BACKGROUND</li>
                <li>• AUTO 9:16 FOR SHORTS</li>
                <li>• OPTIONAL 1-CLICK YOUTUBE UPLOAD</li>
              </ul>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
};

export default VideoGeneratorPage;
