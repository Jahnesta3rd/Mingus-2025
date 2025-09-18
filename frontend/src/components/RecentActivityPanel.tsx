import React, { useState, useEffect } from 'react';
import { 
  Clock, 
  CheckCircle, 
  AlertTriangle, 
  Target, 
  TrendingUp,
  FileText,
  Users,
  MapPin
} from 'lucide-react';

interface ActivityItem {
  id: string;
  type: 'assessment' | 'recommendation' | 'application' | 'profile_update' | 'risk_change' | 'success';
  title: string;
  description: string;
  timestamp: string;
  status: 'completed' | 'pending' | 'failed' | 'success';
  metadata?: Record<string, any>;
}

const RecentActivityPanel: React.FC = () => {
  const [activities, setActivities] = useState<ActivityItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchRecentActivity();
  }, []);

  const fetchRecentActivity = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch('/api/user/activity/recent', {
        headers: {
          'Authorization': `Bearer ${getAuthToken()}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch activity data');
      }

      const data = await response.json();
      setActivities(data.activities || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load activity');
      console.error('Activity fetch failed:', err);
    } finally {
      setLoading(false);
    }
  };

  const getActivityIcon = (type: string, _status: string) => {
    const iconProps = { className: "h-5 w-5" };
    
    switch (type) {
      case 'assessment':
        return <Target {...iconProps} />;
      case 'recommendation':
        return <TrendingUp {...iconProps} />;
      case 'application':
        return <FileText {...iconProps} />;
      case 'profile_update':
        return <Users {...iconProps} />;
      case 'risk_change':
        return <AlertTriangle {...iconProps} />;
      case 'success':
        return <CheckCircle {...iconProps} />;
      default:
        return <Clock {...iconProps} />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
      case 'success':
        return 'text-green-600 bg-green-100';
      case 'pending':
        return 'text-yellow-600 bg-yellow-100';
      case 'failed':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffInHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60));
    
    if (diffInHours < 1) {
      return 'Just now';
    } else if (diffInHours < 24) {
      return `${diffInHours}h ago`;
    } else if (diffInHours < 48) {
      return 'Yesterday';
    } else {
      return date.toLocaleDateString();
    }
  };

  if (loading) {
    return <ActivitySkeleton />;
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex items-center gap-2 text-red-700">
          <AlertTriangle className="h-5 w-5" />
          <span className="text-sm font-medium">Failed to load activity</span>
        </div>
        <p className="text-red-600 text-sm mt-1">{error}</p>
        <button
          onClick={fetchRecentActivity}
          className="mt-2 text-sm text-red-600 hover:text-red-700 font-medium"
        >
          Try again
        </button>
      </div>
    );
  }

  if (activities.length === 0) {
    return (
      <div className="text-center py-8">
        <Clock className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-gray-900 mb-2">No Recent Activity</h3>
        <p className="text-gray-600 text-sm">
          Your recent activity will appear here as you use the platform.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">Recent Activity</h3>
        <button
          onClick={fetchRecentActivity}
          className="text-sm text-blue-600 hover:text-blue-700 font-medium"
        >
          Refresh
        </button>
      </div>

      <div className="space-y-3">
        {activities.map((activity) => (
          <div
            key={activity.id}
            className="flex items-start gap-3 p-3 bg-white border border-gray-200 rounded-lg hover:shadow-sm transition-shadow"
          >
            <div className={`p-2 rounded-lg ${
              activity.status === 'completed' || activity.status === 'success'
                ? 'bg-green-100 text-green-600'
                : activity.status === 'pending'
                ? 'bg-yellow-100 text-yellow-600'
                : activity.status === 'failed'
                ? 'bg-red-100 text-red-600'
                : 'bg-gray-100 text-gray-600'
            }`}>
              {getActivityIcon(activity.type, activity.status)}
            </div>
            
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between mb-1">
                <h4 className="font-medium text-gray-900 text-sm">
                  {activity.title}
                </h4>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(activity.status)}`}>
                  {activity.status}
                </span>
              </div>
              
              <p className="text-gray-600 text-sm mb-2">
                {activity.description}
              </p>
              
              <div className="flex items-center gap-2 text-xs text-gray-500">
                <Clock className="h-3 w-3" />
                <span>{formatTimestamp(activity.timestamp)}</span>
                
                {activity.metadata?.location && (
                  <>
                    <span>•</span>
                    <div className="flex items-center gap-1">
                      <MapPin className="h-3 w-3" />
                      <span>{activity.metadata.location}</span>
                    </div>
                  </>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {activities.length >= 5 && (
        <button className="w-full text-sm text-blue-600 hover:text-blue-700 font-medium py-2 border-t border-gray-200">
          View All Activity
        </button>
      )}
    </div>
  );
};

// Loading Skeleton
const ActivitySkeleton: React.FC = () => {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="h-6 w-32 bg-gray-200 rounded animate-pulse" />
        <div className="h-4 w-16 bg-gray-200 rounded animate-pulse" />
      </div>

      <div className="space-y-3">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="flex items-start gap-3 p-3 bg-white border border-gray-200 rounded-lg">
            <div className="h-9 w-9 bg-gray-200 rounded-lg animate-pulse" />
            <div className="flex-1 space-y-2">
              <div className="flex items-center justify-between">
                <div className="h-4 w-3/4 bg-gray-200 rounded animate-pulse" />
                <div className="h-5 w-16 bg-gray-200 rounded-full animate-pulse" />
              </div>
              <div className="h-3 w-full bg-gray-200 rounded animate-pulse" />
              <div className="h-3 w-2/3 bg-gray-200 rounded animate-pulse" />
              <div className="h-3 w-1/4 bg-gray-200 rounded animate-pulse" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// Helper Functions
const getAuthToken = (): string => {
  return localStorage.getItem('mingus_token') || '';
};

export default RecentActivityPanel;
