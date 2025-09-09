import React, { useState } from 'react';
import MemeSettings, { MemePreferences } from '../components/MemeSettings';
import SettingsPage from '../pages/SettingsPage';

/**
 * Example usage of MemeSettings component
 * This demonstrates how to integrate the meme settings into your app
 */
const MemeSettingsExample: React.FC = () => {
  const [currentUser, setCurrentUser] = useState('demo-user-123');
  const [showFullSettings, setShowFullSettings] = useState(false);
  const [userPreferences, setUserPreferences] = useState<MemePreferences | null>(null);

  const handlePreferencesChange = (preferences: MemePreferences) => {
    setUserPreferences(preferences);
    console.log('User preferences updated:', preferences);
  };

  const handleUserChange = (newUserId: string) => {
    setCurrentUser(newUserId);
    setUserPreferences(null); // Reset preferences when user changes
  };

  if (showFullSettings) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-4xl mx-auto px-4 py-8">
          <div className="mb-6">
            <button
              onClick={() => setShowFullSettings(false)}
              className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              Back to Component Demo
            </button>
          </div>
          <SettingsPage userId={currentUser} />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            MemeSettings Component Demo
          </h1>
          <p className="text-gray-600 mb-6">
            This demonstrates the MemeSettings component with all its features.
            You can test the different settings and see how they work.
          </p>
        </div>

        {/* User ID Selector */}
        <div className="mb-8 bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Demo Controls</h2>
          <div className="space-y-4">
            <div>
              <label htmlFor="userId" className="block text-sm font-medium text-gray-700 mb-2">
                User ID (for testing different users)
              </label>
              <input
                id="userId"
                type="text"
                value={currentUser}
                onChange={(e) => handleUserChange(e.target.value)}
                className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder="Enter user ID"
              />
            </div>
            <div className="flex space-x-4">
              <button
                onClick={() => setShowFullSettings(true)}
                className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                View Full Settings Page
              </button>
            </div>
          </div>
        </div>

        {/* Current Preferences Display */}
        {userPreferences && (
          <div className="mb-8 bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Current Preferences</h2>
            <div className="bg-gray-50 rounded-md p-4">
              <pre className="text-sm text-gray-700 overflow-auto">
                {JSON.stringify(userPreferences, null, 2)}
              </pre>
            </div>
          </div>
        )}

        {/* MemeSettings Component */}
        <div className="mb-8">
          <MemeSettings
            userId={currentUser}
            onPreferencesChange={handlePreferencesChange}
          />
        </div>

        {/* Features List */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Component Features</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-3">
              <h3 className="font-medium text-gray-900">Core Features</h3>
              <ul className="space-y-2 text-sm text-gray-600">
                <li className="flex items-center">
                  <svg className="w-4 h-4 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  Toggle to enable/disable daily memes
                </li>
                <li className="flex items-center">
                  <svg className="w-4 h-4 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  Category selection checkboxes
                </li>
                <li className="flex items-center">
                  <svg className="w-4 h-4 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  Frequency settings (login/daily/weekly)
                </li>
                <li className="flex items-center">
                  <svg className="w-4 h-4 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  Preview memes functionality
                </li>
              </ul>
            </div>
            <div className="space-y-3">
              <h3 className="font-medium text-gray-900">Technical Features</h3>
              <ul className="space-y-2 text-sm text-gray-600">
                <li className="flex items-center">
                  <svg className="w-4 h-4 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  Optimistic updates
                </li>
                <li className="flex items-center">
                  <svg className="w-4 h-4 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  Loading and saving states
                </li>
                <li className="flex items-center">
                  <svg className="w-4 h-4 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  Form validation
                </li>
                <li className="flex items-center">
                  <svg className="w-4 h-4 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  Accessibility features
                </li>
              </ul>
            </div>
          </div>
        </div>

        {/* Usage Instructions */}
        <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-blue-900 mb-3">How to Use</h3>
          <div className="text-sm text-blue-800 space-y-2">
            <p>1. <strong>Toggle memes on/off:</strong> Use the main switch to enable or disable the meme feature completely.</p>
            <p>2. <strong>Select categories:</strong> Choose which types of memes you want to see by checking the category boxes.</p>
            <p>3. <strong>Set frequency:</strong> Choose how often you want to see memes (every login, once per day, or weekly).</p>
            <p>4. <strong>Preview memes:</strong> Click the "Preview Memes" button to see what a meme would look like.</p>
            <p>5. <strong>Reset settings:</strong> Use the "Reset to Defaults" button to restore all settings to their original values.</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MemeSettingsExample;
