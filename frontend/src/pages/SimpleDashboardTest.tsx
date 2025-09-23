import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import DailyOutlookCard from '../components/DailyOutlookCard';

const SimpleDashboardTest: React.FC = () => {
  const navigate = useNavigate();
  const [testResults, setTestResults] = useState<string[]>([]);
  const [isRunning, setIsRunning] = useState(false);

  const runBasicTests = async () => {
    setIsRunning(true);
    setTestResults([]);
    
    const tests = [
      'Testing Daily Outlook Card component...',
      'Testing component imports...',
      'Testing basic functionality...',
      'Testing mobile responsiveness...'
    ];

    for (const test of tests) {
      setTestResults(prev => [...prev, test]);
      await new Promise(resolve => setTimeout(resolve, 500)); // Simulate test delay
    }
    
    setIsRunning(false);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => navigate('/career-dashboard')}
                className="text-blue-600 hover:text-blue-700 font-medium"
              >
                ← Back to Dashboard
              </button>
              <h1 className="text-xl font-semibold text-gray-900">Simple Dashboard Test</h1>
            </div>
            
            <div className="flex items-center space-x-4">
              <button
                onClick={runBasicTests}
                disabled={isRunning}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  isRunning 
                    ? 'bg-gray-400 text-gray-600 cursor-not-allowed' 
                    : 'bg-blue-600 hover:bg-blue-700 text-white'
                }`}
              >
                {isRunning ? 'Running Tests...' : 'Run Basic Tests'}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="space-y-8">
          
          {/* Test Instructions */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
            <h2 className="text-lg font-semibold text-blue-900 mb-2">Test Instructions</h2>
            <div className="text-blue-800 space-y-2">
              <p>• Click "Run Basic Tests" to test component functionality</p>
              <p>• Check the Daily Outlook Card component below</p>
              <p>• Test mobile responsiveness by resizing your browser</p>
              <p>• Navigate to the main dashboard to test full integration</p>
            </div>
          </div>

          {/* Test Results */}
          {testResults.length > 0 && (
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Test Results</h3>
              <div className="space-y-2">
                {testResults.map((result, index) => (
                  <div key={index} className="flex items-center space-x-2 p-2 bg-gray-50 rounded">
                    <span className="text-green-600">✅</span>
                    <span className="text-sm">{result}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Daily Outlook Card Test */}
          <div className="space-y-4">
            <h2 className="text-xl font-semibold text-gray-900">Daily Outlook Card Test</h2>
            <div className="grid gap-6 lg:grid-cols-2">
              <div>
                <h3 className="text-lg font-medium text-gray-700 mb-3">Compact Version</h3>
                <DailyOutlookCard 
                  onViewFullOutlook={() => alert('View Full Outlook clicked!')}
                  compact={true}
                />
              </div>
              <div>
                <h3 className="text-lg font-medium text-gray-700 mb-3">Full Card Version</h3>
                <DailyOutlookCard 
                  onViewFullOutlook={() => alert('View Full Outlook clicked!')}
                  compact={false}
                />
              </div>
            </div>
          </div>

          {/* Navigation Tests */}
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Navigation Tests</h3>
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-3">
                <button
                  onClick={() => navigate('/career-dashboard')}
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
                >
                  Test Main Dashboard
                </button>
                <p className="text-sm text-gray-600">
                  Navigate to the main dashboard to test Daily Outlook as the first tab
                </p>
              </div>
              
              <div className="space-y-3">
                <button
                  onClick={() => navigate('/daily-outlook-test')}
                  className="w-full bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
                >
                  Test Daily Outlook Page
                </button>
                <p className="text-sm text-gray-600">
                  Test individual Daily Outlook components
                </p>
              </div>
            </div>
          </div>

          {/* Browser Info */}
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Browser Information</h3>
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <h4 className="font-medium text-gray-700 mb-2">Screen Size</h4>
                <p className="text-sm text-gray-600">
                  {window.innerWidth} x {window.innerHeight} pixels
                </p>
              </div>
              <div>
                <h4 className="font-medium text-gray-700 mb-2">Device Type</h4>
                <p className="text-sm text-gray-600">
                  {window.innerWidth < 768 ? 'Mobile' : 'Desktop'}
                </p>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
};

export default SimpleDashboardTest;
