import React, { useState, useEffect } from 'react';
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
  ArrowRight,
  Clock,
  Fuel,
  Wrench,
  Shield,
  ParkingCircle,
  Navigation,
  ChevronDown,
  ChevronUp,
  Smartphone
} from 'lucide-react';
import { useAnalytics } from '../hooks/useAnalytics';

// Types (same as main component)
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

interface MobileCareerVehicleOptimizationProps {
  vehicles: Vehicle[];
  className?: string;
}

const MobileCareerVehicleOptimization: React.FC<MobileCareerVehicleOptimizationProps> = ({
  vehicles,
  className = ''
}) => {
  const { trackInteraction, trackError } = useAnalytics();
  
  // State management
  const [activeTab, setActiveTab] = useState<'job-cost' | 'commute-impact' | 'career-move' | 'budget-optimization'>('job-cost');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasAccess, setHasAccess] = useState(false);
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['input']));
  
  // Job Cost Analysis State
  const [jobOffers, setJobOffers] = useState<JobOffer[]>([]);
  const [homeAddress, setHomeAddress] = useState('');
  const [selectedVehicleId, setSelectedVehicleId] = useState<string>('');
  const [jobCostResults, setJobCostResults] = useState<JobCostAnalysis[]>([]);

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

  const toggleSection = (sectionId: string) => {
    setExpandedSections(prev => {
      const newSet = new Set(prev);
      if (newSet.has(sectionId)) {
        newSet.delete(sectionId);
      } else {
        newSet.add(sectionId);
      }
      return newSet;
    });
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
        setExpandedSections(new Set(['results']));
        await trackInteraction('mobile_job_cost_analysis_completed', {
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
      await trackError(err as Error, { context: 'mobile_job_cost_analysis' });
    } finally {
      setLoading(false);
    }
  };

  if (!hasAccess) {
    return (
      <div className={`bg-gray-900 rounded-xl shadow-2xl p-6 text-center ${className}`}>
        <div className="mb-6">
          <div className="text-violet-400 mb-4">
            <Smartphone className="w-16 h-16 mx-auto" />
          </div>
          <h2 className="text-xl font-bold text-white mb-2">Career-Vehicle Optimization</h2>
          <p className="text-gray-400 mb-4 text-sm">
            Optimize your job opportunities and commute costs with our Budget tier add-on
          </p>
        </div>
        
        <div className="bg-gradient-to-r from-violet-600 to-purple-600 rounded-lg p-4 mb-4">
          <h3 className="text-lg font-semibold text-white mb-3">Mobile-Optimized Features</h3>
          <div className="space-y-2 text-left">
            <div className="flex items-center space-x-2">
              <CheckCircle className="w-4 h-4 text-green-300" />
              <span className="text-violet-100 text-sm">Job Opportunity True Cost Calculator</span>
            </div>
            <div className="flex items-center space-x-2">
              <CheckCircle className="w-4 h-4 text-green-300" />
              <span className="text-violet-100 text-sm">Commute Cost Impact Analysis</span>
            </div>
            <div className="flex items-center space-x-2">
              <CheckCircle className="w-4 h-4 text-green-300" />
              <span className="text-violet-100 text-sm">Career Move Financial Planning</span>
            </div>
            <div className="flex items-center space-x-2">
              <CheckCircle className="w-4 h-4 text-green-300" />
              <span className="text-violet-100 text-sm">Budget-Friendly Optimization</span>
            </div>
          </div>
        </div>
        
        <div className="bg-gray-800 rounded-lg p-4">
          <div className="text-center mb-3">
            <div className="text-2xl font-bold text-white">$7/month</div>
            <div className="text-gray-400 text-sm">Add-on to Budget tier ($15 + $7 = $22 total)</div>
          </div>
          <button className="w-full bg-violet-600 hover:bg-violet-700 text-white px-4 py-3 rounded-lg font-semibold text-sm transition-colors duration-200">
            Upgrade to Add Career-Vehicle Optimization
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-gray-900 rounded-xl shadow-2xl p-4 ${className}`}>
      {/* Header */}
      <div className="mb-4">
        <div className="flex items-center space-x-2 mb-2">
          <div className="text-violet-400">
            <Calculator className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white">Career-Vehicle Optimization</h2>
            <p className="text-gray-400 text-sm">Optimize job opportunities and commute costs</p>
          </div>
        </div>
      </div>

      {/* Mobile Tab Navigation */}
      <div className="mb-4">
        <div className="grid grid-cols-2 gap-1 bg-gray-800 rounded-lg p-1">
          {[
            { id: 'job-cost', label: 'Job Costs', icon: DollarSign },
            { id: 'commute-impact', label: 'Commute', icon: BarChart3 },
            { id: 'career-move', label: 'Career Move', icon: MapPin },
            { id: 'budget-optimization', label: 'Budget', icon: Target }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex flex-col items-center space-y-1 px-2 py-2 rounded-md transition-colors duration-200 ${
                activeTab === tab.id
                  ? 'bg-violet-600 text-white'
                  : 'text-gray-400 hover:text-white hover:bg-gray-700'
              }`}
            >
              <tab.icon className="w-4 h-4" />
              <span className="text-xs font-medium">{tab.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Job Cost Analysis Tab */}
      {activeTab === 'job-cost' && (
        <div className="space-y-4">
          {/* Input Section */}
          <div className="bg-gray-800 rounded-lg p-4">
            <button
              onClick={() => toggleSection('input')}
              className="w-full flex items-center justify-between text-white mb-3"
            >
              <h3 className="text-base font-semibold">Job Opportunity Analysis</h3>
              {expandedSections.has('input') ? (
                <ChevronUp className="w-5 h-5" />
              ) : (
                <ChevronDown className="w-5 h-5" />
              )}
            </button>
            
            {expandedSections.has('input') && (
              <div className="space-y-4">
                {/* Home Address */}
                <div>
                  <label className="block text-sm font-medium text-white mb-1">
                    <MapPin className="w-3 h-3 inline mr-1" />
                    Home Address
                  </label>
                  <input
                    type="text"
                    value={homeAddress}
                    onChange={(e) => setHomeAddress(e.target.value)}
                    placeholder="Enter your home address"
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-violet-400 text-sm"
                  />
                </div>

                {/* Vehicle Selection */}
                <div>
                  <label className="block text-sm font-medium text-white mb-1">
                    <Car className="w-3 h-3 inline mr-1" />
                    Select Vehicle
                  </label>
                  <select
                    value={selectedVehicleId}
                    onChange={(e) => setSelectedVehicleId(e.target.value)}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-violet-400 text-sm"
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
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="block text-sm font-medium text-white">
                      Job Offers to Compare
                    </label>
                    <button
                      onClick={addJobOffer}
                      className="flex items-center space-x-1 bg-violet-600 hover:bg-violet-700 text-white px-2 py-1 rounded text-xs font-medium transition-colors duration-200"
                    >
                      <Plus className="w-3 h-3" />
                      <span>Add</span>
                    </button>
                  </div>
                  
                  <div className="space-y-2">
                    {jobOffers.map((offer, index) => (
                      <div key={offer.id} className="bg-gray-700 rounded-lg p-3">
                        <div className="space-y-2">
                          <div className="grid grid-cols-2 gap-2">
                            <input
                              type="text"
                              value={offer.title}
                              onChange={(e) => updateJobOffer(offer.id, 'title', e.target.value)}
                              placeholder="Job Title"
                              className="w-full px-2 py-1 bg-gray-600 border border-gray-500 rounded text-white placeholder-gray-400 text-xs focus:outline-none focus:ring-1 focus:ring-violet-400"
                            />
                            <input
                              type="text"
                              value={offer.company}
                              onChange={(e) => updateJobOffer(offer.id, 'company', e.target.value)}
                              placeholder="Company"
                              className="w-full px-2 py-1 bg-gray-600 border border-gray-500 rounded text-white placeholder-gray-400 text-xs focus:outline-none focus:ring-1 focus:ring-violet-400"
                            />
                          </div>
                          <input
                            type="text"
                            value={offer.location}
                            onChange={(e) => updateJobOffer(offer.id, 'location', e.target.value)}
                            placeholder="Job Location"
                            className="w-full px-2 py-1 bg-gray-600 border border-gray-500 rounded text-white placeholder-gray-400 text-xs focus:outline-none focus:ring-1 focus:ring-violet-400"
                          />
                          <div className="flex items-center justify-between">
                            <input
                              type="number"
                              value={offer.salary}
                              onChange={(e) => updateJobOffer(offer.id, 'salary', parseInt(e.target.value) || 0)}
                              placeholder="Salary"
                              className="w-24 px-2 py-1 bg-gray-600 border border-gray-500 rounded text-white placeholder-gray-400 text-xs focus:outline-none focus:ring-1 focus:ring-violet-400"
                            />
                            <label className="flex items-center space-x-1 text-xs text-gray-300">
                              <input
                                type="checkbox"
                                checked={offer.remoteFriendly}
                                onChange={(e) => updateJobOffer(offer.id, 'remoteFriendly', e.target.checked)}
                                className="rounded border-gray-500 bg-gray-600 text-violet-600 focus:ring-violet-400"
                              />
                              <span>Remote</span>
                            </label>
                            <button
                              onClick={() => removeJobOffer(offer.id)}
                              className="text-red-400 hover:text-red-300 text-xs"
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
                  className="w-full bg-violet-600 hover:bg-violet-700 disabled:bg-gray-600 disabled:cursor-not-allowed text-white px-4 py-2 rounded-lg font-semibold transition-colors duration-200 text-sm"
                >
                  {loading ? (
                    <div className="flex items-center justify-center space-x-2">
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>Calculating...</span>
                    </div>
                  ) : (
                    'Calculate True Job Costs'
                  )}
                </button>
              </div>
            )}
          </div>

          {/* Results Section */}
          {jobCostResults.length > 0 && (
            <div className="bg-gray-800 rounded-lg p-4">
              <button
                onClick={() => toggleSection('results')}
                className="w-full flex items-center justify-between text-white mb-3"
              >
                <h3 className="text-base font-semibold">Analysis Results</h3>
                {expandedSections.has('results') ? (
                  <ChevronUp className="w-5 h-5" />
                ) : (
                  <ChevronDown className="w-5 h-5" />
                )}
              </button>
              
              {expandedSections.has('results') && (
                <div className="space-y-4">
                  {jobCostResults.map((result, index) => (
                    <div key={index} className="bg-gray-700 rounded-lg p-3">
                      <div className="mb-3">
                        <h4 className="text-base font-semibold text-white">{result.jobOffer.title}</h4>
                        <p className="text-gray-400 text-sm">{result.jobOffer.company}</p>
                        <p className="text-gray-500 text-xs">{result.jobOffer.location}</p>
                      </div>

                      <div className="grid grid-cols-2 gap-2 mb-3">
                        <div className="bg-gray-600 rounded p-2">
                          <div className="text-xs text-gray-400 mb-1">Base Salary</div>
                          <div className="text-sm font-semibold text-white">
                            ${result.jobOffer.salary.toLocaleString()}
                          </div>
                        </div>
                        <div className="bg-gray-600 rounded p-2">
                          <div className="text-xs text-gray-400 mb-1">True Compensation</div>
                          <div className="text-sm font-semibold text-violet-400">
                            ${result.trueCompensation.annual.toLocaleString()}
                          </div>
                        </div>
                      </div>

                      <div className="mb-3">
                        <div className="text-xs text-gray-400 mb-1">Weekly Cost Breakdown</div>
                        <div className="grid grid-cols-3 gap-1">
                          <div className="bg-gray-600 rounded p-2 text-center">
                            <div className="text-xs text-gray-400">Fuel</div>
                            <div className="text-xs font-semibold text-white">
                              ${result.commuteAnalysis.cost_breakdown.fuel.daily.toFixed(0)}/day
                            </div>
                          </div>
                          <div className="bg-gray-600 rounded p-2 text-center">
                            <div className="text-xs text-gray-400">Maint.</div>
                            <div className="text-xs font-semibold text-white">
                              ${result.commuteAnalysis.cost_breakdown.maintenance.daily.toFixed(0)}/day
                            </div>
                          </div>
                          <div className="bg-gray-600 rounded p-2 text-center">
                            <div className="text-xs text-gray-400">Other</div>
                            <div className="text-xs font-semibold text-white">
                              ${(result.commuteAnalysis.cost_breakdown.parking.daily + result.commuteAnalysis.cost_breakdown.insurance.daily).toFixed(0)}/day
                            </div>
                          </div>
                        </div>
                      </div>

                      <div className="text-center">
                        <div className="text-xs text-gray-400">Cost as % of Salary</div>
                        <div className="text-lg font-bold text-orange-400">
                          {result.trueCompensation.cost_percentage}%
                        </div>
                      </div>

                      {result.recommendations.length > 0 && (
                        <div className="mt-3 pt-3 border-t border-gray-600">
                          <div className="text-xs text-gray-400 mb-2">Recommendations</div>
                          <ul className="space-y-1">
                            {result.recommendations.slice(0, 2).map((rec, recIndex) => (
                              <li key={recIndex} className="text-xs text-gray-300 flex items-start space-x-1">
                                <ArrowRight className="w-3 h-3 text-violet-400 mt-0.5 flex-shrink-0" />
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
        </div>
      )}

      {/* Other tabs - simplified for mobile */}
      {activeTab === 'commute-impact' && (
        <div className="bg-gray-800 rounded-lg p-4 text-center">
          <BarChart3 className="w-12 h-12 text-gray-600 mx-auto mb-3" />
          <p className="text-gray-400 text-sm">Commute Impact Analysis coming soon...</p>
        </div>
      )}

      {activeTab === 'career-move' && (
        <div className="bg-gray-800 rounded-lg p-4 text-center">
          <MapPin className="w-12 h-12 text-gray-600 mx-auto mb-3" />
          <p className="text-gray-400 text-sm">Career Move Planning coming soon...</p>
        </div>
      )}

      {activeTab === 'budget-optimization' && (
        <div className="bg-gray-800 rounded-lg p-4 text-center">
          <Target className="w-12 h-12 text-gray-600 mx-auto mb-3" />
          <p className="text-gray-400 text-sm">Budget Optimization coming soon...</p>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="mt-4 bg-red-500 bg-opacity-10 border border-red-500 text-red-300 px-3 py-2 rounded-lg flex items-center text-sm">
          <AlertCircle className="w-4 h-4 mr-2" />
          {error}
        </div>
      )}
    </div>
  );
};

export default MobileCareerVehicleOptimization;
