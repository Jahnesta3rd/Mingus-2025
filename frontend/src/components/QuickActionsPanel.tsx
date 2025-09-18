import React from 'react';
import { 
  Target, 
  MapPin, 
  TrendingUp, 
  Shield, 
  AlertTriangle, 
  Users,
  FileText,
  Settings
} from 'lucide-react';

interface QuickActionsPanelProps {
  riskLevel: 'secure' | 'watchful' | 'action_needed' | 'urgent';
  hasRecommendations: boolean;
}

const QuickActionsPanel: React.FC<QuickActionsPanelProps> = ({ 
  riskLevel, 
  hasRecommendations 
}) => {
  const getRiskConfig = (level: string) => {
    const configs = {
      secure: {
        color: 'green',
        icon: Shield,
        primaryAction: 'Explore Growth',
        secondaryAction: 'Update Profile'
      },
      watchful: {
        color: 'yellow',
        icon: AlertTriangle,
        primaryAction: 'View Strategies',
        secondaryAction: 'Market Analysis'
      },
      action_needed: {
        color: 'orange',
        icon: Target,
        primaryAction: 'Protection Plan',
        secondaryAction: 'Emergency Prep'
      },
      urgent: {
        color: 'red',
        icon: AlertTriangle,
        primaryAction: 'Emergency Actions',
        secondaryAction: 'Quick Apply'
      }
    };
    
    return configs[level as keyof typeof configs] || configs.secure;
  };

  const config = getRiskConfig(riskLevel);
  const IconComponent = config.icon;

  const actions = [
    {
      id: 'recommendations',
      title: hasRecommendations ? 'View Job Recommendations' : 'Unlock Recommendations',
      description: hasRecommendations 
        ? 'Explore personalized job opportunities' 
        : 'Complete assessment to unlock recommendations',
      icon: Target,
      color: 'blue',
      enabled: hasRecommendations,
      href: hasRecommendations ? '/recommendations' : '/assessment'
    },
    {
      id: 'location',
      title: 'Location Intelligence',
      description: 'Analyze job markets and opportunities by location',
      icon: MapPin,
      color: 'purple',
      enabled: true,
      href: '/location'
    },
    {
      id: 'analytics',
      title: 'Career Analytics',
      description: 'View detailed career insights and trends',
      icon: TrendingUp,
      color: 'green',
      enabled: true,
      href: '/analytics'
    },
    {
      id: 'profile',
      title: 'Update Profile',
      description: 'Keep your information current for better matches',
      icon: Users,
      color: 'gray',
      enabled: true,
      href: '/profile'
    },
    {
      id: 'resume',
      title: 'Resume Builder',
      description: 'Create or update your professional resume',
      icon: FileText,
      color: 'indigo',
      enabled: true,
      href: '/resume'
    },
    {
      id: 'settings',
      title: 'Account Settings',
      description: 'Manage your preferences and notifications',
      icon: Settings,
      color: 'gray',
      enabled: true,
      href: '/settings'
    }
  ];

  const getColorClasses = (color: string, enabled: boolean) => {
    if (!enabled) {
      return 'bg-gray-100 text-gray-400 cursor-not-allowed';
    }

    const colorMap = {
      blue: 'bg-blue-50 text-blue-700 hover:bg-blue-100 border-blue-200',
      purple: 'bg-purple-50 text-purple-700 hover:bg-purple-100 border-purple-200',
      green: 'bg-green-50 text-green-700 hover:bg-green-100 border-green-200',
      gray: 'bg-gray-50 text-gray-700 hover:bg-gray-100 border-gray-200',
      indigo: 'bg-indigo-50 text-indigo-700 hover:bg-indigo-100 border-indigo-200'
    };

    return colorMap[color as keyof typeof colorMap] || colorMap.gray;
  };

  const getRiskColorClasses = (color: string) => {
    const colorMap = {
      green: 'bg-green-50 border-green-200',
      yellow: 'bg-yellow-50 border-yellow-200',
      orange: 'bg-orange-50 border-orange-200',
      red: 'bg-red-50 border-red-200'
    };

    return colorMap[color as keyof typeof colorMap] || colorMap.green;
  };

  return (
    <div className="space-y-4">
      {/* Risk Level Alert */}
      <div className={`${getRiskColorClasses(config.color)} rounded-lg p-3 sm:p-4`}>
        <div className="flex items-start gap-3">
          <IconComponent className={`h-5 w-5 text-${config.color}-600 flex-shrink-0 mt-0.5`} />
          <div className="min-w-0 flex-1">
            <h4 className={`font-semibold text-${config.color}-900 text-sm sm:text-base`}>
              {config.primaryAction}
            </h4>
            <p className={`text-xs sm:text-sm text-${config.color}-700 mt-1`}>
              {riskLevel === 'urgent' 
                ? 'Immediate action recommended for your career security'
                : 'Stay proactive with your career development'
              }
            </p>
          </div>
        </div>
      </div>

      {/* Quick Actions Grid */}
      <div className="grid gap-3">
        {actions.map((action) => {
          const ActionIcon = action.icon;
          return (
            <a
              key={action.id}
              href={action.enabled ? action.href : '#'}
              className={`
                flex items-center gap-2 sm:gap-3 p-3 sm:p-4 rounded-lg border transition-all duration-200
                ${getColorClasses(action.color, action.enabled)}
                ${action.enabled ? 'hover:shadow-sm' : ''}
              `}
              onClick={!action.enabled ? (e) => e.preventDefault() : undefined}
            >
              <div className={`p-1.5 sm:p-2 rounded-lg flex-shrink-0 ${
                action.enabled 
                  ? `bg-${action.color}-100` 
                  : 'bg-gray-100'
              }`}>
                <ActionIcon className={`h-4 w-4 sm:h-5 sm:w-5 ${
                  action.enabled 
                    ? `text-${action.color}-600` 
                    : 'text-gray-400'
                }`} />
              </div>
              
              <div className="flex-1 min-w-0">
                <h5 className={`font-medium text-sm sm:text-base ${
                  action.enabled ? 'text-gray-900' : 'text-gray-400'
                }`}>
                  {action.title}
                </h5>
                <p className={`text-xs sm:text-sm mt-0.5 ${
                  action.enabled ? 'text-gray-600' : 'text-gray-400'
                }`}>
                  {action.description}
                </p>
              </div>
              
              {!action.enabled && (
                <div className="text-xs text-gray-400 font-medium flex-shrink-0">
                  Locked
                </div>
              )}
            </a>
          );
        })}
      </div>

      {/* Emergency Actions for High Risk */}
      {riskLevel === 'urgent' && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center gap-3 mb-3">
            <AlertTriangle className="h-5 w-5 text-red-600" />
            <h4 className="font-semibold text-red-900">Emergency Actions</h4>
          </div>
          <div className="space-y-2">
            <button className="w-full bg-red-600 hover:bg-red-700 text-white py-2 px-4 rounded-lg font-medium transition-colors text-sm">
              Access Emergency Job Recommendations
            </button>
            <button className="w-full bg-red-100 hover:bg-red-200 text-red-700 py-2 px-4 rounded-lg font-medium transition-colors text-sm">
              Contact Career Support
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default QuickActionsPanel;
