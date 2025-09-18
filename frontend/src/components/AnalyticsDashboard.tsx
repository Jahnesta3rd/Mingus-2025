import React, { useState, useEffect } from 'react';
import { 
  BarChart, 
  Bar, 
  LineChart, 
  Line, 
  PieChart, 
  Pie, 
  Cell, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer,
  AreaChart,
  Area
} from 'recharts';
import { 
  TrendingUp, 
  TrendingDown, 
  Users, 
  Target, 
  AlertTriangle, 
  CheckCircle,
  RefreshCw,
  Download
} from 'lucide-react';

interface AnalyticsData {
  risk_trends: Array<{
    date: string;
    high_risk: number;
    medium_risk: number;
    low_risk: number;
    total_assessments: number;
  }>;
  success_metrics: {
    total_users: number;
    successful_transitions: number;
    success_rate: number;
    average_salary_increase: number;
  };
  industry_breakdown: Array<{
    industry: string;
    count: number;
    percentage: number;
    color: string;
  }>;
  monthly_performance: Array<{
    month: string;
    assessments: number;
    recommendations: number;
    applications: number;
    success_rate: number;
  }>;
}

interface AnalyticsDashboardProps {
  className?: string;
}

const AnalyticsDashboard: React.FC<AnalyticsDashboardProps> = ({ className = '' }) => {
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [timeRange, setTimeRange] = useState('30_days');
  // const [selectedMetric, setSelectedMetric] = useState('overview');

  useEffect(() => {
    fetchAnalyticsData();
  }, [timeRange]);

  const fetchAnalyticsData = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch('/api/analytics/dashboard', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRF-Token': getCSRFToken()
        },
        body: JSON.stringify({
          time_range: timeRange,
          include_breakdowns: true,
          include_trends: true
        })
      });

      if (!response.ok) {
        throw new Error('Failed to fetch analytics data');
      }

      const data = await response.json();
      setAnalyticsData(data.analytics);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load analytics');
      console.error('Analytics fetch failed:', err);
    } finally {
      setLoading(false);
    }
  };

  // const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

  if (loading) {
    return <AnalyticsSkeleton />;
  }

  if (error) {
    return (
      <div className={`bg-red-50 border border-red-200 rounded-xl p-8 text-center ${className}`}>
        <AlertTriangle className="h-12 w-12 text-red-400 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-red-900 mb-2">Analytics Unavailable</h3>
        <p className="text-red-700 mb-4">{error}</p>
        <button
          onClick={fetchAnalyticsData}
          className="bg-red-600 hover:bg-red-700 text-white px-6 py-2 rounded-lg font-medium transition-colors"
        >
          Try Again
        </button>
      </div>
    );
  }

  if (!analyticsData) {
    return (
      <div className={`bg-gray-50 border border-gray-200 rounded-xl p-8 text-center ${className}`}>
        <Target className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-gray-900 mb-2">No Analytics Data</h3>
        <p className="text-gray-600">Analytics data will appear here once users start using the platform.</p>
      </div>
    );
  }

  return (
    <div className={`space-y-8 ${className}`}>
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Career Analytics</h2>
          <p className="text-gray-600">Comprehensive insights into career protection and job matching</p>
        </div>
        
        <div className="flex gap-3">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="7_days">Last 7 days</option>
            <option value="30_days">Last 30 days</option>
            <option value="90_days">Last 90 days</option>
            <option value="1_year">Last year</option>
          </select>
          
          <button
            onClick={fetchAnalyticsData}
            className="bg-gray-100 hover:bg-gray-200 border border-gray-300 rounded-lg px-4 py-2 text-sm font-medium transition-colors flex items-center gap-2"
          >
            <RefreshCw className="h-4 w-4" />
            Refresh
          </button>
          
          <button
            onClick={() => {/* Export functionality */}}
            className="bg-blue-600 hover:bg-blue-700 text-white rounded-lg px-4 py-2 text-sm font-medium transition-colors flex items-center gap-2"
          >
            <Download className="h-4 w-4" />
            Export
          </button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Total Users"
          value={analyticsData.success_metrics.total_users.toLocaleString()}
          icon={<Users className="h-6 w-6" />}
          trend="+12%"
          trendUp={true}
        />
        <MetricCard
          title="Successful Transitions"
          value={analyticsData.success_metrics.successful_transitions.toLocaleString()}
          icon={<CheckCircle className="h-6 w-6" />}
          trend="+8%"
          trendUp={true}
        />
        <MetricCard
          title="Success Rate"
          value={`${analyticsData.success_metrics.success_rate}%`}
          icon={<Target className="h-6 w-6" />}
          trend="+2.3%"
          trendUp={true}
        />
        <MetricCard
          title="Avg Salary Increase"
          value={`+${analyticsData.success_metrics.average_salary_increase}%`}
          icon={<TrendingUp className="h-6 w-6" />}
          trend="+5.1%"
          trendUp={true}
        />
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Risk Trends Chart */}
        <div className="bg-white border border-gray-200 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Risk Assessment Trends</h3>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={analyticsData.risk_trends}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="date" 
                tickFormatter={(value: any) => new Date(value).toLocaleDateString()}
              />
              <YAxis />
              <Tooltip 
                labelFormatter={(value: any) => new Date(value).toLocaleDateString()}
              />
              <Legend />
              <Area 
                type="monotone" 
                dataKey="high_risk" 
                stackId="1" 
                stroke="#ef4444" 
                fill="#ef4444" 
                fillOpacity={0.6}
                name="High Risk"
              />
              <Area 
                type="monotone" 
                dataKey="medium_risk" 
                stackId="1" 
                stroke="#f59e0b" 
                fill="#f59e0b" 
                fillOpacity={0.6}
                name="Medium Risk"
              />
              <Area 
                type="monotone" 
                dataKey="low_risk" 
                stackId="1" 
                stroke="#10b981" 
                fill="#10b981" 
                fillOpacity={0.6}
                name="Low Risk"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Industry Breakdown */}
        <div className="bg-white border border-gray-200 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Industry Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={analyticsData.industry_breakdown}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ industry, percentage }: any) => `${industry} (${percentage}%)`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="count"
              >
                {analyticsData.industry_breakdown.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Monthly Performance */}
        <div className="bg-white border border-gray-200 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Monthly Performance</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={analyticsData.monthly_performance}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis yAxisId="left" />
              <YAxis yAxisId="right" orientation="right" />
              <Tooltip />
              <Legend />
              <Bar yAxisId="left" dataKey="assessments" fill="#3b82f6" name="Assessments" />
              <Bar yAxisId="left" dataKey="recommendations" fill="#10b981" name="Recommendations" />
              <Bar yAxisId="left" dataKey="applications" fill="#f59e0b" name="Applications" />
              <Line 
                yAxisId="right" 
                type="monotone" 
                dataKey="success_rate" 
                stroke="#ef4444" 
                strokeWidth={2}
                name="Success Rate %"
              />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Success Rate Trend */}
        <div className="bg-white border border-gray-200 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Success Rate Over Time</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={analyticsData.monthly_performance}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis domain={[0, 100]} />
              <Tooltip 
                formatter={(value: any) => [`${value}%`, 'Success Rate']}
              />
              <Line 
                type="monotone" 
                dataKey="success_rate" 
                stroke="#10b981" 
                strokeWidth={3}
                dot={{ fill: '#10b981', strokeWidth: 2, r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};

// Metric Card Component
const MetricCard: React.FC<{
  title: string;
  value: string;
  icon: React.ReactNode;
  trend: string;
  trendUp: boolean;
}> = ({ title, value, icon, trend, trendUp }) => {
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="text-gray-600 text-sm font-medium">{title}</div>
        <div className="text-gray-400">{icon}</div>
      </div>
      <div className="text-2xl font-bold text-gray-900 mb-2">{value}</div>
      <div className={`flex items-center text-sm ${
        trendUp ? 'text-green-600' : 'text-red-600'
      }`}>
        {trendUp ? (
          <TrendingUp className="h-4 w-4 mr-1" />
        ) : (
          <TrendingDown className="h-4 w-4 mr-1" />
        )}
        {trend} from last period
      </div>
    </div>
  );
};

// Loading Skeleton
const AnalyticsSkeleton: React.FC = () => {
  return (
    <div className="space-y-8">
      <div className="flex justify-between items-center">
        <div>
          <div className="h-8 w-64 bg-gray-200 rounded animate-pulse mb-2" />
          <div className="h-4 w-96 bg-gray-200 rounded animate-pulse" />
        </div>
        <div className="flex gap-3">
          <div className="h-10 w-32 bg-gray-200 rounded animate-pulse" />
          <div className="h-10 w-24 bg-gray-200 rounded animate-pulse" />
          <div className="h-10 w-24 bg-gray-200 rounded animate-pulse" />
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="bg-white border border-gray-200 rounded-xl p-6">
            <div className="flex justify-between items-center mb-4">
              <div className="h-4 w-24 bg-gray-200 rounded animate-pulse" />
              <div className="h-6 w-6 bg-gray-200 rounded animate-pulse" />
            </div>
            <div className="h-8 w-16 bg-gray-200 rounded animate-pulse mb-2" />
            <div className="h-4 w-20 bg-gray-200 rounded animate-pulse" />
          </div>
        ))}
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="bg-white border border-gray-200 rounded-xl p-6">
            <div className="h-6 w-48 bg-gray-200 rounded animate-pulse mb-4" />
            <div className="h-64 bg-gray-100 rounded animate-pulse" />
          </div>
        ))}
      </div>
    </div>
  );
};

// Helper Functions
const getCSRFToken = (): string => {
  const metaTag = document.querySelector('meta[name="csrf-token"]');
  if (metaTag) {
    return metaTag.getAttribute('content') || '';
  }
  
  const cookies = document.cookie.split(';');
  for (let cookie of cookies) {
    const [name, value] = cookie.trim().split('=');
    if (name === 'csrf_token') {
      return value;
    }
  }
  
  return '';
};

export default AnalyticsDashboard;
