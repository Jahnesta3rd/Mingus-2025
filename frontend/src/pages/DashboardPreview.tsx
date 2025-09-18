import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import RiskStatusHero from '../components/RiskStatusHero';
import RecommendationTiers from '../components/RecommendationTiers';
import LocationIntelligenceMap from '../components/LocationIntelligenceMap';
import AnalyticsDashboard from '../components/AnalyticsDashboard';
import DashboardErrorBoundary from '../components/DashboardErrorBoundary';
import QuickActionsPanel from '../components/QuickActionsPanel';
import RecentActivityPanel from '../components/RecentActivityPanel';
import UnlockRecommendationsPanel from '../components/UnlockRecommendationsPanel';
import { useAnalytics } from '../hooks/useAnalytics';

interface DashboardState {
  activeTab: 'overview' | 'recommendations' | 'location' | 'analytics';
  riskLevel: 'secure' | 'watchful' | 'action_needed' | 'urgent';
  hasUnlockedRecommendations: boolean;
  emergencyMode: boolean;
  lastUpdated: Date;
}

const DashboardPreview: React.FC = () => {
  const navigate = useNavigate();
  const { trackPageView, trackInteraction } = useAnalytics();
  
  // Sample data for preview
  const [dashboardState, setDashboardState] = useState<DashboardState>({
    activeTab: 'overview',
    riskLevel: 'action_needed',
    hasUnlockedRecommendations: true,
    emergencyMode: false,
    lastUpdated: new Date()
  });
  
  const handleTabChange = async (tab: DashboardState['activeTab']) => {
    setDashboardState(prev => ({ ...prev, activeTab: tab }));
    
    await trackInteraction('dashboard_tab_changed', {
      previous_tab: dashboardState.activeTab,
      new_tab: tab,
      risk_level: dashboardState.riskLevel
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

  // Track page view
  React.useEffect(() => {
    trackPageView('dashboard_preview', {
      risk_level: dashboardState.riskLevel,
      has_recommendations_unlocked: dashboardState.hasUnlockedRecommendations
    });
  }, []);

  return (
    <DashboardErrorBoundary>
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <div className="bg-white border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-16">
              <div className="flex items-center gap-4">
                <h1 className="text-xl font-semibold text-gray-900">Career Protection Dashboard</h1>
                <div className="hidden sm:block">
                  <span className="text-sm text-gray-500">
                    Last updated: {dashboardState.lastUpdated.toLocaleTimeString()}
                  </span>
                </div>
                <div className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full font-medium">
                  PREVIEW MODE
                </div>
              </div>
              
              <div className="flex items-center gap-2 sm:gap-4">
                <button
                  onClick={() => navigate('/')}
                  className="text-sm text-blue-600 hover:text-blue-700 font-medium px-2 py-1 rounded hover:bg-blue-50 transition-colors"
                >
                  <span className="hidden sm:inline">Back to Home</span>
                  <span className="sm:hidden">← Home</span>
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
                  { id: 'overview', label: 'Overview', icon: '📊', shortLabel: 'Overview' },
                  { 
                    id: 'recommendations', 
                    label: 'Job Recommendations', 
                    shortLabel: 'Jobs',
                    icon: '🎯',
                    locked: !dashboardState.hasUnlockedRecommendations,
                    badge: dashboardState.hasUnlockedRecommendations ? null : 'Locked'
                  },
                  { id: 'location', label: 'Location Intelligence', shortLabel: 'Location', icon: '🗺️' },
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
              {dashboardState.activeTab === 'overview' && (
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
              )}
              
              {dashboardState.activeTab === 'recommendations' && (
                dashboardState.hasUnlockedRecommendations ? (
                  <RecommendationTiers />
                ) : (
                  <UnlockRecommendationsPanel riskLevel={dashboardState.riskLevel} />
                )
              )}
              
              {dashboardState.activeTab === 'location' && (
                <LocationIntelligenceMap />
              )}
              
              {dashboardState.activeTab === 'analytics' && (
                <AnalyticsDashboard />
              )}
            </div>
            
          </div>
        </div>
      </div>
    </DashboardErrorBoundary>
  );
};

export default DashboardPreview;

