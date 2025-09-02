import React from 'react';
import { useDashboardStore } from '../../store/dashboardStore';

export function TabNavigation() {
  const { activeTab, setActiveTab } = useDashboardStore();

  const tabs = [
    { id: 'onboarding', label: 'Onboarding', icon: '🚀' },
    { id: 'base-case', label: 'Base Case', icon: '📊' },
    { id: 'career-growth', label: 'Career Growth', icon: '📈' },
    { id: 'emergency-expenses', label: 'Emergency Expenses', icon: '🚨' },
    { id: 'health-impact', label: 'Health Impact', icon: '🏥' },
  ];

  return (
    <nav className="bg-white shadow-sm border-b border-gray-200 mb-6">
      <div className="container mx-auto px-4">
        <div className="flex space-x-8 overflow-x-auto">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center space-x-2 py-4 px-2 border-b-2 font-medium text-base leading-relaxed whitespace-nowrap transition-colors ${
                activeTab === tab.id
                  ? 'border-purple-500 text-purple-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <span className="text-lg">{tab.icon}</span>
              <span>{tab.label}</span>
            </button>
          ))}
        </div>
      </div>
    </nav>
  );
} 