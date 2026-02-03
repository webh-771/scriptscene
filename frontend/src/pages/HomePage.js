import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Sparkles, Video, Wand2, Music, Type } from 'lucide-react';

const HomePage = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-white">
      {/* Hero Section - Neo Brutalism */}
      <section className="hero-section hero-pattern min-h-screen flex items-center justify-center px-6 py-20">
        <div className="max-w-7xl w-full">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            {/* Left: Headline */}
            <motion.div
              initial={{ opacity: 0, x: -50 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5 }}
              className="space-y-8"
            >
              <h1 
                data-testid="hero-title"
                className="text-5xl sm:text-6xl lg:text-7xl font-black leading-none tracking-tight uppercase"
                style={{ textShadow: '6px 6px 0 rgba(0,0,0,0.2)' }}
              >
                Turn Scripts into{' '}
                <span className="text-black" style={{ WebkitTextStroke: '2px #FFD700' }}>
                  VIRAL
                </span>{' '}
                VIDEOS
              </h1>
              
              <p className="text-xl font-bold leading-relaxed max-w-xl">
                AI-POWERED • LIGHTNING FAST • ZERO EDITING SKILLS NEEDED
              </p>

              <div className="flex flex-wrap gap-4">
                <Button
                  data-testid="get-started-btn"
                  onClick={() => navigate('/generate')}
                  className="brutal-button h-16 px-10 bg-black text-white hover:bg-black"
                >
                  <Sparkles className="mr-2 h-6 w-6" />
                  GET STARTED NOW
                </Button>
                
                <Button
                  data-testid="view-library-btn"
                  onClick={() => navigate('/library')}
                  className="brutal-button h-16 px-10 bg-white text-black hover:bg-white"
                >
                  <Video className="mr-2 h-6 w-6" />
                  VIEW LIBRARY
                </Button>
              </div>
            </motion.div>

            {/* Right: Feature Cards */}
            <motion.div
              initial={{ opacity: 0, x: 50 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="grid gap-6"
            >
              <FeatureCard
                icon={<Wand2 className="h-10 w-10" />}
                title="AI VOICEOVER"
                description="Natural speech from your text"
                color="bg-[#FF6B6B]"
              />
              <FeatureCard
                icon={<Video className="h-10 w-10" />}
                title="STOCK VISUALS"
                description="Auto-matched images every second"
                color="bg-[#4ECDC4]"
              />
              <FeatureCard
                icon={<Music className="h-10 w-10" />}
                title="FREE MUSIC"
                description="Copyright-free soundtracks"
                color="bg-[#FFE66D]"
              />
            </motion.div>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-24 px-6 bg-white border-t-6 border-black">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-5xl font-black text-center mb-16 uppercase">
            HOW IT WORKS
          </h2>

          <div className="grid md:grid-cols-3 gap-8">
            <StepCard
              number="01"
              title="WRITE SCRIPT"
              description="Type your content"
              color="bg-[#FF6B6B]"
            />
            <StepCard
              number="02"
              title="AI MAGIC"
              description="We generate everything"
              color="bg-[#4ECDC4]"
            />
            <StepCard
              number="03"
              title="DOWNLOAD"
              description="Get your vertical video"
              color="bg-[#FFE66D]"
            />
          </div>
        </div>
      </section>
    </div>
  );
};

const FeatureCard = ({ icon, title, description, color }) => {
  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      className={`brutal-card p-6 ${color}`}
    >
      <div className="flex items-start gap-4">
        <div className="p-3 bg-white border-3 border-black">
          {icon}
        </div>
        <div>
          <h3 className="text-xl font-black mb-2 uppercase">{title}</h3>
          <p className="text-sm font-bold">{description}</p>
        </div>
      </div>
    </motion.div>
  );
};

const StepCard = ({ number, title, description, color }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      className="relative"
    >
      <div className={`brutal-card p-8 h-full ${color}`}>
        <div className="text-7xl font-black mb-4 opacity-50">{number}</div>
        <h3 className="text-2xl font-black mb-3 uppercase">{title}</h3>
        <p className="font-bold">{description}</p>
      </div>
    </motion.div>
  );
};

export default HomePage;