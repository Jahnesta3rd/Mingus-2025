import React, { useEffect } from 'react';

interface StreakCelebrationProps {
  streak: number;
  onComplete: () => void;
}

const StreakCelebration: React.FC<StreakCelebrationProps> = ({ streak, onComplete }) => {
  useEffect(() => {
    const timer = setTimeout(onComplete, 1500);
    return () => clearTimeout(timer);
  }, [onComplete]);

  const getMessage = () => {
    if (streak >= 30) return "You're on fire! A whole month! 🏆";
    if (streak >= 14) return "Two weeks strong! Unstoppable! 💪";
    if (streak >= 7) return "One week streak! Keep it going! ⭐";
    if (streak >= 3) return "Building momentum! Nice work! 🚀";
    return "Keep the streak alive! 🔥";
  };

  return (
    <>
      <style>{`
        @keyframes overlay-fade-in {
          0% { opacity: 0; }
          100% { opacity: 1; }
        }
        .animate-overlay-fade-in {
          animation: overlay-fade-in 0.3s ease-out forwards;
        }
        @keyframes bounce-in {
          0% { opacity: 0; transform: scale(0.3) translateY(20px); }
          50% { transform: scale(1.05) translateY(-10px); }
          70% { transform: scale(0.95) translateY(5px); }
          100% { opacity: 1; transform: scale(1) translateY(0); }
        }
        .animate-bounce-in {
          animation: bounce-in 0.5s ease-out forwards;
        }
        @keyframes spin-slow {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        .animate-spin-slow {
          animation: spin-slow 4s linear infinite;
        }
      `}</style>
      <div
        className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm animate-overlay-fade-in"
        aria-modal
        aria-label="Streak celebration"
      >
        <div className="relative bg-gray-800 rounded-2xl p-8 max-w-sm w-full mx-4 animate-bounce-in">
          {/* Sparkle decorations */}
          <span className="absolute -top-1 -left-1 text-2xl opacity-80 animate-spin-slow" aria-hidden>
            ✨
          </span>
          <span className="absolute -top-1 -right-1 text-2xl opacity-80 animate-spin-slow [animation-direction:reverse]" aria-hidden>
            ✨
          </span>
          <span className="absolute -bottom-1 -left-1 text-2xl opacity-80 animate-spin-slow [animation-delay:1s]" aria-hidden>
            ✨
          </span>
          <span className="absolute -bottom-1 -right-1 text-2xl opacity-80 animate-spin-slow [animation-direction:reverse] [animation-delay:1s]" aria-hidden>
            ✨
          </span>

          <div className="flex flex-col items-center text-center">
            <span
              className="text-6xl mb-3 drop-shadow-[0_0_12px_rgba(139,92,246,0.6)]"
              role="img"
              aria-label="Fire"
            >
              🔥
            </span>
            <h2 className="text-4xl font-bold text-white mb-2">
              {streak} Day Streak!
            </h2>
            <p className="text-lg text-gray-300">{getMessage()}</p>
          </div>
        </div>
      </div>
    </>
  );
};

export default StreakCelebration;
