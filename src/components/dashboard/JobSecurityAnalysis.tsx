import React, { useState, useEffect } from 'react';
import { 
  TrendingUp, 
  TrendingDown, 
  Shield, 
  AlertTriangle, 
  CheckCircle, 
  ChevronRight,
  Info,
  Clock,
  MapPin,
  Building,
  Users,
  DollarSign
} from 'lucide-react';

interface JobSecurityData {
  overall_score: number;
  user_perception_score: number;
  external_data_score: number;
  confidence_level: number;
  risk_factors: RiskFactor[];
  positive_indicators: string[];
  recommendations: Recommendation[];
  trend_data: TrendPoint[];
  last_updated: string;
  employer_name?: string;
  industry_sector?: string;
  location?: string;
}

interface RiskFactor {
  category: string;
  severity: 'low' | 'medium' | 'high';
  description: string;
  impact_score: number;
}

interface Recommendation {
  priority: 'high' | 'medium' | 'low';
  category: string;
  title: string;
  description: string;
  action_items: string[];
}

interface TrendPoint {
  date: string;
  score: number;
  change?: number;
}

interface JobSecurityAnalysisProps {
  data: JobSecurityData;
  onDrillDown?: (component: string) => void;
  className?: string;
}

const JobSecurityAnalysis: React.FC<JobSecurityAnalysisProps> = ({
  data,
  onDrillDown,
  className = ''
}) => {
  const [selectedComponent, setSelectedComponent] = useState<string | null>(null);
  const [showTrends, setShowTrends] = useState(false);

  const getScoreColor = (score: number) => {
    if (score >= 70) return 'text-[#00e676]';
    if (score >= 40) return 'text-[#ff2d2d]';
    return 'text-[#ff2d2d]';
  };

  const getScoreBgColor = (score: number) => {
    if (score >= 70) return 'bg-[#00e676]/10';
    if (score >= 40) return 'bg-[#ff2d2d]/10';
    return 'bg-[#ff2d2d]/10';
  };

  const getRiskLevel = (score: number) => {
    if (score >= 70) return { level: 'Low Risk', color: 'bg-[#00e676]', text: 'text-[#181a1b]' };
    if (score >= 40) return { level: 'Medium Risk', color: 'bg-[#ff2d2d]', text: 'text-white' };
    return { level: 'High Risk', color: 'bg-[#ff2d2d]', text: 'text-white' };
  };

  const getTrendIcon = (change?: number) => {
    if (!change) return null;
    if (change > 0) return <TrendingUp className="w-4 h-4 text-[#00e676]" />;
    if (change < 0) return <TrendingDown className="w-4 h-4 text-[#ff2d2d]" />;
    return null;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric'
    });
  };

  const riskLevel = getRiskLevel(data.overall_score);

  return (
    <div className={`bg-[#23272a] rounded-xl shadow-lg border-2 border-[#ff2d2d] p-6 text-white ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-[#00e676]/20 rounded-lg">
            <Shield className="w-6 h-6 text-[#00e676]" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white" className="text-xl font-semibold text-gray-800 mb-3">Job Security Analysis</h3>
            <p className="text-gray-400">
              Last updated {formatDate(data.last_updated)}
            </p>
          </div>
        </div>
        <div className={`px-3 py-1 rounded-full text-base leading-relaxed font-medium ${riskLevel.color} ${riskLevel.text}`}>
          {riskLevel.level}
        </div>
      </div>

      {/* Main Score Display */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        {/* Circular Progress Indicator */}
        <div className="flex flex-col items-center">
          <div className="relative w-32 h-32">
            <svg className="w-32 h-32 transform -rotate-90" viewBox="0 0 120 120">
              <circle
                cx="60"
                cy="60"
                r="54"
                stroke="currentColor"
                strokeWidth="8"
                fill="transparent"
                className="text-gray-600"
              />
              <circle
                cx="60"
                cy="60"
                r="54"
                stroke="currentColor"
                strokeWidth="8"
                fill="transparent"
                strokeDasharray={`${2 * Math.PI * 54}`}
                strokeDashoffset={`${2 * Math.PI * 54 * (1 - data.overall_score / 100)}`}
                className={`${getScoreColor(data.overall_score)} transition-all duration-1000`}
                strokeLinecap="round"
              />
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center">
                <div className={`text-3xl font-bold ${getScoreColor(data.overall_score)}`}>
                  {data.overall_score}
                </div>
                <div className="text-base leading-relaxed text-gray-400">Score</div>
              </div>
            </div>
          </div>
          <div className="mt-4 text-center">
            <div className="text-base leading-relaxed text-gray-400">Confidence Level</div>
            <div className="text-lg font-semibold text-white">{data.confidence_level}%</div>
          </div>
        </div>

        {/* Component Breakdown */}
        <div className="lg:col-span-2">
          <h4 className="text-md font-semibold text-white mb-4">Score Components</h4>
          <div className="space-y-4">
            {/* User Perception */}
            <div className="bg-[#181a1b] rounded-lg p-4 cursor-pointer hover:bg-[#2a2d2e] transition-colors border border-gray-700"
                 onClick={() => onDrillDown?.('user_perception')}>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-2">
                  <Users className="w-4 h-4 text-[#00e676]" />
                  <span className="text-base leading-relaxed font-medium text-gray-300">User Perception</span>
                </div>
                <ChevronRight className="w-4 h-4 text-gray-500" />
              </div>
              <div className="flex items-center space-x-3">
                <div className="flex-1 bg-gray-700 rounded-full h-2">
                  <div 
                    className={`h-2 rounded-full ${getScoreColor(data.user_perception_score)}`}
                    style={{ width: `${data.user_perception_score}%` }}
                  />
                </div>
                <span className={`text-base leading-relaxed font-semibold ${getScoreColor(data.user_perception_score)}`}>
                  {data.user_perception_score}
                </span>
              </div>
            </div>

            {/* External Data */}
            <div className="bg-[#181a1b] rounded-lg p-4 cursor-pointer hover:bg-[#2a2d2e] transition-colors border border-gray-700"
                 onClick={() => onDrillDown?.('external_data')}>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-2">
                  <Building className="w-4 h-4 text-[#00e676]" />
                  <span className="text-base leading-relaxed font-medium text-gray-300">External Data</span>
                </div>
                <ChevronRight className="w-4 h-4 text-gray-500" />
              </div>
              <div className="flex items-center space-x-3">
                <div className="flex-1 bg-gray-700 rounded-full h-2">
                  <div 
                    className={`h-2 rounded-full ${getScoreColor(data.external_data_score)}`}
                    style={{ width: `${data.external_data_score}%` }}
                  />
                </div>
                <span className={`text-base leading-relaxed font-semibold ${getScoreColor(data.external_data_score)}`}>
                  {data.external_data_score}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Context Information */}
      {(data.employer_name || data.industry_sector || data.location) && (
        <div className="bg-[#00e676]/10 rounded-lg p-4 mb-6 border border-[#00e676]/20">
          <h4 className="text-base leading-relaxed font-semibold text-[#00e676] mb-3">Analysis Context</h4>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-base leading-relaxed">
            {data.employer_name && (
              <div className="flex items-center space-x-2">
                <Building className="w-4 h-4 text-[#00e676]" />
                <span className="text-gray-300">{data.employer_name}</span>
              </div>
            )}
            {data.industry_sector && (
              <div className="flex items-center space-x-2">
                <DollarSign className="w-4 h-4 text-[#00e676]" />
                <span className="text-gray-300">{data.industry_sector}</span>
              </div>
            )}
            {data.location && (
              <div className="flex items-center space-x-2">
                <MapPin className="w-4 h-4 text-[#00e676]" />
                <span className="text-gray-300">{data.location}</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Risk Factors and Positive Indicators */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Risk Factors */}
        <div>
          <h4 className="text-md font-semibold text-white mb-4 flex items-center">
            <AlertTriangle className="w-5 h-5 text-[#ff2d2d] mr-2" />
            Risk Factors
          </h4>
          <div className="space-y-3">
            {data.risk_factors.map((factor, index) => (
              <div key={index} className="bg-[#ff2d2d]/10 rounded-lg p-3 border border-[#ff2d2d]/20">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-base leading-relaxed font-medium text-[#ff2d2d]">{factor.category}</span>
                  <span className={`px-2 py-1 rounded text-base leading-relaxed font-medium ${
                    factor.severity === 'high' ? 'bg-[#ff2d2d] text-white' :
                    factor.severity === 'medium' ? 'bg-[#ff2d2d]/50 text-white' :
                    'bg-[#00e676]/50 text-[#181a1b]'
                  }`}>
                    {factor.severity.toUpperCase()}
                  </span>
                </div>
                <p className="text-base leading-relaxed text-gray-300">{factor.description}</p>
                <div className="mt-2 flex items-center space-x-2">
                  <div className="flex-1 bg-[#ff2d2d]/20 rounded-full h-1">
                    <div 
                      className="bg-[#ff2d2d] h-1 rounded-full"
                      style={{ width: `${factor.impact_score}%` }}
                    />
                  </div>
                  <span className="text-base leading-relaxed text-[#ff2d2d]">{factor.impact_score}% impact</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Positive Indicators */}
        <div>
          <h4 className="text-md font-semibold text-white mb-4 flex items-center">
            <CheckCircle className="w-5 h-5 text-[#00e676] mr-2" />
            Positive Indicators
          </h4>
          <div className="space-y-3">
            {data.positive_indicators.map((indicator, index) => (
              <div key={index} className="bg-[#00e676]/10 rounded-lg p-3 border border-[#00e676]/20">
                <div className="flex items-center space-x-2">
                  <CheckCircle className="w-4 h-4 text-[#00e676] flex-shrink-0" />
                  <span className="text-base leading-relaxed text-gray-300">{indicator}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recommendations */}
      <div className="mb-6">
        <h4 className="text-md font-semibold text-white mb-4">Personalized Recommendations</h4>
        <div className="space-y-4">
          {data.recommendations.map((rec, index) => (
            <div key={index} className="bg-[#181a1b] rounded-lg p-4 border-l-4 border-[#00e676]">
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center space-x-2">
                  <span className={`px-2 py-1 rounded text-base leading-relaxed font-medium ${
                    rec.priority === 'high' ? 'bg-[#ff2d2d] text-white' :
                    rec.priority === 'medium' ? 'bg-[#ff2d2d]/50 text-white' :
                    'bg-[#00e676] text-[#181a1b]'
                  }`}>
                    {rec.priority.toUpperCase()} PRIORITY
                  </span>
                  <span className="text-base leading-relaxed text-gray-500">{rec.category}</span>
                </div>
              </div>
              <h5 className="font-medium text-white mb-2">{rec.title}</h5>
              <p className="text-base leading-relaxed text-gray-400 mb-3">{rec.description}</p>
              <div className="space-y-1">
                {rec.action_items.map((item, itemIndex) => (
                  <div key={itemIndex} className="flex items-center space-x-2 text-base leading-relaxed text-gray-300">
                    <div className="w-1.5 h-1.5 bg-[#00e676] rounded-full"></div>
                    <span>{item}</span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Trend Analysis */}
      <div className="border-t border-gray-700 pt-6">
        <div className="flex items-center justify-between mb-4">
          <h4 className="text-md font-semibold text-white">12-Week Trend</h4>
          <button
            onClick={() => setShowTrends(!showTrends)}
            className="text-base leading-relaxed text-[#00e676] hover:text-[#00c060] flex items-center space-x-1"
          >
            <span>{showTrends ? 'Hide' : 'Show'} Details</span>
            <ChevronRight className={`w-4 h-4 transition-transform ${showTrends ? 'rotate-90' : ''}`} />
          </button>
        </div>
        
        {showTrends && (
          <div className="bg-[#181a1b] rounded-lg p-4 border border-gray-700">
            <div className="flex items-center justify-between mb-4">
              <div className="space-y-1">
                {data.trend_data.slice(-3).map((point, index) => (
                  <div key={index} className="flex items-center space-x-3 text-base leading-relaxed">
                    <span className="text-gray-400 w-16">{formatDate(point.date)}</span>
                    <span className={`font-semibold ${getScoreColor(point.score)}`}>
                      {point.score}
                    </span>
                    {getTrendIcon(point.change)}
                    {point.change && (
                      <span className={`text-base leading-relaxed ${point.change > 0 ? 'text-[#00e676]' : 'text-[#ff2d2d]'}`}>
                        {point.change > 0 ? '+' : ''}{point.change}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default JobSecurityAnalysis; 