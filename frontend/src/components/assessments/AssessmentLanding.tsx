import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import LoadingSpinner from '../shared/LoadingSpinner';

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

const AssessmentLanding: React.FC = () => {
  const [assessments, setAssessments] = useState<Assessment[]>([]);
  const [stats, setStats] = useState<AssessmentStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

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

  useEffect(() => {
    fetchAssessments();
    fetchStats();
  }, [fetchAssessments, fetchStats]);

  const handleAssessmentClick = (assessment: Assessment) => {
    navigate(`/assessments/${assessment.type}`);
  };

  const getAssessmentIcon = (type: string) => {
    const icons: Record<string, string> = {
      ai_job_risk: '🤖',
      relationship_impact: '💕',
      tax_impact: '💰',
      income_comparison: '📊',
    };
    return icons[type] || '📋';
  };

  const getAssessmentColor = (type: string) => {
    const colors: Record<string, string> = {
      ai_job_risk: 'from-purple-500 to-purple-600',
      relationship_impact: 'from-pink-500 to-pink-600',
      tax_impact: 'from-green-500 to-green-600',
      income_comparison: 'from-blue-500 to-blue-600',
    };
    return colors[type] || 'from-gray-500 to-gray-600';
  };

  const getTrendingBadge = (assessment: Assessment) => {
    if (assessment.stats.completion_rate > 85) {
      return { text: '🔥 Trending', color: 'bg-orange-500' };
    }
    if (assessment.stats.average_score > 75) {
      return { text: '⭐ Popular', color: 'bg-yellow-500' };
    }
    if (assessment.stats.total_attempts > 100) {
      return { text: '📈 Growing', color: 'bg-green-500' };
    }
    return null;
  };

  const getValueProposition = (type: string) => {
    const propositions: Record<string, string> = {
      ai_job_risk: 'Discover your job\'s AI vulnerability and learn augmentation strategies',
      relationship_impact: 'Understand how finances affect relationships and reduce stress',
      tax_impact: 'Optimize your tax strategy and identify potential savings',
      income_comparison: 'Compare your earnings and discover growth opportunities',
    };
    return propositions[type] || 'Get personalized insights and actionable recommendations';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <LoadingSpinner size="xl" className="mx-auto mb-4" />
          <p className="text-gray-600">Loading assessments...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md mx-auto p-6">
          <div className="text-6xl mb-4">⚠️</div>
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Unable to Load Assessments</h1>
          <p className="text-gray-600 mb-6">{error}</p>
          <button
            onClick={fetchAssessments}
            className="bg-purple-600 text-white px-6 py-3 rounded-lg hover:bg-purple-700 transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header Section */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center">
            <h1 className="text-4xl font-bold text-gray-900 mb-4">
              Financial Wellness Assessments
            </h1>
            <p className="text-xl text-gray-600 mb-6 max-w-3xl mx-auto">
              Take personalized assessments to understand your financial health, 
              identify risks, and discover opportunities for growth.
            </p>
            
            {/* Social Proof Stats */}
            {stats && (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                <div className="text-center">
                  <div className="text-2xl font-bold text-purple-600">
                    {stats.total_users_helped.toLocaleString()}+
                  </div>
                  <div className="text-sm text-gray-600">Users Helped</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">
                    {stats.this_week.completion_rate}%
                  </div>
                  <div className="text-sm text-gray-600">Completion Rate</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">
                    {stats.this_week.completed_assessments}
                  </div>
                  <div className="text-sm text-gray-600">This Week</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-orange-600">
                    {stats.this_week.average_score}
                  </div>
                  <div className="text-sm text-gray-600">Avg Score</div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Assessments Grid */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {assessments.map((assessment) => {
            const trendingBadge = getTrendingBadge(assessment);
            
            return (
              <div
                key={assessment.id}
                className="bg-white rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 cursor-pointer group"
                onClick={() => handleAssessmentClick(assessment)}
              >
                {/* Assessment Header */}
                <div className={`bg-gradient-to-r ${getAssessmentColor(assessment.type)} p-6 rounded-t-xl relative`}>
                  <div className="text-4xl mb-2">{getAssessmentIcon(assessment.type)}</div>
                  <h3 className="text-xl font-bold text-white mb-2">{assessment.title}</h3>
                  <p className="text-white/90 text-sm">{assessment.description}</p>
                  
                  {/* Trending Badge */}
                  {trendingBadge && (
                    <div className={`absolute top-4 right-4 ${trendingBadge.color} text-white text-xs font-semibold px-2 py-1 rounded-full`}>
                      {trendingBadge.text}
                    </div>
                  )}
                </div>

                {/* Assessment Content */}
                <div className="p-6">
                  {/* Value Proposition */}
                  <p className="text-gray-700 text-sm mb-4">
                    {getValueProposition(assessment.type)}
                  </p>

                  {/* Stats */}
                  <div className="space-y-3 mb-6">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Completion Rate</span>
                      <span className="font-semibold text-green-600">
                        {assessment.stats.completion_rate}%
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Avg Score</span>
                      <span className="font-semibold text-blue-600">
                        {assessment.stats.average_score}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Est. Time</span>
                      <span className="font-semibold text-purple-600">
                        {assessment.estimated_duration_minutes} min
                      </span>
                    </div>
                  </div>

                  {/* Progress Bar */}
                  <div className="mb-4">
                    <div className="flex justify-between text-xs text-gray-600 mb-1">
                      <span>Progress</span>
                      <span>{assessment.stats.completed_attempts} completed</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-gradient-to-r from-green-400 to-green-600 h-2 rounded-full transition-all duration-300"
                        style={{
                          width: `${Math.min((assessment.stats.completed_attempts / Math.max(assessment.stats.total_attempts, 1)) * 100, 100)}%`
                        }}
                      />
                    </div>
                  </div>

                  {/* CTA Button */}
                  <button className="w-full bg-purple-600 text-white py-3 px-4 rounded-lg font-semibold hover:bg-purple-700 transition-colors group-hover:scale-105 transform duration-200">
                    {assessment.user_completed ? 'Retake Assessment' : 'Start Assessment'}
                  </button>

                  {/* User Status */}
                  {assessment.user_completed && (
                    <div className="mt-3 text-center">
                      <span className="text-xs text-green-600 bg-green-100 px-2 py-1 rounded-full">
                        ✓ Completed
                      </span>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Empty State */}
        {assessments.length === 0 && (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">📋</div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">No Assessments Available</h3>
            <p className="text-gray-600">Check back later for new assessments.</p>
          </div>
        )}
      </div>

      {/* Footer CTA */}
      <div className="bg-gradient-to-r from-purple-600 to-purple-800 text-white py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold mb-4">
            Ready to Transform Your Financial Future?
          </h2>
          <p className="text-xl mb-8 text-purple-100">
            Join thousands of users who have gained clarity and confidence through our assessments.
          </p>
          <button className="bg-white text-purple-600 px-8 py-4 rounded-lg font-semibold text-lg hover:bg-gray-100 transition-colors">
            Get Started Today
          </button>
        </div>
      </div>
    </div>
  );
};

export default AssessmentLanding;
