import React, { useState, useEffect } from 'react';
import MemeSettings, { MemePreferences } from '../components/MemeSettings';

export interface SettingsPageProps {
  userId?: string;
  className?: string;
}

const SettingsPage: React.FC<SettingsPageProps> = ({
  userId = 'demo-user-123', // Default for demo purposes
  className = '',
}) => {
  const [activeTab, setActiveTab] = useState('memes');
  const [userPreferences, setUserPreferences] = useState<MemePreferences | null>(null);

  // Handle preference changes
  const handlePreferencesChange = (preferences: MemePreferences) => {
    setUserPreferences(preferences);
    console.log('Preferences updated:', preferences);
  };

  // Tab configuration
  const tabs = [
    {
      id: 'memes',
      label: 'Meme Settings',
      description: 'Customize your daily meme experience',
      icon: '😄',
    },
    {
      id: 'notifications',
      label: 'Notifications',
      description: 'Manage your notification preferences',
      icon: '🔔',
    },
    {
      id: 'privacy',
      label: 'Privacy & Security',
      description: 'Control your privacy and security settings',
      icon: '🔒',
    },
    {
      id: 'account',
      label: 'Account',
      description: 'Manage your account information',
      icon: '👤',
    },
  ];

  return (
    <div className={`min-h-screen bg-gray-50 ${className}`}>
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
          <p className="mt-2 text-gray-600">
            Manage your Mingus app preferences and customize your experience.
          </p>
        </div>

        <div className="flex flex-col lg:flex-row gap-8">
          {/* Sidebar Navigation */}
          <div className="lg:w-64 flex-shrink-0">
            <nav className="space-y-1">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`w-full text-left px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    activeTab === tab.id
                      ? 'bg-blue-100 text-blue-700 border-r-2 border-blue-700'
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                  }`}
                >
                  <div className="flex items-center space-x-3">
                    <span className="text-lg">{tab.icon}</span>
                    <div>
                      <div className="font-medium">{tab.label}</div>
                      <div className="text-xs text-gray-500">{tab.description}</div>
                    </div>
                  </div>
                </button>
              ))}
            </nav>
          </div>

          {/* Main Content */}
          <div className="flex-1">
            {activeTab === 'memes' && (
              <div>
                <MemeSettings
                  userId={userId}
                  onPreferencesChange={handlePreferencesChange}
                />
              </div>
            )}

            {activeTab === 'notifications' && (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">
                  Notification Settings
                </h2>
                <p className="text-gray-600 mb-6">
                  This section will contain notification preferences. Coming soon!
                </p>
                <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
                  <div className="flex">
                    <div className="flex-shrink-0">
                      <svg className="h-5 w-5 text-blue-400" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <div className="ml-3">
                      <p className="text-sm text-blue-700">
                        Notification settings are not yet implemented. This will include options for
                        email notifications, push notifications, and frequency settings.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'privacy' && (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">
                  Privacy & Security
                </h2>
                <p className="text-gray-600 mb-6">
                  This section will contain privacy and security settings. Coming soon!
                </p>
                <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
                  <div className="flex">
                    <div className="flex-shrink-0">
                      <svg className="h-5 w-5 text-blue-400" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <div className="ml-3">
                      <p className="text-sm text-blue-700">
                        Privacy and security settings are not yet implemented. This will include options for
                        data sharing, account security, and privacy controls.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'account' && (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">
                  Account Settings
                </h2>
                <p className="text-gray-600 mb-6">
                  This section will contain account management options. Coming soon!
                </p>
                <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
                  <div className="flex">
                    <div className="flex-shrink-0">
                      <svg className="h-5 w-5 text-blue-400" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <div className="ml-3">
                      <p className="text-sm text-blue-700">
                        Account settings are not yet implemented. This will include options for
                        profile management, password changes, and account deletion.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="mt-12 pt-8 border-t border-gray-200">
          <div className="flex flex-col sm:flex-row justify-between items-center">
            <div className="text-sm text-gray-500">
              Mingus Personal Finance App v1.0.0
            </div>
            <div className="mt-4 sm:mt-0">
              <button className="text-sm text-gray-500 hover:text-gray-700">
                Need help? Contact Support
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;
