import React, { useState, useRef, useEffect } from 'react';
import { 
  Car, 
  Wrench, 
  DollarSign, 
  Fuel, 
  Calendar, 
  MapPin, 
  CheckCircle, 
  AlertCircle, 
  ArrowRight, 
  ArrowLeft,
  Clock,
  TrendingUp,
  Shield,
  Target
} from 'lucide-react';

interface VehicleAssessmentPageProps {
  className?: string;
}

interface AssessmentData {
  // Personal Info
  email: string;
  firstName: string;
  
  // Vehicle Details
  vehicleAge: string;
  vehicleMileage: string;
  maintenanceHistory: string;
  monthlyTransportationCosts: string;
  fuelEfficiency: string;
  vehicleValue: string;
  
  // Financial Health
  emergencyFund: string;
  vehicleInsurance: string;
  maintenanceBudget: string;
  replacementTimeline: string;
  
  // Goals & Preferences
  vehicleGoals: string[];
  commuteDistance: string;
  environmentalConcerns: string;
  technologyPreferences: string;
}

const VehicleAssessmentPage: React.FC<VehicleAssessmentPageProps> = ({ className = '' }) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [assessmentData, setAssessmentData] = useState<AssessmentData>({
    email: '',
    firstName: '',
    vehicleAge: '',
    vehicleMileage: '',
    maintenanceHistory: '',
    monthlyTransportationCosts: '',
    fuelEfficiency: '',
    vehicleValue: '',
    emergencyFund: '',
    vehicleInsurance: '',
    maintenanceBudget: '',
    replacementTimeline: '',
    vehicleGoals: [],
    commuteDistance: '',
    environmentalConcerns: '',
    technologyPreferences: ''
  });
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showResults, setShowResults] = useState(false);
  const [assessmentResult, setAssessmentResult] = useState<any>(null);

  const steps = [
    { id: 'personal', title: 'Personal Info', icon: <Car className="w-5 h-5" /> },
    { id: 'vehicle', title: 'Vehicle Details', icon: <Wrench className="w-5 h-5" /> },
    { id: 'financial', title: 'Financial Health', icon: <DollarSign className="w-5 h-5" /> },
    { id: 'goals', title: 'Goals & Preferences', icon: <Target className="w-5 h-5" /> },
    { id: 'results', title: 'Assessment Results', icon: <CheckCircle className="w-5 h-5" /> }
  ];

  const handleInputChange = (field: keyof AssessmentData, value: any) => {
    setAssessmentData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleArrayChange = (field: keyof AssessmentData, value: string, checked: boolean) => {
    setAssessmentData(prev => {
      const currentArray = (prev[field] as string[]) || [];
      if (checked) {
        return { ...prev, [field]: [...currentArray, value] };
      } else {
        return { ...prev, [field]: currentArray.filter(item => item !== value) };
      }
    });
  };

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(prev => prev + 1);
    }
  };

  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(prev => prev - 1);
    }
  };

  const handleSubmit = async () => {
    setLoading(true);
    setError(null);

    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Mock assessment results
      const mockResults = {
        overallScore: 78,
        riskLevel: 'moderate',
        recommendations: [
          {
            category: 'Maintenance',
            priority: 'high',
            title: 'Schedule Regular Maintenance',
            description: 'Your vehicle is approaching 100,000 miles. Consider scheduling a comprehensive inspection.',
            impact: 'Prevent major repairs and maintain resale value',
            cost: '$200-400'
          },
          {
            category: 'Financial Planning',
            priority: 'medium',
            title: 'Build Vehicle Replacement Fund',
            description: 'Start saving for your next vehicle. Based on your current vehicle age, consider a 3-5 year timeline.',
            impact: 'Avoid financing stress and get better deals',
            cost: '$200-500/month'
          },
          {
            category: 'Fuel Efficiency',
            priority: 'low',
            title: 'Consider Fuel-Efficient Options',
            description: 'Your current fuel efficiency could be improved. Consider hybrid or electric options for your next vehicle.',
            impact: 'Save $50-100/month on fuel costs',
            cost: 'Varies'
          }
        ],
        insights: {
          vehicleHealth: 75,
          financialReadiness: 82,
          environmentalImpact: 65,
          technologyAdoption: 70
        },
        nextSteps: [
          'Schedule a maintenance inspection within 30 days',
          'Start setting aside $300/month for vehicle replacement',
          'Research fuel-efficient vehicle options',
          'Review your insurance coverage for potential savings'
        ]
      };
      
      setAssessmentResult(mockResults);
      setShowResults(true);
      setCurrentStep(steps.length - 1);
    } catch (err) {
      setError('Assessment failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const renderPersonalInfoStep = () => (
    <div className="space-y-6">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Let's Get Started</h2>
        <p className="text-gray-600">Tell us a bit about yourself and your vehicle situation</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            First Name *
          </label>
          <input
            type="text"
            value={assessmentData.firstName}
            onChange={(e) => handleInputChange('firstName', e.target.value)}
            placeholder="Enter your first name"
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Email Address *
          </label>
          <input
            type="email"
            value={assessmentData.email}
            onChange={(e) => handleInputChange('email', e.target.value)}
            placeholder="your.email@example.com"
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            required
          />
        </div>
      </div>
    </div>
  );

  const renderVehicleDetailsStep = () => (
    <div className="space-y-6">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Vehicle Details</h2>
        <p className="text-gray-600">Help us understand your current vehicle situation</p>
      </div>

      <div className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">
            How old is your current vehicle? *
          </label>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {['Less than 2 years', '2-5 years', '6-10 years', '11-15 years', '16-20 years', 'Over 20 years'].map((option) => (
              <button
                key={option}
                onClick={() => handleInputChange('vehicleAge', option)}
                className={`p-3 text-left border rounded-lg transition-colors ${
                  assessmentData.vehicleAge === option
                    ? 'border-blue-500 bg-blue-50 text-blue-700'
                    : 'border-gray-300 hover:border-gray-400'
                }`}
              >
                {option}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">
            What is your vehicle's current mileage? *
          </label>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {['Under 50,000 miles', '50,000 - 75,000 miles', '75,000 - 100,000 miles', '100,000 - 150,000 miles', '150,000 - 200,000 miles', 'Over 200,000 miles'].map((option) => (
              <button
                key={option}
                onClick={() => handleInputChange('vehicleMileage', option)}
                className={`p-3 text-left border rounded-lg transition-colors ${
                  assessmentData.vehicleMileage === option
                    ? 'border-blue-500 bg-blue-50 text-blue-700'
                    : 'border-gray-300 hover:border-gray-400'
                }`}
              >
                {option}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">
            How would you describe your recent maintenance history? *
          </label>
          <div className="space-y-3">
            {[
              'Regular maintenance, no major issues',
              'Some minor repairs, mostly routine maintenance',
              'Several unexpected repairs in the past year',
              'Major repairs needed recently',
              'I don\'t keep track of maintenance'
            ].map((option) => (
              <button
                key={option}
                onClick={() => handleInputChange('maintenanceHistory', option)}
                className={`w-full p-3 text-left border rounded-lg transition-colors ${
                  assessmentData.maintenanceHistory === option
                    ? 'border-blue-500 bg-blue-50 text-blue-700'
                    : 'border-gray-300 hover:border-gray-400'
                }`}
              >
                {option}
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Monthly Transportation Costs *
            </label>
            <select
              value={assessmentData.monthlyTransportationCosts}
              onChange={(e) => handleInputChange('monthlyTransportationCosts', e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              required
            >
              <option value="">Select range</option>
              <option value="Under $200">Under $200</option>
              <option value="$200-400">$200-400</option>
              <option value="$400-600">$400-600</option>
              <option value="$600-800">$600-800</option>
              <option value="Over $800">Over $800</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Fuel Efficiency *
            </label>
            <select
              value={assessmentData.fuelEfficiency}
              onChange={(e) => handleInputChange('fuelEfficiency', e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              required
            >
              <option value="">Select range</option>
              <option value="Under 20 MPG">Under 20 MPG</option>
              <option value="20-25 MPG">20-25 MPG</option>
              <option value="25-30 MPG">25-30 MPG</option>
              <option value="30-35 MPG">30-35 MPG</option>
              <option value="Over 35 MPG">Over 35 MPG</option>
            </select>
          </div>
        </div>
      </div>
    </div>
  );

  const renderFinancialHealthStep = () => (
    <div className="space-y-6">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Financial Health</h2>
        <p className="text-gray-600">Help us understand your financial readiness for vehicle expenses</p>
      </div>

      <div className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">
            Do you have an emergency fund for vehicle repairs? *
          </label>
          <div className="space-y-3">
            {[
              'Yes, I have $2,000+ set aside',
              'Yes, I have $1,000-2,000 set aside',
              'Yes, I have $500-1,000 set aside',
              'Yes, but less than $500',
              'No, I don\'t have an emergency fund'
            ].map((option) => (
              <button
                key={option}
                onClick={() => handleInputChange('emergencyFund', option)}
                className={`w-full p-3 text-left border rounded-lg transition-colors ${
                  assessmentData.emergencyFund === option
                    ? 'border-blue-500 bg-blue-50 text-blue-700'
                    : 'border-gray-300 hover:border-gray-400'
                }`}
              >
                {option}
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Monthly Vehicle Insurance Cost *
            </label>
            <select
              value={assessmentData.vehicleInsurance}
              onChange={(e) => handleInputChange('vehicleInsurance', e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              required
            >
              <option value="">Select range</option>
              <option value="Under $100">Under $100</option>
              <option value="$100-150">$100-150</option>
              <option value="$150-200">$150-200</option>
              <option value="$200-250">$200-250</option>
              <option value="Over $250">Over $250</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Monthly Maintenance Budget *
            </label>
            <select
              value={assessmentData.maintenanceBudget}
              onChange={(e) => handleInputChange('maintenanceBudget', e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              required
            >
              <option value="">Select range</option>
              <option value="Under $50">Under $50</option>
              <option value="$50-100">$50-100</option>
              <option value="$100-150">$100-150</option>
              <option value="$150-200">$150-200</option>
              <option value="Over $200">Over $200</option>
            </select>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">
            When do you plan to replace your current vehicle? *
          </label>
          <div className="space-y-3">
            {[
              'Within the next year',
              '1-2 years',
              '2-3 years',
              '3-5 years',
              '5+ years',
              'I\'m not sure'
            ].map((option) => (
              <button
                key={option}
                onClick={() => handleInputChange('replacementTimeline', option)}
                className={`w-full p-3 text-left border rounded-lg transition-colors ${
                  assessmentData.replacementTimeline === option
                    ? 'border-blue-500 bg-blue-50 text-blue-700'
                    : 'border-gray-300 hover:border-gray-400'
                }`}
              >
                {option}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );

  const renderGoalsStep = () => (
    <div className="space-y-6">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Goals & Preferences</h2>
        <p className="text-gray-600">Tell us about your vehicle goals and preferences</p>
      </div>

      <div className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">
            What are your main vehicle goals? (Select all that apply)
          </label>
          <div className="space-y-3">
            {[
              'Reduce fuel costs',
              'Improve reliability',
              'Increase safety features',
              'Reduce environmental impact',
              'Upgrade technology features',
              'Lower maintenance costs',
              'Improve resale value',
              'Better performance'
            ].map((goal) => (
              <label key={goal} className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  checked={assessmentData.vehicleGoals.includes(goal)}
                  onChange={(e) => handleArrayChange('vehicleGoals', goal, e.target.checked)}
                  className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
                <span className="text-sm text-gray-700">{goal}</span>
              </label>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Daily Commute Distance *
          </label>
          <select
            value={assessmentData.commuteDistance}
            onChange={(e) => handleInputChange('commuteDistance', e.target.value)}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            required
          >
            <option value="">Select distance</option>
            <option value="Under 10 miles">Under 10 miles</option>
            <option value="10-20 miles">10-20 miles</option>
            <option value="20-30 miles">20-30 miles</option>
            <option value="30-50 miles">30-50 miles</option>
            <option value="Over 50 miles">Over 50 miles</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">
            How important are environmental concerns in your vehicle decisions? *
          </label>
          <div className="space-y-3">
            {[
              'Very important - I prioritize eco-friendly options',
              'Somewhat important - I consider environmental impact',
              'Moderately important - I balance cost and environment',
              'Not very important - Cost and convenience come first',
              'Not important at all - Environmental impact doesn\'t factor in'
            ].map((option) => (
              <button
                key={option}
                onClick={() => handleInputChange('environmentalConcerns', option)}
                className={`w-full p-3 text-left border rounded-lg transition-colors ${
                  assessmentData.environmentalConcerns === option
                    ? 'border-blue-500 bg-blue-50 text-blue-700'
                    : 'border-gray-300 hover:border-gray-400'
                }`}
              >
                {option}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );

  const renderResultsStep = () => (
    <div className="space-y-8">
      {assessmentResult && (
        <>
          {/* Overall Score */}
          <div className="text-center">
            <div className="inline-flex items-center justify-center w-24 h-24 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full mb-4">
              <span className="text-3xl font-bold text-white">{assessmentResult.overallScore}</span>
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Assessment Complete!</h2>
            <p className="text-gray-600">Your vehicle financial health score</p>
          </div>

          {/* Score Breakdown */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(assessmentResult.insights).map(([key, value]) => (
              <div key={key} className="bg-white p-4 rounded-lg border text-center">
                <div className="text-2xl font-bold text-blue-600 mb-1">{value}%</div>
                <div className="text-sm text-gray-600 capitalize">{key.replace(/([A-Z])/g, ' $1').trim()}</div>
              </div>
            ))}
          </div>

          {/* Recommendations */}
          <div className="space-y-4">
            <h3 className="text-xl font-semibold text-gray-900">Personalized Recommendations</h3>
            {assessmentResult.recommendations.map((rec: any, index: number) => (
              <div key={index} className="bg-white p-6 rounded-lg border-l-4 border-blue-500">
                <div className="flex items-start justify-between mb-2">
                  <h4 className="font-semibold text-gray-900">{rec.title}</h4>
                  <span className={`px-2 py-1 text-xs rounded-full ${
                    rec.priority === 'high' ? 'bg-red-100 text-red-800' :
                    rec.priority === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-green-100 text-green-800'
                  }`}>
                    {rec.priority} priority
                  </span>
                </div>
                <p className="text-gray-600 mb-2">{rec.description}</p>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Impact: {rec.impact}</span>
                  <span className="font-medium text-gray-900">Cost: {rec.cost}</span>
                </div>
              </div>
            ))}
          </div>

          {/* Next Steps */}
          <div className="bg-blue-50 p-6 rounded-lg">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Next Steps</h3>
            <ul className="space-y-2">
              {assessmentResult.nextSteps.map((step: string, index: number) => (
                <li key={index} className="flex items-center space-x-2">
                  <CheckCircle className="w-4 h-4 text-blue-600" />
                  <span className="text-gray-700">{step}</span>
                </li>
              ))}
            </ul>
          </div>
        </>
      )}
    </div>
  );

  const renderCurrentStep = () => {
    switch (currentStep) {
      case 0: return renderPersonalInfoStep();
      case 1: return renderVehicleDetailsStep();
      case 2: return renderFinancialHealthStep();
      case 3: return renderGoalsStep();
      case 4: return renderResultsStep();
      default: return null;
    }
  };

  const canProceed = () => {
    switch (currentStep) {
      case 0: return assessmentData.firstName && assessmentData.email;
      case 1: return assessmentData.vehicleAge && assessmentData.vehicleMileage && assessmentData.maintenanceHistory && assessmentData.monthlyTransportationCosts && assessmentData.fuelEfficiency;
      case 2: return assessmentData.emergencyFund && assessmentData.vehicleInsurance && assessmentData.maintenanceBudget && assessmentData.replacementTimeline;
      case 3: return assessmentData.commuteDistance && assessmentData.environmentalConcerns;
      default: return true;
    }
  };

  return (
    <div className={`min-h-screen bg-gray-50 py-8 ${className}`}>
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Vehicle Financial Health Assessment
          </h1>
          <p className="text-gray-600 max-w-2xl mx-auto">
            Get personalized insights about your vehicle's financial health and receive 
            recommendations to optimize your transportation costs and planning.
          </p>
        </div>

        {/* Progress Steps */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            {steps.map((step, index) => (
              <div key={step.id} className="flex items-center">
                <div className={`flex items-center justify-center w-10 h-10 rounded-full border-2 ${
                  currentStep >= index
                    ? 'border-blue-500 bg-blue-500 text-white'
                    : 'border-gray-300 bg-white text-gray-500'
                }`}>
                  {currentStep > index ? (
                    <CheckCircle className="w-5 h-5" />
                  ) : (
                    step.icon
                  )}
                </div>
                <span className={`ml-2 text-sm font-medium ${
                  currentStep >= index ? 'text-blue-600' : 'text-gray-500'
                }`}>
                  {step.title}
                </span>
                {index < steps.length - 1 && (
                  <div className={`w-16 h-0.5 ml-4 ${
                    currentStep > index ? 'bg-blue-500' : 'bg-gray-300'
                  }`} />
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Main Content */}
        <div className="bg-white rounded-lg shadow-lg p-8">
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center">
              <AlertCircle className="w-5 h-5 text-red-500 mr-2" />
              <p className="text-red-700">{error}</p>
            </div>
          )}

          {renderCurrentStep()}

          {/* Navigation */}
          {currentStep < steps.length - 1 && (
            <div className="flex justify-between mt-8">
              <button
                onClick={handlePrevious}
                disabled={currentStep === 0}
                className="flex items-center px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                Previous
              </button>

              {currentStep === steps.length - 2 ? (
                <button
                  onClick={handleSubmit}
                  disabled={!canProceed() || loading}
                  className="flex items-center px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {loading ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Processing...
                    </>
                  ) : (
                    <>
                      Complete Assessment
                      <CheckCircle className="w-4 h-4 ml-2" />
                    </>
                  )}
                </button>
              ) : (
                <button
                  onClick={handleNext}
                  disabled={!canProceed()}
                  className="flex items-center px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  Next
                  <ArrowRight className="w-4 h-4 ml-2" />
                </button>
              )}
            </div>
          )}

          {currentStep === steps.length - 1 && (
            <div className="flex justify-center mt-8">
              <button
                onClick={() => {
                  setCurrentStep(0);
                  setAssessmentData({
                    email: '',
                    firstName: '',
                    vehicleAge: '',
                    vehicleMileage: '',
                    maintenanceHistory: '',
                    monthlyTransportationCosts: '',
                    fuelEfficiency: '',
                    vehicleValue: '',
                    emergencyFund: '',
                    vehicleInsurance: '',
                    maintenanceBudget: '',
                    replacementTimeline: '',
                    vehicleGoals: [],
                    commuteDistance: '',
                    environmentalConcerns: '',
                    technologyPreferences: ''
                  });
                  setShowResults(false);
                  setAssessmentResult(null);
                }}
                className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Start New Assessment
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default VehicleAssessmentPage;
