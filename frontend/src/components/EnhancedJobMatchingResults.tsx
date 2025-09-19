import React, { useState } from 'react';
import { 
  Target, 
  TrendingUp, 
  Users, 
  Award, 
  Clock, 
  DollarSign, 
  CheckCircle, 
  AlertCircle,
  Lightbulb,
  BarChart3,
  ArrowRight,
  ExternalLink,
  Star,
  Zap,
  Brain,
  Briefcase
} from 'lucide-react';

interface ProblemStatement {
  context: string;
  challenge: string;
  impact: string;
  desired_outcome: string;
  timeframe: string;
  constraints: string[];
}

interface SolutionRecommendation {
  name: string;
  description: string;
  total_score: number;
  relevance_score: number;
  industry_demand_score: number;
  career_impact_score: number;
  learning_roi_score: number;
  competitive_advantage_score: number;
  reasoning: string;
  time_to_acquire: string;
  cost_estimate: string;
  salary_impact: string;
}

interface ProblemSolutionSummary {
  problem_statement: ProblemStatement;
  industry_context: string;
  company_stage: string;
  confidence_score: number;
  top_solutions: {
    skills: Array<{name: string; score: number}>;
    certifications: Array<{name: string; score: number}>;
    titles: Array<{name: string; score: number}>;
  };
}

interface CareerPositioningPlan {
  problem_solving_focus: string;
  solution_roadmap: Array<{
    skill: string;
    timeline: string;
    cost: string;
    expected_impact: string;
  }>;
  skill_development_plan: {
    immediate_actions: Array<{
      action: string;
      timeline: string;
      cost: string;
      priority: string;
    }>;
    short_term_goals: Array<{
      action: string;
      timeline: string;
      cost: string;
      priority: string;
    }>;
    medium_term_goals: Array<{
      action: string;
      timeline: string;
      cost: string;
      priority: string;
    }>;
    long_term_goals: Array<{
      action: string;
      timeline: string;
      cost: string;
      priority: string;
    }>;
  };
  networking_strategy: string[];
  portfolio_projects: string[];
  interview_preparation: string[];
}

interface EnhancedJobMatch {
  job_opportunity: {
    job_id: string;
    title: string;
    company: string;
    location: string;
    salary_min: number;
    salary_max: number;
    salary_median: number;
    url: string;
    description: string;
    overall_score: number;
  };
  enhanced_score: number;
  problem_solution_alignment: number;
  positioning_strategy: {
    problem_focus: string;
    solution_approach: string[];
    key_skills_to_highlight: string[];
    value_proposition: string;
    interview_talking_points: Array<{
      problem: string;
      solution: string;
      impact: string;
    }>;
    resume_keywords: string[];
  };
  application_insights: {
    application_strength: number;
    skill_gaps: Array<{
      skill: string;
      priority: string;
      time_to_learn: string;
      cost: string;
    }>;
    immediate_actions: string[];
    salary_negotiation_points: string[];
    company_research_focus: string[];
    cover_letter_angles: string[];
  };
}

interface EnhancedMatchingResult {
  job_matches: EnhancedJobMatch[];
  problem_solution_summary: ProblemSolutionSummary;
  career_positioning_plan: CareerPositioningPlan;
  success_probability: number;
  generated_at: string;
}

interface EnhancedJobMatchingResultsProps {
  result: EnhancedMatchingResult;
  userTier: 'Budget' | 'Mid-tier' | 'Professional';
  onJobSelect?: (job: EnhancedJobMatch) => void;
  onUpgradePrompt?: () => void;
  className?: string;
}

const EnhancedJobMatchingResults: React.FC<EnhancedJobMatchingResultsProps> = ({
  result,
  userTier,
  onJobSelect,
  onUpgradePrompt,
  className = ''
}) => {
  const [activeTab, setActiveTab] = useState<'overview' | 'problems' | 'solutions' | 'positioning' | 'jobs'>('overview');
  const [expandedJob, setExpandedJob] = useState<string | null>(null);

  const getTierColor = (tier: string) => {
    switch (tier) {
      case 'Budget': return 'bg-violet-600';
      case 'Mid-tier': return 'bg-purple-600';
      case 'Professional': return 'bg-violet-700';
      default: return 'bg-slate-600';
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-400';
    if (score >= 60) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'High': return 'bg-red-100 text-red-800';
      case 'Medium': return 'bg-yellow-100 text-yellow-800';
      case 'Low': return 'bg-green-100 text-green-800';
      default: return 'bg-slate-600 text-white';
    }
  };

  const formatSalary = (min: number, max: number) => {
    return `$${(min / 1000).toFixed(0)}k - $${(max / 1000).toFixed(0)}k`;
  };

  const tabs = [
    { id: 'overview', label: 'Overview', icon: BarChart3 },
    { id: 'problems', label: 'Problem Analysis', icon: Target },
    { id: 'solutions', label: 'Solutions', icon: Lightbulb },
    { id: 'positioning', label: 'Positioning', icon: Brain },
    { id: 'jobs', label: 'Job Matches', icon: Briefcase }
  ];

  return (
    <div className={`bg-slate-900 ${className}`}>
      {/* Header */}
      <div className="bg-gradient-to-r from-violet-600 to-purple-600 p-6 rounded-t-xl">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-white mb-2">
              Enhanced Job Matching Results
            </h2>
            <p className="text-violet-100">
              Problem-Solution Analysis for Strategic Career Positioning
            </p>
          </div>
          <div className="text-right">
            <div className="text-3xl font-bold text-white">
              {Math.round(result.success_probability * 100)}%
            </div>
            <div className="text-violet-100 text-sm">Success Probability</div>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="bg-slate-800 border-b border-slate-700">
        <div className="flex space-x-1 p-4">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center space-x-2 px-4 py-2 rounded-lg font-medium transition-colors ${
                  activeTab === tab.id
                    ? 'bg-violet-600 text-white'
                    : 'text-gray-400 hover:text-violet-400 hover:bg-slate-700'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Content */}
      <div className="p-6">
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Success Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 shadow-sm">
                <div className="flex items-center space-x-3 mb-4">
                  <div className="p-2 bg-violet-100 rounded-lg">
                    <Target className="w-6 h-6 text-violet-600" />
                  </div>
                  <h3 className="text-lg font-semibold text-white">Problem Analysis</h3>
                </div>
                <div className="text-2xl font-bold text-white mb-2">
                  {Math.round(result.problem_solution_summary.confidence_score * 100)}%
                </div>
                <div className="text-gray-400 text-sm">Confidence Score</div>
                <div className="text-sm text-gray-500 mt-2">
                  {result.problem_solution_summary.industry_context} • {result.problem_solution_summary.company_stage}
                </div>
              </div>

              <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 shadow-sm">
                <div className="flex items-center space-x-3 mb-4">
                  <div className="p-2 bg-yellow-100 rounded-lg">
                    <Lightbulb className="w-6 h-6 text-yellow-400" />
                  </div>
                  <h3 className="text-lg font-semibold text-white">Solutions Generated</h3>
                </div>
                <div className="text-2xl font-bold text-white mb-2">
                  {result.problem_solution_summary.top_solutions.skills.length + 
                   result.problem_solution_summary.top_solutions.certifications.length + 
                   result.problem_solution_summary.top_solutions.titles.length}
                </div>
                <div className="text-gray-400 text-sm">Total Recommendations</div>
                <div className="text-sm text-gray-500 mt-2">
                  Skills • Certifications • Titles
                </div>
              </div>

              <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 shadow-sm">
                <div className="flex items-center space-x-3 mb-4">
                  <div className="p-2 bg-green-100 rounded-lg">
                    <Briefcase className="w-6 h-6 text-green-400" />
                  </div>
                  <h3 className="text-lg font-semibold text-white">Job Matches</h3>
                </div>
                <div className="text-2xl font-bold text-white mb-2">
                  {result.job_matches.length}
                </div>
                <div className="text-gray-400 text-sm">Enhanced Matches</div>
                <div className="text-sm text-gray-500 mt-2">
                  Problem-Solution Aligned
                </div>
              </div>
            </div>

            {/* Problem Statement */}
            <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 shadow-sm">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center space-x-2">
                <div className="p-2 bg-violet-100 rounded-lg">
                  <Target className="w-5 h-5 text-violet-600" />
                </div>
                <span>Problem Statement</span>
              </h3>
              <div className="bg-slate-700 border border-slate-600 rounded-lg p-4">
                <p className="text-gray-400 leading-relaxed">
                  <span className="font-semibold text-white">{result.problem_solution_summary.problem_statement.context}</span> facing{' '}
                  <span className="text-violet-400 font-medium">{result.problem_solution_summary.problem_statement.challenge}</span> which is causing{' '}
                  <span className="text-red-400 font-medium">{result.problem_solution_summary.problem_statement.impact}</span>. They need{' '}
                  <span className="text-yellow-400 font-medium">solution-focused professionals</span> to achieve{' '}
                  <span className="text-green-400 font-medium">{result.problem_solution_summary.problem_statement.desired_outcome}</span>.
                </p>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-gradient-to-r from-violet-600 to-purple-600 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-white mb-3">Next Steps</h3>
                <ul className="space-y-2 text-violet-100">
                  <li className="flex items-center space-x-2">
                    <CheckCircle className="w-4 h-4" />
                    <span>Review problem-solution analysis</span>
                  </li>
                  <li className="flex items-center space-x-2">
                    <CheckCircle className="w-4 h-4" />
                    <span>Develop positioning strategy</span>
                  </li>
                  <li className="flex items-center space-x-2">
                    <CheckCircle className="w-4 h-4" />
                    <span>Apply to enhanced job matches</span>
                  </li>
                </ul>
              </div>

              <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 shadow-sm">
                <h3 className="text-lg font-semibold text-white mb-3">Tier Benefits</h3>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-gray-400">Current Tier:</span>
                    <span className={`px-2 py-1 rounded-full text-xs font-semibold ${getTierColor(userTier)} text-white`}>
                      {userTier}
                    </span>
                  </div>
                  {userTier === 'Budget' && (
                    <div className="text-sm text-yellow-400">
                      Upgrade to Mid-tier for advanced AI analysis
                    </div>
                  )}
                  {userTier === 'Mid-tier' && (
                    <div className="text-sm text-green-400">
                      Full access to enhanced features
                    </div>
                  )}
                  {userTier === 'Professional' && (
                    <div className="text-sm text-purple-400">
                      Premium executive-level positioning
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'problems' && (
          <div className="space-y-6">
            <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 shadow-sm">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center space-x-2">
                <div className="p-2 bg-violet-100 rounded-lg">
                  <Target className="w-5 h-5 text-violet-600" />
                </div>
                <span>Business Problem Analysis</span>
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="text-md font-semibold text-gray-400 mb-3">Context</h4>
                  <p className="text-gray-500 bg-slate-700 border border-slate-700 rounded-lg p-3">
                    {result.problem_solution_summary.problem_statement.context}
                  </p>
                </div>
                
                <div>
                  <h4 className="text-md font-semibold text-gray-400 mb-3">Primary Challenge</h4>
                  <p className="text-red-400 bg-red-50 border border-red-200 rounded-lg p-3">
                    {result.problem_solution_summary.problem_statement.challenge}
                  </p>
                </div>
                
                <div>
                  <h4 className="text-md font-semibold text-gray-400 mb-3">Business Impact</h4>
                  <p className="text-yellow-400 bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                    {result.problem_solution_summary.problem_statement.impact}
                  </p>
                </div>
                
                <div>
                  <h4 className="text-md font-semibold text-gray-400 mb-3">Desired Outcome</h4>
                  <p className="text-green-400 bg-green-50 border border-green-200 rounded-lg p-3">
                    {result.problem_solution_summary.problem_statement.desired_outcome}
                  </p>
                </div>
              </div>

              <div className="mt-6">
                <h4 className="text-md font-semibold text-gray-400 mb-3">Constraints & Timeline</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="bg-slate-700 border border-slate-700 rounded-lg p-3">
                    <div className="flex items-center space-x-2 mb-2">
                      <Clock className="w-4 h-4 text-violet-600" />
                      <span className="text-sm font-medium text-gray-400">Timeline</span>
                    </div>
                    <p className="text-gray-500">{result.problem_solution_summary.problem_statement.timeframe}</p>
                  </div>
                  <div className="bg-slate-700 border border-slate-700 rounded-lg p-3">
                    <div className="flex items-center space-x-2 mb-2">
                      <AlertCircle className="w-4 h-4 text-orange-600" />
                      <span className="text-sm font-medium text-gray-400">Constraints</span>
                    </div>
                    <ul className="text-gray-500 text-sm space-y-1">
                      {result.problem_solution_summary.problem_statement.constraints.map((constraint, index) => (
                        <li key={index}>• {constraint}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'solutions' && (
          <div className="space-y-6">
            {/* Skills */}
            <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 shadow-sm">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center space-x-2">
                <div className="p-2 bg-yellow-100 rounded-lg">
                  <Zap className="w-5 h-5 text-yellow-400" />
                </div>
                <span>Top Skill Recommendations</span>
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {result.problem_solution_summary.top_solutions.skills.map((skill, index) => (
                  <div key={index} className="bg-slate-700 border border-slate-700 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-semibold text-white">{skill.name}</h4>
                      <span className={`text-lg font-bold ${getScoreColor(skill.score)}`}>
                        {skill.score}/100
                      </span>
                    </div>
                    <div className="w-full bg-slate-500 rounded-full h-2 mb-2">
                      <div 
                        className="bg-gradient-to-r from-yellow-400 to-yellow-500 h-2 rounded-full"
                        style={{ width: `${skill.score}%` }}
                      ></div>
                    </div>
                    <div className="text-sm text-gray-500">
                      High-demand skill for {result.problem_solution_summary.industry_context} industry
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Certifications */}
            <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 shadow-sm">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center space-x-2">
                <div className="p-2 bg-violet-100 rounded-lg">
                  <Award className="w-5 h-5 text-violet-600" />
                </div>
                <span>Certification Recommendations</span>
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {result.problem_solution_summary.top_solutions.certifications.map((cert, index) => (
                  <div key={index} className="bg-slate-700 border border-slate-700 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-semibold text-white">{cert.name}</h4>
                      <span className={`text-lg font-bold ${getScoreColor(cert.score)}`}>
                        {cert.score}/100
                      </span>
                    </div>
                    <div className="w-full bg-slate-500 rounded-full h-2 mb-2">
                      <div 
                        className="bg-gradient-to-r from-blue-400 to-blue-500 h-2 rounded-full"
                        style={{ width: `${cert.score}%` }}
                      ></div>
                    </div>
                    <div className="text-sm text-gray-500">
                      Industry-recognized certification
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Titles */}
            <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 shadow-sm">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center space-x-2">
                <div className="p-2 bg-green-100 rounded-lg">
                  <Briefcase className="w-5 h-5 text-green-400" />
                </div>
                <span>Optimal Title Recommendations</span>
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {result.problem_solution_summary.top_solutions.titles.map((title, index) => (
                  <div key={index} className="bg-slate-700 border border-slate-700 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-semibold text-white">{title.name}</h4>
                      <span className={`text-lg font-bold ${getScoreColor(title.score)}`}>
                        {title.score}/100
                      </span>
                    </div>
                    <div className="w-full bg-slate-500 rounded-full h-2 mb-2">
                      <div 
                        className="bg-gradient-to-r from-green-400 to-green-500 h-2 rounded-full"
                        style={{ width: `${title.score}%` }}
                      ></div>
                    </div>
                    <div className="text-sm text-gray-500">
                      Strategic positioning title
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'positioning' && (
          <div className="space-y-6">
            {/* Problem-Solution Focus */}
            <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 shadow-sm">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center space-x-2">
                <div className="p-2 bg-purple-100 rounded-lg">
                  <Brain className="w-5 h-5 text-purple-600" />
                </div>
                <span>Strategic Positioning</span>
              </h3>
              
              <div className="bg-slate-700 border border-slate-700 rounded-lg p-4 mb-6">
                <h4 className="font-semibold text-white mb-2">Problem Focus</h4>
                <p className="text-gray-400">{result.career_positioning_plan.problem_solving_focus}</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="font-semibold text-white mb-3">Solution Roadmap</h4>
                  <div className="space-y-3">
                    {result.career_positioning_plan.solution_roadmap.slice(0, 3).map((item, index) => (
                      <div key={index} className="bg-slate-700 border border-slate-700 rounded-lg p-3">
                        <div className="flex items-center justify-between mb-1">
                          <span className="font-medium text-white">{item.skill}</span>
                          <span className="text-sm text-gray-500">{item.timeline}</span>
                        </div>
                        <div className="text-sm text-gray-500">
                          Cost: {item.cost} • Impact: {item.expected_impact}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div>
                  <h4 className="font-semibold text-white mb-3">Networking Strategy</h4>
                  <div className="space-y-2">
                    {result.career_positioning_plan.networking_strategy.slice(0, 3).map((strategy, index) => (
                      <div key={index} className="flex items-center space-x-2 text-gray-400">
                        <Users className="w-4 h-4 text-violet-600" />
                        <span className="text-sm">{strategy}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Action Plan */}
            <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 shadow-sm">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center space-x-2">
                <div className="p-2 bg-green-100 rounded-lg">
                  <Clock className="w-5 h-5 text-green-400" />
                </div>
                <span>Action Plan</span>
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div>
                  <h4 className="font-semibold text-white mb-3 text-sm">Immediate (0-30 days)</h4>
                  <div className="space-y-2">
                    {result.career_positioning_plan.skill_development_plan.immediate_actions.slice(0, 2).map((action, index) => (
                      <div key={index} className="bg-slate-700 border border-slate-700 rounded-lg p-2">
                        <div className="text-xs text-white font-medium">{action.action}</div>
                        <div className="text-xs text-gray-500">{action.timeline}</div>
                      </div>
                    ))}
                  </div>
                </div>

                <div>
                  <h4 className="font-semibold text-white mb-3 text-sm">Short-term (30-60 days)</h4>
                  <div className="space-y-2">
                    {result.career_positioning_plan.skill_development_plan.short_term_goals.slice(0, 2).map((goal, index) => (
                      <div key={index} className="bg-slate-700 border border-slate-700 rounded-lg p-2">
                        <div className="text-xs text-white font-medium">{goal.action}</div>
                        <div className="text-xs text-gray-500">{goal.timeline}</div>
                      </div>
                    ))}
                  </div>
                </div>

                <div>
                  <h4 className="font-semibold text-white mb-3 text-sm">Medium-term (60-90 days)</h4>
                  <div className="space-y-2">
                    {result.career_positioning_plan.skill_development_plan.medium_term_goals.slice(0, 2).map((goal, index) => (
                      <div key={index} className="bg-slate-700 border border-slate-700 rounded-lg p-2">
                        <div className="text-xs text-white font-medium">{goal.action}</div>
                        <div className="text-xs text-gray-500">{goal.timeline}</div>
                      </div>
                    ))}
                  </div>
                </div>

                <div>
                  <h4 className="font-semibold text-white mb-3 text-sm">Long-term (90+ days)</h4>
                  <div className="space-y-2">
                    {result.career_positioning_plan.skill_development_plan.long_term_goals.slice(0, 2).map((goal, index) => (
                      <div key={index} className="bg-slate-700 border border-slate-700 rounded-lg p-2">
                        <div className="text-xs text-white font-medium">{goal.action}</div>
                        <div className="text-xs text-gray-500">{goal.timeline}</div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'jobs' && (
          <div className="space-y-6">
            {result.job_matches.length === 0 ? (
              <div className="text-center py-12">
                <Briefcase className="w-16 h-16 text-gray-500 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-gray-500 mb-2">No Enhanced Job Matches</h3>
                <p className="text-gray-500 mb-4">
                  No job matches found with problem-solution alignment
                </p>
                {onUpgradePrompt && (
                  <button
                    onClick={onUpgradePrompt}
                    className="bg-violet-600 hover:bg-violet-700 text-white px-6 py-2 rounded-lg font-semibold transition-colors"
                  >
                    Upgrade for More Matches
                  </button>
                )}
              </div>
            ) : (
              <div className="space-y-4">
                {result.job_matches.map((match, index) => (
                  <div key={index} className="bg-slate-800 border border-slate-700 rounded-lg p-6 shadow-sm hover:shadow-md transition-shadow">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3 mb-2">
                          <h4 className="text-xl font-bold text-white">{match.job_opportunity.title}</h4>
                          <span className="px-3 py-1 rounded-full text-xs font-semibold bg-violet-100 text-blue-800">
                            Enhanced Match
                          </span>
                        </div>
                        <p className="text-gray-500 mb-2">{match.job_opportunity.company} • {match.job_opportunity.location}</p>
                        <div className="flex items-center space-x-6 text-sm text-gray-500">
                          <span>Salary: {formatSalary(match.job_opportunity.salary_min, match.job_opportunity.salary_max)}</span>
                          <span>Enhanced Score: <span className={getScoreColor(match.enhanced_score)}>{Math.round(match.enhanced_score)}/100</span></span>
                          <span>Alignment: <span className={getScoreColor(match.problem_solution_alignment)}>{Math.round(match.problem_solution_alignment)}/100</span></span>
                        </div>
                      </div>
                      <div className="flex space-x-2">
                        <button
                          onClick={() => setExpandedJob(expandedJob === match.job_opportunity.job_id ? null : match.job_opportunity.job_id)}
                          className="bg-slate-600 hover:bg-slate-500 text-gray-400 px-4 py-2 rounded-lg font-semibold transition-colors"
                        >
                          {expandedJob === match.job_opportunity.job_id ? 'Collapse' : 'Details'}
                        </button>
                        {onJobSelect && (
                          <button
                            onClick={() => onJobSelect(match)}
                            className="bg-violet-600 hover:bg-violet-700 text-white px-4 py-2 rounded-lg font-semibold transition-colors flex items-center space-x-2"
                          >
                            <ExternalLink className="w-4 h-4" />
                            <span>Apply</span>
                          </button>
                        )}
                      </div>
                    </div>

                    {expandedJob === match.job_opportunity.job_id && (
                      <div className="mt-6 space-y-6">
                        {/* Positioning Strategy */}
                        <div className="bg-slate-700 border border-slate-700 rounded-lg p-4">
                          <h5 className="font-semibold text-white mb-3 flex items-center space-x-2">
                            <div className="p-1 bg-purple-100 rounded">
                              <Brain className="w-4 h-4 text-purple-600" />
                            </div>
                            <span>Positioning Strategy</span>
                          </h5>
                          <div className="space-y-3">
                            <div>
                              <h6 className="text-sm font-medium text-gray-400 mb-1">Problem Focus</h6>
                              <p className="text-gray-500 text-sm">{match.positioning_strategy.problem_focus}</p>
                            </div>
                            <div>
                              <h6 className="text-sm font-medium text-gray-400 mb-1">Value Proposition</h6>
                              <p className="text-gray-500 text-sm">{match.positioning_strategy.value_proposition}</p>
                            </div>
                            <div>
                              <h6 className="text-sm font-medium text-gray-400 mb-1">Key Skills to Highlight</h6>
                              <div className="flex flex-wrap gap-2">
                                {match.positioning_strategy.key_skills_to_highlight.slice(0, 5).map((skill, skillIndex) => (
                                  <span key={skillIndex} className="px-2 py-1 bg-violet-100 text-blue-800 text-xs rounded-full">
                                    {skill}
                                  </span>
                                ))}
                              </div>
                            </div>
                          </div>
                        </div>

                        {/* Application Insights */}
                        <div className="bg-slate-700 border border-slate-700 rounded-lg p-4">
                          <h5 className="font-semibold text-white mb-3 flex items-center space-x-2">
                            <div className="p-1 bg-green-100 rounded">
                              <TrendingUp className="w-4 h-4 text-green-400" />
                            </div>
                            <span>Application Insights</span>
                          </h5>
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                              <div className="flex items-center justify-between mb-2">
                                <span className="text-sm text-gray-400">Application Strength</span>
                                <span className={`text-lg font-bold ${getScoreColor(match.application_insights.application_strength)}`}>
                                  {match.application_insights.application_strength}%
                                </span>
                              </div>
                              <div className="w-full bg-slate-500 rounded-full h-2">
                                <div 
                                  className="bg-gradient-to-r from-green-400 to-green-500 h-2 rounded-full"
                                  style={{ width: `${match.application_insights.application_strength}%` }}
                                ></div>
                              </div>
                            </div>
                            <div>
                              <div className="text-sm text-gray-400 mb-2">Skill Gaps ({match.application_insights.skill_gaps.length})</div>
                              <div className="space-y-1">
                                {match.application_insights.skill_gaps.slice(0, 3).map((gap, gapIndex) => (
                                  <div key={gapIndex} className="flex items-center justify-between text-xs">
                                    <span className="text-gray-500">{gap.skill}</span>
                                    <span className={`px-2 py-1 rounded-full text-xs ${getPriorityColor(gap.priority)}`}>
                                      {gap.priority}
                                    </span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          </div>
                        </div>

                        {/* Immediate Actions */}
                        <div className="bg-slate-700 border border-slate-700 rounded-lg p-4">
                          <h5 className="font-semibold text-white mb-3 flex items-center space-x-2">
                            <div className="p-1 bg-violet-100 rounded">
                              <CheckCircle className="w-4 h-4 text-violet-600" />
                            </div>
                            <span>Immediate Actions</span>
                          </h5>
                          <ul className="space-y-2">
                            {match.application_insights.immediate_actions.slice(0, 3).map((action, actionIndex) => (
                              <li key={actionIndex} className="flex items-center space-x-2 text-sm text-gray-400">
                                <ArrowRight className="w-3 h-3 text-violet-600" />
                                <span>{action}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default EnhancedJobMatchingResults;
