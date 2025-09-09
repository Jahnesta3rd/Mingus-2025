import React, { useState, useEffect } from 'react';

// Types
interface MoodStatistics {
  mood_label: string;
  count: number;
  avg_score: number;
}

interface MoodTrend {
  date: string;
  avg_mood: number;
  mood_count: number;
}

interface SpendingCorrelation {
  correlation_coefficient: number;
  pattern: {
    type: string;
    description: string;
    risk_level: string;
    recommendation: string;
  };
  data_points: number;
  confidence: string;
}

interface MoodInsight {
  type: string;
  message: string;
  recommendation: string;
}

interface MoodAnalytics {
  mood_statistics: MoodStatistics[];
  spending_correlation: SpendingCorrelation;
  mood_trends: MoodTrend[];
  insights: MoodInsight[];
}

interface MoodDashboardProps {
  userId: string;
  sessionId?: string;
  className?: string;
}

// Mood Chart Component
const MoodChart: React.FC<{ trends: MoodTrend[] }> = ({ trends }) => {
  if (trends.length === 0) {
    return (
      <div className="text-center text-gray-500 py-8">
        <p>No mood data available yet</p>
        <p className="text-sm">Keep using the meme splash page to build your mood history!</p>
      </div>
    );
  }

  const maxMood = 5;
  const minMood = 1;
  const chartHeight = 200;
  const chartWidth = 400;

  // Calculate points for the line chart
  const points = trends.map((trend, index) => {
    const x = (index / (trends.length - 1)) * chartWidth;
    const y = chartHeight - ((trend.avg_mood - minMood) / (maxMood - minMood)) * chartHeight;
    return `${x},${y}`;
  }).join(' ');

  return (
    <div className="bg-gray-800 rounded-lg p-4">
      <h3 className="text-white text-lg font-semibold mb-4">Mood Trend (Last 30 Days)</h3>
      <div className="relative">
        <svg width={chartWidth} height={chartHeight} className="w-full h-48">
          {/* Grid lines */}
          {[1, 2, 3, 4, 5].map((mood) => {
            const y = chartHeight - ((mood - minMood) / (maxMood - minMood)) * chartHeight;
            return (
              <g key={mood}>
                <line
                  x1={0}
                  y1={y}
                  x2={chartWidth}
                  y2={y}
                  stroke="#374151"
                  strokeWidth={1}
                />
                <text
                  x={-10}
                  y={y + 5}
                  fill="#9CA3AF"
                  fontSize="12"
                  textAnchor="end"
                >
                  {mood}
                </text>
              </g>
            );
          })}
          
          {/* Mood line */}
          <polyline
            fill="none"
            stroke="#3B82F6"
            strokeWidth={3}
            points={points}
          />
          
          {/* Data points */}
          {trends.map((trend, index) => {
            const x = (index / (trends.length - 1)) * chartWidth;
            const y = chartHeight - ((trend.avg_mood - minMood) / (maxMood - minMood)) * chartHeight;
            return (
              <circle
                key={index}
                cx={x}
                cy={y}
                r={4}
                fill="#3B82F6"
                className="hover:r-6 transition-all"
              />
            );
          })}
        </svg>
        
        {/* Y-axis label */}
        <div className="absolute left-0 top-1/2 transform -rotate-90 -translate-y-1/2 -translate-x-8 text-gray-400 text-sm">
          Mood Score
        </div>
      </div>
    </div>
  );
};

// Mood Statistics Component
const MoodStatistics: React.FC<{ stats: MoodStatistics[] }> = ({ stats }) => {
  const getMoodEmoji = (mood: string) => {
    const emojis = {
      'excited': '🎉',
      'happy': '😊',
      'neutral': '😐',
      'sad': '😔',
      'angry': '😤'
    };
    return emojis[mood as keyof typeof emojis] || '😐';
  };

  const getMoodColor = (mood: string) => {
    const colors = {
      'excited': 'bg-yellow-400',
      'happy': 'bg-green-400',
      'neutral': 'bg-gray-400',
      'sad': 'bg-blue-400',
      'angry': 'bg-red-400'
    };
    return colors[mood as keyof typeof colors] || 'bg-gray-400';
  };

  if (stats.length === 0) {
    return (
      <div className="text-center text-gray-500 py-4">
        <p>No mood statistics available</p>
      </div>
    );
  }

  const totalMoods = stats.reduce((sum, stat) => sum + stat.count, 0);

  return (
    <div className="space-y-3">
      {stats.map((stat) => (
        <div key={stat.mood_label} className="flex items-center justify-between bg-gray-800 rounded-lg p-3">
          <div className="flex items-center space-x-3">
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-lg ${getMoodColor(stat.mood_label)}`}>
              {getMoodEmoji(stat.mood_label)}
            </div>
            <div>
              <p className="text-white font-medium capitalize">{stat.mood_label}</p>
              <p className="text-gray-400 text-sm">Average: {stat.avg_score.toFixed(1)}/5</p>
            </div>
          </div>
          <div className="text-right">
            <p className="text-white font-semibold">{stat.count}</p>
            <p className="text-gray-400 text-sm">{((stat.count / totalMoods) * 100).toFixed(0)}%</p>
          </div>
        </div>
      ))}
    </div>
  );
};

// Correlation Display Component
const CorrelationDisplay: React.FC<{ correlation: SpendingCorrelation }> = ({ correlation }) => {
  const getRiskColor = (riskLevel: string) => {
    switch (riskLevel) {
      case 'high': return 'text-red-400';
      case 'medium': return 'text-yellow-400';
      case 'low': return 'text-green-400';
      default: return 'text-gray-400';
    }
  };

  const getConfidenceColor = (confidence: string) => {
    switch (confidence) {
      case 'high': return 'text-green-400';
      case 'medium': return 'text-yellow-400';
      case 'low': return 'text-red-400';
      default: return 'text-gray-400';
    }
  };

  return (
    <div className="bg-gray-800 rounded-lg p-4">
      <h3 className="text-white text-lg font-semibold mb-4">Mood & Spending Pattern</h3>
      
      <div className="space-y-4">
        <div>
          <p className="text-gray-300 text-sm mb-2">Pattern Type</p>
          <p className="text-white font-medium capitalize">{correlation.pattern.type.replace('_', ' ')}</p>
        </div>
        
        <div>
          <p className="text-gray-300 text-sm mb-2">Description</p>
          <p className="text-white">{correlation.pattern.description}</p>
        </div>
        
        <div>
          <p className="text-gray-300 text-sm mb-2">Risk Level</p>
          <p className={`font-medium ${getRiskColor(correlation.pattern.risk_level)}`}>
            {correlation.pattern.risk_level.toUpperCase()}
          </p>
        </div>
        
        <div>
          <p className="text-gray-300 text-sm mb-2">Recommendation</p>
          <p className="text-white">{correlation.pattern.recommendation}</p>
        </div>
        
        <div className="flex justify-between items-center pt-4 border-t border-gray-700">
          <div>
            <p className="text-gray-300 text-sm">Data Points</p>
            <p className="text-white font-semibold">{correlation.data_points}</p>
          </div>
          <div>
            <p className="text-gray-300 text-sm">Confidence</p>
            <p className={`font-semibold ${getConfidenceColor(correlation.confidence)}`}>
              {correlation.confidence.toUpperCase()}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

// Insights Component
const InsightsList: React.FC<{ insights: MoodInsight[] }> = ({ insights }) => {
  if (insights.length === 0) {
    return (
      <div className="text-center text-gray-500 py-4">
        <p>No insights available yet</p>
        <p className="text-sm">Keep tracking your mood to get personalized insights!</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {insights.map((insight, index) => (
        <div key={index} className="bg-gray-800 rounded-lg p-4">
          <div className="flex items-start space-x-3">
            <div className="w-2 h-2 bg-blue-400 rounded-full mt-2 flex-shrink-0"></div>
            <div>
              <p className="text-white font-medium mb-1">{insight.message}</p>
              <p className="text-gray-300 text-sm">{insight.recommendation}</p>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

// Main Mood Dashboard Component
const MoodDashboard: React.FC<MoodDashboardProps> = ({ 
  userId, 
  sessionId, 
  className = '' 
}) => {
  const [analytics, setAnalytics] = useState<MoodAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchMoodAnalytics();
  }, [userId]);

  const fetchMoodAnalytics = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch('/api/mood-analytics', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': userId,
          ...(sessionId && { 'X-Session-ID': sessionId }),
        },
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch mood analytics: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      setAnalytics(data);
    } catch (err) {
      console.error('Error fetching mood analytics:', err);
      setError(err instanceof Error ? err.message : 'Failed to load mood analytics');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className={`bg-gray-900 rounded-lg p-6 ${className}`}>
        <div className="animate-pulse">
          <div className="h-6 bg-gray-700 rounded w-1/3 mb-4"></div>
          <div className="space-y-3">
            <div className="h-4 bg-gray-700 rounded"></div>
            <div className="h-4 bg-gray-700 rounded w-5/6"></div>
            <div className="h-4 bg-gray-700 rounded w-4/6"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`bg-gray-900 rounded-lg p-6 ${className}`}>
        <div className="text-center">
          <p className="text-red-400 mb-4">Failed to load mood analytics</p>
          <button
            onClick={fetchMoodAnalytics}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  if (!analytics) {
    return (
      <div className={`bg-gray-900 rounded-lg p-6 ${className}`}>
        <div className="text-center text-gray-500">
          <p>No mood analytics available</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-gray-900 rounded-lg p-6 ${className}`}>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-white mb-2">Your Mood & Spending Pattern</h2>
        <p className="text-gray-400">Track how your mood affects your spending habits</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Mood Statistics */}
        <div>
          <h3 className="text-white text-lg font-semibold mb-4">Mood Statistics</h3>
          <MoodStatistics stats={analytics.mood_statistics} />
        </div>

        {/* Spending Correlation */}
        <div>
          <h3 className="text-white text-lg font-semibold mb-4">Spending Pattern</h3>
          <CorrelationDisplay correlation={analytics.spending_correlation} />
        </div>

        {/* Mood Trend Chart */}
        <div className="lg:col-span-2">
          <MoodChart trends={analytics.mood_trends} />
        </div>

        {/* Insights */}
        <div className="lg:col-span-2">
          <h3 className="text-white text-lg font-semibold mb-4">Personalized Insights</h3>
          <InsightsList insights={analytics.insights} />
        </div>
      </div>

      {/* Refresh Button */}
      <div className="mt-6 text-center">
        <button
          onClick={fetchMoodAnalytics}
          className="px-6 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition-colors"
        >
          Refresh Analytics
        </button>
      </div>
    </div>
  );
};

export default MoodDashboard;
