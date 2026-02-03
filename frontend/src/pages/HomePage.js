import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Sparkles, Video, Wand2, Music, Type } from 'lucide-react';

const HomePage = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="hero-background min-h-screen flex items-center justify-center px-6">
        <div className="max-w-7xl w-full">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            {/* Left: Headline */}
            <motion.div
              initial={{ opacity: 0, x: -50 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.8 }}
              className="space-y-8"
            >
              <h1 
                data-testid="hero-title"
                className="text-4xl sm:text-5xl lg:text-6xl font-heading font-bold leading-tight tracking-tight"
              >
                <span className="gradient-text">
                  Turn Scripts into
                </span>
                <br />
                <span className="text-primary">
                  Stunning Videos
                </span>
              </h1>
              
              <p className="text-base sm:text-lg text-gray-400 leading-relaxed max-w-xl">
                Transform your written content into professional videos with AI-powered voiceovers, 
                dynamic visuals, and perfectly timed subtitles. Production-ready in minutes.
              </p>

              <div className="flex flex-wrap gap-4">
                <Button
                  data-testid="get-started-btn"
                  onClick={() => navigate('/generate')}
                  size="lg"
                  className="h-14 px-8 rounded-full bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white font-semibold shadow-lg neon-glow"
                >
                  <Sparkles className="mr-2 h-5 w-5" />
                  Get Started
                </Button>
                
                <Button
                  data-testid="view-library-btn"
                  onClick={() => navigate('/library')}
                  size="lg"
                  variant="outline"
                  className="h-14 px-8 rounded-full bg-white/5 border border-white/10 hover:bg-white/10"
                >
                  <Video className="mr-2 h-5 w-5" />
                  View Library
                </Button>
              </div>
            </motion.div>

            {/* Right: Feature Cards */}
            <motion.div
              initial={{ opacity: 0, x: 50 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.8, delay: 0.2 }}
              className="grid gap-6"
            >
              <FeatureCard
                icon={<Wand2 className="h-8 w-8 text-primary" />}
                title="AI-Powered Voiceover"
                description="Natural-sounding speech generated from your script using advanced AI"
              />
              <FeatureCard
                icon={<Video className="h-8 w-8 text-primary" />}
                title="Dynamic Visuals"
                description="Automatically matched stock footage and images from free libraries"
              />
              <FeatureCard
                icon={<Type className="h-8 w-8 text-primary" />}
                title="Perfect Subtitles"
                description="Precisely timed captions synced with voiceover"
              />
              <FeatureCard
                icon={<Music className="h-8 w-8 text-primary" />}
                title="Background Music"
                description="Copyright-free music tracks to enhance your video"
              />
            </motion.div>
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="py-24 px-6 bg-background">
        <div className="max-w-6xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl lg:text-5xl font-heading font-bold mb-4">
              How It Works
            </h2>
            <p className="text-lg text-gray-400">
              Create professional videos in just a few steps
            </p>
          </motion.div>

          <div className="grid md:grid-cols-3 gap-8">
            <StepCard
              number="01"
              title="Write Your Script"
              description="Type or paste your script. Our AI will analyze and prepare it for video generation."
            />
            <StepCard
              number="02"
              title="Choose Options"
              description="Select voice style, background music, and subtitle preferences."
            />
            <StepCard
              number="03"
              title="Generate & Download"
              description="Let AI create your video. Download when ready in HD quality."
            />
          </div>
        </div>
      </section>
    </div>
  );
};

const FeatureCard = ({ icon, title, description }) => {
  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      className="glass rounded-xl p-6 hover:border-primary/50 transition-colors duration-300"
    >
      <div className="flex items-start gap-4">
        <div className="p-3 bg-primary/10 rounded-lg">
          {icon}
        </div>
        <div>
          <h3 className="text-lg font-semibold mb-2">{title}</h3>
          <p className="text-sm text-gray-400">{description}</p>
        </div>
      </div>
    </motion.div>
  );
};

const StepCard = ({ number, title, description }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      className="relative"
    >
      <div className="glass rounded-xl p-8 h-full">
        <div className="text-6xl font-bold text-primary/20 mb-4">{number}</div>
        <h3 className="text-xl font-heading font-semibold mb-3">{title}</h3>
        <p className="text-gray-400">{description}</p>
      </div>
    </motion.div>
  );
};

export default HomePage;