import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getDailyVibe } from '../../services/vibeService';
import type { VibeResponse } from '../../services/vibeService';

const delay = (ms: number) => new Promise((r) => setTimeout(r, ms));

const LogoSplash: React.FC = () => {
  const navigate = useNavigate();
  const [phase, setPhase] = useState<'enter' | 'hold' | 'exit'>('enter');
  const [enterDone, setEnterDone] = useState(false);

  // Trigger enter animation on next frame so CSS transition runs
  useEffect(() => {
    if (phase !== 'enter') return;
    const id = requestAnimationFrame(() => {
      requestAnimationFrame(() => setEnterDone(true));
    });
    return () => cancelAnimationFrame(id);
  }, [phase]);

  useEffect(() => {
    let mounted = true;

    const runFlow = async () => {
      const vibePromise = getDailyVibe().catch(() => null);

      await delay(300);
      if (!mounted) return;
      setPhase('hold');

      const [vibeData] = await Promise.all([vibePromise, delay(1000)]);
      if (!mounted) return;

      setPhase('exit');
      await delay(200);
      if (!mounted) return;

      navigate('/vibe-check-meme', { replace: true });
    };

    runFlow();
    return () => {
      mounted = false;
    };
  }, [navigate]);

  const isEnter = phase === 'enter';
  const isExit = phase === 'exit';
  const isHold = phase === 'hold';

  const contentOpacityScale =
    isExit ? 'opacity-0 scale-110' : !isEnter || enterDone ? 'opacity-100 scale-100' : 'opacity-0 scale-90';
  const transitionClass = isExit ? 'duration-200' : 'duration-300';
  const pulseClass = isHold ? 'animate-pulse-subtle' : '';

  return (
    <>
      <style>{`
        @keyframes pulse-subtle {
          0%, 100% { transform: scale(1); }
          50% { transform: scale(1.02); }
        }
        .animate-pulse-subtle {
          animation: pulse-subtle 2s ease-in-out infinite;
        }
        @keyframes bounce-dot {
          0%, 80%, 100% { transform: scale(0.6); opacity: 0.5; }
          40% { transform: scale(1); opacity: 1; }
        }
        .animate-bounce-dot {
          animation: bounce-dot 1.4s ease-in-out infinite both;
        }
        .animate-bounce-dot:nth-child(1) { animation-delay: 0s; }
        .animate-bounce-dot:nth-child(2) { animation-delay: 0.2s; }
        .animate-bounce-dot:nth-child(3) { animation-delay: 0.4s; }
      `}</style>
      <div className="min-h-screen bg-gray-900 flex flex-col items-center justify-center relative">
        <div
          className={`flex flex-col items-center justify-center transition-all ease-out ${transitionClass} ${contentOpacityScale} ${pulseClass}`}
        >
          <h1 className="text-6xl md:text-7xl font-bold text-white tracking-tight">MINGUS</h1>
          <p className="mt-3 text-lg text-violet-400">Build Wealth. Live Well.</p>
        </div>

        <div className="absolute bottom-12 left-1/2 -translate-x-1/2 flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-violet-500 animate-bounce-dot" />
          <span className="w-2 h-2 rounded-full bg-violet-500 animate-bounce-dot" />
          <span className="w-2 h-2 rounded-full bg-violet-500 animate-bounce-dot" />
        </div>
      </div>
    </>
  );
};

export default LogoSplash;
