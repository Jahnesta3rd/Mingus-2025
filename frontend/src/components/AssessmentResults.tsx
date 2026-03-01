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

/** Band-specific result copy: headline + recommendation paragraph (by assessment type and risk_level). */
const ASSESSMENT_BAND_COPY: Record<string, Record<string, { headline: string; copy: string }>> = {
  'ai-risk': {
    'High Risk': {
      headline: 'Your role has significant automation exposure.',
      copy: 'Several factors suggest your current position is vulnerable to AI displacement from the nature of your daily tasks to your current adaptation pace. The good news: awareness is the first step. Mingus can help you identify the specific skills and moves most likely to protect your income.'
    },
    'Elevated Risk': {
      headline: 'Real vulnerabilities worth addressing now.',
      copy: "Your role has meaningful automation risk, but it's not inevitable. Targeted action – learning the right skills, increasing your visibility, and diversifying your income – can significantly improve your position."
    },
    'Moderate Risk': {
      headline: 'You have a moat, but it needs reinforcing.',
      copy: 'Your role has strong AI-resistant elements, but gaps remain. Staying ahead requires consistent adaptation. Mingus can help you identify the highest-leverage moves to protect and grow your income.'
    },
    'Low Risk': {
      headline: "You're well-positioned in the age of AI.",
      copy: "Your role's human-judgment content, your proactive adaptation, and your visibility to leadership all signal strong AI resilience. Use this position to your advantage – now is the time to negotiate and grow."
    }
  },
  'income-comparison': {
    'Significant Gap': {
      headline: "You're likely leaving real money on the table.",
      copy: "The data is clear: people who benchmark and negotiate earn significantly more over their careers. You haven't done either recently – and that gap compounds. Mingus will show you exactly what people in your role and location are earning, and how to start closing the gap."
    },
    'Awareness Gap': {
      headline: "You know there's a gap – now it's time to act.",
      copy: "You have some sense of the market, but you haven't made the moves that change the number. Mingus will help you build a specific, timed plan to increase your income."
    },
    'Active but Incomplete': {
      headline: 'Good instincts. A few optimizations could make a real difference.',
      copy: 'You benchmark and negotiate – that puts you ahead of most. But there are a few specific opportunities you may be missing. Mingus will show you where to focus.'
    },
    'Income Optimized': {
      headline: 'You manage your income like an asset.',
      copy: 'You benchmark, negotiate, and understand your full compensation. Mingus will help you put that income to work – building wealth, not just earning it.'
    }
  },
  'cuffing-season': {
    'Not Ready': {
      headline: 'Significant barriers are standing between you and the relationship you want.',
      copy: 'Emotional and financial blocks are real – and they affect how you show up in relationships. Mingus can help you address the financial piece directly, which often unlocks more than people expect.'
    },
    'Warming Up': {
      headline: "You're closer than you think – a few things are in the way.",
      copy: 'The barriers are real but addressable. For many people, financial stress is the silent relationship killer. Getting that stable changes everything. Mingus can help.'
    },
    'Mostly Ready': {
      headline: "You're in a good position – a few refinements could make a difference.",
      copy: "You're emotionally available and mostly aligned in what you want. Removing the last friction points – often financial anxiety – can meaningfully improve how you show up."
    },
    'Fully Ready': {
      headline: "You're ready – and you know what you want.",
      copy: "High readiness across the board. Financial confidence, emotional availability, and clarity on what you're looking for. Mingus can help you maintain the foundation that makes relationships thrive."
    }
  },
  'layoff-risk': {
    'High Risk': {
      headline: 'Multiple layoff risk factors are active right now.',
      copy: 'Multiple factors suggest your job security could be at risk. Mingus can help you build a plan to reduce exposure and protect your income.'
    },
    'Elevated Risk': {
      headline: 'Some layoff risk factors need your attention.',
      copy: 'You have meaningful exposure, but targeted steps – visibility, skills, and a financial buffer – can significantly improve your position. Mingus can help you prioritize.'
    },
    'Moderate Risk': {
      headline: 'You have a solid base, but stay proactive.',
      copy: 'Your position and relationships provide some protection. Staying visible and continuing to build skills will help you maintain that edge. Mingus can help you track and strengthen your position.'
    },
    'Low Risk': {
      headline: 'Your job security looks strong.',
      copy: 'Your visibility, institutional knowledge, and relationships signal lower layoff risk. Use this stability to build your financial foundation and career options. Mingus can help you make the most of it.'
    }
  },
  'vehicle-financial-health': {
    'High Risk': {
      headline: 'Your vehicle finances need attention.',
      copy: 'Unexpected costs and lack of planning can put real pressure on your budget. Mingus can help you build a vehicle emergency fund and plan for total cost of ownership.'
    },
    'Elevated Risk': {
      headline: 'A few changes could reduce vehicle-related stress.',
      copy: 'You have some awareness of costs, but gaps remain. Mingus can help you track expenses and plan for repairs so you stay in control.'
    },
    'Moderate Risk': {
      headline: 'You\'re in decent shape – small steps can help.',
      copy: 'You manage most vehicle costs consciously. Mingus can help you optimize insurance, savings, and your next purchase decision.'
    },
    'Low Risk': {
      headline: 'You\'re on top of your vehicle finances.',
      copy: 'You plan for total cost, track expenses, and have a buffer. Mingus can help you keep that foundation strong and put savings to work elsewhere.'
    }
  }
};

function getBandCopy(assessmentType: string, riskLevel: string): { headline: string; copy: string } | null {
  const byType = ASSESSMENT_BAND_COPY[assessmentType];
  if (!byType) return null;
  return byType[riskLevel] ?? null;
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
    const lower = level.toLowerCase();
    // Legacy single-word levels
    if (lower === 'low') {
      return { color: 'text-green-400', bgColor: 'bg-green-900/20', borderColor: 'border-green-500', icon: Shield, label: 'Low Risk' };
    }
    if (lower === 'medium') {
      return { color: 'text-yellow-400', bgColor: 'bg-yellow-900/20', borderColor: 'border-yellow-500', icon: AlertTriangle, label: 'Medium Risk' };
    }
    if (lower === 'high') {
      return { color: 'text-red-400', bgColor: 'bg-red-900/20', borderColor: 'border-red-500', icon: AlertTriangle, label: 'High Risk' };
    }
    // Point-weighted band labels: derive color from band name, use band as label
    const positive = /low risk|income optimized|fully ready/i;
    const caution = /elevated risk|moderate risk|awareness gap|active but incomplete|warming up|mostly ready/i;
    if (positive.test(level)) {
      return { color: 'text-green-400', bgColor: 'bg-green-900/20', borderColor: 'border-green-500', icon: Shield, label: level };
    }
    if (caution.test(level)) {
      return { color: 'text-yellow-400', bgColor: 'bg-yellow-900/20', borderColor: 'border-yellow-500', icon: AlertTriangle, label: level };
    }
    return { color: 'text-red-400', bgColor: 'bg-red-900/20', borderColor: 'border-red-500', icon: AlertTriangle, label: level };
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
      case 'vehicle-financial-health':
        return 'Vehicle Financial Health Assessment';
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
              {/* Band-specific headline and copy, or fallback interpretation */}
              <div className="mt-4 text-center px-4 space-y-2">
                {(() => {
                  const bandCopy = getBandCopy(result.assessment_type, result.risk_level);
                  const interpretation = getScoreInterpretation(result.assessment_type, result.score);
                  if (bandCopy) {
                    return (
                      <>
                        <p className="text-white font-semibold">{bandCopy.headline}</p>
                        <p className="text-gray-300 text-sm leading-relaxed">{bandCopy.copy}</p>
                      </>
                    );
                  }
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
