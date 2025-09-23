import React, { useState, useEffect } from 'react';
import { 
  Chart as ChartJS, 
  CategoryScale, 
  LinearScale, 
  BarElement, 
  LineElement, 
  PointElement, 
  Title, 
  Tooltip, 
  Legend,
  ArcElement
} from 'chart.js';
import { Bar, Line, Doughnut } from 'react-chartjs-2';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
);

interface TestVariant {
  variant_id: string;
  variant_name: string;
  variant_type: 'control' | 'variant';
  content_config: any;
  weight: number;
  is_control: boolean;
}

interface UserSegment {
  segment_id: string;
  segment_name: string;
  criteria: any;
  user_count: number;
  description: string;
}

interface TestMetrics {
  variant_id: string;
  users_exposed: number;
  users_engaged: number;
  conversions: number;
  revenue_impact: number;
  engagement_rate: number;
  conversion_rate: number;
  statistical_significance: number;
  confidence_interval: [number, number];
  p_value: number;
}

interface ABTest {
  test_id: string;
  test_name: string;
  test_type: string;
  description: string;
  status: 'draft' | 'active' | 'paused' | 'completed' | 'cancelled';
  variants: TestVariant[];
  target_segments: UserSegment[];
  success_metrics: string[];
  duration_days: number;
  traffic_allocation: number;
  created_at: string;
  started_at?: string;
  ended_at?: string;
}

interface TestResult {
  test_id: string;
  winner_variant?: string;
  is_statistically_significant: boolean;
  confidence_level: number;
  effect_size: number;
  recommendations: string[];
  metrics: TestMetrics[];
}

const ABTestingManager: React.FC = () => {
  const [tests, setTests] = useState<ABTest[]>([]);
  const [selectedTest, setSelectedTest] = useState<ABTest | null>(null);
  const [testResults, setTestResults] = useState<TestResult | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form state for creating new tests
  const [newTest, setNewTest] = useState({
    test_name: '',
    test_type: 'content_format',
    description: '',
    duration_days: 14,
    traffic_allocation: 0.5
  });

  useEffect(() => {
    fetchTests();
  }, []);

  const fetchTests = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/ab-tests');
      if (response.ok) {
        const data = await response.json();
        setTests(data.tests || []);
      }
    } catch (err) {
      setError('Failed to fetch tests');
    } finally {
      setLoading(false);
    }
  };

  const fetchTestResults = async (testId: string) => {
    try {
      const response = await fetch(`/api/ab-tests/${testId}/results`);
      if (response.ok) {
        const data = await response.json();
        setTestResults(data);
      }
    } catch (err) {
      setError('Failed to fetch test results');
    }
  };

  const createTest = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/ab-tests', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(newTest),
      });

      if (response.ok) {
        setShowCreateModal(false);
        setNewTest({
          test_name: '',
          test_type: 'content_format',
          description: '',
          duration_days: 14,
          traffic_allocation: 0.5
        });
        fetchTests();
      } else {
        setError('Failed to create test');
      }
    } catch (err) {
      setError('Failed to create test');
    } finally {
      setLoading(false);
    }
  };

  const startTest = async (testId: string) => {
    try {
      const response = await fetch(`/api/ab-tests/${testId}/start`, {
        method: 'POST',
      });

      if (response.ok) {
        fetchTests();
      } else {
        setError('Failed to start test');
      }
    } catch (err) {
      setError('Failed to start test');
    }
  };

  const pauseTest = async (testId: string) => {
    try {
      const response = await fetch(`/api/ab-tests/${testId}/pause`, {
        method: 'POST',
      });

      if (response.ok) {
        fetchTests();
      } else {
        setError('Failed to pause test');
      }
    } catch (err) {
      setError('Failed to pause test');
    }
  };

  const endTest = async (testId: string) => {
    try {
      const response = await fetch(`/api/ab-tests/${testId}/end`, {
        method: 'POST',
      });

      if (response.ok) {
        fetchTests();
        if (selectedTest?.test_id === testId) {
          setSelectedTest(null);
          setTestResults(null);
        }
      } else {
        setError('Failed to end test');
      }
    } catch (err) {
      setError('Failed to end test');
    }
  };

  const handleTestSelect = (test: ABTest) => {
    setSelectedTest(test);
    if (test.status === 'completed') {
      fetchTestResults(test.test_id);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'draft': return 'bg-gray-100 text-gray-800';
      case 'active': return 'bg-green-100 text-green-800';
      case 'paused': return 'bg-yellow-100 text-yellow-800';
      case 'completed': return 'bg-blue-100 text-blue-800';
      case 'cancelled': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getTestTypeLabel = (type: string) => {
    const labels: { [key: string]: string } = {
      'content_format': 'Content Format',
      'timing_optimization': 'Timing Optimization',
      'personalization_depth': 'Personalization Depth',
      'call_to_action': 'Call to Action',
      'insight_type': 'Insight Type',
      'encouragement_style': 'Encouragement Style'
    };
    return labels[type] || type;
  };

  // Chart data for performance metrics
  const getPerformanceChartData = () => {
    if (!testResults) return null;

    const variants = testResults.metrics.map(m => m.variant_id);
    const engagementRates = testResults.metrics.map(m => m.engagement_rate);
    const conversionRates = testResults.metrics.map(m => m.conversion_rate);

    return {
      labels: variants,
      datasets: [
        {
          label: 'Engagement Rate',
          data: engagementRates,
          backgroundColor: 'rgba(59, 130, 246, 0.5)',
          borderColor: 'rgba(59, 130, 246, 1)',
          borderWidth: 1,
        },
        {
          label: 'Conversion Rate',
          data: conversionRates,
          backgroundColor: 'rgba(16, 185, 129, 0.5)',
          borderColor: 'rgba(16, 185, 129, 1)',
          borderWidth: 1,
        },
      ],
    };
  };

  const getStatisticalSignificanceChart = () => {
    if (!testResults) return null;

    const significant = testResults.is_statistically_significant ? 1 : 0;
    const notSignificant = 1 - significant;

    return {
      labels: ['Statistically Significant', 'Not Significant'],
      datasets: [
        {
          data: [significant, notSignificant],
          backgroundColor: [
            'rgba(16, 185, 129, 0.8)',
            'rgba(239, 68, 68, 0.8)',
          ],
          borderWidth: 0,
        },
      ],
    };
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">A/B Testing Manager</h1>
          <p className="mt-2 text-gray-600">
            Create, manage, and analyze A/B tests for content optimization
          </p>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-md p-4">
            <div className="flex">
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">Error</h3>
                <div className="mt-2 text-sm text-red-700">{error}</div>
              </div>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="mb-6 flex justify-between items-center">
          <div className="flex space-x-4">
            <button
              onClick={() => setShowCreateModal(true)}
              className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors"
            >
              Create New Test
            </button>
            <button
              onClick={fetchTests}
              className="bg-gray-600 text-white px-4 py-2 rounded-md hover:bg-gray-700 transition-colors"
            >
              Refresh
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Tests List */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow">
              <div className="px-6 py-4 border-b border-gray-200">
                <h2 className="text-lg font-semibold text-gray-900">Active Tests</h2>
              </div>
              <div className="divide-y divide-gray-200">
                {loading ? (
                  <div className="p-6 text-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                  </div>
                ) : tests.length === 0 ? (
                  <div className="p-6 text-center text-gray-500">
                    No tests found
                  </div>
                ) : (
                  tests.map((test) => (
                    <div
                      key={test.test_id}
                      className={`p-6 cursor-pointer hover:bg-gray-50 ${
                        selectedTest?.test_id === test.test_id ? 'bg-blue-50' : ''
                      }`}
                      onClick={() => handleTestSelect(test)}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <h3 className="text-sm font-medium text-gray-900">
                            {test.test_name}
                          </h3>
                          <p className="text-sm text-gray-500">
                            {getTestTypeLabel(test.test_type)}
                          </p>
                        </div>
                        <span
                          className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(
                            test.status
                          )}`}
                        >
                          {test.status}
                        </span>
                      </div>
                      <div className="mt-2 text-xs text-gray-500">
                        Created: {new Date(test.created_at).toLocaleDateString()}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>

          {/* Test Details */}
          <div className="lg:col-span-2">
            {selectedTest ? (
              <div className="space-y-6">
                {/* Test Overview */}
                <div className="bg-white rounded-lg shadow">
                  <div className="px-6 py-4 border-b border-gray-200">
                    <div className="flex items-center justify-between">
                      <h2 className="text-lg font-semibold text-gray-900">
                        {selectedTest.test_name}
                      </h2>
                      <div className="flex space-x-2">
                        {selectedTest.status === 'draft' && (
                          <button
                            onClick={() => startTest(selectedTest.test_id)}
                            className="bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700"
                          >
                            Start Test
                          </button>
                        )}
                        {selectedTest.status === 'active' && (
                          <button
                            onClick={() => pauseTest(selectedTest.test_id)}
                            className="bg-yellow-600 text-white px-3 py-1 rounded text-sm hover:bg-yellow-700"
                          >
                            Pause Test
                          </button>
                        )}
                        {selectedTest.status === 'paused' && (
                          <button
                            onClick={() => startTest(selectedTest.test_id)}
                            className="bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700"
                          >
                            Resume Test
                          </button>
                        )}
                        {['active', 'paused'].includes(selectedTest.status) && (
                          <button
                            onClick={() => endTest(selectedTest.test_id)}
                            className="bg-red-600 text-white px-3 py-1 rounded text-sm hover:bg-red-700"
                          >
                            End Test
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="px-6 py-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="text-sm font-medium text-gray-500">Type</label>
                        <p className="text-sm text-gray-900">
                          {getTestTypeLabel(selectedTest.test_type)}
                        </p>
                      </div>
                      <div>
                        <label className="text-sm font-medium text-gray-500">Status</label>
                        <p className="text-sm text-gray-900">{selectedTest.status}</p>
                      </div>
                      <div>
                        <label className="text-sm font-medium text-gray-500">Duration</label>
                        <p className="text-sm text-gray-900">{selectedTest.duration_days} days</p>
                      </div>
                      <div>
                        <label className="text-sm font-medium text-gray-500">Traffic Allocation</label>
                        <p className="text-sm text-gray-900">
                          {(selectedTest.traffic_allocation * 100).toFixed(1)}%
                        </p>
                      </div>
                    </div>
                    <div className="mt-4">
                      <label className="text-sm font-medium text-gray-500">Description</label>
                      <p className="text-sm text-gray-900 mt-1">{selectedTest.description}</p>
                    </div>
                  </div>
                </div>

                {/* Variants */}
                <div className="bg-white rounded-lg shadow">
                  <div className="px-6 py-4 border-b border-gray-200">
                    <h3 className="text-lg font-semibold text-gray-900">Test Variants</h3>
                  </div>
                  <div className="px-6 py-4">
                    <div className="space-y-4">
                      {selectedTest.variants.map((variant) => (
                        <div key={variant.variant_id} className="border rounded-lg p-4">
                          <div className="flex items-center justify-between">
                            <div>
                              <h4 className="text-sm font-medium text-gray-900">
                                {variant.variant_name}
                                {variant.is_control && (
                                  <span className="ml-2 text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                                    Control
                                  </span>
                                )}
                              </h4>
                              <p className="text-sm text-gray-500">
                                Weight: {(variant.weight * 100).toFixed(1)}%
                              </p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Test Results */}
                {selectedTest.status === 'completed' && testResults && (
                  <div className="bg-white rounded-lg shadow">
                    <div className="px-6 py-4 border-b border-gray-200">
                      <h3 className="text-lg font-semibold text-gray-900">Test Results</h3>
                    </div>
                    <div className="px-6 py-4">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {/* Performance Chart */}
                        <div>
                          <h4 className="text-sm font-medium text-gray-900 mb-4">
                            Performance Metrics
                          </h4>
                          {getPerformanceChartData() && (
                            <Bar
                              data={getPerformanceChartData()!}
                              options={{
                                responsive: true,
                                plugins: {
                                  legend: {
                                    position: 'top' as const,
                                  },
                                  title: {
                                    display: false,
                                  },
                                },
                              }}
                            />
                          )}
                        </div>

                        {/* Statistical Significance */}
                        <div>
                          <h4 className="text-sm font-medium text-gray-900 mb-4">
                            Statistical Significance
                          </h4>
                          {getStatisticalSignificanceChart() && (
                            <Doughnut
                              data={getStatisticalSignificanceChart()!}
                              options={{
                                responsive: true,
                                plugins: {
                                  legend: {
                                    position: 'bottom' as const,
                                  },
                                },
                              }}
                            />
                          )}
                        </div>
                      </div>

                      {/* Winner and Recommendations */}
                      <div className="mt-6">
                        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                          <h4 className="text-sm font-medium text-green-800 mb-2">
                            Test Winner
                          </h4>
                          <p className="text-sm text-green-700">
                            {testResults.winner_variant || 'No clear winner'}
                          </p>
                        </div>

                        {testResults.recommendations.length > 0 && (
                          <div className="mt-4">
                            <h4 className="text-sm font-medium text-gray-900 mb-2">
                              Recommendations
                            </h4>
                            <ul className="list-disc list-inside space-y-1">
                              {testResults.recommendations.map((rec, index) => (
                                <li key={index} className="text-sm text-gray-700">
                                  {rec}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="bg-white rounded-lg shadow p-8 text-center">
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  Select a Test
                </h3>
                <p className="text-gray-500">
                  Choose a test from the list to view details and results
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Create Test Modal */}
        {showCreateModal && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
            <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
              <div className="mt-3">
                <h3 className="text-lg font-medium text-gray-900 mb-4">
                  Create New A/B Test
                </h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      Test Name
                    </label>
                    <input
                      type="text"
                      value={newTest.test_name}
                      onChange={(e) =>
                        setNewTest({ ...newTest, test_name: e.target.value })
                      }
                      className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      Test Type
                    </label>
                    <select
                      value={newTest.test_type}
                      onChange={(e) =>
                        setNewTest({ ...newTest, test_type: e.target.value })
                      }
                      className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                    >
                      <option value="content_format">Content Format</option>
                      <option value="timing_optimization">Timing Optimization</option>
                      <option value="personalization_depth">Personalization Depth</option>
                      <option value="call_to_action">Call to Action</option>
                      <option value="insight_type">Insight Type</option>
                      <option value="encouragement_style">Encouragement Style</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      Description
                    </label>
                    <textarea
                      value={newTest.description}
                      onChange={(e) =>
                        setNewTest({ ...newTest, description: e.target.value })
                      }
                      rows={3}
                      className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">
                        Duration (days)
                      </label>
                      <input
                        type="number"
                        value={newTest.duration_days}
                        onChange={(e) =>
                          setNewTest({ ...newTest, duration_days: parseInt(e.target.value) })
                        }
                        className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">
                        Traffic Allocation
                      </label>
                      <input
                        type="number"
                        min="0"
                        max="1"
                        step="0.1"
                        value={newTest.traffic_allocation}
                        onChange={(e) =>
                          setNewTest({ ...newTest, traffic_allocation: parseFloat(e.target.value) })
                        }
                        className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>
                  </div>
                </div>
                <div className="flex justify-end space-x-3 mt-6">
                  <button
                    onClick={() => setShowCreateModal(false)}
                    className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={createTest}
                    disabled={loading}
                    className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50"
                  >
                    {loading ? 'Creating...' : 'Create Test'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ABTestingManager;
