import React from 'react';
import LocationIntelligenceMap from '../components/LocationIntelligenceMap';

const LocationMapTestPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Location Intelligence Map
          </h1>
          <p className="text-lg text-gray-600">
            Interactive geographic visualization of career opportunities with commute analysis
          </p>
        </div>

        {/* Map Component */}
        <div className="mb-8">
          <LocationIntelligenceMap className="w-full" />
        </div>

        {/* Features Overview */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-lg p-6 shadow-sm">
            <div className="flex items-center mb-3">
              <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center mr-3">
                <span className="text-blue-600 text-sm font-semibold">🗺️</span>
              </div>
              <h3 className="text-lg font-semibold text-gray-900">Interactive Map</h3>
            </div>
            <p className="text-gray-600 text-sm">
              Real-time job visualization with Google Maps integration, radius controls, and tier-based markers.
            </p>
          </div>

          <div className="bg-white rounded-lg p-6 shadow-sm">
            <div className="flex items-center mb-3">
              <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center mr-3">
                <span className="text-green-600 text-sm font-semibold">🚗</span>
              </div>
              <h3 className="text-lg font-semibold text-gray-900">Commute Analysis</h3>
            </div>
            <p className="text-gray-600 text-sm">
              Multi-mode transportation analysis with real-time routes, cost calculations, and time estimates.
            </p>
          </div>

          <div className="bg-white rounded-lg p-6 shadow-sm">
            <div className="flex items-center mb-3">
              <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center mr-3">
                <span className="text-purple-600 text-sm font-semibold">📊</span>
              </div>
              <h3 className="text-lg font-semibold text-gray-900">Analytics Integration</h3>
            </div>
            <p className="text-gray-600 text-sm">
              Comprehensive user interaction tracking and location analytics for data-driven insights.
            </p>
          </div>
        </div>

        {/* Technical Details */}
        <div className="bg-white rounded-lg p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Technical Implementation</h3>
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-medium text-gray-900 mb-2">Features Implemented</h4>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>✅ Google Maps integration with custom styling</li>
                <li>✅ Real-time job marker visualization</li>
                <li>✅ Radius adjustment controls (5, 10, 30 miles, nationwide)</li>
                <li>✅ Commute time analysis (driving, transit, walking)</li>
                <li>✅ Interactive job details panel</li>
                <li>✅ Location analytics tracking</li>
                <li>✅ Responsive design for mobile</li>
                <li>✅ Accessibility features</li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium text-gray-900 mb-2">API Integration</h4>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• <code>/api/risk/jobs-in-radius</code> - Job data fetching</li>
                <li>• <code>/api/location/geocode</code> - Location geocoding</li>
                <li>• <code>/api/analytics/user-behavior/track-interaction</code> - Analytics</li>
                <li>• Google Maps Directions API - Route calculation</li>
                <li>• Google Maps Geocoding API - Address resolution</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Usage Instructions */}
        <div className="bg-blue-50 rounded-lg p-6 mt-8">
          <h3 className="text-lg font-semibold text-blue-900 mb-3">How to Use</h3>
          <div className="text-blue-800 text-sm space-y-2">
            <p>1. <strong>Allow Location Access:</strong> The map will request your location for accurate job searching</p>
            <p>2. <strong>Adjust Radius:</strong> Use the radius selector to expand or narrow your search area</p>
            <p>3. <strong>Explore Jobs:</strong> Click on job markers to see detailed information and commute options</p>
            <p>4. <strong>Change Commute Mode:</strong> Switch between driving, transit, and walking to see different route options</p>
            <p>5. <strong>View Details:</strong> Use the job details panel to see salary ranges and apply for positions</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LocationMapTestPage;
