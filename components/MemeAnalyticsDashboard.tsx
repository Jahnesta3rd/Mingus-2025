import React, { useState, useEffect, useCallback } from 'react';
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

// TypeScript interfaces
interface MemeEngagementMetrics {
  total_views: number;
  total_skips: number;
  total_likes: number;
  total_shares: number;
  total_conversions: number;
  skip_rate: number;
  engagement_rate: number;
  conversion_rate: number;
  avg_time_spent: number;
  unique_users: number;
}

interface MemeCategoryMetrics {
  category: string;
  total_views: number;
  total_skips: number;
  skip_rate: number;
  engagement_rate: number;
  avg_time_spent: number;
  unique_users: number;
  conversion_rate: number;
}

interface DailyTrend {
  date: string;
  total_views: number;
  total_skips: number;
  skip_rate: number;
  engagement_rate: number;
  unique_users: number;
  avg_time_spent: number;
}

interface MemeAlert {
  alert_id: string;
  alert_type: string;
  severity: string;
  message: string;
  threshold: number;
  current_value: number;
  timestamp: string;
  is_resolved: boolean;
  resolved_at?: string;
}

interface MemeAnalyticsDashboardProps {
  className?: string;
}

// Color scheme for charts
const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D'];

// Loading skeleton component
const DashboardSkeleton: React.FC = () => (
  <div className="animate-pulse space-y-6">
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
      {[1, 2, 3, 4].map((i) => (
        <div key={i} className="bg-gray-200 rounded-lg p-4 h-24"></div>
      ))}
    </div>
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div className="bg-gray-200 rounded-lg p-4 h-80"></div>
      <div className="bg-gray-200 rounded-lg p-4 h-80"></div>
    </div>
  </div>
);

// Main component
const MemeAnalyticsDashboard: React.FC<MemeAnalyticsDashboardProps> = ({
  className = ''
}) => {
  // State management
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dateRange, setDateRange] = useState('30'); // days
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  
  // Data state
  const [engagementMetrics, setEngagementMetrics] = useState<MemeEngagementMetrics | null>(null);
  const [categoryMetrics, setCategoryMetrics] = useState<MemeCategoryMetrics[]>([]);
  const [dailyTrends, setDailyTrends] = useState<DailyTrend[]>([]);
  const [alerts, setAlerts] = useState<MemeAlert[]>([]);
  const [sampleReports, setSampleReports] = useState<any[]>([]);

  // Fetch dashboard data
  const fetchDashboardData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const params = new URLSearchParams({
        days: dateRange
      });

      if (selectedCategory !== 'all') {
        params.append('category', selectedCategory);
      }

      const response = await fetch(`/api/meme-analytics/dashboard/metrics?${params}`, {
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      if (data.success) {
        setEngagementMetrics(data.data.engagement_metrics);
        setCategoryMetrics(data.data.category_metrics);
        setDailyTrends(data.data.daily_trends);
      } else {
        throw new Error(data.error || 'Failed to load dashboard data');
      }
    } catch (err) {
      console.error('Error fetching dashboard data:', err);
      setError(err instanceof Error ? err.message : 'Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  }, [dateRange, selectedCategory]);

  // Fetch alerts
  const fetchAlerts = useCallback(async () => {
    try {
      const response = await fetch('/api/meme-analytics/alerts', {
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setAlerts(data.data.alerts);
        }
      }
    } catch (err) {
      console.error('Error fetching alerts:', err);
    }
  }, []);

  // Fetch sample reports
  const fetchSampleReports = useCallback(async () => {
    try {
      const response = await fetch('/api/meme-analytics/sample-reports', {
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setSampleReports(data.data.sample_reports);
        }
      }
    } catch (err) {
      console.error('Error fetching sample reports:', err);
    }
  }, []);

  // Export data
  const exportData = useCallback(async (format: 'csv' | 'json') => {
    try {
      const params = new URLSearchParams({
        format: format,
        days: dateRange
      });

      const response = await fetch(`/api/meme-analytics/export?${params}`, {
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (response.ok) {
        if (format === 'csv') {
          const blob = await response.blob();
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `meme_analytics_${new Date().toISOString().split('T')[0]}.csv`;
          document.body.appendChild(a);
          a.click();
          window.URL.revokeObjectURL(url);
          document.body.removeChild(a);
        } else {
          const data = await response.json();
          const blob = new Blob([JSON.stringify(data.data, null, 2)], { type: 'application/json' });
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `meme_analytics_${new Date().toISOString().split('T')[0]}.json`;
          document.body.appendChild(a);
          a.click();
          window.URL.revokeObjectURL(url);
          document.body.removeChild(a);
        }
      }
    } catch (err) {
      console.error('Error exporting data:', err);
      setError('Failed to export data');
    }
  }, [dateRange]);

  // Load data on mount and when filters change
  useEffect(() => {
    fetchDashboardData();
    fetchAlerts();
    fetchSampleReports();
  }, [fetchDashboardData, fetchAlerts, fetchSampleReports]);

  // Loading state
  if (loading) {
    return (
      <div className={`bg-white rounded-lg shadow-lg p-6 ${className}`}>
        <DashboardSkeleton />
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg shadow-lg overflow-hidden ${className}`}>
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 to-blue-600 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-white">Meme Analytics Dashboard</h2>
            <p className="text-purple-100 text-sm">Track the success of your meme splash page feature</p>
          </div>
          <div className="flex items-center space-x-4">
            <select
              value={dateRange}
              onChange={(e) => setDateRange(e.target.value)}
              className="bg-white bg-opacity-20 text-white border border-white border-opacity-30 rounded px-3 py-1 text-sm"
            >
              <option value="7">Last 7 days</option>
              <option value="30">Last 30 days</option>
              <option value="90">Last 90 days</option>
            </select>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="bg-white bg-opacity-20 text-white border border-white border-opacity-30 rounded px-3 py-1 text-sm"
            >
              <option value="all">All Categories</option>
              <option value="faith">Faith & Spirituality</option>
              <option value="work_life">Work & Career</option>
              <option value="friendships">Friendships</option>
              <option value="children">Parenting & Children</option>
              <option value="relationships">Relationships</option>
              <option value="going_out">Social Life</option>
            </select>
          </div>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mx-6 mt-6">
          <div className="flex items-center">
            <svg className="w-5 h-5 text-red-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
            <span className="text-red-800 font-medium">{error}</span>
          </div>
        </div>
      )}

      {/* Content */}
      <div className="p-6 space-y-6">
        {/* Key Metrics */}
        {engagementMetrics && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
              <div className="flex items-center">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-blue-600">Total Views</p>
                  <p className="text-2xl font-bold text-blue-900">{engagementMetrics.total_views.toLocaleString()}</p>
                </div>
              </div>
            </div>

            <div className="bg-green-50 rounded-lg p-4 border border-green-200">
              <div className="flex items-center">
                <div className="p-2 bg-green-100 rounded-lg">
                  <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5" />
                  </svg>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-green-600">Engagement Rate</p>
                  <p className="text-2xl font-bold text-green-900">{engagementMetrics.engagement_rate.toFixed(1)}%</p>
                </div>
              </div>
            </div>

            <div className="bg-orange-50 rounded-lg p-4 border border-orange-200">
              <div className="flex items-center">
                <div className="p-2 bg-orange-100 rounded-lg">
                  <svg className="w-6 h-6 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-orange-600">Avg Time Spent</p>
                  <p className="text-2xl font-bold text-orange-900">{engagementMetrics.avg_time_spent.toFixed(1)}s</p>
                </div>
              </div>
            </div>

            <div className="bg-purple-50 rounded-lg p-4 border border-purple-200">
              <div className="flex items-center">
                <div className="p-2 bg-purple-100 rounded-lg">
                  <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                  </svg>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-purple-600">Unique Users</p>
                  <p className="text-2xl font-bold text-purple-900">{engagementMetrics.unique_users.toLocaleString()}</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Daily Trends Chart */}
          <div className="bg-gray-50 rounded-lg p-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Daily Engagement Trends</h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={dailyTrends}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="engagement_rate" stroke="#10B981" strokeWidth={2} name="Engagement Rate (%)" />
                <Line type="monotone" dataKey="skip_rate" stroke="#EF4444" strokeWidth={2} name="Skip Rate (%)" />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Category Performance Chart */}
          <div className="bg-gray-50 rounded-lg p-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Category Performance</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={categoryMetrics}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="category" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="engagement_rate" fill="#10B981" name="Engagement Rate (%)" />
                <Bar dataKey="skip_rate" fill="#EF4444" name="Skip Rate (%)" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Alerts Section */}
        {alerts.length > 0 && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <h3 className="text-lg font-semibold text-yellow-900 mb-3">Active Alerts</h3>
            <div className="space-y-2">
              {alerts.map((alert) => (
                <div key={alert.alert_id} className="flex items-center justify-between p-3 bg-white rounded border border-yellow-200">
                  <div className="flex items-center">
                    <div className={`p-2 rounded-full mr-3 ${
                      alert.severity === 'critical' ? 'bg-red-100' : 'bg-yellow-100'
                    }`}>
                      <svg className={`w-4 h-4 ${
                        alert.severity === 'critical' ? 'text-red-600' : 'text-yellow-600'
                      }`} fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">{alert.message}</p>
                      <p className="text-sm text-gray-600">
                        Current: {alert.current_value.toFixed(1)}% | Threshold: {alert.threshold.toFixed(1)}%
                      </p>
                    </div>
                  </div>
                  <span className={`px-2 py-1 rounded text-xs font-medium ${
                    alert.severity === 'critical' ? 'bg-red-100 text-red-800' : 'bg-yellow-100 text-yellow-800'
                  }`}>
                    {alert.severity}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Sample Reports */}
        {sampleReports.length > 0 && (
          <div className="bg-gray-50 rounded-lg p-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Sample Reports</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {sampleReports.map((report, index) => (
                <div key={index} className="bg-white rounded-lg p-4 border border-gray-200">
                  <h4 className="font-semibold text-gray-900 mb-2">{report.name}</h4>
                  <p className="text-sm text-gray-600 mb-3">{report.period}</p>
                  {report.metrics && (
                    <div className="space-y-1">
                      {Object.entries(report.metrics).map(([key, value]) => (
                        <div key={key} className="flex justify-between text-sm">
                          <span className="text-gray-600">{key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}:</span>
                          <span className="font-medium">{value}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Export Section */}
        <div className="bg-gray-50 rounded-lg p-4">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Export Data</h3>
          <div className="flex space-x-4">
            <button
              onClick={() => exportData('csv')}
              className="bg-green-600 hover:bg-green-700 text-white font-semibold py-2 px-4 rounded-lg transition-colors focus:outline-none focus:ring-4 focus:ring-green-500 focus:ring-opacity-50"
            >
              Export as CSV
            </button>
            <button
              onClick={() => exportData('json')}
              className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-lg transition-colors focus:outline-none focus:ring-4 focus:ring-blue-500 focus:ring-opacity-50"
            >
              Export as JSON
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MemeAnalyticsDashboard;
