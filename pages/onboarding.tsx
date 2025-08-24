// pages/onboarding.tsx
import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import { OnboardingFlow } from '../components/onboarding/OnboardingFlow';
import { useUserStore, useUser, useUserLoading, useUserError } from '../store/userStore';
import { UserProfile } from '../types/user';

interface OnboardingPageProps {
  // Next.js page props
}

export default function OnboardingPage({}: OnboardingPageProps) {
  const router = useRouter();
  const [isInitialized, setIsInitialized] = useState(false);
  const [redirecting, setRedirecting] = useState(false);

  // Use store selectors
  const user = useUser();
  const isLoading = useUserLoading();
  const error = useUserError();

  // Get store actions
  const {
    loadProfile,
    createProfile,
    loadOnboardingProgress,
    clearOnboardingProgress,
    clearError
  } = useUserStore();

  // Initialize the page
  useEffect(() => {
    const initializeOnboarding = async () => {
      try {
        // Check if user already has a profile
        const profileResult = await loadProfile();
        
        if (profileResult.success && user.profileCompletionPercentage === 100) {
          // User has completed onboarding, redirect to dashboard
          setRedirecting(true);
          router.push('/dashboard');
          return;
        }

        // Load onboarding progress
        await loadOnboardingProgress();
        
        setIsInitialized(true);
      } catch (error) {
        console.error('Failed to initialize onboarding:', error);
        setIsInitialized(true); // Still show the page even if there's an error
      }
    };

    initializeOnboarding();
  }, []);

  const handleComplete = async (userData: Partial<UserProfile>) => {
    try {
      // Update user data in store
      useUserStore.getState().updateUser(userData);
      
      // Save final profile
      const saveResult = await useUserStore.getState().saveProfile();
      
      if (saveResult.success) {
        // Clear onboarding progress
        clearOnboardingProgress();
        
        // Show success message
        showSuccessMessage('Profile completed successfully!');
        
        // Redirect to dashboard after a short delay
        setTimeout(() => {
          setRedirecting(true);
          router.push('/dashboard');
        }, 1500);
      } else {
        throw new Error(saveResult.error || 'Failed to save profile');
      }
    } catch (error) {
      console.error('Failed to complete onboarding:', error);
      showErrorMessage('Failed to complete onboarding. Please try again.');
    }
  };

  const handleStepChange = async (step: number, data: Partial<UserProfile>) => {
    try {
      // Update user data in store
      useUserStore.getState().updateUser(data);
      
      // Update onboarding progress
      const completedSteps = Array.from({ length: step - 1 }, (_, i) => i + 1);
      useUserStore.getState().updateOnboardingProgress(step, completedSteps, data);
      
      // Save progress
      await useUserStore.getState().saveOnboardingProgress();
    } catch (error) {
      console.error('Failed to update step:', error);
      showErrorMessage('Failed to save progress. Please try again.');
    }
  };

  const handleSave = async (data: Partial<UserProfile>) => {
    try {
      // Update user data in store
      useUserStore.getState().updateUser(data);
      
      // Save to API
      const result = await useUserStore.getState().saveProfile();
      
      if (result.success) {
        showSuccessMessage('Progress saved successfully!');
      } else {
        throw new Error(result.error || 'Failed to save progress');
      }
    } catch (error) {
      console.error('Failed to save progress:', error);
      showErrorMessage('Failed to save progress. Please try again.');
    }
  };

  const showSuccessMessage = (message: string) => {
    // You can implement a toast notification system here
    console.log('Success:', message);
  };

  const showErrorMessage = (message: string) => {
    // You can implement a toast notification system here
    console.error('Error:', message);
  };

  // Show loading state while initializing
  if (!isInitialized || isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Setting up your profile</h2>
          <p className="text-gray-600">Please wait while we load your information...</p>
        </div>
      </div>
    );
  }

  // Show redirecting state
  if (redirecting) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600 mx-auto mb-4"></div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Profile completed!</h2>
          <p className="text-gray-600">Redirecting to your dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-6 py-4">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Welcome to MINGUS</h1>
              <p className="text-gray-600">Let's set up your personalized financial profile</p>
            </div>
            
            <div className="flex items-center space-x-4">
              {/* Logo or branding */}
              <div className="text-blue-600 font-bold text-xl">MINGUS</div>
            </div>
          </div>
        </div>
      </div>

      {/* Error display */}
      {error && (
        <div className="max-w-4xl mx-auto px-6 py-4">
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <svg className="h-5 w-5 text-red-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
                <span className="text-red-800">{error}</span>
              </div>
              <button
                onClick={clearError}
                className="text-red-400 hover:text-red-600"
              >
                <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Main onboarding flow */}
      <OnboardingFlow
        onComplete={handleComplete}
        onStepChange={handleStepChange}
        onSave={handleSave}
        initialData={user}
        autoSave={true}
        showAnalytics={true}
        allowSkip={true}
      />

      {/* Footer */}
      <div className="bg-white border-t border-gray-200 mt-12">
        <div className="max-w-4xl mx-auto px-6 py-8">
          <div className="text-center">
            <p className="text-sm text-gray-500 mb-4">
              Your data is secure and protected. We use industry-standard encryption to keep your information safe.
            </p>
            <div className="flex justify-center space-x-6 text-xs text-gray-400">
              <a href="/privacy" className="hover:text-gray-600">Privacy Policy</a>
              <a href="/terms" className="hover:text-gray-600">Terms of Service</a>
              <a href="/support" className="hover:text-gray-600">Support</a>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// Add page metadata for SEO
export const metadata = {
  title: 'Onboarding - MINGUS Financial Profile Setup',
  description: 'Complete your MINGUS financial profile to get personalized insights and recommendations.',
  keywords: 'financial profile, onboarding, personal finance, MINGUS',
  robots: 'noindex, nofollow' // Prevent indexing of onboarding pages
}; 