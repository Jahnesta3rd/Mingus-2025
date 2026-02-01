import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import DailyOutlookCard from '../components/DailyOutlookCard';
import MobileDailyOutlook from '../components/MobileDailyOutlook';
import { useAnalytics } from '../hooks/useAnalytics';

const DailyOutlookTestPage: React.FC = () => {
  const navigate = useNavigate();
  const { trackPageView } = useAnalytics();
  const [showMobileView, setShowMobileView] = useState(false);
  const [showFullView, setShowFullView] = useState(false);

  React.useEffect(() => {
    trackPageView('daily_outlook_test_page', {
      test_mode: true
    });
  }, [trackPageView]);

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
              <h1 className="text-xl font-semibold text-gray-900">Daily Outlook Test Page</h1>
            </div>
            
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setShowMobileView(!showMobileView)}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  showMobileView 
                    ? 'bg-blue-600 text-white' 
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                {showMobileView ? 'Desktop View' : 'Mobile View'}
              </button>
              
              <button
                onClick={() => setShowFullView(!showFullView)}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  showFullView 
                    ? 'bg-green-600 text-white' 
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                {showFullView ? 'Hide Full View' : 'Show Full View'}
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
              <p>• <strong>Card View:</strong> Test the compact Daily Outlook card component</p>
              <p>• <strong>Mobile View:</strong> Toggle to test mobile-optimized version with swipe gestures</p>
              <p>• <strong>Full View:</strong> Test the full Daily Outlook modal experience</p>
              <p>• <strong>Performance:</strong> Check caching, lazy loading, and background refresh</p>
              <p>• <strong>Interactions:</strong> Test action completion, rating, and sharing features</p>
            </div>
          </div>

          {/* Card View Test */}
          <div className="space-y-4">
            <h2 className="text-xl font-semibold text-gray-900">Daily Outlook Card (Dashboard Integration)</h2>
            <div className="grid gap-6 lg:grid-cols-2">
              <div>
                <h3 className="text-lg font-medium text-gray-700 mb-3">Compact Version</h3>
                <DailyOutlookCard 
                  onViewFullOutlook={() => setShowFullView(true)}
                  compact={true}
                />
              </div>
              <div>
                <h3 className="text-lg font-medium text-gray-700 mb-3">Full Card Version</h3>
                <DailyOutlookCard 
                  onViewFullOutlook={() => setShowFullView(true)}
                  compact={false}
                />
              </div>
            </div>
          </div>

          {/* Mobile View Test */}
          {showMobileView && (
            <div className="space-y-4">
              <h2 className="text-xl font-semibold text-gray-900">Mobile Daily Outlook</h2>
              <div className="max-w-md mx-auto">
                <MobileDailyOutlook 
                  onClose={() => setShowMobileView(false)}
                  isFullScreen={true}
                />
              </div>
            </div>
          )}

          {/* Full View Modal Test */}
          {showFullView && (
            <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
              <div className="bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
                <div className="flex items-center justify-between p-4 border-b border-gray-200">
                  <h2 className="text-xl font-semibold text-gray-900">Daily Outlook - Full View</h2>
                  <button
                    onClick={() => setShowFullView(false)}
                    className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                    aria-label="Close"
                  >
                    <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
                <div className="overflow-y-auto max-h-[calc(90vh-80px)]">
                  {showMobileView ? (
                    <MobileDailyOutlook 
                      onClose={() => setShowFullView(false)}
                      isFullScreen={true}
                    />
                  ) : (
                    <div className="p-6">
                      <div className="text-center text-gray-500">
                        <p>Full Daily Outlook component would be loaded here</p>
                        <p className="text-sm mt-2">(Lazy loaded in production)</p>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Performance Test */}
          <div className="space-y-4">
            <h2 className="text-xl font-semibold text-gray-900">Performance Testing</h2>
            <div className="grid gap-4 md:grid-cols-2">
              <div className="bg-white rounded-lg border border-gray-200 p-4">
                <h3 className="font-medium text-gray-900 mb-2">Cache Status</h3>
                <div className="text-sm text-gray-600 space-y-1">
                  <p>• Check browser DevTools → Network tab</p>
                  <p>• Look for cache hits on subsequent loads</p>
                  <p>• Background refresh should be silent</p>
                </div>
              </div>
              
              <div className="bg-white rounded-lg border border-gray-200 p-4">
                <h3 className="font-medium text-gray-900 mb-2">Mobile Gestures</h3>
                <div className="text-sm text-gray-600 space-y-1">
                  <p>• Swipe left/right to navigate sections</p>
                  <p>• Tap sections to expand/collapse</p>
                  <p>• Test touch targets (44px minimum)</p>
                </div>
              </div>
            </div>
          </div>

          {/* Integration Test */}
          <div className="space-y-4">
            <h2 className="text-xl font-semibold text-gray-900">Integration Test</h2>
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <h3 className="font-medium text-gray-900 mb-3">Dashboard Integration</h3>
                  <button
                    onClick={() => navigate('/dashboard')}
                    className="w-full bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
                  >
                    Test in Dashboard
                  </button>
                  <p className="text-sm text-gray-600 mt-2">
                    Navigate to the main dashboard to test Daily Outlook as the first tab
                  </p>
                </div>
                
                <div>
                  <h3 className="font-medium text-gray-900 mb-3">Component Features</h3>
                  <div className="text-sm text-gray-600 space-y-1">
                    <p>✓ Lazy loading with Suspense</p>
                    <p>✓ Intelligent caching system</p>
                    <p>✓ Mobile-optimized interactions</p>
                    <p>✓ Error boundaries and fallbacks</p>
                    <p>✓ Analytics integration</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
};

export default DailyOutlookTestPage;