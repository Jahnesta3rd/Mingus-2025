import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import LoadingSpinner from '../shared/LoadingSpinner';
import { usePageViewTracking, useAssessmentTracking, useSocialProofTracking } from '../analytics/AssessmentAnalytics';
import { LiveCompletionCounter, LiveConversionRate, LiveActiveUsers } from '../analytics/RealTimeMetrics';

// Types
interface Assessment {
  id: string;
  type: string;
  title: string;
  description: string;
  estimated_duration_minutes: number;
  version: string;
  requires_authentication: boolean;
  allow_anonymous: boolean;
  max_attempts_per_user: number;
  stats: {
    total_attempts: number;
    completed_attempts: number;
    completion_rate: number;
    average_score: number;
    average_time_minutes: number;
  };
  user_completed: boolean;
  attempts_remaining: number;
}

interface AssessmentStats {
  today: {
    total_assessments: number;
    completed_assessments: number;
    completion_rate: number;
    average_score: number;
  };
  this_week: {
    total_assessments: number;
    completed_assessments: number;
    completion_rate: number;
    average_score: number;
  };
  by_assessment_type: Record<string, {
    total_attempts: number;
    average_score: number;
  }>;
  risk_distribution: {
    low: number;
    medium: number;
    high: number;
    critical: number;
  };
  total_users_helped: number;
}

const AssessmentLandingEnhanced: React.FC = () => {
  const [assessments, setAssessments] = useState<Assessment[]>([]);
  const [stats, setStats] = useState<AssessmentStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedAssessment, setSelectedAssessment] = useState<Assessment | null>(null);
  const [showSocialProof, setShowSocialProof] = useState(true);
  const navigate = useNavigate();

  // Analytics tracking
  usePageViewTracking();
  const { trackInteraction } = useSocialProofTracking();

  // Fetch available assessments
  const fetchAssessments = useCallback(async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/assessments/available', {
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      setAssessments(data.assessments || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load assessments');
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch assessment statistics
  const fetchStats = useCallback(async () => {
    try {
      const response = await fetch('/api/assessments/stats', {
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (err) {
      console.error('Failed to load assessment stats:', err);
    }
  }, []);

  // Load data on component mount
  useEffect(() => {
    fetchAssessments();
    fetchStats();
  }, [fetchAssessments, fetchStats]);

  // Handle assessment selection
  const handleAssessmentSelect = useCallback((assessment: Assessment) => {
    setSelectedAssessment(assessment);
    trackInteraction('assessment_selected');
  }, [trackInteraction]);

  // Handle assessment start
  const handleStartAssessment = useCallback((assessment: Assessment) => {
    trackInteraction('assessment_start_clicked');
    navigate(`/assessment/${assessment.type}`);
  }, [navigate, trackInteraction]);

  // Handle social proof interaction
  const handleSocialProofClick = useCallback((interactionType: string) => {
    trackInteraction(interactionType);
  }, [trackInteraction]);

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

  // Get assessment type display name
  const getAssessmentTypeDisplay = (type: string): string => {
    const displayNames: Record<string, string> = {
      'ai_job_risk': 'AI Job Risk Assessment',
      'relationship_impact': 'Relationship Impact Assessment',
      'tax_impact': 'Tax Impact Assessment',
      'income_comparison': 'Income Comparison Assessment'
    };
    return displayNames[type] || type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-600 text-xl mb-4">Error Loading Assessments</div>
          <div className="text-gray-600 mb-4">{error}</div>
          <button
            onClick={fetchAssessments}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                Financial Risk Assessments
              </h1>
              <p className="text-gray-600 mt-2">
                Evaluate your financial situation and identify potential risks
              </p>
            </div>
            
            {/* Social Proof Header */}
            {showSocialProof && (
              <div className="flex items-center space-x-6">
                <div className="text-center">
                  <LiveCompletionCounter className="text-blue-600" />
                </div>
                <div className="text-center">
                  <LiveConversionRate className="text-green-600" />
                </div>
                <div className="text-center">
                  <LiveActiveUsers className="text-purple-600" />
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2">
            {/* Assessment Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
              {assessments.map((assessment) => (
                <div
                  key={assessment.id}
                  className={`bg-white rounded-lg shadow-sm border-2 transition-all duration-200 cursor-pointer hover:shadow-md ${
                    selectedAssessment?.id === assessment.id
                      ? 'border-blue-500 shadow-md'
                      : 'border-gray-200 hover:border-blue-300'
                  }`}
                  onClick={() => handleAssessmentSelect(assessment)}
                >
                  <div className="p-6">
                    <div className="flex items-start justify-between mb-4">
                      <h3 className="text-xl font-semibold text-gray-900">
                        {getAssessmentTypeDisplay(assessment.type)}
                      </h3>
                      {assessment.user_completed && (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                          Completed
                        </span>
                      )}
                    </div>
                    
                    <p className="text-gray-600 mb-4 line-clamp-3">
                      {assessment.description}
                    </p>
                    
                    <div className="flex items-center justify-between text-sm text-gray-500 mb-4">
                      <span>⏱ {assessment.estimated_duration_minutes} min</span>
                      <span>📊 {assessment.stats.completion_rate}% completion rate</span>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <div className="text-sm text-gray-500">
                        {assessment.attempts_remaining > 0 ? (
                          <span>{assessment.attempts_remaining} attempts remaining</span>
                        ) : (
                          <span className="text-red-600">No attempts remaining</span>
                        )}
                      </div>
                      
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleStartAssessment(assessment);
                        }}
                        disabled={assessment.attempts_remaining === 0}
                        className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                          assessment.attempts_remaining > 0
                            ? 'bg-blue-600 text-white hover:bg-blue-700'
                            : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                        }`}
                      >
                        {assessment.user_completed ? 'Retake' : 'Start Assessment'}
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Selected Assessment Details */}
            {selectedAssessment && (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h3 className="text-xl font-semibold text-gray-900 mb-4">
                  {getAssessmentTypeDisplay(selectedAssessment.type)} - Details
                </h3>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h4 className="font-medium text-gray-900 mb-2">Assessment Statistics</h4>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Total Attempts:</span>
                        <span className="font-medium">{selectedAssessment.stats.total_attempts.toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Completed:</span>
                        <span className="font-medium">{selectedAssessment.stats.completed_attempts.toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Average Score:</span>
                        <span className="font-medium">{selectedAssessment.stats.average_score}%</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Average Time:</span>
                        <span className="font-medium">{selectedAssessment.stats.average_time_minutes} min</span>
                      </div>
                    </div>
                  </div>
                  
                  <div>
                    <h4 className="font-medium text-gray-900 mb-2">What You'll Learn</h4>
                    <ul className="space-y-2 text-sm text-gray-600">
                      <li className="flex items-start">
                        <span className="text-green-500 mr-2">✓</span>
                        Risk level assessment and analysis
                      </li>
                      <li className="flex items-start">
                        <span className="text-green-500 mr-2">✓</span>
                        Personalized recommendations
                      </li>
                      <li className="flex items-start">
                        <span className="text-green-500 mr-2">✓</span>
                        Actionable next steps
                      </li>
                      <li className="flex items-start">
                        <span className="text-green-500 mr-2">✓</span>
                        Detailed report and insights
                      </li>
                    </ul>
                  </div>
                </div>
                
                <div className="mt-6 pt-6 border-t border-gray-200">
                  <button
                    onClick={() => handleStartAssessment(selectedAssessment)}
                    disabled={selectedAssessment.attempts_remaining === 0}
                    className={`w-full px-6 py-3 rounded-lg font-medium text-lg transition-colors ${
                      selectedAssessment.attempts_remaining > 0
                        ? 'bg-blue-600 text-white hover:bg-blue-700'
                        : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                    }`}
                  >
                    {selectedAssessment.user_completed ? 'Retake Assessment' : 'Start Assessment Now'}
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Social Proof Section */}
            {showSocialProof && (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Live Activity
                </h3>
                
                <div className="space-y-4">
                  <div className="text-center p-4 bg-blue-50 rounded-lg">
                    <div className="text-2xl font-bold text-blue-600 mb-1">
                      <LiveCompletionCounter />
                    </div>
                    <p className="text-sm text-blue-600">assessments completed today</p>
                  </div>
                  
                  <div className="text-center p-4 bg-green-50 rounded-lg">
                    <div className="text-2xl font-bold text-green-600 mb-1">
                      <LiveConversionRate />
                    </div>
                    <p className="text-sm text-green-600">conversion rate</p>
                  </div>
                  
                  <div className="text-center p-4 bg-purple-50 rounded-lg">
                    <div className="text-2xl font-bold text-purple-600 mb-1">
                      <LiveActiveUsers />
                    </div>
                    <p className="text-sm text-purple-600">users active now</p>
                  </div>
                </div>
                
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <button
                    onClick={() => handleSocialProofClick('social_proof_viewed')}
                    className="text-sm text-blue-600 hover:text-blue-800"
                  >
                    View detailed analytics →
                  </button>
                </div>
              </div>
            )}

            {/* Overall Statistics */}
            {stats && (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Overall Statistics
                </h3>
                
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Today's Completions</span>
                      <span className="font-medium">{stats.today.completed_assessments}</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
                      <div
                        className="bg-blue-600 h-2 rounded-full"
                        style={{ width: `${stats.today.completion_rate}%` }}
                      ></div>
                    </div>
                  </div>
                  
                  <div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">This Week</span>
                      <span className="font-medium">{stats.this_week.completed_assessments}</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
                      <div
                        className="bg-green-600 h-2 rounded-full"
                        style={{ width: `${stats.this_week.completion_rate}%` }}
                      ></div>
                    </div>
                  </div>
                  
                  <div className="pt-4 border-t border-gray-200">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-gray-900">
                        {stats.total_users_helped.toLocaleString()}
                      </div>
                      <div className="text-sm text-gray-600">Users Helped</div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Risk Distribution */}
            {stats && (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Risk Distribution
                </h3>
                
                <div className="space-y-3">
                  {Object.entries(stats.risk_distribution).map(([level, count]) => (
                    <div key={level} className="flex items-center justify-between">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${getRiskLevelColor(level)}`}>
                        {level.charAt(0).toUpperCase() + level.slice(1)}
                      </span>
                      <span className="text-sm font-medium text-gray-900">{count}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Quick Actions */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Quick Actions
              </h3>
              
              <div className="space-y-3">
                <button
                  onClick={() => handleSocialProofClick('view_all_assessments')}
                  className="w-full text-left p-3 rounded-lg border border-gray-200 hover:border-blue-300 hover:bg-blue-50 transition-colors"
                >
                  <div className="font-medium text-gray-900">View All Assessments</div>
                  <div className="text-sm text-gray-600">Explore our full assessment library</div>
                </button>
                
                <button
                  onClick={() => handleSocialProofClick('view_results')}
                  className="w-full text-left p-3 rounded-lg border border-gray-200 hover:border-blue-300 hover:bg-blue-50 transition-colors"
                >
                  <div className="font-medium text-gray-900">View Your Results</div>
                  <div className="text-sm text-gray-600">Check your previous assessment results</div>
                </button>
                
                <button
                  onClick={() => handleSocialProofClick('get_help')}
                  className="w-full text-left p-3 rounded-lg border border-gray-200 hover:border-blue-300 hover:bg-blue-50 transition-colors"
                >
                  <div className="font-medium text-gray-900">Get Help</div>
                  <div className="text-sm text-gray-600">Contact our support team</div>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AssessmentLandingEnhanced;
