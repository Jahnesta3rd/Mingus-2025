import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import GoalTypeCard from './GoalTypeCard';
import FeasibilityChecker from './FeasibilityChecker';
import SmartSuggestions from './SmartSuggestions';
import ProgressTimeline from './ProgressTimeline';
import { useGoalsSetup } from '../../hooks/useGoalsSetup';
import { Goal, GoalType } from '../../types/goals';

const GoalsSetup: React.FC = () => {
  const navigate = useNavigate();
  const {
    selectedGoals,
    currentGoalIndex,
    goals,
    userFinances,
    isLoading,
    error,
    toggleGoalSelection,
    addGoal,
    updateGoal,
    removeGoal,
    saveGoals,
    loadUserFinances
  } = useGoalsSetup();

  const [currentGoal, setCurrentGoal] = useState<Partial<Goal>>({
    type: 'emergency_fund',
    name: '',
    targetAmount: 0,
    currentAmount: 0,
    targetDate: new Date(),
    priority: 3,
    monthlyContribution: 0,
    motivationNote: ''
  });

  const [timeline, setTimeline] = useState<string>('1year');
  const [motivation, setMotivation] = useState<string>('');

  useEffect(() => {
    loadUserFinances();
  }, [loadUserFinances]);

  useEffect(() => {
    if (selectedGoals.length > 0 && currentGoalIndex < selectedGoals.length) {
      const goalType = selectedGoals[currentGoalIndex];
      setCurrentGoal(prev => ({
        ...prev,
        type: goalType,
        name: getGoalTypeName(goalType)
      }));
    }
  }, [selectedGoals, currentGoalIndex]);

  const getGoalTypeName = (type: GoalType): string => {
    const goalNames: Record<GoalType, string> = {
      emergency_fund: 'Emergency Fund',
      debt_payoff: 'Debt Payoff',
      home_purchase: 'Home Purchase',
      vacation_fund: 'Vacation Fund',
      wedding_fund: 'Wedding Fund',
      car_purchase: 'Car Purchase',
      retirement_savings: 'Retirement Savings',
      investment_portfolio: 'Investment Portfolio',
      side_business: 'Side Business',
      education_fund: 'Education Fund',
      child_fund: 'Child Fund',
      important_dates: 'Important Dates'
    };
    return goalNames[type];
  };

  const handleAmountChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const amount = parseFloat(e.target.value) || 0;
    setCurrentGoal(prev => ({
      ...prev,
      targetAmount: amount
    }));
  };

  const handleTimelineChange = (newTimeline: string) => {
    setTimeline(newTimeline);
    const targetDate = calculateTargetDate(newTimeline);
    setCurrentGoal(prev => ({
      ...prev,
      targetDate
    }));
  };

  const calculateTargetDate = (timeline: string): Date => {
    const now = new Date();
    switch (timeline) {
      case '6months':
        return new Date(now.setMonth(now.getMonth() + 6));
      case '1year':
        return new Date(now.setFullYear(now.getFullYear() + 1));
      case '2years':
        return new Date(now.setFullYear(now.getFullYear() + 2));
      case '5years':
        return new Date(now.setFullYear(now.getFullYear() + 5));
      default:
        return now;
    }
  };

  const calculateMonthlyContribution = useCallback(() => {
    if (!currentGoal.targetAmount || !currentGoal.targetDate) return 0;
    
    const monthsRemaining = Math.max(1, 
      (new Date(currentGoal.targetDate).getTime() - new Date().getTime()) / 
      (1000 * 60 * 60 * 24 * 30.44)
    );
    
    return Math.ceil((currentGoal.targetAmount - (currentGoal.currentAmount || 0)) / monthsRemaining);
  }, [currentGoal.targetAmount, currentGoal.targetDate, currentGoal.currentAmount]);

  const handleSaveGoal = () => {
    if (!currentGoal.type || !currentGoal.targetAmount) return;

    const goal: Goal = {
      id: `goal_${Date.now()}`,
      type: currentGoal.type as GoalType,
      name: currentGoal.name || getGoalTypeName(currentGoal.type as GoalType),
      targetAmount: currentGoal.targetAmount,
      currentAmount: currentGoal.currentAmount || 0,
      targetDate: currentGoal.targetDate,
      priority: currentGoal.priority || 3,
      monthlyContribution: calculateMonthlyContribution(),
      motivationNote: motivation
    };

    addGoal(goal);
    
    // Move to next goal or complete
    if (currentGoalIndex < selectedGoals.length - 1) {
      setCurrentGoalIndex(currentGoalIndex + 1);
      setMotivation('');
    } else {
      handleComplete();
    }
  };

  const handleComplete = async () => {
    try {
      await saveGoals();
      navigate('/onboarding/step5'); // Move to next onboarding step
    } catch (err) {
      console.error('Failed to save goals:', err);
    }
  };

  const handleSkip = () => {
    navigate('/onboarding/step5');
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading your financial profile...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-500 text-6xl mb-4">⚠️</div>
          <h2 className="text-xl font-semibold text-gray-800 mb-2" className="text-2xl font-semibold text-gray-800 mb-4">Something went wrong</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <button 
            onClick={() => window.location.reload()}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Progress Bar */}
      <div className="bg-white shadow-sm">
        <div className="max-w-4xl mx-auto px-4 py-3">
          <div className="flex items-center justify-between mb-2">
            <span className="text-base leading-relaxed font-medium text-blue-600">Step 4 of 8</span>
            <span className="text-base leading-relaxed text-gray-500">Goals Setting</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div className="bg-gradient-to-r from-blue-500 to-indigo-600 h-2 rounded-full" style={{ width: '50%' }}></div>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Welcome/Intro Section */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4" className="text-4xl font-bold text-gray-900 mb-6">
            Let's Set Your Financial Goals 🎯
          </h1>
          <p className="text-xl text-gray-600 mb-6 max-w-2xl mx-auto">
            Your goals drive everything else. Let's map out what you're working toward.
          </p>
          <div className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white p-6 rounded-2xl shadow-lg">
            <p className="text-lg font-medium">
              "A goal without a plan is just a wish. Let's make yours reality." 💪
            </p>
          </div>
        </div>

        {/* Goal Type Selector */}
        <div className="mb-12">
          <h2 className="text-2xl font-semibold text-gray-900 mb-6 text-center" className="text-2xl font-semibold text-gray-800 mb-4">
            Choose Your Financial Goals
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {goalTypes.map(type => (
              <GoalTypeCard
                key={type.id}
                icon={type.icon}
                name={type.name}
                description={type.description}
                examples={type.examples}
                selected={selectedGoals.includes(type.id)}
                onClick={() => toggleGoalSelection(type.id)}
              />
            ))}
          </div>
        </div>

        {/* Goal Details Form */}
        {selectedGoals.length > 0 && (
          <div className="bg-white rounded-2xl shadow-xl p-8 mb-8">
            <div className="text-center mb-8">
              <h2 className="text-2xl font-semibold text-gray-900 mb-2" className="text-2xl font-semibold text-gray-800 mb-4">
                {currentGoal.name} Details
              </h2>
              <p className="text-gray-600">
                Goal {currentGoalIndex + 1} of {selectedGoals.length}
              </p>
            </div>

            {/* Amount Input Section */}
            <div className="mb-8">
              <label className="block text-lg font-medium text-gray-900 mb-4">
                How much do you need?
              </label>
              <div className="relative max-w-md mx-auto">
                <span className="absolute left-4 top-1/2 transform -translate-y-1/2 text-2xl font-bold text-gray-500">
                  $
                </span>
                <input
                  type="number"
                  value={currentGoal.targetAmount || ''}
                  onChange={handleAmountChange}
                  placeholder="0"
                  className="w-full pl-12 pr-4 py-4 text-2xl font-bold text-gray-900 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all"
                />
              </div>
              
              {/* Smart Suggestions */}
              {userFinances && (
                <SmartSuggestions
                  userIncome={userFinances.monthlyIncome}
                  userExpenses={userFinances.monthlyExpenses}
                  goalType={currentGoal.type as GoalType}
                  onApplyAmount={(amount) => setCurrentGoal(prev => ({ ...prev, targetAmount: amount }))}
                />
              )}
            </div>

            {/* Timeline Section */}
            <div className="mb-8">
              <label className="block text-lg font-medium text-gray-900 mb-4">
                When do you want to achieve this?
              </label>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {[
                  { value: '6months', label: '6 months' },
                  { value: '1year', label: '1 year' },
                  { value: '2years', label: '2 years' },
                  { value: '5years', label: '5+ years' }
                ].map(option => (
                  <button
                    key={option.value}
                    onClick={() => handleTimelineChange(option.value)}
                    className={`py-3 px-4 rounded-xl border-2 transition-all ${
                      timeline === option.value
                        ? 'border-blue-500 bg-blue-50 text-blue-700'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    {option.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Contribution Analysis */}
            <div className="mb-8">
              <div className="bg-gradient-to-r from-green-50 to-blue-50 p-6 rounded-xl border border-green-200">
                <h3 className="text-lg font-semibold text-gray-900 mb-2" className="text-xl font-semibold text-gray-800 mb-3">
                  Monthly Contribution Needed
                </h3>
                <div className="text-3xl font-bold text-green-600 mb-2">
                  ${calculateMonthlyContribution().toLocaleString()}
                </div>
                <div className="text-base leading-relaxed text-gray-600">
                  {calculateMonthlyContribution() <= (userFinances?.monthlyIncome || 0) * 0.3
                    ? "✅ Achievable with your current income"
                    : "⚠️ This is a stretch goal - consider adjusting timeline or amount"}
                </div>
              </div>
            </div>

            {/* Feasibility Checker */}
            {userFinances && (
              <div className="mb-8">
                <FeasibilityChecker
                  goal={currentGoal as Goal}
                  userFinances={userFinances}
                  onApplyAdjustment={(adjustment) => {
                    if (adjustment.type === 'amount') {
                      setCurrentGoal(prev => ({ ...prev, targetAmount: adjustment.value as number }));
                    } else if (adjustment.type === 'timeline') {
                      handleTimelineChange(adjustment.value as string);
                    }
                  }}
                />
              </div>
            )}

            {/* Motivation Section */}
            <div className="mb-8">
              <label className="block text-lg font-medium text-gray-900 mb-4">
                What's driving this goal? (Optional but powerful)
              </label>
              <textarea
                placeholder="e.g., 'Want to buy a house in my childhood neighborhood' or 'Building security for my family'"
                value={motivation}
                onChange={(e) => setMotivation(e.target.value)}
                className="w-full p-4 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all resize-none"
                rows={3}
              />
            </div>

            {/* Progress Visualization */}
            <div className="mb-8">
              <ProgressTimeline
                goal={currentGoal as Goal}
                monthlyContribution={calculateMonthlyContribution()}
              />
            </div>

            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <button
                onClick={handleSaveGoal}
                disabled={!currentGoal.targetAmount}
                className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white px-8 py-3 rounded-xl font-semibold hover:from-blue-700 hover:to-indigo-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {currentGoalIndex < selectedGoals.length - 1 ? 'Save & Continue' : 'Complete Goals'}
              </button>
              <button
                onClick={handleSkip}
                className="bg-gray-100 text-gray-700 px-8 py-3 rounded-xl font-semibold hover:bg-gray-200 transition-all"
              >
                Skip for Now
              </button>
            </div>
          </div>
        )}

        {/* Navigation */}
        <div className="flex justify-between items-center">
          <button
            onClick={() => navigate('/onboarding/step3')}
            className="flex items-center text-gray-600 hover:text-gray-800 transition-colors"
          >
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back to Financial Profile
          </button>
          
          {selectedGoals.length > 0 && (
            <div className="text-base leading-relaxed text-gray-500">
              {goals.length} goal{goals.length !== 1 ? 's' : ''} saved
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Goal types data
const goalTypes = [
  {
    id: 'emergency_fund',
    icon: '🛡️',
    name: 'Emergency Fund',
    description: 'Protect your peace of mind',
    examples: ['3-6 months of expenses', 'Medical emergencies', 'Job loss protection']
  },
  {
    id: 'home_purchase',
    icon: '🏠',
    name: 'Home Ownership',
    description: 'Build generational wealth',
    examples: ['Down payment', 'Closing costs', 'Home improvements']
  },
  {
    id: 'wedding_fund',
    icon: '💒',
    name: 'Wedding Fund',
    description: 'Celebrate your love properly',
    examples: ['Venue and catering', 'Photography', 'Honeymoon']
  },
  {
    id: 'vacation_fund',
    icon: '✈️',
    name: 'Travel Fund',
    description: 'See the world, embrace experiences',
    examples: ['International trips', 'Weekend getaways', 'Bucket list destinations']
  },
  {
    id: 'car_purchase',
    icon: '🚗',
    name: 'Reliable Transportation',
    description: 'Independence and mobility',
    examples: ['New car down payment', 'Used car purchase', 'Car maintenance fund']
  },
  {
    id: 'education_fund',
    icon: '📚',
    name: 'Education Investment',
    description: 'Keep learning, keep growing',
    examples: ['Graduate school', 'Certifications', 'Skill development']
  },
  {
    id: 'child_fund',
    icon: '👶',
    name: 'Family Planning',
    description: 'Secure the next generation',
    examples: ['Childcare costs', 'Education savings', 'Family expenses']
  },
  {
    id: 'side_business',
    icon: '💼',
    name: 'Side Business',
    description: 'Build multiple income streams',
    examples: ['Startup capital', 'Equipment costs', 'Marketing budget']
  },
  {
    id: 'debt_payoff',
    icon: '💳',
    name: 'Debt Payoff',
    description: 'Break free from debt',
    examples: ['Credit cards', 'Student loans', 'Personal loans']
  },
  {
    id: 'retirement_savings',
    icon: '🌅',
    name: 'Retirement Savings',
    description: 'Secure your future',
    examples: ['401(k) contributions', 'IRA investments', 'Retirement lifestyle']
  },
  {
    id: 'investment_portfolio',
    icon: '📈',
    name: 'Investment Portfolio',
    description: 'Grow your wealth',
    examples: ['Stock investments', 'Real estate', 'Diversified portfolio']
  },
  {
    id: 'important_dates',
    icon: '📅',
    name: 'Important Dates',
    description: 'Plan for life events',
    examples: ['Anniversaries', 'Birthdays', 'Special occasions']
  }
];

export default GoalsSetup; 