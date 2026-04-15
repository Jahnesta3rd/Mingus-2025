import React, { useState, useEffect, useRef, lazy, Suspense } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import RiskStatusHero from '../components/RiskStatusHero';
import RecommendationTiers from '../components/RecommendationTiers';
import LocationIntelligenceMap from '../components/LocationIntelligenceMap';
import AnalyticsDashboard from '../components/AnalyticsDashboard';
import VehicleDashboard from '../components/VehicleDashboard';
import HousingLocationTile from '../components/HousingLocationTile';
import HousingNotificationSystem from '../components/HousingNotificationSystem';
import HousingProfileIntegration from '../components/HousingProfileIntegration';
import DashboardErrorBoundary from '../components/DashboardErrorBoundary';
import DashboardWellnessSection from '../components/DashboardWellnessSection';
import QuickActionsPanel from '../components/QuickActionsPanel';
import RecentActivityPanel from '../components/RecentActivityPanel';
import UnlockRecommendationsPanel from '../components/UnlockRecommendationsPanel';
import DashboardSkeleton from '../components/DashboardSkeleton';
import DailyOutlookCard from '../components/DailyOutlookCard';
import QuickSetupOverlay from '../components/QuickSetupOverlay';
import SpendingMilestonesWidget from '../components/SpendingMilestonesWidget';
import SpecialDatesWidget from '../components/SpecialDatesWidget';
import LifeLedgerErrorBoundary from '../components/LifeLedger/LifeLedgerErrorBoundary';
import LifeLedgerWidget from '../components/LifeLedger/LifeLedgerWidget';
import CorrelationWidget from '../components/LifeLedger/CorrelationWidget';
import UserProfile from '../components/UserProfile';
import FeatureRating from '../components/FeatureRating';
import { useAuth } from '../hooks/useAuth';
import { useAnalytics } from '../hooks/useAnalytics';
import { useDashboardStore, useDashboardSelectors } from '../stores/dashboardStore';

// Lazy load the full Daily Outlook component for performance
const DailyOutlook = lazy(() => import('../components/DailyOutlook'));
const MobileDailyOutlook = lazy(() => import('../components/MobileDailyOutlook'));

interface DashboardState {
  activeTab: 'daily-outlook' | 'overview' | 'recommendations' | 'location' | 'analytics' | 'housing' | 'vehicle' | 'life-ledger';
  riskLevel: 'secure' | 'watchful' | 'action_needed' | 'urgent';
  hasUnlockedRecommendations: boolean;
  emergencyMode: boolean;
  lastUpdated: Date;
  showFullDailyOutlook: boolean;
  isMobile: boolean;
}

const CareerProtectionDashboard: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const { user, isAuthenticated, loading: authLoading } = useAuth();
  const { trackPageView, trackInteraction } = useAnalytics();
  const [showProfileModal, setShowProfileModal] = useState(false);
  
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
    let localTab = storeActiveTab === 'vehicles' ? 'vehicle' : storeActiveTab;
    if (localTab === 'financial-forecast') {
      localTab = 'daily-outlook';
    }
    if (localTab !== dashboardState.activeTab) {
      setDashboardState(prev => ({ ...prev, activeTab: localTab as DashboardState['activeTab'] }));
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

  // Set page title
  useEffect(() => {
    document.title = 'Dashboard';
  }, []);

  // Wait for auth check (/api/auth/verify) before redirecting — avoids e2e race
  useEffect(() => {
    if (authLoading) return;
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }
  }, [authLoading, isAuthenticated, navigate]);

  // SINGLE useEffect that runs ONCE after auth is ready - all data fetching happens here
  useEffect(() => {
    if (authLoading || !isAuthenticated) return;
    if (hasInitializedRef.current) return;
    hasInitializedRef.current = true;

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
  }, [authLoading, isAuthenticated]); // Run when auth is ready, then once (ref guards re-run)
  
  useEffect(() => {
    const tab = searchParams.get('tab');
    if (tab === 'financial-forecast') {
      navigate('/dashboard/forecast', { replace: true });
      return;
    }
    if (tab === 'life-ledger') {
      setDashboardState((prev) => ({ ...prev, activeTab: 'life-ledger' }));
      setActiveTab('life-ledger');
    } else if (tab === 'housing') {
      setDashboardState((prev) => ({ ...prev, activeTab: 'housing' }));
      setActiveTab('housing');
    } else if (tab === 'vehicle' || tab === 'vehicles') {
      setDashboardState((prev) => ({ ...prev, activeTab: 'vehicle' }));
      setActiveTab('vehicles');
    } else {
      return;
    }
    const next = new URLSearchParams(searchParams);
    next.delete('tab');
    setSearchParams(next, { replace: true });
  }, [searchParams, setActiveTab, setSearchParams, navigate]);

  const handleTabChange = async (tab: DashboardState['activeTab']) => {
    setDashboardState(prev => ({ ...prev, activeTab: tab }));
    setActiveTab(tab === 'vehicle' ? 'vehicles' : tab);
    
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
      user_tier: (user as { tier?: string })?.tier,
      is_mobile: dashboardState.isMobile
    });
  };

  const handleCloseFullDailyOutlook = () => {
    setDashboardState(prev => ({ ...prev, showFullDailyOutlook: false }));
    trackInteraction('daily_outlook_close_full', {
      user_tier: (user as { tier?: string })?.tier,
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
                <Link
                  to="/dashboard/roster"
                  className="text-xs sm:text-sm text-[#6D28D9] hover:opacity-90 font-medium px-2 py-1 rounded hover:bg-[#EDE9FE] transition-colors whitespace-nowrap"
                >
                  My Roster
                </Link>
                <Link
                  to="/dashboard/spirit"
                  className="text-xs sm:text-sm text-purple-600 hover:text-purple-700 font-medium px-2 py-1 rounded hover:bg-purple-50 transition-colors whitespace-nowrap"
                >
                  Spirit &amp; Finance
                </Link>
                <button
                  onClick={() => setShowProfileModal(true)}
                  className="text-sm text-purple-600 hover:text-purple-700 font-medium px-2 py-1 rounded hover:bg-purple-50 transition-colors"
                >
                  <span className="hidden sm:inline">Edit Profile</span>
                  <span className="sm:hidden">👤</span>
                </button>
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

          <LifeLedgerErrorBoundary>
            <LifeLedgerWidget />
          </LifeLedgerErrorBoundary>

          <CorrelationWidget />

          {/* Wellness Section - Check-in reminder, score card, impact card */}
          <DashboardWellnessSection />
          
          {/* Tools sections (secondary to app shell navigation) */}
          <div className="flex flex-col gap-6 lg:flex-row lg:gap-8">
            <nav
              className="flex w-full flex-shrink-0 flex-col gap-1 lg:w-52 lg:border-r lg:border-[#E2E8F0] lg:pr-4"
              aria-label="Financial tools sections"
            >
              {[
                { id: 'daily-outlook', label: 'Daily Outlook', icon: '🌅' },
                { id: 'life-ledger', label: 'Life Ledger', icon: '💛' },
                { id: 'overview', label: 'Overview', icon: '📊' },
                {
                  id: 'recommendations',
                  label: 'Job Recommendations',
                  icon: '🎯',
                  locked: false,
                  badge: null,
                },
                { id: 'location', label: 'Location Intelligence', icon: '🗺️' },
                {
                  id: 'housing',
                  label: 'Housing Location',
                  icon: '🏠',
                  badge: unreadAlerts.length > 0 ? unreadAlerts.length.toString() : null,
                },
                { id: 'vehicle', label: 'Vehicle Status', icon: '🚗' },
                { id: 'analytics', label: 'Career Analytics', icon: '📈' },
              ].map((tab) => (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() =>
                    'locked' in tab && tab.locked
                      ? null
                      : handleTabChange(tab.id as DashboardState['activeTab'])
                  }
                  className={[
                    'flex w-full items-center gap-2 rounded-lg px-3 py-2.5 text-left text-sm font-medium transition-colors',
                    dashboardState.activeTab === tab.id
                      ? 'bg-[#5B2D8E] text-white'
                      : 'locked' in tab && tab.locked
                        ? 'cursor-not-allowed text-[#64748B] opacity-50'
                        : 'bg-transparent text-[#64748B] hover:bg-[#F8FAFC] hover:text-[#1E293B]',
                  ].join(' ')}
                  disabled={'locked' in tab ? tab.locked : false}
                >
                  <span className="text-base" aria-hidden>
                    {tab.icon}
                  </span>
                  <span className="min-w-0 flex-1">{tab.label}</span>
                  {tab.badge ? (
                    <span
                      className={
                        dashboardState.activeTab === tab.id
                          ? 'rounded-full bg-white/20 px-2 py-0.5 text-xs text-white tabular-nums'
                          : 'rounded-full bg-[#E2E8F0] px-2 py-0.5 text-xs font-medium text-[#64748B] tabular-nums'
                      }
                    >
                      {tab.badge}
                    </span>
                  ) : null}
                </button>
              ))}
              <p className="mt-2 px-3 text-xs text-[#64748B]">
                Full cash forecast lives under{' '}
                <Link to="/dashboard/forecast" className="font-medium text-[#6D28D9] hover:underline">
                  Forecast
                </Link>
                .
              </p>
            </nav>

            <div className="min-h-[600px] min-w-0 flex-1">
            {dashboardState.activeTab === 'daily-outlook' && (
              <div className="space-y-6">
                {/* Daily Outlook Card for Dashboard Overview */}
                <div className="grid gap-6 lg:grid-cols-2">
                  <div className="lg:col-span-1">
                    <DailyOutlookCard 
                      onViewFullOutlook={handleViewFullDailyOutlook}
                      compact={false}
                    />
                    <button
                      type="button"
                      onClick={() => handleTabChange('overview')}
                      className="mt-2 block text-sm text-purple-600 hover:underline cursor-pointer"
                    >
                      View all milestones →
                    </button>
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

            {dashboardState.activeTab === 'life-ledger' && (
              <LifeLedgerErrorBoundary>
                <LifeLedgerWidget className="mt-4" anchorSectionId={false} />
              </LifeLedgerErrorBoundary>
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

                <SpendingMilestonesWidget userId={user?.id ?? ''} className="mt-6" />
                <SpecialDatesWidget
                  userId={user?.id ?? ''}
                  userEmail={user?.email ?? ''}
                  onNavigateToForecast={() => navigate('/dashboard/forecast')}
                  className="mt-6"
                />
                
                {/* Bottom Row - Housing Location Tile */}
                <div>
                  <HousingLocationTile />
                </div>
              </div>
            )}
            
            {/*
              Job recommendations are fetched inside RecommendationTiers, not in this file.
              User current salary: use 0 here until wired; snapshot hook reads `current_salary` from
              GET /api/career/recommendations/:userId — TODO align tiers with that (or confirmed) field.
            */}
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

          <div className="mt-8 pt-4 border-t border-gray-100">
            <FeatureRating featureName="test_feature" />
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

      {/* Edit Profile Modal */}
      {showProfileModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-60 p-4">
          <div className="relative w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-xl">
            <button
              onClick={() => setShowProfileModal(false)}
              className="absolute top-4 right-4 z-10 text-white bg-gray-700 hover:bg-gray-600 rounded-full w-8 h-8 flex items-center justify-center text-lg font-bold"
              aria-label="Close profile editor"
            >
              ×
            </button>
            <UserProfile
              headerDisplayName={user?.name}
              showBetaBadge={user?.is_beta === true}
              onSave={(data) => {
                console.log('Profile updated:', data);
                setShowProfileModal(false);
              }}
              onComplete={() => setShowProfileModal(false)}
            />
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
