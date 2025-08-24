import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useRouter } from 'next/router';

// TypeScript interfaces
interface Meme {
  id: string;
  image_url: string;
  caption: string;
  category: string;
  alt_text: string;
  tags?: string[];
}

interface MemeAnalytics {
  meme_id: string;
  interaction_type: 'viewed' | 'skipped' | 'continued' | 'liked' | 'shared' | 'reported';
  time_spent_seconds?: number;
  source_page?: string;
}

interface MemeSplashPageProps {
  onOptOut?: () => void;
  onContinue?: () => void;
  onSkip?: () => void;
  autoAdvanceSeconds?: number;
  showOptOutModal?: boolean;
}

// Error Boundary Component
class MemeErrorBoundary extends React.Component<
  { children: React.ReactNode; fallback?: React.ReactNode },
  { hasError: boolean }
> {
  constructor(props: { children: React.ReactNode; fallback?: React.ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(): { hasError: boolean } {
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('MemeSplashPage Error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div className="min-h-screen bg-black flex items-center justify-center p-4">
          <div className="text-center">
            <div className="text-red-500 text-6xl mb-4">😅</div>
            <h2 className="text-white text-xl font-bold mb-2">Oops! Something went wrong</h2>
            <p className="text-gray-400 mb-4">We couldn't load your daily inspiration</p>
            <button
              onClick={() => window.location.reload()}
              className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-lg transition-colors"
            >
              Try Again
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

// Loading Skeleton Component
const MemeSkeleton: React.FC = () => (
  <div className="min-h-screen bg-black flex flex-col animate-pulse">
    {/* Header skeleton */}
    <div className="flex justify-between items-center p-4">
      <div>
        <div className="h-6 w-24 bg-gray-700 rounded mb-2"></div>
        <div className="h-4 w-32 bg-gray-800 rounded"></div>
      </div>
      <div className="h-4 w-32 bg-gray-700 rounded"></div>
    </div>

    {/* Main content skeleton */}
    <div className="flex-1 flex items-center justify-center px-4">
      <div className="max-w-md w-full">
        <div className="bg-gray-800 rounded-lg overflow-hidden">
          {/* Image skeleton */}
          <div className="h-64 bg-gray-700"></div>
          
          {/* Caption skeleton */}
          <div className="p-4">
            <div className="h-4 bg-gray-700 rounded mb-2"></div>
            <div className="h-4 bg-gray-700 rounded w-3/4"></div>
          </div>
        </div>

        {/* Button skeleton */}
        <div className="mt-6 space-y-3">
          <div className="h-12 bg-gray-700 rounded-lg"></div>
          <div className="h-8 bg-gray-800 rounded"></div>
        </div>
      </div>
    </div>
  </div>
);

// Main Component
const MemeSplashPage: React.FC<MemeSplashPageProps> = ({
  onOptOut,
  onContinue,
  onSkip,
  autoAdvanceSeconds = 10,
  showOptOutModal = true
}) => {
  const [meme, setMeme] = useState<Meme | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showOptOutModal, setShowOptOutModal] = useState(false);
  const [optOutLoading, setOptOutLoading] = useState(false);
  const [timeSpent, setTimeSpent] = useState(0);
  const [autoAdvanceCountdown, setAutoAdvanceCountdown] = useState(autoAdvanceSeconds);
  const [imageLoaded, setImageLoaded] = useState(false);
  const [imageError, setImageError] = useState(false);
  
  const router = useRouter();
  const startTime = useRef<number>(Date.now());
  const countdownInterval = useRef<NodeJS.Timeout>();
  const timeSpentInterval = useRef<NodeJS.Timeout>();

  // Fetch meme data
  const fetchMeme = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch('/api/user-meme', {
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      if (data.success && data.meme) {
        setMeme(data.meme);
        // Track view analytics
        trackAnalytics(data.meme.id, 'viewed');
      } else {
        throw new Error('No meme available');
      }
    } catch (err) {
      console.error('Error fetching meme:', err);
      setError(err instanceof Error ? err.message : 'Failed to load meme');
    } finally {
      setLoading(false);
    }
  }, []);

  // Track analytics
  const trackAnalytics = useCallback(async (memeId: string, interactionType: MemeAnalytics['interaction_type']) => {
    try {
      await fetch('/api/meme-analytics', {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          meme_id: memeId,
          interaction_type: interactionType,
          time_spent_seconds: Math.floor((Date.now() - startTime.current) / 1000),
          source_page: 'meme_splash'
        })
      });
    } catch (err) {
      console.error('Error tracking analytics:', err);
    }
  }, []);

  // Handle continue to dashboard
  const handleContinue = useCallback(async () => {
    if (meme) {
      await trackAnalytics(meme.id, 'continued');
    }
    
    if (onContinue) {
      onContinue();
    } else {
      router.push('/dashboard');
    }
  }, [meme, onContinue, router, trackAnalytics]);

  // Handle skip (not today)
  const handleSkip = useCallback(async () => {
    if (meme) {
      await trackAnalytics(meme.id, 'skipped');
    }
    
    if (onSkip) {
      onSkip();
    } else {
      router.push('/dashboard');
    }
  }, [meme, onSkip, router, trackAnalytics]);

  // Handle opt out
  const handleOptOut = useCallback(async () => {
    try {
      setOptOutLoading(true);
      
      if (meme) {
        await trackAnalytics(meme.id, 'skipped');
      }

      const response = await fetch('/api/user-meme-preferences', {
        method: 'PUT',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          daily_memes_enabled: false,
          opt_out_reason: 'user_requested',
          opt_out_source: 'splash_page'
        })
      });

      if (response.ok) {
        if (onOptOut) {
          onOptOut();
        } else {
          router.push('/dashboard');
        }
      } else {
        throw new Error('Failed to update preferences');
      }
    } catch (err) {
      console.error('Error opting out:', err);
      // Even if opt-out fails, continue to dashboard
      handleContinue();
    } finally {
      setOptOutLoading(false);
      setShowOptOutModal(false);
    }
  }, [meme, onOptOut, router, trackAnalytics, handleContinue]);

  // Auto-advance countdown
  useEffect(() => {
    if (!loading && meme && autoAdvanceSeconds > 0) {
      countdownInterval.current = setInterval(() => {
        setAutoAdvanceCountdown((prev) => {
          if (prev <= 1) {
            handleContinue();
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    }

    return () => {
      if (countdownInterval.current) {
        clearInterval(countdownInterval.current);
      }
    };
  }, [loading, meme, autoAdvanceSeconds, handleContinue]);

  // Track time spent
  useEffect(() => {
    if (!loading && meme) {
      timeSpentInterval.current = setInterval(() => {
        setTimeSpent(Math.floor((Date.now() - startTime.current) / 1000));
      }, 1000);
    }

    return () => {
      if (timeSpentInterval.current) {
        clearInterval(timeSpentInterval.current);
      }
    };
  }, [loading, meme]);

  // Fetch meme on mount
  useEffect(() => {
    fetchMeme();
  }, [fetchMeme]);

  // Handle keyboard navigation
  useEffect(() => {
    const handleKeyPress = (event: KeyboardEvent) => {
      switch (event.key) {
        case 'Enter':
        case ' ':
          event.preventDefault();
          handleContinue();
          break;
        case 'Escape':
          event.preventDefault();
          handleSkip();
          break;
        case 'o':
        case 'O':
          event.preventDefault();
          setShowOptOutModal(true);
          break;
      }
    };

    if (!loading && meme) {
      document.addEventListener('keydown', handleKeyPress);
    }

    return () => {
      document.removeEventListener('keydown', handleKeyPress);
    };
  }, [loading, meme, handleContinue, handleSkip]);

  // Loading state
  if (loading) {
    return <MemeSkeleton />;
  }

  // Error state
  if (error) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center p-4">
        <div className="text-center max-w-md">
          <div className="text-red-500 text-6xl mb-4">😅</div>
          <h2 className="text-white text-xl font-bold mb-2">Oops! Something went wrong</h2>
          <p className="text-gray-400 mb-6">{error}</p>
          <div className="space-y-3">
            <button
              onClick={fetchMeme}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors"
            >
              Try Again
            </button>
            <button
              onClick={handleContinue}
              className="w-full text-gray-400 hover:text-white text-sm underline transition-colors"
            >
              Continue to Dashboard
            </button>
          </div>
        </div>
      </div>
    );
  }

  // No meme available
  if (!meme) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center p-4">
        <div className="text-center max-w-md">
          <div className="text-gray-500 text-6xl mb-4">📅</div>
          <h2 className="text-white text-xl font-bold mb-2">No inspiration today</h2>
          <p className="text-gray-400 mb-6">Check back tomorrow for your daily dose of motivation!</p>
          <button
            onClick={handleContinue}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors"
          >
            Continue to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black flex flex-col relative">
      {/* Auto-advance indicator */}
      {autoAdvanceSeconds > 0 && (
        <div className="absolute top-4 right-4 z-10">
          <div className="bg-black bg-opacity-75 text-white px-3 py-1 rounded-full text-sm">
            Auto-continue in {autoAdvanceCountdown}s
          </div>
        </div>
      )}

      {/* Header */}
      <div className="flex justify-between items-center p-4">
        <div className="text-white">
          <h1 className="text-xl font-bold">MINGUS</h1>
          <p className="text-sm text-gray-400">Daily Inspiration</p>
        </div>
        <button
          onClick={() => setShowOptOutModal(true)}
          className="text-gray-400 hover:text-white text-sm underline transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-black rounded"
          aria-label="Turn off daily memes"
        >
          Turn off daily memes
        </button>
      </div>

      {/* Main meme content */}
      <div className="flex-1 flex items-center justify-center px-4">
        <div className="max-w-md w-full">
          <div className="bg-white rounded-lg overflow-hidden shadow-lg">
            {/* Meme image */}
            <div className="relative">
              {!imageLoaded && !imageError && (
                <div className="h-64 bg-gray-200 animate-pulse flex items-center justify-center">
                  <div className="text-gray-500">Loading...</div>
                </div>
              )}
              
              {imageError && (
                <div className="h-64 bg-gray-200 flex items-center justify-center">
                  <div className="text-center text-gray-500">
                    <div className="text-4xl mb-2">🖼️</div>
                    <p>Image unavailable</p>
                  </div>
                </div>
              )}
              
              <img
                src={meme.image_url}
                alt={meme.alt_text}
                className={`w-full h-auto ${!imageLoaded || imageError ? 'hidden' : ''}`}
                onLoad={() => setImageLoaded(true)}
                onError={() => {
                  setImageError(true);
                  setImageLoaded(true);
                }}
                loading="eager"
              />
              
              {meme.category && (
                <div className="absolute top-2 left-2 bg-black bg-opacity-75 text-white px-2 py-1 rounded text-xs">
                  {meme.category}
                </div>
              )}
            </div>
            
            {/* Meme caption */}
            <div className="p-4">
              <p className="text-gray-800 text-center text-lg font-medium leading-relaxed">
                {meme.caption}
              </p>
            </div>
          </div>

          {/* Action buttons */}
          <div className="mt-6 space-y-3">
            {/* Primary Continue Button */}
            <button
              onClick={handleContinue}
              className="w-full bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white font-semibold py-4 px-6 rounded-lg transition-all duration-200 transform hover:scale-105 focus:outline-none focus:ring-4 focus:ring-blue-500 focus:ring-opacity-50 shadow-lg"
              aria-label="Continue to dashboard"
            >
              Continue to Dashboard
            </button>
            
            {/* Secondary actions */}
            <div className="flex space-x-4 text-sm">
              <button
                onClick={handleSkip}
                className="flex-1 text-gray-400 hover:text-white underline transition-colors focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 focus:ring-offset-black rounded"
                aria-label="Skip for today"
              >
                Not today
              </button>
              
              <button
                onClick={() => setShowOptOutModal(true)}
                className="flex-1 text-gray-400 hover:text-white underline transition-colors focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 focus:ring-offset-black rounded"
                aria-label="Turn off daily memes permanently"
              >
                Turn off daily memes
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Opt-out confirmation modal */}
      {showOptOutModal && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center p-4 z-50"
          onClick={(e) => e.target === e.currentTarget && setShowOptOutModal(false)}
        >
          <div className="bg-white rounded-lg max-w-sm w-full p-6 shadow-xl">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Turn off daily memes?
            </h3>
            <p className="text-gray-600 mb-6">
              You can re-enable them anytime in Settings → Notifications → Daily Memes.
            </p>
            
            <div className="space-y-3">
              <button
                onClick={handleOptOut}
                disabled={optOutLoading}
                className="w-full bg-red-600 hover:bg-red-700 disabled:bg-red-400 text-white font-semibold py-3 px-4 rounded-lg transition-colors focus:outline-none focus:ring-4 focus:ring-red-500 focus:ring-opacity-50"
                aria-label="Confirm turn off daily memes"
              >
                {optOutLoading ? (
                  <span className="flex items-center justify-center">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Turning off...
                  </span>
                ) : (
                  'Turn Off Daily Memes'
                )}
              </button>
              
              <button
                onClick={() => setShowOptOutModal(false)}
                disabled={optOutLoading}
                className="w-full bg-gray-200 hover:bg-gray-300 disabled:bg-gray-100 text-gray-800 font-semibold py-3 px-4 rounded-lg transition-colors focus:outline-none focus:ring-4 focus:ring-gray-500 focus:ring-opacity-50"
                aria-label="Keep daily memes enabled"
              >
                Keep Daily Memes
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Export with error boundary wrapper
const MemeSplashPageWithErrorBoundary: React.FC<MemeSplashPageProps> = (props) => (
  <MemeErrorBoundary>
    <MemeSplashPage {...props} />
  </MemeErrorBoundary>
);

export default MemeSplashPageWithErrorBoundary;
