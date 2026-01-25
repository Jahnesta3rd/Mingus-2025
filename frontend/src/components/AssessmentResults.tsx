import React from 'react';
import { useNavigate } from 'react-router-dom';
import { AlertTriangle, Target, Download, Mail, Calendar, Shield, X } from 'lucide-react';

// Types
export interface AssessmentResult {
  assessment_id?: number;
  score: number;
  risk_level: string;
  recommendations: string[];
  assessment_type: string;
  completed_at: string;
  percentile?: number;
  benchmark?: {
    average: number;
    high: number;
    low: number;
  };
}

interface AssessmentResultsProps {
  result: AssessmentResult;
  onClose: () => void;
  onRetake: () => void;
  onShare: () => void;
  className?: string;
}

// Chart components
const ScoreChart: React.FC<{ score: number; maxScore?: number }> = ({ score, maxScore = 100 }) => {
  const roundedScore = Math.round(score);
  const percentage = (roundedScore / maxScore) * 100;
  const radius = 45;
  const circumference = 2 * Math.PI * radius;
  const strokeDasharray = circumference;
  const strokeDashoffset = circumference - (percentage / 100) * circumference;

  return (
    <div className="relative w-32 h-32 max-w-full mx-auto" style={{ maxWidth: '150px', height: 'auto' }}>
      <svg className="w-full h-full max-w-full transform -rotate-90" viewBox="0 0 100 100" style={{ maxWidth: '100%', height: 'auto' }}>
        {/* Background circle */}
        <circle
          cx="50"
          cy="50"
          r={radius}
          stroke="currentColor"
          strokeWidth="6"
          fill="none"
          className="text-gray-700"
        />
        {/* Progress circle */}
        <circle
          cx="50"
          cy="50"
          r={radius}
          stroke="currentColor"
          strokeWidth="6"
          fill="none"
          strokeDasharray={strokeDasharray}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          className="text-violet-500 transition-all duration-1000 ease-out"
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="text-center">
          <div className="text-3xl font-bold text-white">{roundedScore}</div>
          <div className="text-xs text-gray-400">out of {maxScore}</div>
        </div>
      </div>
    </div>
  );
};

const BenchmarkChart: React.FC<{ 
  userScore: number; 
  benchmark: { average: number; high: number; low: number };
  title: string;
}> = ({ userScore, benchmark, title }) => {
  const maxValue = Math.max(userScore, benchmark.high);
  const userPercentage = (userScore / maxValue) * 100;
  const avgPercentage = (benchmark.average / maxValue) * 100;
  const highPercentage = (benchmark.high / maxValue) * 100;
  // const lowPercentage = (benchmark.low / maxValue) * 100;

  return (
    <div className="bg-gray-800 rounded-lg p-4">
      <h4 className="text-sm font-medium text-white mb-3">{title}</h4>
      <div className="space-y-3">
        {/* User Score */}
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-300">Your Score</span>
          <div className="flex items-center space-x-2">
            <div className="w-24 bg-gray-700 rounded-full h-2">
              <div 
                className="bg-gradient-to-r from-violet-500 to-purple-500 h-2 rounded-full transition-all duration-1000"
                style={{ width: `${userPercentage}%` }}
              />
            </div>
            <span className="text-sm font-medium text-white w-8">{userScore}</span>
          </div>
        </div>

        {/* Benchmark Average */}
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-400">Industry Average</span>
          <div className="flex items-center space-x-2">
            <div className="w-24 bg-gray-700 rounded-full h-2">
              <div 
                className="bg-gray-500 h-2 rounded-full transition-all duration-1000"
                style={{ width: `${avgPercentage}%` }}
              />
            </div>
            <span className="text-sm text-gray-400 w-8">{benchmark.average}</span>
          </div>
        </div>

        {/* High Benchmark */}
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-400">Top Performers</span>
          <div className="flex items-center space-x-2">
            <div className="w-24 bg-gray-700 rounded-full h-2">
              <div 
                className="bg-green-500 h-2 rounded-full transition-all duration-1000"
                style={{ width: `${highPercentage}%` }}
              />
            </div>
            <span className="text-sm text-gray-400 w-8">{benchmark.high}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

const RiskLevelIndicator: React.FC<{ riskLevel: string; score: number }> = ({ riskLevel, score }) => {
  const getRiskConfig = (level: string) => {
    switch (level.toLowerCase()) {
      case 'low':
        return { 
          color: 'text-green-400', 
          bgColor: 'bg-green-900/20', 
          borderColor: 'border-green-500',
          icon: Shield,
          label: 'Low Risk'
        };
      case 'medium':
        return { 
          color: 'text-yellow-400', 
          bgColor: 'bg-yellow-900/20', 
          borderColor: 'border-yellow-500',
          icon: AlertTriangle,
          label: 'Medium Risk'
        };
      case 'high':
        return { 
          color: 'text-red-400', 
          bgColor: 'bg-red-900/20', 
          borderColor: 'border-red-500',
          icon: AlertTriangle,
          label: 'High Risk'
        };
      default:
        return { 
          color: 'text-gray-400', 
          bgColor: 'bg-gray-900/20', 
          borderColor: 'border-gray-500',
          icon: Target,
          label: 'Unknown'
        };
    }
  };

  const config = getRiskConfig(riskLevel);
  const Icon = config.icon;

  return (
    <div className={`${config.bgColor} ${config.borderColor} border rounded-lg p-4`}>
      <div className="flex items-center space-x-3">
        <Icon className={`w-6 h-6 ${config.color}`} />
        <div>
          <div className={`text-sm font-medium ${config.color}`}>
            {config.label}
          </div>
          <div className="text-xs text-gray-400">
            Score: {Math.round(score)}/100
          </div>
        </div>
      </div>
    </div>
  );
};


// Main AssessmentResults Component
const AssessmentResults: React.FC<AssessmentResultsProps> = ({
  result,
  onClose,
  onRetake,
  onShare,
  className = ''
}) => {
  const navigate = useNavigate();
  
  // Handle PDF download
  const handleDownloadPDF = async () => {
    if (!result.assessment_id) {
      console.error('Assessment ID not available for download');
      // Fallback: try to generate a client-side PDF or show error
      alert('Assessment ID not available. Please complete the assessment again to download PDF.');
      return;
    }
    
    try {
      const response = await fetch(`/api/assessments/${result.assessment_id}/download`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        if (response.status === 503) {
          const errorData = await response.json();
          alert(errorData.error || 'PDF generation is not available. Please contact support.');
        } else if (response.status === 404) {
          alert('Assessment not found. Please complete the assessment again.');
        } else {
          alert('Failed to download PDF. Please try again later.');
        }
        return;
      }
      
      // Get the PDF blob
      const blob = await response.blob();
      
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `assessment-results-${result.assessment_type}-${result.assessment_id || Date.now()}.pdf`;
      document.body.appendChild(a);
      a.click();
      
      // Cleanup
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Error downloading PDF:', error);
      alert('Failed to download PDF. Please check your connection and try again.');
    }
  };
  
  const getAssessmentTitle = (type: string) => {
    switch (type) {
      case 'ai-risk':
        return 'AI Replacement Risk Assessment';
      case 'income-comparison':
        return 'Income Comparison Assessment';
      case 'cuffing-season':
        return 'Cuffing Season Score';
      case 'layoff-risk':
        return 'Layoff Risk Assessment';
      default:
        return 'Assessment Results';
    }
  };

  const getScoreInterpretation = (type: string, score: number) => {
    const roundedScore = Math.round(score);
    
    if (type === 'ai-risk') {
      if (roundedScore < 30) return { color: 'text-green-400', text: 'Low AI replacement risk. Your role has strong human-centric elements.' };
      if (roundedScore < 60) return { color: 'text-yellow-400', text: 'Moderate AI risk. Consider building skills in areas AI struggles with.' };
      return { color: 'text-red-400', text: 'Higher AI risk. Focus on creativity, leadership, and interpersonal skills.' };
    }
    if (type === 'income-comparison') {
      if (roundedScore >= 70) return { color: 'text-green-400', text: 'Above market rate! You\'re earning well for your role and location.' };
      if (roundedScore >= 40) return { color: 'text-yellow-400', text: 'Near market rate. There may be room for salary negotiation.' };
      return { color: 'text-red-400', text: 'Below market rate. Consider negotiating or exploring new opportunities.' };
    }
    if (type === 'layoff-risk') {
      if (roundedScore < 30) return { color: 'text-green-400', text: 'Low layoff risk. Your position appears stable.' };
      if (roundedScore < 60) return { color: 'text-yellow-400', text: 'Moderate risk. Stay visible and document your contributions.' };
      return { color: 'text-red-400', text: 'Elevated risk. Consider networking and updating your resume.' };
    }
    if (type === 'cuffing-season') {
      if (roundedScore >= 70) return { color: 'text-green-400', text: 'High relationship readiness! You\'re in a great position.' };
      if (roundedScore >= 40) return { color: 'text-yellow-400', text: 'Moderate readiness. Focus on the areas identified below.' };
      return { color: 'text-orange-400', text: 'Some preparation needed. Work on yourself first.' };
    }
    if (type === 'vehicle-financial-health') {
      if (roundedScore >= 80) return { color: 'text-green-400', text: 'Excellent vehicle financial health! You\'re well-prepared.' };
      if (roundedScore >= 60) return { color: 'text-blue-400', text: 'Good standing. Some areas could use attention.' };
      if (roundedScore >= 40) return { color: 'text-yellow-400', text: 'Moderate risk. Sign up to see personalized financial insights.' };
      if (roundedScore >= 20) return { color: 'text-orange-400', text: 'Elevated risk. Action recommended to improve your position.' };
      return { color: 'text-red-400', text: 'High risk. Immediate attention needed in key areas.' };
    }
    // Generic fallback
    if (roundedScore >= 80) return { color: 'text-green-400', text: 'Excellent! You\'re well-positioned with low risk.' };
    if (roundedScore >= 60) return { color: 'text-blue-400', text: 'Good standing. Some areas could use attention.' };
    if (roundedScore >= 40) return { color: 'text-yellow-400', text: 'Moderate risk. Consider the recommendations below.' };
    if (roundedScore >= 20) return { color: 'text-orange-400', text: 'Elevated risk. Action recommended to improve your position.' };
    return { color: 'text-red-400', text: 'High risk. Immediate attention needed in key areas.' };
  };

  return (
    <div className={`bg-gray-900 rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden overflow-x-hidden ${className}`}>
      {/* Header */}
      <div className="bg-gradient-to-r from-violet-600 to-purple-600 p-6 text-white">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-2xl font-bold">{getAssessmentTitle(result.assessment_type)}</h2>
            <p className="text-violet-100 text-sm">Results • Completed {new Date(result.completed_at).toLocaleDateString()}</p>
          </div>
          <button
            onClick={onClose}
            className="text-violet-200 hover:text-white transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-violet-400 focus:ring-offset-2 focus:ring-offset-violet-600 rounded p-1"
            aria-label="Close results"
          >
            <X className="w-6 h-6" />
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="p-4 sm:p-6 overflow-y-auto overflow-x-hidden max-h-[calc(90vh-200px)]">
        <div className="max-w-2xl mx-auto space-y-6">
          {/* Left Column - Score and Charts */}
          <div className="space-y-6">
            {/* Score Display */}
            <div className="bg-gray-800 rounded-lg p-4 sm:p-6 text-center overflow-hidden">
              <h3 className="text-lg font-semibold text-white mb-4">Your Score</h3>
              <div className="max-w-[200px] mx-auto p-2">
                <ScoreChart score={result.score} />
              </div>
              {/* Score interpretation */}
              <div className="mt-4 text-center px-4">
                {(() => {
                  const interpretation = getScoreInterpretation(result.assessment_type, result.score);
                  return (
                    <p className={`${interpretation.color} font-medium`}>
                      {interpretation.text}
                    </p>
                  );
                })()}
              </div>
              <div className="mt-4">
                <RiskLevelIndicator riskLevel={result.risk_level} score={Math.round(result.score)} />
              </div>
            </div>

            {/* Benchmark Comparison */}
            {result.benchmark && (
              <BenchmarkChart
                userScore={Math.round(result.score)}
                benchmark={result.benchmark}
                title="Industry Comparison"
              />
            )}

            {/* Percentile Display */}
            {result.percentile && (
              <div className="bg-gray-800 rounded-lg p-4">
                <h4 className="text-sm font-medium text-white mb-3">Percentile Ranking</h4>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-300">You scored higher than</span>
                  <span className="text-2xl font-bold text-violet-400">{Math.round(result.percentile)}%</span>
                  <span className="text-sm text-gray-300">of people</span>
                </div>
              </div>
            )}
          </div>

          {/* Signup CTA */}
          <div className="mt-8 p-6 bg-gradient-to-r from-violet-900/50 to-purple-900/50 rounded-xl border border-violet-500/30">
            <h3 className="text-xl font-bold text-white text-center mb-3">
              See How This Affects Your Finances
            </h3>
            
            <p className="text-gray-300 text-center mb-6">
              Your {result.assessment_type === 'ai-risk' ? 'AI risk score' : 
                    result.assessment_type === 'income-comparison' ? 'income positioning' :
                    result.assessment_type === 'layoff-risk' ? 'job security score' :
                    'readiness score'} directly impacts your financial forecast. 
              Sign up to see personalized projections and actionable insights.
            </p>

            <ul className="text-gray-300 text-sm space-y-2 mb-6 max-w-sm mx-auto">
              <li className="flex items-center gap-2">
                <svg className="w-5 h-5 text-green-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                <span>See your score's impact on cash flow</span>
              </li>
              <li className="flex items-center gap-2">
                <svg className="w-5 h-5 text-green-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                <span>Get personalized financial projections</span>
              </li>
              <li className="flex items-center gap-2">
                <svg className="w-5 h-5 text-green-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                <span>Track improvements over time</span>
              </li>
            </ul>

            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <button
                onClick={() => {
                  // Store assessment results for pre-fill
                  localStorage.setItem('assessmentResults', JSON.stringify({
                    type: result.assessment_type,
                    score: Math.round(result.score),
                    completedAt: new Date().toISOString()
                  }));
                  onClose();
                  setTimeout(() => {
                    navigate(`/signup?from=assessment&type=${result.assessment_type}`);
                  }, 100);
                }}
                className="px-8 py-3 bg-violet-600 hover:bg-violet-500 text-white font-semibold rounded-lg transition-colors text-center"
              >
                Sign Up Free
              </button>
              
              <button
                onClick={onClose}
                className="px-8 py-3 bg-transparent hover:bg-gray-700 text-gray-300 font-medium rounded-lg border border-gray-600 transition-colors text-center"
              >
                Maybe Later
              </button>
            </div>

            <p className="text-gray-500 text-xs text-center mt-4">
              Free 14-day trial • No credit card required
            </p>
          </div>
        </div>

        {/* Email Confirmation */}
        <div className="mt-6 bg-green-900/20 border border-green-500/30 rounded-lg p-4">
          <div className="flex items-center space-x-3">
            <Mail className="w-5 h-5 text-green-400" />
            <div>
              <div className="text-sm font-medium text-green-400">
                📧 Results Email Sent!
              </div>
              <div className="text-xs text-green-300">
                Check your email for detailed results
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Actions */}
        <div className="mt-8 pt-6 border-t border-gray-700">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button 
                onClick={handleDownloadPDF}
                className="flex items-center space-x-2 text-gray-400 hover:text-white transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                disabled={!result.assessment_id}
                title={result.assessment_id ? 'Download assessment results as PDF' : 'Assessment ID not available'}
              >
                <Download className="w-4 h-4" />
                <span className="text-sm">Download PDF</span>
              </button>
              <button className="flex items-center space-x-2 text-gray-400 hover:text-white transition-colors duration-200">
                <Mail className="w-4 h-4" />
                <span className="text-sm">Resend Email</span>
              </button>
              <button className="flex items-center space-x-2 text-gray-400 hover:text-white transition-colors duration-200">
                <Calendar className="w-4 h-4" />
                <span className="text-sm">Schedule Follow-up</span>
              </button>
            </div>
            <div className="text-xs text-gray-500">
              Results generated on {new Date().toLocaleString()}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AssessmentResults;
