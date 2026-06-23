import { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { ArrowLeft, Download, Youtube, Loader2, Sparkles, X, Trash2 } from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const STATUS_COLOR = {
  done: 'bg-[#4ECDC4]', running: 'bg-[#FFE66D]', queued: 'bg-white', error: 'bg-[#FF6B6B]',
};

const JobsPage = () => {
  const navigate = useNavigate();
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [publishJob, setPublishJob] = useState(null);   // job being published (modal)

  const fetchJobs = useCallback(async () => {
    try {
      const { data } = await axios.get(`${API}/videos`);
      setJobs(data);
    } catch (e) { console.error(e); } finally { setLoading(false); }
  }, []);

  useEffect(() => {
    fetchJobs();
    const t = setInterval(fetchJobs, 3000);   // live updates for running/uploading jobs
    return () => clearInterval(t);
  }, [fetchJobs]);

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b-4 border-black bg-[#FFE66D]">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <button onClick={() => navigate('/')} className="brutal-button bg-white text-black px-6 flex items-center">
            <ArrowLeft className="h-5 w-5 mr-2" /> BACK
          </button>
          <h1 className="text-3xl font-black uppercase">JOBS</h1>
          <button onClick={() => navigate('/generate')} className="brutal-button bg-black text-white px-6">
            + NEW
          </button>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-6 py-10">
        {loading ? (
          <p className="font-black uppercase">Loading…</p>
        ) : jobs.length === 0 ? (
          <div className="text-center py-20">
            <p className="text-2xl font-black uppercase mb-4">No jobs yet</p>
            <button onClick={() => navigate('/generate')} className="brutal-button bg-black text-white px-8 h-14 text-xl">
              CREATE ONE
            </button>
          </div>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {jobs.map((j) => (
              <JobCard key={j.job_id} job={j} onPublish={() => setPublishJob(j)} onDelete={fetchJobs} />
            ))}
          </div>
        )}
      </div>

      {publishJob && (
        <PublishModal job={publishJob} onClose={() => setPublishJob(null)} onDone={fetchJobs} />
      )}
    </div>
  );
};

const JobCard = ({ job, onPublish, onDelete }) => {
  const done = job.status === 'done';
  const up = job.upload_status;
  const remove = async () => {
    if (!window.confirm('Delete this job and its video?')) return;
    try { await axios.delete(`${API}/videos/${job.job_id}`); toast.success('Deleted'); onDelete(); }
    catch (e) { toast.error('Delete failed'); }
  };
  return (
    <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}
      className="brutal-card bg-white p-4">
      <div className="flex items-center justify-between mb-2">
        <span className={`px-2 py-1 text-xs font-black uppercase border-2 border-black ${STATUS_COLOR[job.status] || 'bg-white'}`}>
          {job.status}{job.status === 'running' ? ` ${job.progress}%` : ''}
        </span>
        <div className="flex items-center gap-2">
          {up && <span className="text-xs font-black uppercase">{up === 'uploaded' ? '✓ ON YT' : `YT: ${up}`}</span>}
          <button onClick={remove} title="Delete" className="border-2 border-black bg-[#FF6B6B] p-1 hover:bg-[#ff4f4f]">
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      </div>
      <p className="font-black text-sm mb-3 line-clamp-2">{job.title || job.topic || 'Untitled'}</p>

      <div className="aspect-[9/16] max-h-64 mx-auto bg-black border-2 border-black mb-3">
        {done && job.video_url
          ? <video controls className="w-full h-full" src={`${BACKEND_URL}${job.video_url}`} />
          : <div className="w-full h-full flex items-center justify-center">
              {job.status === 'error'
                ? <span className="text-[#FF6B6B] font-black text-xs px-2 text-center">{job.error || 'FAILED'}</span>
                : <Loader2 className="h-8 w-8 animate-spin text-white" />}
            </div>}
      </div>

      {done && (
        <div className="flex gap-2">
          <a href={`${BACKEND_URL}${job.video_url}`} target="_blank" rel="noreferrer"
            className="brutal-button flex-1 bg-[#4ECDC4] text-black py-2 text-sm text-center flex items-center justify-center">
            <Download className="h-4 w-4 mr-1" /> SAVE
          </a>
          {job.youtube_url
            ? <a href={job.youtube_url} target="_blank" rel="noreferrer"
                className="brutal-button flex-1 bg-[#FF6B6B] text-black py-2 text-sm text-center flex items-center justify-center">
                <Youtube className="h-4 w-4 mr-1" /> VIEW
              </a>
            : <button onClick={onPublish} disabled={up === 'uploading' || up === 'optimizing' || up === 'queued'}
                className="brutal-button flex-1 bg-black text-white py-2 text-sm disabled:opacity-50 flex items-center justify-center">
                {(up === 'uploading' || up === 'optimizing' || up === 'queued')
                  ? <><Loader2 className="h-4 w-4 mr-1 animate-spin" /> {up.toUpperCase()}</>
                  : <><Youtube className="h-4 w-4 mr-1" /> UPLOAD</>}
              </button>}
        </div>
      )}
      {up === 'error' && <p className="text-xs font-bold text-[#FF6B6B] mt-2">{job.upload_error}</p>}
    </motion.div>
  );
};

const PublishModal = ({ job, onClose, onDone }) => {
  const [title, setTitle] = useState(job.title || job.topic || '');
  const [description, setDescription] = useState(job.description || '');
  const [tags, setTags] = useState((job.hashtags || []).join(', '));
  const [privacy, setPrivacy] = useState('public');
  const [optimize, setOptimize] = useState(true);
  const [suggesting, setSuggesting] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const suggest = async () => {
    setSuggesting(true);
    try {
      const { data } = await axios.get(`${API}/publish/${job.job_id}/metadata`);
      setTitle(data.title); setDescription(data.description); setTags((data.tags || []).join(', '));
      toast.success('AI suggestions filled in');
    } catch (e) { toast.error('Suggestion failed'); } finally { setSuggesting(false); }
  };

  const submit = async () => {
    setSubmitting(true);
    try {
      await axios.post(`${API}/publish/${job.job_id}/youtube`, {
        title, description,
        tags: tags.split(',').map((t) => t.trim()).filter(Boolean),
        privacy, optimize,
      });
      toast.success('Upload queued — track it on the card');
      onDone(); onClose();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to queue upload');
    } finally { setSubmitting(false); }
  };

  const inp = 'brutal-input w-full p-3 font-bold';
  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center p-4 z-50">
      <div className="brutal-card bg-white p-6 max-w-lg w-full max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-black uppercase">UPLOAD TO YOUTUBE</h2>
          <button onClick={onClose}><X className="h-6 w-6" /></button>
        </div>

        <button onClick={suggest} disabled={suggesting}
          className="brutal-button bg-[#FFE66D] text-black w-full py-2 mb-4 flex items-center justify-center">
          {suggesting ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Sparkles className="h-4 w-4 mr-2" />}
          SUGGEST WITH AI
        </button>

        <label className="text-xs font-black uppercase block mb-1">Title</label>
        <input value={title} onChange={(e) => setTitle(e.target.value)} className={`${inp} mb-3`} maxLength={100} />

        <label className="text-xs font-black uppercase block mb-1">Description</label>
        <textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={4} className={`${inp} mb-3 resize-none`} />

        <label className="text-xs font-black uppercase block mb-1">Tags (comma-separated)</label>
        <input value={tags} onChange={(e) => setTags(e.target.value)} className={`${inp} mb-3`} />

        <label className="text-xs font-black uppercase block mb-1">Privacy</label>
        <select value={privacy} onChange={(e) => setPrivacy(e.target.value)} className={`${inp} mb-3`}>
          <option value="public">PUBLIC</option>
          <option value="unlisted">UNLISTED</option>
          <option value="private">PRIVATE</option>
        </select>

        <label className="flex items-center gap-3 cursor-pointer mb-3">
          <input type="checkbox" checked={optimize} onChange={(e) => setOptimize(e.target.checked)} className="w-5 h-5 border-3 border-black" />
          <span className="font-black uppercase text-sm">Re-optimize with AI before upload</span>
        </label>

        {job.music_credit && (
          <div className="border-2 border-black bg-[#FFE66D] p-2 mb-4 text-xs font-bold">
            🎵 Music credit auto-added to description:<br />{job.music_credit}
          </div>
        )}

        <button onClick={submit} disabled={submitting}
          className="brutal-button bg-black text-white w-full h-14 text-xl disabled:opacity-50 flex items-center justify-center">
          {submitting ? <Loader2 className="h-5 w-5 mr-2 animate-spin" /> : <Youtube className="h-5 w-5 mr-2" />}
          QUEUE UPLOAD
        </button>
      </div>
    </div>
  );
};

export default JobsPage;
