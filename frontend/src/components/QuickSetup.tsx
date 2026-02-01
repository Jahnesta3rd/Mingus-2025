import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { DollarSign, MapPin, Target, ArrowRight, Award } from 'lucide-react';

interface QuickSetupData {
  incomeRange: string;
  location: string;
  primaryGoal: string;
}

const QuickSetup: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [formData, setFormData] = useState<QuickSetupData>({
    incomeRange: '',
    location: '',
    primaryGoal: ''
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fromAssessment, setFromAssessment] = useState(false);
  const [assessmentType, setAssessmentType] = useState<string | null>(null);

  // Check if user came from assessment
  useEffect(() => {
    const from = searchParams.get('from');
    const type = searchParams.get('type');
    
    if (from === 'assessment') {
      setFromAssessment(true);
      if (type) {
        setAssessmentType(type);
      } else {
        // Try to get from localStorage
        const savedData = localStorage.getItem('mingus_assessment');
        if (savedData) {
          try {
            const { assessmentType: savedType } = JSON.parse(savedData);
            setAssessmentType(savedType);
          } catch (e) {
            // Ignore parse errors
          }
        }
      }
    }
  }, [searchParams]);

  // Helper function to format assessment type
  const formatAssessmentType = (type: string): string => {
    const names: Record<string, string> = {
      'ai-risk': 'AI Replacement Risk',
      'income-comparison': 'Income Comparison',
      'cuffing-season': 'Cuffing Season Score',
      'layoff-risk': 'Layoff Risk'
    };
    return names[type] || 'Assessment';
  };

  const incomeRanges = [
    { value: '30-50k', label: '$30,000 - $50,000' },
    { value: '50-75k', label: '$50,000 - $75,000' },
    { value: '75-100k', label: '$75,000 - $100,000' },
    { value: '100k+', label: '$100,000+' }
  ];

  const financialGoals = [
    { value: 'emergency-fund', label: 'Build Emergency Fund' },
    { value: 'debt-payoff', label: 'Pay Off Debt' },
    { value: 'investing', label: 'Start Investing' },
    { value: 'home-purchase', label: 'Save for Home' },
    { value: 'retirement', label: 'Plan for Retirement' }
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    
    try {
      const response = await fetch('/api/profile/quick-setup', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify(formData)
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || 'Failed to save profile setup');
      }
      
      // Clear assessment data from localStorage after successful setup
      localStorage.removeItem('mingus_assessment');
      
      navigate('/dashboard');
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Setup error occurred';
      setError(errorMessage);
      console.error('Setup error:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const isValid = formData.incomeRange && formData.location && formData.primaryGoal;

  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center px-4">
      <div className="max-w-md w-full">
        <div className="text-center mb-8">
          {fromAssessment && assessmentType && (
            <div className="mb-4 inline-flex items-center gap-2 bg-violet-600/20 border border-violet-500/30 rounded-full px-4 py-2">
              <Award className="h-4 w-4 text-violet-400" />
              <span className="text-sm text-violet-300">
                {formatAssessmentType(assessmentType)} Assessment Completed
              </span>
            </div>
          )}
          <h1 className="text-3xl font-bold text-white mb-2">
            {fromAssessment 
              ? "Let's personalize your experience based on your assessment"
              : "Let's personalize your experience"
            }
          </h1>
          <p className="text-gray-400">
            Just 3 quick questions to get you started
          </p>
        </div>
        
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Income Range */}
          <div>
            <label className="flex items-center gap-2 text-white font-medium mb-3">
              <DollarSign className="h-5 w-5 text-violet-400" />
              What's your annual income range?
            </label>
            <div className="grid grid-cols-2 gap-3">
              {incomeRanges.map(range => (
                <button
                  key={range.value}
                  type="button"
                  onClick={() => setFormData(prev => ({ ...prev, incomeRange: range.value }))}
                  className={`p-3 rounded-lg border text-sm transition-all ${
                    formData.incomeRange === range.value
                      ? 'bg-violet-600 border-violet-500 text-white'
                      : 'bg-gray-800 border-gray-700 text-gray-300 hover:border-violet-500'
                  }`}
                >
                  {range.label}
                </button>
              ))}
            </div>
          </div>
          
          {/* Location */}
          <div>
            <label className="flex items-center gap-2 text-white font-medium mb-3">
              <MapPin className="h-5 w-5 text-violet-400" />
              Where are you located?
            </label>
            <input
              type="text"
              placeholder="City, State or ZIP code"
              value={formData.location}
              onChange={(e) => setFormData(prev => ({ ...prev, location: e.target.value }))}
              className="w-full p-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:border-violet-500 focus:outline-none"
            />
          </div>
          
          {/* Primary Goal */}
          <div>
            <label className="flex items-center gap-2 text-white font-medium mb-3">
              <Target className="h-5 w-5 text-violet-400" />
              What's your top financial priority?
            </label>
            <div className="space-y-2">
              {financialGoals.map(goal => (
                <button
                  key={goal.value}
                  type="button"
                  onClick={() => setFormData(prev => ({ ...prev, primaryGoal: goal.value }))}
                  className={`w-full p-3 rounded-lg border text-left transition-all ${
                    formData.primaryGoal === goal.value
                      ? 'bg-violet-600 border-violet-500 text-white'
                      : 'bg-gray-800 border-gray-700 text-gray-300 hover:border-violet-500'
                  }`}
                >
                  {goal.label}
                </button>
              ))}
            </div>
          </div>
          
          {error && (
            <div className="rounded-md bg-red-900/50 border border-red-700 p-3">
              <p className="text-sm text-red-200">{error}</p>
            </div>
          )}
          
          {/* Submit */}
          <button
            type="submit"
            disabled={!isValid || isSubmitting}
            className={`w-full py-4 rounded-lg font-semibold flex items-center justify-center gap-2 transition-all ${
              isValid && !isSubmitting
                ? 'bg-gradient-to-r from-violet-600 to-purple-600 text-white hover:from-violet-700 hover:to-purple-700'
                : 'bg-gray-700 text-gray-400 cursor-not-allowed'
            }`}
          >
            {isSubmitting ? 'Setting up...' : (
              <>
                Go to Dashboard
                <ArrowRight className="h-5 w-5" />
              </>
            )}
          </button>
          
          {/* Skip Option */}
          <button
            type="button"
            onClick={() => navigate('/dashboard')}
            className="w-full py-2 text-gray-400 hover:text-white transition-colors text-sm"
          >
            Skip for now
          </button>
        </form>
      </div>
    </div>
  );
};

export default QuickSetup;
