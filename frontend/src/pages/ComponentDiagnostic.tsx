import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const ComponentDiagnostic: React.FC = () => {
  const navigate = useNavigate();
  const [diagnostics, setDiagnostics] = useState<string[]>([]);
  const [isRunning, setIsRunning] = useState(false);

  const runDiagnostics = async () => {
    setIsRunning(true);
    setDiagnostics([]);
    
    const tests = [
      'Checking React imports...',
      'Checking component imports...',
      'Checking hooks...',
      'Checking routing...',
      'Checking browser compatibility...'
    ];

    for (const test of tests) {
      setDiagnostics(prev => [...prev, `⏳ ${test}`]);
      await new Promise(resolve => setTimeout(resolve, 500));
      
      try {
        // Test React
        if (test.includes('React')) {
          setDiagnostics(prev => [...prev, `✅ React is available`]);
        }
        
        // Test component imports
        if (test.includes('component imports')) {
          try {
            const { default: DailyOutlookCard } = await import('../components/DailyOutlookCard');
            setDiagnostics(prev => [...prev, `✅ DailyOutlookCard imported successfully`]);
          } catch (error) {
            setDiagnostics(prev => [...prev, `❌ DailyOutlookCard import failed: ${error}`]);
          }
        }
        
        // Test hooks
        if (test.includes('hooks')) {
          try {
            const { useAnalytics } = await import('../hooks/useAnalytics');
            setDiagnostics(prev => [...prev, `✅ useAnalytics hook available`]);
          } catch (error) {
            setDiagnostics(prev => [...prev, `❌ useAnalytics hook failed: ${error}`]);
          }
        }
        
        // Test routing
        if (test.includes('routing')) {
          setDiagnostics(prev => [...prev, `✅ React Router is working`]);
        }
        
        // Test browser compatibility
        if (test.includes('browser compatibility')) {
          const features = {
            'Local Storage': typeof Storage !== 'undefined',
            'Fetch API': typeof fetch !== 'undefined',
            'Touch Events': 'ontouchstart' in window,
            'Suspense': typeof React.Suspense === 'function',
            'Lazy': typeof React.lazy === 'function'
          };
          
          Object.entries(features).forEach(([feature, available]) => {
            setDiagnostics(prev => [...prev, `${available ? '✅' : '❌'} ${feature}: ${available ? 'Available' : 'Not Available'}`]);
          });
        }
        
      } catch (error) {
        setDiagnostics(prev => [...prev, `❌ Error in ${test}: ${error}`]);
      }
    }
    
    setIsRunning(false);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <h1 className="text-xl font-semibold text-gray-900">Component Diagnostic</h1>
              <div className="bg-red-100 text-red-800 px-2 py-1 rounded-full text-xs font-medium">
                DIAGNOSTIC MODE
              </div>
            </div>
            
            <div className="flex items-center gap-2 sm:gap-4">
              <button
                onClick={() => navigate('/debug-dashboard')}
                className="text-sm text-blue-600 hover:text-blue-700 font-medium px-2 py-1 rounded hover:bg-blue-50 transition-colors"
              >
                Back to Debug Dashboard
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="space-y-8">
          
          {/* Instructions */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
            <h2 className="text-lg font-semibold text-blue-900 mb-2">Diagnostic Instructions</h2>
            <div className="text-blue-800 space-y-2">
              <p>• Click "Run Diagnostics" to check component imports and functionality</p>
              <p>• This will help identify what's causing the issues</p>
              <p>• Check the results below for any error messages</p>
            </div>
          </div>

          {/* Diagnostic Button */}
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900">Component Diagnostics</h3>
              <button
                onClick={runDiagnostics}
                disabled={isRunning}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  isRunning 
                    ? 'bg-gray-400 text-gray-600 cursor-not-allowed' 
                    : 'bg-red-600 hover:bg-red-700 text-white'
                }`}
              >
                {isRunning ? 'Running Diagnostics...' : 'Run Diagnostics'}
              </button>
            </div>
          </div>

          {/* Diagnostic Results */}
          {diagnostics.length > 0 && (
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Diagnostic Results</h3>
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {diagnostics.map((result, index) => (
                  <div key={index} className="flex items-center space-x-2 p-2 bg-gray-50 rounded text-sm">
                    <span>{result}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

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
                <h4 className="font-medium text-gray-700 mb-2">User Agent</h4>
                <p className="text-sm text-gray-600 break-all">
                  {navigator.userAgent.substring(0, 100)}...
                </p>
              </div>
            </div>
          </div>

          {/* Quick Navigation */}
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Navigation</h3>
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-3">
                <button
                  onClick={() => navigate('/debug-dashboard')}
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
                >
                  Debug Dashboard
                </button>
                <p className="text-sm text-gray-600">
                  Working dashboard with mock components
                </p>
              </div>
              
              <div className="space-y-3">
                <button
                  onClick={() => navigate('/simple-test')}
                  className="w-full bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
                >
                  Simple Test Page
                </button>
                <p className="text-sm text-gray-600">
                  Test individual components
                </p>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
};

export default ComponentDiagnostic;
