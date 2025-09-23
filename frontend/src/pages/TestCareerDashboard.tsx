import React, { useState, useEffect, lazy, Suspense } from 'react';
import { useNavigate } from 'react-router-dom';
import RiskStatusHero from '../components/RiskStatusHero';
import RecommendationTiers from '../components/RecommendationTiers';
import LocationIntelligenceMap from '../components/LocationIntelligenceMap';
import AnalyticsDashboard from '../components/AnalyticsDashboard';
import HousingLocationTile from '../components/HousingLocationTile';
import HousingNotificationSystem from '../components/HousingNotificationSystem';
import HousingProfileIntegration from '../components/HousingProfileIntegration';
import DashboardErrorBoundary from '../components/DashboardErrorBoundary';
import QuickActionsPanel from '../components/QuickActionsPanel';
import RecentActivityPanel from '../components/RecentActivityPanel';
import UnlockRecommendationsPanel from '../components/UnlockRecommendationsPanel';
import DashboardSkeleton from '../components/DashboardSkeleton';
import DailyOutlookCard from '../components/DailyOutlookCard';
import { useAnalytics } from '../hooks/useAnalytics';

// Lazy load the full Daily Outlook component for performance
const DailyOutlook = lazy(() => import('../components/DailyOutlook'));
const MobileDailyOutlook = lazy(() => import('../components/MobileDailyOutlook'));

interface DashboardState {
  activeTab: 'daily-outlook' | 'overview' | 'recommendations' | 'location' | 'analytics' | 'housing';
  riskLevel: 'secure' | 'watchful' | 'action_needed' | 'urgent';
  hasUnlockedRecommendations: boolean;
  emergencyMode: boolean;
  lastUpdated: Date;
  showFullDailyOutlook: boolean;
  isMobile: boolean;
}

const TestCareerDashboard: React.FC = () => {
  const navigate = useNavigate();
  const { trackPageView, trackInteraction } = useAnalytics();
  
  // Local state for Daily Outlook integration
  const [dashboardState, setDashboardState] = useState<DashboardState>({
    activeTab: 'daily-outlook', // Start with Daily Outlook as first tab
    riskLevel: 'watchful',
    hasUnlockedRecommendations: true,
    emergencyMode: false,
    lastUpdated: new Date(),
    showFullDailyOutlook: false,
    isMobile: window.innerWidth < 768
  });

  // Handle mobile detection
  useEffect(() => {
    const handleResize = () => {
      setDashboardState(prev => ({ ...prev, isMobile: window.innerWidth < 768 }));
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Track page view
  useEffect(() => {
    trackPageView('test_career_dashboard', {
      test_mode: true,
      active_tab: dashboardState.activeTab
    });
  }, [trackPageView, dashboardState.activeTab]);

  const handleTabChange = async (tab: DashboardState['activeTab']) => {
    setDashboardState(prev => ({ ...prev, activeTab: tab }));
    
    // Track tab interaction
    await trackInteraction('dashboard_tab_changed', {
      previous_tab: dashboardState.activeTab,
      new_tab: tab,
      risk_level: dashboardState.riskLevel,
      test_mode: true
    });
  };

  const handleViewFullDailyOutlook = () => {
    setDashboardState(prev => ({ ...prev, showFullDailyOutlook: true }));
    trackInteraction('daily_outlook_view_full', {
      is_mobile: dashboardState.isMobile,
      test_mode: true
    });
  };

  const handleCloseFullDailyOutlook = () => {
    setDashboardState(prev => ({ ...prev, showFullDailyOutlook: false }));
    trackInteraction('daily_outlook_close_full', {
      is_mobile: dashboardState.isMobile,
      test_mode: true
    });
  };

  const handleRiskLevelChange = (newRiskLevel: DashboardState['riskLevel']) => {
    setDashboardState(prev => ({ 
      ...prev, 
      riskLevel: newRiskLevel,
      emergencyMode: newRiskLevel === 'urgent'
    }));
  };

  return (
    <DashboardErrorBoundary>
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <div className="bg-white border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-16">
              <div className="flex items-center gap-4">
                <h1 className="text-xl font-semibold text-gray-900">Test Career Dashboard</h1>
                <div className="hidden sm:block">
                  <span className="text-sm text-gray-500">
                    Last updated: {dashboardState.lastUpdated.toLocaleTimeString()}
                  </span>
                </div>
                <div className="bg-yellow-100 text-yellow-800 px-2 py-1 rounded-full text-xs font-medium">
                  TEST MODE
                </div>
              </div>
              
              <div className="flex items-center gap-2 sm:gap-4">
                <button
                  onClick={() => navigate('/simple-test')}
                  className="text-sm text-blue-600 hover:text-blue-700 font-medium px-2 py-1 rounded hover:bg-blue-50 transition-colors"
                >
                  Back to Tests
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
                  { id: 'housing', label: 'Housing Location', shortLabel: 'Housing', icon: '🏠' },
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
                        riskLevel={dashboardState.riskLevel}
                        hasRecommendations={dashboardState.hasUnlockedRecommendations}
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
                  {/* Housing Location Tile - Full Width */}
                  <HousingLocationTile />
                  
                  {/* Additional Housing Content */}
                  <div className="grid gap-6 lg:grid-cols-2">
                    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                      <h3 className="text-lg font-semibold text-gray-900 mb-4">Housing Information</h3>
                      <p className="text-gray-500">Housing data would be displayed here in the real application.</p>
                    </div>
                    
                    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                      <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Housing Activity</h3>
                      <p className="text-gray-500">Recent housing activity would be displayed here.</p>
                    </div>
                  </div>
                  
                  {/* Profile Integration */}
                  <HousingProfileIntegration />
                </div>
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
      </div>
    </DashboardErrorBoundary>
  );
};

export default TestCareerDashboard;
