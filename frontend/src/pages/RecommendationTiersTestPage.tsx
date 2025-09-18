import React, { useState } from 'react';
import RecommendationTiers from '../components/RecommendationTiers';

const RecommendationTiersTestPage: React.FC = () => {
  const [userId, setUserId] = useState('test-user-123');
  const [locationRadius, setLocationRadius] = useState(10);

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Recommendation Tiers Component Test
          </h1>
          <p className="text-gray-600 mb-6">
            Testing the RecommendationTiers component with three-tier job recommendations and interactive features.
          </p>

          {/* Test Controls */}
          <div className="bg-white rounded-lg shadow p-6 mb-8">
            <h2 className="text-lg font-semibold text-gray-800 mb-4">Test Controls</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  User ID
                </label>
                <input
                  type="text"
                  value={userId}
                  onChange={(e) => setUserId(e.target.value)}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Enter user ID"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Location Radius (miles)
                </label>
                <input
                  type="number"
                  value={locationRadius}
                  onChange={(e) => setLocationRadius(Number(e.target.value))}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  min="1"
                  max="999"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Component Test */}
        <RecommendationTiers
          userId={userId}
          locationRadius={locationRadius}
          className="mb-8"
        />

        {/* Component Features Documentation */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Component Features</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div>
              <h3 className="font-semibold text-gray-700 mb-2">Three Tiers</h3>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• <span className="text-blue-600 font-medium">Conservative</span> - Safe growth (15-20% increase)</li>
                <li>• <span className="text-purple-600 font-medium">Optimal</span> - Strategic advance (25-30% increase)</li>
                <li>• <span className="text-orange-600 font-medium">Stretch</span> - Ambitious leap (35%+ increase)</li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold text-gray-700 mb-2">Interactive Features</h3>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Tier expansion/collapse</li>
                <li>• Comparison mode</li>
                <li>• Location radius filtering</li>
                <li>• Job preview cards</li>
                <li>• Apply button interactions</li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold text-gray-700 mb-2">Job Information</h3>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Salary range display</li>
                <li>• Success probability</li>
                <li>• Location and commute</li>
                <li>• Company details</li>
                <li>• Skills gap analysis</li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold text-gray-700 mb-2">Analytics Integration</h3>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Tier expansion tracking</li>
                <li>• Job interaction events</li>
                <li>• Location filter changes</li>
                <li>• Comparison mode usage</li>
                <li>• Apply button clicks</li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold text-gray-700 mb-2">Responsive Design</h3>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Mobile-first approach</li>
                <li>• Adaptive grid layouts</li>
                <li>• Touch-friendly interactions</li>
                <li>• Optimized typography</li>
                <li>• Flexible spacing</li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold text-gray-700 mb-2">Accessibility</h3>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• ARIA labels and descriptions</li>
                <li>• Keyboard navigation</li>
                <li>• Focus management</li>
                <li>• Screen reader support</li>
                <li>• Semantic HTML structure</li>
              </ul>
            </div>
          </div>
        </div>

        {/* API Integration Info */}
        <div className="mt-8 bg-blue-50 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-blue-800 mb-2">API Integration</h2>
          <p className="text-blue-700 text-sm mb-3">
            This component integrates with the existing risk analytics and recommendation APIs:
          </p>
          <div className="bg-white rounded p-4 text-sm font-mono text-gray-700">
            <div>Endpoint: <span className="text-blue-600">POST /api/risk/trigger-recommendations</span></div>
            <div>Analytics: <span className="text-blue-600">POST /api/analytics/user-behavior/track-interaction</span></div>
            <div>Data: <span className="text-blue-600">Three-tier job recommendations with detailed analysis</span></div>
          </div>
        </div>

        {/* Test Scenarios */}
        <div className="mt-8 bg-green-50 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-green-800 mb-2">Test Scenarios</h2>
          <div className="grid md:grid-cols-2 gap-4 text-sm text-green-700">
            <div>
              <h3 className="font-semibold mb-2">Basic Functionality</h3>
              <ul className="space-y-1">
                <li>• Load recommendations with default settings</li>
                <li>• Test tier expansion/collapse</li>
                <li>• Try comparison mode toggle</li>
                <li>• Change location radius</li>
                <li>• Click apply buttons</li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold mb-2">Edge Cases</h3>
              <ul className="space-y-1">
                <li>• Test with no jobs in area</li>
                <li>• Test with different user IDs</li>
                <li>• Test API error handling</li>
                <li>• Test loading states</li>
                <li>• Test mobile responsiveness</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RecommendationTiersTestPage;
