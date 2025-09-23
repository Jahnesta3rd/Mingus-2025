import React, { useState, useEffect, useCallback } from 'react';
import { 
  Flame, 
  Trophy, 
  Star, 
  Award, 
  Target, 
  Zap, 
  Sparkles, 
  Gift, 
  Crown, 
  Shield,
  Clock,
  Calendar,
  TrendingUp,
  Heart,
  CheckCircle,
  RotateCcw,
  Share2,
  Settings,
  ChevronRight,
  Play,
  Pause,
  RefreshCw
} from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { useAnalytics } from '../hooks/useAnalytics';

// ========================================
// TYPESCRIPT INTERFACES
// ========================================

interface StreakData {
  current_streak: number;
  longest_streak: number;
  total_days: number;
  streak_start_date: string;
  last_activity_date: string;
  is_active: boolean;
  streak_type: 'daily_outlook' | 'goal_completion' | 'engagement' | 'mixed';
}

interface Milestone {
  id: string;
  name: string;
  days_required: number;
  description: string;
  reward: string;
  icon: string;
  color: string;
  achieved: boolean;
  achieved_date?: string;
  progress_percentage: number;
}

interface Achievement {
  id: string;
  name: string;
  description: string;
  icon: string;
  color: string;
  points: number;
  unlocked: boolean;
  unlocked_date?: string;
  category: 'streak' | 'engagement' | 'goals' | 'social' | 'special';
}

interface RecoveryOption {
  id: string;
  type: 'restart' | 'catch_up' | 'grace_period' | 'streak_freeze';
  title: string;
  description: string;
  cost?: number;
  available: boolean;
  action: string;
}

interface WeeklyChallenge {
  id: string;
  title: string;
  description: string;
  target: number;
  current_progress: number;
  reward: string;
  deadline: string;
  category: 'streak' | 'goals' | 'engagement' | 'social';
  difficulty: 'easy' | 'medium' | 'hard';
}

interface StreakTrackerProps {
  className?: string;
  showRecoveryOptions?: boolean;
  showAchievements?: boolean;
  showWeeklyChallenges?: boolean;
  compact?: boolean;
}

// ========================================
// ANIMATION COMPONENTS
// ========================================

const ConfettiAnimation: React.FC<{ show: boolean; onComplete: () => void }> = ({ show, onComplete }) => {
  useEffect(() => {
    if (show) {
      const timer = setTimeout(() => {
        onComplete();
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [show, onComplete]);

  if (!show) return null;

  return (
    <div className="fixed inset-0 pointer-events-none z-50">
      <div className="absolute inset-0 bg-gradient-to-r from-yellow-400 via-pink-500 to-purple-600 opacity-20 animate-pulse" />
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <Sparkles className="h-16 w-16 text-white animate-bounce" />
          <div className="text-white text-2xl font-bold mt-4 animate-pulse">
            🎉 Milestone Achieved! 🎉
          </div>
        </div>
      </div>
    </div>
  );
};

const ProgressRing: React.FC<{ 
  progress: number; 
  size: number; 
  strokeWidth: number; 
  color: string;
  animated?: boolean;
}> = ({ progress, size, strokeWidth, color, animated = true }) => {
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const strokeDasharray = circumference;
  const strokeDashoffset = circumference - (progress / 100) * circumference;

  return (
    <svg width={size} height={size} className="transform -rotate-90">
      <circle
        cx={size / 2}
        cy={size / 2}
        r={radius}
        stroke="currentColor"
        strokeWidth={strokeWidth}
        fill="transparent"
        className="text-gray-200"
      />
      <circle
        cx={size / 2}
        cy={size / 2}
        r={radius}
        stroke="currentColor"
        strokeWidth={strokeWidth}
        fill="transparent"
        strokeDasharray={strokeDasharray}
        strokeDashoffset={strokeDashoffset}
        className={`${color} transition-all duration-1000 ease-in-out ${
          animated ? 'animate-pulse' : ''
        }`}
        style={{
          strokeLinecap: 'round',
        }}
      />
    </svg>
  );
};

// ========================================
// MAIN COMPONENT
// ========================================

const StreakTracker: React.FC<StreakTrackerProps> = ({ 
  className = '', 
  showRecoveryOptions = true,
  showAchievements = true,
  showWeeklyChallenges = true,
  compact = false
}) => {
  const { user } = useAuth();
  const { trackInteraction, trackError } = useAnalytics();
  
  // State management
  const [streakData, setStreakData] = useState<StreakData | null>(null);
  const [milestones, setMilestones] = useState<Milestone[]>([]);
  const [achievements, setAchievements] = useState<Achievement[]>([]);
  const [recoveryOptions, setRecoveryOptions] = useState<RecoveryOption[]>([]);
  const [weeklyChallenges, setWeeklyChallenges] = useState<WeeklyChallenge[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCelebration, setShowCelebration] = useState(false);
  const [showRecovery, setShowRecovery] = useState(false);
  const [showAchievementsPanel, setShowAchievementsPanel] = useState(false);
  const [showChallengesPanel, setShowChallengesPanel] = useState(false);

  // ========================================
  // DATA FETCHING
  // ========================================

  const fetchStreakData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem('mingus_token');
      const response = await fetch('/api/gamification/streak', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch streak data');
      }

      const data = await response.json();
      setStreakData(data.streak_data);
      setMilestones(data.milestones || []);
      setAchievements(data.achievements || []);
      setRecoveryOptions(data.recovery_options || []);
      setWeeklyChallenges(data.weekly_challenges || []);

      // Check for milestone celebration
      const newMilestone = milestones.find(m => m.achieved && !m.achieved_date);
      if (newMilestone) {
        setShowCelebration(true);
        setTimeout(() => setShowCelebration(false), 3000);
      }

      await trackInteraction('streak_data_loaded', {
        current_streak: data.streak_data?.current_streak || 0,
        total_achievements: data.achievements?.length || 0
      });

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load streak data';
      setError(errorMessage);
      await trackError('streak_fetch_error', errorMessage);
    } finally {
      setLoading(false);
    }
  }, [trackInteraction, trackError, milestones]);

  // ========================================
  // ACTION HANDLERS
  // ========================================

  const handleRecoveryAction = useCallback(async (option: RecoveryOption) => {
    try {
      const token = localStorage.getItem('mingus_token');
      const response = await fetch('/api/gamification/recovery', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          recovery_type: option.type,
          action: option.action
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to process recovery action');
      }

      await trackInteraction('recovery_action_taken', {
        recovery_type: option.type,
        action: option.action
      });

      // Refresh data
      await fetchStreakData();
      setShowRecovery(false);

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to process recovery';
      setError(errorMessage);
      await trackError('recovery_action_error', errorMessage);
    }
  }, [trackInteraction, trackError, fetchStreakData]);

  const handleShareAchievement = useCallback(async (achievement: Achievement) => {
    try {
      if (navigator.share) {
        await navigator.share({
          title: 'Achievement Unlocked!',
          text: `I just unlocked "${achievement.name}" in my Daily Outlook streak! 🎉`,
          url: window.location.href,
        });
      } else {
        await navigator.clipboard.writeText(
          `I just unlocked "${achievement.name}" in my Daily Outlook streak! 🎉`
        );
      }

      await trackInteraction('achievement_shared', {
        achievement_id: achievement.id,
        achievement_name: achievement.name
      });

    } catch (err) {
      await trackError('share_error', err instanceof Error ? err.message : 'Share failed');
    }
  }, [trackInteraction, trackError]);

  const handleChallengeAction = useCallback(async (challenge: WeeklyChallenge) => {
    try {
      const token = localStorage.getItem('mingus_token');
      const response = await fetch('/api/gamification/challenges', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          challenge_id: challenge.id,
          action: 'participate'
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to join challenge');
      }

      await trackInteraction('challenge_joined', {
        challenge_id: challenge.id,
        challenge_title: challenge.title
      });

      // Refresh data
      await fetchStreakData();

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to join challenge';
      setError(errorMessage);
      await trackError('challenge_action_error', errorMessage);
    }
  }, [trackInteraction, trackError, fetchStreakData]);

  // ========================================
  // EFFECTS
  // ========================================

  useEffect(() => {
    fetchStreakData();
  }, [fetchStreakData]);

  // ========================================
  // RENDER HELPERS
  // ========================================

  const getStreakIcon = (streak: number) => {
    if (streak >= 100) return <Crown className="h-8 w-8 text-yellow-500" />;
    if (streak >= 30) return <Trophy className="h-8 w-8 text-purple-500" />;
    if (streak >= 7) return <Award className="h-8 w-8 text-blue-500" />;
    return <Flame className="h-8 w-8 text-orange-500" />;
  };

  const getStreakColor = (streak: number) => {
    if (streak >= 100) return 'from-yellow-400 to-yellow-600';
    if (streak >= 30) return 'from-purple-400 to-purple-600';
    if (streak >= 7) return 'from-blue-400 to-blue-600';
    return 'from-orange-400 to-orange-600';
  };

  const getMilestoneIcon = (icon: string) => {
    const iconMap: { [key: string]: React.ReactNode } = {
      'trophy': <Trophy className="h-6 w-6" />,
      'star': <Star className="h-6 w-6" />,
      'crown': <Crown className="h-6 w-6" />,
      'shield': <Shield className="h-6 w-6" />,
      'gift': <Gift className="h-6 w-6" />,
      'zap': <Zap className="h-6 w-6" />,
      'heart': <Heart className="h-6 w-6" />,
      'target': <Target className="h-6 w-6" />
    };
    return iconMap[icon] || <Award className="h-6 w-6" />;
  };

  const getAchievementIcon = (icon: string) => {
    const iconMap: { [key: string]: React.ReactNode } = {
      'trophy': <Trophy className="h-5 w-5" />,
      'star': <Star className="h-5 w-5" />,
      'crown': <Crown className="h-5 w-5" />,
      'shield': <Shield className="h-5 w-5" />,
      'gift': <Gift className="h-5 w-5" />,
      'zap': <Zap className="h-5 w-5" />,
      'heart': <Heart className="h-5 w-5" />,
      'target': <Target className="h-5 w-5" />,
      'check': <CheckCircle className="h-5 w-5" />
    };
    return iconMap[icon] || <Award className="h-5 w-5" />;
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'easy': return 'text-green-600 bg-green-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'hard': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  // ========================================
  // LOADING STATE
  // ========================================

  if (loading) {
    return (
      <div className={`bg-white rounded-2xl shadow-lg p-6 ${className}`} role="status" aria-label="Loading streak data">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded-lg mb-4"></div>
          <div className="h-4 bg-gray-200 rounded w-3/4 mb-6"></div>
          <div className="space-y-4">
            <div className="h-20 bg-gray-200 rounded-lg"></div>
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
            <h3 className="text-lg font-semibold text-red-900">Unable to Load Streak Data</h3>
            <p className="text-red-700">{error}</p>
          </div>
        </div>
        <button
          onClick={fetchStreakData}
          className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors"
        >
          Try Again
        </button>
      </div>
    );
  }

  if (!streakData) {
    return null;
  }

  // ========================================
  // MAIN RENDER
  // ========================================

  return (
    <div className={`bg-white rounded-2xl shadow-lg overflow-hidden ${className}`} role="article" aria-label="Streak tracker">
      {/* Celebration Animation */}
      <ConfettiAnimation show={showCelebration} onComplete={() => setShowCelebration(false)} />

      <div className="p-6 space-y-6">
        {/* Header */}
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-2 flex items-center justify-center space-x-2">
            {getStreakIcon(streakData.current_streak)}
            <span>Streak Tracker</span>
          </h2>
          <p className="text-gray-600">Keep your momentum going!</p>
        </div>

        {/* Main Streak Display */}
        <div className={`bg-gradient-to-r ${getStreakColor(streakData.current_streak)} rounded-xl p-6 text-center text-white`}>
          <div className="flex items-center justify-center space-x-4 mb-4">
            <div className="text-6xl font-bold">
              {streakData.current_streak}
            </div>
            <div className="text-left">
              <div className="text-2xl font-semibold">Day Streak</div>
              <div className="text-sm opacity-90">
                {streakData.is_active ? 'Active' : 'Inactive'}
              </div>
            </div>
          </div>
          
          {/* Progress Ring */}
          <div className="flex justify-center mb-4">
            <div className="relative">
              <ProgressRing
                progress={Math.min((streakData.current_streak / 30) * 100, 100)}
                size={120}
                strokeWidth={8}
                color="text-white"
                animated={true}
              />
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="text-center">
                  <div className="text-lg font-bold">Goal</div>
                  <div className="text-sm">30 days</div>
                </div>
              </div>
            </div>
          </div>

          <div className="flex justify-between text-sm opacity-90">
            <span>Longest: {streakData.longest_streak} days</span>
            <span>Total: {streakData.total_days} days</span>
          </div>
        </div>

        {/* Milestones */}
        {!compact && (
          <div className="space-y-3">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center space-x-2">
              <Trophy className="h-5 w-5 text-yellow-500" />
              <span>Milestones</span>
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {milestones.slice(0, 4).map((milestone) => (
                <div
                  key={milestone.id}
                  className={`rounded-lg p-4 border-2 ${
                    milestone.achieved 
                      ? 'border-green-200 bg-green-50' 
                      : 'border-gray-200 bg-gray-50'
                  }`}
                >
                  <div className="flex items-center space-x-3">
                    <div className={`p-2 rounded-lg ${
                      milestone.achieved ? 'bg-green-100' : 'bg-gray-100'
                    }`}>
                      <div className={milestone.color}>
                        {getMilestoneIcon(milestone.icon)}
                      </div>
                    </div>
                    <div className="flex-1">
                      <h4 className="font-medium text-gray-900">{milestone.name}</h4>
                      <p className="text-sm text-gray-600">{milestone.description}</p>
                      <div className="mt-2">
                        <div className="flex justify-between text-xs text-gray-500 mb-1">
                          <span>{milestone.days_required} days</span>
                          <span>{milestone.progress_percentage}%</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div
                            className={`h-2 rounded-full transition-all duration-500 ${
                              milestone.achieved ? 'bg-green-500' : 'bg-blue-500'
                            }`}
                            style={{ width: `${milestone.progress_percentage}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Quick Actions */}
        <div className="flex flex-wrap gap-3">
          {!streakData.is_active && showRecoveryOptions && (
            <button
              onClick={() => setShowRecovery(true)}
              className="flex items-center space-x-2 bg-orange-600 text-white px-4 py-2 rounded-lg hover:bg-orange-700 transition-colors"
            >
              <RotateCcw className="h-4 w-4" />
              <span>Recovery Options</span>
            </button>
          )}
          
          {showAchievements && (
            <button
              onClick={() => setShowAchievementsPanel(true)}
              className="flex items-center space-x-2 bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 transition-colors"
            >
              <Award className="h-4 w-4" />
              <span>Achievements</span>
            </button>
          )}
          
          {showWeeklyChallenges && (
            <button
              onClick={() => setShowChallengesPanel(true)}
              className="flex items-center space-x-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Target className="h-4 w-4" />
              <span>Challenges</span>
            </button>
          )}
          
          <button
            onClick={() => {
              if (navigator.share) {
                navigator.share({
                  title: 'My Streak Progress',
                  text: `I'm on a ${streakData.current_streak} day streak! 🔥`,
                  url: window.location.href,
                });
              }
            }}
            className="flex items-center space-x-2 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors"
          >
            <Share2 className="h-4 w-4" />
            <span>Share</span>
          </button>
        </div>

        {/* Recovery Options Modal */}
        {showRecovery && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-2xl p-6 max-w-md w-full max-h-96 overflow-y-auto">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">Recovery Options</h3>
                <button
                  onClick={() => setShowRecovery(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ×
                </button>
              </div>
              <div className="space-y-3">
                {recoveryOptions.map((option) => (
                  <div
                    key={option.id}
                    className="border rounded-lg p-4 hover:bg-gray-50 transition-colors"
                  >
                    <h4 className="font-medium text-gray-900 mb-2">{option.title}</h4>
                    <p className="text-sm text-gray-600 mb-3">{option.description}</p>
                    <button
                      onClick={() => handleRecoveryAction(option)}
                      disabled={!option.available}
                      className={`w-full py-2 px-4 rounded-lg transition-colors ${
                        option.available
                          ? 'bg-blue-600 text-white hover:bg-blue-700'
                          : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                      }`}
                    >
                      {option.available ? 'Use This Option' : 'Not Available'}
                    </button>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Achievements Panel */}
        {showAchievementsPanel && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-2xl p-6 max-w-2xl w-full max-h-96 overflow-y-auto">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">Achievements</h3>
                <button
                  onClick={() => setShowAchievementsPanel(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ×
                </button>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {achievements.map((achievement) => (
                  <div
                    key={achievement.id}
                    className={`rounded-lg p-4 border-2 ${
                      achievement.unlocked 
                        ? 'border-green-200 bg-green-50' 
                        : 'border-gray-200 bg-gray-50'
                    }`}
                  >
                    <div className="flex items-center space-x-3">
                      <div className={`p-2 rounded-lg ${
                        achievement.unlocked ? 'bg-green-100' : 'bg-gray-100'
                      }`}>
                        <div className={achievement.color}>
                          {getAchievementIcon(achievement.icon)}
                        </div>
                      </div>
                      <div className="flex-1">
                        <h4 className="font-medium text-gray-900">{achievement.name}</h4>
                        <p className="text-sm text-gray-600">{achievement.description}</p>
                        <div className="flex items-center justify-between mt-2">
                          <span className="text-xs text-gray-500">{achievement.points} pts</span>
                          {achievement.unlocked && (
                            <button
                              onClick={() => handleShareAchievement(achievement)}
                              className="text-xs text-blue-600 hover:text-blue-800"
                            >
                              Share
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Weekly Challenges Panel */}
        {showChallengesPanel && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-2xl p-6 max-w-2xl w-full max-h-96 overflow-y-auto">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">Weekly Challenges</h3>
                <button
                  onClick={() => setShowChallengesPanel(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ×
                </button>
              </div>
              <div className="space-y-4">
                {weeklyChallenges.map((challenge) => (
                  <div
                    key={challenge.id}
                    className="border rounded-lg p-4 hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <h4 className="font-medium text-gray-900">{challenge.title}</h4>
                        <p className="text-sm text-gray-600">{challenge.description}</p>
                      </div>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getDifficultyColor(challenge.difficulty)}`}>
                        {challenge.difficulty}
                      </span>
                    </div>
                    
                    <div className="mb-3">
                      <div className="flex justify-between text-sm text-gray-500 mb-1">
                        <span>Progress</span>
                        <span>{challenge.current_progress}/{challenge.target}</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-500 h-2 rounded-full transition-all duration-500"
                          style={{ width: `${(challenge.current_progress / challenge.target) * 100}%` }}
                        />
                      </div>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <div className="text-sm text-gray-600">
                        <span className="font-medium">Reward:</span> {challenge.reward}
                      </div>
                      <button
                        onClick={() => handleChallengeAction(challenge)}
                        className="flex items-center space-x-1 bg-blue-600 text-white px-3 py-1 rounded-lg hover:bg-blue-700 transition-colors text-sm"
                      >
                        <Play className="h-3 w-3" />
                        <span>Join</span>
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default StreakTracker;
