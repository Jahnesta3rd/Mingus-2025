import React, { useState, useEffect, useCallback, useRef } from 'react';

// TypeScript interfaces
interface MemeData {
  id: number;
  image_url: string;
  category: string;
  caption: string;
  alt_text: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

interface MemeAnalytics {
  meme_id: number;
  action: 'view' | 'continue' | 'skip' | 'auto_advance';
  timestamp: string;
  user_id?: string;
  session_id?: string;
}

interface MoodData {
  mood: 'excited' | 'happy' | 'neutral' | 'sad' | 'angry';
  score: number;
  timestamp: string;
  meme_id: number;
  meme_category: string;
}

interface MemeSplashPageProps {
  onContinue: () => void;
  onSkip: () => void;
  userId?: string;
  sessionId?: string;
  autoAdvanceDelay?: number; // in milliseconds, default 10000
  className?: string;
  enableMoodTracking?: boolean;
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
        <div className="min-h-screen bg-gray-900 flex items-center justify-center p-4">
          <div className="text-center text-white">
            <h2 className="text-xl font-semibold mb-2">Something went wrong</h2>
            <p className="text-gray-300 mb-4">Unable to load meme content</p>
            <button
              onClick={() => this.setState({ hasError: false })}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
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

// Mood Selector Component
const MoodSelector: React.FC<{
  onMoodSelect: (mood: string) => void;
  selectedMood?: string;
  disabled?: boolean;
}> = ({ onMoodSelect, selectedMood, disabled = false }) => {
  const moods = [
    { emoji: '🎉', label: 'excited', color: 'bg-yellow-400', description: 'Very positive, motivated' },
    { emoji: '😊', label: 'happy', color: 'bg-green-400', description: 'Positive, content' },
    { emoji: '😐', label: 'neutral', color: 'bg-gray-400', description: 'Neither positive nor negative' },
    { emoji: '😔', label: 'sad', color: 'bg-blue-400', description: 'Negative, discouraged' },
    { emoji: '😤', label: 'angry', color: 'bg-red-400', description: 'Very negative, frustrated' }
  ];

  return (
    <div className="mb-6">
      <p className="text-center text-white text-sm mb-4">
        How does this make you feel?
      </p>
      <div className="flex justify-center space-x-3">
        {moods.map((mood) => (
          <button
            key={mood.label}
            onClick={() => !disabled && onMoodSelect(mood.label)}
            disabled={disabled}
            className={`w-12 h-12 rounded-full flex items-center justify-center text-2xl transition-all duration-200 ${
              selectedMood === mood.label 
                ? `${mood.color} scale-110 shadow-lg ring-2 ring-white` 
                : 'bg-gray-700 hover:bg-gray-600'
            } ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
            aria-label={`Select ${mood.label} mood: ${mood.description}`}
            title={`${mood.label}: ${mood.description}`}
          >
            {mood.emoji}
          </button>
        ))}
      </div>
      {selectedMood && (
        <p className="text-center text-gray-300 text-xs mt-2">
          {moods.find(m => m.label === selectedMood)?.description}
        </p>
      )}
    </div>
  );
};

// Loading Skeleton Component
const LoadingSkeleton: React.FC = () => (
  <div className="min-h-screen bg-gray-900 flex items-center justify-center p-4">
    <div className="w-full max-w-md">
      {/* Image skeleton */}
      <div className="bg-gray-700 rounded-lg h-64 mb-4 animate-pulse"></div>
      
      {/* Caption skeleton */}
      <div className="space-y-2 mb-6">
        <div className="bg-gray-700 h-4 rounded animate-pulse"></div>
        <div className="bg-gray-700 h-4 rounded w-3/4 animate-pulse"></div>
      </div>
      
      {/* Button skeleton */}
      <div className="bg-gray-700 h-12 rounded-lg animate-pulse mb-3"></div>
      
      {/* Skip link skeleton */}
      <div className="bg-gray-700 h-4 rounded w-32 animate-pulse mx-auto"></div>
    </div>
  </div>
);

// Main MemeSplashPage Component
const MemeSplashPage: React.FC<MemeSplashPageProps> = ({
  onContinue,
  onSkip,
  userId,
  sessionId,
  autoAdvanceDelay = 10000,
  className = '',
  enableMoodTracking = true
}) => {
  const [meme, setMeme] = useState<MemeData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isVisible, setIsVisible] = useState(false);
  const [countdown, setCountdown] = useState(Math.ceil(autoAdvanceDelay / 1000));
  const [selectedMood, setSelectedMood] = useState<string | null>(null);
  const [moodSubmitted, setMoodSubmitted] = useState(false);
  
  const autoAdvanceTimerRef = useRef<NodeJS.Timeout | null>(null);
  const countdownTimerRef = useRef<NodeJS.Timeout | null>(null);
  const hasInteractedRef = useRef(false);

  // Fetch meme data from API
  const fetchMeme = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch('/api/user-meme', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          ...(userId && { 'X-User-ID': userId }),
          ...(sessionId && { 'X-Session-ID': sessionId }),
        },
        credentials: 'include', // Include cookies for authentication
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch meme: ${response.status} ${response.statusText}`);
      }

      const memeData: MemeData = await response.json();
      setMeme(memeData);
      
      // Send view analytics
      await sendAnalytics(memeData.id, 'view');
      
      // Start auto-advance timer
      startAutoAdvanceTimer();
      
    } catch (err) {
      console.error('Error fetching meme:', err);
      setError(err instanceof Error ? err.message : 'Failed to load meme');
    } finally {
      setLoading(false);
    }
  }, [userId, sessionId]);

  // Send analytics to API
  const sendAnalytics = useCallback(async (memeId: number, action: MemeAnalytics['action']) => {
    try {
      const analyticsData: MemeAnalytics = {
        meme_id: memeId,
        action,
        timestamp: new Date().toISOString(),
        ...(userId && { user_id: userId }),
        ...(sessionId && { session_id: sessionId }),
      };

      await fetch('/api/meme-analytics', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(analyticsData),
        credentials: 'include',
      });
    } catch (err) {
      console.error('Error sending analytics:', err);
      // Don't throw - analytics failure shouldn't break the component
    }
  }, [userId, sessionId]);

  // Send mood data to API
  const sendMoodData = useCallback(async (mood: string) => {
    if (!meme || !enableMoodTracking) return;

    try {
      const moodScore = {
        'excited': 5,
        'happy': 4,
        'neutral': 3,
        'sad': 2,
        'angry': 1
      }[mood] || 3;

      const moodData = {
        meme_id: meme.id,
        mood_score: moodScore,
        mood_label: mood,
        meme_category: meme.category,
        user_id: userId,
        session_id: sessionId
      };

      await fetch('/api/meme-mood', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify(moodData)
      });

      setMoodSubmitted(true);
    } catch (err) {
      console.error('Error sending mood data:', err);
      // Don't throw - mood tracking failure shouldn't break user experience
    }
  }, [meme, userId, sessionId, enableMoodTracking]);

  // Handle mood selection
  const handleMoodSelect = useCallback((mood: string) => {
    setSelectedMood(mood);
    sendMoodData(mood);
  }, [sendMoodData]);

  // Start auto-advance timer
  const startAutoAdvanceTimer = useCallback(() => {
    // Clear existing timers
    if (autoAdvanceTimerRef.current) {
      clearTimeout(autoAdvanceTimerRef.current);
    }
    if (countdownTimerRef.current) {
      clearInterval(countdownTimerRef.current);
    }

    // Reset countdown
    setCountdown(Math.ceil(autoAdvanceDelay / 1000));

    // Start countdown timer
    countdownTimerRef.current = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          if (countdownTimerRef.current) {
            clearInterval(countdownTimerRef.current);
          }
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    // Start auto-advance timer
    autoAdvanceTimerRef.current = setTimeout(() => {
      if (!hasInteractedRef.current && meme) {
        sendAnalytics(meme.id, 'auto_advance');
        onContinue();
      }
    }, autoAdvanceDelay);
  }, [autoAdvanceDelay, meme, onContinue, sendAnalytics]);

  // Handle continue button click
  const handleContinue = useCallback(() => {
    hasInteractedRef.current = true;
    if (meme) {
      sendAnalytics(meme.id, 'continue');
    }
    
    // Clear timers
    if (autoAdvanceTimerRef.current) {
      clearTimeout(autoAdvanceTimerRef.current);
    }
    if (countdownTimerRef.current) {
      clearInterval(countdownTimerRef.current);
    }
    
    onContinue();
  }, [meme, onContinue, sendAnalytics]);

  // Handle skip button click
  const handleSkip = useCallback(() => {
    hasInteractedRef.current = true;
    if (meme) {
      sendAnalytics(meme.id, 'skip');
    }
    
    // Clear timers
    if (autoAdvanceTimerRef.current) {
      clearTimeout(autoAdvanceTimerRef.current);
    }
    if (countdownTimerRef.current) {
      clearInterval(countdownTimerRef.current);
    }
    
    onSkip();
  }, [meme, onSkip, sendAnalytics]);

  // Handle keyboard navigation
  const handleKeyDown = useCallback((event: React.KeyboardEvent) => {
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
    }
  }, [handleContinue, handleSkip]);

  // Initialize component
  useEffect(() => {
    fetchMeme();
    
    // Trigger entrance animation
    const timer = setTimeout(() => setIsVisible(true), 100);
    
    return () => {
      clearTimeout(timer);
      if (autoAdvanceTimerRef.current) {
        clearTimeout(autoAdvanceTimerRef.current);
      }
      if (countdownTimerRef.current) {
        clearInterval(countdownTimerRef.current);
      }
    };
  }, [fetchMeme]);

  // Loading state
  if (loading) {
    return <LoadingSkeleton />;
  }

  // Error state
  if (error) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center p-4">
        <div className="text-center text-white max-w-md">
          <div className="mb-6">
            <div className="w-16 h-16 bg-red-600 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
            <h2 className="text-xl font-semibold mb-2">Unable to Load Meme</h2>
            <p className="text-gray-300 mb-4">{error}</p>
          </div>
          
          <div className="space-y-3">
            <button
              onClick={fetchMeme}
              className="w-full px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-gray-900"
            >
              Try Again
            </button>
            <button
              onClick={onSkip}
              className="w-full px-6 py-3 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition-colors focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 focus:ring-offset-gray-900"
            >
              Skip This Feature
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Main content
  return (
    <div 
      className={`min-h-screen bg-gray-900 flex items-center justify-center p-4 transition-all duration-500 ${
        isVisible ? 'opacity-100 scale-100' : 'opacity-0 scale-95'
      } ${className}`}
      onKeyDown={handleKeyDown}
      tabIndex={-1}
    >
      <div className="w-full max-w-md">
        {/* Meme Image */}
        <div className="relative mb-6">
          <img
            src={meme?.image_url}
            alt={meme?.alt_text || 'Meme image'}
            className="w-full h-64 object-cover rounded-lg shadow-lg"
            onError={(e) => {
              console.error('Image failed to load:', meme?.image_url);
              setError('Failed to load meme image');
            }}
          />
          
          {/* Auto-advance countdown indicator */}
          {countdown > 0 && (
            <div className="absolute top-4 right-4 bg-black bg-opacity-50 text-white px-3 py-1 rounded-full text-sm">
              {countdown}s
            </div>
          )}
        </div>

        {/* Caption */}
        <div className="text-center mb-8">
          <p className="text-white text-lg leading-relaxed">
            {meme?.caption}
          </p>
        </div>

        {/* Mood Selector */}
        {enableMoodTracking && (
          <MoodSelector
            onMoodSelect={handleMoodSelect}
            selectedMood={selectedMood || undefined}
            disabled={moodSubmitted}
          />
        )}

        {/* Action Buttons */}
        <div className="space-y-4">
          <button
            onClick={handleContinue}
            className="w-full px-6 py-4 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-gray-900 transition-all duration-200 transform hover:scale-105 active:scale-95"
            aria-label="Continue to dashboard"
          >
            Continue to Dashboard
          </button>
          
          <button
            onClick={handleSkip}
            className="w-full text-gray-400 hover:text-white transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 focus:ring-offset-gray-900 rounded-lg py-2"
            aria-label="Skip this feature"
          >
            Skip this feature
          </button>
        </div>

        {/* Accessibility hint */}
        <div className="mt-6 text-center">
          <p className="text-gray-500 text-xs">
            Press Enter to continue or Escape to skip
          </p>
        </div>
      </div>
    </div>
  );
};

// Export with Error Boundary
const MemeSplashPageWithErrorBoundary: React.FC<MemeSplashPageProps> = (props) => (
  <MemeErrorBoundary>
    <MemeSplashPage {...props} />
  </MemeErrorBoundary>
);

export default MemeSplashPageWithErrorBoundary;
export type { MemeData, MemeAnalytics, MemeSplashPageProps };
