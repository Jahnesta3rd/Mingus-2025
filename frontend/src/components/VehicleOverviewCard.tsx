import React from 'react';
import { 
  Car, 
  Gauge, 
  DollarSign, 
  AlertTriangle, 
  TrendingUp,
  Calendar,
  MapPin
} from 'lucide-react';
import { Vehicle, VehicleStats } from '../types/vehicle';

interface VehicleOverviewCardProps {
  vehicles: Vehicle[];
  stats: VehicleStats;
  loading?: boolean;
}

const VehicleOverviewCard: React.FC<VehicleOverviewCardProps> = ({ 
  vehicles, 
  stats, 
  loading = false 
}) => {
  if (loading) {
    return <VehicleOverviewSkeleton />;
  }

  if (vehicles.length === 0) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="text-center py-8">
          <Car className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">No Vehicles Added</h3>
          <p className="text-gray-600 text-sm mb-4">
            Add your first vehicle to start tracking maintenance and budget.
          </p>
          <button className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition-colors">
            Add Vehicle
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      {/* Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <StatCard
          title="Total Vehicles"
          value={stats.totalVehicles.toString()}
          icon={<Car className="h-5 w-5" />}
          color="blue"
        />
        <StatCard
          title="Total Mileage"
          value={`${(stats.totalMileage / 1000).toFixed(0)}k`}
          icon={<Gauge className="h-5 w-5" />}
          color="green"
        />
        <StatCard
          title="Monthly Budget"
          value={`$${stats.totalMonthlyBudget.toLocaleString()}`}
          icon={<DollarSign className="h-5 w-5" />}
          color="purple"
        />
        <StatCard
          title="Upcoming Service"
          value={stats.upcomingMaintenanceCount.toString()}
          icon={<Calendar className="h-5 w-5" />}
          color="orange"
        />
      </div>

      {/* Vehicle List */}
      <div className="space-y-3">
        <h4 className="font-semibold text-gray-900 text-sm">Your Vehicles</h4>
        {vehicles.map((vehicle) => (
          <VehicleItem key={vehicle.id} vehicle={vehicle} />
        ))}
      </div>

      {/* Alerts */}
      {stats.overdueMaintenanceCount > 0 && (
        <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-3">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-red-600" />
            <span className="text-sm font-medium text-red-900">
              {stats.overdueMaintenanceCount} overdue maintenance item{stats.overdueMaintenanceCount > 1 ? 's' : ''}
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

// Stat Card Component
const StatCard: React.FC<{
  title: string;
  value: string;
  icon: React.ReactNode;
  color: 'blue' | 'green' | 'purple' | 'orange' | 'red';
}> = ({ title, value, icon, color }) => {
  const colorClasses = {
    blue: 'bg-blue-100 text-blue-600',
    green: 'bg-green-100 text-green-600',
    purple: 'bg-purple-100 text-purple-600',
    orange: 'bg-orange-100 text-orange-600',
    red: 'bg-red-100 text-red-600'
  };

  return (
    <div className="bg-gray-50 rounded-lg p-3">
      <div className="flex items-center justify-between mb-2">
        <div className={`p-1.5 rounded-lg ${colorClasses[color]}`}>
          {icon}
        </div>
        <span className="text-lg font-bold text-gray-900">{value}</span>
      </div>
      <p className="text-xs text-gray-600">{title}</p>
    </div>
  );
};

// Vehicle Item Component
const VehicleItem: React.FC<{ vehicle: Vehicle }> = ({ vehicle }) => {
  const formatVehicleName = (vehicle: Vehicle) => {
    return `${vehicle.year} ${vehicle.make} ${vehicle.model}${vehicle.trim ? ` ${vehicle.trim}` : ''}`;
  };

  const getMileageStatus = (mileage: number) => {
    if (mileage < 50000) return { color: 'text-green-600', label: 'Low' };
    if (mileage < 100000) return { color: 'text-yellow-600', label: 'Medium' };
    return { color: 'text-orange-600', label: 'High' };
  };

  const mileageStatus = getMileageStatus(vehicle.currentMileage);

  return (
    <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
      <div className="flex items-center gap-3">
        <div className="p-2 bg-blue-100 rounded-lg">
          <Car className="h-4 w-4 text-blue-600" />
        </div>
        <div>
          <h5 className="font-medium text-gray-900 text-sm">
            {formatVehicleName(vehicle)}
          </h5>
          <div className="flex items-center gap-2 text-xs text-gray-600">
            <Gauge className="h-3 w-3" />
            <span>{vehicle.currentMileage.toLocaleString()} miles</span>
            <span className={`font-medium ${mileageStatus.color}`}>
              ({mileageStatus.label} mileage)
            </span>
          </div>
        </div>
      </div>
      
      <div className="flex items-center gap-2">
        {vehicle.assignedMsa && (
          <div className="flex items-center gap-1 text-xs text-gray-500">
            <MapPin className="h-3 w-3" />
            <span>{vehicle.assignedMsa}</span>
          </div>
        )}
        <button className="text-blue-600 hover:text-blue-700 text-xs font-medium">
          View Details
        </button>
      </div>
    </div>
  );
};

// Loading Skeleton
const VehicleOverviewSkeleton: React.FC = () => {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      {/* Stats Grid Skeleton */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="bg-gray-50 rounded-lg p-3">
            <div className="flex items-center justify-between mb-2">
              <div className="h-6 w-6 bg-gray-200 rounded-lg animate-pulse" />
              <div className="h-6 w-12 bg-gray-200 rounded animate-pulse" />
            </div>
            <div className="h-3 w-16 bg-gray-200 rounded animate-pulse" />
          </div>
        ))}
      </div>

      {/* Vehicle List Skeleton */}
      <div className="space-y-3">
        <div className="h-4 w-24 bg-gray-200 rounded animate-pulse" />
        {[1, 2].map((i) => (
          <div key={i} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <div className="flex items-center gap-3">
              <div className="h-8 w-8 bg-gray-200 rounded-lg animate-pulse" />
              <div className="space-y-1">
                <div className="h-4 w-32 bg-gray-200 rounded animate-pulse" />
                <div className="h-3 w-24 bg-gray-200 rounded animate-pulse" />
              </div>
            </div>
            <div className="h-4 w-20 bg-gray-200 rounded animate-pulse" />
          </div>
        ))}
      </div>
    </div>
  );
};

export default VehicleOverviewCard;
