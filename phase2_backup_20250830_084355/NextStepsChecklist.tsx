import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle, Circle, Star, TrendingUp, Target, Users, Bell, CreditCard } from 'lucide-react';

interface ChecklistItem {
  id: string;
  title: string;
  description: string;
  category: 'profile' | 'accounts' | 'notifications' | 'community' | 'goals';
  priority: 'high' | 'medium' | 'low';
  completed: boolean;
  action?: {
    type: 'navigate' | 'modal' | 'external';
    target: string;
    text: string;
  };
  estimatedTime?: number; // in minutes
}

interface NextStepsChecklistProps {
  userId: string;
  onItemComplete: (itemId: string) => void;
  onActionClick: (action: any) => void;
}

export const NextStepsChecklist: React.FC<NextStepsChecklistProps> = ({
  userId,
  onItemComplete,
  onActionClick
}) => {
  const [checklistItems, setChecklistItems] = useState<ChecklistItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCompleted, setShowCompleted] = useState(false);

  useEffect(() => {
    loadChecklistItems();
  }, [userId]);

  const loadChecklistItems = async () => {
    try {
      setLoading(true);
      // In a real app, this would fetch from an API
      const items = await generatePersonalizedChecklist(userId);
      setChecklistItems(items);
    } catch (error) {
      console.error('Error loading checklist:', error);
    } finally {
      setLoading(false);
    }
  };

  const generatePersonalizedChecklist = async (userId: string): Promise<ChecklistItem[]> => {
    // This would typically fetch user data and generate personalized items
    // For now, we'll return a sample checklist
    return [
      {
        id: 'complete-profile',
        title: 'Complete Your Profile',
        description: 'Add your employment details, income sources, and financial goals for personalized insights.',
        category: 'profile',
        priority: 'high',
        completed: false,
        action: {
          type: 'navigate',
          target: '/profile',
          text: 'Complete Profile'
        },
        estimatedTime: 5
      },
      {
        id: 'connect-bank',
        title: 'Connect Your Bank Account',
        description: 'Link your primary bank account for automatic expense tracking and cash flow analysis.',
        category: 'accounts',
        priority: 'high',
        completed: false,
        action: {
          type: 'modal',
          target: 'connect-accounts',
          text: 'Connect Account'
        },
        estimatedTime: 3
      },
      {
        id: 'setup-notifications',
        title: 'Set Up Notifications',
        description: 'Choose your preferred notification settings to stay updated on your progress and insights.',
        category: 'notifications',
        priority: 'medium',
        completed: false,
        action: {
          type: 'modal',
          target: 'notification-settings',
          text: 'Set Up Notifications'
        },
        estimatedTime: 2
      },
      {
        id: 'join-community',
        title: 'Join Community Event',
        description: 'Connect with others on similar financial journeys. Share experiences and get support.',
        category: 'community',
        priority: 'medium',
        completed: false,
        action: {
          type: 'navigate',
          target: '/community',
          text: 'Join Event'
        },
        estimatedTime: 10
      },
      {
        id: 'set-emergency-goal',
        title: 'Set Emergency Fund Goal',
        description: 'Define your emergency fund target based on your job security and monthly expenses.',
        category: 'goals',
        priority: 'high',
        completed: false,
        action: {
          type: 'navigate',
          target: '/goals',
          text: 'Set Goal'
        },
        estimatedTime: 3
      },
      {
        id: 'review-insights',
        title: 'Review Your Insights',
        description: 'Check out your personalized financial insights and recommendations.',
        category: 'profile',
        priority: 'low',
        completed: false,
        action: {
          type: 'navigate',
          target: '/insights',
          text: 'View Insights'
        },
        estimatedTime: 5
      }
    ];
  };

  const handleItemToggle = async (itemId: string) => {
    const updatedItems = checklistItems.map(item =>
      item.id === itemId ? { ...item, completed: !item.completed } : item
    );
    setChecklistItems(updatedItems);
    
    const item = updatedItems.find(i => i.id === itemId);
    if (item && !item.completed) {
      onItemComplete(itemId);
    }
  };

  const handleActionClick = (item: ChecklistItem) => {
    if (item.action) {
      onActionClick(item.action);
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'profile': return <Target size={16} />;
      case 'accounts': return <CreditCard size={16} />;
      case 'notifications': return <Bell size={16} />;
      case 'community': return <Users size={16} />;
      case 'goals': return <TrendingUp size={16} />;
      default: return <Circle size={16} />;
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'text-red-500';
      case 'medium': return 'text-yellow-500';
      case 'low': return 'text-green-500';
      default: return 'text-gray-500';
    }
  };

  const completedCount = checklistItems.filter(item => item.completed).length;
  const totalCount = checklistItems.length;
  const progressPercentage = totalCount > 0 ? (completedCount / totalCount) * 100 : 0;

  const filteredItems = showCompleted 
    ? checklistItems 
    : checklistItems.filter(item => !item.completed);

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="space-y-3">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-12 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Next Steps</h3>
          <p className="text-base leading-relaxed text-gray-600">
            Complete these tasks to get the most out of Mingus
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Star className="text-yellow-500" size={20} />
          <span className="text-base leading-relaxed font-medium text-gray-900">
            {completedCount}/{totalCount}
          </span>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-base leading-relaxed font-medium text-gray-700">Progress</span>
          <span className="text-base leading-relaxed text-gray-500">{Math.round(progressPercentage)}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <motion.div
            className="bg-gradient-to-r from-blue-500 to-purple-600 h-2 rounded-full"
            initial={{ width: 0 }}
            animate={{ width: `${progressPercentage}%` }}
            transition={{ duration: 0.5, ease: "easeOut" }}
          />
        </div>
      </div>

      {/* Filter Toggle */}
      <div className="flex items-center justify-between mb-4">
        <button
          onClick={() => setShowCompleted(!showCompleted)}
          className="text-base leading-relaxed text-blue-600 hover:text-blue-700 font-medium"
        >
          {showCompleted ? 'Hide completed' : 'Show completed'}
        </button>
        {completedCount > 0 && (
          <span className="text-base leading-relaxed text-green-600 font-medium">
            Great progress! Keep it up! 🎉
          </span>
        )}
      </div>

      {/* Checklist Items */}
      <div className="space-y-3">
        <AnimatePresence>
          {filteredItems.map((item) => (
            <motion.div
              key={item.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.2 }}
              className={`p-4 rounded-lg border transition-all duration-200 ${
                item.completed
                  ? 'bg-green-50 border-green-200'
                  : 'bg-gray-50 border-gray-200 hover:bg-gray-100'
              }`}
            >
              <div className="flex items-start space-x-3">
                {/* Checkbox */}
                <button
                  onClick={() => handleItemToggle(item.id)}
                  className="flex-shrink-0 mt-1"
                >
                  {item.completed ? (
                    <CheckCircle className="text-green-500" size={20} />
                  ) : (
                    <Circle className="text-gray-400 hover:text-gray-600" size={20} />
                  )}
                </button>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2 mb-1">
                    <div className="text-gray-500">
                      {getCategoryIcon(item.category)}
                    </div>
                    <h4 className={`text-base leading-relaxed font-medium ${
                      item.completed ? 'text-green-800 line-through' : 'text-gray-900'
                    }`}>
                      {item.title}
                    </h4>
                    <div className={`w-2 h-2 rounded-full ${getPriorityColor(item.priority)}`} />
                  </div>
                  
                  <p className={`text-base leading-relaxed ${
                    item.completed ? 'text-green-700' : 'text-gray-600'
                  }`}>
                    {item.description}
                  </p>

                  {/* Action and Time */}
                  <div className="flex items-center justify-between mt-3">
                    <div className="flex items-center space-x-4">
                      {item.action && !item.completed && (
                        <button
                          onClick={() => handleActionClick(item)}
                          className="text-base leading-relaxed text-blue-600 hover:text-blue-700 font-medium"
                        >
                          {item.action.text}
                        </button>
                      )}
                      {item.estimatedTime && (
                        <span className="text-base leading-relaxed text-gray-500">
                          ~{item.estimatedTime} min
                        </span>
                      )}
                    </div>
                    
                    {item.completed && (
                      <span className="text-base leading-relaxed text-green-600 font-medium">
                        Completed! 🎉
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {/* Empty State */}
        {filteredItems.length === 0 && (
          <div className="text-center py-8">
            <CheckCircle className="text-green-500 mx-auto mb-3" size={48} />
            <h4 className="text-lg font-medium text-gray-900 mb-2">
              All caught up!
            </h4>
            <p className="text-gray-600">
              You've completed all your next steps. Great job! 🎉
            </p>
          </div>
        )}
      </div>

      {/* Encouragement */}
      {completedCount > 0 && completedCount < totalCount && (
        <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
          <div className="flex items-center space-x-2">
            <TrendingUp className="text-blue-600" size={20} />
            <span className="text-base leading-relaxed font-medium text-blue-800">
              You're making great progress!
            </span>
          </div>
          <p className="text-base leading-relaxed text-blue-700 mt-1">
            {totalCount - completedCount} more steps to go. You've got this! 💪
          </p>
        </div>
      )}
    </div>
  );
}; 