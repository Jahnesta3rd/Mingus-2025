import React, { useState, useEffect } from 'react';
import { 
  Car, 
  Wrench, 
  DollarSign, 
  Calendar, 
  AlertTriangle, 
  TrendingUp,
  Plus,
  Settings,
  RefreshCw,
  Clock
} from 'lucide-react';
import { 
  Vehicle, 
  VehicleStats, 
  MaintenanceItem, 
  VehicleBudget, 
  QuickAction,
  VehicleDashboardData,
  VehicleDashboardState
} from '../types/vehicle';
import VehicleOverviewCard from './VehicleOverviewCard';
import UpcomingMaintenanceSection from './UpcomingMaintenanceSection';
import MonthlyBudgetDisplay from './MonthlyBudgetDisplay';
import VehicleQuickActions from './VehicleQuickActions';

interface VehicleDashboardProps {
  className?: string;
}

const VehicleDashboard: React.FC<VehicleDashboardProps> = ({ className = '' }) => {
  const [dashboardState, setDashboardState] = useState<VehicleDashboardState>({
    loading: true,
    error: null,
    lastUpdated: '',
    refreshInterval: 30000, // 30 seconds
    autoRefresh: true
  });

  const [dashboardData, setDashboardData] = useState<VehicleDashboardData>({
    vehicles: [],
    stats: {
      totalVehicles: 0,
      totalMileage: 0,
      averageMonthlyMiles: 0,
      totalMonthlyBudget: 0,
      upcomingMaintenanceCount: 0,
      overdueMaintenanceCount: 0
    },
    upcomingMaintenance: [],
    maintenancePredictions: [],
    budgets: [],
    recentExpenses: [],
    quickActions: []
  });

  useEffect(() => {
    fetchVehicleData();
    
    let interval: NodeJS.Timeout | null = null;
    if (dashboardState.autoRefresh) {
      interval = setInterval(fetchVehicleData, dashboardState.refreshInterval);
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [dashboardState.autoRefresh, dashboardState.refreshInterval]);

  const fetchVehicleData = async () => {
    try {
      setDashboardState(prev => ({ ...prev, loading: true, error: null }));

      const response = await fetch('/api/vehicles/dashboard', {
        headers: {
          'Authorization': `Bearer ${getAuthToken()}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch vehicle dashboard data');
      }

      const data = await response.json();
      setDashboardData(data);
      setDashboardState(prev => ({ 
        ...prev, 
        loading: false, 
        lastUpdated: new Date().toISOString() 
      }));

    } catch (err) {
      setDashboardState(prev => ({ 
        ...prev, 
        loading: false, 
        error: err instanceof Error ? err.message : 'Failed to load vehicle data' 
      }));
    }
  };

  const handleRefresh = () => {
    fetchVehicleData();
  };

  const handleAutoRefreshToggle = () => {
    setDashboardState(prev => ({ ...prev, autoRefresh: !prev.autoRefresh }));
  };

  if (dashboardState.loading && dashboardData.vehicles.length === 0) {
    return <VehicleDashboardSkeleton />;
  }

  if (dashboardState.error) {
    return (
      <div className={`bg-red-50 border border-red-200 rounded-lg p-6 ${className}`}>
        <div className="flex items-center gap-3 mb-4">
          <AlertTriangle className="h-6 w-6 text-red-600" />
          <h3 className="text-lg font-semibold text-red-900">Failed to Load Vehicle Dashboard</h3>
        </div>
        <p className="text-red-700 mb-4">{dashboardState.error}</p>
        <div className="flex gap-3">
          <button
            onClick={handleRefresh}
            className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
          >
            Try Again
          </button>
          <button
            onClick={handleAutoRefreshToggle}
            className="bg-red-100 hover:bg-red-200 text-red-700 px-4 py-2 rounded-lg font-medium transition-colors"
          >
            {dashboardState.autoRefresh ? 'Disable Auto-Refresh' : 'Enable Auto-Refresh'}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-blue-100 rounded-lg">
            <Car className="h-6 w-6 text-blue-600" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Vehicle Dashboard</h2>
            <p className="text-gray-600 text-sm">
              Manage your vehicles, maintenance, and budget
            </p>
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          {dashboardState.lastUpdated && (
            <div className="flex items-center gap-2 text-sm text-gray-500">
              <Clock className="h-4 w-4" />
              <span>Updated {formatLastUpdated(dashboardState.lastUpdated)}</span>
            </div>
          )}
          
          <button
            onClick={handleRefresh}
            disabled={dashboardState.loading}
            className="flex items-center gap-2 bg-gray-100 hover:bg-gray-200 text-gray-700 px-3 py-2 rounded-lg font-medium transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 ${dashboardState.loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          
          <button
            onClick={handleAutoRefreshToggle}
            className={`px-3 py-2 rounded-lg font-medium transition-colors ${
              dashboardState.autoRefresh 
                ? 'bg-blue-100 text-blue-700 hover:bg-blue-200' 
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Auto-refresh {dashboardState.autoRefresh ? 'ON' : 'OFF'}
          </button>
        </div>
      </div>

      {/* Overview Cards */}
      <div className="grid gap-6 lg:gap-8 lg:grid-cols-2">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Vehicle Overview</h3>
          <VehicleOverviewCard 
            vehicles={dashboardData.vehicles}
            stats={dashboardData.stats}
            loading={dashboardState.loading}
          />
        </div>
        
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
          <VehicleQuickActions 
            actions={dashboardData.quickActions}
            onActionClick={(actionId) => handleQuickAction(actionId)}
          />
        </div>
      </div>

      {/* Maintenance and Budget Section */}
      <div className="grid gap-6 lg:gap-8 lg:grid-cols-2">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Upcoming Maintenance</h3>
          <UpcomingMaintenanceSection 
            maintenanceItems={dashboardData.upcomingMaintenance}
            predictions={dashboardData.maintenancePredictions}
            loading={dashboardState.loading}
          />
        </div>
        
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Monthly Budget</h3>
          <MonthlyBudgetDisplay 
            budgets={dashboardData.budgets}
            recentExpenses={dashboardData.recentExpenses}
            loading={dashboardState.loading}
          />
        </div>
      </div>
    </div>
  );
};

// Loading Skeleton
const VehicleDashboardSkeleton: React.FC = () => {
  return (
    <div className="space-y-6">
      {/* Header Skeleton */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 bg-gray-200 rounded-lg animate-pulse" />
          <div>
            <div className="h-8 w-48 bg-gray-200 rounded animate-pulse mb-2" />
            <div className="h-4 w-64 bg-gray-200 rounded animate-pulse" />
          </div>
        </div>
        <div className="flex gap-3">
          <div className="h-10 w-20 bg-gray-200 rounded-lg animate-pulse" />
          <div className="h-10 w-24 bg-gray-200 rounded-lg animate-pulse" />
        </div>
      </div>

      {/* Cards Skeleton */}
      <div className="grid gap-6 lg:gap-8 lg:grid-cols-2">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="space-y-4">
            <div className="h-6 w-32 bg-gray-200 rounded animate-pulse" />
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <div className="space-y-4">
                <div className="h-4 w-full bg-gray-200 rounded animate-pulse" />
                <div className="h-4 w-3/4 bg-gray-200 rounded animate-pulse" />
                <div className="h-4 w-1/2 bg-gray-200 rounded animate-pulse" />
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// Helper Functions
const getAuthToken = (): string => {
  return localStorage.getItem('mingus_token') || '';
};

const formatLastUpdated = (timestamp: string): string => {
  const date = new Date(timestamp);
  const now = new Date();
  const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60));
  
  if (diffInMinutes < 1) {
    return 'just now';
  } else if (diffInMinutes < 60) {
    return `${diffInMinutes}m ago`;
  } else {
    return date.toLocaleTimeString();
  }
};

const handleQuickAction = (actionId: string) => {
  // Handle quick action clicks
  console.log('Quick action clicked:', actionId);
  // Implement navigation or action handling
};

export default VehicleDashboard;
