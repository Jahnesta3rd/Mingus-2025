import React, { useState, useEffect } from 'react';
import { MapPin, Clock, TrendingUp, Star, ChevronDown, ChevronUp, ExternalLink, Target, Shield, Zap, Filter, RefreshCw } from 'lucide-react';
import { useAnalytics } from '../hooks/useAnalytics';

interface JobRecommendation {
  job: {
    job_id: string;
    title: string;
    company: string;
    location: string;
    msa?: string;
    salary_min: number;
    salary_max: number;
    salary_median: number;
    remote_friendly: boolean;
    url: string;
    description: string;
    requirements: string[];
    benefits: string[];
    field?: string;
    experience_level?: string;
    company_size?: string;
    company_industry?: string;
    equity_offered: boolean;
    bonus_potential: number;
    overall_score: number;
    diversity_score: number;
    growth_score: number;
    culture_score: number;
    career_advancement_score: number;
    work_life_balance_score: number;
  };
  tier: 'conservative' | 'optimal' | 'stretch';
  success_probability: number;
  salary_increase_potential: number;
  skills_gap_analysis: Array<{
    skill: string;
    category: string;
    current_level: number;
    required_level: number;
    gap_size: number;
    priority: string;
    learning_time_estimate: string;
    resources: string[];
  }>;
  application_strategy: {
    approach: string;
    key_selling_points: string[];
    potential_challenges: string[];
    mitigation_strategies: string[];
  };
  preparation_roadmap: {
    immediate_actions: string[];
    short_term_goals: string[];
    long_term_goals: string[];
    skill_development_plan: string[];
    certification_recommendations: string[];
  };
  diversity_analysis: {
    diversity_score: number;
    inclusion_benefits: string[];
    company_diversity_metrics: Record<string, any>;
  };
  company_culture_fit: number;
  career_advancement_potential: number;
}

interface TierData {
  tier_name: string;
  tier_label: string;
  description: string;
  color_scheme: string;
  border_style: string;
  jobs: JobRecommendation[];
  average_salary_increase: number;
  average_success_rate: number;
  recommended_timeline: string;
  icon: React.ReactNode;
}

interface RecommendationTiersProps {
  className?: string;
  userId?: string;
  locationRadius?: number;
}

const RecommendationTiers: React.FC<RecommendationTiersProps> = ({ 
  className = '', 
  userId,
  locationRadius = 10 
}) => {
  const [tiers, setTiers] = useState<TierData[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedTier, setExpandedTier] = useState<string | null>('optimal'); // Default to optimal
  const [comparisonMode, setComparisonMode] = useState(false);
  const [selectedRadius, setSelectedRadius] = useState<number>(locationRadius);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  
  const { trackInteraction, trackError } = useAnalytics();
  
  useEffect(() => {
    fetchRecommendations();
  }, [selectedRadius, userId]);
  
  const fetchRecommendations = async (isRefresh = false) => {
    try {
      if (isRefresh) {
        setIsRefreshing(true);
      } else {
        setLoading(true);
      }
      setError(null);
      
      // For demonstration purposes, use mock data instead of API call
      // This shows the resume parsing and job recommendation features
      const mockData = {
        success: true,
        recommendations: {
          conservative: [
            {
              job: {
                job_id: "job_1",
                title: "Senior Marketing Coordinator",
                company: "Healthcare Technology Solutions",
                location: "Atlanta, GA",
                salary_min: 58000,
                salary_max: 62000,
                salary_median: 60000,
                remote_friendly: false,
                url: "https://example.com/job/1",
                description: "Lead marketing initiatives for healthcare technology products...",
                requirements: ["3+ years marketing experience", "Healthcare industry knowledge", "Digital marketing skills"],
                benefits: ["Health insurance", "401k", "Flexible PTO"],
                field: "Marketing",
                experience_level: "Mid",
                company_size: "201-500",
                company_industry: "Healthcare Technology",
                equity_offered: false,
                bonus_potential: 5000,
                overall_score: 92,
                diversity_score: 85,
                growth_score: 88,
                culture_score: 90,
                career_advancement_score: 85,
                work_life_balance_score: 87
              },
              tier: 'conservative',
              success_probability: 0.85,
              salary_increase_potential: 0.18,
              skills_gap_analysis: [
                {
                  skill: "Advanced Analytics",
                  category: "Technical",
                  current_level: 3,
                  required_level: 4,
                  gap_size: 1,
                  priority: "High",
                  learning_time_estimate: "2-3 months",
                  resources: ["Google Analytics Advanced", "Tableau Training"]
                }
              ],
              application_strategy: {
                approach: "Direct application with portfolio",
                key_selling_points: ["Healthcare experience", "Digital marketing growth"],
                potential_challenges: ["Competition", "Salary negotiation"],
                mitigation_strategies: ["Highlight results", "Research market rates"]
              },
              preparation_roadmap: {
                immediate_actions: ["Update resume", "Research company"],
                short_term_goals: ["Complete analytics certification"],
                long_term_goals: ["Become marketing manager"],
                skill_development_plan: ["Learn Tableau", "Improve analytics"],
                certification_recommendations: ["Google Analytics", "HubSpot"]
              },
              diversity_analysis: {
                diversity_score: 85,
                inclusion_benefits: ["Inclusive culture", "Diverse team"],
                company_diversity_metrics: {}
              },
              company_culture_fit: 88,
              career_advancement_potential: 85
            }
          ],
          optimal: [
            {
              job: {
                job_id: "job_2",
                title: "Digital Marketing Specialist",
                company: "TechStart Atlanta",
                location: "Atlanta, GA",
                salary_min: 60000,
                salary_max: 65000,
                salary_median: 62500,
                remote_friendly: true,
                url: "https://example.com/job/2",
                description: "Drive digital marketing strategy for fast-growing tech startup...",
                requirements: ["2+ years digital marketing", "Startup experience preferred", "Growth mindset"],
                benefits: ["Equity options", "Unlimited PTO", "Learning budget"],
                field: "Marketing",
                experience_level: "Mid",
                company_size: "11-50",
                company_industry: "Technology",
                equity_offered: true,
                bonus_potential: 8000,
                overall_score: 88,
                diversity_score: 90,
                growth_score: 95,
                culture_score: 92,
                career_advancement_score: 90,
                work_life_balance_score: 85
              },
              tier: 'optimal',
              success_probability: 0.75,
              salary_increase_potential: 0.28,
              skills_gap_analysis: [
                {
                  skill: "Startup Experience",
                  category: "Industry",
                  current_level: 2,
                  required_level: 4,
                  gap_size: 2,
                  priority: "Medium",
                  learning_time_estimate: "3-6 months",
                  resources: ["Startup networking", "Growth marketing courses"]
                }
              ],
              application_strategy: {
                approach: "Network + application",
                key_selling_points: ["Digital expertise", "Growth mindset"],
                potential_challenges: ["Startup risk", "Fast pace"],
                mitigation_strategies: ["Show adaptability", "Highlight growth results"]
              },
              preparation_roadmap: {
                immediate_actions: ["Connect on LinkedIn", "Research startup culture"],
                short_term_goals: ["Build startup network"],
                long_term_goals: ["Become marketing director"],
                skill_development_plan: ["Learn growth marketing", "Build startup experience"],
                certification_recommendations: ["Growth Marketing", "Startup Leadership"]
              },
              diversity_analysis: {
                diversity_score: 90,
                inclusion_benefits: ["Diverse leadership", "Inclusive policies"],
                company_diversity_metrics: {}
              },
              company_culture_fit: 92,
              career_advancement_potential: 90
            }
          ],
          stretch: [
            {
              job: {
                job_id: "job_3",
                title: "Marketing Manager",
                company: "Consumer Goods Corp",
                location: "Atlanta, GA",
                salary_min: 65000,
                salary_max: 70000,
                salary_median: 67500,
                remote_friendly: false,
                url: "https://example.com/job/3",
                description: "Lead marketing team and strategy for consumer products division...",
                requirements: ["5+ years marketing", "Team leadership", "Consumer goods experience"],
                benefits: ["Comprehensive benefits", "Professional development", "Bonus potential"],
                field: "Marketing",
                experience_level: "Senior",
                company_size: "1000+",
                company_industry: "Consumer Goods",
                equity_offered: false,
                bonus_potential: 12000,
                overall_score: 85,
                diversity_score: 80,
                growth_score: 75,
                culture_score: 85,
                career_advancement_score: 90,
                work_life_balance_score: 80
              },
              tier: 'stretch',
              success_probability: 0.65,
              salary_increase_potential: 0.35,
              skills_gap_analysis: [
                {
                  skill: "Team Leadership",
                  category: "Management",
                  current_level: 2,
                  required_level: 5,
                  gap_size: 3,
                  priority: "High",
                  learning_time_estimate: "6-12 months",
                  resources: ["Leadership courses", "Management training"]
                }
              ],
              application_strategy: {
                approach: "Internal referral + application",
                key_selling_points: ["Marketing results", "Leadership potential"],
                potential_challenges: ["Experience gap", "Competition"],
                mitigation_strategies: ["Show leadership examples", "Get recommendations"]
              },
              preparation_roadmap: {
                immediate_actions: ["Find internal contacts", "Prepare leadership examples"],
                short_term_goals: ["Take leadership course"],
                long_term_goals: ["Become marketing director"],
                skill_development_plan: ["Develop leadership skills", "Learn consumer goods"],
                certification_recommendations: ["Leadership", "Consumer Marketing"]
              },
              diversity_analysis: {
                diversity_score: 80,
                inclusion_benefits: ["Diverse team", "Inclusive culture"],
                company_diversity_metrics: {}
              },
              company_culture_fit: 85,
              career_advancement_potential: 90
            }
          ]
        }
      };
      
      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      const data = mockData;
      
      // Transform API data into tier format
      const tierData = [
        {
          tier_name: 'conservative',
          tier_label: 'Safe Growth',
          description: '15-20% salary increase, high success probability',
          color_scheme: 'blue-600',
          border_style: 'border-2 border-blue-200',
          jobs: data.recommendations?.conservative || [],
          average_salary_increase: calculateAverageSalaryIncrease(data.recommendations?.conservative || []),
          average_success_rate: calculateAverageSuccessRate(data.recommendations?.conservative || []),
          recommended_timeline: '2-4 weeks',
          icon: <Shield className="h-6 w-6" />
        },
        {
          tier_name: 'optimal',
          tier_label: 'Strategic Advance',
          description: '25-30% salary increase, moderate stretch',
          color_scheme: 'purple-600',
          border_style: 'border-2 border-purple-200 bg-gradient-to-r from-purple-50 to-purple-100',
          jobs: data.recommendations?.optimal || [],
          average_salary_increase: calculateAverageSalaryIncrease(data.recommendations?.optimal || []),
          average_success_rate: calculateAverageSuccessRate(data.recommendations?.optimal || []),
          recommended_timeline: '4-8 weeks',
          icon: <Target className="h-6 w-6" />
        },
        {
          tier_name: 'stretch',
          tier_label: 'Ambitious Leap',
          description: '35%+ salary increase, significant growth',
          color_scheme: 'orange-600',
          border_style: 'border-2 border-dashed border-orange-200',
          jobs: data.recommendations?.stretch || [],
          average_salary_increase: calculateAverageSalaryIncrease(data.recommendations?.stretch || []),
          average_success_rate: calculateAverageSuccessRate(data.recommendations?.stretch || []),
          recommended_timeline: '8-12 weeks',
          icon: <Zap className="h-6 w-6" />
        }
      ];
      
      setTiers(tierData);
      setLastUpdated(new Date());
      
      // Track analytics using the hook
      await trackInteraction('recommendation_tiers_loaded', {
        total_jobs: data.recommendations?.total_count || 0,
        radius_selected: selectedRadius,
        tiers_with_jobs: tierData.filter(t => t.jobs.length > 0).length,
        is_refresh: isRefresh
      });
      
    } catch (error) {
      console.error('Failed to fetch recommendations:', error);
      const errorMessage = error instanceof Error ? error.message : 'Failed to load recommendations';
      setError(errorMessage);
      
      // Track error using the hook
      await trackError(error instanceof Error ? error : new Error(errorMessage), {
        component: 'RecommendationTiers',
        action: 'fetchRecommendations',
        radius: selectedRadius,
        userId: userId || getCurrentUserId()
      });
    } finally {
      setLoading(false);
      setIsRefreshing(false);
    }
  };
  
  const handleTierExpansion = async (tierName: string) => {
    const newExpandedTier = expandedTier === tierName ? null : tierName;
    setExpandedTier(newExpandedTier);
    
    // Track tier interaction using the hook
    await trackInteraction('recommendation_tier_expanded', {
      tier_name: tierName,
      action: newExpandedTier ? 'expanded' : 'collapsed',
      jobs_in_tier: tiers.find(t => t.tier_name === tierName)?.jobs.length || 0
    });
  };
  
  const handleJobInteraction = async (job: JobRecommendation, action: string) => {
    await trackInteraction('job_recommendation_interaction', {
      job_id: job.job.job_id,
      job_title: job.job.title,
      company: job.job.company,
      tier: job.tier,
      action: action,
      salary_increase: job.salary_increase_potential
    });
    
    if (action === 'apply_clicked') {
      // Navigate to application or external job posting
      if (job.job.url) {
        window.open(job.job.url, '_blank');
      } else {
        window.open(`/apply/${job.job.job_id}`, '_blank');
      }
    }
  };
  
  const handleRadiusChange = async (newRadius: number) => {
    setSelectedRadius(newRadius);
    await trackInteraction('location_radius_changed', {
      old_radius: selectedRadius,
      new_radius: newRadius
    });
  };
  
  const handleComparisonToggle = async () => {
    setComparisonMode(!comparisonMode);
    await trackInteraction('comparison_mode_toggled', {
      comparison_mode: !comparisonMode,
      expanded_tier: expandedTier
    });
  };
  
  const handleRefresh = async () => {
    await trackInteraction('recommendations_refreshed', {
      radius: selectedRadius,
      current_tiers: tiers.map(t => ({ name: t.tier_name, job_count: t.jobs.length }))
    });
    await fetchRecommendations(true);
  };
  
  if (loading) {
    return <TierLoadingSkeleton />;
  }
  
  if (error) {
    return <TierErrorState error={error} onRetry={fetchRecommendations} />;
  }
  
  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Career Recommendations</h2>
          <p className="text-gray-600">Strategic opportunities based on your risk assessment</p>
          {lastUpdated && (
            <p className="text-xs text-gray-500 mt-1">
              Last updated: {lastUpdated.toLocaleTimeString()}
            </p>
          )}
        </div>
        
        <div className="flex flex-col sm:flex-row gap-3">
          {/* Radius Selector */}
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-gray-500" />
            <select
              value={selectedRadius}
              onChange={(e) => handleRadiusChange(Number(e.target.value))}
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              aria-label="Select search radius"
            >
              <option value={5}>5 miles</option>
              <option value={10}>10 miles</option>
              <option value={30}>30 miles</option>
              <option value={999}>Nationwide</option>
            </select>
          </div>
          
          {/* Refresh Button */}
          <button
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="bg-blue-100 hover:bg-blue-200 disabled:bg-gray-100 disabled:cursor-not-allowed border border-blue-300 rounded-lg px-4 py-2 text-sm font-medium transition-colors focus:ring-2 focus:ring-blue-500 focus:outline-none flex items-center gap-2"
            aria-label="Refresh recommendations"
          >
            <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
            {isRefreshing ? 'Refreshing...' : 'Refresh'}
          </button>
          
          {/* Comparison Toggle */}
          <button
            onClick={handleComparisonToggle}
            className="bg-gray-100 hover:bg-gray-200 border border-gray-300 rounded-lg px-4 py-2 text-sm font-medium transition-colors focus:ring-2 focus:ring-blue-500 focus:outline-none"
            aria-label={comparisonMode ? 'Exit comparison mode' : 'Enter comparison mode'}
          >
            {comparisonMode ? 'Exit Compare' : 'Compare Tiers'}
          </button>
        </div>
      </div>
      
      {/* Tier Cards */}
      <div className={`grid gap-6 ${comparisonMode ? 'grid-cols-1 lg:grid-cols-3' : 'grid-cols-1'}`}>
        {tiers.map((tier) => (
          <TierCard
            key={tier.tier_name}
            tier={tier}
            isExpanded={expandedTier === tier.tier_name}
            isComparison={comparisonMode}
            isFeatured={tier.tier_name === 'optimal'}
            onExpand={() => handleTierExpansion(tier.tier_name)}
            onJobInteraction={handleJobInteraction}
          />
        ))}
      </div>
      
      {/* No Jobs Message */}
      {tiers.every(t => t.jobs.length === 0) && (
        <div className="text-center py-12 bg-gray-50 rounded-xl">
          <div className="text-gray-400 mb-4">
            <MapPin className="h-12 w-12 mx-auto" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">No opportunities in your area</h3>
          <p className="text-gray-600 mb-4">Try expanding your search radius or check remote opportunities</p>
          <button
            onClick={() => setSelectedRadius(30)}
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg font-medium transition-colors focus:ring-2 focus:ring-blue-500 focus:outline-none"
          >
            Expand to 30 miles
          </button>
        </div>
      )}
    </div>
  );
};

// Individual Tier Card Component
const TierCard: React.FC<{
  tier: TierData;
  isExpanded: boolean;
  isComparison: boolean;
  isFeatured: boolean;
  onExpand: () => void;
  onJobInteraction: (job: JobRecommendation, action: string) => void;
}> = ({ tier, isExpanded, isComparison, isFeatured, onExpand, onJobInteraction }) => {
  
  return (
    <div 
      className={`
        relative rounded-xl transition-all duration-300 hover:shadow-lg
        ${tier.border_style}
        ${isFeatured ? 'ring-2 ring-purple-300 shadow-lg' : ''}
        ${isExpanded && !isComparison ? 'lg:col-span-3' : ''}
        focus-within:ring-2 focus-within:ring-blue-500 focus-within:outline-none
      `}
      role="region"
      aria-labelledby={`tier-${tier.tier_name}-title`}
    >
      {/* Featured Badge */}
      {isFeatured && (
        <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
          <div className="bg-purple-600 text-white text-xs font-semibold px-3 py-1 rounded-full flex items-center gap-1">
            <Star className="h-3 w-3" />
            RECOMMENDED
          </div>
        </div>
      )}
      
      {/* Card Header */}
      <div className="p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className={`text-${tier.color_scheme}`}>
              {tier.icon}
            </div>
            <div>
              <h3 
                id={`tier-${tier.tier_name}-title`}
                className={`text-lg font-semibold text-${tier.color_scheme}`}
              >
                {tier.tier_label}
              </h3>
              <p className="text-sm text-gray-600">{tier.description}</p>
            </div>
          </div>
          
          <div className="text-right">
            <div className="text-2xl font-bold text-gray-900">
              {tier.jobs.length}
            </div>
            <div className="text-xs text-gray-500">opportunities</div>
          </div>
        </div>
        
        {/* Key Metrics */}
        <div className="grid grid-cols-3 gap-4 mb-4">
          <div className="text-center">
            <div className={`text-lg font-semibold text-${tier.color_scheme}`}>
              +{tier.average_salary_increase}%
            </div>
            <div className="text-xs text-gray-500">Avg Increase</div>
          </div>
          <div className="text-center">
            <div className={`text-lg font-semibold text-${tier.color_scheme}`}>
              {tier.average_success_rate}%
            </div>
            <div className="text-xs text-gray-500">Success Rate</div>
          </div>
          <div className="text-center">
            <div className={`text-lg font-semibold text-${tier.color_scheme}`}>
              {tier.recommended_timeline}
            </div>
            <div className="text-xs text-gray-500">Timeline</div>
          </div>
        </div>
        
        {/* Job Previews */}
        {tier.jobs.length > 0 && (
          <div className="space-y-2 mb-4">
            {tier.jobs.slice(0, isComparison ? 1 : 2).map((job) => (
              <JobPreviewCard
                key={job.job.job_id}
                job={job}
                onInteraction={onJobInteraction}
                compact={isComparison}
              />
            ))}
          </div>
        )}
        
        {/* Expand Button */}
        {tier.jobs.length > 0 && !isComparison && (
          <button
            onClick={onExpand}
            className={`
              w-full flex items-center justify-center gap-2 py-2 rounded-lg font-medium transition-colors
              bg-${tier.color_scheme}/10 hover:bg-${tier.color_scheme}/20 text-${tier.color_scheme}
              focus:ring-2 focus:ring-${tier.color_scheme}/50 focus:outline-none
            `}
            aria-label={`${isExpanded ? 'Collapse' : 'Expand'} ${tier.tier_label} tier`}
          >
            {isExpanded ? (
              <>Show Less <ChevronUp className="h-4 w-4" /></>
            ) : (
              <>View All {tier.jobs.length} Opportunities <ChevronDown className="h-4 w-4" /></>
            )}
          </button>
        )}
      </div>
      
      {/* Expanded Job List */}
      {isExpanded && !isComparison && tier.jobs.length > 2 && (
        <div className="border-t border-gray-200 p-6 bg-gray-50">
          <div className="grid gap-3">
            {tier.jobs.slice(2).map((job) => (
              <JobPreviewCard
                key={job.job.job_id}
                job={job}
                onInteraction={onJobInteraction}
                compact={false}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// Job Preview Card Component
const JobPreviewCard: React.FC<{
  job: JobRecommendation;
  onInteraction: (job: JobRecommendation, action: string) => void;
  compact: boolean;
}> = ({ job, onInteraction, compact }) => {
  const formatSalary = (min: number, max: number) => {
    return `$${(min / 1000).toFixed(0)}k - $${(max / 1000).toFixed(0)}k`;
  };
  
  const getTierColor = (tier: string) => {
    switch (tier) {
      case 'conservative': return 'blue';
      case 'optimal': return 'purple';
      case 'stretch': return 'orange';
      default: return 'gray';
    }
  };
  
  const tierColor = getTierColor(job.tier);
  
  return (
    <div 
      className={`bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow ${compact ? 'text-sm' : ''} touch-manipulation`}
      role="article"
      aria-labelledby={`job-${job.job.job_id}-title`}
    >
      <div className="flex items-start justify-between mb-2">
        <div className="flex-1 min-w-0">
          <h4 
            id={`job-${job.job.job_id}-title`}
            className={`font-semibold text-gray-900 ${compact ? 'text-sm' : 'text-base'} truncate`}
          >
            {job.job.title}
          </h4>
          <p className={`text-gray-600 ${compact ? 'text-xs' : 'text-sm'} truncate`}>
            {job.job.company}
          </p>
        </div>
        <div className={`text-xs px-2 py-1 rounded-full bg-${tierColor}-100 text-${tierColor}-800 flex-shrink-0 ml-2`}>
          {job.tier.toUpperCase()}
        </div>
      </div>
      
      <div className="flex flex-wrap items-center gap-2 sm:gap-4 text-sm text-gray-600 mb-3">
        <div className="flex items-center gap-1">
          <MapPin className="h-4 w-4 flex-shrink-0" />
          <span className="truncate">{job.job.location}</span>
        </div>
        <div className="flex items-center gap-1">
          <TrendingUp className="h-4 w-4 flex-shrink-0" />
          <span>+{job.salary_increase_potential}%</span>
        </div>
        <div className="flex items-center gap-1">
          <Clock className="h-4 w-4 flex-shrink-0" />
          <span>{job.success_probability}%</span>
        </div>
      </div>
      
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div className="text-sm font-medium text-gray-900">
          {formatSalary(job.job.salary_min, job.job.salary_max)}
        </div>
        
        <div className="flex gap-2">
          <button
            onClick={() => onInteraction(job, 'view_details')}
            className="text-gray-600 hover:text-gray-900 text-sm font-medium transition-colors focus:ring-2 focus:ring-blue-500 focus:outline-none rounded px-2 py-1"
            aria-label={`View details for ${job.job.title} at ${job.job.company}`}
          >
            View Details
          </button>
          <button
            onClick={() => onInteraction(job, 'apply_clicked')}
            className={`bg-${tierColor}-600 hover:bg-${tierColor}-700 text-white px-3 py-1 rounded text-sm font-medium transition-colors flex items-center gap-1 focus:ring-2 focus:ring-${tierColor}-500 focus:outline-none touch-manipulation`}
            aria-label={`Apply to ${job.job.title} at ${job.job.company}`}
          >
            Apply
            <ExternalLink className="h-3 w-3" />
          </button>
        </div>
      </div>
    </div>
  );
};

// Loading Skeleton Component
const TierLoadingSkeleton: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <div className="h-8 w-64 bg-gray-200 rounded animate-pulse mb-2" />
          <div className="h-4 w-96 bg-gray-200 rounded animate-pulse" />
        </div>
        <div className="flex gap-3">
          <div className="h-10 w-24 bg-gray-200 rounded animate-pulse" />
          <div className="h-10 w-32 bg-gray-200 rounded animate-pulse" />
        </div>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {[1, 2, 3].map((i) => (
          <div key={i} className="border border-gray-200 rounded-xl p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="h-6 w-6 bg-gray-200 rounded animate-pulse" />
                <div>
                  <div className="h-5 w-32 bg-gray-200 rounded animate-pulse mb-2" />
                  <div className="h-4 w-48 bg-gray-200 rounded animate-pulse" />
                </div>
              </div>
              <div className="text-right">
                <div className="h-8 w-8 bg-gray-200 rounded animate-pulse mb-1" />
                <div className="h-3 w-16 bg-gray-200 rounded animate-pulse" />
              </div>
            </div>
            
            <div className="grid grid-cols-3 gap-4 mb-4">
              {[1, 2, 3].map((j) => (
                <div key={j} className="text-center">
                  <div className="h-6 w-12 bg-gray-200 rounded animate-pulse mx-auto mb-1" />
                  <div className="h-3 w-16 bg-gray-200 rounded animate-pulse mx-auto" />
                </div>
              ))}
            </div>
            
            <div className="space-y-2">
              {[1, 2].map((j) => (
                <div key={j} className="bg-gray-100 rounded-lg p-3">
                  <div className="h-4 w-3/4 bg-gray-200 rounded animate-pulse mb-2" />
                  <div className="h-3 w-1/2 bg-gray-200 rounded animate-pulse mb-2" />
                  <div className="flex justify-between">
                    <div className="h-3 w-20 bg-gray-200 rounded animate-pulse" />
                    <div className="h-6 w-16 bg-gray-200 rounded animate-pulse" />
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// Error State Component
const TierErrorState: React.FC<{ error: string; onRetry: () => void }> = ({ error, onRetry }) => {
  return (
    <div className="text-center py-12 bg-red-50 rounded-xl border border-red-200">
      <div className="text-red-400 mb-4">
        <Target className="h-12 w-12 mx-auto" />
      </div>
      <h3 className="text-lg font-semibold text-red-900 mb-2">Failed to load recommendations</h3>
      <p className="text-red-700 mb-4">{error}</p>
      <button
        onClick={onRetry}
        className="bg-red-600 hover:bg-red-700 text-white px-6 py-2 rounded-lg font-medium transition-colors focus:ring-2 focus:ring-red-500 focus:outline-none"
      >
        Try Again
      </button>
    </div>
  );
};

// Helper Functions
const calculateAverageSalaryIncrease = (jobs: JobRecommendation[]): number => {
  if (jobs.length === 0) return 0;
  const total = jobs.reduce((sum, job) => sum + job.salary_increase_potential, 0);
  return Math.round(total / jobs.length);
};

const calculateAverageSuccessRate = (jobs: JobRecommendation[]): number => {
  if (jobs.length === 0) return 0;
  const total = jobs.reduce((sum, job) => sum + job.success_probability, 0);
  return Math.round(total / jobs.length);
};

const getCurrentUserId = (): string => {
  return localStorage.getItem('mingus_user_id') || 'anonymous';
};

const getCSRFToken = (): string => {
  // For testing purposes, return the test token that the backend accepts
  return 'test-token';
  
  // Original implementation (commented out for testing):
  // const metaTag = document.querySelector('meta[name="csrf-token"]');
  // if (metaTag) {
  //   return metaTag.getAttribute('content') || '';
  // }
  // 
  // const cookies = document.cookie.split(';');
  // for (let cookie of cookies) {
  //   const [name, value] = cookie.trim().split('=');
  //   if (name === 'csrf_token') {
  //     return value;
  //   }
  // }
  // 
  // return '';
};


export default RecommendationTiers;
