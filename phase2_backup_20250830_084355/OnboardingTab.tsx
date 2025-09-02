import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import OnboardingProgressTracker from '../onboarding/OnboardingProgressTracker';

export function OnboardingTab() {
  const [currentStep, setCurrentStep] = useState<string>('welcome');
  const [stepStatus, setStepStatus] = useState<any>({});
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchStepStatus = async () => {
      try {
        const res = await fetch('/api/onboarding/progress/steps');
        const data = await res.json();
        if (data.success && data.step_status) {
          setStepStatus(data.step_status);
          // Determine current step
          const steps = Object.keys(data.step_status);
          const currentStepIndex = steps.findIndex(
            (step) => !data.step_status[step]?.completed
          );
          if (currentStepIndex >= 0) {
            setCurrentStep(steps[currentStepIndex]);
          }
        }
      } catch (err) {
        console.error('Failed to fetch step status:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchStepStatus();
  }, []);

  const getStepComponent = () => {
    switch (currentStep) {
      case 'welcome':
        return (
          <div className="text-center py-12">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Welcome to Mingus!</h2>
            <p className="text-gray-600 mb-6">Let's get started with your financial wellness journey.</p>
            <button
              onClick={() => navigate('/onboarding/welcome')}
              className="bg-gradient-to-r from-purple-600 to-pink-600 text-white px-6 py-3 rounded-lg hover:from-purple-700 hover:to-pink-700 transition-colors"
            >
              Start Onboarding
            </button>
          </div>
        );
      case 'choice':
        return (
          <div className="text-center py-12">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Choose Your Experience</h2>
            <p className="text-gray-600 mb-6">Select how detailed you'd like your setup to be.</p>
            <button
              onClick={() => navigate('/onboarding/choice')}
              className="bg-gradient-to-r from-purple-600 to-indigo-600 text-white px-6 py-3 rounded-lg hover:from-purple-700 hover:to-indigo-700 transition-colors"
            >
              Make Choice
            </button>
          </div>
        );
      case 'profile':
        return (
          <div className="text-center py-12">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Profile Setup</h2>
            <p className="text-gray-600 mb-6">Tell us about yourself to personalize your experience.</p>
            <button
              onClick={() => navigate('/onboarding/profile')}
              className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white px-6 py-3 rounded-lg hover:from-blue-700 hover:to-indigo-700 transition-colors"
            >
              Complete Profile
            </button>
          </div>
        );
      case 'preferences':
        return (
          <div className="text-center py-12">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Preferences</h2>
            <p className="text-gray-600 mb-6">Customize your experience and notifications.</p>
            <button
              onClick={() => navigate('/onboarding/preferences')}
              className="bg-gradient-to-r from-green-600 to-blue-600 text-white px-6 py-3 rounded-lg hover:from-green-700 hover:to-blue-700 transition-colors"
            >
              Set Preferences
            </button>
          </div>
        );
      case 'expenses':
        return (
          <div className="text-center py-12">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Monthly Expenses</h2>
            <p className="text-gray-600 mb-6">Track your spending to get better insights.</p>
            <button
              onClick={() => navigate('/onboarding/expenses')}
              className="bg-gradient-to-r from-orange-600 to-red-600 text-white px-6 py-3 rounded-lg hover:from-orange-700 hover:to-red-700 transition-colors"
            >
              Track Expenses
            </button>
          </div>
        );
      case 'goals':
        return (
          <div className="text-center py-12">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Financial Goals</h2>
            <p className="text-gray-600 mb-6">Set your financial goals and priorities.</p>
            <button
              onClick={() => navigate('/onboarding/goals')}
              className="bg-gradient-to-r from-green-600 to-teal-600 text-white px-6 py-3 rounded-lg hover:from-green-700 hover:to-teal-700 transition-colors"
            >
              Set Goals
            </button>
          </div>
        );
      case 'financial_questionnaire':
        return (
          <div className="text-center py-12">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Financial Assessment</h2>
            <p className="text-gray-600 mb-6">Complete a quick financial questionnaire.</p>
            <button
              onClick={() => navigate('/onboarding/financial-questionnaire')}
              className="bg-gradient-to-r from-purple-600 to-indigo-600 text-white px-6 py-3 rounded-lg hover:from-purple-700 hover:to-indigo-700 transition-colors"
            >
              Take Assessment
            </button>
          </div>
        );
      case 'lifestyle_questionnaire':
        return (
          <div className="text-center py-12">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Lifestyle Assessment</h2>
            <p className="text-gray-600 mb-6">Share your lifestyle preferences for personalized insights.</p>
            <button
              onClick={() => navigate('/onboarding/lifestyle-questionnaire')}
              className="bg-gradient-to-r from-pink-600 to-purple-600 text-white px-6 py-3 rounded-lg hover:from-pink-700 hover:to-purple-700 transition-colors"
            >
              Complete Assessment
            </button>
          </div>
        );
      case 'complete':
        return (
          <div className="text-center py-12">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">🎉 Onboarding Complete!</h2>
            <p className="text-gray-600 mb-6">You're all set to start your financial wellness journey.</p>
            <button
              onClick={() => navigate('/onboarding/complete')}
              className="bg-gradient-to-r from-green-600 to-blue-600 text-white px-6 py-3 rounded-lg hover:from-green-700 hover:to-blue-700 transition-colors"
            >
              View Summary
            </button>
          </div>
        );
      default:
        return (
          <div className="text-center py-12">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Welcome to Mingus!</h2>
            <p className="text-gray-600 mb-6">Let's get started with your financial wellness journey.</p>
            <button
              onClick={() => navigate('/onboarding/welcome')}
              className="bg-gradient-to-r from-purple-600 to-pink-600 text-white px-6 py-3 rounded-lg hover:from-purple-700 hover:to-pink-700 transition-colors"
            >
              Start Onboarding
            </button>
          </div>
        );
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading your onboarding progress...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">
          Welcome to Mingus! 🎉
        </h2>
        <p className="text-gray-600 mb-6">
          Let's get you set up with your personalized financial wellness journey. 
          Complete the steps below to unlock your full Mingus experience.
        </p>
        
        <OnboardingProgressTracker />
      </div>
      
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        {getStepComponent()}
      </div>
      
      <div className="bg-gradient-to-r from-purple-50 to-pink-50 rounded-xl border border-purple-200 p-6">
        <h3 className="text-lg font-semibold text-purple-900 mb-4">
          What's Next?
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-white p-4 rounded-lg border border-purple-100">
            <h4 className="font-semibold text-purple-800 mb-2">📊 Financial Profile</h4>
            <p className="text-base leading-relaxed text-gray-600">
              Set up your financial baseline and preferences
            </p>
          </div>
          <div className="bg-white p-4 rounded-lg border border-purple-100">
            <h4 className="font-semibold text-purple-800 mb-2">🎯 Goals & Dreams</h4>
            <p className="text-base leading-relaxed text-gray-600">
              Define your financial goals and priorities
            </p>
          </div>
          <div className="bg-white p-4 rounded-lg border border-purple-100">
            <h4 className="font-semibold text-purple-800 mb-2">📝 Quick Assessment</h4>
            <p className="text-base leading-relaxed text-gray-600">
              Complete our brief financial questionnaire
            </p>
          </div>
          <div className="bg-white p-4 rounded-lg border border-purple-100">
            <h4 className="font-semibold text-purple-800 mb-2">🌟 Lifestyle Insights</h4>
            <p className="text-base leading-relaxed text-gray-600">
              Share your lifestyle preferences for personalized advice
            </p>
          </div>
        </div>
      </div>
    </div>
  );
} 