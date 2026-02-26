import React, { useState, useEffect } from 'react';
import { ThumbsUp, ThumbsDown } from 'lucide-react';

interface VibeCheckMemeProps {
  onContinue: () => void;
  userId?: string;
}

interface MemeData {
  id: string;
  image_url: string;
  caption: string;
  category: string;
  media_type?: 'image' | 'video' | 'audio';
}

const VibeCheckMeme: React.FC<VibeCheckMemeProps> = ({ onContinue, userId }) => {
  const [meme, setMeme] = useState<MemeData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [voted, setVoted] = useState(false);

  useEffect(() => {
    fetchMeme();
  }, []);

  const fetchMeme = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/user-meme', {
        headers: { 'X-User-ID': userId || '' },
        credentials: 'include',
      });
      if (!response.ok) throw new Error('Failed to fetch meme');
      const data = await response.json();
      setMeme(data);
      trackInteraction('view', null);
    } catch (err) {
      setError('Could not load vibe check');
    } finally {
      setLoading(false);
    }
  };

  const trackInteraction = async (action: string, vote: 'up' | 'down' | null) => {
    if (!meme) return;
    try {
      await fetch('/api/meme-analytics', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ meme_id: meme.id, action, vote, user_id: userId }),
      });
    } catch (e) {
      console.error('Analytics error:', e);
    }
  };

  const handleVote = async (vote: 'up' | 'down') => {
    setVoted(true);
    await trackInteraction('vote', vote);
    setTimeout(() => onContinue(), 800);
  };

  if (loading)
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-white text-xl">Loading vibe check...</div>
      </div>
    );

  if (error || !meme)
    return (
      <div className="min-h-screen bg-gray-900 flex flex-col items-center justify-center p-4">
        <p className="text-gray-400 mb-4">{error || 'No meme available'}</p>
        <button
          onClick={onContinue}
          className="px-6 py-2 bg-violet-600 text-white rounded-lg"
        >
          Continue to Dashboard
        </button>
      </div>
    );

  return (
    <div className="min-h-screen bg-gray-900 flex flex-col items-center justify-center p-4">
      <h1 className="text-3xl font-bold text-white mb-2">Vibe Check</h1>
      <p className="text-violet-400 mb-6">How's this hitting today?</p>
      <div className="bg-gray-800 rounded-xl shadow-2xl max-w-md w-full overflow-hidden">
        {meme.media_type === 'video' ? (
          <video
            src={meme.image_url}
            className="w-full h-64 object-cover"
            controls
            playsInline
            aria-label={meme.caption}
          />
        ) : meme.media_type === 'audio' ? (
          <div className="w-full h-64 flex flex-col items-center justify-center bg-gray-900 gap-2">
            <audio src={meme.image_url} controls className="w-full max-w-sm" aria-label={meme.caption} />
            <span className="text-gray-400 text-sm">Audio meme</span>
          </div>
        ) : (
          <img
            src={meme.image_url}
            alt={meme.caption}
            className="w-full h-64 object-cover"
            onError={(e) => {
              (e.target as HTMLImageElement).src = '/placeholder-meme.png';
            }}
          />
        )}
        <div className="p-4">
          <p className="text-white text-center text-lg">{meme.caption}</p>
        </div>
      </div>
      {!voted ? (
        <div className="flex gap-8 mt-8">
          <button
            onClick={() => handleVote('down')}
            className="flex flex-col items-center gap-2 p-4 rounded-xl bg-gray-800 hover:bg-red-900/50 group"
          >
            <ThumbsDown className="w-12 h-12 text-gray-400 group-hover:text-red-400" />
            <span className="text-gray-400 group-hover:text-red-400">Nah</span>
          </button>
          <button
            onClick={() => handleVote('up')}
            className="flex flex-col items-center gap-2 p-4 rounded-xl bg-gray-800 hover:bg-green-900/50 group"
          >
            <ThumbsUp className="w-12 h-12 text-gray-400 group-hover:text-green-400" />
            <span className="text-gray-400 group-hover:text-green-400">Vibes</span>
          </button>
        </div>
      ) : (
        <div className="mt-8 text-green-400 text-xl animate-pulse">
          Got it! Loading dashboard...
        </div>
      )}
      {!voted && (
        <button
          onClick={() => {
            trackInteraction('skip', null);
            onContinue();
          }}
          className="mt-6 text-gray-500 hover:text-gray-300 text-sm"
        >
          Skip for now
        </button>
      )}
    </div>
  );
};

export default VibeCheckMeme;
