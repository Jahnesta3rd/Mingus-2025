import React, { useState, useEffect } from 'react';
import { 
  BellIcon, 
  EyeIcon, 
  CheckCircleIcon, 
  XMarkIcon,
  SunIcon,
  BoltIcon,
  HeartIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline';
import NotificationService from '../services/notificationService';

interface RichNotificationProps {
  notification: {
    id: string;
    title: string;
    message: string;
    preview: string;
    balanceScore: number;
    streakCount: number;
    actionUrl: string;
    scheduledTime: string;
    isDelivered: boolean;
    deliveredAt?: string;
    clickedAt?: string;
    actionTaken?: string;
  };
  onAction?: (action: string, data?: any) => void;
  onDismiss?: () => void;
  className?: string;
}

const RichNotification: React.FC<RichNotificationProps> = ({
  notification,
  onAction,
  onDismiss,
  className = ''
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [actionTaken, setActionTaken] = useState<string | null>(null);
  const notificationService = NotificationService.getInstance();

  const handleAction = async (action: string, data?: any) => {
    try {
      // Track the interaction
      await notificationService.trackNotificationInteraction(
        notification.id,
        'action_taken',
        { action, data }
      );
      
      setActionTaken(action);
      onAction?.(action, data);
    } catch (error) {
      console.error('Error tracking notification action:', error);
    }
  };

  const handleDismiss = async () => {
    try {
      // Track the dismissal
      await notificationService.trackNotificationInteraction(
        notification.id,
        'dismissed'
      );
      
      onDismiss?.();
    } catch (error) {
      console.error('Error tracking notification dismissal:', error);
    }
  };

  const handleView = async () => {
    try {
      // Track the view
      await notificationService.trackNotificationInteraction(
        notification.id,
        'clicked'
      );
      
      // Navigate to the action URL
      window.location.href = notification.actionUrl;
    } catch (error) {
      console.error('Error tracking notification view:', error);
    }
  };

  const getBalanceScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600 bg-green-100';
    if (score >= 60) return 'text-yellow-600 bg-yellow-100';
    if (score >= 40) return 'text-orange-600 bg-orange-100';
    return 'text-red-600 bg-red-100';
  };

  const getBalanceScoreIcon = (score: number) => {
    if (score >= 80) return <CheckCircleIcon className="h-5 w-5" />;
    if (score >= 60) return <SunIcon className="h-5 w-5" />;
    if (score >= 40) return <BoltIcon className="h-5 w-5" />;
    return <HeartIcon className="h-5 w-5" />;
  };

  const getStreakMessage = (streak: number) => {
    if (streak === 0) return null;
    if (streak === 1) return "Great start!";
    if (streak < 7) return `You're on a ${streak}-day streak!`;
    if (streak < 30) return `Amazing ${streak}-day streak!`;
    return `Incredible ${streak}-day streak!`;
  };

  return (
    <div className={`bg-white rounded-lg shadow-lg border border-gray-200 overflow-hidden ${className}`}>
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 px-4 py-3 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-100 rounded-full">
              <BellIcon className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-gray-900">{notification.title}</h3>
              <p className="text-xs text-gray-600">
                {notification.deliveredAt 
                  ? new Date(notification.deliveredAt).toLocaleString()
                  : 'Scheduled for ' + new Date(notification.scheduledTime).toLocaleString()
                }
              </p>
            </div>
          </div>
          <button
            onClick={handleDismiss}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <XMarkIcon className="h-5 w-5" />
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="p-4">
        <div className="mb-4">
          <p className="text-gray-700 text-sm leading-relaxed">{notification.message}</p>
          {notification.preview && (
            <div className="mt-2 p-3 bg-gray-50 rounded-md">
              <p className="text-xs text-gray-600 italic">"{notification.preview}"</p>
            </div>
          )}
        </div>

        {/* Balance Score */}
        <div className="mb-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">Today's Balance Score</span>
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${getBalanceScoreColor(notification.balanceScore)}`}>
              {notification.balanceScore}/100
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className={`h-2 rounded-full transition-all duration-300 ${
                notification.balanceScore >= 80 ? 'bg-green-500' :
                notification.balanceScore >= 60 ? 'bg-yellow-500' :
                notification.balanceScore >= 40 ? 'bg-orange-500' : 'bg-red-500'
              }`}
              style={{ width: `${notification.balanceScore}%` }}
            />
          </div>
        </div>

        {/* Streak Information */}
        {notification.streakCount > 0 && (
          <div className="mb-4 p-3 bg-gradient-to-r from-purple-50 to-pink-50 rounded-lg border border-purple-200">
            <div className="flex items-center space-x-2">
              <ChartBarIcon className="h-5 w-5 text-purple-600" />
              <div>
                <p className="text-sm font-medium text-purple-900">
                  {getStreakMessage(notification.streakCount)}
                </p>
                <p className="text-xs text-purple-700">
                  Keep up the great work!
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex items-center space-x-2">
          <button
            onClick={handleView}
            className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
          >
            <EyeIcon className="h-4 w-4 inline mr-2" />
            View Outlook
          </button>
          
          <button
            onClick={() => handleAction('quick_action', { type: 'balance_check' })}
            className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md text-sm font-medium hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 transition-colors"
          >
            Quick Action
          </button>
        </div>

        {/* Action Taken Feedback */}
        {actionTaken && (
          <div className="mt-3 p-2 bg-green-50 border border-green-200 rounded-md">
            <div className="flex items-center space-x-2">
              <CheckCircleIcon className="h-4 w-4 text-green-600" />
              <span className="text-sm text-green-700">
                Action taken: {actionTaken}
              </span>
            </div>
          </div>
        )}

        {/* Expandable Details */}
        <div className="mt-4 pt-4 border-t border-gray-200">
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-sm text-gray-600 hover:text-gray-800 transition-colors"
          >
            {isExpanded ? 'Show Less' : 'Show Details'}
          </button>
          
          {isExpanded && (
            <div className="mt-2 space-y-2 text-xs text-gray-500">
              <div className="flex justify-between">
                <span>Notification ID:</span>
                <span className="font-mono">{notification.id}</span>
              </div>
              <div className="flex justify-between">
                <span>Status:</span>
                <span className={notification.isDelivered ? 'text-green-600' : 'text-yellow-600'}>
                  {notification.isDelivered ? 'Delivered' : 'Pending'}
                </span>
              </div>
              {notification.clickedAt && (
                <div className="flex justify-between">
                  <span>Last Clicked:</span>
                  <span>{new Date(notification.clickedAt).toLocaleString()}</span>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default RichNotification;
