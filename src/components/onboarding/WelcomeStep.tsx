import React, { useState, useEffect } from 'react';
import { OnboardingProgressBar } from './OnboardingProgressBar';
import { UniversalContinueButton } from './UniversalContinueButton';

const WelcomeStep: React.FC = () => {
  const [hasViewedWelcome, setHasViewedWelcome] = useState(false);
  const [startTime] = useState(Date.now());
  
  // TODO: Get userId from auth context
  const userId = "user_123"; // This should come from your auth system

  useEffect(() => {
    // Mark as viewed after 3 seconds
    const timer = setTimeout(() => {
      setHasViewedWelcome(true);
    }, 3000);

    return () => clearTimeout(timer);
  }, []);

  const getCompletionData = () => {
    return {
      viewed_welcome_screen: hasViewedWelcome,
      clicked_get_started: true,
      time_spent: Math.round((Date.now() - startTime) / 60000) // minutes
    };
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <OnboardingProgressBar userId={userId} currentStep="welcome" />
      
      <div className="container mx-auto px-4 py-12">
        <div className="max-w-2xl mx-auto text-center">
          <div className="mb-8">
            <h1 className="text-4xl font-bold text-gray-900 mb-4">
              Welcome to Mingus! 👋
            </h1>
            <p className="text-xl text-gray-600 mb-6">
              Finally, a finance app that gets your real life
            </p>
          </div>

          <div className="bg-white rounded-lg shadow-lg p-8 mb-8">
            <h2 className="text-2xl font-semibold mb-6">What makes Mingus different?</h2>
            
            <div className="grid md:grid-cols-3 gap-6 mb-8">
              <div className="text-center">
                <div className="text-3xl mb-2">🏃‍♀️</div>
                <h3 className="font-medium mb-2">Health Connection</h3>
                <p className="text-sm text-gray-600">
                  See how stress and wellness impact your spending
                </p>
              </div>
              
              <div className="text-center">
                <div className="text-3xl mb-2">📊</div>
                <h3 className="font-medium mb-2">Job Security</h3>
                <p className="text-sm text-gray-600">
                  Early warning system for employment risks
                </p>
              </div>
              
              <div className="text-center">
                <div className="text-3xl mb-2">🎯</div>
                <h3 className="font-medium mb-2">Life Planning</h3>
                <p className="text-sm text-gray-600">
                  Plan for what matters: birthdays, trips, goals
                </p>
              </div>
            </div>

            <div className="bg-blue-50 rounded-lg p-4 mb-6">
              <p className="text-sm text-blue-800">
                ⏱️ This setup takes about 25 minutes. You can save your progress and return anytime.
              </p>
            </div>
          </div>

          <div className="flex justify-center">
            <UniversalContinueButton
              userId={userId}
              currentStep="welcome"
              completionData={getCompletionData()}
              isValid={hasViewedWelcome}
              className="text-lg px-8 py-4"
            >
              Get Started →
            </UniversalContinueButton>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WelcomeStep; 