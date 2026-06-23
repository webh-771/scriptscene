import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { ArrowLeft, Play, Download, Loader2, Mic, Type, Sparkles, Youtube, Image, AlignCenter } from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const LANGUAGES = [
  { value: 'en', label: 'ENGLISH' },
  { value: 'hi', label: 'HINDI (हिन्दी)' },
  { value: 'es', label: 'SPANISH' },
  { value: 'fr', label: 'FRENCH' },
  { value: 'pt', label: 'PORTUGUESE' },
  { value: 'it', label: 'ITALIAN' },
];

const NICHES = [
  { value: 'scary', label: 'SCARY / HORROR' },
  { value: 'motivation', label: 'MOTIVATION' },
  { value: 'facts', label: 'DID-YOU-KNOW FACTS' },
  { value: 'finance', label: 'MONEY / FINANCE' },
];

// Kokoro voices grouped by language.
const VOICES = {
  en: [
    { value: 'am_michael', label: 'MICHAEL (M, US)' },
    { value: 'am_adam', label: 'ADAM (M, US)' },
    { value: 'am_onyx', label: 'ONYX (M, US)' },
    { value: 'am_puck', label: 'PUCK (M, US)' },
    { value: 'af_heart', label: 'HEART (F, US)' },
    { value: 'af_bella', label: 'BELLA (F, US)' },
    { value: 'af_nicole', label: 'NICOLE (F, US)' },
    { value: 'af_sky', label: 'SKY (F, US)' },
    { value: 'bm_george', label: 'GEORGE (M, UK)' },
    { value: 'bm_lewis', label: 'LEWIS (M, UK)' },
    { value: 'bf_emma', label: 'EMMA (F, UK)' },
    { value: 'bf_isabella', label: 'ISABELLA (F, UK)' },
  ],
  hi: [
    { value: 'hm_omega', label: 'OMEGA (M)' },
    { value: 'hm_psi', label: 'PSI (M)' },
    { value: 'hf_alpha', label: 'ALPHA (F)' },
    { value: 'hf_beta', label: 'BETA (F)' },
  ],
  es: [
    { value: 'em_alex', label: 'ALEX (M)' },
    { value: 'em_santa', label: 'SANTA (M)' },
    { value: 'ef_dora', label: 'DORA (F)' },
  ],
  fr: [
    { value: 'ff_siwis', label: 'SIWIS (F)' },
  ],
  pt: [
    { value: 'pm_alex', label: 'ALEX (M)' },
    { value: 'pm_santa', label: 'SANTA (M)' },
    { value: 'pf_dora', label: 'DORA (F)' },
  ],
  it: [
    { value: 'im_nicola', label: 'NICOLA (M)' },
    { value: 'if_sara', label: 'SARA (F)' },
  ],
};

const BACKGROUNDS = [
  { value: 'broll', label: 'STOCK B-ROLL' },
  { value: 'gameplay', label: 'GAMEPLAY LOOP' },
  { value: 'gradient', label: 'GRADIENT' },
  { value: 'solid', label: 'SOLID COLOR' },
  { value: 'audiogram', label: 'AUDIOGRAM' },
];

const GRADIENTS = ['aurora', 'sunset', 'mint', 'violet', 'noir'];
const ASPECTS = [{ value: '9:16', label: '9:16' }, { value: '1:1', label: '1:1' }, { value: '16:9', label: '16:9' }];
const PRESETS = ['storytime', 'top5', 'didyouknow', 'hottake', 'explainer', 'tutorial', 'mythbuster', 'casestudy'];
const POSITIONS = ['top', 'middle', 'bottom'];
const PILLS = ['none', 'filled', 'outline'];

const Field = ({ label, children }) => (
  <div className="mb-4">
    <label className="text-xs font-black mb-1 block uppercase">{label}</label>
    {children}
  </div>
);
const sel = 'brutal-input w-full p-3 font-bold';

const VideoGeneratorPage = () => {
  const navigate = useNavigate();

  // source
  const [source, setSource] = useState('topic');     // topic | script
  const [topic, setTopic] = useState('');
  const [script, setScript] = useState('');
  const [niche, setNiche] = useState('scary');
  const [language, setLanguage] = useState('en');

  // voice (Kokoro, per language)
  const [voice, setVoice] = useState(VOICES.en[0].value);

  // background
  const [bgType, setBgType] = useState('broll');
  const [bgQuery, setBgQuery] = useState('');
  const [gradient, setGradient] = useState('aurora');
  const [solidColor, setSolidColor] = useState('#101418');

  // format / captions
  const [aspect, setAspect] = useState('9:16');
  const [preset, setPreset] = useState('storytime');
  const [position, setPosition] = useState('middle');
  const [wordsPerChunk, setWordsPerChunk] = useState(3);
  const [capColor, setCapColor] = useState('#FFFFFF');
  const [highlight, setHighlight] = useState('');
  const [fontScale, setFontScale] = useState(1.0);
  const [strokeWidth, setStrokeWidth] = useState(6);
  const [pill, setPill] = useState('none');
  const [uppercase, setUppercase] = useState(true);

  const [music, setMusic] = useState(true);
  const [publishYoutube, setPublishYoutube] = useState(false);

  // job
  const [isGenerating, setIsGenerating] = useState(false);
  const [jobId, setJobId] = useState(null);
  const [progress, setProgress] = useState(0);
  const [stage, setStage] = useState('');
  const [videoUrl, setVideoUrl] = useState(null);
  const [youtubeUrl, setYoutubeUrl] = useState(null);
  const [title, setTitle] = useState('');

  // keep voice valid when language switches
  useEffect(() => { setVoice(VOICES[language][0].value); }, [language]);

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
    } catch (e) { console.error(e); }
  };

  const validSource = () =>
    (source === 'topic' && topic.trim().length >= 3) ||
    (source === 'script' && script.trim().length >= 10);

  const handleGenerate = async () => {
    if (!validSource()) { toast.error('Fill the content source first'); return; }
    setIsGenerating(true); setProgress(0);
    setVideoUrl(null); setYoutubeUrl(null); setTitle('');

    const payload = {
      niche,
      language,
      tts_engine: 'kokoro',
      voice,
      background_type: bgType,
      aspect,
      music,
      publish_youtube: publishYoutube,
      captions: {
        preset, position, words_per_chunk: Number(wordsPerChunk),
        color: capColor, highlight: highlight || null,
        font_scale: Number(fontScale), stroke_width: Number(strokeWidth),
        pill, uppercase,
      },
    };
    if (source === 'topic') payload.topic = topic;
    if (source === 'script') payload.script = script;
    if (bgType === 'broll' || bgType === 'gameplay') payload.background_query = bgQuery || null;
    if (bgType === 'gradient') payload.gradient = gradient;
    if (bgType === 'solid') payload.solid_color = solidColor;

    try {
      const { data } = await axios.post(`${API}/videos/generate`, payload);
      setJobId(data.job_id);
      toast.success('Generation started!');
    } catch (e) {
      setIsGenerating(false);
      toast.error(e.response?.data?.detail || 'Failed to start');
    }
  };

  const previewAspect = aspect === '9:16' ? 'aspect-[9/16] max-w-xs' : aspect === '1:1' ? 'aspect-square max-w-sm' : 'aspect-video max-w-md';

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b-4 border-black bg-[#FFE66D]">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <button onClick={() => navigate('/')} className="brutal-button bg-white text-black px-6 flex items-center">
            <ArrowLeft className="h-5 w-5 mr-2" /> BACK
          </button>
          <h1 className="text-3xl font-black uppercase">STUDIO</h1>
          <div className="w-28" />
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-6 py-12">
        <div className="grid lg:grid-cols-2 gap-8">
          {/* CONTROLS */}
          <motion.div initial={{ opacity: 0, x: -30 }} animate={{ opacity: 1, x: 0 }} className="space-y-6">

            {/* Source */}
            <div className="brutal-card bg-[#4ECDC4] p-6">
              <h3 className="text-xl font-black uppercase flex items-center gap-2 mb-3"><Type className="h-5 w-5" /> CONTENT</h3>
              <div className="flex gap-2 mb-4">
                {['topic', 'script'].map((s) => (
                  <button key={s} onClick={() => setSource(s)}
                    className={`brutal-button flex-1 py-2 text-sm ${source === s ? 'bg-black text-white' : 'bg-white text-black'}`}>
                    {s.toUpperCase()}
                  </button>
                ))}
              </div>
              {source === 'topic' && (
                <input value={topic} onChange={(e) => setTopic(e.target.value)} maxLength={300}
                  placeholder="e.g. a creepy story about the last subway train"
                  className="brutal-input w-full p-4 text-black placeholder:text-gray-600" />
              )}
              {source === 'script' && (
                <textarea value={script} onChange={(e) => setScript(e.target.value)} rows={5}
                  placeholder="Paste your own script verbatim..."
                  className="brutal-input w-full p-4 text-black placeholder:text-gray-600 resize-none" />
              )}
              <div className="grid grid-cols-2 gap-3 mt-3">
                {source !== 'script' && (
                  <Field label="Niche">
                    <select value={niche} onChange={(e) => setNiche(e.target.value)} className={sel}>
                      {NICHES.map((n) => <option key={n.value} value={n.value}>{n.label}</option>)}
                    </select>
                  </Field>
                )}
                <Field label="Language">
                  <select value={language} onChange={(e) => setLanguage(e.target.value)} className={sel}>
                    {LANGUAGES.map((l) => <option key={l.value} value={l.value}>{l.label}</option>)}
                  </select>
                </Field>
              </div>
            </div>

            {/* Voice */}
            <div className="brutal-card bg-[#FF6B6B] p-6">
              <h3 className="text-xl font-black uppercase flex items-center gap-2 mb-3"><Mic className="h-5 w-5" /> VOICE</h3>
              <Field label="Voice (Kokoro)">
                <select value={voice} onChange={(e) => setVoice(e.target.value)} className={sel}>
                  {VOICES[language].map((v) => <option key={v.value} value={v.value}>{v.label}</option>)}
                </select>
              </Field>
            </div>

            {/* Background */}
            <div className="brutal-card bg-[#FFE66D] p-6">
              <h3 className="text-xl font-black uppercase flex items-center gap-2 mb-3"><Image className="h-5 w-5" /> BACKGROUND</h3>
              <Field label="Type">
                <select value={bgType} onChange={(e) => setBgType(e.target.value)} className={sel}>
                  {BACKGROUNDS.map((b) => <option key={b.value} value={b.value}>{b.label}</option>)}
                </select>
              </Field>
              {(bgType === 'broll' || bgType === 'gameplay') && (
                <Field label="Search / keyword (optional)">
                  <input value={bgQuery} onChange={(e) => setBgQuery(e.target.value)}
                    placeholder="e.g. dark forest, city night" className={sel} />
                </Field>
              )}
              {bgType === 'gradient' && (
                <Field label="Gradient">
                  <select value={gradient} onChange={(e) => setGradient(e.target.value)} className={sel}>
                    {GRADIENTS.map((g) => <option key={g} value={g}>{g.toUpperCase()}</option>)}
                  </select>
                </Field>
              )}
              {bgType === 'solid' && (
                <Field label="Color">
                  <input type="color" value={solidColor} onChange={(e) => setSolidColor(e.target.value)}
                    className="brutal-input w-full h-12 p-1" />
                </Field>
              )}
            </div>

            {/* Captions */}
            <div className="brutal-card bg-white p-6">
              <h3 className="text-xl font-black uppercase flex items-center gap-2 mb-3"><AlignCenter className="h-5 w-5" /> CAPTIONS</h3>
              <div className="grid grid-cols-2 gap-3">
                <Field label="Preset">
                  <select value={preset} onChange={(e) => setPreset(e.target.value)} className={sel}>
                    {PRESETS.map((p) => <option key={p} value={p}>{p.toUpperCase()}</option>)}
                  </select>
                </Field>
                <Field label="Position">
                  <select value={position} onChange={(e) => setPosition(e.target.value)} className={sel}>
                    {POSITIONS.map((p) => <option key={p} value={p}>{p.toUpperCase()}</option>)}
                  </select>
                </Field>
                <Field label={`Words / chunk: ${wordsPerChunk}`}>
                  <input type="range" min="1" max="5" value={wordsPerChunk}
                    onChange={(e) => setWordsPerChunk(e.target.value)} className="w-full" />
                </Field>
                <Field label={`Font scale: ${fontScale}`}>
                  <input type="range" min="0.6" max="1.6" step="0.1" value={fontScale}
                    onChange={(e) => setFontScale(e.target.value)} className="w-full" />
                </Field>
                <Field label="Text color">
                  <input type="color" value={capColor} onChange={(e) => setCapColor(e.target.value)} className="brutal-input w-full h-10 p-1" />
                </Field>
                <Field label="Highlight (accent)">
                  <input type="color" value={highlight || '#FF6FB5'} onChange={(e) => setHighlight(e.target.value)} className="brutal-input w-full h-10 p-1" />
                </Field>
                <Field label={`Stroke: ${strokeWidth}`}>
                  <input type="range" min="0" max="16" value={strokeWidth}
                    onChange={(e) => setStrokeWidth(e.target.value)} className="w-full" />
                </Field>
                <Field label="Pill">
                  <select value={pill} onChange={(e) => setPill(e.target.value)} className={sel}>
                    {PILLS.map((p) => <option key={p} value={p}>{p.toUpperCase()}</option>)}
                  </select>
                </Field>
              </div>
              <label className="flex items-center gap-3 cursor-pointer mt-2">
                <input type="checkbox" checked={uppercase} onChange={(e) => setUppercase(e.target.checked)} className="w-5 h-5 border-3 border-black" />
                <span className="font-black uppercase text-sm">UPPERCASE</span>
              </label>
            </div>

            {/* Format + output */}
            <div className="brutal-card bg-[#4ECDC4] p-6">
              <h3 className="text-xl font-black uppercase flex items-center gap-2 mb-3"><Sparkles className="h-5 w-5" /> OUTPUT</h3>
              <Field label="Aspect ratio">
                <div className="flex gap-2">
                  {ASPECTS.map((a) => (
                    <button key={a.value} onClick={() => setAspect(a.value)}
                      className={`brutal-button flex-1 py-2 ${aspect === a.value ? 'bg-black text-white' : 'bg-white text-black'}`}>
                      {a.label}
                    </button>
                  ))}
                </div>
              </Field>
              <label className="flex items-center gap-3 cursor-pointer mt-2">
                <input type="checkbox" checked={music} onChange={(e) => setMusic(e.target.checked)} className="w-5 h-5 border-3 border-black" />
                <span className="font-black uppercase text-sm">BACKGROUND MUSIC</span>
              </label>
              <label className="flex items-center gap-3 cursor-pointer mt-2">
                <input type="checkbox" checked={publishYoutube} onChange={(e) => setPublishYoutube(e.target.checked)} className="w-5 h-5 border-3 border-black" />
                <span className="font-black uppercase text-sm flex items-center gap-2"><Youtube className="h-4 w-4" /> AUTO-UPLOAD TO YOUTUBE</span>
              </label>
            </div>

            <button onClick={handleGenerate} disabled={isGenerating || !validSource()}
              className="brutal-button w-full h-20 bg-black text-white disabled:opacity-50 text-2xl">
              {isGenerating
                ? <><Loader2 className="mr-3 h-7 w-7 animate-spin inline" /> GENERATING...</>
                : <><Play className="mr-3 h-7 w-7 inline" /> GENERATE</>}
            </button>
          </motion.div>

          {/* PREVIEW */}
          <motion.div initial={{ opacity: 0, x: 30 }} animate={{ opacity: 1, x: 0 }} className="space-y-6 lg:sticky lg:top-6 self-start">
            <div className="brutal-card bg-white p-6">
              <h2 className="text-2xl font-black uppercase mb-1">PREVIEW</h2>
              {title && <p className="text-sm font-bold mb-4">{title}</p>}
              <div className={`${previewAspect} mx-auto bg-black border-4 border-black mb-6`}>
                {videoUrl ? (
                  <video controls className="w-full h-full" src={`${BACKEND_URL}${videoUrl}`} />
                ) : (
                  <div className="w-full h-full flex items-center justify-center bg-gray-100">
                    <div className="text-center">
                      <Play className="h-16 w-16 mx-auto mb-4" />
                      <p className="font-bold uppercase">{aspect}</p>
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
          </motion.div>
        </div>
      </div>
    </div>
  );
};

export default VideoGeneratorPage;
