import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Home, 
  MapPin, 
  BarChart3, 
  Settings, 
  Search, 
  Compare, 
  TrendingUp,
  AlertTriangle,
  RefreshCw,
  ArrowLeft,
  ArrowRight,
  Star,
  Lock,
  CheckCircle,
  XCircle
} from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
import { useAnalytics } from '../../hooks/useAnalytics';
import DashboardErrorBoundary from '../DashboardErrorBoundary';

// ========================================
// TYPE DEFINITIONS
// ========================================

interface UserTier {
  tier: 'budget' | 'budget_career_vehicle' | 'mid_tier' | 'professional';
  features: {
    showBasicSearch: boolean;
    showScenarioPlanning: boolean;
    showCareerIntegration: boolean;
    showAdvancedAnalytics: boolean;
    showExportOptions: boolean;
    showBusinessFeatures: boolean;
  };
}

interface HousingSearchState {
  location: string;
  budget: {
    min: number;
    max: number;
  };
  preferences: {
    propertyType: 'apartment' | 'house' | 'condo' | 'any';
    bedrooms: number;
    bathrooms: number;
    amenities: string[];
  };
  radius: number; // in miles
  searchResults: any[];
  loading: boolean;
  error: string | null;
}

interface Scenario {
  id: string;
  name: string;
  location: string;
  budget: number;
  commuteTime: number;
  qualityOfLife: number;
  careerOpportunities: number;
  costOfLiving: number;
  createdAt: Date;
  isActive: boolean;
}

interface OptimalLocationState {
  activeView: 'search' | 'scenarios' | 'results' | 'preferences';
  housingSearch: HousingSearchState;
  scenarios: Scenario[];
  selectedScenario: Scenario | null;
  userPreferences: {
    prioritizeCommute: boolean;
    prioritizeCost: boolean;
    prioritizeCareer: boolean;
    prioritizeLifestyle: boolean;
  };
  loading: boolean;
  error: string | null;
  lastUpdated: Date;
}

// ========================================
// TIER CONFIGURATION
// ========================================

const getTierFeatures = (tier: UserTier['tier']): UserTier['features'] => {
  const tierConfig = {
    budget: {
      tier: 'budget' as const,
      features: {
        showBasicSearch: true,
        showScenarioPlanning: false,
        showCareerIntegration: false,
        showAdvancedAnalytics: false,
        showExportOptions: false,
        showBusinessFeatures: false
      }
    },
    budget_career_vehicle: {
      tier: 'budget_career_vehicle' as const,
      features: {
        showBasicSearch: true,
        showScenarioPlanning: false,
        showCareerIntegration: true,
        showAdvancedAnalytics: false,
        showExportOptions: false,
        showBusinessFeatures: false
      }
    },
    mid_tier: {
      tier: 'mid_tier' as const,
      features: {
        showBasicSearch: true,
        showScenarioPlanning: true,
        showCareerIntegration: true,
        showAdvancedAnalytics: true,
        showExportOptions: false,
        showBusinessFeatures: false
      }
    },
    professional: {
      tier: 'professional' as const,
      features: {
        showBasicSearch: true,
        showScenarioPlanning: true,
        showCareerIntegration: true,
        showAdvancedAnalytics: true,
        showExportOptions: true,
        showBusinessFeatures: true
      }
    }
  };

  return tierConfig[tier].features;
};

// ========================================
// MAIN COMPONENT
// ========================================

interface OptimalLocationRouterProps {
  className?: string;
}

const OptimalLocationRouter: React.FC<OptimalLocationRouterProps> = ({ className = '' }) => {
  const navigate = useNavigate();
  const { user, isAuthenticated, loading: authLoading } = useAuth();
  const { trackPageView, trackInteraction, trackError } = useAnalytics();

  // State management
  const [userTier, setUserTier] = useState<UserTier | null>(null);
  const [optimalLocationState, setOptimalLocationState] = useState<OptimalLocationState>({
    activeView: 'search',
    housingSearch: {
      location: '',
      budget: { min: 0, max: 0 },
      preferences: {
        propertyType: 'any',
        bedrooms: 1,
        bathrooms: 1,
        amenities: []
      },
      radius: 10,
      searchResults: [],
      loading: false,
      error: null
    },
    scenarios: [],
    selectedScenario: null,
    userPreferences: {
      prioritizeCommute: true,
      prioritizeCost: true,
      prioritizeCareer: false,
      prioritizeLifestyle: false
    },
    loading: true,
    error: null,
    lastUpdated: new Date()
  });

  // ========================================
  // AUTHENTICATION & TIER MANAGEMENT
  // ========================================

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      navigate('/login');
      return;
    }

    if (isAuthenticated && user) {
      initializeOptimalLocation();
    }
  }, [isAuthenticated, authLoading, user, navigate]);

  const initializeOptimalLocation = async () => {
    try {
      setOptimalLocationState(prev => ({ ...prev, loading: true, error: null }));

      // Fetch user tier
      const tierResponse = await fetch('/api/user/tier', {
        headers: {
          'Authorization': `Bearer ${user?.token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!tierResponse.ok) {
        throw new Error('Failed to load user tier information');
      }

      const tierData = await tierResponse.json();
      const tier = tierData.tier || 'budget';
      const features = getTierFeatures(tier);
      
      setUserTier({ tier, features });

      // Fetch existing scenarios
      const scenariosResponse = await fetch('/api/optimal-location/scenarios', {
        headers: {
          'Authorization': `Bearer ${user?.token}`,
          'Content-Type': 'application/json'
        }
      });

      if (scenariosResponse.ok) {
        const scenariosData = await scenariosResponse.json();
        setOptimalLocationState(prev => ({
          ...prev,
          scenarios: scenariosData.scenarios || [],
          loading: false,
          lastUpdated: new Date()
        }));
      } else {
        setOptimalLocationState(prev => ({
          ...prev,
          loading: false,
          lastUpdated: new Date()
        }));
      }

      // Track page view
      await trackPageView('optimal_location_router', {
        user_id: user?.id,
        user_tier: tier,
        active_view: 'search'
      });

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to initialize optimal location feature';
      setOptimalLocationState(prev => ({
        ...prev,
        loading: false,
        error: errorMessage
      }));
      
      await trackError(error instanceof Error ? error : new Error(errorMessage), {
        component: 'OptimalLocationRouter',
        action: 'initialize'
      });
    }
  };

  // ========================================
  // VIEW NAVIGATION
  // ========================================

  const handleViewChange = useCallback(async (newView: OptimalLocationState['activeView']) => {
    setOptimalLocationState(prev => ({ ...prev, activeView: newView }));
    
    await trackInteraction('optimal_location_view_changed', {
      previous_view: optimalLocationState.activeView,
      new_view: newView,
      user_tier: userTier?.tier
    });
  }, [optimalLocationState.activeView, userTier?.tier, trackInteraction]);

  // ========================================
  // HOUSING SEARCH
  // ========================================

  const handleSearchSubmit = useCallback(async (searchData: Partial<HousingSearchState['housingSearch']>) => {
    if (!userTier?.features.showBasicSearch) {
      await trackInteraction('feature_restricted', {
        feature: 'housing_search',
        user_tier: userTier?.tier,
        required_tier: 'budget'
      });
      return;
    }

    try {
      setOptimalLocationState(prev => ({
        ...prev,
        housingSearch: { ...prev.housingSearch, loading: true, error: null }
      }));

      const response = await fetch('/api/optimal-location/housing-search', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${user?.token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(searchData)
      });

      if (!response.ok) {
        throw new Error('Housing search failed');
      }

      const data = await response.json();
      
      setOptimalLocationState(prev => ({
        ...prev,
        housingSearch: {
          ...prev.housingSearch,
          ...searchData,
          searchResults: data.results || [],
          loading: false,
          error: null
        }
      }));

      await trackInteraction('housing_search_completed', {
        location: searchData.location,
        budget_range: searchData.budget,
        results_count: data.results?.length || 0,
        user_tier: userTier?.tier
      });

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Search failed';
      setOptimalLocationState(prev => ({
        ...prev,
        housingSearch: {
          ...prev.housingSearch,
          loading: false,
          error: errorMessage
        }
      }));

      await trackError(error instanceof Error ? error : new Error(errorMessage), {
        component: 'OptimalLocationRouter',
        action: 'housing_search'
      });
    }
  }, [userTier, user?.token, trackInteraction, trackError]);

  // ========================================
  // SCENARIO MANAGEMENT
  // ========================================

  const handleCreateScenario = useCallback(async (scenarioData: Omit<Scenario, 'id' | 'createdAt'>) => {
    if (!userTier?.features.showScenarioPlanning) {
      await trackInteraction('feature_restricted', {
        feature: 'scenario_planning',
        user_tier: userTier?.tier,
        required_tier: 'mid_tier'
      });
      return;
    }

    try {
      const response = await fetch('/api/optimal-location/scenarios', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${user?.token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(scenarioData)
      });

      if (!response.ok) {
        throw new Error('Failed to create scenario');
      }

      const data = await response.json();
      const newScenario: Scenario = {
        ...scenarioData,
        id: data.scenario_id,
        createdAt: new Date()
      };

      setOptimalLocationState(prev => ({
        ...prev,
        scenarios: [...prev.scenarios, newScenario]
      }));

      await trackInteraction('scenario_created', {
        scenario_name: scenarioData.name,
        location: scenarioData.location,
        user_tier: userTier?.tier
      });

    } catch (error) {
      await trackError(error instanceof Error ? error : new Error('Scenario creation failed'), {
        component: 'OptimalLocationRouter',
        action: 'create_scenario'
      });
    }
  }, [userTier, user?.token, trackInteraction, trackError]);

  // ========================================
  // LOADING & ERROR STATES
  // ========================================

  if (authLoading || optimalLocationState.loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-violet-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading optimal location feature...</p>
        </div>
      </div>
    );
  }

  if (optimalLocationState.error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-xl shadow-lg p-8 max-w-2xl w-full text-center">
          <div className="text-red-500 mb-6">
            <AlertTriangle className="h-16 w-16 mx-auto" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900 mb-4">
            Unable to Load Feature
          </h1>
          <p className="text-gray-600 mb-6">
            {optimalLocationState.error}
          </p>
          <button
            onClick={initializeOptimalLocation}
            className="bg-violet-600 hover:bg-violet-700 text-white px-6 py-3 rounded-lg font-medium transition-colors flex items-center justify-center gap-2 mx-auto"
          >
            <RefreshCw className="h-5 w-5" />
            Try Again
          </button>
        </div>
      </div>
    );
  }

  if (!userTier) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-xl shadow-lg p-8 max-w-2xl w-full text-center">
          <div className="text-yellow-500 mb-6">
            <Lock className="h-16 w-16 mx-auto" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900 mb-4">
            Subscription Required
          </h1>
          <p className="text-gray-600 mb-6">
            The Optimal Living Location feature requires an active subscription.
          </p>
          <button
            onClick={() => navigate('/pricing')}
            className="bg-violet-600 hover:bg-violet-700 text-white px-6 py-3 rounded-lg font-medium transition-colors"
          >
            View Pricing Plans
          </button>
        </div>
      </div>
    );
  }

  // ========================================
  // RENDER COMPONENT
  // ========================================

  return (
    <DashboardErrorBoundary>
      <div className={`min-h-screen bg-gray-50 ${className}`}>
        {/* Header */}
        <div className="bg-white border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-16">
              {/* Back Button */}
              <button
                onClick={() => navigate('/career-dashboard')}
                className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors"
                aria-label="Back to dashboard"
              >
                <ArrowLeft className="h-5 w-5" />
                <span className="hidden sm:inline">Back to Dashboard</span>
              </button>

              {/* Title */}
              <h1 className="text-xl font-semibold text-gray-900">
                Optimal Living Location
              </h1>

              {/* User Tier Badge */}
              <div className="flex items-center gap-2">
                <div className={`px-3 py-1 rounded-full text-xs font-medium ${
                  userTier.tier === 'professional' ? 'bg-purple-100 text-purple-800' :
                  userTier.tier === 'mid_tier' ? 'bg-blue-100 text-blue-800' :
                  userTier.tier === 'budget_career_vehicle' ? 'bg-green-100 text-green-800' :
                  'bg-gray-100 text-gray-800'
                }`}>
                  {userTier.tier.replace('_', ' ').toUpperCase()}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="bg-white border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <nav className="flex space-x-8" role="tablist">
              {[
                { id: 'search', label: 'Housing Search', icon: Search, enabled: userTier.features.showBasicSearch },
                { id: 'scenarios', label: 'Scenarios', icon: Compare, enabled: userTier.features.showScenarioPlanning },
                { id: 'results', label: 'Results', icon: BarChart3, enabled: true },
                { id: 'preferences', label: 'Preferences', icon: Settings, enabled: true }
              ].map((tab) => {
                const IconComponent = tab.icon;
                const isActive = optimalLocationState.activeView === tab.id;
                const isDisabled = !tab.enabled;

                return (
                  <button
                    key={tab.id}
                    onClick={() => tab.enabled && handleViewChange(tab.id as OptimalLocationState['activeView'])}
                    disabled={isDisabled}
                    className={`
                      flex items-center gap-2 px-1 py-4 text-sm font-medium border-b-2 transition-colors
                      ${isActive 
                        ? 'border-violet-500 text-violet-600' 
                        : isDisabled
                        ? 'border-transparent text-gray-400 cursor-not-allowed'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                      }
                    `}
                    role="tab"
                    aria-selected={isActive}
                    aria-disabled={isDisabled}
                  >
                    <IconComponent className="h-5 w-5" />
                    <span className="hidden sm:inline">{tab.label}</span>
                    {isDisabled && <Lock className="h-4 w-4" />}
                  </button>
                );
              })}
            </nav>
          </div>
        </div>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {optimalLocationState.activeView === 'search' && (
            <HousingSearchView
              state={optimalLocationState.housingSearch}
              userTier={userTier}
              onSubmit={handleSearchSubmit}
              onViewChange={handleViewChange}
            />
          )}

          {optimalLocationState.activeView === 'scenarios' && (
            <ScenarioComparisonView
              scenarios={optimalLocationState.scenarios}
              selectedScenario={optimalLocationState.selectedScenario}
              userTier={userTier}
              onCreateScenario={handleCreateScenario}
              onSelectScenario={(scenario) => setOptimalLocationState(prev => ({ 
                ...prev, 
                selectedScenario: scenario 
              }))}
            />
          )}

          {optimalLocationState.activeView === 'results' && (
            <ResultsDisplayView
              searchResults={optimalLocationState.housingSearch.searchResults}
              scenarios={optimalLocationState.scenarios}
              selectedScenario={optimalLocationState.selectedScenario}
              userTier={userTier}
            />
          )}

          {optimalLocationState.activeView === 'preferences' && (
            <PreferencesManagementView
              preferences={optimalLocationState.userPreferences}
              userTier={userTier}
              onUpdatePreferences={(prefs) => setOptimalLocationState(prev => ({
                ...prev,
                userPreferences: { ...prev.userPreferences, ...prefs }
              }))}
            />
          )}
        </main>
      </div>
    </DashboardErrorBoundary>
  );
};

// ========================================
// VIEW COMPONENTS
// ========================================

// Housing Search View
const HousingSearchView: React.FC<{
  state: HousingSearchState;
  userTier: UserTier;
  onSubmit: (data: Partial<HousingSearchState>) => void;
  onViewChange: (view: OptimalLocationState['activeView']) => void;
}> = ({ state, userTier, onSubmit, onViewChange }) => {
  const [formData, setFormData] = useState({
    location: state.location,
    budget: state.budget,
    preferences: state.preferences,
    radius: state.radius
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <div className="space-y-6">
      {/* Feature Restriction Notice */}
      {!userTier.features.showBasicSearch && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex items-center gap-2">
            <Lock className="h-5 w-5 text-yellow-600" />
            <p className="text-yellow-800">
              Housing search is available with Budget tier or higher. 
              <button 
                onClick={() => onViewChange('preferences')}
                className="ml-1 text-yellow-600 hover:text-yellow-700 underline"
              >
                Upgrade your plan
              </button>
            </p>
          </div>
        </div>
      )}

      {/* Search Form */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Find Your Optimal Location</h2>
        
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Location Input */}
          <div>
            <label htmlFor="location" className="block text-sm font-medium text-gray-700 mb-2">
              Location
            </label>
            <input
              type="text"
              id="location"
              value={formData.location}
              onChange={(e) => setFormData(prev => ({ ...prev, location: e.target.value }))}
              placeholder="Enter city, state, or ZIP code"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-violet-400 focus:border-violet-500"
              disabled={!userTier.features.showBasicSearch}
            />
          </div>

          {/* Budget Range */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label htmlFor="minBudget" className="block text-sm font-medium text-gray-700 mb-2">
                Minimum Budget ($)
              </label>
              <input
                type="number"
                id="minBudget"
                value={formData.budget.min}
                onChange={(e) => setFormData(prev => ({ 
                  ...prev, 
                  budget: { ...prev.budget, min: parseInt(e.target.value) || 0 }
                }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-violet-400 focus:border-violet-500"
                disabled={!userTier.features.showBasicSearch}
              />
            </div>
            <div>
              <label htmlFor="maxBudget" className="block text-sm font-medium text-gray-700 mb-2">
                Maximum Budget ($)
              </label>
              <input
                type="number"
                id="maxBudget"
                value={formData.budget.max}
                onChange={(e) => setFormData(prev => ({ 
                  ...prev, 
                  budget: { ...prev.budget, max: parseInt(e.target.value) || 0 }
                }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-violet-400 focus:border-violet-500"
                disabled={!userTier.features.showBasicSearch}
              />
            </div>
          </div>

          {/* Property Preferences */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label htmlFor="propertyType" className="block text-sm font-medium text-gray-700 mb-2">
                Property Type
              </label>
              <select
                id="propertyType"
                value={formData.preferences.propertyType}
                onChange={(e) => setFormData(prev => ({ 
                  ...prev, 
                  preferences: { ...prev.preferences, propertyType: e.target.value as any }
                }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-violet-400 focus:border-violet-500"
                disabled={!userTier.features.showBasicSearch}
              >
                <option value="any">Any</option>
                <option value="apartment">Apartment</option>
                <option value="house">House</option>
                <option value="condo">Condo</option>
              </select>
            </div>
            <div>
              <label htmlFor="bedrooms" className="block text-sm font-medium text-gray-700 mb-2">
                Bedrooms
              </label>
              <select
                id="bedrooms"
                value={formData.preferences.bedrooms}
                onChange={(e) => setFormData(prev => ({ 
                  ...prev, 
                  preferences: { ...prev.preferences, bedrooms: parseInt(e.target.value) }
                }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-violet-400 focus:border-violet-500"
                disabled={!userTier.features.showBasicSearch}
              >
                <option value={1}>1+</option>
                <option value={2}>2+</option>
                <option value={3}>3+</option>
                <option value={4}>4+</option>
              </select>
            </div>
            <div>
              <label htmlFor="bathrooms" className="block text-sm font-medium text-gray-700 mb-2">
                Bathrooms
              </label>
              <select
                id="bathrooms"
                value={formData.preferences.bathrooms}
                onChange={(e) => setFormData(prev => ({ 
                  ...prev, 
                  preferences: { ...prev.preferences, bathrooms: parseInt(e.target.value) }
                }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-violet-400 focus:border-violet-500"
                disabled={!userTier.features.showBasicSearch}
              >
                <option value={1}>1+</option>
                <option value={2}>2+</option>
                <option value={3}>3+</option>
              </select>
            </div>
          </div>

          {/* Search Radius */}
          <div>
            <label htmlFor="radius" className="block text-sm font-medium text-gray-700 mb-2">
              Search Radius: {formData.radius} miles
            </label>
            <input
              type="range"
              id="radius"
              min="1"
              max="50"
              value={formData.radius}
              onChange={(e) => setFormData(prev => ({ ...prev, radius: parseInt(e.target.value) }))}
              className="w-full"
              disabled={!userTier.features.showBasicSearch}
            />
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={!userTier.features.showBasicSearch || state.loading}
            className="w-full bg-violet-600 hover:bg-violet-700 disabled:bg-gray-400 text-white px-6 py-3 rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
          >
            {state.loading ? (
              <>
                <RefreshCw className="h-5 w-5 animate-spin" />
                Searching...
              </>
            ) : (
              <>
                <Search className="h-5 w-5" />
                Search Locations
              </>
            )}
          </button>
        </form>

        {/* Error Display */}
        {state.error && (
          <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-center gap-2">
              <XCircle className="h-5 w-5 text-red-600" />
              <p className="text-red-800">{state.error}</p>
            </div>
          </div>
        )}
      </div>

      {/* Search Results Preview */}
      {state.searchResults.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Found {state.searchResults.length} locations
          </h3>
          <button
            onClick={() => onViewChange('results')}
            className="text-violet-600 hover:text-violet-700 font-medium flex items-center gap-2"
          >
            View Results
            <ArrowRight className="h-4 w-4" />
          </button>
        </div>
      )}
    </div>
  );
};

// Scenario Comparison View
const ScenarioComparisonView: React.FC<{
  scenarios: Scenario[];
  selectedScenario: Scenario | null;
  userTier: UserTier;
  onCreateScenario: (data: Omit<Scenario, 'id' | 'createdAt'>) => void;
  onSelectScenario: (scenario: Scenario) => void;
}> = ({ scenarios, selectedScenario, userTier, onCreateScenario, onSelectScenario }) => {
  return (
    <div className="space-y-6">
      {/* Feature Restriction Notice */}
      {!userTier.features.showScenarioPlanning && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex items-center gap-2">
            <Lock className="h-5 w-5 text-yellow-600" />
            <p className="text-yellow-800">
              Scenario planning is available with Mid-tier or higher. 
              <button className="ml-1 text-yellow-600 hover:text-yellow-700 underline">
                Upgrade your plan
              </button>
            </p>
          </div>
        </div>
      )}

      {/* Scenarios List */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-semibold text-gray-900">Location Scenarios</h2>
          {userTier.features.showScenarioPlanning && (
            <button className="bg-violet-600 hover:bg-violet-700 text-white px-4 py-2 rounded-lg font-medium transition-colors">
              Create New Scenario
            </button>
          )}
        </div>

        {scenarios.length === 0 ? (
          <div className="text-center py-8">
            <MapPin className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-500">No scenarios created yet</p>
            {userTier.features.showScenarioPlanning && (
              <p className="text-sm text-gray-400 mt-2">
                Create your first scenario to compare different locations
              </p>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {scenarios.map((scenario) => (
              <div
                key={scenario.id}
                onClick={() => onSelectScenario(scenario)}
                className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                  selectedScenario?.id === scenario.id
                    ? 'border-violet-500 bg-violet-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <h3 className="font-medium text-gray-900">{scenario.name}</h3>
                <p className="text-sm text-gray-600">{scenario.location}</p>
                <div className="mt-2 flex items-center gap-4 text-xs text-gray-500">
                  <span>${scenario.budget.toLocaleString()}/mo</span>
                  <span>{scenario.commuteTime}min commute</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// Results Display View
const ResultsDisplayView: React.FC<{
  searchResults: any[];
  scenarios: Scenario[];
  selectedScenario: Scenario | null;
  userTier: UserTier;
}> = ({ searchResults, scenarios, selectedScenario, userTier }) => {
  return (
    <div className="space-y-6">
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Search Results</h2>
        
        {searchResults.length === 0 ? (
          <div className="text-center py-8">
            <Search className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-500">No search results yet</p>
            <p className="text-sm text-gray-400 mt-2">
              Use the Housing Search to find locations
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {searchResults.map((result, index) => (
              <div key={index} className="p-4 border border-gray-200 rounded-lg">
                <h3 className="font-medium text-gray-900">{result.title || 'Property'}</h3>
                <p className="text-sm text-gray-600">{result.location}</p>
                <div className="mt-2 flex items-center gap-4 text-sm text-gray-500">
                  <span>${result.price?.toLocaleString()}/mo</span>
                  <span>{result.bedrooms} bed</span>
                  <span>{result.bathrooms} bath</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// Preferences Management View
const PreferencesManagementView: React.FC<{
  preferences: OptimalLocationState['userPreferences'];
  userTier: UserTier;
  onUpdatePreferences: (prefs: Partial<OptimalLocationState['userPreferences']>) => void;
}> = ({ preferences, userTier, onUpdatePreferences }) => {
  return (
    <div className="space-y-6">
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Location Preferences</h2>
        
        <div className="space-y-4">
          {[
            { key: 'prioritizeCommute', label: 'Prioritize Commute Time', description: 'Focus on locations with shorter commute times' },
            { key: 'prioritizeCost', label: 'Prioritize Cost of Living', description: 'Focus on more affordable locations' },
            { key: 'prioritizeCareer', label: 'Prioritize Career Opportunities', description: 'Focus on locations with better job markets' },
            { key: 'prioritizeLifestyle', label: 'Prioritize Lifestyle Quality', description: 'Focus on locations with better quality of life' }
          ].map((pref) => (
            <div key={pref.key} className="flex items-start gap-3">
              <input
                type="checkbox"
                id={pref.key}
                checked={preferences[pref.key as keyof typeof preferences]}
                onChange={(e) => onUpdatePreferences({ [pref.key]: e.target.checked })}
                className="mt-1 h-4 w-4 text-violet-600 focus:ring-violet-400 border-gray-300 rounded"
              />
              <div>
                <label htmlFor={pref.key} className="text-sm font-medium text-gray-900">
                  {pref.label}
                </label>
                <p className="text-sm text-gray-500">{pref.description}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Tier Information */}
      <div className="bg-gray-50 rounded-xl p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Your Plan Features</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[
            { feature: 'Basic Housing Search', enabled: userTier.features.showBasicSearch },
            { feature: 'Scenario Planning', enabled: userTier.features.showScenarioPlanning },
            { feature: 'Career Integration', enabled: userTier.features.showCareerIntegration },
            { feature: 'Advanced Analytics', enabled: userTier.features.showAdvancedAnalytics },
            { feature: 'Export Options', enabled: userTier.features.showExportOptions },
            { feature: 'Business Features', enabled: userTier.features.showBusinessFeatures }
          ].map((item) => (
            <div key={item.feature} className="flex items-center gap-2">
              {item.enabled ? (
                <CheckCircle className="h-5 w-5 text-green-500" />
              ) : (
                <XCircle className="h-5 w-5 text-gray-400" />
              )}
              <span className={`text-sm ${item.enabled ? 'text-gray-900' : 'text-gray-500'}`}>
                {item.feature}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default OptimalLocationRouter;
