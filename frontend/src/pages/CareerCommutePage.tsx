import React, { useState, useEffect } from 'react';
import { 
  Briefcase, 
  Car, 
  Calculator, 
  TrendingUp, 
  Target,
  AlertCircle,
  Loader2
} from 'lucide-react';
import CareerCommuteIntegration from '../components/CareerCommuteIntegration';
import { useAnalytics } from '../hooks/useAnalytics';

// Types
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

interface Vehicle {
  id: string;
  make: string;
  model: string;
  year: number;
  mpg: number;
  fuelType: 'gasoline' | 'electric' | 'hybrid';
  currentMileage: number;
  monthlyMiles: number;
}

interface CommuteScenario {
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

const CareerCommutePage: React.FC = () => {
  const { trackInteraction, trackError } = useAnalytics();
  
  // State management
  const [jobRecommendations, setJobRecommendations] = useState<JobRecommendation[]>([]);
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load data on mount
  useEffect(() => {
    loadPageData();
  }, []);

  const loadPageData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Load job recommendations and vehicles in parallel
      const [jobsResponse, vehiclesResponse] = await Promise.all([
        fetch('/api/job-recommendations', {
          headers: {
            'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || ''
          }
        }),
        fetch('/api/commute/vehicles', {
          headers: {
            'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || ''
          }
        })
      ]);

      if (!jobsResponse.ok || !vehiclesResponse.ok) {
        throw new Error('Failed to load data');
      }

      const [jobsData, vehiclesData] = await Promise.all([
        jobsResponse.json(),
        vehiclesResponse.json()
      ]);

      setJobRecommendations(jobsData.recommendations || []);
      setVehicles(vehiclesData.vehicles || []);

      await trackInteraction('career_commute_page_loaded', {
        job_count: jobsData.recommendations?.length || 0,
        vehicle_count: vehiclesData.vehicles?.length || 0
      });

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load page data');
      await trackError(err as Error, { context: 'career_commute_page_load' });
    } finally {
      setLoading(false);
    }
  };

  const handleSaveScenario = async (scenario: CommuteScenario) => {
    try {
      await trackInteraction('commute_scenario_saved', {
        scenario_id: scenario.id,
        job_company: scenario.name.split(' - ')[0]
      });
    } catch (err) {
      await trackError(err as Error, { context: 'save_commute_scenario' });
    }
  };

  const handleLoadScenario = async (scenarioId: string) => {
    try {
      await trackInteraction('commute_scenario_loaded', { scenario_id: scenarioId });
    } catch (err) {
      await trackError(err as Error, { context: 'load_commute_scenario' });
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-violet-400 animate-spin mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-white mb-2">Loading Career Analysis</h2>
          <p className="text-gray-400">Preparing your commute cost calculations...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center max-w-md mx-auto">
          <AlertCircle className="w-16 h-16 text-red-400 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-white mb-2">Unable to Load Data</h2>
          <p className="text-gray-400 mb-6">{error}</p>
          <button
            onClick={loadPageData}
            className="bg-violet-600 hover:bg-violet-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors duration-200"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900">
      {/* Header */}
      <div className="bg-gradient-to-r from-violet-600 to-purple-600 text-white">
        <div className="container mx-auto px-6 py-12">
          <div className="flex items-center space-x-4 mb-6">
            <div className="bg-violet-500 bg-opacity-20 p-3 rounded-lg">
              <Calculator className="w-8 h-8" />
            </div>
            <div>
              <h1 className="text-3xl font-bold">Career + Commute Analysis</h1>
              <p className="text-violet-100 text-lg">
                Evaluate job opportunities with true compensation including transportation costs
              </p>
            </div>
          </div>

          {/* Quick Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-violet-500 bg-opacity-20 rounded-lg p-4">
              <div className="flex items-center space-x-3">
                <Briefcase className="w-6 h-6 text-violet-200" />
                <div>
                  <div className="text-2xl font-bold text-white">
                    {jobRecommendations.length}
                  </div>
                  <div className="text-violet-200 text-sm">Job Opportunities</div>
                </div>
              </div>
            </div>
            <div className="bg-violet-500 bg-opacity-20 rounded-lg p-4">
              <div className="flex items-center space-x-3">
                <Car className="w-6 h-6 text-violet-200" />
                <div>
                  <div className="text-2xl font-bold text-white">
                    {vehicles.length}
                  </div>
                  <div className="text-violet-200 text-sm">Vehicles Available</div>
                </div>
              </div>
            </div>
            <div className="bg-violet-500 bg-opacity-20 rounded-lg p-4">
              <div className="flex items-center space-x-3">
                <TrendingUp className="w-6 h-6 text-violet-200" />
                <div>
                  <div className="text-2xl font-bold text-white">
                    {jobRecommendations.reduce((sum, job) => sum + job.salary_increase_potential, 0) / jobRecommendations.length * 100 || 0}%
                  </div>
                  <div className="text-violet-200 text-sm">Avg. Salary Increase</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-6 py-8">
        {jobRecommendations.length === 0 ? (
          <div className="text-center py-12">
            <Target className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-white mb-2">No Job Recommendations</h3>
            <p className="text-gray-400 mb-6">
              Complete your career assessment to get personalized job recommendations.
            </p>
            <button className="bg-violet-600 hover:bg-violet-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors duration-200">
              Take Career Assessment
            </button>
          </div>
        ) : vehicles.length === 0 ? (
          <div className="text-center py-12">
            <Car className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-white mb-2">No Vehicles Added</h3>
            <p className="text-gray-400 mb-6">
              Add your vehicles to calculate accurate commute costs.
            </p>
            <button className="bg-violet-600 hover:bg-violet-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors duration-200">
              Add Vehicle
            </button>
          </div>
        ) : (
          <CareerCommuteIntegration
            jobRecommendations={jobRecommendations}
            vehicles={vehicles}
            onSaveScenario={handleSaveScenario}
            onLoadScenario={handleLoadScenario}
          />
        )}
      </div>
    </div>
  );
};

export default CareerCommutePage;
