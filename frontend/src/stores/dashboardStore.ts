import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { useCallback } from 'react';

// ========================================
// TYPES & INTERFACES
// ========================================

export interface HousingSearch {
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

export interface HousingScenario {
  id: number;
  scenario_name: string;
  housing_data: any;
  commute_data: any;
  financial_impact: any;
  is_favorite: boolean;
  created_at: string;
}

export interface LeaseInfo {
  id: string;
  property_address: string;
  lease_start_date: string;
  lease_end_date: string;
  monthly_rent: number;
  is_active: boolean;
  renewal_reminder_days: number;
}

export interface HousingAlert {
  id: string;
  type: 'lease_expiration' | 'new_opportunity' | 'market_change' | 'career_opportunity';
  title: string;
  message: string;
  severity: 'low' | 'medium' | 'high' | 'urgent';
  created_at: string;
  is_read: boolean;
  action_url?: string;
  expires_at?: string;
}

export interface HousingLocationState {
  recentSearches: HousingSearch[];
  recentScenarios: HousingScenario[];
  leaseInfo: LeaseInfo | null;
  alerts: HousingAlert[];
  loading: boolean;
  error: string | null;
  lastUpdated: Date;
  isLoadingHousing: boolean;
  housingDataFetched: boolean;
}

export interface DashboardState {
  activeTab: 'daily-outlook' | 'financial-forecast' | 'overview' | 'recommendations' | 'vehicles' | 'location' | 'analytics' | 'housing';
  riskLevel: 'secure' | 'watchful' | 'action_needed' | 'urgent';
  hasUnlockedRecommendations: boolean;
  emergencyMode: boolean;
  lastUpdated: Date;
  housing: HousingLocationState;
}

export interface DashboardActions {
  // Tab management
  setActiveTab: (tab: DashboardState['activeTab']) => void;
  
  // Risk management
  setRiskLevel: (level: DashboardState['riskLevel']) => void;
  setEmergencyMode: (mode: boolean) => void;
  setUnlockedRecommendations: (unlocked: boolean) => void;
  
  // Housing data management
  setHousingSearches: (searches: HousingSearch[]) => void;
  addHousingSearch: (search: HousingSearch) => void;
  setHousingScenarios: (scenarios: HousingScenario[]) => void;
  addHousingScenario: (scenario: HousingScenario) => void;
  updateHousingScenario: (id: number, updates: Partial<HousingScenario>) => void;
  deleteHousingScenario: (id: number) => void;
  
  // Lease management
  setLeaseInfo: (lease: LeaseInfo | null) => void;
  updateLeaseInfo: (updates: Partial<LeaseInfo>) => void;
  
  // Alert management
  setHousingAlerts: (alerts: HousingAlert[]) => void;
  addHousingAlert: (alert: HousingAlert) => void;
  markAlertAsRead: (alertId: string) => void;
  dismissAlert: (alertId: string) => void;
  clearAllAlerts: () => void;
  
  // Data fetching
  fetchHousingData: () => Promise<void>;
  refreshHousingData: () => Promise<void>;
  
  // Loading and error states
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  
  // Reset
  resetDashboard: () => void;
}

// ========================================
// STORE IMPLEMENTATION
// ========================================

const initialState: DashboardState = {
  activeTab: 'daily-outlook',
  riskLevel: 'secure',
  hasUnlockedRecommendations: false,
  emergencyMode: false,
  lastUpdated: new Date(),
  housing: {
    recentSearches: [],
    recentScenarios: [],
    leaseInfo: null,
    alerts: [],
    loading: false,
    error: null,
    lastUpdated: new Date(),
    isLoadingHousing: false,
    housingDataFetched: false,
  },
};

export const useDashboardStore = create<DashboardState & DashboardActions>()(
  persist(
    (set, get) => ({
      ...initialState,

      // Tab management
      setActiveTab: (tab) => set({ activeTab: tab }),

      // Risk management
      setRiskLevel: (level) => set({ riskLevel: level }),
      setEmergencyMode: (mode) => set({ emergencyMode: mode }),
      setUnlockedRecommendations: (unlocked) => set({ hasUnlockedRecommendations: unlocked }),

      // Housing data management
      setHousingSearches: (searches) => 
        set((state) => ({
          housing: {
            ...state.housing,
            recentSearches: searches,
            lastUpdated: new Date(),
          },
        })),

      addHousingSearch: (search) =>
        set((state) => ({
          housing: {
            ...state.housing,
            recentSearches: [search, ...state.housing.recentSearches].slice(0, 10), // Keep only last 10
            lastUpdated: new Date(),
          },
        })),

      setHousingScenarios: (scenarios) =>
        set((state) => ({
          housing: {
            ...state.housing,
            recentScenarios: scenarios,
            lastUpdated: new Date(),
          },
        })),

      addHousingScenario: (scenario) =>
        set((state) => ({
          housing: {
            ...state.housing,
            recentScenarios: [scenario, ...state.housing.recentScenarios],
            lastUpdated: new Date(),
          },
        })),

      updateHousingScenario: (id, updates) =>
        set((state) => ({
          housing: {
            ...state.housing,
            recentScenarios: state.housing.recentScenarios.map((scenario) =>
              scenario.id === id ? { ...scenario, ...updates } : scenario
            ),
            lastUpdated: new Date(),
          },
        })),

      deleteHousingScenario: (id) =>
        set((state) => ({
          housing: {
            ...state.housing,
            recentScenarios: state.housing.recentScenarios.filter((scenario) => scenario.id !== id),
            lastUpdated: new Date(),
          },
        })),

      // Lease management
      setLeaseInfo: (lease) =>
        set((state) => ({
          housing: {
            ...state.housing,
            leaseInfo: lease,
            lastUpdated: new Date(),
          },
        })),

      updateLeaseInfo: (updates) =>
        set((state) => ({
          housing: {
            ...state.housing,
            leaseInfo: state.housing.leaseInfo ? { ...state.housing.leaseInfo, ...updates } : null,
            lastUpdated: new Date(),
          },
        })),

      // Alert management
      setHousingAlerts: (alerts) =>
        set((state) => ({
          housing: {
            ...state.housing,
            alerts,
            lastUpdated: new Date(),
          },
        })),

      addHousingAlert: (alert) =>
        set((state) => ({
          housing: {
            ...state.housing,
            alerts: [alert, ...state.housing.alerts],
            lastUpdated: new Date(),
          },
        })),

      markAlertAsRead: (alertId) =>
        set((state) => ({
          housing: {
            ...state.housing,
            alerts: state.housing.alerts.map((alert) =>
              alert.id === alertId ? { ...alert, is_read: true } : alert
            ),
            lastUpdated: new Date(),
          },
        })),

      dismissAlert: (alertId) =>
        set((state) => ({
          housing: {
            ...state.housing,
            alerts: state.housing.alerts.filter((alert) => alert.id !== alertId),
            lastUpdated: new Date(),
          },
        })),

      clearAllAlerts: () =>
        set((state) => ({
          housing: {
            ...state.housing,
            alerts: [],
            lastUpdated: new Date(),
          },
        })),

      // Data fetching
      fetchHousingData: async () => {
        // Prevent multiple simultaneous calls
        const state = get();
        if (state.housing.isLoadingHousing) return;
        
        set((prevState) => ({
          housing: { ...prevState.housing, isLoadingHousing: true, loading: true, error: null },
        }));
        
        const token = localStorage.getItem('mingus_token');
        if (!token) {
          set((prevState) => ({
            housing: { ...prevState.housing, isLoadingHousing: false, loading: false },
          }));
          return;
        }

        const headers = {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        };

        // Helper that returns fallback on ANY error - no retry
        const safeFetch = async <T>(url: string, fallback: T): Promise<T> => {
          try {
            const response = await fetch(url, { headers });
            if (!response.ok) return fallback;
            const data = await response.json();
            return data.data || data || fallback;
          } catch {
            return fallback;
          }
        };

        const [searches, scenarios, leaseInfo, alerts] = await Promise.all([
          safeFetch('/api/housing/recent-searches', { searches: [] }),
          safeFetch('/api/housing/scenarios', { scenarios: [] }),
          safeFetch('/api/housing/lease-info', { lease_info: null }),
          safeFetch('/api/housing/alerts', { alerts: [] }),
        ]);

        set((prevState) => ({
          housing: {
            ...prevState.housing,
            recentSearches: searches.searches || [],
            recentScenarios: scenarios.scenarios || [],
            leaseInfo: leaseInfo.lease_info || null,
            alerts: alerts.alerts || [],
            isLoadingHousing: false,
            loading: false,
            error: null,
            housingDataFetched: true,
            lastUpdated: new Date(),
          },
        }));
      },

      refreshHousingData: async () => {
        const { fetchHousingData } = get();
        await fetchHousingData();
      },

      // Loading and error states
      setLoading: (loading) =>
        set((state) => ({
          housing: { ...state.housing, loading },
        })),

      setError: (error) =>
        set((state) => ({
          housing: { ...state.housing, error },
        })),

      // Reset
      resetDashboard: () => set(initialState),
    }),
    {
      name: 'mingus-dashboard-store',
      partialize: (state) => ({
        activeTab: state.activeTab,
        riskLevel: state.riskLevel,
        hasUnlockedRecommendations: state.hasUnlockedRecommendations,
        emergencyMode: state.emergencyMode,
        housing: {
          recentSearches: state.housing.recentSearches,
          recentScenarios: state.housing.recentScenarios,
          leaseInfo: state.housing.leaseInfo,
          alerts: state.housing.alerts,
        },
      }),
    }
  )
);

// ========================================
// SELECTORS
// ========================================

export const useDashboardSelectors = () => {
  const store = useDashboardStore();
  
  return {
    // Basic selectors
    activeTab: store.activeTab,
    riskLevel: store.riskLevel,
    emergencyMode: store.emergencyMode,
    hasUnlockedRecommendations: store.hasUnlockedRecommendations,
    
    // Housing selectors
    housingSearches: store.housing.recentSearches,
    housingScenarios: store.housing.recentScenarios,
    leaseInfo: store.housing.leaseInfo,
    housingAlerts: store.housing.alerts,
    unreadAlerts: store.housing.alerts.filter(alert => !alert.is_read),
    urgentAlerts: store.housing.alerts.filter(alert => alert.severity === 'urgent'),
    
    // Computed selectors
    hasLeaseExpiringSoon: () => {
      if (!store.housing.leaseInfo || !store.housing.leaseInfo.lease_end_date) return false;
      const leaseEnd = new Date(store.housing.leaseInfo.lease_end_date);
      const now = new Date();
      const daysUntilExpiry = Math.ceil((leaseEnd.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
      return daysUntilExpiry <= 60 && daysUntilExpiry > 0;
    },
    
    leaseExpirationDays: () => {
      if (!store.housing.leaseInfo || !store.housing.leaseInfo.lease_end_date) return null;
      const leaseEnd = new Date(store.housing.leaseInfo.lease_end_date);
      const now = new Date();
      return Math.ceil((leaseEnd.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
    },
    
    // Loading and error states
    housingLoading: store.housing.loading,
    housingError: store.housing.error,
    lastUpdated: store.housing.lastUpdated,
  };
};

// ========================================
// HOOKS FOR SPECIFIC FEATURES
// ========================================

export const useHousingNotifications = () => {
  const { addHousingAlert, markAlertAsRead, dismissAlert } = useDashboardStore();
  const { leaseInfo, hasLeaseExpiringSoon, leaseExpirationDays } = useDashboardSelectors();
  
  const checkLeaseExpiration = () => {
    if (hasLeaseExpiringSoon() && leaseInfo) {
      const days = leaseExpirationDays();
      if (days && days <= 60) {
        addHousingAlert({
          id: `lease-expiry-${leaseInfo.id}`,
          type: 'lease_expiration',
          title: 'Lease Expiration Alert',
          message: `Your lease expires in ${days} days. Consider starting your housing search.`,
          severity: days <= 30 ? 'urgent' : days <= 45 ? 'high' : 'medium',
          created_at: new Date().toISOString(),
          is_read: false,
          action_url: '/housing/search',
        });
      }
    }
  };
  
  const checkNewOpportunities = async () => {
    // This would typically check for new housing opportunities in saved search areas
    // For now, we'll simulate this
    try {
      const response = await fetch('/api/housing/new-opportunities', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('mingus_token')}`,
          'X-CSRF-Token': 'test-token',
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.opportunities && data.opportunities.length > 0) {
          data.opportunities.forEach((opportunity: any) => {
            addHousingAlert({
              id: `opportunity-${opportunity.id}`,
              type: 'new_opportunity',
              title: 'New Housing Opportunity',
              message: `New ${opportunity.property_type} found in ${opportunity.area} for $${opportunity.rent}/month`,
              severity: 'medium',
              created_at: new Date().toISOString(),
              is_read: false,
              action_url: `/housing/opportunity/${opportunity.id}`,
            });
          });
        }
      }
    } catch (error) {
      console.error('Error checking new opportunities:', error);
    }
  };
  
  return {
    checkLeaseExpiration,
    checkNewOpportunities,
    markAlertAsRead,
    dismissAlert,
  };
};

export const useHousingDataSync = () => {
  const { fetchHousingData, refreshHousingData } = useDashboardStore();
  const { checkLeaseExpiration, checkNewOpportunities } = useHousingNotifications();
  
  const syncAllHousingData = useCallback(async () => {
    await fetchHousingData();
    checkLeaseExpiration();
    await checkNewOpportunities();
  }, [fetchHousingData, checkLeaseExpiration, checkNewOpportunities]);
  
  return {
    syncAllHousingData,
    refreshHousingData,
  };
};
