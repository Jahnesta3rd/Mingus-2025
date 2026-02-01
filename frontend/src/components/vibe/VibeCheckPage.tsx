import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { getDailyVibe, recordReaction } from '../../services/vibeService';
import type { VibeData } from '../../services/vibeService';
import LoadingSpinner from '../common/LoadingSpinner';
import StreakCelebration from './StreakCelebration';

const categoryStyles: Record<string, { bg: string; text: string; border: string }> = {
  career: { bg: 'bg-blue-900/30', text: 'text-blue-400', border: 'border-blue-500' },
  housing: { bg: 'bg-green-900/30', text: 'text-green-400', border: 'border-green-500' },
  family_relationships: { bg: 'bg-purple-900/30', text: 'text-purple-400', border: 'border-purple-500' },
  personal_relationships: { bg: 'bg-pink-900/30', text: 'text-pink-400', border: 'border-pink-500' },
  entertainment: { bg: 'bg-yellow-900/30', text: 'text-yellow-400', border: 'border-yellow-500' },
  kids_worship: { bg: 'bg-orange-900/30', text: 'text-orange-400', border: 'border-orange-500' },
  vehicles: { bg: 'bg-red-900/30', text: 'text-red-400', border: 'border-red-500' },
};

const categoryEmojis: Record<string, string> = {
  career: '💼',
  housing: '🏠',
  family_relationships: '👨‍👩‍👧‍👦',
  personal_relationships: '💕',
  entertainment: '🎉',
  kids_worship: '🙏',
  vehicles: '🚗',
};

const DEFAULT_CATEGORY = {
  bg: 'bg-gray-800/50',
  text: 'text-gray-400',
  border: 'border-gray-500',
};

function getCategoryKey(category: string): string {
  return category.toLowerCase().replace(/\s+/g, '_');
}

const VibeCheckPage: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [vibe, setVibe] = useState<VibeData | null>(null);
  const [isReacting, setIsReacting] = useState(false);
  const [reaction, setReaction] = useState<'like' | 'dislike' | null>(null);
  const [streak, setStreak] = useState(0);
  const [showStreak, setShowStreak] = useState(false);
  const [imageLoaded, setImageLoaded] = useState(false);
  const startTimeRef = useRef<number>(0);

  const loadVibe = useCallback(async () => {
    setLoading(true);
    setVibe(null);
    setReaction(null);
    setImageLoaded(false);

    try {
      const prefetched = sessionStorage.getItem('prefetched_vibe');
      if (prefetched) {
        sessionStorage.removeItem('prefetched_vibe');
        const data = JSON.parse(prefetched) as VibeData;
        setVibe(data);
        startTimeRef.current = Date.now();
        setLoading(false);
        return;
      }

      const response = await getDailyVibe();
      if (!response.has_vibe || !response.vibe) {
        navigate('/dashboard', { replace: true });
        return;
      }
      setVibe(response.vibe);
      startTimeRef.current = Date.now();
    } catch {
      setTimeout(() => navigate('/dashboard', { replace: true }), 500);
    } finally {
      setLoading(false);
    }
  }, [navigate]);

  useEffect(() => {
    loadVibe();
  }, [loadVibe]);

  const handleReaction = useCallback(
    async (reactionType: 'like' | 'dislike' | 'skip') => {
      if (!vibe || isReacting) return;
      setIsReacting(true);
      setReaction(reactionType === 'skip' ? null : reactionType);

      const responseTimeMs = Date.now() - startTimeRef.current;

      try {
        const response = await recordReaction(vibe.vibe_id, reactionType, responseTimeMs);
        const today = new Date().toISOString().split('T')[0];
        sessionStorage.setItem('last_vibe_date', today);

        if (reactionType === 'skip') {
          navigate('/dashboard', { replace: true });
          return;
        }

        setStreak(response.streak);
        if (response.streak > 0) {
          setShowStreak(true);
        } else {
          setTimeout(() => navigate('/dashboard', { replace: true }), 400);
        }
      } catch {
        setIsReacting(false);
        setReaction(null);
        setTimeout(() => navigate('/dashboard', { replace: true }), 500);
      }
    },
    [vibe, isReacting, navigate]
  );

  const handleStreakComplete = useCallback(() => {
    setShowStreak(false);
    navigate('/dashboard', { replace: true });
  }, [navigate]);

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (!vibe || isReacting) return;
      switch (e.key) {
        case 'ArrowRight':
        case 'l':
        case 'L':
          e.preventDefault();
          handleReaction('like');
          break;
        case 'ArrowLeft':
        case 'j':
        case 'J':
          e.preventDefault();
          handleReaction('dislike');
          break;
        case 'Escape':
        case 's':
        case 'S':
          e.preventDefault();
          handleReaction('skip');
          break;
        default:
          break;
      }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [vibe, isReacting, handleReaction]);

  if (loading) {
    return <LoadingSpinner fullScreen message="Loading your daily vibe..." />;
  }

  if (!vibe) {
    return null;
  }

  const categoryKey = getCategoryKey(vibe.category);
  const style = categoryStyles[categoryKey] ?? DEFAULT_CATEGORY;
  const emoji = categoryEmojis[categoryKey] ?? '✨';

  const cardTransform =
    reaction === 'like'
      ? 'translateX(20px) rotate(3deg)'
      : reaction === 'dislike'
        ? 'translateX(-20px) rotate(-3deg)'
        : 'translateX(0) rotate(0)';

  return (
    <div className="min-h-screen bg-gray-900 text-white flex flex-col">
      {showStreak && <StreakCelebration streak={streak} onComplete={handleStreakComplete} />}

      {/* Header */}
      <header className="flex items-center justify-between px-4 py-4 md:px-6 border-b border-gray-800">
        <h1 className="text-lg md:text-xl font-semibold text-white">✨ Your Daily Vibe Check</h1>
        <span
          className={`px-3 py-1 rounded-full text-sm font-medium border ${style.bg} ${style.text} ${style.border}`}
        >
          {emoji} {vibe.category_display} {vibe.day_of_week}
        </span>
        <button
          type="button"
          onClick={() => handleReaction('skip')}
          disabled={isReacting}
          className="text-gray-400 hover:text-white text-sm font-medium disabled:opacity-50 min-w-[48px] min-h-[48px] flex items-center justify-center -mr-2"
        >
          Skip
        </button>
      </header>

      {/* Main card */}
      <main className="flex-1 flex flex-col items-center px-4 py-6 md:py-8">
        <div
          className="w-full max-w-lg transition-all duration-300 ease-out rounded-2xl overflow-hidden bg-gray-800/50 border border-gray-700"
          style={{ transform: cardTransform }}
        >
          <div className="aspect-[4/3] bg-gray-800 relative flex items-center justify-center">
            {!imageLoaded && (
              <div className="absolute inset-0 flex items-center justify-center">
                <LoadingSpinner size="lg" message="Loading image..." />
              </div>
            )}
            <img
              src={vibe.image_url}
              alt={vibe.alt_text}
              className={`w-full h-full object-cover ${!imageLoaded ? 'opacity-0' : 'opacity-100'} transition-opacity duration-300`}
              onLoad={() => setImageLoaded(true)}
            />
          </div>
          <div className="p-4 md:p-5">
            <h2 className="text-xl md:text-2xl font-bold text-white mb-3">{vibe.title}</h2>
            <div className="flex flex-wrap gap-2">
              {vibe.tags.map((tag) => (
                <span
                  key={tag}
                  className="px-2.5 py-1 rounded-md bg-gray-700/80 text-gray-300 text-sm"
                >
                  #{tag}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Reaction buttons */}
        <div className="flex items-center gap-6 mt-8">
          <button
            type="button"
            onClick={() => handleReaction('dislike')}
            disabled={isReacting}
            className="min-w-[48px] min-h-[48px] w-14 h-14 rounded-full bg-gray-700 hover:bg-gray-600 border-2 border-gray-600 flex items-center justify-center text-2xl disabled:opacity-50 disabled:cursor-not-allowed transition-colors focus:outline-none focus:ring-2 focus:ring-violet-500 focus:ring-offset-2 focus:ring-offset-gray-900"
            aria-label="Dislike"
          >
            👎
          </button>
          <button
            type="button"
            onClick={() => handleReaction('like')}
            disabled={isReacting}
            className="min-w-[48px] min-h-[48px] w-14 h-14 rounded-full bg-gray-700 hover:bg-gray-600 border-2 border-gray-600 flex items-center justify-center text-2xl disabled:opacity-50 disabled:cursor-not-allowed transition-colors focus:outline-none focus:ring-2 focus:ring-violet-500 focus:ring-offset-2 focus:ring-offset-gray-900"
            aria-label="Like"
          >
            👍
          </button>
        </div>
      </main>

      {/* Footer */}
      <footer className="px-4 py-4 text-center text-gray-500 text-sm border-t border-gray-800">
        Check your vibe. Check your wallet. 💰
      </footer>
    </div>
  );
};

export default VibeCheckPage;
