import React, { useState, useEffect, useCallback } from 'react';
import RealTimeMetrics from './RealTimeMetrics';

// Types
interface ConversionFunnelData {
  total_sessions: number;
  conversion_rates: {
    [key: string]: {
      count: number;
      rate: number;
      drop_off: number;
    };
  };
  drop_off_analysis: {
    [key: string]: number;
  };
  time_period_days: number;
  assessment_type?: string;
}

interface LeadQualityData {
  total_leads: number;
  quality_distribution: {
    [key: string]: number;
  };
  conversion_by_quality: {
    [key: string]: {
      total: number;
      converted: number;
    };
  };
  average_score: number;
  average_completion_time: number;
  time_period_days: number;
  assessment_type?: string;
}

interface PerformanceData {
  performance_metrics: {
    [key: string]: {
      average_ms?: number;
      average_percentage?: number;
      count: number;
    };
  };
  time_period_days: number;
  total_metrics: number;
}

interface GeographicData {
  geographic_data: {
    [key: string]: {
      total_sessions: number;
      completed_assessments: number;
      conversion_rate: number;
      average_score: number;
      average_completion_time: number;
      average_page_load_time: number;
      error_rate: number;
    };
  };
  time_period_days: number;
  total_countries: number;
}

interface DashboardData {
  real_time_metrics: any;
  conversion_funnel: ConversionFunnelData;
  lead_quality_metrics: LeadQualityData;
  performance_metrics: PerformanceData;
  geographic_analytics: GeographicData;
  last_updated: string;
}

const AnalyticsDashboard: React.FC = () => {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedAssessmentType, setSelectedAssessmentType] = useState<string>('all');
  const [timePeriod, setTimePeriod] = useState<number>(30);
  const [activeTab, setActiveTab] = useState<string>('overview');

  // Fetch dashboard data
  const fetchDashboardData = useCallback(async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/analytics/dashboard', {
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      setDashboardData(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboard data');
      console.error('Error fetching dashboard data:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch specific analytics data
  const fetchAnalyticsData = useCallback(async (endpoint: string, params?: Record<string, any>) => {
    try {
      const url = new URL(`/api/analytics/${endpoint}`, window.location.origin);
      if (params) {
        Object.entries(params).forEach(([key, value]) => {
          url.searchParams.append(key, value.toString());
        });
      }

      const response = await fetch(url.toString(), {
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`Error fetching ${endpoint}:`, error);
      throw error;
    }
  }, []);

  // Load initial data
  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  // Refresh data when parameters change
  useEffect(() => {
    if (activeTab !== 'overview') {
      fetchDashboardData();
    }
  }, [activeTab, selectedAssessmentType, timePeriod, fetchDashboardData]);

  // Export data
  const exportData = useCallback(async (dataType: string) => {
    try {
      const startDate = new Date();
      startDate.setDate(startDate.getDate() - timePeriod);
      
      const params = {
        start_date: startDate.toISOString(),
        end_date: new Date().toISOString(),
        data_type: dataType
      };

      if (selectedAssessmentType !== 'all') {
        params.assessment_type = selectedAssessmentType;
      }

      const data = await fetchAnalyticsData('export', params);
      
      // Create and download CSV
      const csvContent = convertToCSV(data.data);
      const blob = new Blob([csvContent], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${dataType}_export_${new Date().toISOString().split('T')[0]}.csv`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error exporting data:', error);
    }
  }, [fetchAnalyticsData, selectedAssessmentType, timePeriod]);

  // Convert data to CSV
  const convertToCSV = (data: any[]): string => {
    if (!data || data.length === 0) return '';
    
    const headers = Object.keys(data[0]);
    const csvRows = [headers.join(',')];
    
    for (const row of data) {
      const values = headers.map(header => {
        const value = row[header];
        return typeof value === 'string' ? `"${value}"` : value;
      });
      csvRows.push(values.join(','));
    }
    
    return csvRows.join('\n');
  };

  // Get conversion funnel stages
  const getFunnelStages = (): string[] => {
    return [
      'landing_view',
      'assessment_start',
      'assessment_complete',
      'email_capture',
      'conversion_modal',
      'payment_attempt',
      'payment_success'
    ];
  };

  // Get risk level color
  const getRiskLevelColor = (level: string): string => {
    switch (level.toLowerCase()) {
      case 'low': return 'text-green-600 bg-green-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'high': return 'text-orange-600 bg-orange-100';
      case 'critical': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  // Get lead quality color
  const getLeadQualityColor = (quality: string): string => {
    switch (quality.toLowerCase()) {
      case 'hot': return 'text-red-600 bg-red-100';
      case 'warm': return 'text-orange-600 bg-orange-100';
      case 'cold': return 'text-blue-600 bg-blue-100';
      case 'unqualified': return 'text-gray-600 bg-gray-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <div className="text-gray-600">Loading analytics dashboard...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-600 text-xl mb-4">Error Loading Dashboard</div>
          <div className="text-gray-600 mb-4">{error}</div>
          <button
            onClick={fetchDashboardData}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                Analytics Dashboard
              </h1>
              <p className="text-gray-600 mt-2">
                Comprehensive analytics and insights for assessment system
              </p>
            </div>
            
            <div className="flex items-center space-x-4">
              <select
                value={selectedAssessmentType}
                onChange={(e) => setSelectedAssessmentType(e.target.value)}
                className="border border-gray-300 rounded-lg px-3 py-2 text-sm"
              >
                <option value="all">All Assessments</option>
                <option value="ai_job_risk">AI Job Risk</option>
                <option value="relationship_impact">Relationship Impact</option>
                <option value="tax_impact">Tax Impact</option>
                <option value="income_comparison">Income Comparison</option>
              </select>
              
              <select
                value={timePeriod}
                onChange={(e) => setTimePeriod(Number(e.target.value))}
                className="border border-gray-300 rounded-lg px-3 py-2 text-sm"
              >
                <option value={7}>Last 7 days</option>
                <option value={30}>Last 30 days</option>
                <option value={90}>Last 90 days</option>
                <option value={365}>Last year</option>
              </select>
              
              <button
                onClick={() => fetchDashboardData()}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
              >
                Refresh
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Navigation Tabs */}
        <div className="mb-8">
          <nav className="flex space-x-8">
            {[
              { id: 'overview', label: 'Overview' },
              { id: 'conversion', label: 'Conversion Funnel' },
              { id: 'leads', label: 'Lead Quality' },
              { id: 'performance', label: 'Performance' },
              { id: 'geographic', label: 'Geographic' }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {/* Overview Tab */}
        {activeTab === 'overview' && dashboardData && (
          <div className="space-y-8">
            {/* Real-time Metrics */}
            <div>
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Real-time Metrics</h2>
              <RealTimeMetrics 
                assessmentType={selectedAssessmentType !== 'all' ? selectedAssessmentType : undefined}
                refreshInterval={30000}
                showChangeIndicator={true}
              />
            </div>

            {/* Quick Stats */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                      <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                      </svg>
                    </div>
                  </div>
                  <div className="ml-4">
                    <div className="text-2xl font-bold text-gray-900">
                      {dashboardData.conversion_funnel.total_sessions.toLocaleString()}
                    </div>
                    <div className="text-sm text-gray-600">Total Sessions</div>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
                      <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </div>
                  </div>
                  <div className="ml-4">
                    <div className="text-2xl font-bold text-gray-900">
                      {dashboardData.lead_quality_metrics.total_leads.toLocaleString()}
                    </div>
                    <div className="text-sm text-gray-600">Total Leads</div>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center">
                      <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                      </svg>
                    </div>
                  </div>
                  <div className="ml-4">
                    <div className="text-2xl font-bold text-gray-900">
                      {dashboardData.lead_quality_metrics.average_score.toFixed(1)}%
                    </div>
                    <div className="text-sm text-gray-600">Average Score</div>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 bg-orange-100 rounded-lg flex items-center justify-center">
                      <svg className="w-5 h-5 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </div>
                  </div>
                  <div className="ml-4">
                    <div className="text-2xl font-bold text-gray-900">
                      {Math.round(dashboardData.lead_quality_metrics.average_completion_time / 60)}m
                    </div>
                    <div className="text-sm text-gray-600">Avg. Completion Time</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Conversion Funnel Tab */}
        {activeTab === 'conversion' && dashboardData && (
          <div className="space-y-8">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-bold text-gray-900">Conversion Funnel Analysis</h2>
              <button
                onClick={() => exportData('funnel')}
                className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors"
              >
                Export Data
              </button>
            </div>

            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="space-y-6">
                {getFunnelStages().map((stage, index) => {
                  const stageData = dashboardData.conversion_funnel.conversion_rates[stage];
                  if (!stageData) return null;

                  const previousStage = index > 0 ? getFunnelStages()[index - 1] : null;
                  const previousData = previousStage ? dashboardData.conversion_funnel.conversion_rates[previousStage] : null;
                  const conversionRate = previousData ? (stageData.count / previousData.count * 100) : 100;

                  return (
                    <div key={stage} className="flex items-center space-x-4">
                      <div className="w-24 text-sm font-medium text-gray-600 capitalize">
                        {stage.replace(/_/g, ' ')}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-lg font-semibold text-gray-900">
                            {stageData.count.toLocaleString()}
                          </span>
                          <span className="text-sm text-gray-600">
                            {conversionRate.toFixed(1)}% conversion
                          </span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                            style={{ width: `${conversionRate}%` }}
                          ></div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Drop-off Analysis */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Drop-off Analysis</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {Object.entries(dashboardData.conversion_funnel.drop_off_analysis).map(([stage, count]) => (
                  <div key={stage} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <span className="text-sm font-medium text-gray-700 capitalize">
                      {stage.replace(/_/g, ' ')}
                    </span>
                    <span className="text-sm font-semibold text-red-600">
                      {count.toLocaleString()} dropped
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Lead Quality Tab */}
        {activeTab === 'leads' && dashboardData && (
          <div className="space-y-8">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-bold text-gray-900">Lead Quality Analysis</h2>
              <button
                onClick={() => exportData('leads')}
                className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors"
              >
                Export Data
              </button>
            </div>

            {/* Quality Distribution */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Lead Quality Distribution</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {Object.entries(dashboardData.lead_quality_metrics.quality_distribution).map(([quality, count]) => (
                  <div key={quality} className="text-center p-4 bg-gray-50 rounded-lg">
                    <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium mb-2 ${getLeadQualityColor(quality)}`}>
                      {quality.charAt(0).toUpperCase() + quality.slice(1)}
                    </div>
                    <div className="text-2xl font-bold text-gray-900">{count.toLocaleString()}</div>
                    <div className="text-sm text-gray-600">
                      {((count / dashboardData.lead_quality_metrics.total_leads) * 100).toFixed(1)}%
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Conversion by Quality */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Conversion by Lead Quality</h3>
              <div className="space-y-4">
                {Object.entries(dashboardData.lead_quality_metrics.conversion_by_quality).map(([quality, data]) => {
                  const conversionRate = data.total > 0 ? (data.converted / data.total * 100) : 0;
                  return (
                    <div key={quality} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                      <div className="flex items-center space-x-3">
                        <span className={`px-2 py-1 rounded text-xs font-medium ${getLeadQualityColor(quality)}`}>
                          {quality.charAt(0).toUpperCase() + quality.slice(1)}
                        </span>
                        <span className="text-sm text-gray-600">
                          {data.converted} / {data.total} converted
                        </span>
                      </div>
                      <span className="text-lg font-semibold text-gray-900">
                        {conversionRate.toFixed(1)}%
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {/* Performance Tab */}
        {activeTab === 'performance' && dashboardData && (
          <div className="space-y-8">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-bold text-gray-900">Performance Metrics</h2>
              <button
                onClick={() => exportData('performance')}
                className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors"
              >
                Export Data
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {Object.entries(dashboardData.performance_metrics.performance_metrics).map(([metric, data]) => (
                <div key={metric} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4 capitalize">
                    {metric.replace(/_/g, ' ')}
                  </h3>
                  <div className="space-y-3">
                    {data.average_ms !== undefined && (
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Average:</span>
                        <span className="text-sm font-medium">{data.average_ms.toFixed(2)}ms</span>
                      </div>
                    )}
                    {data.average_percentage !== undefined && (
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Average:</span>
                        <span className="text-sm font-medium">{data.average_percentage.toFixed(2)}%</span>
                      </div>
                    )}
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Total Records:</span>
                      <span className="text-sm font-medium">{data.count.toLocaleString()}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Geographic Tab */}
        {activeTab === 'geographic' && dashboardData && (
          <div className="space-y-8">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-bold text-gray-900">Geographic Analytics</h2>
              <button
                onClick={() => exportData('geographic')}
                className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors"
              >
                Export Data
              </button>
            </div>

            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Country
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Sessions
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Completed
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Conversion Rate
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Avg Score
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Avg Load Time
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {Object.entries(dashboardData.geographic_analytics.geographic_data)
                      .sort(([, a], [, b]) => b.total_sessions - a.total_sessions)
                      .slice(0, 20)
                      .map(([country, data]) => (
                        <tr key={country}>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                            {country}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {data.total_sessions.toLocaleString()}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {data.completed_assessments.toLocaleString()}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {data.conversion_rate.toFixed(1)}%
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {data.average_score.toFixed(1)}%
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {data.average_page_load_time.toFixed(0)}ms
                          </td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AnalyticsDashboard;
