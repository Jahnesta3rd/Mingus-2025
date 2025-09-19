import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router } from 'react-router-dom';
import OptimalLocationRouter from '../components/OptimalLocation/OptimalLocationRouter';

// Mock data for testing
const mockUserTiers = [
  { tier: 'budget', label: 'Budget', color: 'bg-gray-100 text-gray-800' },
  { tier: 'budget_career_vehicle', label: 'Budget Career Vehicle', color: 'bg-green-100 text-green-800' },
  { tier: 'mid_tier', label: 'Mid-tier', color: 'bg-blue-100 text-blue-800' },
  { tier: 'professional', label: 'Professional', color: 'bg-purple-100 text-purple-800' }
];

const mockScenarios = [
  {
    id: '1',
    name: 'Downtown Living',
    location: 'San Francisco, CA',
    budget: 3500,
    commuteTime: 15,
    qualityOfLife: 8,
    careerOpportunities: 9,
    costOfLiving: 6,
    createdAt: new Date('2024-01-15'),
    isActive: true
  },
  {
    id: '2',
    name: 'Suburban Family',
    location: 'Palo Alto, CA',
    budget: 2800,
    commuteTime: 45,
    qualityOfLife: 9,
    careerOpportunities: 8,
    costOfLiving: 7,
    createdAt: new Date('2024-01-10'),
    isActive: false
  },
  {
    id: '3',
    name: 'Remote Work Setup',
    location: 'Austin, TX',
    budget: 2000,
    commuteTime: 0,
    qualityOfLife: 8,
    careerOpportunities: 7,
    costOfLiving: 8,
    createdAt: new Date('2024-01-05'),
    isActive: false
  }
];

const mockSearchResults = [
  {
    id: '1',
    title: 'Modern Apartment in SOMA',
    location: 'San Francisco, CA',
    price: 3200,
    bedrooms: 1,
    bathrooms: 1,
    amenities: ['Gym', 'Pool', 'Parking'],
    commuteTime: 20,
    walkScore: 85
  },
  {
    id: '2',
    title: 'Charming Victorian House',
    location: 'Mission District, San Francisco, CA',
    price: 4500,
    bedrooms: 2,
    bathrooms: 1,
    amenities: ['Garden', 'Parking', 'Fireplace'],
    commuteTime: 25,
    walkScore: 92
  },
  {
    id: '3',
    title: 'Luxury Condo with City Views',
    location: 'Financial District, San Francisco, CA',
    price: 5500,
    bedrooms: 2,
    bathrooms: 2,
    amenities: ['Concierge', 'Gym', 'Rooftop', 'Parking'],
    commuteTime: 10,
    walkScore: 95
  }
];

// Test Controls Component
const TestControls: React.FC<{
  currentTier: string;
  onTierChange: (tier: string) => void;
  onReset: () => void;
  onLoadMockData: () => void;
}> = ({ currentTier, onTierChange, onReset, onLoadMockData }) => {
  return (
    <div className="fixed top-4 right-4 bg-white rounded-lg shadow-lg p-4 z-50 max-w-sm">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Test Controls</h3>
      
      {/* Tier Selection */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          User Tier
        </label>
        <select
          value={currentTier}
          onChange={(e) => onTierChange(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-violet-500 focus:border-violet-500"
        >
          {mockUserTiers.map((tier) => (
            <option key={tier.tier} value={tier.tier}>
              {tier.label}
            </option>
          ))}
        </select>
      </div>

      {/* Action Buttons */}
      <div className="space-y-2">
        <button
          onClick={onLoadMockData}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
        >
          Load Mock Data
        </button>
        <button
          onClick={onReset}
          className="w-full bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
        >
          Reset Component
        </button>
      </div>

      {/* Current State Display */}
      <div className="mt-4 p-3 bg-gray-50 rounded-lg">
        <h4 className="text-sm font-medium text-gray-900 mb-2">Current State</h4>
        <div className="text-xs text-gray-600 space-y-1">
          <div>Tier: <span className="font-medium">{currentTier}</span></div>
          <div>Mock Data: <span className="font-medium">Loaded</span></div>
        </div>
      </div>
    </div>
  );
};

// Responsive Test Component
const ResponsiveTest: React.FC = () => {
  const [currentBreakpoint, setCurrentBreakpoint] = useState<string>('');
  const [windowSize, setWindowSize] = useState({ width: 0, height: 0 });

  useEffect(() => {
    const updateWindowSize = () => {
      const width = window.innerWidth;
      const height = window.innerHeight;
      setWindowSize({ width, height });

      // Determine current breakpoint
      if (width <= 375) {
        setCurrentBreakpoint('Mobile Small (≤375px)');
      } else if (width <= 414) {
        setCurrentBreakpoint('Mobile Medium (376px-414px)');
      } else if (width <= 768) {
        setCurrentBreakpoint('Mobile Large (415px-768px)');
      } else if (width <= 1024) {
        setCurrentBreakpoint('Tablet (769px-1024px)');
      } else {
        setCurrentBreakpoint('Desktop (≥1025px)');
      }
    };

    updateWindowSize();
    window.addEventListener('resize', updateWindowSize);
    return () => window.removeEventListener('resize', updateWindowSize);
  }, []);

  return (
    <div className="fixed bottom-4 left-4 bg-black/80 text-white p-3 rounded-lg z-50 text-sm">
      <div className="font-bold mb-1">Responsive Test</div>
      <div>Breakpoint: {currentBreakpoint}</div>
      <div>Size: {windowSize.width} × {windowSize.height}</div>
    </div>
  );
};

// Main Test Page Component
const OptimalLocationTestPage: React.FC = () => {
  const [currentTier, setCurrentTier] = useState('mid_tier');
  const [componentKey, setComponentKey] = useState(0);

  // Mock the useAuth hook
  const mockAuth = {
    user: {
      id: 'test-user',
      email: 'test@example.com',
      name: 'Test User',
      token: 'test-token',
      isAuthenticated: true
    },
    isAuthenticated: true,
    loading: false,
    login: async () => {},
    logout: () => {}
  };

  // Mock the useAnalytics hook
  const mockAnalytics = {
    trackPageView: async (page: string, metadata?: any) => {
      console.log('Analytics - Page View:', page, metadata);
    },
    trackInteraction: async (interaction: string, data?: any) => {
      console.log('Analytics - Interaction:', interaction, data);
    },
    trackError: async (error: Error, context?: any) => {
      console.log('Analytics - Error:', error, context);
    },
    getSessionId: () => 'test-session',
    getUserId: () => 'test-user'
  };

  // Mock fetch for API calls
  useEffect(() => {
    const originalFetch = window.fetch;
    
    window.fetch = jest.fn().mockImplementation((url: string) => {
      console.log('Mock API Call:', url);
      
      if (url.includes('/api/user/tier')) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ tier: currentTier })
        });
      }
      
      if (url.includes('/api/optimal-location/scenarios')) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ scenarios: mockScenarios })
        });
      }
      
      if (url.includes('/api/optimal-location/housing-search')) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ results: mockSearchResults })
        });
      }
      
      if (url.includes('/api/analytics/')) {
        return Promise.resolve({
          ok: true,
          json: async () => ({ success: true })
        });
      }
      
      return originalFetch(url);
    });

    return () => {
      window.fetch = originalFetch;
    };
  }, [currentTier]);

  const handleTierChange = (tier: string) => {
    setCurrentTier(tier);
    setComponentKey(prev => prev + 1); // Force component re-render
  };

  const handleReset = () => {
    setComponentKey(prev => prev + 1);
  };

  const handleLoadMockData = () => {
    // This would typically load mock data into the component
    console.log('Loading mock data...');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Test Controls */}
      <TestControls
        currentTier={currentTier}
        onTierChange={handleTierChange}
        onReset={handleReset}
        onLoadMockData={handleLoadMockData}
      />

      {/* Responsive Test Indicator */}
      <ResponsiveTest />

      {/* Mock Provider Wrapper */}
      <div>
        {/* Mock the hooks at the module level */}
        {(() => {
          // This is a hack to mock the hooks - in a real test, you'd use proper mocking
          const originalUseAuth = require('../hooks/useAuth').useAuth;
          const originalUseAnalytics = require('../hooks/useAnalytics').useAnalytics;
          
          require('../hooks/useAuth').useAuth = () => mockAuth;
          require('../hooks/useAnalytics').useAnalytics = () => mockAnalytics;
          
          return (
            <OptimalLocationRouter key={componentKey} />
          );
        })()}
      </div>

      {/* Test Instructions */}
      <div className="fixed bottom-4 right-4 bg-white rounded-lg shadow-lg p-4 z-50 max-w-sm">
        <h3 className="text-lg font-semibold text-gray-900 mb-2">Test Instructions</h3>
        <div className="text-sm text-gray-600 space-y-2">
          <div>• Use the tier selector to test different user tiers</div>
          <div>• Try different screen sizes to test responsiveness</div>
          <div>• Test form submissions and navigation</div>
          <div>• Check accessibility with keyboard navigation</div>
          <div>• Verify error handling and loading states</div>
        </div>
      </div>
    </div>
  );
};

// Test Page with Router
const OptimalLocationTestPageWithRouter: React.FC = () => {
  return (
    <Router>
      <OptimalLocationTestPage />
    </Router>
  );
};

export default OptimalLocationTestPageWithRouter;
