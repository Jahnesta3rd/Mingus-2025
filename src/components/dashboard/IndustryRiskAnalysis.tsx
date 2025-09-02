import React, { useState, useEffect } from 'react';
import { 
  TrendingUp, 
  TrendingDown, 
  AlertTriangle, 
  CheckCircle, 
  MapPin, 
  Monitor, 
  Users, 
  DollarSign,
  ArrowUpRight,
  ArrowDownRight,
  Minus,
  Building2,
  Briefcase,
  Target,
  Lightbulb,
  BarChart3,
  Shield,
  Zap,
  Globe,
  Home
} from 'lucide-react';

interface IndustryRiskData {
  naics_code: string;
  industry_name: string;
  overall_risk_level: string;
  overall_risk_score: number;
  employment_trends: {
    employment_trend: number;
    job_growth_rate: number;
    unemployment_rate: number;
    trend_direction: string;
    growth_category: string;
  };
  automation_risk: {
    automation_risk_score: number;
    ai_replacement_probability: number;
    routine_task_percentage: number;
    cognitive_skill_requirement: number;
    risk_level: string;
    mitigation_strategies: string[];
  };
  economic_sensitivity: {
    economic_cycle_sensitivity: number;
    recession_resilience: number;
    gdp_correlation: number;
    sensitivity_category: string;
    resilience_category: string;
  };
  geographic_factors: {
    geographic_concentration: number;
    remote_work_adoption: number;
    location_flexibility: number;
    concentration_risk: string;
    remote_work_potential: string;
  };
  career_advancement: {
    advancement_opportunities: number;
    skill_development_potential: number;
    salary_growth_potential: number;
    leadership_representation: number;
    recommendations: string[];
    positive_indicators: string[];
    advancement_category: string;
  };
  risk_factors: string[];
  positive_indicators: string[];
  recommendations: string[];
  last_updated: string;
  confidence_level: number;
}

interface IndustryRiskAnalysisProps {
  industryName: string;
  jobTitle?: string;
  location?: string;
  className?: string;
  onDrillDown?: (section: string) => void;
}

const IndustryRiskAnalysis: React.FC<IndustryRiskAnalysisProps> = ({
  industryName,
  jobTitle = '',
  location = '',
  className = '',
  onDrillDown
}) => {
  const [riskData, setRiskData] = useState<IndustryRiskData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    const fetchRiskData = async () => {
      try {
        setLoading(true);
        // Simulate API call - replace with actual endpoint
        const response = await fetch('/api/industry-risk-assessment', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            industry_name: industryName,
            job_title: jobTitle,
            location: location
          })
        });

        if (!response.ok) {
          throw new Error('Failed to fetch industry risk data');
        }

        const data = await response.json();
        setRiskData(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred');
      } finally {
        setLoading(false);
      }
    };

    if (industryName) {
      fetchRiskData();
    }
  }, [industryName, jobTitle, location]);

  const getRiskColor = (score: number) => {
    if (score <= 20) return 'text-green-500';
    if (score <= 40) return 'text-blue-500';
    if (score <= 60) return 'text-yellow-500';
    if (score <= 80) return 'text-orange-500';
    return 'text-red-500';
  };

  const getRiskBgColor = (score: number) => {
    if (score <= 20) return 'bg-green-500/10';
    if (score <= 40) return 'bg-blue-500/10';
    if (score <= 60) return 'bg-yellow-500/10';
    if (score <= 80) return 'bg-orange-500/10';
    return 'bg-red-500/10';
  };

  const getRiskLevel = (score: number) => {
    if (score <= 20) return 'Very Low';
    if (score <= 40) return 'Low';
    if (score <= 60) return 'Moderate';
    if (score <= 80) return 'High';
    return 'Very High';
  };

  const getTrendIcon = (trend: number) => {
    if (trend > 0) return <ArrowUpRight className="w-4 h-4 text-green-500" />;
    if (trend < 0) return <ArrowDownRight className="w-4 h-4 text-red-500" />;
    return <Minus className="w-4 h-4 text-gray-500" />;
  };

  const getTrendColor = (trend: number) => {
    if (trend > 0) return 'text-green-500';
    if (trend < 0) return 'text-red-500';
    return 'text-gray-500';
  };

  if (loading) {
    return (
      <div className={`bg-gray-900 rounded-lg p-6 ${className}`}>
        <div className="animate-pulse">
          <div className="h-6 bg-gray-700 rounded w-1/3 mb-4"></div>
          <div className="space-y-3">
            <div className="h-4 bg-gray-700 rounded"></div>
            <div className="h-4 bg-gray-700 rounded w-5/6"></div>
            <div className="h-4 bg-gray-700 rounded w-4/6"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !riskData) {
    return (
      <div className={`bg-gray-900 rounded-lg p-6 ${className}`}>
        <div className="text-center">
          <AlertTriangle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-white mb-2" className="text-xl font-semibold text-gray-800 mb-3">Analysis Unavailable</h3>
          <p className="text-gray-400">
            {error || 'Unable to load industry risk analysis at this time.'}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-gray-900 rounded-lg border border-gray-800 ${className}`}>
      {/* Header */}
      <div className="p-6 border-b border-gray-800">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <Building2 className="w-6 h-6 text-blue-500" />
            <div>
              <h2 className="text-xl font-bold text-white" className="text-2xl font-semibold text-gray-800 mb-4">{riskData.industry_name}</h2>
              <p className="text-gray-400 text-base leading-relaxed">NAICS: {riskData.naics_code}</p>
            </div>
          </div>
          <div className="text-right">
            <div className={`inline-flex items-center px-3 py-1 rounded-full text-base leading-relaxed font-medium ${getRiskBgColor(riskData.overall_risk_score)} ${getRiskColor(riskData.overall_risk_score)}`}>
              {getRiskLevel(riskData.overall_risk_score)} Risk
            </div>
            <p className="text-gray-400 text-base leading-relaxed mt-1">
              Score: {riskData.overall_risk_score}/100
            </p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="flex space-x-1 bg-gray-800 rounded-lg p-1">
          {[
            { id: 'overview', label: 'Overview', icon: BarChart3 },
            { id: 'employment', label: 'Employment', icon: TrendingUp },
            { id: 'automation', label: 'Automation', icon: Zap },
            { id: 'economic', label: 'Economic', icon: DollarSign },
            { id: 'geographic', label: 'Geographic', icon: MapPin },
            { id: 'career', label: 'Career', icon: Target }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center space-x-2 px-3 py-2 rounded-md text-base leading-relaxed font-medium transition-colors ${
                activeTab === tab.id
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-400 hover:text-white hover:bg-gray-700'
              }`}
            >
              <tab.icon className="w-4 h-4" />
              <span>{tab.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="p-6">
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Risk Score Overview */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-gray-800 rounded-lg p-4">
                <div className="flex items-center space-x-3 mb-3">
                  <Shield className="w-5 h-5 text-blue-500" />
                  <h3 className="font-semibold text-white" className="text-xl font-semibold text-gray-800 mb-3">Overall Risk</h3>
                </div>
                <div className="text-2xl font-bold text-white mb-1">
                  {riskData.overall_risk_score}
                </div>
                <div className={`text-base leading-relaxed ${getRiskColor(riskData.overall_risk_score)}`}>
                  {getRiskLevel(riskData.overall_risk_score)} Risk Level
                </div>
              </div>

              <div className="bg-gray-800 rounded-lg p-4">
                <div className="flex items-center space-x-3 mb-3">
                  <TrendingUp className="w-5 h-5 text-green-500" />
                  <h3 className="font-semibold text-white" className="text-xl font-semibold text-gray-800 mb-3">Job Growth</h3>
                </div>
                <div className="flex items-center space-x-2">
                  {getTrendIcon(riskData.employment_trends.employment_trend)}
                  <span className={`text-2xl font-bold ${getTrendColor(riskData.employment_trends.employment_trend)}`}>
                    {Math.abs(riskData.employment_trends.job_growth_rate).toFixed(1)}%
                  </span>
                </div>
                <div className="text-base leading-relaxed text-gray-400">
                  Annual growth rate
                </div>
              </div>

              <div className="bg-gray-800 rounded-lg p-4">
                <div className="flex items-center space-x-3 mb-3">
                  <Zap className="w-5 h-5 text-yellow-500" />
                  <h3 className="font-semibold text-white" className="text-xl font-semibold text-gray-800 mb-3">Automation Risk</h3>
                </div>
                <div className="text-2xl font-bold text-white mb-1">
                  {riskData.automation_risk.automation_risk_score}
                </div>
                <div className="text-base leading-relaxed text-gray-400">
                  {riskData.automation_risk.risk_level} risk
                </div>
              </div>
            </div>

            {/* Key Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-gray-800 rounded-lg p-4">
                <h3 className="font-semibold text-white mb-4 flex items-center space-x-2" className="text-xl font-semibold text-gray-800 mb-3">
                  <AlertTriangle className="w-5 h-5 text-red-500" />
                  <span>Risk Factors</span>
                </h3>
                <ul className="space-y-2">
                  {riskData.risk_factors.map((factor, index) => (
                    <li key={index} className="flex items-start space-x-2 text-base leading-relaxed text-gray-300">
                      <div className="w-1.5 h-1.5 bg-red-500 rounded-full mt-2 flex-shrink-0"></div>
                      <span>{factor}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="bg-gray-800 rounded-lg p-4">
                <h3 className="font-semibold text-white mb-4 flex items-center space-x-2" className="text-xl font-semibold text-gray-800 mb-3">
                  <CheckCircle className="w-5 h-5 text-green-500" />
                  <span>Positive Indicators</span>
                </h3>
                <ul className="space-y-2">
                  {riskData.positive_indicators.map((indicator, index) => (
                    <li key={index} className="flex items-start space-x-2 text-base leading-relaxed text-gray-300">
                      <div className="w-1.5 h-1.5 bg-green-500 rounded-full mt-2 flex-shrink-0"></div>
                      <span>{indicator}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            {/* Recommendations */}
            <div className="bg-gray-800 rounded-lg p-4">
              <h3 className="font-semibold text-white mb-4 flex items-center space-x-2" className="text-xl font-semibold text-gray-800 mb-3">
                <Lightbulb className="w-5 h-5 text-yellow-500" />
                <span>Recommendations</span>
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {riskData.recommendations.slice(0, 6).map((rec, index) => (
                  <div key={index} className="flex items-start space-x-3 p-3 bg-gray-700 rounded-lg">
                    <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
                    <p className="text-base leading-relaxed text-gray-300">{rec}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'employment' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-gray-800 rounded-lg p-4">
                <h3 className="font-semibold text-white mb-4" className="text-xl font-semibold text-gray-800 mb-3">Employment Trends</h3>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-gray-400">Employment Trend</span>
                    <div className="flex items-center space-x-2">
                      {getTrendIcon(riskData.employment_trends.employment_trend)}
                      <span className={`font-semibold ${getTrendColor(riskData.employment_trends.employment_trend)}`}>
                        {riskData.employment_trends.employment_trend > 0 ? '+' : ''}{riskData.employment_trends.employment_trend.toFixed(1)}%
                      </span>
                    </div>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-400">Job Growth Rate</span>
                    <span className="font-semibold text-white">{riskData.employment_trends.job_growth_rate.toFixed(1)}%</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-400">Unemployment Rate</span>
                    <span className="font-semibold text-white">{riskData.employment_trends.unemployment_rate.toFixed(1)}%</span>
                  </div>
                </div>
              </div>

              <div className="bg-gray-800 rounded-lg p-4">
                <h3 className="font-semibold text-white mb-4" className="text-xl font-semibold text-gray-800 mb-3">Growth Analysis</h3>
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-gray-400">Growth Category</span>
                      <span className="font-semibold text-white capitalize">{riskData.employment_trends.growth_category}</span>
                    </div>
                    <div className="w-full bg-gray-700 rounded-full h-2">
                      <div 
                        className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${Math.max(0, Math.min(100, riskData.employment_trends.job_growth_rate * 10))}%` }}
                      ></div>
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-gray-400">Trend Direction</span>
                      <span className="font-semibold text-white capitalize">{riskData.employment_trends.trend_direction}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'automation' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-gray-800 rounded-lg p-4">
                <h3 className="font-semibold text-white mb-4" className="text-xl font-semibold text-gray-800 mb-3">Automation Risk Assessment</h3>
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-gray-400">Automation Risk Score</span>
                      <span className="font-semibold text-white">{riskData.automation_risk.automation_risk_score}/100</span>
                    </div>
                    <div className="w-full bg-gray-700 rounded-full h-2">
                      <div 
                        className="bg-yellow-500 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${riskData.automation_risk.automation_risk_score}%` }}
                      ></div>
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-gray-400">AI Replacement Probability</span>
                      <span className="font-semibold text-white">{(riskData.automation_risk.ai_replacement_probability * 100).toFixed(1)}%</span>
                    </div>
                    <div className="w-full bg-gray-700 rounded-full h-2">
                      <div 
                        className="bg-red-500 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${riskData.automation_risk.ai_replacement_probability * 100}%` }}
                      ></div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-gray-800 rounded-lg p-4">
                <h3 className="font-semibold text-white mb-4" className="text-xl font-semibold text-gray-800 mb-3">Task Analysis</h3>
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-gray-400">Routine Tasks</span>
                      <span className="font-semibold text-white">{riskData.automation_risk.routine_task_percentage.toFixed(1)}%</span>
                    </div>
                    <div className="w-full bg-gray-700 rounded-full h-2">
                      <div 
                        className="bg-orange-500 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${riskData.automation_risk.routine_task_percentage}%` }}
                      ></div>
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-gray-400">Cognitive Skills Required</span>
                      <span className="font-semibold text-white">{riskData.automation_risk.cognitive_skill_requirement.toFixed(1)}%</span>
                    </div>
                    <div className="w-full bg-gray-700 rounded-full h-2">
                      <div 
                        className="bg-green-500 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${riskData.automation_risk.cognitive_skill_requirement}%` }}
                      ></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-gray-800 rounded-lg p-4">
              <h3 className="font-semibold text-white mb-4" className="text-xl font-semibold text-gray-800 mb-3">Mitigation Strategies</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {riskData.automation_risk.mitigation_strategies.map((strategy, index) => (
                  <div key={index} className="flex items-start space-x-3 p-3 bg-gray-700 rounded-lg">
                    <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
                    <p className="text-base leading-relaxed text-gray-300">{strategy}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'economic' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-gray-800 rounded-lg p-4">
                <h3 className="font-semibold text-white mb-4" className="text-xl font-semibold text-gray-800 mb-3">Economic Sensitivity</h3>
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-gray-400">Cycle Sensitivity</span>
                      <span className="font-semibold text-white">{riskData.economic_sensitivity.economic_cycle_sensitivity}/100</span>
                    </div>
                    <div className="w-full bg-gray-700 rounded-full h-2">
                      <div 
                        className="bg-orange-500 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${riskData.economic_sensitivity.economic_cycle_sensitivity}%` }}
                      ></div>
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-gray-400">Recession Resilience</span>
                      <span className="font-semibold text-white">{riskData.economic_sensitivity.recession_resilience}/100</span>
                    </div>
                    <div className="w-full bg-gray-700 rounded-full h-2">
                      <div 
                        className="bg-green-500 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${riskData.economic_sensitivity.recession_resilience}%` }}
                      ></div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-gray-800 rounded-lg p-4">
                <h3 className="font-semibold text-white mb-4" className="text-xl font-semibold text-gray-800 mb-3">GDP Correlation</h3>
                <div className="text-center">
                  <div className="text-3xl font-bold text-white mb-2">
                    {riskData.economic_sensitivity.gdp_correlation > 0 ? '+' : ''}{riskData.economic_sensitivity.gdp_correlation.toFixed(2)}
                  </div>
                  <p className="text-gray-400 text-base leading-relaxed">
                    {Math.abs(riskData.economic_sensitivity.gdp_correlation) > 0.7 ? 'Strong' : 
                     Math.abs(riskData.economic_sensitivity.gdp_correlation) > 0.4 ? 'Moderate' : 'Weak'} correlation
                  </p>
                </div>
              </div>

              <div className="bg-gray-800 rounded-lg p-4">
                <h3 className="font-semibold text-white mb-4" className="text-xl font-semibold text-gray-800 mb-3">Risk Categories</h3>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-gray-400">Sensitivity</span>
                    <span className="font-semibold text-white capitalize">{riskData.economic_sensitivity.sensitivity_category}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-400">Resilience</span>
                    <span className="font-semibold text-white capitalize">{riskData.economic_sensitivity.resilience_category}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'geographic' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-gray-800 rounded-lg p-4">
                <h3 className="font-semibold text-white mb-4" className="text-xl font-semibold text-gray-800 mb-3">Geographic Factors</h3>
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-gray-400">Geographic Concentration</span>
                      <span className="font-semibold text-white">{riskData.geographic_factors.geographic_concentration.toFixed(1)}%</span>
                    </div>
                    <div className="w-full bg-gray-700 rounded-full h-2">
                      <div 
                        className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${riskData.geographic_factors.geographic_concentration}%` }}
                      ></div>
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-gray-400">Remote Work Adoption</span>
                      <span className="font-semibold text-white">{riskData.geographic_factors.remote_work_adoption.toFixed(1)}%</span>
                    </div>
                    <div className="w-full bg-gray-700 rounded-full h-2">
                      <div 
                        className="bg-green-500 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${riskData.geographic_factors.remote_work_adoption}%` }}
                      ></div>
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-gray-400">Location Flexibility</span>
                      <span className="font-semibold text-white">{riskData.geographic_factors.location_flexibility.toFixed(1)}%</span>
                    </div>
                    <div className="w-full bg-gray-700 rounded-full h-2">
                      <div 
                        className="bg-purple-500 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${riskData.geographic_factors.location_flexibility}%` }}
                      ></div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-gray-800 rounded-lg p-4">
                <h3 className="font-semibold text-white mb-4" className="text-xl font-semibold text-gray-800 mb-3">Risk Assessment</h3>
                <div className="space-y-4">
                  <div className="flex justify-between items-center p-3 bg-gray-700 rounded-lg">
                    <span className="text-gray-400">Concentration Risk</span>
                    <span className="font-semibold text-white capitalize">{riskData.geographic_factors.concentration_risk}</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-gray-700 rounded-lg">
                    <span className="text-gray-400">Remote Work Potential</span>
                    <span className="font-semibold text-white capitalize">{riskData.geographic_factors.remote_work_potential}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'career' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-gray-800 rounded-lg p-4">
                <h3 className="font-semibold text-white mb-4" className="text-xl font-semibold text-gray-800 mb-3">Career Advancement Metrics</h3>
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-gray-400">Advancement Opportunities</span>
                      <span className="font-semibold text-white">{riskData.career_advancement.advancement_opportunities.toFixed(1)}%</span>
                    </div>
                    <div className="w-full bg-gray-700 rounded-full h-2">
                      <div 
                        className="bg-green-500 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${riskData.career_advancement.advancement_opportunities}%` }}
                      ></div>
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-gray-400">Skill Development</span>
                      <span className="font-semibold text-white">{riskData.career_advancement.skill_development_potential.toFixed(1)}%</span>
                    </div>
                    <div className="w-full bg-gray-700 rounded-full h-2">
                      <div 
                        className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${riskData.career_advancement.skill_development_potential}%` }}
                      ></div>
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-gray-400">Salary Growth</span>
                      <span className="font-semibold text-white">{riskData.career_advancement.salary_growth_potential.toFixed(1)}%</span>
                    </div>
                    <div className="w-full bg-gray-700 rounded-full h-2">
                      <div 
                        className="bg-yellow-500 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${riskData.career_advancement.salary_growth_potential}%` }}
                      ></div>
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-gray-400">Leadership Representation</span>
                      <span className="font-semibold text-white">{riskData.career_advancement.leadership_representation.toFixed(1)}%</span>
                    </div>
                    <div className="w-full bg-gray-700 rounded-full h-2">
                      <div 
                        className="bg-purple-500 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${riskData.career_advancement.leadership_representation}%` }}
                      ></div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-gray-800 rounded-lg p-4">
                <h3 className="font-semibold text-white mb-4" className="text-xl font-semibold text-gray-800 mb-3">Advancement Category</h3>
                <div className="text-center">
                  <div className="text-3xl font-bold text-white mb-2 capitalize">
                    {riskData.career_advancement.advancement_category}
                  </div>
                  <p className="text-gray-400 text-base leading-relaxed">
                    Career advancement opportunities
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-gray-800 rounded-lg p-4">
              <h3 className="font-semibold text-white mb-4" className="text-xl font-semibold text-gray-800 mb-3">Career Recommendations</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {riskData.career_advancement.recommendations.map((rec, index) => (
                  <div key={index} className="flex items-start space-x-3 p-3 bg-gray-700 rounded-lg">
                    <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
                    <p className="text-base leading-relaxed text-gray-300">{rec}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-gray-800 bg-gray-800/50">
        <div className="flex items-center justify-between text-base leading-relaxed text-gray-400">
          <div className="flex items-center space-x-4">
            <span>Last updated: {new Date(riskData.last_updated).toLocaleDateString()}</span>
            <span>Confidence: {(riskData.confidence_level * 100).toFixed(0)}%</span>
          </div>
          <button
            onClick={() => onDrillDown?.(activeTab)}
            className="text-blue-500 hover:text-blue-400 transition-colors"
          >
            View Details →
          </button>
        </div>
      </div>
    </div>
  );
};

export default IndustryRiskAnalysis; 