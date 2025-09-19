import React, { useState, useEffect } from 'react';
import { Car, TrendingUp, TrendingDown, AlertCircle, CheckCircle, Target, Heart } from 'lucide-react';

// Types
interface CheckinData {
  id: number;
  user_id: string;
  check_in_date: string;
  week_start_date: string;
  physical_activity: number;
  relationship_satisfaction: number;
  meditation_minutes: number;
  stress_spending: number;
  vehicle_expenses: number;
  transportation_stress: number;
  commute_satisfaction: number;
  vehicle_decisions: string;
  created_at: string;
}

interface AnalyticsData {
  summary: {
    total_checkins: number;
    date_range: {
      start: string;
      end: string;
    };
  };
  health_metrics: {
    avg_physical_activity: number;
    avg_relationship_satisfaction: number;
    avg_meditation_minutes: number;
    avg_stress_spending: number;
    trend: string;
  };
  vehicle_metrics: {
    avg_vehicle_expenses: number;
    avg_transportation_stress: number;
    avg_commute_satisfaction: number;
    trend: string;
  };
  recommendations: Array<{
    category: string;
    priority: string;
    message: string;
    action: string;
  }>;
}

interface WeeklyCheckinAnalyticsProps {
  userId: string;
  sessionId?: string;
  className?: string;
}

// Helper functions
const getTrendIcon = (trend: string) => {
  switch (trend) {
    case 'improving':
    case 'decreasing':
      return <TrendingUp className="w-4 h-4 text-green-400" />;
    case 'declining':
    case 'increasing':
      return <TrendingDown className="w-4 h-4 text-red-400" />;
    default:
      return <div className="w-4 h-4 bg-gray-400 rounded-full" />;
  }
};

const getTrendColor = (trend: string) => {
  switch (trend) {
    case 'improving':
    case 'decreasing':
      return 'text-green-400';
    case 'declining':
    case 'increasing':
      return 'text-red-400';
    default:
      return 'text-gray-400';
  }
};

const getPriorityColor = (priority: string) => {
  switch (priority) {
    case 'critical':
      return 'text-red-400 bg-red-900/20';
    case 'high':
      return 'text-orange-400 bg-orange-900/20';
    case 'medium':
      return 'text-yellow-400 bg-yellow-900/20';
    case 'low':
      return 'text-blue-400 bg-blue-900/20';
    default:
      return 'text-gray-400 bg-gray-900/20';
  }
};

const getCategoryIcon = (category: string) => {
  switch (category) {
    case 'health':
      return <Heart className="w-4 h-4" />;
    case 'vehicle':
    case 'transportation':
    case 'commute':
      return <Car className="w-4 h-4" />;
    case 'financial':
      return <Target className="w-4 h-4" />;
    case 'relationships':
      return <Heart className="w-4 h-4" />;
    default:
      return <AlertCircle className="w-4 h-4" />;
  }
};

// Main Component
const WeeklyCheckinAnalytics: React.FC<WeeklyCheckinAnalyticsProps> = ({ 
  userId, 
  sessionId, 
  className = '' 
}) => {
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchAnalytics();
  }, [userId]);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch('/api/weekly-checkin/analytics', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': userId,
          ...(sessionId && { 'X-Session-ID': sessionId }),
        },
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch analytics: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      setAnalytics(data.analytics);
    } catch (err) {
      console.error('Error fetching weekly check-in analytics:', err);
      setError(err instanceof Error ? err.message : 'Failed to load analytics');
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
          <p className="text-red-400 mb-4">Failed to load analytics</p>
          <button
            onClick={fetchAnalytics}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-gray-900"
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
          <p>No analytics data available</p>
          <p className="text-sm">Complete your first weekly check-in to see insights!</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-gray-900 rounded-lg p-6 ${className}`}>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-white mb-2">Weekly Check-in Analytics</h2>
        <p className="text-gray-400">
          {analytics.summary.total_checkins} check-ins from {analytics.summary.date_range.start} to {analytics.summary.date_range.end}
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Health Metrics */}
        <div className="bg-gray-800 rounded-lg p-4">
          <h3 className="text-white text-lg font-semibold mb-4 flex items-center">
            <Heart className="w-5 h-5 text-pink-500 mr-2" />
            Health & Wellness
          </h3>
          
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-gray-300">Physical Activity</span>
              <span className="text-white font-semibold">
                {analytics.health_metrics.avg_physical_activity} workouts/week
              </span>
            </div>
            
            <div className="flex justify-between items-center">
              <span className="text-gray-300">Relationship Satisfaction</span>
              <span className="text-white font-semibold">
                {analytics.health_metrics.avg_relationship_satisfaction}/10
              </span>
            </div>
            
            <div className="flex justify-between items-center">
              <span className="text-gray-300">Meditation</span>
              <span className="text-white font-semibold">
                {analytics.health_metrics.avg_meditation_minutes} min/week
              </span>
            </div>
            
            <div className="flex justify-between items-center">
              <span className="text-gray-300">Stress Spending</span>
              <span className="text-white font-semibold">
                ${analytics.health_metrics.avg_stress_spending}/week
              </span>
            </div>
            
            <div className="flex justify-between items-center pt-2 border-t border-gray-700">
              <span className="text-gray-300">Trend</span>
              <div className="flex items-center">
                {getTrendIcon(analytics.health_metrics.trend)}
                <span className={`ml-2 capitalize ${getTrendColor(analytics.health_metrics.trend)}`}>
                  {analytics.health_metrics.trend}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Vehicle Metrics */}
        <div className="bg-gray-800 rounded-lg p-4">
          <h3 className="text-white text-lg font-semibold mb-4 flex items-center">
            <Car className="w-5 h-5 text-blue-500 mr-2" />
            Vehicle & Transportation
          </h3>
          
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-gray-300">Vehicle Expenses</span>
              <span className="text-white font-semibold">
                ${analytics.vehicle_metrics.avg_vehicle_expenses}/week
              </span>
            </div>
            
            <div className="flex justify-between items-center">
              <span className="text-gray-300">Transportation Stress</span>
              <span className="text-white font-semibold">
                {analytics.vehicle_metrics.avg_transportation_stress}/5
              </span>
            </div>
            
            <div className="flex justify-between items-center">
              <span className="text-gray-300">Commute Satisfaction</span>
              <span className="text-white font-semibold">
                {analytics.vehicle_metrics.avg_commute_satisfaction}/5
              </span>
            </div>
            
            <div className="flex justify-between items-center pt-2 border-t border-gray-700">
              <span className="text-gray-300">Expense Trend</span>
              <div className="flex items-center">
                {getTrendIcon(analytics.vehicle_metrics.trend)}
                <span className={`ml-2 capitalize ${getTrendColor(analytics.vehicle_metrics.trend)}`}>
                  {analytics.vehicle_metrics.trend}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Recommendations */}
      {analytics.recommendations && analytics.recommendations.length > 0 && (
        <div className="mt-6">
          <h3 className="text-white text-lg font-semibold mb-4 flex items-center">
            <CheckCircle className="w-5 h-5 text-green-500 mr-2" />
            Personalized Recommendations
          </h3>
          
          <div className="space-y-3">
            {analytics.recommendations.map((rec, index) => (
              <div key={index} className={`p-4 rounded-lg border-l-4 ${getPriorityColor(rec.priority)}`}>
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0">
                    {getCategoryIcon(rec.category)}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-white font-medium">{rec.message}</span>
                      <span className={`px-2 py-1 rounded text-xs font-medium ${getPriorityColor(rec.priority)}`}>
                        {rec.priority.toUpperCase()}
                      </span>
                    </div>
                    <p className="text-gray-300 text-sm">{rec.action}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Refresh Button */}
      <div className="mt-6 text-center">
        <button
          onClick={fetchAnalytics}
          className="px-6 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition-colors focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 focus:ring-offset-gray-900"
        >
          Refresh Analytics
        </button>
      </div>
    </div>
  );
};

export default WeeklyCheckinAnalytics;
