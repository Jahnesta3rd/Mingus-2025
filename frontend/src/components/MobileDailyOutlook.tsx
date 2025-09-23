import React, { useState, useEffect, useCallback, useRef } from 'react';
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
  Moon,
  ChevronDown,
  ChevronUp,
  X,
  Menu
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

interface MobileDailyOutlookProps {
  className?: string;
  onClose?: () => void;
  isFullScreen?: boolean;
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

// ========================================
// COLLAPSIBLE SECTION COMPONENT
// ========================================

interface CollapsibleSectionProps {
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
  defaultExpanded?: boolean;
  className?: string;
}

const CollapsibleSection: React.FC<CollapsibleSectionProps> = ({
  title,
  icon,
  children,
  defaultExpanded = false,
  className = ''
}) => {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  return (
    <div className={`bg-white rounded-lg border border-gray-200 ${className}`}>
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between p-4 text-left hover:bg-gray-50 transition-colors"
        aria-expanded={isExpanded}
      >
        <div className="flex items-center space-x-3">
          {icon}
          <span className="font-medium text-gray-900">{title}</span>
        </div>
        {isExpanded ? (
          <ChevronUp className="h-5 w-5 text-gray-500" />
        ) : (
          <ChevronDown className="h-5 w-5 text-gray-500" />
        )}
      </button>
      
      {isExpanded && (
        <div className="px-4 pb-4 border-t border-gray-100">
          {children}
        </div>
      )}
    </div>
  );
};

// ========================================
// SWIPE GESTURE HOOK
// ========================================

const useSwipeGesture = (onSwipeLeft?: () => void, onSwipeRight?: () => void) => {
  const [touchStart, setTouchStart] = useState<number | null>(null);
  const [touchEnd, setTouchEnd] = useState<number | null>(null);

  const minSwipeDistance = 50;

  const onTouchStart = (e: React.TouchEvent) => {
    setTouchEnd(null);
    setTouchStart(e.targetTouches[0].clientX);
  };

  const onTouchMove = (e: React.TouchEvent) => {
    setTouchEnd(e.targetTouches[0].clientX);
  };

  const onTouchEnd = () => {
    if (!touchStart || !touchEnd) return;
    
    const distance = touchStart - touchEnd;
    const isLeftSwipe = distance > minSwipeDistance;
    const isRightSwipe = distance < -minSwipeDistance;

    if (isLeftSwipe && onSwipeLeft) {
      onSwipeLeft();
    }
    if (isRightSwipe && onSwipeRight) {
      onSwipeRight();
    }
  };

  return {
    onTouchStart,
    onTouchMove,
    onTouchEnd
  };
};

// ========================================
// MAIN COMPONENT
// ========================================

const MobileDailyOutlook: React.FC<MobileDailyOutlookProps> = ({ 
  className = '', 
  onClose,
  isFullScreen = false 
}) => {
  const { user } = useAuth();
  const { trackInteraction, trackError } = useAnalytics();
  
  // Use caching hook for data management
  const { data: outlookData, loading, error, refetch, isStale } = useDailyOutlookCache();
  const [rating, setRating] = useState(0);
  const [showCelebration, setShowCelebration] = useState(false);
  const [completedActions, setCompletedActions] = useState<Set<string>>(new Set());
  const [currentSection, setCurrentSection] = useState(0);

  // Touch gesture handlers
  const swipeHandlers = useSwipeGesture(
    () => setCurrentSection(prev => Math.min(prev + 1, 2)), // Swipe left - next section
    () => setCurrentSection(prev => Math.max(prev - 1, 0))  // Swipe right - previous section
  );

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
      trackInteraction('mobile_daily_outlook_loaded', {
        user_tier: outlookData.user_tier,
        balance_score: outlookData.balance_score.value,
        streak_count: outlookData.streak_data.current_streak,
        is_stale: isStale
      });
    }
  }, [outlookData, isStale, trackInteraction]);

  // ========================================
  // ACTION HANDLERS
  // ========================================

  const handleActionToggle = async (actionId: string, completed: boolean) => {
    try {
      const token = localStorage.getItem('mingus_token');
      const response = await fetch('/api/daily-outlook/actions', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ action_id: actionId, completed }),
      });

      if (response.ok) {
        setCompletedActions(prev => {
          const newSet = new Set(prev);
          if (completed) {
            newSet.add(actionId);
          } else {
            newSet.delete(actionId);
          }
          return newSet;
        });

        await trackInteraction('action_toggled', { action_id: actionId, completed });
      }
    } catch (err) {
      console.error('Failed to update action:', err);
    }
  };

  const handleRatingSubmit = async (newRating: number) => {
    try {
      const token = localStorage.getItem('mingus_token');
      const response = await fetch('/api/daily-outlook/rating', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          rating: newRating, 
          timestamp: new Date().toISOString() 
        }),
      });

      if (response.ok) {
        setRating(newRating);
        await trackInteraction('rating_submitted', { rating: newRating });
      }
    } catch (err) {
      console.error('Failed to submit rating:', err);
    }
  };

  const handleShare = async () => {
    try {
      if (navigator.share) {
        await navigator.share({
          title: 'My Daily Outlook',
          text: `My balance score is ${outlookData?.balance_score.value}! Check out my progress.`,
          url: window.location.href,
        });
      } else {
        await navigator.clipboard.writeText(
          `My balance score is ${outlookData?.balance_score.value}! Check out my progress.`
        );
      }
      await trackInteraction('daily_outlook_shared', {
        balance_score: outlookData?.balance_score.value
      });
    } catch (err) {
      console.error('Failed to share:', err);
    }
  };

  // ========================================
  // LOADING STATE
  // ========================================

  if (loading) {
    return (
      <div className={`bg-white rounded-2xl shadow-lg overflow-hidden ${className}`}>
        <div className="p-6">
          <div className="animate-pulse space-y-4">
            <div className="h-6 bg-gray-200 rounded w-1/3"></div>
            <div className="h-16 bg-gray-200 rounded"></div>
            <div className="h-4 bg-gray-200 rounded w-2/3"></div>
            <div className="h-8 bg-gray-200 rounded w-1/2"></div>
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
      <div className={`bg-white rounded-2xl shadow-lg overflow-hidden ${className}`}>
        <div className="p-6 text-center">
          <div className="text-red-500 mb-4">
            <svg className="h-12 w-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Failed to Load</h3>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={refetch}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  if (!outlookData) {
    return (
      <div className={`bg-white rounded-2xl shadow-lg overflow-hidden ${className}`}>
        <div className="p-6 text-center text-gray-500">
          <p>No outlook data available</p>
        </div>
      </div>
    );
  }

  // ========================================
  // MAIN RENDER
  // ========================================

  return (
    <div 
      className={`bg-white rounded-2xl shadow-lg overflow-hidden ${className}`} 
      role="article" 
      aria-label="Daily outlook"
      {...swipeHandlers}
    >
      {/* Celebration Animation */}
      {showCelebration && (
        <div className="absolute inset-0 bg-gradient-to-r from-yellow-400 via-pink-500 to-purple-600 opacity-20 animate-pulse z-10 pointer-events-none">
          <div className="flex items-center justify-center h-full">
            <Sparkles className="h-16 w-16 text-white animate-bounce" />
          </div>
        </div>
      )}

      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white p-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-lg font-bold">
              {getGreeting()}, {outlookData.user_name}! 👋
            </h1>
            <div className="flex items-center space-x-2 text-blue-100 text-sm">
              <Clock className="h-4 w-4" />
              <span>{outlookData.current_time}</span>
            </div>
          </div>
          {onClose && (
            <button
              onClick={onClose}
              className="p-2 hover:bg-blue-700 rounded-lg transition-colors"
              aria-label="Close"
            >
              <X className="h-5 w-5" />
            </button>
          )}
        </div>
      </div>

      <div className="p-4 space-y-4">
        {/* Balance Score */}
        <CollapsibleSection
          title="Balance Score"
          icon={<Target className="h-5 w-5 text-blue-500" />}
          defaultExpanded={true}
        >
          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="flex items-center space-x-3">
                  <span className="text-3xl font-bold text-gray-900">
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
        </CollapsibleSection>

        {/* Primary Insight */}
        <CollapsibleSection
          title="Today's Insight"
          icon={getInsightIcon(outlookData.primary_insight.icon)}
          defaultExpanded={true}
        >
          <div className={`rounded-lg p-4 border ${getInsightTypeColor(outlookData.primary_insight.type)}`}>
            <h4 className="font-semibold text-sm mb-2">{outlookData.primary_insight.title}</h4>
            <p className="text-sm">{outlookData.primary_insight.message}</p>
          </div>
        </CollapsibleSection>

        {/* Quick Actions */}
        <CollapsibleSection
          title="Quick Actions"
          icon={<Zap className="h-5 w-5 text-yellow-500" />}
          defaultExpanded={false}
        >
          <div className="space-y-3">
            {outlookData.quick_actions.map((action) => (
              <div key={action.id} className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                <button
                  onClick={() => handleActionToggle(action.id, !completedActions.has(action.id))}
                  className="flex-shrink-0"
                  aria-label={`${completedActions.has(action.id) ? 'Mark as incomplete' : 'Mark as complete'} ${action.title}`}
                >
                  {completedActions.has(action.id) ? (
                    <CheckCircle className="h-5 w-5 text-green-500" />
                  ) : (
                    <Circle className="h-5 w-5 text-gray-400" />
                  )}
                </button>
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <span className="font-medium text-sm">{action.title}</span>
                    <span className={`text-xs px-2 py-1 rounded-full ${
                      action.priority === 'high' ? 'bg-red-100 text-red-700' :
                      action.priority === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                      'bg-green-100 text-green-700'
                    }`}>
                      {action.priority}
                    </span>
                  </div>
                  <p className="text-xs text-gray-600 mt-1">{action.description}</p>
                  <p className="text-xs text-gray-500 mt-1">⏱️ {action.estimated_time}</p>
                </div>
              </div>
            ))}
          </div>
        </CollapsibleSection>

        {/* Streak & Encouragement */}
        <CollapsibleSection
          title="Streak & Progress"
          icon={<Flame className="h-5 w-5 text-orange-500" />}
          defaultExpanded={false}
        >
          <div className="space-y-4">
            <div className="bg-orange-50 rounded-lg p-4">
              <div className="flex items-center space-x-2 mb-2">
                <Flame className="h-5 w-5 text-orange-500" />
                <span className="font-semibold text-orange-800">
                  {outlookData.streak_data.current_streak} Day Streak
                </span>
              </div>
              <div className="w-full bg-orange-200 rounded-full h-2">
                <div 
                  className="bg-orange-500 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${outlookData.streak_data.progress_percentage}%` }}
                />
              </div>
              <p className="text-xs text-orange-700 mt-2">
                {outlookData.streak_data.next_milestone - outlookData.streak_data.current_streak} days to next milestone
              </p>
            </div>
            
            <div className="bg-blue-50 rounded-lg p-4">
              <div className="flex items-center space-x-2">
                <span className="text-lg">{outlookData.encouragement_message.emoji}</span>
                <p className="text-sm text-blue-800">{outlookData.encouragement_message.text}</p>
              </div>
            </div>
          </div>
        </CollapsibleSection>

        {/* Tomorrow's Teaser */}
        <CollapsibleSection
          title="Tomorrow's Preview"
          icon={<Calendar className="h-5 w-5 text-purple-500" />}
          defaultExpanded={false}
        >
          <div className="bg-purple-50 rounded-lg p-4">
            <h4 className="font-semibold text-purple-800 mb-2">{outlookData.tomorrow_teaser.title}</h4>
            <p className="text-sm text-purple-700 mb-2">{outlookData.tomorrow_teaser.description}</p>
            <div className="flex items-center space-x-1">
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
              <span className="text-xs text-purple-600 ml-2">
                Excitement Level: {outlookData.tomorrow_teaser.excitement_level}/5
              </span>
            </div>
          </div>
        </CollapsibleSection>

        {/* Rating & Share */}
        <div className="flex items-center justify-between pt-4 border-t border-gray-200">
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-600">Rate today:</span>
            <div className="flex space-x-1">
              {[1, 2, 3, 4, 5].map((star) => (
                <button
                  key={star}
                  onClick={() => handleRatingSubmit(star)}
                  className="focus:outline-none"
                >
                  <Star
                    className={`h-5 w-5 ${
                      star <= rating ? 'text-yellow-400 fill-current' : 'text-gray-300'
                    }`}
                  />
                </button>
              ))}
            </div>
          </div>
          
          <button
            onClick={handleShare}
            className="flex items-center space-x-1 text-blue-600 hover:text-blue-700 text-sm font-medium transition-colors"
          >
            <Share2 className="h-4 w-4" />
            <span>Share</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default MobileDailyOutlook;
