import React, { useState, useEffect, useRef, lazy, Suspense } from 'react';
import { useNavigate } from 'react-router-dom';
import RiskStatusHero from '../components/RiskStatusHero';
import RecommendationTiers from '../components/RecommendationTiers';
import LocationIntelligenceMap from '../components/LocationIntelligenceMap';
import AnalyticsDashboard from '../components/AnalyticsDashboard';
import VehicleDashboard from '../components/VehicleDashboard';
import HousingLocationTile from '../components/HousingLocationTile';
import HousingNotificationSystem from '../components/HousingNotificationSystem';
import HousingProfileIntegration from '../components/HousingProfileIntegration';
import DashboardErrorBoundary from '../components/DashboardErrorBoundary';
import QuickActionsPanel from '../components/QuickActionsPanel';
import RecentActivityPanel from '../components/RecentActivityPanel';
import UnlockRecommendationsPanel from '../components/UnlockRecommendationsPanel';
import DashboardSkeleton from '../components/DashboardSkeleton';
import DailyOutlookCard from '../components/DailyOutlookCard';
import QuickSetupOverlay from '../components/QuickSetupOverlay';
import { useAuth } from '../hooks/useAuth';
import { useAnalytics } from '../hooks/useAnalytics';
import { useDashboardStore, useDashboardSelectors } from '../stores/dashboardStore';

// Lazy load the full Daily Outlook component for performance
const DailyOutlook = lazy(() => import('../components/DailyOutlook'));
const MobileDailyOutlook = lazy(() => import('../components/MobileDailyOutlook'));

interface DashboardState {
  activeTab: 'daily-outlook' | 'overview' | 'recommendations' | 'location' | 'analytics' | 'housing' | 'vehicle';
  riskLevel: 'secure' | 'watchful' | 'action_needed' | 'urgent';
  hasUnlockedRecommendations: boolean;
  emergencyMode: boolean;
  lastUpdated: Date;
  showFullDailyOutlook: boolean;
  isMobile: boolean;
}

const CareerProtectionDashboard: React.FC = () => {
  const navigate = useNavigate();
  const { user, isAuthenticated } = useAuth();
  const { trackPageView, trackInteraction } = useAnalytics();
  
  // Use ref to track initialization - prevents double-initialization
  const hasInitializedRef = useRef(false);
  
  // Use dashboard store - DO NOT put these functions in useEffect dependencies
  const { 
    activeTab: storeActiveTab, 
    setActiveTab, 
    setRiskLevel, 
    setEmergencyMode, 
    setUnlockedRecommendations,
    fetchHousingData
  } = useDashboardStore();

  // Local state for Daily Outlook integration
  const [dashboardState, setDashboardState] = useState<DashboardState>({
    activeTab: storeActiveTab as DashboardState['activeTab'],
    riskLevel: 'watchful',
    hasUnlockedRecommendations: true,
    emergencyMode: false,
    lastUpdated: new Date(),
    showFullDailyOutlook: false,
    isMobile: window.innerWidth < 768
  });
  
  const { 
    housingSearches, 
    housingScenarios, 
    leaseInfo, 
    housingAlerts, 
    unreadAlerts, 
    urgentAlerts,
    hasLeaseExpiringSoon,
    housingLoading,
    housingError 
  } = useDashboardSelectors();
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showQuickSetup, setShowQuickSetup] = useState(false);

  // Sync local state with store when store changes (non-data-fetching, safe)
  useEffect(() => {
    if (storeActiveTab !== dashboardState.activeTab) {
      setDashboardState(prev => ({ ...prev, activeTab: storeActiveTab as DashboardState['activeTab'] }));
    }
  }, [storeActiveTab]); // Only depend on storeActiveTab, not dashboardState.activeTab

  // Handle mobile detection (non-data-fetching, safe)
  useEffect(() => {
    const handleResize = () => {
      setDashboardState(prev => ({ ...prev, isMobile: window.innerWidth < 768 }));
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // SINGLE useEffect that runs ONCE on mount - all data fetching happens here
  useEffect(() => {
    // Prevent double-initialization
    if (hasInitializedRef.current) return;
    hasInitializedRef.current = true;

    // Authentication check - redirect if not authenticated
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }

    // Set up periodic housing data sync every 5 minutes
    const interval = setInterval(() => {
      fetchHousingData();
    }, 5 * 60 * 1000);

    const initDashboard = async () => {
      setLoading(true);
      setError(null);
      
      try {
        // Track page view
        trackPageView('career_protection_dashboard', {
          user_id: user?.id,
          risk_level: dashboardState.activeTab,
          has_recommendations_unlocked: true
        });

        // Fetch dashboard state
        const dashboardResponse = await fetch('/api/risk/dashboard-state', {
          credentials: 'include'
        });
        
        if (dashboardResponse.ok) {
          const dashboardData = await dashboardResponse.json();
          
          // Update store with dashboard state
          setRiskLevel(dashboardData.current_risk_level || 'watchful');
          setUnlockedRecommendations(dashboardData.recommendations_unlocked || false);
          
          // Update local state
          setDashboardState(prev => ({
            ...prev,
            riskLevel: dashboardData.current_risk_level || 'watchful',
            hasUnlockedRecommendations: dashboardData.recommendations_unlocked || false,
            emergencyMode: dashboardData.current_risk_level === 'urgent'
          }));
        }

        // Check setup status
        try {
          const setupResponse = await fetch('/api/profile/setup-status', {
            credentials: 'include'
          });
          
          if (setupResponse.ok) {
            const setupData = await setupResponse.json();
            if (!setupData.setupCompleted) {
              setShowQuickSetup(true);
            }
          }
        } catch (setupError) {
          // Fail silently if endpoint doesn't exist yet
          console.debug('Setup status check failed:', setupError);
        }

        // Fetch housing data (using store function)
        await fetchHousingData();
        
      } catch (err) {
        console.error('Dashboard initialization error:', err);
        setError(err instanceof Error ? err.message : 'Failed to load dashboard');
      } finally {
        setLoading(false);
      }
    };

    initDashboard();

    // Cleanup interval on unmount
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // EMPTY dependency array - runs once on mount only
  
  const handleTabChange = async (tab: DashboardState['activeTab']) => {
    setDashboardState(prev => ({ ...prev, activeTab: tab }));
    setActiveTab(tab);
    
    // Track tab interaction (non-blocking)
    trackInteraction('dashboard_tab_changed', {
      previous_tab: dashboardState.activeTab,
      new_tab: tab,
      risk_level: dashboardState.riskLevel
    }).catch(err => console.error('Failed to track tab change:', err));
  };

  const handleViewFullDailyOutlook = () => {
    setDashboardState(prev => ({ ...prev, showFullDailyOutlook: true }));
    trackInteraction('daily_outlook_view_full', {
      user_tier: user?.tier,
      is_mobile: dashboardState.isMobile
    });
  };

  const handleCloseFullDailyOutlook = () => {
    setDashboardState(prev => ({ ...prev, showFullDailyOutlook: false }));
    trackInteraction('daily_outlook_close_full', {
      user_tier: user?.tier,
      is_mobile: dashboardState.isMobile
    });
  };
  
  const handleRiskLevelChange = (newRiskLevel: DashboardState['riskLevel']) => {
    setDashboardState(prev => ({ 
      ...prev, 
      riskLevel: newRiskLevel,
      emergencyMode: newRiskLevel === 'urgent'
    }));
  };
  
  const handleEmergencyUnlock = () => {
    setDashboardState(prev => ({ 
      ...prev, 
      hasUnlockedRecommendations: true,
      emergencyMode: false
    }));
  };
  
  // Loading state
  if (loading) {
    return <DashboardSkeleton />;
  }
  
  // Error state
  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-xl shadow-lg p-8 text-center max-w-md">
          <div className="text-red-500 mb-4">
            <svg className="h-12 w-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Dashboard Unavailable</h3>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={() => {
              hasInitializedRef.current = false;
              window.location.reload();
            }}
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg font-medium transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }
  
  // Emergency mode overlay
  if (dashboardState.emergencyMode) {
    return (
      <EmergencyModeInterface
        onEmergencyUnlock={handleEmergencyUnlock}
        onContinueToNormal={() => setDashboardState(prev => ({ ...prev, emergencyMode: false }))}
      />
    );
  }
  
  return (
    <DashboardErrorBoundary>
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <div className="bg-white border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-16">
              <div className="flex items-center gap-4">
                {/* Logo */}
                <div className="flex items-center space-x-3">
                  <div className="flex-shrink-0">
                    <img 
                      src="/mingus-logo.png" 
                      alt="Mingus" 
                      className="h-8 w-auto object-contain"
                    />
                  </div>
                  <h1 className="text-xl font-semibold text-gray-900">Dashboard</h1>
                </div>
                <div className="hidden sm:block">
                  <span className="text-sm text-gray-500">
                    Last updated: {dashboardState.lastUpdated.toLocaleTimeString()}
                  </span>
                </div>
              </div>
              
              <div className="flex items-center gap-2 sm:gap-4">
                <HousingNotificationSystem />
                <button
                  onClick={() => {
                    fetchHousingData().catch(err => console.error('Failed to refresh:', err));
                  }}
                  className="text-sm text-blue-600 hover:text-blue-700 font-medium px-2 py-1 rounded hover:bg-blue-50 transition-colors"
                >
                  <span className="hidden sm:inline">Refresh</span>
                  <span className="sm:hidden">↻</span>
                </button>
                
                {/* Risk Level Indicator */}
                <div className={`
                  px-2 sm:px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wide
                  ${dashboardState.riskLevel === 'secure' ? 'bg-green-100 text-green-800' : ''}
                  ${dashboardState.riskLevel === 'watchful' ? 'bg-yellow-100 text-yellow-800' : ''}
                  ${dashboardState.riskLevel === 'action_needed' ? 'bg-orange-100 text-orange-800' : ''}
                  ${dashboardState.riskLevel === 'urgent' ? 'bg-red-100 text-red-800' : ''}
                `}>
                  <span className="hidden sm:inline">{dashboardState.riskLevel.replace('_', ' ')}</span>
                  <span className="sm:hidden">{dashboardState.riskLevel.charAt(0).toUpperCase()}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      
      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="space-y-8">
          
          {/* Risk Status Hero - Always Visible */}
          <RiskStatusHero 
            onRiskLevelChange={handleRiskLevelChange}
          />
          
          {/* Tab Navigation */}
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-2 sm:space-x-8 overflow-x-auto">
              {[
                { id: 'daily-outlook', label: 'Daily Outlook', icon: '🌅', shortLabel: 'Outlook' },
                { id: 'overview', label: 'Overview', icon: '📊', shortLabel: 'Overview' },
                { 
                  id: 'recommendations', 
                  label: 'Job Recommendations', 
                  shortLabel: 'Jobs',
                  icon: '🎯',
                  locked: false,
                  badge: null
                },
                { id: 'location', label: 'Location Intelligence', shortLabel: 'Location', icon: '🗺️' },
                { id: 'housing', label: 'Housing Location', shortLabel: 'Housing', icon: '🏠', badge: unreadAlerts.length > 0 ? unreadAlerts.length.toString() : null },
                { id: 'vehicle', label: 'Vehicle Status', shortLabel: 'Vehicle', icon: '🚗' },
                { id: 'analytics', label: 'Career Analytics', shortLabel: 'Analytics', icon: '📈' }
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => tab.locked ? null : handleTabChange(tab.id as any)}
                  className={`
                    relative py-2 px-1 border-b-2 font-medium text-sm whitespace-nowrap flex items-center gap-1 sm:gap-2 flex-shrink-0
                    ${dashboardState.activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : tab.locked
                        ? 'border-transparent text-gray-400 cursor-not-allowed'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }
                  `}
                  disabled={tab.locked}
                >
                  <span className="text-base sm:text-sm">{tab.icon}</span>
                  <span className="hidden sm:inline">{tab.label}</span>
                  <span className="sm:hidden">{tab.shortLabel}</span>
                  {tab.badge && (
                    <span className="ml-1 sm:ml-2 bg-gray-200 text-gray-600 text-xs px-1 sm:px-2 py-0.5 rounded-full">
                      {tab.badge}
                    </span>
                  )}
                </button>
              ))}
            </nav>
          </div>
          
          {/* Tab Content */}
          <div className="min-h-[600px]">
            {dashboardState.activeTab === 'daily-outlook' && (
              <div className="space-y-6">
                {/* Daily Outlook Card for Dashboard Overview */}
                <div className="grid gap-6 lg:grid-cols-2">
                  <div className="lg:col-span-1">
                    <DailyOutlookCard 
                      onViewFullOutlook={handleViewFullDailyOutlook}
                      compact={false}
                    />
                  </div>
                  <div className="lg:col-span-1">
                    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                      <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
                      <QuickActionsPanel 
                        riskLevel={dashboardState.riskLevel}
                        hasRecommendations={dashboardState.hasUnlockedRecommendations}
                      />
                    </div>
                  </div>
                </div>
                
                {/* Recent Activity */}
                <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h3>
                  <RecentActivityPanel />
                </div>
              </div>
            )}

            {dashboardState.activeTab === 'overview' && (
              <div className="space-y-6">
                {/* Top Row - Quick Actions and Recent Activity */}
                <div className="grid gap-6 lg:gap-8 lg:grid-cols-2">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
                    <QuickActionsPanel 
                      riskLevel="watchful"
                      hasRecommendations={true}
                    />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h3>
                    <RecentActivityPanel />
                  </div>
                </div>
                
                {/* Bottom Row - Housing Location Tile */}
                <div>
                  <HousingLocationTile />
                </div>
              </div>
            )}
            
            {dashboardState.activeTab === 'recommendations' && (
              <RecommendationTiers />
            )}
            
            {dashboardState.activeTab === 'location' && (
              <LocationIntelligenceMap />
            )}
            
            {dashboardState.activeTab === 'housing' && (
              <div className="space-y-6">
                {/* Housing Alerts */}
                {urgentAlerts.length > 0 && (
                  <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                    <h3 className="text-lg font-semibold text-red-800 mb-2">Urgent Housing Alerts</h3>
                    <div className="space-y-2">
                      {urgentAlerts.map((alert) => (
                        <div key={alert.id} className="flex items-center justify-between p-3 bg-red-100 rounded-lg">
                          <div>
                            <p className="font-medium text-red-800">{alert.title}</p>
                            <p className="text-sm text-red-700">{alert.message}</p>
                          </div>
                          {alert.action_url && (
                            <button className="text-sm bg-red-600 text-white px-3 py-1 rounded hover:bg-red-700">
                              View
                            </button>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                
                {/* Housing Location Tile - Full Width */}
                <HousingLocationTile />
                
                {/* Additional Housing Content */}
                <div className="grid gap-6 lg:grid-cols-2">
                  <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Lease Information</h3>
                    {leaseInfo ? (
                      <div className="space-y-3">
                        <div>
                          <p className="text-sm text-gray-600">Property Address</p>
                          <p className="font-medium text-gray-900">{leaseInfo.property_address ?? 'N/A'}</p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-600">Monthly Rent</p>
                          <p className="font-medium text-gray-900">
                            ${leaseInfo?.monthly_rent?.toLocaleString() ?? 'N/A'}
                          </p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-600">Lease End Date</p>
                          <p className="font-medium text-gray-900">
                            {leaseInfo?.lease_end_date 
                              ? new Date(leaseInfo.lease_end_date).toLocaleDateString()
                              : 'N/A'}
                            {hasLeaseExpiringSoon() && (
                              <span className="ml-2 text-red-600 text-sm font-medium">
                                (Expires Soon!)
                              </span>
                            )}
                          </p>
                        </div>
                      </div>
                    ) : (
                      <p className="text-gray-500">No lease information available</p>
                    )}
                  </div>
                  
                  <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Housing Activity</h3>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-600">Recent Searches</span>
                        <span className="font-medium text-gray-900">{housingSearches.length}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-600">Saved Scenarios</span>
                        <span className="font-medium text-gray-900">{housingScenarios.length}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-600">Unread Alerts</span>
                        <span className="font-medium text-gray-900">{unreadAlerts.length}</span>
                      </div>
                    </div>
                  </div>
                </div>
                
                {/* Profile Integration */}
                <HousingProfileIntegration />
              </div>
            )}
            
            {dashboardState.activeTab === 'vehicle' && (
              <VehicleDashboard />
            )}
            
            {dashboardState.activeTab === 'analytics' && (
              <AnalyticsDashboard />
            )}
          </div>
          
        </div>
      </div>

      {/* Full Daily Outlook Modal/Overlay */}
      {dashboardState.showFullDailyOutlook && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
            <div className="flex items-center justify-between p-4 border-b border-gray-200">
              <h2 className="text-xl font-semibold text-gray-900">Daily Outlook</h2>
              <button
                onClick={handleCloseFullDailyOutlook}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                aria-label="Close"
              >
                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="overflow-y-auto max-h-[calc(90vh-80px)]">
              <Suspense fallback={
                <div className="p-6">
                  <div className="animate-pulse space-y-4">
                    <div className="h-6 bg-gray-200 rounded w-1/3"></div>
                    <div className="h-16 bg-gray-200 rounded"></div>
                    <div className="h-4 bg-gray-200 rounded w-2/3"></div>
                  </div>
                </div>
              }>
                {dashboardState.isMobile ? (
                  <MobileDailyOutlook 
                    onClose={handleCloseFullDailyOutlook}
                    isFullScreen={true}
                  />
                ) : (
                  <DailyOutlook />
                )}
              </Suspense>
            </div>
          </div>
        </div>
      )}
      <QuickSetupOverlay
        isOpen={showQuickSetup}
        onClose={() => setShowQuickSetup(false)}
        onComplete={() => setShowQuickSetup(false)}
      />
    </div>
    </DashboardErrorBoundary>
  );
};

// Emergency Mode Interface
const EmergencyModeInterface: React.FC<{
  onEmergencyUnlock: () => void;
  onContinueToNormal: () => void;
}> = ({ onEmergencyUnlock, onContinueToNormal }) => {
  return (
    <div className="fixed inset-0 bg-red-600 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl p-8 max-w-md text-center shadow-2xl">
        <div className="text-red-600 mb-6">
          <svg className="h-16 w-16 mx-auto animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
        </div>
        
        <h2 className="text-2xl font-bold text-gray-900 mb-4">
          High Career Risk Detected
        </h2>
        
        <p className="text-gray-600 mb-6">
          Our analysis indicates immediate attention needed for your career security. 
          We're unlocking emergency job recommendations to help protect your future.
        </p>
        
        <div className="space-y-3">
          <button
            onClick={onEmergencyUnlock}
            className="w-full bg-red-600 hover:bg-red-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors"
          >
            Access Emergency Recommendations
          </button>
          
          <button
            onClick={onContinueToNormal}
            className="w-full bg-gray-200 hover:bg-gray-300 text-gray-700 font-medium py-3 px-6 rounded-lg transition-colors"
          >
            Continue to Dashboard
          </button>
        </div>
      </div>
    </div>
  );
};

export default CareerProtectionDashboard;
