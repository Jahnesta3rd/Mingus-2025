import React, { useState, useEffect, useCallback } from 'react';
import { 
  Calculator, 
  Car, 
  DollarSign, 
  MapPin, 
  TrendingUp, 
  Target, 
  BarChart3, 
  AlertCircle, 
  CheckCircle, 
  Loader2,
  Plus,
  Save,
  Download,
  ArrowRight,
  Clock,
  Fuel,
  Wrench,
  Shield,
  ParkingCircle,
  Route
} from 'lucide-react';
import { useAnalytics } from '../hooks/useAnalytics';

// Types
export interface JobOffer {
  id: string;
  title: string;
  company: string;
  location: string;
  salary: number;
  benefits: string[];
  remoteFriendly: boolean;
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

export interface JobCostAnalysis {
  jobOffer: JobOffer;
  commuteAnalysis: {
    distance_miles: number;
    work_days_per_month: number;
    daily_cost: number;
    monthly_cost: number;
    annual_cost: number;
    cost_breakdown: {
      fuel: { daily: number; monthly: number; annual: number };
      maintenance: { daily: number; monthly: number; annual: number };
      depreciation: { daily: number; monthly: number; annual: number };
      insurance: { daily: number; monthly: number; annual: number };
      parking: { daily: number; monthly: number; annual: number };
      tolls: { daily: number; monthly: number; annual: number };
    };
    cost_per_mile: number;
  };
  trueCompensation: {
    annual: number;
    monthly: number;
    break_even_salary: number;
    cost_percentage: number;
  };
  recommendations: string[];
}

export interface CommuteImpactAnalysis {
  jobLocation: {
    name: string;
    address: string;
    salary: number;
  };
  transportationOptions: {
    driving: any;
    public_transport?: any;
    carpooling?: any;
  };
  financialImpact: {
    annual_driving_cost: number;
    break_even_salary: number;
    cost_as_salary_percentage: number;
  };
  monthlyProjections: Array<{
    month: number;
    monthly_cost: number;
    cumulative_cost: number;
  }>;
  recommendations: string[];
}

interface CareerVehicleOptimizationProps {
  vehicles: Vehicle[];
  className?: string;
}

const CareerVehicleOptimization: React.FC<CareerVehicleOptimizationProps> = ({
  vehicles,
  className = ''
}) => {
  const { trackInteraction, trackError } = useAnalytics();
  
  // State management
  const [activeTab, setActiveTab] = useState<'job-cost' | 'commute-impact' | 'career-move' | 'budget-optimization'>('job-cost');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasAccess, setHasAccess] = useState(false);
  
  // Job Cost Analysis State
  const [jobOffers, setJobOffers] = useState<JobOffer[]>([]);
  const [homeAddress, setHomeAddress] = useState('');
  const [selectedVehicleId, setSelectedVehicleId] = useState<string>('');
  const [jobCostResults, setJobCostResults] = useState<JobCostAnalysis[]>([]);
  
  // Commute Impact Analysis State
  const [jobLocations, setJobLocations] = useState<Array<{name: string; address: string; salary: number}>>([]);
  const [commuteImpactResults, setCommuteImpactResults] = useState<CommuteImpactAnalysis[]>([]);
  
  // Career Move Planning State
  const [currentLocation, setCurrentLocation] = useState('');
  const [newJobLocation, setNewJobLocation] = useState('');
  const [newSalary, setNewSalary] = useState(0);
  const [movingDistance, setMovingDistance] = useState(0);
  
  // Budget Optimization State
  const [currentIncome, setCurrentIncome] = useState(0);
  const [currentCommuteCost, setCurrentCommuteCost] = useState(0);
  const [jobOpportunities, setJobOpportunities] = useState<Array<{title: string; location: string; salary: number; distance_miles: number}>>([]);

  // Check feature access on mount
  useEffect(() => {
    checkFeatureAccess();
  }, []);

  const checkFeatureAccess = async () => {
    try {
      const response = await fetch('/api/career-vehicle/feature-access', {
        headers: {
          'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || ''
        }
      });

      if (response.ok) {
        const data = await response.json();
        setHasAccess(data.has_access);
      }
    } catch (err) {
      console.error('Failed to check feature access:', err);
    }
  };

  const addJobOffer = () => {
    const newOffer: JobOffer = {
      id: `job_${Date.now()}`,
      title: '',
      company: '',
      location: '',
      salary: 0,
      benefits: [],
      remoteFriendly: false
    };
    setJobOffers([...jobOffers, newOffer]);
  };

  const updateJobOffer = (id: string, field: keyof JobOffer, value: any) => {
    setJobOffers(jobOffers.map(offer => 
      offer.id === id ? { ...offer, [field]: value } : offer
    ));
  };

  const removeJobOffer = (id: string) => {
    setJobOffers(jobOffers.filter(offer => offer.id !== id));
  };

  const calculateJobCosts = async () => {
    if (!homeAddress || !selectedVehicleId || jobOffers.length === 0) {
      setError('Please fill in all required fields');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/career-vehicle/job-cost-analysis', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || ''
        },
        body: JSON.stringify({
          job_offers: jobOffers,
          home_address: homeAddress,
          vehicle_id: selectedVehicleId,
          work_days_per_month: 22,
          include_parking: true,
          include_tolls: true
        })
      });

      if (response.ok) {
        const data = await response.json();
        setJobCostResults(data.analysis_results);
        await trackInteraction('job_cost_analysis_completed', {
          job_count: jobOffers.length,
          vehicle_id: selectedVehicleId
        });
      } else {
        const errorData = await response.json();
        if (errorData.upgrade_required) {
          setError('Career-vehicle optimization add-on required. Upgrade to access this feature.');
        } else {
          setError(errorData.error || 'Failed to calculate job costs');
        }
      }
    } catch (err) {
      setError('Failed to calculate job costs');
      await trackError(err as Error, { context: 'job_cost_analysis' });
    } finally {
      setLoading(false);
    }
  };

  const calculateCommuteImpact = async () => {
    if (!homeAddress || !selectedVehicleId || jobLocations.length === 0) {
      setError('Please fill in all required fields');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/career-vehicle/commute-impact-analysis', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || ''
        },
        body: JSON.stringify({
          job_locations: jobLocations,
          home_address: homeAddress,
          vehicle_id: selectedVehicleId,
          analysis_period_months: 12,
          include_public_transport: true,
          include_carpooling: true
        })
      });

      if (response.ok) {
        const data = await response.json();
        setCommuteImpactResults(data.impact_analysis);
        await trackInteraction('commute_impact_analysis_completed', {
          location_count: jobLocations.length,
          vehicle_id: selectedVehicleId
        });
      } else {
        const errorData = await response.json();
        if (errorData.upgrade_required) {
          setError('Career-vehicle optimization add-on required. Upgrade to access this feature.');
        } else {
          setError(errorData.error || 'Failed to analyze commute impact');
        }
      }
    } catch (err) {
      setError('Failed to analyze commute impact');
      await trackError(err as Error, { context: 'commute_impact_analysis' });
    } finally {
      setLoading(false);
    }
  };

  if (!hasAccess) {
    return (
      <div className={`bg-gray-900 rounded-xl shadow-2xl p-8 text-center ${className}`}>
        <div className="mb-6">
          <div className="text-violet-400 mb-4">
            <Calculator className="w-16 h-16 mx-auto" />
          </div>
          <h2 className="text-2xl font-bold text-white mb-2">Career-Vehicle Optimization</h2>
          <p className="text-gray-400 mb-6">
            Optimize your job opportunities and commute costs with our Budget tier add-on
          </p>
        </div>
        
        <div className="bg-gradient-to-r from-violet-600 to-purple-600 rounded-lg p-6 mb-6">
          <h3 className="text-xl font-semibold text-white mb-4">Add-on Features</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-left">
            <div className="flex items-center space-x-3">
              <CheckCircle className="w-5 h-5 text-green-300" />
              <span className="text-violet-100">Job Opportunity True Cost Calculator</span>
            </div>
            <div className="flex items-center space-x-3">
              <CheckCircle className="w-5 h-5 text-green-300" />
              <span className="text-violet-100">Commute Cost Impact Analysis</span>
            </div>
            <div className="flex items-center space-x-3">
              <CheckCircle className="w-5 h-5 text-green-300" />
              <span className="text-violet-100">Career Move Financial Planning</span>
            </div>
            <div className="flex items-center space-x-3">
              <CheckCircle className="w-5 h-5 text-green-300" />
              <span className="text-violet-100">Budget-Friendly Optimization</span>
            </div>
          </div>
        </div>
        
        <div className="bg-gray-800 rounded-lg p-6">
          <div className="text-center mb-4">
            <div className="text-3xl font-bold text-white">$7/month</div>
            <div className="text-gray-400">Add-on to Budget tier ($15 + $7 = $22 total)</div>
          </div>
          <button className="w-full bg-violet-600 hover:bg-violet-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors duration-200">
            Upgrade to Add Career-Vehicle Optimization
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-gray-900 rounded-xl shadow-2xl p-6 ${className}`}>
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center space-x-3 mb-2">
          <div className="text-violet-400">
            <Calculator className="w-8 h-8" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-white">Career-Vehicle Optimization</h2>
            <p className="text-gray-400">Optimize job opportunities and commute costs for budget-conscious users</p>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="mb-6">
        <div className="flex space-x-1 bg-gray-800 rounded-lg p-1">
          {[
            { id: 'job-cost', label: 'Job Cost Analysis', icon: DollarSign },
            { id: 'commute-impact', label: 'Commute Impact', icon: BarChart3 },
            { id: 'career-move', label: 'Career Move Planning', icon: MapPin },
            { id: 'budget-optimization', label: 'Budget Optimization', icon: Target }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center space-x-2 px-4 py-2 rounded-md transition-colors duration-200 ${
                activeTab === tab.id
                  ? 'bg-violet-600 text-white'
                  : 'text-gray-400 hover:text-white hover:bg-gray-700'
              }`}
            >
              <tab.icon className="w-4 h-4" />
              <span className="text-sm font-medium">{tab.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Job Cost Analysis Tab */}
      {activeTab === 'job-cost' && (
        <div className="space-y-6">
          {/* Input Section */}
          <div className="bg-gray-800 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-white mb-4">Job Opportunity Analysis</h3>
            
            {/* Home Address */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-white mb-2">
                <MapPin className="w-4 h-4 inline mr-2" />
                Home Address
              </label>
              <input
                type="text"
                value={homeAddress}
                onChange={(e) => setHomeAddress(e.target.value)}
                placeholder="Enter your home address"
                className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-violet-500"
              />
            </div>

            {/* Vehicle Selection */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-white mb-2">
                <Car className="w-4 h-4 inline mr-2" />
                Select Vehicle
              </label>
              <select
                value={selectedVehicleId}
                onChange={(e) => setSelectedVehicleId(e.target.value)}
                className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-violet-500"
              >
                <option value="">Select a vehicle</option>
                {vehicles.map((vehicle) => (
                  <option key={vehicle.id} value={vehicle.id}>
                    {vehicle.year} {vehicle.make} {vehicle.model} ({vehicle.mpg} MPG)
                  </option>
                ))}
              </select>
            </div>

            {/* Job Offers */}
            <div className="mb-4">
              <div className="flex items-center justify-between mb-3">
                <label className="block text-sm font-medium text-white">
                  Job Offers to Compare
                </label>
                <button
                  onClick={addJobOffer}
                  className="flex items-center space-x-2 bg-violet-600 hover:bg-violet-700 text-white px-3 py-2 rounded-lg text-sm font-medium transition-colors duration-200"
                >
                  <Plus className="w-4 h-4" />
                  <span>Add Job</span>
                </button>
              </div>
              
              <div className="space-y-3">
                {jobOffers.map((offer, index) => (
                  <div key={offer.id} className="bg-gray-700 rounded-lg p-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      <div>
                        <label className="block text-xs text-gray-400 mb-1">Job Title</label>
                        <input
                          type="text"
                          value={offer.title}
                          onChange={(e) => updateJobOffer(offer.id, 'title', e.target.value)}
                          placeholder="Software Engineer"
                          className="w-full px-3 py-2 bg-gray-600 border border-gray-500 rounded text-white placeholder-gray-400 text-sm focus:outline-none focus:ring-1 focus:ring-violet-500"
                        />
                      </div>
                      <div>
                        <label className="block text-xs text-gray-400 mb-1">Company</label>
                        <input
                          type="text"
                          value={offer.company}
                          onChange={(e) => updateJobOffer(offer.id, 'company', e.target.value)}
                          placeholder="Tech Corp"
                          className="w-full px-3 py-2 bg-gray-600 border border-gray-500 rounded text-white placeholder-gray-400 text-sm focus:outline-none focus:ring-1 focus:ring-violet-500"
                        />
                      </div>
                      <div>
                        <label className="block text-xs text-gray-400 mb-1">Location</label>
                        <input
                          type="text"
                          value={offer.location}
                          onChange={(e) => updateJobOffer(offer.id, 'location', e.target.value)}
                          placeholder="123 Main St, City, State"
                          className="w-full px-3 py-2 bg-gray-600 border border-gray-500 rounded text-white placeholder-gray-400 text-sm focus:outline-none focus:ring-1 focus:ring-violet-500"
                        />
                      </div>
                      <div>
                        <label className="block text-xs text-gray-400 mb-1">Salary</label>
                        <input
                          type="number"
                          value={offer.salary}
                          onChange={(e) => updateJobOffer(offer.id, 'salary', parseInt(e.target.value) || 0)}
                          placeholder="75000"
                          className="w-full px-3 py-2 bg-gray-600 border border-gray-500 rounded text-white placeholder-gray-400 text-sm focus:outline-none focus:ring-1 focus:ring-violet-500"
                        />
                      </div>
                      <div className="flex items-center space-x-2">
                        <label className="flex items-center space-x-2 text-sm text-gray-300">
                          <input
                            type="checkbox"
                            checked={offer.remoteFriendly}
                            onChange={(e) => updateJobOffer(offer.id, 'remoteFriendly', e.target.checked)}
                            className="rounded border-gray-500 bg-gray-600 text-violet-600 focus:ring-violet-500"
                          />
                          <span>Remote Friendly</span>
                        </label>
                      </div>
                      <div className="flex justify-end">
                        <button
                          onClick={() => removeJobOffer(offer.id)}
                          className="text-red-400 hover:text-red-300 text-sm"
                        >
                          Remove
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <button
              onClick={calculateJobCosts}
              disabled={loading || !homeAddress || !selectedVehicleId || jobOffers.length === 0}
              className="w-full bg-violet-600 hover:bg-violet-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white px-6 py-3 rounded-lg font-semibold transition-colors duration-200"
            >
              {loading ? (
                <div className="flex items-center justify-center space-x-2">
                  <Loader2 className="w-5 h-5 animate-spin" />
                  <span>Calculating...</span>
                </div>
              ) : (
                'Calculate True Job Costs'
              )}
            </button>
          </div>

          {/* Results Section */}
          {jobCostResults.length > 0 && (
            <div className="space-y-6">
              <h3 className="text-lg font-semibold text-white">Analysis Results</h3>
              
              {jobCostResults.map((result, index) => (
                <div key={index} className="bg-gray-800 rounded-lg p-6">
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <h4 className="text-xl font-semibold text-white">{result.jobOffer.title}</h4>
                      <p className="text-gray-400">{result.jobOffer.company} • {result.jobOffer.location}</p>
                    </div>
                    <div className="text-right">
                      <div className="text-2xl font-bold text-violet-400">
                        ${result.trueCompensation.annual.toLocaleString()}
                      </div>
                      <div className="text-sm text-gray-400">True Annual Compensation</div>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                    <div className="bg-gray-700 rounded-lg p-4">
                      <div className="text-sm text-gray-400 mb-1">Base Salary</div>
                      <div className="text-xl font-semibold text-white">
                        ${result.jobOffer.salary.toLocaleString()}
                      </div>
                    </div>
                    <div className="bg-gray-700 rounded-lg p-4">
                      <div className="text-sm text-gray-400 mb-1">Annual Commute Cost</div>
                      <div className="text-xl font-semibold text-red-400">
                        -${result.commuteAnalysis.annual_cost.toLocaleString()}
                      </div>
                    </div>
                    <div className="bg-gray-700 rounded-lg p-4">
                      <div className="text-sm text-gray-400 mb-1">Cost as % of Salary</div>
                      <div className="text-xl font-semibold text-orange-400">
                        {result.trueCompensation.cost_percentage}%
                      </div>
                    </div>
                  </div>

                  <div className="mb-4">
                    <h5 className="text-sm font-medium text-white mb-2">Weekly Cost Breakdown</h5>
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                      <div className="bg-gray-700 rounded p-3">
                        <div className="text-xs text-gray-400">Fuel</div>
                        <div className="text-sm font-semibold text-white">
                          ${result.commuteAnalysis.cost_breakdown.fuel.daily.toFixed(2)}/day
                        </div>
                      </div>
                      <div className="bg-gray-700 rounded p-3">
                        <div className="text-xs text-gray-400">Maintenance</div>
                        <div className="text-sm font-semibold text-white">
                          ${result.commuteAnalysis.cost_breakdown.maintenance.daily.toFixed(2)}/day
                        </div>
                      </div>
                      <div className="bg-gray-700 rounded p-3">
                        <div className="text-xs text-gray-400">Parking</div>
                        <div className="text-sm font-semibold text-white">
                          ${result.commuteAnalysis.cost_breakdown.parking.daily.toFixed(2)}/day
                        </div>
                      </div>
                    </div>
                  </div>

                  {result.recommendations.length > 0 && (
                    <div>
                      <h5 className="text-sm font-medium text-white mb-2">Recommendations</h5>
                      <ul className="space-y-1">
                        {result.recommendations.map((rec, recIndex) => (
                          <li key={recIndex} className="text-sm text-gray-300 flex items-start space-x-2">
                            <ArrowRight className="w-4 h-4 text-violet-400 mt-0.5 flex-shrink-0" />
                            <span>{rec}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Commute Impact Analysis Tab */}
      {activeTab === 'commute-impact' && (
        <div className="space-y-6">
          <div className="bg-gray-800 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-white mb-4">Commute Impact Analysis</h3>
            <p className="text-gray-400 mb-4">
              Analyze transportation cost projections for different job locations
            </p>
            
            <div className="text-center py-8">
              <BarChart3 className="w-16 h-16 text-gray-600 mx-auto mb-4" />
              <p className="text-gray-400">Commute Impact Analysis coming soon...</p>
            </div>
          </div>
        </div>
      )}

      {/* Career Move Planning Tab */}
      {activeTab === 'career-move' && (
        <div className="space-y-6">
          <div className="bg-gray-800 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-white mb-4">Career Move Financial Planning</h3>
            <p className="text-gray-400 mb-4">
              Plan career moves with vehicle and moving cost considerations
            </p>
            
            <div className="text-center py-8">
              <MapPin className="w-16 h-16 text-gray-600 mx-auto mb-4" />
              <p className="text-gray-400">Career Move Planning coming soon...</p>
            </div>
          </div>
        </div>
      )}

      {/* Budget Optimization Tab */}
      {activeTab === 'budget-optimization' && (
        <div className="space-y-6">
          <div className="bg-gray-800 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-white mb-4">Budget-Friendly Optimization</h3>
            <p className="text-gray-400 mb-4">
              Optimize budget around job and commute decisions for budget-tier users
            </p>
            
            <div className="text-center py-8">
              <Target className="w-16 h-16 text-gray-600 mx-auto mb-4" />
              <p className="text-gray-400">Budget Optimization coming soon...</p>
            </div>
          </div>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="mt-6 bg-red-500 bg-opacity-10 border border-red-500 text-red-300 px-4 py-3 rounded-lg flex items-center">
          <AlertCircle className="w-5 h-5 mr-2" />
          {error}
        </div>
      )}
    </div>
  );
};

export default CareerVehicleOptimization;
