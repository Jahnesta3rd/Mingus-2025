import React, { useState, useEffect } from 'react';
import { 
  Calculator, 
  Car, 
  DollarSign, 
  TrendingUp, 
  Target, 
  BarChart3,
  ArrowLeft,
  CheckCircle,
  Star,
  Users,
  Clock,
  MapPin
} from 'lucide-react';
import CareerVehicleOptimization from '../components/CareerVehicleOptimization';
import { useAnalytics } from '../hooks/useAnalytics';

// Mock data for demonstration
const mockVehicles = [
  {
    id: '1',
    make: 'Honda',
    model: 'Civic',
    year: 2018,
    mpg: 32,
    fuelType: 'gasoline' as const,
    currentMileage: 45000,
    monthlyMiles: 1200
  },
  {
    id: '2',
    make: 'Toyota',
    model: 'Prius',
    year: 2020,
    mpg: 54,
    fuelType: 'hybrid' as const,
    currentMileage: 25000,
    monthlyMiles: 800
  },
  {
    id: '3',
    make: 'Ford',
    model: 'F-150',
    year: 2019,
    mpg: 22,
    fuelType: 'gasoline' as const,
    currentMileage: 60000,
    monthlyMiles: 1500
  }
];

const CareerVehicleOptimizationPage: React.FC = () => {
  const { trackPageView, trackInteraction } = useAnalytics();
  const [showFeature, setShowFeature] = useState(false);

  useEffect(() => {
    trackPageView('career_vehicle_optimization_page');
  }, [trackPageView]);

  const handleUpgradeClick = () => {
    trackInteraction('upgrade_career_vehicle_addon_clicked', {
      source: 'career_vehicle_page'
    });
    // In a real app, this would trigger the upgrade flow
    console.log('Upgrade to career-vehicle optimization add-on');
  };

  if (!showFeature) {
    return (
      <div className="min-h-screen bg-gray-900 text-white">
        {/* Navigation */}
        <div className="bg-gray-800 border-b border-gray-700">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-16">
              <div className="flex items-center space-x-4">
                <button
                  onClick={() => window.history.back()}
                  className="flex items-center space-x-2 text-gray-400 hover:text-white transition-colors duration-200"
                >
                  <ArrowLeft className="w-5 h-5" />
                  <span>Back</span>
                </button>
                <div className="h-6 w-px bg-gray-600" />
                <h1 className="text-xl font-semibold">Career-Vehicle Optimization</h1>
              </div>
            </div>
          </div>
        </div>

        {/* Hero Section */}
        <div className="bg-gradient-to-br from-violet-900 via-purple-900 to-indigo-900">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
            <div className="text-center">
              <div className="mb-8">
                <div className="inline-flex items-center justify-center w-20 h-20 bg-violet-600 rounded-full mb-6">
                  <Calculator className="w-10 h-10 text-white" />
                </div>
                <h1 className="text-4xl md:text-5xl font-bold text-white mb-4">
                  Career-Vehicle Optimization
                </h1>
                <p className="text-xl text-violet-200 mb-8 max-w-3xl mx-auto">
                  Make every dollar count with our Budget tier add-on. Optimize job opportunities 
                  and commute costs to maximize your true take-home pay.
                </p>
              </div>

              {/* Pricing Card */}
              <div className="bg-white bg-opacity-10 backdrop-blur-lg rounded-2xl p-8 max-w-md mx-auto mb-12">
                <div className="text-center">
                  <div className="text-4xl font-bold text-white mb-2">$7/month</div>
                  <div className="text-violet-200 mb-4">Add-on to Budget tier</div>
                  <div className="text-sm text-violet-300 mb-6">
                    Budget tier ($15) + Career-Vehicle add-on ($7) = $22 total
                  </div>
                  <button
                    onClick={() => setShowFeature(true)}
                    className="w-full bg-violet-600 hover:bg-violet-700 text-white px-8 py-4 rounded-lg font-semibold text-lg transition-colors duration-200"
                  >
                    Try Career-Vehicle Optimization
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Features Section */}
        <div className="py-16 bg-gray-900">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-16">
              <h2 className="text-3xl font-bold text-white mb-4">
                Four Powerful Features for Budget-Conscious Users
              </h2>
              <p className="text-xl text-gray-400 max-w-3xl mx-auto">
                Designed specifically for users who need to optimize every financial decision
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              {/* Job Opportunity True Cost Calculator */}
              <div className="bg-gray-800 rounded-xl p-8">
                <div className="flex items-center space-x-4 mb-6">
                  <div className="w-12 h-12 bg-violet-600 rounded-lg flex items-center justify-center">
                    <DollarSign className="w-6 h-6 text-white" />
                  </div>
                  <h3 className="text-xl font-semibold text-white">Job Opportunity True Cost Calculator</h3>
                </div>
                <p className="text-gray-400 mb-6">
                  Input job salary and location to calculate total transportation costs including fuel, 
                  wear, parking, and more. See your "real take-home" after transportation expenses.
                </p>
                <ul className="space-y-2 text-gray-300">
                  <li className="flex items-center space-x-2">
                    <CheckCircle className="w-4 h-4 text-green-400" />
                    <span>Compare multiple job offers side-by-side</span>
                  </li>
                  <li className="flex items-center space-x-2">
                    <CheckCircle className="w-4 h-4 text-green-400" />
                    <span>Calculate true compensation after commute costs</span>
                  </li>
                  <li className="flex items-center space-x-2">
                    <CheckCircle className="w-4 h-4 text-green-400" />
                    <span>Factor in parking, tolls, and vehicle wear</span>
                  </li>
                </ul>
              </div>

              {/* Commute Cost Impact Analysis */}
              <div className="bg-gray-800 rounded-xl p-8">
                <div className="flex items-center space-x-4 mb-6">
                  <div className="w-12 h-12 bg-blue-600 rounded-lg flex items-center justify-center">
                    <BarChart3 className="w-6 h-6 text-white" />
                  </div>
                  <h3 className="text-xl font-semibold text-white">Commute Cost Impact Analysis</h3>
                </div>
                <p className="text-gray-400 mb-6">
                  Get annual transportation cost projections for different job locations. 
                  Calculate break-even salary and compare driving vs public transportation.
                </p>
                <ul className="space-y-2 text-gray-300">
                  <li className="flex items-center space-x-2">
                    <CheckCircle className="w-4 h-4 text-green-400" />
                    <span>Annual cost projections for different locations</span>
                  </li>
                  <li className="flex items-center space-x-2">
                    <CheckCircle className="w-4 h-4 text-green-400" />
                    <span>Break-even salary calculator</span>
                  </li>
                  <li className="flex items-center space-x-2">
                    <CheckCircle className="w-4 h-4 text-green-400" />
                    <span>Public transport vs driving comparison</span>
                  </li>
                </ul>
              </div>

              {/* Career Move Financial Planning */}
              <div className="bg-gray-800 rounded-xl p-8">
                <div className="flex items-center space-x-4 mb-6">
                  <div className="w-12 h-12 bg-green-600 rounded-lg flex items-center justify-center">
                    <MapPin className="w-6 h-6 text-white" />
                  </div>
                  <h3 className="text-xl font-semibold text-white">Career Move Financial Planning</h3>
                </div>
                <p className="text-gray-400 mb-6">
                  Plan career moves with moving cost estimates, vehicle replacement timing, 
                  and emergency fund adjustments for different commute requirements.
                </p>
                <ul className="space-y-2 text-gray-300">
                  <li className="flex items-center space-x-2">
                    <CheckCircle className="w-4 h-4 text-green-400" />
                    <span>Moving cost estimates for job location changes</span>
                  </li>
                  <li className="flex items-center space-x-2">
                    <CheckCircle className="w-4 h-4 text-green-400" />
                    <span>Vehicle replacement timing based on new commute</span>
                  </li>
                  <li className="flex items-center space-x-2">
                    <CheckCircle className="w-4 h-4 text-green-400" />
                    <span>Emergency fund adjustments for longer commutes</span>
                  </li>
                </ul>
              </div>

              {/* Budget-Friendly Optimization */}
              <div className="bg-gray-800 rounded-xl p-8">
                <div className="flex items-center space-x-4 mb-6">
                  <div className="w-12 h-12 bg-orange-600 rounded-lg flex items-center justify-center">
                    <Target className="w-6 h-6 text-white" />
                  </div>
                  <h3 className="text-xl font-semibold text-white">Budget-Friendly Optimization</h3>
                </div>
                <p className="text-gray-400 mb-6">
                  Identify jobs within optimal commute radius, get gas-saving route recommendations, 
                  and optimize maintenance timing around job changes.
                </p>
                <ul className="space-y-2 text-gray-300">
                  <li className="flex items-center space-x-2">
                    <CheckCircle className="w-4 h-4 text-green-400" />
                    <span>Jobs within optimal commute radius for your vehicle</span>
                  </li>
                  <li className="flex items-center space-x-2">
                    <CheckCircle className="w-4 h-4 text-green-400" />
                    <span>Gas-saving route recommendations</span>
                  </li>
                  <li className="flex items-center space-x-2">
                    <CheckCircle className="w-4 h-4 text-green-400" />
                    <span>Car replacement vs repair decisions</span>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        {/* Target Audience Section */}
        <div className="py-16 bg-gray-800">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-bold text-white mb-4">
                Perfect for Budget-Tier Users
              </h2>
              <p className="text-xl text-gray-400 max-w-3xl mx-auto">
                Addresses the core pain point: transportation costs eating into wages
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <div className="text-center">
                <div className="w-16 h-16 bg-violet-600 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Users className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-lg font-semibold text-white mb-2">Budget-Conscious</h3>
                <p className="text-gray-400">
                  For users who need to make every dollar count and optimize major life decisions
                </p>
              </div>

              <div className="text-center">
                <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Car className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-lg font-semibold text-white mb-2">Vehicle Owners</h3>
                <p className="text-gray-400">
                  Optimize transportation costs around job changes and career moves
                </p>
              </div>

              <div className="text-center">
                <div className="w-16 h-16 bg-green-600 rounded-full flex items-center justify-center mx-auto mb-4">
                  <TrendingUp className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-lg font-semibold text-white mb-2">Career Focused</h3>
                <p className="text-gray-400">
                  Make informed decisions about job opportunities and career advancement
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Tier Comparison */}
        <div className="py-16 bg-gray-900">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-bold text-white mb-4">
                Tier Comparison After Add-on
              </h2>
              <p className="text-xl text-gray-400">
                See how the career-vehicle add-on fits into our pricing structure
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              {/* Budget Tier */}
              <div className="bg-gray-800 rounded-xl p-6">
                <h3 className="text-lg font-semibold text-white mb-2">Budget</h3>
                <div className="text-2xl font-bold text-white mb-4">$15/month</div>
                <ul className="space-y-2 text-gray-300 text-sm">
                  <li>Basic financial wellness only</li>
                </ul>
              </div>

              {/* Budget + Career Transport */}
              <div className="bg-gradient-to-br from-violet-600 to-purple-600 rounded-xl p-6 relative">
                <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                  <span className="bg-yellow-400 text-yellow-900 px-3 py-1 rounded-full text-xs font-semibold">
                    RECOMMENDED
                  </span>
                </div>
                <h3 className="text-lg font-semibold text-white mb-2">Budget + Career Transport</h3>
                <div className="text-2xl font-bold text-white mb-4">$22/month</div>
                <ul className="space-y-2 text-violet-100 text-sm">
                  <li>Basic financial wellness</li>
                  <li>Job/commute optimization</li>
                  <li>True cost calculator</li>
                  <li>Career move planning</li>
                </ul>
              </div>

              {/* Mid-tier */}
              <div className="bg-gray-800 rounded-xl p-6">
                <h3 className="text-lg font-semibold text-white mb-2">Mid-tier</h3>
                <div className="text-2xl font-bold text-white mb-4">$35/month</div>
                <ul className="space-y-2 text-gray-300 text-sm">
                  <li>Complete vehicle management</li>
                  <li>Career optimization</li>
                  <li>Advanced analytics</li>
                </ul>
              </div>

              {/* Professional */}
              <div className="bg-gray-800 rounded-xl p-6">
                <h3 className="text-lg font-semibold text-white mb-2">Professional</h3>
                <div className="text-2xl font-bold text-white mb-4">$100/month</div>
                <ul className="space-y-2 text-gray-300 text-sm">
                  <li>Everything included</li>
                  <li>Business/executive features</li>
                  <li>Priority support</li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        {/* CTA Section */}
        <div className="py-16 bg-gradient-to-r from-violet-600 to-purple-600">
          <div className="max-w-4xl mx-auto text-center px-4 sm:px-6 lg:px-8">
            <h2 className="text-3xl font-bold text-white mb-4">
              Ready to Optimize Your Career and Commute?
            </h2>
            <p className="text-xl text-violet-100 mb-8">
              Start making smarter financial decisions about your job opportunities and transportation costs.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <button
                onClick={() => setShowFeature(true)}
                className="bg-white text-violet-600 px-8 py-4 rounded-lg font-semibold text-lg hover:bg-gray-100 transition-colors duration-200"
              >
                Try Career-Vehicle Optimization
              </button>
              <button
                onClick={handleUpgradeClick}
                className="border-2 border-white text-white px-8 py-4 rounded-lg font-semibold text-lg hover:bg-white hover:text-violet-600 transition-colors duration-200"
              >
                Upgrade Now
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Navigation */}
      <div className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setShowFeature(false)}
                className="flex items-center space-x-2 text-gray-400 hover:text-white transition-colors duration-200"
              >
                <ArrowLeft className="w-5 h-5" />
                <span>Back to Overview</span>
              </button>
              <div className="h-6 w-px bg-gray-600" />
              <h1 className="text-xl font-semibold">Career-Vehicle Optimization</h1>
            </div>
            <div className="flex items-center space-x-2">
              <div className="bg-violet-600 text-white px-3 py-1 rounded-full text-sm font-medium">
                Add-on Active
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <CareerVehicleOptimization 
          vehicles={mockVehicles}
          className="w-full"
        />
      </div>
    </div>
  );
};

export default CareerVehicleOptimizationPage;
