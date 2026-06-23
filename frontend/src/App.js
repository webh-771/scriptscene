import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Toaster } from '@/components/ui/sonner';
import HomePage from './pages/HomePage';
import VideoGeneratorPage from './pages/VideoGeneratorPage';
import JobsPage from './pages/VideoLibraryPage';
import '@/App.css';

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/generate" element={<VideoGeneratorPage />} />
          <Route path="/jobs" element={<JobsPage />} />
          <Route path="/library" element={<JobsPage />} />
        </Routes>
      </BrowserRouter>
      <Toaster position="top-right" richColors />
    </div>
  );
}

export default App;