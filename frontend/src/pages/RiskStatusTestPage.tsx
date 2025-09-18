import React from 'react';
import RiskStatusHero from '../components/RiskStatusHero';

const RiskStatusTestPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Risk Status Hero Component Test
          </h1>
          <p className="text-gray-600">
            Testing the RiskStatusHero component with different states and responsive design.
          </p>
        </div>

        {/* Test different container sizes */}
        <div className="space-y-8">
          {/* Full width */}
          <div>
            <h2 className="text-xl font-semibold text-gray-800 mb-4">Full Width</h2>
            <RiskStatusHero />
          </div>

          {/* Medium width */}
          <div>
            <h2 className="text-xl font-semibold text-gray-800 mb-4">Medium Width</h2>
            <div className="max-w-2xl">
              <RiskStatusHero />
            </div>
          </div>

          {/* Small width */}
          <div>
            <h2 className="text-xl font-semibold text-gray-800 mb-4">Small Width</h2>
            <div className="max-w-md">
              <RiskStatusHero />
            </div>
          </div>

          {/* Mobile simulation */}
          <div>
            <h2 className="text-xl font-semibold text-gray-800 mb-4">Mobile Simulation</h2>
            <div className="max-w-sm mx-auto">
              <RiskStatusHero />
            </div>
          </div>
        </div>

        {/* Component Features Documentation */}
        <div className="mt-12 bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Component Features</h2>
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <h3 className="font-semibold text-gray-700 mb-2">Visual States</h3>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Secure (Green) - Career on track</li>
                <li>• Watchful (Amber) - Market changes detected</li>
                <li>• Action Needed (Orange) - Proactive steps recommended</li>
                <li>• Urgent (Red) - Immediate action required</li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold text-gray-700 mb-2">Features</h3>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Animated circular progress ring</li>
                <li>• Real-time risk score display</li>
                <li>• Primary threat preview</li>
                <li>• Context-aware CTA buttons</li>
                <li>• Emergency indicators</li>
                <li>• Loading and error states</li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold text-gray-700 mb-2">Accessibility</h3>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• ARIA labels for screen readers</li>
                <li>• Keyboard navigation support</li>
                <li>• Focus management</li>
                <li>• Semantic HTML structure</li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold text-gray-700 mb-2">Analytics Integration</h3>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Risk hero viewed events</li>
                <li>• CTA click tracking</li>
                <li>• Risk level analytics</li>
                <li>• User interaction metrics</li>
              </ul>
            </div>
          </div>
        </div>

        {/* API Integration Info */}
        <div className="mt-8 bg-blue-50 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-blue-800 mb-2">API Integration</h2>
          <p className="text-blue-700 text-sm mb-3">
            This component integrates with the existing risk analytics API:
          </p>
          <div className="bg-white rounded p-4 text-sm font-mono text-gray-700">
            <div>Endpoint: <span className="text-blue-600">POST /api/risk/assess-and-track</span></div>
            <div>Analytics: <span className="text-blue-600">POST /api/analytics/user-behavior/track-interaction</span></div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RiskStatusTestPage;
