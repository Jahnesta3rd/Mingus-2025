import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const DebugDashboard: React.FC = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('daily-outlook');
  const [showModal, setShowModal] = useState(false);

  const tabs = [
    { id: 'daily-outlook', label: 'Daily Outlook', icon: '🌅', shortLabel: 'Outlook' },
    { id: 'overview', label: 'Overview', icon: '📊', shortLabel: 'Overview' },
    { id: 'recommendations', label: 'Recommendations', icon: '🎯', shortLabel: 'Jobs' },
    { id: 'analytics', label: 'Analytics', icon: '📈', shortLabel: 'Analytics' }
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <h1 className="text-xl font-semibold text-gray-900">Debug Dashboard</h1>
              <div className="bg-green-100 text-green-800 px-2 py-1 rounded-full text-xs font-medium">
                DEBUG MODE
              </div>
            </div>
            
            <div className="flex items-center gap-2 sm:gap-4">
              <button
                onClick={() => navigate('/simple-test')}
                className="text-sm text-blue-600 hover:text-blue-700 font-medium px-2 py-1 rounded hover:bg-blue-50 transition-colors"
              >
                Back to Tests
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="space-y-8">
          
          {/* Debug Info */}
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
            <h2 className="text-lg font-semibold text-yellow-900 mb-2">Debug Information</h2>
            <div className="text-yellow-800 space-y-2">
              <p>• Current tab: <strong>{activeTab}</strong></p>
              <p>• Modal state: <strong>{showModal ? 'Open' : 'Closed'}</strong></p>
              <p>• Screen size: <strong>{window.innerWidth}x{window.innerHeight}</strong></p>
              <p>• Device type: <strong>{window.innerWidth < 768 ? 'Mobile' : 'Desktop'}</strong></p>
            </div>
          </div>

          {/* Tab Navigation */}
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-2 sm:space-x-8 overflow-x-auto">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`
                    relative py-2 px-1 border-b-2 font-medium text-sm whitespace-nowrap flex items-center gap-1 sm:gap-2 flex-shrink-0
                    ${activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }
                  `}
                >
                  <span className="text-base sm:text-sm">{tab.icon}</span>
                  <span className="hidden sm:inline">{tab.label}</span>
                  <span className="sm:hidden">{tab.shortLabel}</span>
                </button>
              ))}
            </nav>
          </div>

          {/* Tab Content */}
          <div className="min-h-[600px]">
            {activeTab === 'daily-outlook' && (
              <div className="space-y-6">
                <h2 className="text-2xl font-bold text-gray-900">Daily Outlook Tab</h2>
                
                {/* Mock Daily Outlook Card */}
                <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-gray-900">Daily Outlook</h3>
                    <div className="text-sm text-gray-500">Test Mode</div>
                  </div>
                  
                  <div className="grid gap-6 lg:grid-cols-2">
                    <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="flex items-center space-x-3">
                            <span className="text-2xl font-bold text-gray-900">85</span>
                            <span className="text-green-500">↗️</span>
                          </div>
                          <p className="text-sm text-gray-600 mt-1">Balance Score</p>
                        </div>
                        <div className="text-right">
                          <span className="text-sm font-medium text-green-600">+5.2%</span>
                          <p className="text-xs text-gray-500">vs yesterday</p>
                        </div>
                      </div>
                    </div>
                    
                    <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                      <div className="flex items-start space-x-3">
                        <span className="text-lg">☀️</span>
                        <div>
                          <h4 className="font-semibold text-sm mb-1">Great Progress!</h4>
                          <p className="text-sm text-green-800">Your financial health is improving steadily.</p>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <div className="mt-4 flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="flex items-center space-x-1">
                        <span className="text-orange-500">🔥</span>
                        <span className="text-sm font-medium text-gray-900">7 day streak</span>
                      </div>
                      <div className="text-xs text-gray-500">
                        🎉 You're doing amazing! Every small step counts.
                      </div>
                    </div>
                    <button
                      onClick={() => setShowModal(true)}
                      className="flex items-center space-x-1 text-blue-600 hover:text-blue-700 text-sm font-medium transition-colors"
                    >
                      <span>View Full Outlook</span>
                      <span>→</span>
                    </button>
                  </div>
                </div>

                {/* Quick Actions Mock */}
                <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
                  <div className="space-y-3">
                    <div className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                      <div className="w-2 h-2 bg-red-500 rounded-full"></div>
                      <span className="text-sm">Review Budget</span>
                      <span className="text-gray-400 text-xs">(5 min)</span>
                    </div>
                    <div className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                      <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
                      <span className="text-sm">Update Goals</span>
                      <span className="text-gray-400 text-xs">(10 min)</span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'overview' && (
              <div className="space-y-6">
                <h2 className="text-2xl font-bold text-gray-900">Overview Tab</h2>
                <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                  <p className="text-gray-600">Overview content would be displayed here.</p>
                </div>
              </div>
            )}

            {activeTab === 'recommendations' && (
              <div className="space-y-6">
                <h2 className="text-2xl font-bold text-gray-900">Recommendations Tab</h2>
                <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                  <p className="text-gray-600">Job recommendations would be displayed here.</p>
                </div>
              </div>
            )}

            {activeTab === 'analytics' && (
              <div className="space-y-6">
                <h2 className="text-2xl font-bold text-gray-900">Analytics Tab</h2>
                <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                  <p className="text-gray-600">Analytics content would be displayed here.</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
            <div className="flex items-center justify-between p-4 border-b border-gray-200">
              <h2 className="text-xl font-semibold text-gray-900">Daily Outlook - Full View</h2>
              <button
                onClick={() => setShowModal(false)}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                aria-label="Close"
              >
                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="overflow-y-auto max-h-[calc(90vh-80px)] p-6">
              <div className="space-y-6">
                <h3 className="text-lg font-semibold text-gray-900">Full Daily Outlook Content</h3>
                <div className="bg-blue-50 rounded-lg p-4">
                  <p className="text-blue-800">This would be the full Daily Outlook component with all features:</p>
                  <ul className="mt-2 text-sm text-blue-700 space-y-1">
                    <li>• Complete balance score analysis</li>
                    <li>• Detailed insights and recommendations</li>
                    <li>• Quick actions with completion tracking</li>
                    <li>• Streak progress and milestones</li>
                    <li>• Tomorrow's preview</li>
                    <li>• Rating and sharing features</li>
                  </ul>
                </div>
                <div className="text-center">
                  <button
                    onClick={() => setShowModal(false)}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg font-medium transition-colors"
                  >
                    Close Modal
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DebugDashboard;
