import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ArrowLeft, Play, Download, Clock, FileVideo } from 'lucide-react';
import axios from 'axios';
import { format } from 'date-fns';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const VideoLibraryPage = () => {
  const navigate = useNavigate();
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchProjects();
  }, []);

  const fetchProjects = async () => {
    try {
      const response = await axios.get(`${API}/video/projects`);
      setProjects(response.data);
    } catch (error) {
      console.error('Failed to fetch projects:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = (videoUrl) => {
    window.open(`${BACKEND_URL}${videoUrl}`, '_blank');
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
          <h1 className="text-2xl font-heading font-bold">Video Library</h1>
          <Button
            data-testid="create-new-button"
            onClick={() => navigate('/generate')}
            className="bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500"
          >
            Create New
          </Button>
        </div>
      </header>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-6 py-12">
        {loading ? (
          <div className="text-center py-20">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-primary border-t-transparent" />
            <p className="mt-4 text-gray-400">Loading projects...</p>
          </div>
        ) : projects.length === 0 ? (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center py-20"
          >
            <FileVideo className="h-20 w-20 mx-auto text-gray-600 mb-4" />
            <h2 className="text-2xl font-heading font-bold mb-2">No videos yet</h2>
            <p className="text-gray-400 mb-6">Create your first video to get started</p>
            <Button
              onClick={() => navigate('/generate')}
              className="bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500"
            >
              Create Video
            </Button>
          </motion.div>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {projects.map((project, index) => (
              <ProjectCard
                key={project.job_id}
                project={project}
                index={index}
                onDownload={handleDownload}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

const ProjectCard = ({ project, index, onDownload }) => {
  const statusColors = {
    completed: 'text-green-500',
    processing: 'text-yellow-500',
    queued: 'text-blue-500',
    failed: 'text-red-500'
  };

  const statusLabels = {
    completed: 'Completed',
    processing: 'Processing',
    queued: 'Queued',
    failed: 'Failed'
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1 }}
    >
      <Card className="glass border-white/10 h-full hover:border-primary/50 transition-colors duration-300">
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <CardTitle className="text-lg line-clamp-2">
                {project.script.substring(0, 60)}...
              </CardTitle>
              <div className="flex items-center gap-2 mt-2 text-sm text-gray-400">
                <Clock className="h-4 w-4" />
                {format(new Date(project.created_at), 'MMM dd, yyyy')}
              </div>
            </div>
            <span className={`text-xs font-medium ${statusColors[project.status]}`}>
              {statusLabels[project.status]}
            </span>
          </div>
        </CardHeader>
        <CardContent>
          {project.video_url ? (
            <div className="space-y-3">
              <div className="aspect-video bg-black rounded-lg overflow-hidden">
                <video
                  className="w-full h-full object-cover"
                  src={`${BACKEND_URL}${project.video_url}`}
                  controls={false}
                />
              </div>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  className="flex-1"
                  variant="outline"
                  onClick={() => {
                    const video = document.querySelector(`video[src="${BACKEND_URL}${project.video_url}"]`);
                    if (video) {
                      video.play();
                    }
                  }}
                >
                  <Play className="h-4 w-4 mr-1" />
                  Play
                </Button>
                <Button
                  size="sm"
                  className="flex-1 bg-gradient-to-r from-indigo-600 to-violet-600"
                  onClick={() => onDownload(project.video_url)}
                >
                  <Download className="h-4 w-4 mr-1" />
                  Download
                </Button>
              </div>
            </div>
          ) : (
            <div className="aspect-video bg-black/60 rounded-lg flex items-center justify-center">
              <p className="text-sm text-gray-500">
                {project.status === 'failed' ? 'Generation failed' : 'Processing...'}
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
};

export default VideoLibraryPage;