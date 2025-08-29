import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import LoadingSpinner from '../shared/LoadingSpinner';
import ConversionModal from './ConversionModal';

// Types
interface AssessmentResult {
  id: string;
  assessment_type: string;
  score: number;
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  segment: string;
  product_tier: string;
  insights: string[];
  recommendations: string[];
  cost_projection: {
    amount: number;
    timeframe: string;
    currency: string;
  };
  social_comparison: {
    percentile: number;
    total_users: number;
    message: string;
  };
  processing_time_ms: number;
  conversion_offer: {
    lead_id: string;
    lead_score: number;
    offer_type: string;
    discount_percentage: number;
    trial_days: number;
    message: string;
  };
  upgrade_message: string;
  created_at: string;
}

interface AssessmentResultsProps {
  assessmentId?: string;
}

const AssessmentResults: React.FC<AssessmentResultsProps> = ({ assessmentId: propAssessmentId }) => {
  const { assessmentType, assessmentId: urlAssessmentId } = useParams<{ 
    assessmentType: string; 
    assessmentId: string; 
  }>();
  const navigate = useNavigate();
  const [result, setResult] = useState<AssessmentResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showConversionModal, setShowConversionModal] = useState(false);
  const [downloadingPDF, setDownloadingPDF] = useState(false);

  const finalAssessmentId = propAssessmentId || urlAssessmentId;

  // Fetch assessment results
  const fetchResults = useCallback(async () => {
    if (!finalAssessmentId) return;

    try {
      setLoading(true);
      const response = await fetch(`/api/assessments/${finalAssessmentId}/results`, {
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load results');
    } finally {
      setLoading(false);
    }
  }, [finalAssessmentId]);

  useEffect(() => {
    fetchResults();
  }, [fetchResults]);

  // Get risk level styling
  const getRiskLevelStyle = (riskLevel: string) => {
    const styles = {
      low: {
        color: 'text-green-600',
        bg: 'bg-green-100',
        border: 'border-green-200',
        icon: '🟢',
      },
      medium: {
        color: 'text-yellow-600',
        bg: 'bg-yellow-100',
        border: 'border-yellow-200',
        icon: '🟡',
      },
      high: {
        color: 'text-orange-600',
        bg: 'bg-orange-100',
        border: 'border-orange-200',
        icon: '🟠',
      },
      critical: {
        color: 'text-red-600',
        bg: 'bg-red-100',
        border: 'border-red-200',
        icon: '🔴',
      },
    };
    return styles[riskLevel as keyof typeof styles] || styles.medium;
  };

  // Get score color based on value
  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    if (score >= 40) return 'text-orange-600';
    return 'text-red-600';
  };

  // Download PDF
  const handleDownloadPDF = async () => {
    if (!result) return;

    try {
      setDownloadingPDF(true);
      const response = await fetch(`/api/assessments/${result.id}/pdf`, {
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error('Failed to generate PDF');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `assessment-results-${result.assessment_type}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error('Failed to download PDF:', err);
    } finally {
      setDownloadingPDF(false);
    }
  };

  // Share results
  const handleShare = async () => {
    if (!result) return;

    const shareData = {
      title: 'My Financial Assessment Results',
      text: `I scored ${result.score}% on my ${result.assessment_type.replace('_', ' ')} assessment. Check out your results!`,
      url: window.location.href,
    };

    if (navigator.share) {
      try {
        await navigator.share(shareData);
      } catch (err) {
        console.log('Share cancelled');
      }
    } else {
      // Fallback: copy to clipboard
      const text = `${shareData.title}\n${shareData.text}\n${shareData.url}`;
      await navigator.clipboard.writeText(text);
      alert('Results copied to clipboard!');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <LoadingSpinner size="xl" className="mx-auto mb-4" />
          <p className="text-gray-600">Loading your results...</p>
        </div>
      </div>
    );
  }

  if (error || !result) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md mx-auto p-6">
          <div className="text-6xl mb-4">⚠️</div>
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Unable to Load Results</h1>
          <p className="text-gray-600 mb-6">{error || 'Results not found'}</p>
          <button
            onClick={() => navigate('/assessments')}
            className="bg-purple-600 text-white px-6 py-3 rounded-lg hover:bg-purple-700 transition-colors"
          >
            Back to Assessments
          </button>
        </div>
      </div>
    );
  }

  const riskStyle = getRiskLevelStyle(result.risk_level);
  const scoreColor = getScoreColor(result.score);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center">
            <h1 className="text-4xl font-bold text-gray-900 mb-4">
              Your Assessment Results
            </h1>
            <p className="text-xl text-gray-600">
              Here's what we discovered about your financial wellness
            </p>
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Results */}
          <div className="lg:col-span-2 space-y-6">
            {/* Score and Risk Level */}
            <div className="bg-white rounded-xl shadow-lg p-8">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-bold text-gray-900">Your Score</h2>
                <div className={`px-4 py-2 rounded-full border ${riskStyle.bg} ${riskStyle.border}`}>
                  <span className={`font-semibold ${riskStyle.color}`}>
                    {riskStyle.icon} {result.risk_level.toUpperCase()} RISK
                  </span>
                </div>
              </div>

              {/* Score Visualization */}
              <div className="text-center mb-6">
                <div className={`text-6xl font-bold ${scoreColor} mb-2`}>
                  {result.score}%
                </div>
                <div className="w-full bg-gray-200 rounded-full h-4 mb-4">
                  <div
                    className={`h-4 rounded-full transition-all duration-1000 ${
                      result.score >= 80 ? 'bg-green-500' :
                      result.score >= 60 ? 'bg-yellow-500' :
                      result.score >= 40 ? 'bg-orange-500' : 'bg-red-500'
                    }`}
                    style={{ width: `${result.score}%` }}
                  />
                </div>
                <p className="text-gray-600">
                  {result.segment} • {result.product_tier}
                </p>
              </div>

              {/* Social Comparison */}
              <div className="bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  How You Compare
                </h3>
                <p className="text-gray-700">
                  {result.social_comparison.message}
                </p>
                <div className="mt-3 text-sm text-gray-600">
                  Based on {result.social_comparison.total_users.toLocaleString()} users
                </div>
              </div>
            </div>

            {/* Insights */}
            <div className="bg-white rounded-xl shadow-lg p-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Key Insights</h2>
              <div className="space-y-4">
                {result.insights.map((insight, index) => (
                  <div key={index} className="flex items-start space-x-3">
                    <div className="w-2 h-2 bg-purple-500 rounded-full mt-2 flex-shrink-0"></div>
                    <p className="text-gray-700">{insight}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Recommendations */}
            <div className="bg-white rounded-xl shadow-lg p-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Personalized Recommendations</h2>
              <div className="space-y-4">
                {result.recommendations.map((recommendation, index) => (
                  <div key={index} className="border-l-4 border-green-500 pl-4">
                    <p className="text-gray-700">{recommendation}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Cost Projection */}
            <div className="bg-white rounded-xl shadow-lg p-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Financial Impact</h2>
              <div className="bg-gradient-to-r from-green-50 to-blue-50 rounded-lg p-6">
                <div className="text-center">
                  <div className="text-3xl font-bold text-green-600 mb-2">
                    {result.cost_projection.currency}${result.cost_projection.amount.toLocaleString()}
                  </div>
                  <p className="text-gray-700">
                    Potential impact over {result.cost_projection.timeframe}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Conversion Offer */}
            <div className="bg-gradient-to-r from-purple-600 to-purple-800 text-white rounded-xl p-6">
              <h3 className="text-xl font-bold mb-4">Get Full Access</h3>
              <p className="mb-4 text-purple-100">
                {result.upgrade_message}
              </p>
              <button
                onClick={() => setShowConversionModal(true)}
                className="w-full bg-white text-purple-600 py-3 px-4 rounded-lg font-semibold hover:bg-gray-100 transition-colors"
              >
                Unlock Premium Features
              </button>
            </div>

            {/* Actions */}
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Actions</h3>
              <div className="space-y-3">
                <button
                  onClick={handleDownloadPDF}
                  disabled={downloadingPDF}
                  className="w-full flex items-center justify-center px-4 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
                >
                  {downloadingPDF ? (
                    <>
                      <LoadingSpinner size="sm" className="mr-2" />
                      Generating PDF...
                    </>
                  ) : (
                    <>
                      📄 Download PDF
                    </>
                  )}
                </button>
                <button
                  onClick={handleShare}
                  className="w-full flex items-center justify-center px-4 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  📤 Share Results
                </button>
                <button
                  onClick={() => navigate('/assessments')}
                  className="w-full flex items-center justify-center px-4 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  📋 Take Another Assessment
                </button>
              </div>
            </div>

            {/* Assessment Info */}
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Assessment Details</h3>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Type:</span>
                  <span className="font-medium">{result.assessment_type.replace('_', ' ')}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Completed:</span>
                  <span className="font-medium">
                    {new Date(result.created_at).toLocaleDateString()}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Processing Time:</span>
                  <span className="font-medium">{result.processing_time_ms}ms</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Conversion Modal */}
      {showConversionModal && (
        <ConversionModal
          assessmentResult={result}
          onClose={() => setShowConversionModal(false)}
        />
      )}
    </div>
  );
};

export default AssessmentResults;
