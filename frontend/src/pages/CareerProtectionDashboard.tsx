import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import RiskStatusHero from '../components/RiskStatusHero';
import RecommendationTiers from '../components/RecommendationTiers';
import LocationIntelligenceMap from '../components/LocationIntelligenceMap';
import AnalyticsDashboard from '../components/AnalyticsDashboard';
import DashboardErrorBoundary from '../components/DashboardErrorBoundary';
import QuickActionsPanel from '../components/QuickActionsPanel';
import RecentActivityPanel from '../components/RecentActivityPanel';
import UnlockRecommendationsPanel from '../components/UnlockRecommendationsPanel';
import DashboardSkeleton from '../components/DashboardSkeleton';
import { useAuth } from '../hooks/useAuth';
import { useAnalytics } from '../hooks/useAnalytics';

interface DashboardState {
  activeTab: 'overview' | 'recommendations' | 'location' | 'analytics';
  riskLevel: 'secure' | 'watchful' | 'action_needed' | 'urgent';
  hasUnlockedRecommendations: boolean;
  emergencyMode: boolean;
  lastUpdated: Date;
}

const CareerProtectionDashboard: React.FC = () => {
  const navigate = useNavigate();
  const { user, isAuthenticated } = useAuth();
  const { trackPageView, trackInteraction } = useAnalytics();
  
  const [dashboardState, setDashboardState] = useState<DashboardState>({
    activeTab: 'overview',
    riskLevel: 'secure',
    hasUnlockedRecommendations: false,
    emergencyMode: false,
    lastUpdated: new Date()
  });
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Authentication check
  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }
    
    initializeDashboard();
  }, [isAuthenticated]);
  
  // Track page view
  useEffect(() => {
    trackPageView('career_protection_dashboard', {
      user_id: user?.id,
      risk_level: dashboardState.riskLevel,
      has_recommendations_unlocked: dashboardState.hasUnlockedRecommendations
    });
  }, []);
  
  const initializeDashboard = async () => {
    try {
      setLoading(true);
      
      // Fetch user's current state
      const response = await fetch('/api/risk/dashboard-state', {
        headers: {
          'Authorization': `Bearer ${user?.token}`
        }
      });
      
      if (!response.ok) {
        throw new Error('Failed to load dashboard data');
      }
      
      const data = await response.json();
      
      setDashboardState({
        activeTab: 'overview',
        riskLevel: data.current_risk_level,
        hasUnlockedRecommendations: data.recommendations_unlocked,
        emergencyMode: data.current_risk_level === 'urgent',
        lastUpdated: new Date()
      });
      
      // If emergency mode, show emergency interface
      if (data.current_risk_level === 'urgent') {
        setDashboardState(prev => ({ ...prev, emergencyMode: true }));
      }
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      console.error('Dashboard initialization failed:', err);
    } finally {
      setLoading(false);
    }
  };
  
  const handleTabChange = async (tab: DashboardState['activeTab']) => {
    setDashboardState(prev => ({ ...prev, activeTab: tab }));
    
    // Track tab interaction
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
            onClick={initializeDashboard}
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
                <h1 className="text-xl font-semibold text-gray-900">Career Protection</h1>
                <div className="hidden sm:block">
                  <span className="text-sm text-gray-500">
                    Last updated: {dashboardState.lastUpdated.toLocaleTimeString()}
                  </span>
                </div>
              </div>
              
              <div className="flex items-center gap-2 sm:gap-4">
                <button
                  onClick={initializeDashboard}
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
