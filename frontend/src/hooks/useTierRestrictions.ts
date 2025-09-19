import { useState, useEffect, useCallback } from 'react';

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

interface TierRestrictions {
  tierInfo: TierInfo | null;
  loading: boolean;
  error: string | null;
  hasFeatureAccess: (feature: string) => boolean;
  canPerformAction: (action: string, currentCount: number) => boolean;
  getRemainingQuota: (action: string, currentCount: number) => number;
  refreshTierInfo: () => Promise<void>;
}

export const useTierRestrictions = (): TierRestrictions => {
  const [tierInfo, setTierInfo] = useState<TierInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchTierInfo = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch('/api/housing/tier-info', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'X-CSRF-Token': 'test-token'
        }
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch tier info: ${response.status}`);
      }

      const data = await response.json();
      if (data.success) {
        setTierInfo(data.data);
      } else {
        throw new Error(data.message || 'Failed to fetch tier information');
      }
    } catch (err) {
      console.error('Error fetching tier info:', err);
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, []);

  const hasFeatureAccess = useCallback((feature: string): boolean => {
    if (!tierInfo) return false;
    
    switch (feature) {
      case 'optimal_location':
        return tierInfo.has_optimal_location;
      case 'career_integration':
        return tierInfo.features.career_integration;
      case 'export_functionality':
        return tierInfo.features.export_functionality;
      case 'advanced_analytics':
        return tierInfo.features.advanced_analytics;
      default:
        return false;
    }
  }, [tierInfo]);

  const canPerformAction = useCallback((action: string, currentCount: number): boolean => {
    if (!tierInfo) return false;
    
    switch (action) {
      case 'housing_search':
        const searchLimit = tierInfo.features.housing_searches_per_month;
        return searchLimit === -1 || currentCount < searchLimit;
      case 'save_scenario':
        const scenarioLimit = tierInfo.features.scenarios_saved;
        return scenarioLimit === -1 || currentCount < scenarioLimit;
      default:
        return false;
    }
  }, [tierInfo]);

  const getRemainingQuota = useCallback((action: string, currentCount: number): number => {
    if (!tierInfo) return 0;
    
    switch (action) {
      case 'housing_search':
        const searchLimit = tierInfo.features.housing_searches_per_month;
        return searchLimit === -1 ? -1 : Math.max(0, searchLimit - currentCount);
      case 'save_scenario':
        const scenarioLimit = tierInfo.features.scenarios_saved;
        return scenarioLimit === -1 ? -1 : Math.max(0, scenarioLimit - currentCount);
      default:
        return 0;
    }
  }, [tierInfo]);

  const refreshTierInfo = useCallback(async () => {
    await fetchTierInfo();
  }, [fetchTierInfo]);

  useEffect(() => {
    fetchTierInfo();
  }, [fetchTierInfo]);

  return {
    tierInfo,
    loading,
    error,
    hasFeatureAccess,
    canPerformAction,
    getRemainingQuota,
    refreshTierInfo
  };
};

// Hook for specific housing feature restrictions
export const useHousingRestrictions = () => {
  const { tierInfo, hasFeatureAccess, canPerformAction, getRemainingQuota } = useTierRestrictions();
  
  const canSearchHousing = useCallback((currentSearches: number) => {
    return canPerformAction('housing_search', currentSearches);
  }, [canPerformAction]);
  
  const canSaveScenario = useCallback((currentScenarios: number) => {
    return canPerformAction('save_scenario', currentScenarios);
  }, [canPerformAction]);
  
  const canUseCareerIntegration = useCallback(() => {
    return hasFeatureAccess('career_integration');
  }, [hasFeatureAccess]);
  
  const canExportData = useCallback(() => {
    return hasFeatureAccess('export_functionality');
  }, [hasFeatureAccess]);
  
  const getSearchQuotaInfo = useCallback((currentSearches: number) => {
    if (!tierInfo) return { remaining: 0, limit: 0, unlimited: false };
    
    const limit = tierInfo.features.housing_searches_per_month;
    const remaining = getRemainingQuota('housing_search', currentSearches);
    
    return {
      remaining,
      limit,
      unlimited: limit === -1,
      used: currentSearches
    };
  }, [tierInfo, getRemainingQuota]);
  
  const getScenarioQuotaInfo = useCallback((currentScenarios: number) => {
    if (!tierInfo) return { remaining: 0, limit: 0, unlimited: false };
    
    const limit = tierInfo.features.scenarios_saved;
    const remaining = getRemainingQuota('save_scenario', currentScenarios);
    
    return {
      remaining,
      limit,
      unlimited: limit === -1,
      used: currentScenarios
    };
  }, [tierInfo, getRemainingQuota]);
  
  return {
    tierInfo,
    canSearchHousing,
    canSaveScenario,
    canUseCareerIntegration,
    canExportData,
    getSearchQuotaInfo,
    getScenarioQuotaInfo,
    hasOptimalLocation: hasFeatureAccess('optimal_location')
  };
};

// Component wrapper for tier-based feature gating
interface TierGateProps {
  feature: string;
  fallback?: React.ReactNode;
  children: React.ReactNode;
}

export const TierGate: React.FC<TierGateProps> = ({ feature, fallback, children }) => {
  const { hasFeatureAccess, loading } = useTierRestrictions();
  
  if (loading) {
    return <div className="animate-pulse bg-gray-200 rounded h-8 w-full"></div>;
  }
  
  if (!hasFeatureAccess(feature)) {
    return fallback ? <>{fallback}</> : null;
  }
  
  return <>{children}</>;
};

// Hook for upgrade prompts and tier management
export const useUpgradePrompts = () => {
  const { tierInfo, loading } = useTierRestrictions();
  
  const getUpgradePrompt = useCallback((feature: string) => {
    if (!tierInfo || loading) return null;
    
    const currentTier = tierInfo.current_tier;
    const upgradeOptions = tierInfo.upgrade_options;
    
    // Find the lowest tier that has the feature
    const requiredTier = upgradeOptions.find(option => {
      // This would need to be enhanced based on actual tier feature mapping
      return option.tier !== currentTier;
    });
    
    if (!requiredTier) return null;
    
    return {
      feature,
      currentTier,
      requiredTier: requiredTier.tier,
      upgradePrice: requiredTier.price_difference,
      description: requiredTier.description
    };
  }, [tierInfo, loading]);
  
  const shouldShowUpgradePrompt = useCallback((feature: string, usagePercentage: number = 0.8) => {
    if (!tierInfo) return false;
    
    // Show upgrade prompt when user is close to their limit
    const searchQuota = getSearchQuotaInfo(0);
    const scenarioQuota = getScenarioQuotaInfo(0);
    
    if (feature === 'housing_search' && !searchQuota.unlimited) {
      return (searchQuota.used / searchQuota.limit) >= usagePercentage;
    }
    
    if (feature === 'save_scenario' && !scenarioQuota.unlimited) {
      return (scenarioQuota.used / scenarioQuota.limit) >= usagePercentage;
    }
    
    return false;
  }, [tierInfo]);
  
  return {
    getUpgradePrompt,
    shouldShowUpgradePrompt,
    upgradeOptions: tierInfo?.upgrade_options || [],
    currentTier: tierInfo?.current_tier || 'budget'
  };
};

// Helper function to get search quota info (used in useUpgradePrompts)
const getSearchQuotaInfo = (currentSearches: number) => {
  // This would typically come from a context or be passed as a parameter
  // For now, return a mock structure
  return { remaining: 5, limit: 5, unlimited: false, used: currentSearches };
};

const getScenarioQuotaInfo = (currentScenarios: number) => {
  // This would typically come from a context or be passed as a parameter
  // For now, return a mock structure
  return { remaining: 3, limit: 3, unlimited: false, used: currentScenarios };
};
