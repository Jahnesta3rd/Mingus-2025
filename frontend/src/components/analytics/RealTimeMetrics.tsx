import React, { useState, useEffect, useCallback } from 'react';

interface RealTimeMetricsData {
  real_time_metrics: {
    [key: string]: {
      value: number;
      previous_value: number;
      change_percentage: number | null;
      last_updated: string;
    };
  };
  period_start: string;
  period_end: string;
}

interface RealTimeMetricsProps {
  assessmentType?: string;
  refreshInterval?: number; // milliseconds
  showChangeIndicator?: boolean;
  className?: string;
}

const RealTimeMetrics: React.FC<RealTimeMetricsProps> = ({
  assessmentType,
  refreshInterval = 30000, // 30 seconds
  showChangeIndicator = true,
  className = ''
}) => {
  const [metrics, setMetrics] = useState<RealTimeMetricsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  // Fetch real-time metrics
  const fetchMetrics = useCallback(async () => {
    try {
      setLoading(true);
      const url = assessmentType 
        ? `/api/analytics/real-time?assessment_type=${assessmentType}`
        : '/api/analytics/real-time';
      
      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      setMetrics(data);
      setLastUpdate(new Date());
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load metrics');
      console.error('Error fetching real-time metrics:', err);
    } finally {
      setLoading(false);
    }
  }, [assessmentType]);

  // Initial fetch
  useEffect(() => {
    fetchMetrics();
  }, [fetchMetrics]);

  // Set up refresh interval
  useEffect(() => {
    const interval = setInterval(fetchMetrics, refreshInterval);
    return () => clearInterval(interval);
  }, [fetchMetrics, refreshInterval]);

  // Format number with commas
  const formatNumber = (num: number): string => {
    return num.toLocaleString();
  };

  // Get change indicator
  const getChangeIndicator = (changePercentage: number | null): string => {
    if (changePercentage === null) return '';
    if (changePercentage > 0) return '↗';
    if (changePercentage < 0) return '↘';
    return '→';
  };

  // Get change color class
  const getChangeColorClass = (changePercentage: number | null): string => {
    if (changePercentage === null) return 'text-gray-500';
    if (changePercentage > 0) return 'text-green-600';
    if (changePercentage < 0) return 'text-red-600';
    return 'text-gray-500';
  };

  // Get metric display name
  const getMetricDisplayName = (metricKey: string): string => {
    const displayNames: { [key: string]: string } = {
      'assessments_completed_today': 'Assessments Completed Today',
      'total_sessions_today': 'Total Sessions Today',
      'conversion_rate_today': 'Conversion Rate Today',
      'average_score_today': 'Average Score Today',
      'active_users_now': 'Active Users Now',
      'recent_completions': 'Recent Completions'
    };
    return displayNames[metricKey] || metricKey.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  // Get metric value with formatting
  const getMetricValue = (metricKey: string, value: number): string => {
    if (metricKey.includes('rate') || metricKey.includes('percentage')) {
      return `${value.toFixed(1)}%`;
    }
    if (metricKey.includes('score')) {
      return value.toFixed(1);
    }
    return formatNumber(value);
  };

  if (loading && !metrics) {
    return (
      <div className={`real-time-metrics loading ${className}`}>
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
          <div className="h-6 bg-gray-200 rounded w-1/2"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`real-time-metrics error ${className}`}>
        <div className="text-red-600 text-sm">
          <svg className="inline w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
          Unable to load live metrics
        </div>
      </div>
    );
  }

  if (!metrics || !metrics.real_time_metrics) {
    return (
      <div className={`real-time-metrics empty ${className}`}>
        <div className="text-gray-500 text-sm">No metrics available</div>
      </div>
    );
  }

  const metricEntries = Object.entries(metrics.real_time_metrics);

  return (
    <div className={`real-time-metrics ${className}`}>
      <div className="metrics-header mb-4">
        <h3 className="text-lg font-semibold text-gray-900">
          Live Metrics
          {assessmentType && (
            <span className="text-sm font-normal text-gray-600 ml-2">
              ({assessmentType.replace(/_/g, ' ')})
            </span>
          )}
        </h3>
        {lastUpdate && (
          <p className="text-xs text-gray-500">
            Last updated: {lastUpdate.toLocaleTimeString()}
            <span className="ml-2 inline-block w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
          </p>
        )}
      </div>

      <div className="metrics-grid grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {metricEntries.map(([metricKey, metricData]) => (
          <div key={metricKey} className="metric-card bg-white rounded-lg shadow-sm border border-gray-200 p-4">
            <div className="metric-header flex items-center justify-between mb-2">
              <h4 className="text-sm font-medium text-gray-700">
                {getMetricDisplayName(metricKey)}
              </h4>
              {showChangeIndicator && metricData.change_percentage !== null && (
                <span className={`text-xs font-medium ${getChangeColorClass(metricData.change_percentage)}`}>
                  {getChangeIndicator(metricData.change_percentage)}
                  {Math.abs(metricData.change_percentage).toFixed(1)}%
                </span>
              )}
            </div>
            
            <div className="metric-value">
              <span className="text-2xl font-bold text-gray-900">
                {getMetricValue(metricKey, metricData.value)}
              </span>
            </div>

            {showChangeIndicator && metricData.previous_value !== metricData.value && (
              <div className="metric-change mt-1">
                <span className="text-xs text-gray-500">
                  vs {getMetricValue(metricKey, metricData.previous_value)} previously
                </span>
              </div>
            )}
          </div>
        ))}
      </div>

      {metricEntries.length === 0 && (
        <div className="no-metrics text-center py-8">
          <div className="text-gray-400 mb-2">
            <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <p className="text-gray-500">No metrics available for this period</p>
        </div>
      )}

      <div className="metrics-footer mt-4 pt-4 border-t border-gray-200">
        <div className="flex items-center justify-between text-xs text-gray-500">
          <span>Data updates every {refreshInterval / 1000} seconds</span>
          <button
            onClick={fetchMetrics}
            disabled={loading}
            className="text-blue-600 hover:text-blue-800 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Refreshing...' : 'Refresh Now'}
          </button>
        </div>
      </div>
    </div>
  );
};

// Social proof counter component
interface SocialProofCounterProps {
  metricKey: string;
  label: string;
  format?: 'number' | 'percentage' | 'decimal';
  refreshInterval?: number;
  className?: string;
}

export const SocialProofCounter: React.FC<SocialProofCounterProps> = ({
  metricKey,
  label,
  format = 'number',
  refreshInterval = 30000,
  className = ''
}) => {
  const [value, setValue] = useState<number>(0);
  const [loading, setLoading] = useState(true);

  const fetchValue = async () => {
    try {
      const response = await fetch('/api/analytics/real-time', {
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });

      if (response.ok) {
        const data = await response.json();
        const metricData = data.real_time_metrics?.[metricKey];
        if (metricData) {
          setValue(metricData.value);
        }
      }
    } catch (error) {
      console.error('Error fetching social proof counter:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchValue();
    const interval = setInterval(fetchValue, refreshInterval);
    return () => clearInterval(interval);
  }, [metricKey, refreshInterval]);

  const formatValue = (val: number): string => {
    switch (format) {
      case 'percentage':
        return `${val.toFixed(1)}%`;
      case 'decimal':
        return val.toFixed(1);
      default:
        return val.toLocaleString();
    }
  };

  if (loading) {
    return (
      <div className={`social-proof-counter loading ${className}`}>
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-16"></div>
        </div>
      </div>
    );
  }

  return (
    <div className={`social-proof-counter ${className}`}>
      <span className="counter-value font-bold text-lg">
        {formatValue(value)}
      </span>
      <span className="counter-label text-sm text-gray-600 ml-1">
        {label}
      </span>
    </div>
  );
};

// Live completion counter for social proof
export const LiveCompletionCounter: React.FC<{ assessmentType?: string; className?: string }> = ({
  assessmentType,
  className = ''
}) => {
  return (
    <SocialProofCounter
      metricKey="assessments_completed_today"
      label="completed today"
      format="number"
      className={className}
    />
  );
};

// Live conversion rate display
export const LiveConversionRate: React.FC<{ assessmentType?: string; className?: string }> = ({
  assessmentType,
  className = ''
}) => {
  return (
    <SocialProofCounter
      metricKey="conversion_rate_today"
      label="conversion rate"
      format="percentage"
      className={className}
    />
  );
};

// Live active users counter
export const LiveActiveUsers: React.FC<{ className?: string }> = ({ className = '' }) => {
  return (
    <SocialProofCounter
      metricKey="active_users_now"
      label="active now"
      format="number"
      className={className}
    />
  );
};

export default RealTimeMetrics;
