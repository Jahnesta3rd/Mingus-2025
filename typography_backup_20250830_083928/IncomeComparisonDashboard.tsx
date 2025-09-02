import React, { useState, useEffect } from 'react';
import SalaryBenchmarkWidget from './SalaryBenchmarkWidget';
import CareerAdvancementSimulator from './CareerAdvancementSimulator';
import CulturalContextIntegration from './CulturalContextIntegration';
import SocialSharing from '../common/SocialSharing';
import TouchOptimizedChart from '../common/TouchOptimizedChart';
import { usePWA } from '../../hooks/usePWA';
import { SalaryBenchmarkFilters } from '../../types/salary';

interface IncomeComparisonDashboardProps {
  className?: string;
}

const IncomeComparisonDashboard: React.FC<IncomeComparisonDashboardProps> = ({
  className = ''
}) => {
  const [userSalary, setUserSalary] = useState(75000);
  const [userIndustry, setUserIndustry] = useState('Technology');
  const [activeSection, setActiveSection] = useState<'benchmark' | 'career' | 'cultural'>('benchmark');
  const [isMobile, setIsMobile] = useState(false);
  const [showInstallPrompt, setShowInstallPrompt] = useState(false);
  const [showOfflineIndicator, setShowOfflineIndicator] = useState(false);
  
  const { isOnline, canInstall, installApp, isInstalled } = usePWA();

  // Detect mobile screen size
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };
    
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // Handle offline/online status
  useEffect(() => {
    setShowOfflineIndicator(!isOnline);
    if (!isOnline) {
      setTimeout(() => setShowOfflineIndicator(false), 5000);
    }
  }, [isOnline]);

  // Show install prompt for eligible users
  useEffect(() => {
    if (canInstall && !isInstalled && isMobile) {
      setTimeout(() => setShowInstallPrompt(true), 3000);
    }
  }, [canInstall, isInstalled, isMobile]);

  const handleFiltersChange = (filters: SalaryBenchmarkFilters) => {
    // Update user industry when filters change
    setUserIndustry(filters.industry);
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount);
  };

  return (
    <div className={`min-h-screen bg-gray-50 ${className}`}>
      {/* Offline Indicator */}
      {showOfflineIndicator && (
        <div className="fixed top-0 left-0 right-0 z-50 bg-yellow-500 text-white p-3 text-center">
          <div className="flex items-center justify-center gap-2">
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
            <span className="text-sm font-medium">You're offline - Some features may be limited</span>
          </div>
        </div>
      )}

      {/* Install Prompt */}
      {showInstallPrompt && (
        <div className="fixed top-0 left-0 right-0 z-50 bg-blue-600 text-white p-4">
          <div className="flex items-center justify-between max-w-7xl mx-auto">
            <div className="flex items-center gap-3">
              <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clipRule="evenodd" />
              </svg>
              <div>
                <div className="font-medium">Install Mingus Income Dashboard</div>
                <div className="text-sm opacity-90">Get quick access and work offline</div>
              </div>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setShowInstallPrompt(false)}
                className="px-3 py-1 text-sm bg-blue-700 rounded hover:bg-blue-800 transition-colors"
              >
                Not now
              </button>
              <button
                onClick={() => {
                  installApp();
                  setShowInstallPrompt(false);
                }}
                className="px-3 py-1 text-sm bg-white text-blue-600 rounded hover:bg-gray-100 transition-colors"
              >
                Install
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="py-6">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  Income Comparison Dashboard
                </h1>
                <p className="mt-1 text-sm text-gray-600">
                  Maximize your earning potential with data-driven insights for African American professionals
                </p>
              </div>
              
              {/* Quick Stats */}
              <div className="mt-4 sm:mt-0 flex space-x-4">
                <div className="text-center">
                  <div className="text-lg font-semibold text-blue-600">
                    {formatCurrency(userSalary)}
                  </div>
                  <div className="text-xs text-gray-500">Current Salary</div>
                </div>
                <div className="text-center">
                  <div className="text-lg font-semibold text-green-600">
                    {formatCurrency(100000)}
                  </div>
                  <div className="text-xs text-gray-500">Target Salary</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Mobile Navigation */}
      {isMobile && (
        <div className="bg-white border-b sticky top-0 z-10">
          <div className="flex">
            <button
              onClick={() => setActiveSection('benchmark')}
              className={`flex-1 py-3 px-4 text-sm font-medium border-b-2 transition-colors ${
                activeSection === 'benchmark'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500'
              }`}
            >
              Benchmark
            </button>
            <button
              onClick={() => setActiveSection('career')}
              className={`flex-1 py-3 px-4 text-sm font-medium border-b-2 transition-colors ${
                activeSection === 'career'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500'
              }`}
            >
              Career Path
            </button>
            <button
              onClick={() => setActiveSection('cultural')}
              className={`flex-1 py-3 px-4 text-sm font-medium border-b-2 transition-colors ${
                activeSection === 'cultural'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500'
              }`}
            >
              Equity
            </button>
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {isMobile ? (
          // Mobile Layout - Single Column
          <div className="space-y-6">
            {activeSection === 'benchmark' && (
              <SalaryBenchmarkWidget
                userSalary={userSalary}
                onFiltersChange={handleFiltersChange}
              />
            )}
            {activeSection === 'career' && (
              <CareerAdvancementSimulator
                currentSalary={userSalary}
                targetSalary={100000}
              />
            )}
            {activeSection === 'cultural' && (
              <CulturalContextIntegration
                userSalary={userSalary}
                industry={userIndustry}
              />
            )}
          </div>
        ) : (
          // Desktop Layout - Grid
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Salary Benchmark Widget */}
            <div className="lg:col-span-1">
              <SalaryBenchmarkWidget
                userSalary={userSalary}
                onFiltersChange={handleFiltersChange}
              />
            </div>

            {/* Career Advancement Simulator */}
            <div className="lg:col-span-1">
              <CareerAdvancementSimulator
                currentSalary={userSalary}
                targetSalary={100000}
              />
            </div>

            {/* Cultural Context Integration */}
            <div className="lg:col-span-1">
              <CulturalContextIntegration
                userSalary={userSalary}
                industry={userIndustry}
              />
            </div>
          </div>
        )}

        {/* Call to Action Section */}
        <div className="mt-12 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg p-8 text-white">
          <div className="text-center">
            <h2 className="text-2xl font-bold mb-4">
              Ready to Accelerate Your Career?
            </h2>
            <p className="text-blue-100 mb-6 max-w-2xl mx-auto">
              Join thousands of African American professionals who are using data-driven insights
              to negotiate better salaries, advance their careers, and build generational wealth.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <button className="bg-white text-blue-600 px-6 py-3 rounded-md font-medium hover:bg-gray-100 transition-colors">
                Get Your Personalized Report
              </button>
              <button className="border border-white text-white px-6 py-3 rounded-md font-medium hover:bg-white hover:text-blue-600 transition-colors">
                Join Our Community
              </button>
            </div>
          </div>
        </div>

        {/* Social Sharing Section */}
        <div className="mt-8 text-center">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Share Your Insights
          </h3>
          <div className="flex flex-wrap justify-center gap-4">
            <SocialSharing
              title="My Salary Comparison - Mingus Income Dashboard"
              text={`I'm earning $${userSalary.toLocaleString()} in ${userIndustry}. See how you compare!`}
              variant="button"
              className="bg-gradient-to-r from-blue-600 to-purple-600"
            />
            <SocialSharing
              title="My Career Advancement Plan - Mingus Income Dashboard"
              text="I'm planning my path to higher earnings. Check out my strategy!"
              variant="button"
              className="bg-gradient-to-r from-green-600 to-blue-600"
            />
          </div>
        </div>

        {/* Trust Indicators */}
        <div className="mt-12">
          <div className="text-center">
            <h3 className="text-lg font-semibold text-gray-900 mb-6">
              Trusted by Leading Organizations
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-8 items-center opacity-60">
              <div className="text-gray-400 font-semibold">National Black MBA Association</div>
              <div className="text-gray-400 font-semibold">Black Enterprise</div>
              <div className="text-gray-400 font-semibold">National Society of Black Engineers</div>
              <div className="text-gray-400 font-semibold">Urban League</div>
            </div>
          </div>
        </div>

        {/* Data Privacy Notice */}
        <div className="mt-8 text-center">
          <p className="text-xs text-gray-500">
            Your data is protected and used only to provide personalized insights. 
            We never share your information with third parties without your consent.
          </p>
        </div>

        {/* Floating Share Button for Mobile */}
        {isMobile && (
          <SocialSharing
            title="Mingus Income Dashboard"
            text="Check out this amazing income comparison dashboard for African American professionals!"
            variant="floating"
          />
        )}
      </div>
    </div>
  );
};

export default IncomeComparisonDashboard; 