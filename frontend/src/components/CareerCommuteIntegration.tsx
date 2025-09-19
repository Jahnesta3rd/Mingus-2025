import React, { useState, useEffect, useCallback } from 'react';
import { 
  Briefcase, 
  MapPin, 
  Calculator, 
  TrendingUp, 
  Target,
  AlertCircle,
  Loader2,
  Plus,
  Save,
  BarChart3
} from 'lucide-react';
import CommuteCostCalculator from './CommuteCostCalculator';
import { useAnalytics } from '../hooks/useAnalytics';

// Types
export interface JobRecommendation {
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

export interface Vehicle {
  id: string;
  make: string;
  model: string;
  year: number;
  mpg: number;
  fuelType: 'gasoline' | 'electric' | 'hybrid';
  currentMileage: number;
  monthlyMiles: number;
}

export interface CommuteScenario {
  id: string;
  name: string;
  jobLocation: {
    address: string;
    coordinates?: {
      lat: number;
      lng: number;
    };
  };
  homeLocation: {
    address: string;
    coordinates?: {
      lat: number;
      lng: number;
    };
  };
  vehicle: {
    id: string;
    make: string;
    model: string;
    year: number;
    mpg: number;
    fuelType: 'gasoline' | 'electric' | 'hybrid';
  };
  commuteDetails: {
    distance: number;
    duration: number;
    frequency: 'daily' | 'weekly' | 'monthly';
    daysPerWeek: number;
  };
  costs: {
    fuel: number;
    maintenance: number;
    depreciation: number;
    insurance: number;
    parking: number;
    tolls: number;
    total: number;
  };
  createdAt: string;
  updatedAt: string;
}

interface CareerCommuteIntegrationProps {
  jobRecommendations: JobRecommendation[];
  vehicles: Vehicle[];
  onSaveScenario: (scenario: CommuteScenario) => void;
  onLoadScenario: (scenarioId: string) => void;
  className?: string;
}

const CareerCommuteIntegration: React.FC<CareerCommuteIntegrationProps> = ({
  jobRecommendations,
  vehicles,
  onSaveScenario,
  onLoadScenario,
  className = ''
}) => {
  const { trackInteraction, trackError } = useAnalytics();
  
  // State management
  const [selectedJob, setSelectedJob] = useState<JobRecommendation | null>(null);
  const [showCommuteCalculator, setShowCommuteCalculator] = useState(false);
  const [savedScenarios, setSavedScenarios] = useState<CommuteScenario[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load saved scenarios on mount
  useEffect(() => {
    loadSavedScenarios();
  }, []);

  const loadSavedScenarios = async () => {
    try {
      const response = await fetch('/api/commute/scenarios', {
        headers: {
          'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || ''
        }
      });

      if (response.ok) {
        const data = await response.json();
        setSavedScenarios(data.scenarios || []);
      }
    } catch (err) {
      console.error('Failed to load saved scenarios:', err);
    }
  };

  const handleJobSelect = useCallback((job: JobRecommendation) => {
    setSelectedJob(job);
    setShowCommuteCalculator(true);
    trackInteraction('job_selected_for_commute', {
      job_id: job.job.job_id,
      company: job.job.company,
      salary: job.job.salary_median
    });
  }, [trackInteraction]);

  const handleSaveScenario = useCallback(async (scenario: CommuteScenario) => {
    try {
      setSavedScenarios(prev => [...prev, scenario]);
      onSaveScenario(scenario);
      await trackInteraction('commute_scenario_saved', {
        scenario_id: scenario.id,
        job_company: selectedJob?.job.company
      });
    } catch (err) {
      setError('Failed to save commute scenario');
      await trackError(err as Error, { context: 'save_commute_scenario' });
    }
  }, [selectedJob, onSaveScenario, trackInteraction, trackError]);

  const handleLoadScenario = useCallback(async (scenarioId: string) => {
    try {
      onLoadScenario(scenarioId);
      await trackInteraction('commute_scenario_loaded', { scenario_id: scenarioId });
    } catch (err) {
      setError('Failed to load commute scenario');
      await trackError(err as Error, { context: 'load_commute_scenario' });
    }
  }, [onLoadScenario, trackInteraction, trackError]);

  const getTierColor = (tier: string) => {
    switch (tier) {
      case 'conservative':
        return 'from-green-600 to-emerald-600';
      case 'optimal':
        return 'from-violet-600 to-purple-600';
      case 'stretch':
        return 'from-orange-600 to-red-600';
      default:
        return 'from-gray-600 to-gray-700';
    }
  };

  const getTierLabel = (tier: string) => {
    switch (tier) {
      case 'conservative':
        return 'Conservative';
      case 'optimal':
        return 'Optimal';
      case 'stretch':
        return 'Stretch';
      default:
        return 'Unknown';
    }
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="bg-gray-900 rounded-xl p-6">
        <div className="flex items-center space-x-3 mb-4">
          <div className="text-violet-400">
            <Calculator className="w-8 h-8" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-white">Career + Commute Analysis</h2>
            <p className="text-gray-400">
              Evaluate job opportunities with true compensation including transportation costs
            </p>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-gray-800 rounded-lg p-4">
            <div className="text-2xl font-bold text-violet-400">
              {jobRecommendations.length}
            </div>
            <div className="text-sm text-gray-400">Job Opportunities</div>
          </div>
          <div className="bg-gray-800 rounded-lg p-4">
            <div className="text-2xl font-bold text-green-400">
              {vehicles.length}
            </div>
            <div className="text-sm text-gray-400">Vehicles Available</div>
          </div>
          <div className="bg-gray-800 rounded-lg p-4">
            <div className="text-2xl font-bold text-orange-400">
              {savedScenarios.length}
            </div>
            <div className="text-sm text-gray-400">Saved Scenarios</div>
          </div>
        </div>
      </div>

      {/* Job Recommendations with Commute Analysis */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-white">Job Opportunities</h3>
        {jobRecommendations.map((job) => (
          <div
            key={job.job.job_id}
            className="bg-gray-900 rounded-xl p-6 border border-gray-800 hover:border-gray-700 transition-all duration-200"
          >
            <div className="flex items-start justify-between mb-4">
              <div className="flex-1">
                <div className="flex items-center space-x-3 mb-2">
                  <h4 className="text-xl font-bold text-white">{job.job.title}</h4>
                  <span className={`px-3 py-1 rounded-full text-xs font-semibold bg-gradient-to-r ${getTierColor(job.tier)} text-white`}>
                    {getTierLabel(job.tier)}
                  </span>
                </div>
                <p className="text-gray-400 mb-2">{job.job.company} • {job.job.location}</p>
                <div className="flex items-center space-x-4 text-sm text-gray-400">
                  <span>Salary: ${job.job.salary_median.toLocaleString()}</span>
                  <span>Success: {Math.round(job.success_probability * 100)}%</span>
                  <span>Increase: +{Math.round(job.salary_increase_potential * 100)}%</span>
                </div>
              </div>
              <button
                onClick={() => handleJobSelect(job)}
                className="flex items-center space-x-2 bg-violet-600 hover:bg-violet-700 text-white px-4 py-2 rounded-lg font-semibold transition-colors duration-200"
              >
                <Calculator className="w-4 h-4" />
                <span>Analyze Commute</span>
              </button>
            </div>

            {/* Job Details */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
              <div className="bg-gray-800 rounded-lg p-3">
                <div className="text-sm text-gray-400">Diversity Score</div>
                <div className="text-lg font-semibold text-white">
                  {Math.round(job.diversity_analysis.diversity_score * 100)}%
                </div>
              </div>
              <div className="bg-gray-800 rounded-lg p-3">
                <div className="text-sm text-gray-400">Growth Potential</div>
                <div className="text-lg font-semibold text-white">
                  {Math.round(job.career_advancement_potential * 100)}%
                </div>
              </div>
              <div className="bg-gray-800 rounded-lg p-3">
                <div className="text-sm text-gray-400">Culture Fit</div>
                <div className="text-lg font-semibold text-white">
                  {Math.round(job.company_culture_fit * 100)}%
                </div>
              </div>
              <div className="bg-gray-800 rounded-lg p-3">
                <div className="text-sm text-gray-400">Remote Friendly</div>
                <div className="text-lg font-semibold text-white">
                  {job.job.remote_friendly ? 'Yes' : 'No'}
                </div>
              </div>
            </div>

            {/* Benefits */}
            {job.job.benefits.length > 0 && (
              <div className="mb-4">
                <h5 className="text-sm font-medium text-gray-400 mb-2">Benefits</h5>
                <div className="flex flex-wrap gap-2">
                  {job.job.benefits.slice(0, 5).map((benefit, index) => (
                    <span
                      key={index}
                      className="px-2 py-1 bg-violet-500 bg-opacity-20 text-violet-300 rounded text-xs"
                    >
                      {benefit}
                    </span>
                  ))}
                  {job.job.benefits.length > 5 && (
                    <span className="px-2 py-1 bg-gray-700 text-gray-300 rounded text-xs">
                      +{job.job.benefits.length - 5} more
                    </span>
                  )}
                </div>
              </div>
            )}

            {/* Skills Gap Analysis */}
            {job.skills_gap_analysis.length > 0 && (
              <div className="mb-4">
                <h5 className="text-sm font-medium text-gray-400 mb-2">Key Skills Needed</h5>
                <div className="space-y-2">
                  {job.skills_gap_analysis.slice(0, 3).map((skill, index) => (
                    <div key={index} className="flex items-center justify-between">
                      <span className="text-sm text-white">{skill.skill}</span>
                      <div className="flex items-center space-x-2">
                        <div className="w-20 bg-gray-700 rounded-full h-2">
                          <div
                            className="bg-violet-500 h-2 rounded-full"
                            style={{ width: `${(skill.current_level / skill.required_level) * 100}%` }}
                          />
                        </div>
                        <span className="text-xs text-gray-400">
                          {skill.current_level}/{skill.required_level}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Commute Cost Calculator Modal */}
      {showCommuteCalculator && selectedJob && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-gray-900 rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden">
            {/* Modal Header */}
            <div className="bg-gradient-to-r from-violet-600 to-purple-600 p-6 text-white">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-xl font-bold">Commute Cost Analysis</h3>
                  <p className="text-violet-100">
                    {selectedJob.job.title} at {selectedJob.job.company}
                  </p>
                </div>
                <button
                  onClick={() => setShowCommuteCalculator(false)}
                  className="text-violet-200 hover:text-white transition-colors duration-200"
                >
                  <AlertCircle className="w-6 h-6" />
                </button>
              </div>
            </div>

            {/* Modal Content */}
            <div className="p-6 overflow-y-auto max-h-[calc(90vh-200px)]">
              <CommuteCostCalculator
                jobOffer={{
                  id: selectedJob.job.job_id,
                  title: selectedJob.job.title,
                  company: selectedJob.job.company,
                  location: selectedJob.job.location,
                  salary: {
                    min: selectedJob.job.salary_min,
                    max: selectedJob.job.salary_max,
                    median: selectedJob.job.salary_median
                  },
                  benefits: selectedJob.job.benefits,
                  remoteFriendly: selectedJob.job.remote_friendly
                }}
                vehicles={vehicles}
                onSaveScenario={handleSaveScenario}
                onLoadScenario={handleLoadScenario}
              />
            </div>
          </div>
        </div>
      )}

      {/* Saved Scenarios Summary */}
      {savedScenarios.length > 0 && (
        <div className="bg-gray-900 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Saved Commute Scenarios</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {savedScenarios.map((scenario) => (
              <div
                key={scenario.id}
                className="bg-gray-800 rounded-lg p-4 hover:bg-gray-700 transition-colors duration-200"
              >
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-semibold text-white text-sm">{scenario.name}</h4>
                  <button
                    onClick={() => handleLoadScenario(scenario.id)}
                    className="text-violet-400 hover:text-violet-300 text-xs"
                  >
                    Load
                  </button>
                </div>
                <div className="text-xs text-gray-400 space-y-1">
                  <div>{scenario.jobLocation.address}</div>
                  <div>→ {scenario.homeLocation.address}</div>
                  <div className="flex justify-between">
                    <span>${scenario.costs.total.toFixed(2)}/week</span>
                    <span>{scenario.commuteDetails.distance.toFixed(1)} mi</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="bg-red-500 bg-opacity-10 border border-red-500 text-red-300 px-4 py-3 rounded-lg flex items-center">
          <AlertCircle className="w-5 h-5 mr-2" />
          {error}
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center py-8">
          <Loader2 className="w-8 h-8 text-violet-400 animate-spin" />
          <span className="ml-3 text-gray-400">Loading commute analysis...</span>
        </div>
      )}
    </div>
  );
};

export default CareerCommuteIntegration;
