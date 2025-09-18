import React from 'react';
import { TrendingUp, AlertTriangle, Target, ArrowRight, Download, Share2, Mail, Calendar, BookOpen, Users, DollarSign, Shield, Zap, X } from 'lucide-react';

// Types
export interface AssessmentResult {
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
  const percentage = (score / maxScore) * 100;
  const radius = 60;
  const circumference = 2 * Math.PI * radius;
  const strokeDasharray = circumference;
  const strokeDashoffset = circumference - (percentage / 100) * circumference;

  return (
    <div className="relative w-32 h-32 mx-auto">
      <svg className="w-32 h-32 transform -rotate-90" viewBox="0 0 120 120">
        {/* Background circle */}
        <circle
          cx="60"
          cy="60"
          r={radius}
          stroke="currentColor"
          strokeWidth="8"
          fill="none"
          className="text-gray-700"
        />
        {/* Progress circle */}
        <circle
          cx="60"
          cy="60"
          r={radius}
          stroke="currentColor"
          strokeWidth="8"
          fill="none"
          strokeDasharray={strokeDasharray}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          className="text-violet-500 transition-all duration-1000 ease-out"
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="text-center">
          <div className="text-2xl font-bold text-white">{score}</div>
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
            Score: {score}/100
          </div>
        </div>
      </div>
    </div>
  );
};

const RecommendationCard: React.FC<{ 
  recommendation: string; 
  index: number;
  category: 'action' | 'learning' | 'networking' | 'financial';
}> = ({ recommendation, index, category }) => {
  const getCategoryConfig = (cat: string) => {
    switch (cat) {
      case 'action':
        return { icon: Zap, color: 'text-blue-400', bgColor: 'bg-blue-900/20' };
      case 'learning':
        return { icon: BookOpen, color: 'text-purple-400', bgColor: 'bg-purple-900/20' };
      case 'networking':
        return { icon: Users, color: 'text-green-400', bgColor: 'bg-green-900/20' };
      case 'financial':
        return { icon: DollarSign, color: 'text-yellow-400', bgColor: 'bg-yellow-900/20' };
      default:
        return { icon: Target, color: 'text-gray-400', bgColor: 'bg-gray-900/20' };
    }
  };

  const config = getCategoryConfig(category);
  const Icon = config.icon;

  return (
    <div className={`${config.bgColor} rounded-lg p-4 border border-gray-700`}>
      <div className="flex items-start space-x-3">
        <div className={`${config.color} mt-1`}>
          <Icon className="w-5 h-5" />
        </div>
        <div className="flex-1">
          <div className="text-sm text-white font-medium mb-1">
            Step {index + 1}
          </div>
          <div className="text-sm text-gray-300">
            {recommendation}
          </div>
        </div>
      </div>
    </div>
  );
};

const CTASection: React.FC<{ 
  onRetake: () => void; 
  onShare: () => void;
  assessmentType: string;
}> = ({ onRetake, onShare, assessmentType }) => {
  const getCTAs = (type: string) => {
    switch (type) {
      case 'ai-risk':
        return {
          primary: {
            title: 'Get AI-Ready Skills Training',
            description: 'Learn the skills that will keep you ahead of AI',
            action: 'Start Learning',
            icon: BookOpen
          },
          secondary: {
            title: 'Join AI Professionals Network',
            description: 'Connect with others navigating AI in their careers',
            action: 'Join Network',
            icon: Users
          }
        };
      case 'income-comparison':
        return {
          primary: {
            title: 'Negotiate Your Salary',
            description: 'Get expert guidance on salary negotiation',
            action: 'Get Negotiation Guide',
            icon: DollarSign
          },
          secondary: {
            title: 'Career Advancement Plan',
            description: 'Create a roadmap to increase your earning potential',
            action: 'Create Plan',
            icon: TrendingUp
          }
        };
      case 'cuffing-season':
        return {
          primary: {
            title: 'Dating Success Workshop',
            description: 'Learn proven strategies for meaningful connections',
            action: 'Join Workshop',
            icon: Users
          },
          secondary: {
            title: 'Confidence Building Course',
            description: 'Build the confidence to attract the right partner',
            action: 'Start Course',
            icon: Target
          }
        };
      case 'layoff-risk':
        return {
          primary: {
            title: 'Job Security Action Plan',
            description: 'Protect your career with strategic moves',
            action: 'Get Action Plan',
            icon: Shield
          },
          secondary: {
            title: 'Skills Development Program',
            description: 'Build in-demand skills to future-proof your career',
            action: 'Start Program',
            icon: BookOpen
          }
        };
      default:
        return {
          primary: {
            title: 'Get Personalized Guidance',
            description: 'Receive expert advice tailored to your results',
            action: 'Get Guidance',
            icon: Target
          },
          secondary: {
            title: 'Join Our Community',
            description: 'Connect with others on similar journeys',
            action: 'Join Community',
            icon: Users
          }
        };
    }
  };

  const ctas = getCTAs(assessmentType);
  const PrimaryIcon = ctas.primary.icon;
  const SecondaryIcon = ctas.secondary.icon;

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-white mb-4">Your Next Steps</h3>
      
      {/* Primary CTA */}
      <div className="bg-gradient-to-r from-violet-600 to-purple-600 rounded-lg p-6">
        <div className="flex items-start space-x-4">
          <div className="text-white">
            <PrimaryIcon className="w-6 h-6" />
          </div>
          <div className="flex-1">
            <h4 className="text-lg font-semibold text-white mb-2">
              {ctas.primary.title}
            </h4>
            <p className="text-violet-100 text-sm mb-4">
              {ctas.primary.description}
            </p>
            <button className="bg-white text-violet-600 px-6 py-2 rounded-lg font-semibold hover:bg-violet-50 transition-colors duration-200 flex items-center space-x-2">
              <span>{ctas.primary.action}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Secondary CTA */}
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <div className="flex items-start space-x-4">
          <div className="text-gray-400">
            <SecondaryIcon className="w-6 h-6" />
          </div>
          <div className="flex-1">
            <h4 className="text-lg font-semibold text-white mb-2">
              {ctas.secondary.title}
            </h4>
            <p className="text-gray-300 text-sm mb-4">
              {ctas.secondary.description}
            </p>
            <button className="bg-gray-700 text-white px-6 py-2 rounded-lg font-semibold hover:bg-gray-600 transition-colors duration-200 flex items-center space-x-2">
              <span>{ctas.secondary.action}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex space-x-3 pt-4">
        <button
          onClick={onRetake}
          className="flex-1 bg-gray-700 text-white px-4 py-2 rounded-lg font-medium hover:bg-gray-600 transition-colors duration-200 flex items-center justify-center space-x-2"
        >
          <Target className="w-4 h-4" />
          <span>Retake Assessment</span>
        </button>
        <button
          onClick={onShare}
          className="flex-1 bg-gray-700 text-white px-4 py-2 rounded-lg font-medium hover:bg-gray-600 transition-colors duration-200 flex items-center justify-center space-x-2"
        >
          <Share2 className="w-4 h-4" />
          <span>Share Results</span>
        </button>
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

  const getScoreInterpretation = (score: number, type: string) => {
    switch (type) {
      case 'ai-risk':
        if (score >= 70) return 'High Risk - Your job may be at risk from AI automation';
        if (score >= 40) return 'Medium Risk - Some aspects of your role could be automated';
        return 'Low Risk - Your job is relatively safe from AI automation';
      case 'income-comparison':
        if (score >= 70) return 'Above Market Rate - You\'re earning more than most in your field';
        if (score >= 40) return 'Market Rate - Your salary aligns with industry standards';
        return 'Below Market Rate - You may be underpaid for your role';
      case 'cuffing-season':
        if (score >= 70) return 'Highly Ready - You\'re well-prepared for meaningful connections';
        if (score >= 40) return 'Somewhat Ready - You have potential for dating success';
        return 'Not Ready - Focus on personal growth before dating';
      case 'layoff-risk':
        if (score >= 70) return 'High Risk - Your job security may be at risk';
        if (score >= 40) return 'Medium Risk - Monitor your situation closely';
        return 'Low Risk - Your job appears secure';
      default:
        return 'Assessment completed successfully';
    }
  };

  return (
    <div className={`bg-gray-900 rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden ${className}`}>
      {/* Header */}
      <div className="bg-gradient-to-r from-violet-600 to-purple-600 p-6 text-white">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-2xl font-bold">{getAssessmentTitle(result.assessment_type)}</h2>
            <p className="text-violet-100 text-sm">Results • Completed {new Date(result.completed_at).toLocaleDateString()}</p>
          </div>
          <button
            onClick={onClose}
            className="text-violet-200 hover:text-white transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:ring-offset-2 focus:ring-offset-violet-600 rounded p-1"
            aria-label="Close results"
          >
            <X className="w-6 h-6" />
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="p-6 overflow-y-auto max-h-[calc(90vh-200px)]">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left Column - Score and Charts */}
          <div className="space-y-6">
            {/* Score Display */}
            <div className="bg-gray-800 rounded-lg p-6 text-center">
              <h3 className="text-lg font-semibold text-white mb-4">Your Score</h3>
              <ScoreChart score={result.score} />
              <div className="mt-4">
                <div className="text-sm text-gray-300 mb-2">
                  {getScoreInterpretation(result.score, result.assessment_type)}
                </div>
                <RiskLevelIndicator riskLevel={result.risk_level} score={result.score} />
              </div>
            </div>

            {/* Benchmark Comparison */}
            {result.benchmark && (
              <BenchmarkChart
                userScore={result.score}
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
                  <span className="text-2xl font-bold text-violet-400">{result.percentile}%</span>
                  <span className="text-sm text-gray-300">of people</span>
                </div>
              </div>
            )}
          </div>

          {/* Right Column - Recommendations and CTAs */}
          <div className="space-y-6">
            {/* Recommendations */}
            <div>
              <h3 className="text-lg font-semibold text-white mb-4">Personalized Recommendations</h3>
              <div className="space-y-3">
                {result.recommendations.map((recommendation, index) => (
                  <RecommendationCard
                    key={index}
                    recommendation={recommendation}
                    index={index}
                    category={index % 2 === 0 ? 'action' : 'learning'}
                  />
                ))}
              </div>
            </div>

            {/* CTAs */}
            <CTASection
              onRetake={onRetake}
              onShare={onShare}
              assessmentType={result.assessment_type}
            />
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
                Check your email for detailed results and personalized recommendations
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Actions */}
        <div className="mt-8 pt-6 border-t border-gray-700">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button className="flex items-center space-x-2 text-gray-400 hover:text-white transition-colors duration-200">
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
