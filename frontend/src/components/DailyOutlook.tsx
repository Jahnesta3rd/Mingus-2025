import React, { useState, useEffect, useCallback } from 'react';
import { 
  TrendingUp, 
  TrendingDown, 
  CheckCircle, 
  Circle, 
  Star, 
  Share2, 
  Calendar, 
  Target, 
  Zap, 
  Award, 
  Clock, 
  Heart,
  ArrowRight,
  Sparkles,
  Trophy,
  Flame,
  Sun,
  Moon
} from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { useAnalytics } from '../hooks/useAnalytics';
import StreakTracker from './StreakTracker';

// ========================================
// TYPESCRIPT INTERFACES
// ========================================

interface DailyOutlookData {
  user_name: string;
  current_time: string;
  balance_score: {
    value: number;
    trend: 'up' | 'down' | 'stable';
    change_percentage: number;
    previous_value: number;
  };
  primary_insight: {
    title: string;
    message: string;
    type: 'positive' | 'neutral' | 'warning' | 'celebration';
    icon: string;
  };
  quick_actions: Array<{
    id: string;
    title: string;
    description: string;
    completed: boolean;
    priority: 'high' | 'medium' | 'low';
    estimated_time: string;
  }>;
  encouragement_message: {
    text: string;
    type: 'motivational' | 'achievement' | 'reminder' | 'celebration';
    emoji: string;
  };
  streak_data: {
    current_streak: number;
    longest_streak: number;
    milestone_reached: boolean;
    next_milestone: number;
    progress_percentage: number;
  };
  tomorrow_teaser: {
    title: string;
    description: string;
    excitement_level: number;
  };
  user_tier: 'budget' | 'budget_career_vehicle' | 'mid_tier' | 'professional';
}

interface DailyOutlookProps {
  className?: string;
  showStreakTracker?: boolean;
  showGamification?: boolean;
}

interface StarRatingProps {
  rating: number;
  onRatingChange: (rating: number) => void;
  disabled?: boolean;
}

// ========================================
// STAR RATING COMPONENT
// ========================================

const StarRating: React.FC<StarRatingProps> = ({ rating, onRatingChange, disabled = false }) => {
  return (
    <div className="flex items-center space-x-1" role="radiogroup" aria-label="Rate your daily outlook">
      {[1, 2, 3, 4, 5].map((star) => (
        <button
          key={star}
          onClick={() => !disabled && onRatingChange(star)}
          className={`transition-colors duration-200 ${
            disabled ? 'cursor-not-allowed opacity-50' : 'cursor-pointer hover:scale-110'
          }`}
          aria-label={`Rate ${star} star${star > 1 ? 's' : ''}`}
          role="radio"
          aria-checked={rating === star}
        >
          <Star
            className={`h-6 w-6 ${
              star <= rating 
                ? 'text-yellow-400 fill-current' 
                : 'text-gray-300 hover:text-yellow-300'
            }`}
          />
        </button>
      ))}
    </div>
  );
};

// ========================================
// MAIN COMPONENT
// ========================================

const DailyOutlook: React.FC<DailyOutlookProps> = ({ 
  className = '', 
  showStreakTracker = true, 
  showGamification = true 
}) => {
  const { user } = useAuth();
  const { trackInteraction, trackError } = useAnalytics();
  
  // State management
  const [outlookData, setOutlookData] = useState<DailyOutlookData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [rating, setRating] = useState(0);
  const [showCelebration, setShowCelebration] = useState(false);
  const [completedActions, setCompletedActions] = useState<Set<string>>(new Set());

  // ========================================
  // DATA FETCHING
  // ========================================

  const fetchDailyOutlook = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem('mingus_token');
      const response = await fetch('/api/daily-outlook', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch daily outlook data');
      }

      const data = await response.json();
      setOutlookData(data);
      
      // Check for streak milestone celebration
      if (data.streak_data.milestone_reached) {
        setShowCelebration(true);
        setTimeout(() => setShowCelebration(false), 3000);
      }

      await trackInteraction('daily_outlook_loaded', {
        user_tier: data.user_tier,
        balance_score: data.balance_score.value,
        streak_count: data.streak_data.current_streak
      });

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load daily outlook';
      setError(errorMessage);
      await trackError('daily_outlook_fetch_error', errorMessage);
    } finally {
      setLoading(false);
    }
  }, [trackInteraction, trackError]);

  // ========================================
  // ACTION HANDLERS
  // ========================================

  const handleActionToggle = useCallback(async (actionId: string, completed: boolean) => {
    try {
      const token = localStorage.getItem('mingus_token');
      const response = await fetch('/api/daily-outlook/actions', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          action_id: actionId,
          completed,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to update action');
      }

      // Optimistic update
      setCompletedActions(prev => {
        const newSet = new Set(prev);
        if (completed) {
          newSet.add(actionId);
        } else {
          newSet.delete(actionId);
        }
        return newSet;
      });

      await trackInteraction('action_toggled', {
        action_id: actionId,
        completed,
        timestamp: new Date().toISOString()
      });

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update action';
      setError(errorMessage);
      await trackError('action_toggle_error', errorMessage);
    }
  }, [trackInteraction, trackError]);

  const handleRatingSubmit = useCallback(async (newRating: number) => {
    try {
      setRating(newRating);
      
      const token = localStorage.getItem('mingus_token');
      await fetch('/api/daily-outlook/rating', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          rating: newRating,
          timestamp: new Date().toISOString(),
        }),
      });

      await trackInteraction('daily_rating_submitted', {
        rating: newRating,
        timestamp: new Date().toISOString()
      });

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to submit rating';
      setError(errorMessage);
      await trackError('rating_submit_error', errorMessage);
    }
  }, [trackInteraction, trackError]);

  const handleShare = useCallback(async () => {
    try {
      if (navigator.share) {
        await navigator.share({
          title: 'My Daily Outlook',
          text: `I'm on a ${outlookData?.streak_data.current_streak || 0} day streak! 🎉`,
          url: window.location.href,
        });
      } else {
        // Fallback for browsers without native share
        await navigator.clipboard.writeText(
          `Check out my daily outlook progress: ${window.location.href}`
        );
      }

      await trackInteraction('achievement_shared', {
        streak_count: outlookData?.streak_data.current_streak || 0,
        balance_score: outlookData?.balance_score.value || 0
      });

    } catch (err) {
      await trackError('share_error', err instanceof Error ? err.message : 'Share failed');
    }
  }, [outlookData, trackInteraction, trackError]);

  // ========================================
  // EFFECTS
  // ========================================

  useEffect(() => {
    fetchDailyOutlook();
  }, [fetchDailyOutlook]);

  // ========================================
  // LOADING STATE
  // ========================================

  if (loading) {
    return (
      <div className={`bg-white rounded-2xl shadow-lg p-6 ${className}`} role="status" aria-label="Loading daily outlook">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded-lg mb-4"></div>
          <div className="h-4 bg-gray-200 rounded w-3/4 mb-6"></div>
          <div className="space-y-4">
            <div className="h-20 bg-gray-200 rounded-lg"></div>
            <div className="h-16 bg-gray-200 rounded-lg"></div>
            <div className="h-16 bg-gray-200 rounded-lg"></div>
          </div>
        </div>
      </div>
    );
  }

  // ========================================
  // ERROR STATE
  // ========================================

  if (error) {
    return (
      <div className={`bg-red-50 border border-red-200 rounded-2xl p-6 ${className}`}>
        <div className="flex items-center space-x-3 mb-4">
          <div className="p-2 bg-red-100 rounded-lg">
            <Target className="h-6 w-6 text-red-600" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-red-900">Unable to Load Daily Outlook</h3>
            <p className="text-red-700">{error}</p>
          </div>
        </div>
        <button
          onClick={fetchDailyOutlook}
          className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors"
        >
          Try Again
        </button>
      </div>
    );
  }

  if (!outlookData) {
    return null;
  }

  // ========================================
  // RENDER HELPERS
  // ========================================

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 17) return 'Good afternoon';
    return 'Good evening';
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'up': return <TrendingUp className="h-5 w-5 text-green-500" />;
      case 'down': return <TrendingDown className="h-5 w-5 text-red-500" />;
      default: return <div className="h-5 w-5" />;
    }
  };

  const getInsightIcon = (type: string) => {
    switch (type) {
      case 'positive': return <Sun className="h-6 w-6 text-yellow-500" />;
      case 'warning': return <Target className="h-6 w-6 text-orange-500" />;
      case 'celebration': return <Trophy className="h-6 w-6 text-purple-500" />;
      default: return <Heart className="h-6 w-6 text-blue-500" />;
    }
  };

  const getTierColor = (tier: string) => {
    switch (tier) {
      case 'budget': return 'blue';
      case 'budget_career_vehicle': return 'green';
      case 'mid_tier': return 'purple';
      case 'professional': return 'gold';
      default: return 'gray';
    }
  };

  const tierColor = getTierColor(outlookData.user_tier);

  // ========================================
  // MAIN RENDER
  // ========================================

  return (
    <div className={`bg-white rounded-2xl shadow-lg overflow-hidden ${className}`} role="article" aria-label="Daily outlook">
      {/* Celebration Animation */}
      {showCelebration && (
        <div className="absolute inset-0 bg-gradient-to-r from-yellow-400 via-pink-500 to-purple-600 opacity-20 animate-pulse z-10 pointer-events-none" data-testid="celebration-animation">
          <div className="flex items-center justify-center h-full">
            <Sparkles className="h-16 w-16 text-white animate-bounce" />
          </div>
        </div>
      )}

      <div className="p-6 space-y-6">
        {/* Header with Greeting */}
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            {getGreeting()}, {outlookData.user_name}! 👋
          </h1>
          <div className="flex items-center justify-center space-x-2 text-gray-600">
            <Clock className="h-4 w-4" />
            <span className="text-sm">{outlookData.current_time}</span>
          </div>
        </div>

        {/* Balance Score with Trend */}
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-6 text-center">
          <div className="flex items-center justify-center space-x-3 mb-2">
            <span className="text-3xl font-bold text-gray-900">
              {outlookData.balance_score.value}
            </span>
            {getTrendIcon(outlookData.balance_score.trend)}
          </div>
          <p className="text-sm text-gray-600">
            Balance Score
            {outlookData.balance_score.change_percentage !== 0 && (
              <span className={`ml-2 ${
                outlookData.balance_score.trend === 'up' ? 'text-green-600' : 'text-red-600'
              }`}>
                {outlookData.balance_score.trend === 'up' ? '+' : ''}
                {outlookData.balance_score.change_percentage}%
              </span>
            )}
          </p>
        </div>

        {/* Primary Insight Card */}
        <div className={`rounded-xl p-6 border-l-4 ${
          outlookData.primary_insight.type === 'positive' ? 'bg-green-50 border-green-400' :
          outlookData.primary_insight.type === 'warning' ? 'bg-orange-50 border-orange-400' :
          outlookData.primary_insight.type === 'celebration' ? 'bg-purple-50 border-purple-400' :
          'bg-blue-50 border-blue-400'
        }`}>
          <div className="flex items-start space-x-3">
            {getInsightIcon(outlookData.primary_insight.type)}
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">
                {outlookData.primary_insight.title}
              </h3>
              <p className="text-gray-700">
                {outlookData.primary_insight.message}
              </p>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="space-y-3" role="region" aria-label="Quick actions">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center space-x-2">
            <Zap className="h-5 w-5 text-yellow-500" />
            <span>Quick Actions</span>
          </h3>
          {outlookData.quick_actions.map((action) => (
            <div
              key={action.id}
              className="bg-gray-50 rounded-lg p-4 hover:bg-gray-100 transition-colors"
            >
              <div className="flex items-start space-x-3">
                <button
                  onClick={() => handleActionToggle(action.id, !completedActions.has(action.id))}
                  className="mt-1 focus:outline-none focus:ring-2 focus:ring-blue-500 rounded"
                  aria-label={`${completedActions.has(action.id) ? 'Mark as incomplete' : 'Mark as complete'}: ${action.title}`}
                >
                  {completedActions.has(action.id) ? (
                    <CheckCircle className="h-6 w-6 text-green-500" />
                  ) : (
                    <Circle className="h-6 w-6 text-gray-400 hover:text-green-500" />
                  )}
                </button>
                <div className="flex-1">
                  <h4 className="font-medium text-gray-900">{action.title}</h4>
                  <p className="text-sm text-gray-600 mb-2">{action.description}</p>
                  <div className="flex items-center space-x-4 text-xs text-gray-500">
                    <span className={`px-2 py-1 rounded-full ${
                      action.priority === 'high' ? 'bg-red-100 text-red-700' :
                      action.priority === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                      'bg-green-100 text-green-700'
                    }`}>
                      {action.priority} priority
                    </span>
                    <span>{action.estimated_time}</span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Encouragement Message */}
        <div className="bg-gradient-to-r from-pink-50 to-purple-50 rounded-xl p-6 text-center">
          <div className="text-4xl mb-2">{outlookData.encouragement_message.emoji}</div>
          <p className="text-gray-700 font-medium">
            {outlookData.encouragement_message.text}
          </p>
        </div>

        {/* Streak Tracker - Enhanced with Gamification System */}
        {/* This component integrates the gamification system with Daily Outlook */}
        {showStreakTracker && showGamification ? (
          <StreakTracker 
            className="mb-6"
            showRecoveryOptions={true}
            showAchievements={true}
            showWeeklyChallenges={true}
            compact={false}
          />
        ) : (
          /* Fallback to simple streak counter */
          <div className="bg-gradient-to-r from-orange-50 to-red-50 rounded-xl p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-2">
                <Flame className="h-6 w-6 text-orange-500" />
                <h3 className="text-lg font-semibold text-gray-900">Streak</h3>
              </div>
              <span className="text-2xl font-bold text-orange-600">
                {outlookData.streak_data.current_streak}
              </span>
            </div>
            
            {/* Progress Bar */}
            <div className="mb-4">
              <div className="flex justify-between text-sm text-gray-600 mb-2">
                <span>Progress to next milestone</span>
                <span>{outlookData.streak_data.progress_percentage}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div
                  className="bg-gradient-to-r from-orange-400 to-red-500 h-3 rounded-full transition-all duration-500"
                  style={{ width: `${outlookData.streak_data.progress_percentage}%` }}
                />
              </div>
            </div>

            <div className="flex items-center justify-between text-sm text-gray-600">
              <span>Longest: {outlookData.streak_data.longest_streak} days</span>
              <span>Next: {outlookData.streak_data.next_milestone} days</span>
            </div>
          </div>
        )}

        {/* Tomorrow's Teaser */}
        <div className="bg-gradient-to-r from-indigo-50 to-blue-50 rounded-xl p-6">
          <div className="flex items-center space-x-2 mb-3">
            <Calendar className="h-5 w-5 text-indigo-500" />
            <h3 className="text-lg font-semibold text-gray-900">Tomorrow's Preview</h3>
          </div>
          <h4 className="font-medium text-gray-900 mb-2">
            {outlookData.tomorrow_teaser.title}
          </h4>
          <p className="text-gray-600 text-sm">
            {outlookData.tomorrow_teaser.description}
          </p>
          <div className="flex items-center space-x-1 mt-3">
            {[...Array(5)].map((_, i) => (
              <Star
                key={i}
                className={`h-4 w-4 ${
                  i < outlookData.tomorrow_teaser.excitement_level
                    ? 'text-yellow-400 fill-current'
                    : 'text-gray-300'
                }`}
              />
            ))}
            <span className="text-xs text-gray-500 ml-2">Excitement level</span>
          </div>
        </div>

        {/* Rating and Share */}
        <div className="border-t pt-6">
          <div className="flex flex-col sm:flex-row items-center justify-between space-y-4 sm:space-y-0 sm:space-x-6">
            <div className="text-center sm:text-left">
              <h3 className="text-sm font-medium text-gray-900 mb-2">Rate your day</h3>
              <StarRating
                rating={rating}
                onRatingChange={handleRatingSubmit}
              />
            </div>
            
            <button
              onClick={handleShare}
              className="flex items-center space-x-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Share2 className="h-4 w-4" />
              <span>Share Achievement</span>
            </button>
          </div>
        </div>

        {/* User Tier Badge */}
        <div className="text-center">
          <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-${tierColor}-100 text-${tierColor}-800`}>
            <Award className="h-3 w-3 mr-1" />
            {outlookData.user_tier.replace('_', ' ').toUpperCase()} TIER
          </span>
        </div>
      </div>
    </div>
  );
};

export default DailyOutlook;
