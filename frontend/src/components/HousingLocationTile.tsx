import React, { useState, useEffect } from 'react';
import { 
  HomeIcon, 
  MapPinIcon, 
  ClockIcon, 
  ExclamationTriangleIcon,
  ArrowUpRightIcon,
  PlusIcon,
  StarIcon,
  CalendarIcon
} from '@heroicons/react/24/outline';
import { useHousingRestrictions, TierGate } from '../hooks/useTierRestrictions';
import { useDashboardSelectors, useDashboardStore } from '../stores/dashboardStore';

interface HousingSearch {
  id: number;
  search_criteria: {
    max_rent: number;
    bedrooms: number;
    zip_code: string;
    housing_type: string;
  };
  results_count: number;
  created_at: string;
  msa_area: string;
}

interface HousingScenario {
  id: number;
  scenario_name: string;
  housing_data: any;
  commute_data: any;
  financial_impact: any;
  is_favorite: boolean;
  created_at: string;
}

interface TierInfo {
  current_tier: string;
  tier_name: string;
  features: {
    housing_searches_per_month: number;
    scenarios_saved: number;
    career_integration: boolean;
    export_functionality: boolean;
    advanced_analytics: boolean;
  };
  has_optimal_location: boolean;
  upgrade_options: Array<{
    tier: string;
    price: number;
    description: string;
    price_difference: number;
  }>;
}

interface HousingLocationTileProps {
  className?: string;
}

const HousingLocationTile: React.FC<HousingLocationTileProps> = ({ className = '' }) => {
  const [showUpgradeModal, setShowUpgradeModal] = useState(false);
  
  // Use dashboard store
  const { 
    housingSearches, 
    housingScenarios, 
    leaseInfo, 
    housingAlerts, 
    unreadAlerts, 
    hasLeaseExpiringSoon,
    housingLoading,
    housingError 
  } = useDashboardSelectors();
  
  const { fetchHousingData } = useDashboardStore();
  
  // Use tier restrictions hook
  const {
    tierInfo,
    canSearchHousing,
    canSaveScenario,
    canUseCareerIntegration,
    getSearchQuotaInfo,
    getScenarioQuotaInfo,
    hasOptimalLocation
  } = useHousingRestrictions();

  useEffect(() => {
    fetchHousingData();
  }, [fetchHousingData]);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric'
    });
  };

  const getTierColor = (tier: string) => {
    switch (tier) {
      case 'budget': return 'text-yellow-600 bg-yellow-50';
      case 'mid_tier': return 'text-blue-600 bg-blue-50';
      case 'professional': return 'text-purple-600 bg-purple-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const getSearchLimitStatus = () => {
    if (!tierInfo) return null;
    
    const searchesUsed = housingSearches.length;
    const quotaInfo = getSearchQuotaInfo(searchesUsed);
    
    if (quotaInfo.unlimited) {
      return { status: 'unlimited', text: 'Unlimited searches' };
    }
    
    if (quotaInfo.remaining <= 0) {
      return { status: 'exceeded', text: 'Limit exceeded' };
    } else if (quotaInfo.remaining <= 2) {
      return { status: 'warning', text: `${quotaInfo.remaining} searches left` };
    }
    
    return { status: 'ok', text: `${quotaInfo.remaining} searches remaining` };
  };

  const getLeaseExpirationAlerts = () => {
    const alerts = [];
    
    if (leaseInfo && leaseInfo.lease_end_date && hasLeaseExpiringSoon()) {
      const leaseEndDate = new Date(leaseInfo.lease_end_date);
      const now = new Date();
      const daysUntilExpiry = Math.ceil((leaseEndDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
      
      alerts.push({
        type: 'lease_expiration',
        message: `Your lease expires in ${daysUntilExpiry} days`,
        date: leaseEndDate,
        urgent: daysUntilExpiry <= 30
      });
    }
    
    return alerts;
  };

  if (housingLoading) {
    return (
      <div className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 ${className}`}>
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="space-y-3">
            <div className="h-4 bg-gray-200 rounded w-full"></div>
            <div className="h-4 bg-gray-200 rounded w-2/3"></div>
            <div className="h-4 bg-gray-200 rounded w-1/2"></div>
          </div>
        </div>
      </div>
    );
  }

  if (housingError) {
    return (
      <div className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 ${className}`}>
        <div className="text-center text-red-600">
          <ExclamationTriangleIcon className="h-8 w-8 mx-auto mb-2" />
          <p className="text-sm">{housingError}</p>
        </div>
      </div>
    );
  }

  const limitStatus = getSearchLimitStatus();
  const leaseAlerts = getLeaseExpirationAlerts();

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 ${className}`}>
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <HomeIcon className="h-6 w-6 text-blue-600" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Housing Location</h3>
              {tierInfo && (
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getTierColor(tierInfo.current_tier)}`}>
                  {tierInfo.tier_name}
                </span>
              )}
            </div>
          </div>
          <button
            onClick={() => setShowUpgradeModal(true)}
            className="text-blue-600 hover:text-blue-700 text-sm font-medium flex items-center space-x-1"
          >
            <span>Upgrade</span>
            <ArrowUpRightIcon className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="p-6 space-y-6">
        {/* Lease Expiration Alerts */}
        {leaseAlerts.length > 0 && (
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
            <div className="flex items-start space-x-3">
              <CalendarIcon className="h-5 w-5 text-amber-600 mt-0.5" />
              <div>
                <h4 className="text-sm font-medium text-amber-800">Lease Alert</h4>
                <p className="text-sm text-amber-700 mt-1">
                  {leaseAlerts[0].message}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Search Limit Status */}
        {limitStatus && (
          <div className={`rounded-lg p-3 ${
            limitStatus.status === 'exceeded' ? 'bg-red-50 border border-red-200' :
            limitStatus.status === 'warning' ? 'bg-yellow-50 border border-yellow-200' :
            'bg-green-50 border border-green-200'
          }`}>
            <div className="flex items-center justify-between">
              <span className={`text-sm font-medium ${
                limitStatus.status === 'exceeded' ? 'text-red-800' :
                limitStatus.status === 'warning' ? 'text-yellow-800' :
                'text-green-800'
              }`}>
                {limitStatus.text}
              </span>
              {limitStatus.status !== 'unlimited' && (
                <button
                  onClick={() => setShowUpgradeModal(true)}
                  className="text-xs text-blue-600 hover:text-blue-700 font-medium"
                >
                  Upgrade for unlimited
                </button>
              )}
            </div>
          </div>
        )}

        {/* Recent Searches */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-sm font-medium text-gray-900">Recent Searches</h4>
            <button className="text-xs text-blue-600 hover:text-blue-700 font-medium">
              View all
            </button>
          </div>
          {housingSearches.length > 0 ? (
            <div className="space-y-2">
              {housingSearches.slice(0, 3).map((search) => (
                <div key={search.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <MapPinIcon className="h-4 w-4 text-gray-400" />
                    <div>
                      <p className="text-sm font-medium text-gray-900">
                        {search.search_criteria?.bedrooms ?? 'N/A'} bed • ${search.search_criteria?.max_rent?.toLocaleString() ?? 'N/A'}/mo
                      </p>
                      <p className="text-xs text-gray-500">
                        {search.search_criteria.zip_code} • {search.results_count} results
                      </p>
                    </div>
                  </div>
                  <span className="text-xs text-gray-400">
                    {formatDate(search.created_at)}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-4">
              <MapPinIcon className="h-8 w-8 text-gray-300 mx-auto mb-2" />
              <p className="text-sm text-gray-500">No recent searches</p>
              <button className="mt-2 text-xs text-blue-600 hover:text-blue-700 font-medium">
                Start searching
              </button>
            </div>
          )}
        </div>

        {/* Recent Scenarios */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-sm font-medium text-gray-900">Saved Scenarios</h4>
            <button className="text-xs text-blue-600 hover:text-blue-700 font-medium">
              View all
            </button>
          </div>
          {housingScenarios.length > 0 ? (
            <div className="space-y-2">
              {housingScenarios.map((scenario) => (
                <div key={scenario.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    {scenario.is_favorite && (
                      <StarIcon className="h-4 w-4 text-yellow-500" />
                    )}
                    <div>
                      <p className="text-sm font-medium text-gray-900">
                        {scenario.scenario_name}
                      </p>
                      <p className="text-xs text-gray-500">
                        Created {formatDate(scenario.created_at)}
                      </p>
                    </div>
                  </div>
                  <button className="text-xs text-gray-400 hover:text-gray-600">
                    View
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-4">
              <HomeIcon className="h-8 w-8 text-gray-300 mx-auto mb-2" />
              <p className="text-sm text-gray-500">No saved scenarios</p>
              <button className="mt-2 text-xs text-blue-600 hover:text-blue-700 font-medium">
                Create scenario
              </button>
            </div>
          )}
        </div>

        {/* Quick Actions */}
        <div className="pt-4 border-t border-gray-200">
          <div className="grid grid-cols-2 gap-3">
            <TierGate
              feature="optimal_location"
              fallback={
                <button 
                  onClick={() => setShowUpgradeModal(true)}
                  className="flex items-center justify-center space-x-2 p-3 bg-yellow-50 hover:bg-yellow-100 rounded-lg transition-colors"
                >
                  <PlusIcon className="h-4 w-4 text-yellow-600" />
                  <span className="text-sm font-medium text-yellow-600">Upgrade to Search</span>
                </button>
              }
            >
              <button 
                disabled={!canSearchHousing(housingSearches.length)}
                className={`flex items-center justify-center space-x-2 p-3 rounded-lg transition-colors ${
                  canSearchHousing(housingSearches.length)
                    ? 'bg-blue-50 hover:bg-blue-100'
                    : 'bg-gray-100 cursor-not-allowed'
                }`}
              >
                <PlusIcon className={`h-4 w-4 ${
                  canSearchHousing(housingSearches.length) ? 'text-blue-600' : 'text-gray-400'
                }`} />
                <span className={`text-sm font-medium ${
                  canSearchHousing(housingSearches.length) ? 'text-blue-600' : 'text-gray-400'
                }`}>
                  New Search
                </span>
              </button>
            </TierGate>
            
            <button className="flex items-center justify-center space-x-2 p-3 bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors">
              <ClockIcon className="h-4 w-4 text-gray-600" />
              <span className="text-sm font-medium text-gray-600">View History</span>
            </button>
          </div>
        </div>
      </div>

      {/* Upgrade Modal */}
      {showUpgradeModal && tierInfo && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
            <div className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Upgrade Your Plan
              </h3>
              <p className="text-sm text-gray-600 mb-6">
                Unlock unlimited housing searches and advanced features
              </p>
              
              <div className="space-y-3">
                {tierInfo.upgrade_options.map((option) => (
                  <div key={option.tier} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="font-medium text-gray-900">
                          {option.tier.replace('_', ' ').toUpperCase()}
                        </h4>
                        <p className="text-sm text-gray-600">{option.description}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-lg font-semibold text-gray-900">
                          ${option.price}/mo
                        </p>
                        <p className="text-xs text-gray-500">
                          +${option.price_difference}/mo
                        </p>
                      </div>
                    </div>
                    <button className="w-full mt-3 bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors">
                      Upgrade to {option.tier.replace('_', ' ').toUpperCase()}
                    </button>
                  </div>
                ))}
              </div>
              
              <button
                onClick={() => setShowUpgradeModal(false)}
                className="w-full mt-4 text-gray-600 hover:text-gray-800 py-2 px-4 rounded-lg border border-gray-300 hover:border-gray-400 transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default HousingLocationTile;
