// pages/test-onboarding.tsx
import React from 'react';
import { OnboardingFlow } from '../components/onboarding/OnboardingFlow';
import { useUserStore } from '../store/userStore';
import { UserProfile } from '../types/user';

export default function TestOnboardingPage() {
  const { updateUser, clearError } = useUserStore();

  const handleComplete = async (userData: Partial<UserProfile>) => {
    console.log('Onboarding completed with data:', userData);
    
    // Update store with completed data
    updateUser({
      ...userData,
      profileCompletionPercentage: 100,
      onboardingStep: 10
    });

    // Show success message
    alert('Onboarding completed successfully! Check console for data.');
  };

  const handleStepChange = async (step: number, data: Partial<UserProfile>) => {
    console.log(`Step ${step} completed with data:`, data);
  };

  const handleSave = async (data: Partial<UserProfile>) => {
    console.log('Saving progress:', data);
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000));
    console.log('Progress saved successfully!');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-6 py-4">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Test Onboarding Flow</h1>
              <p className="text-gray-600">Testing the complete onboarding implementation</p>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="text-blue-600 font-bold text-xl">MINGUS</div>
            </div>
          </div>
        </div>
      </div>

      {/* Test Controls */}
      <div className="max-w-4xl mx-auto px-6 py-4">
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <h3 className="text-lg font-semibold text-blue-900 mb-2">Test Controls</h3>
          <div className="flex space-x-4">
            <button
              onClick={() => clearError()}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              Clear Errors
            </button>
            <button
              onClick={() => console.log('Current store state:', useUserStore.getState())}
              className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
            >
              Log Store State
            </button>
          </div>
        </div>
      </div>

      {/* Main onboarding flow */}
      <OnboardingFlow
        onComplete={handleComplete}
        onStepChange={handleStepChange}
        onSave={handleSave}
        initialData={{}}
        autoSave={true}
        showAnalytics={true}
        allowSkip={true}
      />

      {/* Footer */}
      <div className="bg-white border-t border-gray-200 mt-12">
        <div className="max-w-4xl mx-auto px-6 py-8">
          <div className="text-center">
            <p className="text-sm text-gray-500 mb-4">
              This is a test page for the onboarding implementation. Check the browser console for detailed logs.
            </p>
            <div className="flex justify-center space-x-6 text-xs text-gray-400">
              <span>Test Mode</span>
              <span>Development Environment</span>
              <span>Console Logging Enabled</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 