import React, { useState, useCallback, useEffect, useRef } from 'react';
import { 
  MapPin, 
  Car, 
  DollarSign, 
  Clock, 
  TrendingUp, 
  Save, 
  Plus, 
  Trash2, 
  AlertCircle, 
  Loader2,
  Calculator,
  Target,
  BarChart3,
  FileText,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import { useAnalytics } from '../hooks/useAnalytics';

// Types
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
    distance: number; // miles
    duration: number; // minutes
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

export interface JobOffer {
  id: string;
  title: string;
  company: string;
  location: string;
  salary: {
    min: number;
    max: number;
    median: number;
  };
  benefits: string[];
  remoteFriendly: boolean;
}

export interface CommuteCalculation {
  distance: number;
  duration: number;
  fuelCost: number;
  maintenanceCost: number;
  depreciationCost: number;
  insuranceCost: number;
  parkingCost: number;
  tollsCost: number;
  totalCost: number;
  costPerMile: number;
  annualCost: number;
  trueCompensation: number;
}

interface CommuteCostCalculatorProps {
  jobOffer?: JobOffer;
  vehicles: Vehicle[];
  onSaveScenario: (scenario: CommuteScenario) => void;
  onLoadScenario: (scenarioId: string) => void;
  className?: string;
}

// Address autocomplete hook
const useAddressAutocomplete = () => {
  const [suggestions, setSuggestions] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const searchAddresses = useCallback(async (query: string) => {
    if (query.length < 3) {
      setSuggestions([]);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/geocoding/autocomplete', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || ''
        },
        body: JSON.stringify({ query })
      });

      if (!response.ok) {
        throw new Error('Address search failed');
      }

      const data = await response.json();
      setSuggestions(data.suggestions || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Address search failed');
      setSuggestions([]);
    } finally {
      setLoading(false);
    }
  }, []);

  return { suggestions, loading, error, searchAddresses };
};

// Commute calculation utilities
const calculateCommuteCosts = (
  distance: number,
  vehicle: Vehicle,
  fuelPrice: number = 3.50,
  daysPerWeek: number = 5
): CommuteCalculation => {
  const weeklyDistance = distance * 2 * daysPerWeek; // Round trip
  const monthlyDistance = weeklyDistance * 4.33;
  const annualDistance = monthlyDistance * 12;

  // Fuel costs
  const fuelCostPerMile = fuelPrice / vehicle.mpg;
  const fuelCost = weeklyDistance * fuelCostPerMile;

  // Maintenance costs (based on vehicle age and mileage)
  const vehicleAge = new Date().getFullYear() - vehicle.year;
  const maintenanceRate = vehicleAge > 10 ? 0.15 : vehicleAge > 5 ? 0.10 : 0.08;
  const maintenanceCost = weeklyDistance * maintenanceRate;

  // Depreciation (simplified calculation)
  const depreciationRate = vehicleAge > 10 ? 0.05 : vehicleAge > 5 ? 0.08 : 0.12;
  const depreciationCost = weeklyDistance * depreciationRate;

  // Insurance (prorated for commute)
  const insuranceCost = (500 / 12) * (daysPerWeek / 7); // $500/month insurance

  // Parking (estimated)
  const parkingCost = daysPerWeek * 15; // $15/day parking

  // Tolls (estimated)
  const tollsCost = weeklyDistance * 0.05; // $0.05/mile in tolls

  const totalCost = fuelCost + maintenanceCost + depreciationCost + insuranceCost + parkingCost + tollsCost;
  const costPerMile = totalCost / weeklyDistance;
  const annualCost = totalCost * 52;

  return {
    distance,
    duration: distance * 2, // Assume 2 minutes per mile
    fuelCost,
    maintenanceCost,
    depreciationCost,
    insuranceCost,
    parkingCost,
    tollsCost,
    totalCost,
    costPerMile,
    annualCost,
    trueCompensation: 0 // Will be calculated with salary
  };
};

// Main component
const CommuteCostCalculator: React.FC<CommuteCostCalculatorProps> = ({
  jobOffer,
  vehicles,
  onSaveScenario,
  onLoadScenario,
  className = ''
}) => {
  const { trackInteraction, trackError } = useAnalytics();
  
  // State management
  const [currentStep, setCurrentStep] = useState(0);
  const [jobLocation, setJobLocation] = useState('');
  const [homeLocation, setHomeLocation] = useState('');
  const [selectedVehicle, setSelectedVehicle] = useState<Vehicle | null>(null);
  const [commuteCalculation, setCommuteCalculation] = useState<CommuteCalculation | null>(null);
  const [savedScenarios, setSavedScenarios] = useState<CommuteScenario[]>([]);
  const [showComparison, setShowComparison] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Address autocomplete
  const jobAutocomplete = useAddressAutocomplete();
  const homeAutocomplete = useAddressAutocomplete();

  // Refs
  const jobLocationRef = useRef<HTMLInputElement>(null);
  const homeLocationRef = useRef<HTMLInputElement>(null);

  // Load saved scenarios on mount
  useEffect(() => {
    loadSavedScenarios();
  }, []);

  // Calculate commute when inputs change
  useEffect(() => {
    if (jobLocation && homeLocation && selectedVehicle) {
      calculateCommute();
    }
  }, [jobLocation, homeLocation, selectedVehicle]);

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

  const calculateCommute = async () => {
    if (!jobLocation || !homeLocation || !selectedVehicle) return;

    setLoading(true);
    setError(null);

    try {
      // Get coordinates for both locations
      const [jobCoords, homeCoords] = await Promise.all([
        getCoordinates(jobLocation),
        getCoordinates(homeLocation)
      ]);

      if (!jobCoords || !homeCoords) {
        throw new Error('Could not determine location coordinates');
      }

      // Calculate distance using Google Maps API
      const distance = await calculateDistance(homeCoords, jobCoords);
      
      // Calculate costs
      const calculation = calculateCommuteCosts(distance, selectedVehicle);
      
      // Update true compensation if job offer is provided
      if (jobOffer) {
        calculation.trueCompensation = jobOffer.salary.median - (calculation.annualCost / 12);
      }

      setCommuteCalculation(calculation);
      
      await trackInteraction('commute_calculated', {
        distance,
        vehicle_type: selectedVehicle.fuelType,
        job_location: jobLocation,
        home_location: homeLocation
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to calculate commute');
      await trackError(err as Error, { context: 'commute_calculation' });
    } finally {
      setLoading(false);
    }
  };

  const getCoordinates = async (address: string) => {
    const response = await fetch('/api/geocoding/geocode', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || ''
      },
      body: JSON.stringify({ address })
    });

    if (!response.ok) {
      throw new Error('Geocoding failed');
    }

    const data = await response.json();
    return data.coordinates;
  };

  const calculateDistance = async (origin: { lat: number; lng: number }, destination: { lat: number; lng: number }) => {
    const response = await fetch('/api/geocoding/distance', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || ''
      },
      body: JSON.stringify({ origin, destination })
    });

    if (!response.ok) {
      throw new Error('Distance calculation failed');
    }

    const data = await response.json();
    return data.distance;
  };

  const saveScenario = async () => {
    if (!commuteCalculation || !selectedVehicle) return;

    const scenario: CommuteScenario = {
      id: `scenario_${Date.now()}`,
      name: `${jobOffer?.company || 'Job'} - ${selectedVehicle.make} ${selectedVehicle.model}`,
      jobLocation: {
        address: jobLocation,
        coordinates: await getCoordinates(jobLocation)
      },
      homeLocation: {
        address: homeLocation,
        coordinates: await getCoordinates(homeLocation)
      },
      vehicle: selectedVehicle,
      commuteDetails: {
        distance: commuteCalculation.distance,
        duration: commuteCalculation.duration,
        frequency: 'daily',
        daysPerWeek: 5
      },
      costs: {
        fuel: commuteCalculation.fuelCost,
        maintenance: commuteCalculation.maintenanceCost,
        depreciation: commuteCalculation.depreciationCost,
        insurance: commuteCalculation.insuranceCost,
        parking: commuteCalculation.parkingCost,
        tolls: commuteCalculation.tollsCost,
        total: commuteCalculation.totalCost
      },
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };

    try {
      const response = await fetch('/api/commute/scenarios', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || ''
        },
        body: JSON.stringify(scenario)
      });

      if (response.ok) {
        setSavedScenarios(prev => [...prev, scenario]);
        onSaveScenario(scenario);
        await trackInteraction('scenario_saved', { scenario_id: scenario.id });
      }
    } catch (err) {
      setError('Failed to save scenario');
    }
  };

  const loadScenario = async (scenario: CommuteScenario) => {
    setJobLocation(scenario.jobLocation.address);
    setHomeLocation(scenario.homeLocation.address);
    // Convert scenario vehicle to full Vehicle type with defaults
    setSelectedVehicle({
      ...scenario.vehicle,
      currentMileage: 0,
      monthlyMiles: 0
    });
    onLoadScenario(scenario.id);
    await trackInteraction('scenario_loaded', { scenario_id: scenario.id });
  };

  return (
    <div className={`bg-gray-900 rounded-xl shadow-2xl p-6 ${className}`}>
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center space-x-3 mb-2">
          <div className="text-violet-400">
            <Calculator className="w-8 h-8" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-white">Commute Cost Calculator</h2>
            <p className="text-gray-400">Calculate true compensation including transportation costs</p>
          </div>
        </div>
      </div>

      {/* Job Offer Info */}
      {jobOffer && (
        <div className="bg-gradient-to-r from-violet-600 to-purple-600 rounded-lg p-4 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-white">{jobOffer.title}</h3>
              <p className="text-violet-100">{jobOffer.company} • {jobOffer.location}</p>
              <p className="text-violet-200 text-sm">
                Salary: ${jobOffer.salary.median.toLocaleString()}/year
              </p>
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold text-white">
                ${jobOffer.salary.median.toLocaleString()}
              </div>
              <div className="text-violet-200 text-sm">Base Salary</div>
            </div>
          </div>
        </div>
      )}

      {/* Input Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Job Location */}
        <div className="space-y-3">
          <label className="block text-sm font-medium text-white">
            <MapPin className="w-4 h-4 inline mr-2" />
            Job Location
          </label>
          <div className="relative">
            <input
              ref={jobLocationRef}
              type="text"
              value={jobLocation}
              onChange={(e) => {
                setJobLocation(e.target.value);
                jobAutocomplete.searchAddresses(e.target.value);
              }}
              placeholder="Enter job address"
              className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-violet-400 focus:border-violet-500"
            />
            {jobAutocomplete.loading && (
              <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                <Loader2 className="w-5 h-5 text-violet-400 animate-spin" />
              </div>
            )}
          </div>
          {jobAutocomplete.suggestions.length > 0 && (
            <div className="absolute z-10 w-full bg-gray-800 border border-gray-700 rounded-lg shadow-lg max-h-48 overflow-y-auto">
              {jobAutocomplete.suggestions.map((suggestion, index) => (
                <button
                  key={index}
                  onClick={() => {
                    setJobLocation(suggestion.description);
                    jobAutocomplete.searchAddresses('');
                  }}
                  className="w-full px-4 py-2 text-left text-white hover:bg-gray-700 focus:bg-gray-700 focus:outline-none"
                >
                  {suggestion.description}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Home Location */}
        <div className="space-y-3">
          <label className="block text-sm font-medium text-white">
            <MapPin className="w-4 h-4 inline mr-2" />
            Home Location
          </label>
          <div className="relative">
            <input
              ref={homeLocationRef}
              type="text"
              value={homeLocation}
              onChange={(e) => {
                setHomeLocation(e.target.value);
                homeAutocomplete.searchAddresses(e.target.value);
              }}
              placeholder="Enter home address"
              className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-violet-400 focus:border-violet-500"
            />
            {homeAutocomplete.loading && (
              <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                <Loader2 className="w-5 h-5 text-violet-400 animate-spin" />
              </div>
            )}
          </div>
          {homeAutocomplete.suggestions.length > 0 && (
            <div className="absolute z-10 w-full bg-gray-800 border border-gray-700 rounded-lg shadow-lg max-h-48 overflow-y-auto">
              {homeAutocomplete.suggestions.map((suggestion, index) => (
                <button
                  key={index}
                  onClick={() => {
                    setHomeLocation(suggestion.description);
                    homeAutocomplete.searchAddresses('');
                  }}
                  className="w-full px-4 py-2 text-left text-white hover:bg-gray-700 focus:bg-gray-700 focus:outline-none"
                >
                  {suggestion.description}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Vehicle Selection */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-white mb-3">
          <Car className="w-4 h-4 inline mr-2" />
          Select Vehicle
        </label>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {vehicles.map((vehicle) => (
            <button
              key={vehicle.id}
              onClick={() => setSelectedVehicle(vehicle)}
              className={`p-4 rounded-lg border-2 transition-all duration-200 ${
                selectedVehicle?.id === vehicle.id
                  ? 'border-violet-500 bg-violet-500 bg-opacity-10'
                  : 'border-gray-700 bg-gray-800 hover:border-gray-600'
              }`}
            >
              <div className="text-left">
                <div className="font-semibold text-white">
                  {vehicle.year} {vehicle.make} {vehicle.model}
                </div>
                <div className="text-sm text-gray-400">
                  {vehicle.mpg} MPG • {vehicle.fuelType}
                </div>
                <div className="text-xs text-gray-500 mt-1">
                  {vehicle.currentMileage.toLocaleString()} miles
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Commute Calculation Results */}
      {commuteCalculation && (
        <div className="space-y-6">
          {/* Cost Breakdown */}
          <div className="bg-gray-800 rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-white">Weekly Commute Costs</h3>
              <div className="text-right">
                <div className="text-2xl font-bold text-violet-400">
                  ${commuteCalculation.totalCost.toFixed(2)}
                </div>
                <div className="text-sm text-gray-400">per week</div>
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-gray-700 rounded-lg p-3">
                <div className="text-sm text-gray-400">Fuel</div>
                <div className="text-lg font-semibold text-white">
                  ${commuteCalculation.fuelCost.toFixed(2)}
                </div>
              </div>
              <div className="bg-gray-700 rounded-lg p-3">
                <div className="text-sm text-gray-400">Maintenance</div>
                <div className="text-lg font-semibold text-white">
                  ${commuteCalculation.maintenanceCost.toFixed(2)}
                </div>
              </div>
              <div className="bg-gray-700 rounded-lg p-3">
                <div className="text-sm text-gray-400">Depreciation</div>
                <div className="text-lg font-semibold text-white">
                  ${commuteCalculation.depreciationCost.toFixed(2)}
                </div>
              </div>
              <div className="bg-gray-700 rounded-lg p-3">
                <div className="text-sm text-gray-400">Other</div>
                <div className="text-lg font-semibold text-white">
                  ${(commuteCalculation.insuranceCost + commuteCalculation.parkingCost + commuteCalculation.tollsCost).toFixed(2)}
                </div>
              </div>
            </div>

            <div className="mt-4 pt-4 border-t border-gray-700">
              <div className="flex justify-between items-center">
                <span className="text-gray-400">Distance: {commuteCalculation.distance.toFixed(1)} miles each way</span>
                <span className="text-gray-400">Cost per mile: ${commuteCalculation.costPerMile.toFixed(2)}</span>
              </div>
            </div>
          </div>

          {/* True Compensation */}
          {jobOffer && (
            <div className="bg-gradient-to-r from-green-600 to-emerald-600 rounded-lg p-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-semibold text-white">True Monthly Compensation</h3>
                  <p className="text-green-100 text-sm">
                    After subtracting transportation costs
                  </p>
                </div>
                <div className="text-right">
                  <div className="text-3xl font-bold text-white">
                    ${commuteCalculation.trueCompensation.toLocaleString()}
                  </div>
                  <div className="text-green-200 text-sm">per month</div>
                </div>
              </div>
            </div>
          )}

          {/* Annual Impact */}
          <div className="bg-gray-800 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-white mb-4">Annual Impact</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-violet-400">
                  ${commuteCalculation.annualCost.toLocaleString()}
                </div>
                <div className="text-sm text-gray-400">Annual Commute Cost</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-orange-400">
                  {Math.round(commuteCalculation.annualCost / 2080)} hours
                </div>
                <div className="text-sm text-gray-400">Time Value (at $25/hr)</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-red-400">
                  {Math.round((commuteCalculation.annualCost / (jobOffer?.salary.median || 1)) * 100)}%
                </div>
                <div className="text-sm text-gray-400">of Salary</div>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex space-x-4">
            <button
              onClick={saveScenario}
              className="flex items-center space-x-2 bg-violet-600 hover:bg-violet-700 text-white px-6 py-3 rounded-lg font-semibold transition-colors duration-200"
            >
              <Save className="w-5 h-5" />
              <span>Save Scenario</span>
            </button>
            <button
              onClick={() => setShowComparison(!showComparison)}
              className="flex items-center space-x-2 bg-gray-700 hover:bg-gray-600 text-white px-6 py-3 rounded-lg font-semibold transition-colors duration-200"
            >
              <BarChart3 className="w-5 h-5" />
              <span>{showComparison ? 'Hide' : 'Show'} Comparison</span>
            </button>
          </div>
        </div>
      )}

      {/* Vehicle Comparison Table */}
      {showComparison && vehicles.length > 1 && (
        <div className="mt-6">
          <h3 className="text-lg font-semibold text-white mb-4">Vehicle Comparison</h3>
          <div className="bg-gray-800 rounded-lg overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-700">
                <tr>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-300">Vehicle</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-300">Weekly Cost</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-300">Annual Cost</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-300">Cost/Mile</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700">
                {vehicles.map((vehicle) => {
                  const calc = calculateCommuteCosts(
                    commuteCalculation?.distance || 0,
                    vehicle
                  );
                  return (
                    <tr key={vehicle.id} className="hover:bg-gray-700">
                      <td className="px-4 py-3">
                        <div className="font-medium text-white">
                          {vehicle.year} {vehicle.make} {vehicle.model}
                        </div>
                        <div className="text-sm text-gray-400">
                          {vehicle.mpg} MPG • {vehicle.fuelType}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-white">${calc.totalCost.toFixed(2)}</td>
                      <td className="px-4 py-3 text-white">${calc.annualCost.toLocaleString()}</td>
                      <td className="px-4 py-3 text-white">${calc.costPerMile.toFixed(2)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Saved Scenarios */}
      {savedScenarios.length > 0 && (
        <div className="mt-6">
          <h3 className="text-lg font-semibold text-white mb-4">Saved Scenarios</h3>
          <div className="space-y-3">
            {savedScenarios.map((scenario) => (
              <div
                key={scenario.id}
                className="bg-gray-800 rounded-lg p-4 flex items-center justify-between"
              >
                <div>
                  <div className="font-medium text-white">{scenario.name}</div>
                  <div className="text-sm text-gray-400">
                    {scenario.jobLocation.address} → {scenario.homeLocation.address}
                  </div>
                  <div className="text-xs text-gray-500">
                    ${scenario.costs.total.toFixed(2)}/week • {scenario.commuteDetails.distance.toFixed(1)} miles
                  </div>
                </div>
                <button
                  onClick={() => loadScenario(scenario)}
                  className="bg-violet-600 hover:bg-violet-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors duration-200"
                >
                  Load
                </button>
              </div>
            ))}
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

      {/* Loading State */}
      {loading && (
        <div className="mt-6 flex items-center justify-center py-8">
          <Loader2 className="w-8 h-8 text-violet-400 animate-spin" />
          <span className="ml-3 text-gray-400">Calculating commute costs...</span>
        </div>
      )}
    </div>
  );
};

export default CommuteCostCalculator;
