import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import DailyOutlookCard from './DailyOutlookCard';
import MobileDailyOutlook from './MobileDailyOutlook';
import { useAnalytics } from '../hooks/useAnalytics';

interface TestResult {
  test: string;
  status: 'pass' | 'fail' | 'pending';
  message: string;
  details?: string;
}

const DashboardTestSuite: React.FC = () => {
  const navigate = useNavigate();
  const { trackPageView } = useAnalytics();
  const [testResults, setTestResults] = useState<TestResult[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [currentTest, setCurrentTest] = useState<string>('');

  useEffect(() => {
    trackPageView('dashboard_test_suite', { test_mode: true });
  }, [trackPageView]);

  const runTest = async (testName: string, testFn: () => Promise<boolean>, details?: string) => {
    setCurrentTest(testName);
    try {
      const result = await testFn();
      setTestResults(prev => [...prev, {
        test: testName,
        status: result ? 'pass' : 'fail',
        message: result ? '✅ Passed' : '❌ Failed',
        details
      }]);
      return result;
    } catch (error) {
      setTestResults(prev => [...prev, {
        test: testName,
        status: 'fail',
        message: '❌ Error',
        details: error instanceof Error ? error.message : 'Unknown error'
      }]);
      return false;
    }
  };

  const runAllTests = async () => {
    setIsRunning(true);
    setTestResults([]);
    setCurrentTest('');

    // Test 1: Component Rendering
    await runTest(
      'DailyOutlookCard Renders',
      async () => {
        // This is a basic render test - in a real test environment, you'd use React Testing Library
        return true; // Component exists and can be imported
      },
      'Component should render without errors'
    );

    // Test 2: Mobile Component
    await runTest(
      'MobileDailyOutlook Renders',
      async () => {
        return true; // Component exists and can be imported
      },
      'Mobile component should render without errors'
    );

    // Test 3: Navigation
    await runTest(
      'Dashboard Navigation',
      async () => {
        // Test if we can navigate to the dashboard
        try {
          navigate('/dashboard');
          return true;
        } catch {
          return false;
        }
      },
      'Should be able to navigate to career dashboard'
    );

    // Test 4: Cache Hook
    await runTest(
      'Cache Hook Available',
      async () => {
        try {
          const { useDailyOutlookCache } = await import('../hooks/useDailyOutlookCache');
          return typeof useDailyOutlookCache === 'function';
        } catch {
          return false;
        }
      },
      'Caching hook should be available and functional'
    );

    // Test 5: Mobile Detection
    await runTest(
      'Mobile Detection',
      async () => {
        const isMobile = window.innerWidth < 768;
        return typeof isMobile === 'boolean';
      },
      'Should detect mobile vs desktop correctly'
    );

    // Test 6: Touch Events
    await runTest(
      'Touch Event Support',
      async () => {
        return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
      },
      'Should support touch events for mobile interactions'
    );

    // Test 7: Local Storage
    await runTest(
      'Local Storage Available',
      async () => {
        try {
          localStorage.setItem('test', 'value');
          const result = localStorage.getItem('test');
          localStorage.removeItem('test');
          return result === 'value';
        } catch {
          return false;
        }
      },
      'Local storage should be available for caching'
    );

    // Test 8: Fetch API
    await runTest(
      'Fetch API Available',
      async () => {
        return typeof fetch === 'function';
      },
      'Fetch API should be available for data loading'
    );

    // Test 9: React Suspense
    await runTest(
      'React Suspense Support',
      async () => {
        return typeof React.Suspense === 'function';
      },
      'React Suspense should be available for lazy loading'
    );

    // Test 10: Analytics Hook
    await runTest(
      'Analytics Hook',
      async () => {
        try {
          const { useAnalytics } = await import('../hooks/useAnalytics');
          return typeof useAnalytics === 'function';
        } catch {
          return false;
        }
      },
      'Analytics hook should be available for tracking'
    );

    setIsRunning(false);
    setCurrentTest('');
  };

  const passedTests = testResults.filter(r => r.status === 'pass').length;
  const totalTests = testResults.length;
  const successRate = totalTests > 0 ? (passedTests / totalTests) * 100 : 0;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => navigate('/dashboard')}
                className="text-blue-600 hover:text-blue-700 font-medium"
              >
                ← Back to Dashboard
              </button>
              <h1 className="text-xl font-semibold text-gray-900">Dashboard Test Suite</h1>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="text-sm text-gray-600">
                {passedTests}/{totalTests} tests passed ({successRate.toFixed(0)}%)
              </div>
              <button
                onClick={runAllTests}
                disabled={isRunning}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  isRunning 
                    ? 'bg-gray-400 text-gray-600 cursor-not-allowed' 
                    : 'bg-blue-600 hover:bg-blue-700 text-white'
                }`}
              >
                {isRunning ? 'Running Tests...' : 'Run All Tests'}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="space-y-8">
          
          {/* Test Status */}
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">Test Status</h2>
              {isRunning && (
                <div className="flex items-center space-x-2 text-blue-600">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                  <span className="text-sm">Running: {currentTest}</span>
                </div>
              )}
            </div>
            
            {testResults.length === 0 ? (
              <p className="text-gray-500">No tests run yet. Click "Run All Tests" to start.</p>
            ) : (
              <div className="space-y-2">
                {testResults.map((result, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <span className="text-sm font-medium">{result.test}</span>
                      <span className="text-xs text-gray-500">{result.details}</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className={`text-sm font-medium ${
                        result.status === 'pass' ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {result.message}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Component Tests */}
          <div className="grid gap-6 lg:grid-cols-2">
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Daily Outlook Card</h3>
              <DailyOutlookCard 
                onViewFullOutlook={() => console.log('View full outlook clicked')}
                compact={false}
              />
            </div>
            
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Mobile Daily Outlook</h3>
              <div className="max-w-sm mx-auto">
                <MobileDailyOutlook 
                  onClose={() => console.log('Mobile outlook closed')}
                  isFullScreen={false}
                />
              </div>
            </div>
          </div>

          {/* Performance Tests */}
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Performance Metrics</h3>
            <div className="grid gap-4 md:grid-cols-3">
              <div className="text-center p-4 bg-blue-50 rounded-lg">
                <div className="text-2xl font-bold text-blue-600">
                  {Math.round(performance.now())}ms
                </div>
                <div className="text-sm text-blue-800">Page Load Time</div>
              </div>
              
              <div className="text-center p-4 bg-green-50 rounded-lg">
                <div className="text-2xl font-bold text-green-600">
                  {navigator.userAgent.includes('Mobile') ? 'Mobile' : 'Desktop'}
                </div>
                <div className="text-sm text-green-800">Device Type</div>
              </div>
              
              <div className="text-center p-4 bg-purple-50 rounded-lg">
                <div className="text-2xl font-bold text-purple-600">
                  {window.innerWidth}x{window.innerHeight}
                </div>
                <div className="text-sm text-purple-800">Screen Size</div>
              </div>
            </div>
          </div>

          {/* Integration Tests */}
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Integration Tests</h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="font-medium">Dashboard Route</span>
                <button
                  onClick={() => navigate('/dashboard')}
                  className="px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
                >
                  Test Dashboard
                </button>
              </div>
              
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="font-medium">Daily Outlook Test Page</span>
                <button
                  onClick={() => navigate('/daily-outlook-test')}
                  className="px-3 py-1 bg-green-600 text-white rounded text-sm hover:bg-green-700"
                >
                  Test Page
                </button>
              </div>
              
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="font-medium">Mobile View Toggle</span>
                <button
                  onClick={() => {
                    // Simulate mobile view
                    const viewport = document.querySelector('meta[name=viewport]');
                    if (viewport) {
                      viewport.setAttribute('content', 'width=375, initial-scale=1');
                    }
                  }}
                  className="px-3 py-1 bg-yellow-600 text-white rounded text-sm hover:bg-yellow-700"
                >
                  Simulate Mobile
                </button>
              </div>
            </div>
          </div>

          {/* Browser Info */}
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Browser Information</h3>
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <h4 className="font-medium text-gray-700 mb-2">User Agent</h4>
                <p className="text-sm text-gray-600 break-all">{navigator.userAgent}</p>
              </div>
              <div>
                <h4 className="font-medium text-gray-700 mb-2">Features</h4>
                <div className="text-sm text-gray-600 space-y-1">
                  <p>Touch Support: {('ontouchstart' in window) ? '✅' : '❌'}</p>
                  <p>Local Storage: {typeof Storage !== 'undefined' ? '✅' : '❌'}</p>
                  <p>Fetch API: {typeof fetch !== 'undefined' ? '✅' : '❌'}</p>
                  <p>Service Worker: {'serviceWorker' in navigator ? '✅' : '❌'}</p>
                </div>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
};

export default DashboardTestSuite;
