import React, { useState, useEffect, useRef, lazy, Suspense } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import RecommendationTiers from '../components/RecommendationTiers';
import HousingNotificationSystem from '../components/HousingNotificationSystem';
import DashboardErrorBoundary from '../components/DashboardErrorBoundary';
import DashboardWellnessSection from '../components/DashboardWellnessSection';
import DashboardSkeleton from '../components/DashboardSkeleton';
import QuickSetupOverlay from '../components/QuickSetupOverlay';
import SpendingMilestonesWidget from '../components/SpendingMilestonesWidget';
import SpecialDatesWidget from '../components/SpecialDatesWidget';
import TodayTab from '../components/TodayTab';
import FinancialForecastTab from '../components/FinancialForecastTab';
import type { AuthUserTier } from '../hooks/useAuth';
import { useImportantDateModal } from '../context/ImportantDateModalContext';
import LifeLedgerErrorBoundary from '../components/LifeLedger/LifeLedgerErrorBoundary';
import LifeLedgerWidget from '../components/LifeLedger/LifeLedgerWidget';
import CorrelationWidget from '../components/LifeLedger/CorrelationWidget';
import UserProfile from '../components/UserProfile';
import BugReportButton from '../components/BugReportButton';
import FeatureRating from '../components/FeatureRating';
import { useAuth } from '../hooks/useAuth';
import { useAnalytics } from '../hooks/useAnalytics';
import { useDashboardStore } from '../stores/dashboardStore';

// Lazy load the full Daily Outlook component for performance
const DailyOutlook = lazy(() => import('../components/DailyOutlook'));
const MobileDailyOutlook = lazy(() => import('../components/MobileDailyOutlook'));

type MainTabId = 'today' | 'forecast' | 'plans' | 'discover' | 'you';

interface DashboardState {
  activeTab: MainTabId;
  riskLevel: 'secure' | 'watchful' | 'action_needed' | 'urgent';
  hasUnlockedRecommendations: boolean;
  emergencyMode: boolean;
  lastUpdated: Date;
  showFullDailyOutlook: boolean;
  isMobile: boolean;
}

type LegacyStoreTab =
  | 'daily-outlook'
  | 'financial-forecast'
  | 'overview'
  | 'recommendations'
  | 'vehicles'
  | 'location'
  | 'analytics'
  | 'housing'
  | 'life-ledger';

function storeTabToMainTab(storeTab: string): MainTabId {
  switch (storeTab) {
    case 'financial-forecast':
      return 'forecast';
    case 'recommendations':
      return 'discover';
    case 'overview':
      return 'plans';
    case 'location':
    case 'analytics':
      return 'discover';
    case 'daily-outlook':
    case 'vehicles':
    case 'vehicle':
    case 'life-ledger':
    case 'housing':
    default:
      return 'today';
  }
}

function mainTabToStoreTab(tab: MainTabId): LegacyStoreTab {
  switch (tab) {
    case 'forecast':
      return 'financial-forecast';
    case 'plans':
      return 'overview';
    case 'discover':
      return 'recommendations';
    case 'you':
      return 'overview';
    case 'today':
    default:
      return 'daily-outlook';
  }
}

function legacyQueryTabToMainTab(tab: string): MainTabId | null {
  switch (tab) {
    case 'daily-outlook':
    case 'vehicle':
    case 'vehicles':
      return 'today';
    case 'financial-forecast':
      return 'forecast';
    case 'recommendations':
    case 'job-recommendations':
      return 'discover';
    case 'overview':
      return 'plans';
    case 'life-ledger':
    case 'housing':
      return 'today';
    case 'location':
    case 'analytics':
      return 'discover';
    default:
      return null;
  }
}

function forecastTabTier(tier: AuthUserTier | null): 'budget' | 'mid' | 'professional' {
  if (tier === 'professional') return 'professional';
  if (tier === 'mid_tier') return 'mid';
  return 'budget';
}

const BOTTOM_NAV_TABS: { id: MainTabId; label: string }[] = [
  { id: 'today', label: 'Today' },
  { id: 'forecast', label: 'Forecast' },
  { id: 'plans', label: 'Plans' },
  { id: 'discover', label: 'Discover' },
  { id: 'you', label: 'You' },
];

const MINGUS_PURPLE = '#5B2D8E';
const INK_SOFT = '#8A8580';
const LINE = '#E8E1F0';
const WHISPER_PURPLE = '#FAF5FF';

// Pre-beta: suppress vestigial Quick Personalization popup (#106).
// Root cause is a legacy /api/profile/setup-status definition that doesn't
// reflect the F1-F3.7 modular onboarding architecture; reconciling that
// belongs to the #99 sprint. Until then, do not open the overlay.
const SUPPRESS_QUICK_SETUP_PREBETA = true;

const CareerProtectionDashboard: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const { user, userTier, isAuthenticated, loading: authLoading } = useAuth();
  const { openAddImportantDate, importantDatesRefreshKey } = useImportantDateModal();
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
    activeTab: storeTabToMainTab(storeActiveTab),
    riskLevel: 'watchful',
    hasUnlockedRecommendations: true,
    emergencyMode: false,
    lastUpdated: new Date(),
    showFullDailyOutlook: false,
    isMobile: window.innerWidth < 768
  });
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showQuickSetup, setShowQuickSetup] = useState(false);

  // Sync local state with store when store changes (non-data-fetching, safe)
  useEffect(() => {
    const localTab = storeTabToMainTab(storeActiveTab);
    if (localTab !== dashboardState.activeTab) {
      setDashboardState((prev) => ({ ...prev, activeTab: localTab }));
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
            if (!setupData.setupCompleted && !SUPPRESS_QUICK_SETUP_PREBETA) {
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
    const editProfile = searchParams.get('editProfile') === '1';
    if (!tab && !editProfile) return;

    if (editProfile) {
      setShowProfileModal(true);
      setDashboardState((prev) => ({ ...prev, activeTab: 'you' }));
      setActiveTab(mainTabToStoreTab('you'));
    } else if (tab) {
      const mainTab = legacyQueryTabToMainTab(tab);
      if (mainTab) {
        setDashboardState((prev) => ({ ...prev, activeTab: mainTab }));
        setActiveTab(mainTabToStoreTab(mainTab));
      }
    }

    const next = new URLSearchParams(searchParams);
    if (tab) next.delete('tab');
    if (editProfile) next.delete('editProfile');
    setSearchParams(next, { replace: true });
  }, [searchParams, setActiveTab, setSearchParams]);

  const handleTabChange = async (tab: MainTabId) => {
    setDashboardState((prev) => ({ ...prev, activeTab: tab }));
    setActiveTab(mainTabToStoreTab(tab));
    
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
      <div className="min-h-screen bg-gray-50 pb-16">
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
                <BugReportButton />
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
      <div className="mx-auto max-w-7xl space-y-8 px-4 py-6 sm:px-6 lg:px-8">
        <LifeLedgerErrorBoundary>
          <LifeLedgerWidget />
        </LifeLedgerErrorBoundary>

        <CorrelationWidget />

        <DashboardWellnessSection />

        <div className="min-h-[calc(100vh-8rem)] min-w-0">
          {dashboardState.activeTab === 'today' && (
            <TodayTab
              userEmail={user?.email ?? ''}
              userTier={userTier ?? 'budget'}
            />
          )}

          {dashboardState.activeTab === 'forecast' && (
            <FinancialForecastTab
              userEmail={user?.email ?? ''}
              userTier={forecastTabTier(userTier)}
              className="mt-0"
            />
          )}

          {dashboardState.activeTab === 'plans' && (
            <div className="space-y-6">
              <SpendingMilestonesWidget userId={user?.id ?? ''} className="mt-0" />
              <SpecialDatesWidget
                userId={user?.id ?? ''}
                userEmail={user?.email ?? ''}
                onNavigateToForecast={() => handleTabChange('forecast')}
                onRequestAddDate={openAddImportantDate}
                importantDatesRefreshKey={importantDatesRefreshKey}
                className="mt-6"
              />
            </div>
          )}

          {dashboardState.activeTab === 'discover' && (
            <RecommendationTiers userTier={userTier} userId={user?.id} />
          )}

          {dashboardState.activeTab === 'you' && (
            <div
              className="flex min-h-[calc(100vh-12rem)] flex-1 items-center justify-center rounded-xl"
              style={{ backgroundColor: WHISPER_PURPLE }}
            >
              <p className="text-center text-base font-medium" style={{ color: MINGUS_PURPLE }}>
                You — profile and settings coming soon
              </p>
            </div>
          )}
        </div>

        <div className="mt-8 border-t border-gray-100 pt-4">
          <FeatureRating featureName="test_feature" />
        </div>
      </div>

      {/* 5-tab bottom navigation (#99 D1) */}
      <nav
        className="fixed bottom-0 left-0 right-0 z-40 border-t bg-white"
        style={{ borderColor: LINE, height: '64px' }}
        aria-label="Dashboard sections"
      >
        <div className="mx-auto flex h-full max-w-7xl items-stretch justify-around px-2">
          {BOTTOM_NAV_TABS.map((tab) => {
            const isActive = dashboardState.activeTab === tab.id;
            const color = isActive ? MINGUS_PURPLE : INK_SOFT;
            const userInitial =
              user?.name?.trim()?.[0]?.toUpperCase() ??
              user?.email?.trim()?.[0]?.toUpperCase() ??
              null;

            return (
              <button
                key={tab.id}
                type="button"
                onClick={() => void handleTabChange(tab.id)}
                className="flex min-w-0 flex-1 flex-col items-center justify-center gap-1 px-1"
                aria-current={isActive ? 'page' : undefined}
              >
                {tab.id === 'today' && (
                  <svg
                    width="22"
                    height="22"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke={color}
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    aria-hidden
                  >
                    <path d="M3 10.5 12 3l9 7.5V21a1 1 0 0 1-1 1h-5v-7H9v7H4a1 1 0 0 1-1-1z" />
                  </svg>
                )}
                {tab.id === 'forecast' && (
                  <svg
                    width="22"
                    height="22"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke={color}
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    aria-hidden
                  >
                    <path d="M3 3v18h18" />
                    <path d="m7 14 4-4 4 4 5-6" />
                  </svg>
                )}
                {tab.id === 'plans' && (
                  <svg
                    width="22"
                    height="22"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke={color}
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    aria-hidden
                  >
                    <rect x="3" y="4" width="18" height="18" rx="2" />
                    <path d="M16 2v4M8 2v4M3 10h18" />
                    <path d="m9 15 2 2 4-4" />
                  </svg>
                )}
                {tab.id === 'discover' && (
                  <svg
                    width="22"
                    height="22"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke={color}
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    aria-hidden
                  >
                    <circle cx="11" cy="11" r="7" />
                    <path d="m20 20-3.5-3.5" />
                  </svg>
                )}
                {tab.id === 'you' &&
                  (userInitial ? (
                    <span
                      className="flex h-[22px] w-[22px] items-center justify-center rounded-full text-[11px] font-semibold leading-none"
                      style={{
                        color: isActive ? '#fff' : INK_SOFT,
                        backgroundColor: isActive ? MINGUS_PURPLE : 'transparent',
                        border: `2px solid ${color}`,
                      }}
                      aria-hidden
                    >
                      {userInitial}
                    </span>
                  ) : (
                    <svg
                      width="22"
                      height="22"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke={color}
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      aria-hidden
                    >
                      <circle cx="12" cy="8" r="4" />
                      <path d="M4 20c0-4 4-6 8-6s8 2 8 6" />
                    </svg>
                  ))}
                <span
                  className="truncate"
                  style={{
                    color,
                    fontSize: '10px',
                    fontWeight: 600,
                    letterSpacing: '0.04em',
                  }}
                >
                  {tab.label}
                </span>
              </button>
            );
          })}
        </div>
      </nav>

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
