import React from 'react';
import { 
  Plus, 
  Car, 
  Wrench, 
  DollarSign, 
  FileText, 
  Settings,
  Calendar,
  TrendingUp,
  AlertTriangle,
  MapPin,
  Users
} from 'lucide-react';
import { QuickAction } from '../types/vehicle';

interface VehicleQuickActionsProps {
  actions: QuickAction[];
  onActionClick: (actionId: string) => void;
}

const VehicleQuickActions: React.FC<VehicleQuickActionsProps> = ({ 
  actions, 
  onActionClick 
}) => {
  const defaultActions: QuickAction[] = [
    {
      id: 'add_vehicle',
      title: 'Add Vehicle',
      description: 'Register a new vehicle to your account',
      icon: 'Car',
      color: 'blue',
      enabled: true,
      href: '/vehicles/add'
    },
    {
      id: 'record_maintenance',
      title: 'Record Maintenance',
      description: 'Log completed maintenance or repairs',
      icon: 'Wrench',
      color: 'green',
      enabled: true,
      href: '/maintenance/record'
    },
    {
      id: 'add_expense',
      title: 'Add Expense',
      description: 'Track vehicle-related expenses',
      icon: 'DollarSign',
      color: 'purple',
      enabled: true,
      href: '/expenses/add'
    },
    {
      id: 'schedule_service',
      title: 'Schedule Service',
      description: 'Book upcoming maintenance appointments',
      icon: 'Calendar',
      color: 'orange',
      enabled: true,
      href: '/maintenance/schedule'
    },
    {
      id: 'view_reports',
      title: 'View Reports',
      description: 'Access detailed vehicle analytics',
      icon: 'TrendingUp',
      color: 'blue',
      enabled: true,
      href: '/vehicles/reports'
    },
    {
      id: 'emergency_contact',
      title: 'Emergency Contact',
      description: 'Quick access to roadside assistance',
      icon: 'AlertTriangle',
      color: 'red',
      enabled: true,
      href: '/emergency'
    }
  ];

  const displayActions = actions.length > 0 ? actions : defaultActions;

  const getIconComponent = (iconName: string) => {
    const iconMap = {
      'Car': Car,
      'Wrench': Wrench,
      'DollarSign': DollarSign,
      'FileText': FileText,
      'Settings': Settings,
      'Calendar': Calendar,
      'TrendingUp': TrendingUp,
      'AlertTriangle': AlertTriangle,
      'MapPin': MapPin,
      'Users': Users,
      'Plus': Plus
    };
    
    return iconMap[iconName as keyof typeof iconMap] || Car;
  };

  const getColorClasses = (color: string, enabled: boolean) => {
    if (!enabled) {
      return 'bg-gray-100 text-gray-400 cursor-not-allowed border-gray-200';
    }

    const colorMap = {
      blue: 'bg-blue-50 text-blue-700 hover:bg-blue-100 border-blue-200',
      green: 'bg-green-50 text-green-700 hover:bg-green-100 border-green-200',
      purple: 'bg-purple-50 text-purple-700 hover:bg-purple-100 border-purple-200',
      orange: 'bg-orange-50 text-orange-700 hover:bg-orange-100 border-orange-200',
      red: 'bg-red-50 text-red-700 hover:bg-red-100 border-red-200',
      gray: 'bg-gray-50 text-gray-700 hover:bg-gray-100 border-gray-200'
    };

    return colorMap[color as keyof typeof colorMap] || colorMap.gray;
  };

  const getIconColorClasses = (color: string, enabled: boolean) => {
    if (!enabled) {
      return 'bg-gray-100 text-gray-400';
    }

    const colorMap = {
      blue: 'bg-blue-100 text-blue-600',
      green: 'bg-green-100 text-green-600',
      purple: 'bg-purple-100 text-purple-600',
      orange: 'bg-orange-100 text-orange-600',
      red: 'bg-red-100 text-red-600',
      gray: 'bg-gray-100 text-gray-600'
    };

    return colorMap[color as keyof typeof colorMap] || colorMap.gray;
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      <div className="grid gap-3">
        {displayActions.map((action) => {
          const IconComponent = getIconComponent(action.icon);
          return (
            <button
              key={action.id}
              onClick={() => action.enabled && onActionClick(action.id)}
              className={`
                flex items-center gap-3 p-4 rounded-lg border transition-all duration-200
                ${getColorClasses(action.color, action.enabled)}
                ${action.enabled ? 'hover:shadow-sm cursor-pointer' : 'cursor-not-allowed'}
              `}
              disabled={!action.enabled}
            >
              <div className={`p-2 rounded-lg flex-shrink-0 ${
                getIconColorClasses(action.color, action.enabled)
              }`}>
                <IconComponent className="h-5 w-5" />
              </div>
              
              <div className="flex-1 min-w-0 text-left">
                <h5 className={`font-medium text-sm ${
                  action.enabled ? 'text-gray-900' : 'text-gray-400'
                }`}>
                  {action.title}
                </h5>
                <p className={`text-xs mt-0.5 ${
                  action.enabled ? 'text-gray-600' : 'text-gray-400'
                }`}>
                  {action.description}
                </p>
              </div>
              
              {!action.enabled && (
                <div className="text-xs text-gray-400 font-medium flex-shrink-0">
                  Coming Soon
                </div>
              )}
            </button>
          );
        })}
      </div>

      {/* Quick Stats */}
      <div className="mt-6 pt-4 border-t border-gray-200">
        <h5 className="font-semibold text-gray-900 mb-3">Quick Stats</h5>
        <div className="grid grid-cols-2 gap-3">
          <QuickStatCard
            title="Total Vehicles"
            value="2"
            icon={<Car className="h-4 w-4" />}
            color="blue"
          />
          <QuickStatCard
            title="This Month"
            value="$450"
            icon={<DollarSign className="h-4 w-4" />}
            color="green"
          />
        </div>
      </div>

      {/* Emergency Actions */}
      <div className="mt-6 pt-4 border-t border-gray-200">
        <h5 className="font-semibold text-gray-900 mb-3">Emergency</h5>
        <div className="space-y-2">
          <button className="w-full bg-red-600 hover:bg-red-700 text-white py-2 px-4 rounded-lg font-medium transition-colors text-sm flex items-center justify-center gap-2">
            <AlertTriangle className="h-4 w-4" />
            Roadside Assistance
          </button>
          <button className="w-full bg-red-100 hover:bg-red-200 text-red-700 py-2 px-4 rounded-lg font-medium transition-colors text-sm">
            Emergency Contact
          </button>
        </div>
      </div>
    </div>
  );
};

// Quick Stat Card Component
const QuickStatCard: React.FC<{
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
    <div className="p-3 bg-gray-50 rounded-lg">
      <div className="flex items-center justify-between mb-1">
        <div className={`p-1 rounded-lg ${colorClasses[color]}`}>
          {icon}
        </div>
        <span className="text-lg font-bold text-gray-900">{value}</span>
      </div>
      <p className="text-xs text-gray-600">{title}</p>
    </div>
  );
};

export default VehicleQuickActions;
