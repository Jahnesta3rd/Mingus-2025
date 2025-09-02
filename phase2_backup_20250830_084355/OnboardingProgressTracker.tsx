import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

interface StepStatus {
  completed: boolean;
  completed_at?: string;
}

interface StepStatusMap {
  [stepName: string]: StepStatus;
}

const stepDisplayNames: { [key: string]: string } = {
  welcome: 'Welcome',
  choice: 'Setup Choice',
  profile: 'Profile',
  preferences: 'Preferences',
  expenses: 'Expenses',
  goals: 'Goals',
  financial_questionnaire: 'Financial Assessment',
  lifestyle_questionnaire: 'Lifestyle Assessment',
  complete: 'Complete',
};

const stepRoutes: { [key: string]: string } = {
  welcome: '/onboarding/welcome',
  choice: '/onboarding/choice',
  profile: '/onboarding/profile',
  preferences: '/onboarding/preferences',
  expenses: '/onboarding/expenses',
  goals: '/onboarding/goals',
  financial_questionnaire: '/onboarding/financial-questionnaire',
  lifestyle_questionnaire: '/onboarding/lifestyle-questionnaire',
  complete: '/onboarding/complete',
};

const OnboardingProgressTracker: React.FC = () => {
  const [stepStatus, setStepStatus] = useState<StepStatusMap>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchStepStatus = async () => {
      setLoading(true);
      try {
        const res = await fetch('/api/onboarding/progress/steps');
        const data = await res.json();
        if (data.success && data.step_status) {
          setStepStatus(data.step_status);
        } else {
          setError('Could not load onboarding progress.');
        }
      } catch (err) {
        setError('Failed to fetch onboarding progress.');
      } finally {
        setLoading(false);
      }
    };
    fetchStepStatus();
  }, []);

  const steps = Object.keys(stepDisplayNames);
  const currentStepIndex = steps.findIndex(
    (step) => !stepStatus[step]?.completed
  );
  const completedCount = steps.filter((step) => stepStatus[step]?.completed).length;
  const percent = Math.round((completedCount / steps.length) * 100);

  const handleStepClick = (stepName: string) => {
    const route = stepRoutes[stepName];
    if (route) {
      navigate(route);
    }
  };

  const isStepClickable = (stepName: string, index: number) => {
    // Allow clicking on current step or any completed step
    // For incomplete future steps, only allow clicking if it's the next logical step
    if (stepStatus[stepName]?.completed) return true;
    if (index === currentStepIndex) return true;
    if (index === currentStepIndex + 1) return true; // Allow clicking next step
    return false;
  };

  if (loading) return <div className="py-6 text-center">Loading progress...</div>;
  if (error) return <div className="py-6 text-center text-red-500">{error}</div>;

  return (
    <div className="w-full max-w-2xl mx-auto p-4 bg-white rounded-xl shadow border border-gray-200">
      <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
        <span className="text-2xl mr-2">🚦</span> Onboarding Progress
      </h3>
      <div className="flex items-center justify-between mb-4">
        <div className="w-full bg-gray-200 rounded-full h-3">
          <div
            className="bg-gradient-to-r from-purple-500 to-pink-400 h-3 rounded-full transition-all duration-500"
            style={{ width: `${percent}%` }}
          ></div>
        </div>
        <span className="ml-4 text-base leading-relaxed font-bold text-purple-700">{percent}%</span>
      </div>
      <ol className="flex flex-col md:flex-row md:space-x-6 space-y-4 md:space-y-0">
        {steps.map((step, idx) => {
          const isCompleted = stepStatus[step]?.completed;
          const isCurrent = idx === currentStepIndex;
          const isClickable = isStepClickable(step, idx);
          
          return (
            <li key={step} className="flex-1 flex flex-col items-center">
              <button
                onClick={() => handleStepClick(step)}
                disabled={!isClickable}
                className={`w-10 h-10 flex items-center justify-center rounded-full border-2 transition-all duration-300 ${
                  isCompleted 
                    ? 'bg-green-400 border-green-500 text-white hover:bg-green-500 cursor-pointer' 
                    : isCurrent 
                      ? 'bg-purple-500 border-purple-700 text-white animate-pulse cursor-pointer' 
                      : isClickable
                        ? 'bg-gray-200 border-gray-300 text-gray-500 hover:bg-gray-300 hover:border-gray-400 cursor-pointer'
                        : 'bg-gray-100 border-gray-200 text-gray-400 cursor-not-allowed'
                }`}
                title={isClickable ? `Go to ${stepDisplayNames[step]}` : 'Complete previous steps first'}
              >
                {isCompleted ? '✓' : idx + 1}
              </button>
              <span className={`mt-2 text-base leading-relaxed font-medium text-center ${
                isCompleted 
                  ? 'text-green-700' 
                  : isCurrent 
                    ? 'text-purple-700' 
                    : isClickable
                      ? 'text-gray-500 hover:text-gray-700'
                      : 'text-gray-400'
              }`}>
                {stepDisplayNames[step]}
              </span>
            </li>
          );
        })}
      </ol>
    </div>
  );
};

export default OnboardingProgressTracker; 