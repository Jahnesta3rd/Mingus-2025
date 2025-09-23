import React, { useState, useEffect, useCallback } from 'react';
import { 
  TrendingUp, 
  TrendingDown, 
  CheckCircle, 
  Circle, 
  Star, 
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
  Moon,
  ChevronRight
} from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { useAnalytics } from '../hooks/useAnalytics';
import { useDailyOutlookCache } from '../hooks/useDailyOutlookCache';

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

interface DailyOutlookCardProps {
  className?: string;
  onViewFullOutlook?: () => void;
  compact?: boolean;
}

// ========================================
// UTILITY FUNCTIONS
// ========================================

const getGreeting = (): string => {
  const hour = new Date().getHours();
  if (hour < 12) return 'Good morning';
  if (hour < 17) return 'Good afternoon';
  return 'Good evening';
};

const getTrendIcon = (trend: 'up' | 'down' | 'stable') => {
  switch (trend) {
    case 'up':
      return <TrendingUp className="h-5 w-5 text-green-500" />;
    case 'down':
      return <TrendingDown className="h-5 w-5 text-red-500" />;
    default:
      return <div className="h-5 w-5 bg-gray-400 rounded-full" />;
  }
};

const getInsightIcon = (icon: string) => {
  const iconMap: { [key: string]: React.ReactNode } = {
    sun: <Sun className="h-5 w-5 text-yellow-500" />,
    moon: <Moon className="h-5 w-5 text-blue-500" />,
    target: <Target className="h-5 w-5 text-purple-500" />,
    zap: <Zap className="h-5 w-5 text-yellow-500" />,
    award: <Award className="h-5 w-5 text-green-500" />,
    heart: <Heart className="h-5 w-5 text-red-500" />,
    trophy: <Trophy className="h-5 w-5 text-yellow-600" />,
    flame: <Flame className="h-5 w-5 text-orange-500" />,
  };
  return iconMap[icon] || <Star className="h-5 w-5 text-blue-500" />;
};

const getInsightTypeColor = (type: string) => {
  switch (type) {
    case 'positive':
      return 'bg-green-50 border-green-200 text-green-800';
    case 'celebration':
      return 'bg-yellow-50 border-yellow-200 text-yellow-800';
    case 'warning':
      return 'bg-orange-50 border-orange-200 text-orange-800';
    default:
      return 'bg-blue-50 border-blue-200 text-blue-800';
  }
};

const getTierColor = (tier: string) => {
  switch (tier) {
    case 'professional':
      return 'purple';
    case 'mid_tier':
      return 'blue';
    case 'budget_career_vehicle':
      return 'green';
    case 'budget':
      return 'gray';
    default:
      return 'gray';
  }
};

// ========================================
// MAIN COMPONENT
// ========================================

const DailyOutlookCard: React.FC<DailyOutlookCardProps> = ({ 
  className = '', 
  onViewFullOutlook,
  compact = false 
}) => {
  const { user } = useAuth();
  const { trackInteraction, trackError } = useAnalytics();
  
  // Use caching hook for data management
  const { data: outlookData, loading, error, refetch, isStale } = useDailyOutlookCache();
  const [showCelebration, setShowCelebration] = useState(false);

  // ========================================
  // CELEBRATION EFFECT
  // ========================================

  useEffect(() => {
    if (outlookData?.streak_data.milestone_reached) {
      setShowCelebration(true);
      setTimeout(() => setShowCelebration(false), 3000);
    }
  }, [outlookData?.streak_data.milestone_reached]);

  // ========================================
  // TRACKING
  // ========================================

  useEffect(() => {
    if (outlookData) {
      trackInteraction('daily_outlook_card_loaded', {
        user_tier: outlookData.user_tier,
        balance_score: outlookData.balance_score.value,
        streak_count: outlookData.streak_data.current_streak,
        is_stale: isStale
      });
    }
  }, [outlookData, isStale, trackInteraction]);

  const handleViewFullOutlook = async () => {
    await trackInteraction('daily_outlook_card_view_full', {
      user_tier: outlookData?.user_tier,
      balance_score: outlookData?.balance_score.value
    });
    onViewFullOutlook?.();
  };

  // ========================================
  // LOADING STATE
  // ========================================

  if (loading) {
    return (
      <div className={`bg-white rounded-xl shadow-sm border border-gray-200 p-6 ${className}`}>
        <div className="animate-pulse space-y-4">
          <div className="flex items-center justify-between">
            <div className="h-6 bg-gray-200 rounded w-1/3"></div>
            <div className="h-4 bg-gray-200 rounded w-1/4"></div>
          </div>
          <div className="h-16 bg-gray-200 rounded"></div>
          <div className="h-4 bg-gray-200 rounded w-2/3"></div>
          <div className="h-8 bg-gray-200 rounded w-1/2"></div>
        </div>
      </div>
    );
  }

  // ========================================
  // ERROR STATE
  // ========================================

  if (error) {
    return (
      <div className={`bg-white rounded-xl shadow-sm border border-red-200 p-6 ${className}`}>
        <div className="text-center">
          <div className="text-red-500 mb-2">
            <svg className="h-8 w-8 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <p className="text-red-600 text-sm mb-3">Failed to load daily outlook</p>
          <button
            onClick={refetch}
            className="text-xs bg-red-50 hover:bg-red-100 text-red-700 px-3 py-1 rounded-lg transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  if (!outlookData) {
    return (
      <div className={`bg-white rounded-xl shadow-sm border border-gray-200 p-6 ${className}`}>
        <div className="text-center text-gray-500">
          <p className="text-sm">No outlook data available</p>
        </div>
      </div>
    );
  }

  const tierColor = getTierColor(outlookData.user_tier);

  // ========================================
  // COMPACT VERSION
  // ========================================

  if (compact) {
    return (
      <div className={`bg-white rounded-xl shadow-sm border border-gray-200 p-4 ${className}`} role="article" aria-label="Daily outlook summary">
        {/* Celebration Animation */}
        {showCelebration && (
          <div className="absolute inset-0 bg-gradient-to-r from-yellow-400 via-pink-500 to-purple-600 opacity-20 animate-pulse z-10 pointer-events-none rounded-xl">
            <div className="flex items-center justify-center h-full">
              <Sparkles className="h-8 w-8 text-white animate-bounce" />
            </div>
          </div>
        )}

        <div className="relative">
          {/* Header */}
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center space-x-2">
              <span className="text-lg">🌅</span>
              <h3 className="font-semibold text-gray-900 text-sm">Daily Outlook</h3>
            </div>
            <div className="flex items-center space-x-1 text-xs text-gray-500">
              <Clock className="h-3 w-3" />
              <span>{outlookData.current_time}</span>
            </div>
          </div>

          {/* Balance Score */}
          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-3 mb-3">
            <div className="flex items-center justify-between">
              <div>
                <div className="flex items-center space-x-2">
                  <span className="text-xl font-bold text-gray-900">
                    {outlookData.balance_score.value}
                  </span>
                  {getTrendIcon(outlookData.balance_score.trend)}
                </div>
                <p className="text-xs text-gray-600">Balance Score</p>
              </div>
              {outlookData.balance_score.change_percentage !== 0 && (
                <span className={`text-xs font-medium ${
                  outlookData.balance_score.trend === 'up' ? 'text-green-600' : 'text-red-600'
                }`}>
                  {outlookData.balance_score.trend === 'up' ? '+' : ''}
                  {outlookData.balance_score.change_percentage}%
                </span>
              )}
            </div>
          </div>

          {/* Key Insight */}
          <div className={`rounded-lg p-3 mb-3 border ${getInsightTypeColor(outlookData.primary_insight.type)}`}>
            <div className="flex items-start space-x-2">
              {getInsightIcon(outlookData.primary_insight.icon)}
              <div className="flex-1">
                <p className="font-medium text-sm">{outlookData.primary_insight.title}</p>
                <p className="text-xs opacity-90 mt-1">{outlookData.primary_insight.message}</p>
              </div>
            </div>
          </div>

          {/* Streak & Action */}
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Flame className="h-4 w-4 text-orange-500" />
              <span className="text-sm font-medium text-gray-900">
                {outlookData.streak_data.current_streak} day streak
              </span>
            </div>
            <button
              onClick={handleViewFullOutlook}
              className="flex items-center space-x-1 text-blue-600 hover:text-blue-700 text-sm font-medium transition-colors"
            >
              <span>View Full</span>
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ========================================
  // FULL CARD VERSION
  // ========================================

  return (
    <div className={`bg-white rounded-xl shadow-sm border border-gray-200 p-6 ${className}`} role="article" aria-label="Daily outlook">
      {/* Celebration Animation */}
      {showCelebration && (
        <div className="absolute inset-0 bg-gradient-to-r from-yellow-400 via-pink-500 to-purple-600 opacity-20 animate-pulse z-10 pointer-events-none rounded-xl">
          <div className="flex items-center justify-center h-full">
            <Sparkles className="h-12 w-12 text-white animate-bounce" />
          </div>
        </div>
      )}

      <div className="relative">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Daily Outlook</h3>
            <p className="text-sm text-gray-600">{getGreeting()}, {outlookData.user_name}!</p>
          </div>
          <div className="flex items-center space-x-2 text-sm text-gray-500">
            <Clock className="h-4 w-4" />
            <span>{outlookData.current_time}</span>
          </div>
        </div>

        {/* Balance Score */}
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-4 mb-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center space-x-3">
                <span className="text-2xl font-bold text-gray-900">
                  {outlookData.balance_score.value}
                </span>
                {getTrendIcon(outlookData.balance_score.trend)}
              </div>
              <p className="text-sm text-gray-600 mt-1">Balance Score</p>
            </div>
            {outlookData.balance_score.change_percentage !== 0 && (
              <div className="text-right">
                <span className={`text-sm font-medium ${
                  outlookData.balance_score.trend === 'up' ? 'text-green-600' : 'text-red-600'
                }`}>
                  {outlookData.balance_score.trend === 'up' ? '+' : ''}
                  {outlookData.balance_score.change_percentage}%
                </span>
                <p className="text-xs text-gray-500">vs yesterday</p>
              </div>
            )}
          </div>
        </div>

        {/* Primary Insight */}
        <div className={`rounded-lg p-4 mb-4 border ${getInsightTypeColor(outlookData.primary_insight.type)}`}>
          <div className="flex items-start space-x-3">
            {getInsightIcon(outlookData.primary_insight.icon)}
            <div>
              <h4 className="font-semibold text-sm mb-1">{outlookData.primary_insight.title}</h4>
              <p className="text-sm opacity-90">{outlookData.primary_insight.message}</p>
            </div>
          </div>
        </div>

        {/* Quick Actions Preview */}
        {outlookData.quick_actions.length > 0 && (
          <div className="mb-4">
            <h4 className="text-sm font-medium text-gray-900 mb-2">Today's Actions</h4>
            <div className="space-y-2">
              {outlookData.quick_actions.slice(0, 2).map((action) => (
                <div key={action.id} className="flex items-center space-x-2 text-sm">
                  <div className={`w-2 h-2 rounded-full ${
                    action.priority === 'high' ? 'bg-red-500' : 
                    action.priority === 'medium' ? 'bg-yellow-500' : 'bg-green-500'
                  }`} />
                  <span className="text-gray-700">{action.title}</span>
                  <span className="text-gray-400 text-xs">({action.estimated_time})</span>
                </div>
              ))}
              {outlookData.quick_actions.length > 2 && (
                <p className="text-xs text-gray-500">
                  +{outlookData.quick_actions.length - 2} more actions
                </p>
              )}
            </div>
          </div>
        )}

        {/* Streak & Encouragement */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-1">
              <Flame className="h-4 w-4 text-orange-500" />
              <span className="text-sm font-medium text-gray-900">
                {outlookData.streak_data.current_streak} day streak
              </span>
            </div>
            <div className="text-xs text-gray-500">
              {outlookData.encouragement_message.emoji} {outlookData.encouragement_message.text}
            </div>
          </div>
          <button
            onClick={handleViewFullOutlook}
            className="flex items-center space-x-1 text-blue-600 hover:text-blue-700 text-sm font-medium transition-colors"
          >
            <span>View Full Outlook</span>
            <ArrowRight className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default DailyOutlookCard;
