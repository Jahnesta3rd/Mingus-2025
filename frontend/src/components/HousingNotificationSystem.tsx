import React, { useState, useEffect } from 'react';
import { 
  BellIcon, 
  ExclamationTriangleIcon, 
  InformationCircleIcon,
  CheckCircleIcon,
  XMarkIcon,
  HomeIcon,
  CalendarIcon,
  MapPinIcon
} from '@heroicons/react/24/outline';
import { useDashboardSelectors, useDashboardStore } from '../stores/dashboardStore';

interface HousingNotificationSystemProps {
  className?: string;
}

const HousingNotificationSystem: React.FC<HousingNotificationSystemProps> = ({ className = '' }) => {
  const { 
    housingAlerts, 
    unreadAlerts, 
    urgentAlerts,
    hasLeaseExpiringSoon,
    leaseInfo 
  } = useDashboardSelectors();
  
  const { 
    markAlertAsRead, 
    dismissAlert, 
    clearAllAlerts,
    addHousingAlert 
  } = useDashboardStore();
  
  const [showNotifications, setShowNotifications] = useState(false);
  const [notificationSound, setNotificationSound] = useState(true);

  // Check for new alerts periodically
  useEffect(() => {
    const checkForNewAlerts = async () => {
      // This would typically check for new housing opportunities, market changes, etc.
      // For now, we'll simulate this
      if (leaseInfo && leaseInfo.lease_end_date && leaseInfo.id && hasLeaseExpiringSoon()) {
        const leaseEndDate = new Date(leaseInfo.lease_end_date);
        const now = new Date();
        const daysUntilExpiry = Math.ceil((leaseEndDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
        
        // Only add alert if it doesn't already exist
        const existingAlert = housingAlerts.find(alert => 
          alert.type === 'lease_expiration' && alert.id === `lease-expiry-${leaseInfo.id}`
        );
        
        if (!existingAlert && daysUntilExpiry <= 60) {
          addHousingAlert({
            id: `lease-expiry-${leaseInfo.id}`,
            type: 'lease_expiration',
            title: 'Lease Expiration Alert',
            message: `Your lease expires in ${daysUntilExpiry} days. Consider starting your housing search.`,
            severity: daysUntilExpiry <= 30 ? 'urgent' : daysUntilExpiry <= 45 ? 'high' : 'medium',
            created_at: new Date().toISOString(),
            is_read: false,
            action_url: '/housing/search',
          });
        }
      }
    };

    // Check immediately
    checkForNewAlerts();
    
    // Set up periodic checking every 5 minutes
    const interval = setInterval(checkForNewAlerts, 5 * 60 * 1000);
    
    return () => clearInterval(interval);
  }, [leaseInfo, hasLeaseExpiringSoon, housingAlerts, addHousingAlert]);

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'urgent':
        return <ExclamationTriangleIcon className="h-5 w-5 text-red-500" />;
      case 'high':
        return <ExclamationTriangleIcon className="h-5 w-5 text-orange-500" />;
      case 'medium':
        return <InformationCircleIcon className="h-5 w-5 text-yellow-500" />;
      default:
        return <InformationCircleIcon className="h-5 w-5 text-blue-500" />;
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'urgent':
        return 'bg-red-50 border-red-200 text-red-800';
      case 'high':
        return 'bg-orange-50 border-orange-200 text-orange-800';
      case 'medium':
        return 'bg-yellow-50 border-yellow-200 text-yellow-800';
      default:
        return 'bg-blue-50 border-blue-200 text-blue-800';
    }
  };

  const getAlertIcon = (type: string) => {
    switch (type) {
      case 'lease_expiration':
        return <CalendarIcon className="h-4 w-4" />;
      case 'new_opportunity':
        return <HomeIcon className="h-4 w-4" />;
      case 'market_change':
        return <MapPinIcon className="h-4 w-4" />;
      case 'career_opportunity':
        return <CheckCircleIcon className="h-4 w-4" />;
      default:
        return <InformationCircleIcon className="h-4 w-4" />;
    }
  };

  const handleMarkAsRead = (alertId: string) => {
    markAlertAsRead(alertId);
  };

  const handleDismiss = (alertId: string) => {
    dismissAlert(alertId);
  };

  const handleClearAll = () => {
    clearAllAlerts();
  };

  return (
    <div className={`relative ${className}`}>
      {/* Notification Bell */}
      <button
        onClick={() => setShowNotifications(!showNotifications)}
        className="relative p-2 text-gray-600 hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 rounded-lg"
        aria-label={`Notifications ${unreadAlerts.length > 0 ? `(${unreadAlerts.length} unread)` : ''}`}
      >
        <BellIcon className="h-6 w-6" />
        {unreadAlerts.length > 0 && (
          <span className="absolute -top-1 -right-1 h-5 w-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
            {unreadAlerts.length > 9 ? '9+' : unreadAlerts.length}
          </span>
        )}
      </button>

      {/* Notification Dropdown */}
      {showNotifications && (
        <div className="absolute right-0 mt-2 w-80 bg-white rounded-lg shadow-lg border border-gray-200 z-50">
          <div className="p-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900">Housing Notifications</h3>
              <div className="flex items-center space-x-2">
                {unreadAlerts.length > 0 && (
                  <button
                    onClick={handleClearAll}
                    className="text-sm text-blue-600 hover:text-blue-700 font-medium"
                  >
                    Clear All
                  </button>
                )}
                <button
                  onClick={() => setShowNotifications(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <XMarkIcon className="h-5 w-5" />
                </button>
              </div>
            </div>
          </div>

          <div className="max-h-96 overflow-y-auto">
            {housingAlerts.length === 0 ? (
              <div className="p-4 text-center text-gray-500">
                <BellIcon className="h-8 w-8 mx-auto mb-2 text-gray-300" />
                <p>No notifications</p>
              </div>
            ) : (
              <div className="divide-y divide-gray-200">
                {housingAlerts.map((alert) => (
                  <div
                    key={alert.id}
                    className={`p-4 hover:bg-gray-50 transition-colors ${
                      !alert.is_read ? 'bg-blue-50' : ''
                    }`}
                  >
                    <div className="flex items-start space-x-3">
                      <div className="flex-shrink-0">
                        {getAlertIcon(alert.type)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <p className={`text-sm font-medium ${
                            !alert.is_read ? 'text-gray-900' : 'text-gray-700'
                          }`}>
                            {alert.title}
                          </p>
                          <div className="flex items-center space-x-1">
                            {getSeverityIcon(alert.severity)}
                            {!alert.is_read && (
                              <div className="h-2 w-2 bg-blue-500 rounded-full"></div>
                            )}
                          </div>
                        </div>
                        <p className="text-sm text-gray-600 mt-1">{alert.message}</p>
                        <div className="flex items-center justify-between mt-2">
                          <span className="text-xs text-gray-500">
                            {new Date(alert.created_at).toLocaleDateString()}
                          </span>
                          <div className="flex items-center space-x-2">
                            {alert.action_url && (
                              <button className="text-xs text-blue-600 hover:text-blue-700 font-medium">
                                View
                              </button>
                            )}
                            {!alert.is_read && (
                              <button
                                onClick={() => handleMarkAsRead(alert.id)}
                                className="text-xs text-gray-600 hover:text-gray-700 font-medium"
                              >
                                Mark Read
                              </button>
                            )}
                            <button
                              onClick={() => handleDismiss(alert.id)}
                              className="text-xs text-gray-400 hover:text-gray-600"
                            >
                              Dismiss
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {housingAlerts.length > 0 && (
            <div className="p-4 border-t border-gray-200 bg-gray-50">
              <div className="flex items-center justify-between text-sm text-gray-600">
                <span>{housingAlerts.length} total notifications</span>
                <span>{unreadAlerts.length} unread</span>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Urgent Alert Banner */}
      {urgentAlerts.length > 0 && (
        <div className="fixed top-16 left-0 right-0 z-40 bg-red-600 text-white px-4 py-2">
          <div className="max-w-7xl mx-auto flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <ExclamationTriangleIcon className="h-5 w-5" />
              <span className="font-medium">
                {urgentAlerts.length} urgent housing alert{urgentAlerts.length > 1 ? 's' : ''}
              </span>
            </div>
            <button
              onClick={() => setShowNotifications(true)}
              className="text-sm underline hover:no-underline"
            >
              View Details
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default HousingNotificationSystem;
