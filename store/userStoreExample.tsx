// store/userStoreExample.tsx
import React, { useEffect } from 'react';
import { useUserStore, useUser, useUserLoading, useUserSaving, useUserError, useHasUnsavedChanges, useOnboardingProgress, useUserAnalytics } from './userStore';
import { OnboardingFlow } from '../components/onboarding/OnboardingFlow';
import { UserProfile } from '../types/user';

interface UserStoreExampleProps {
  onComplete?: (userData: Partial<UserProfile>) => void;
}

export const UserStoreExample: React.FC<UserStoreExampleProps> = ({ onComplete }) => {
  // Use store selectors for better performance
  const user = useUser();
  const isLoading = useUserLoading();
  const isSaving = useUserSaving();
  const error = useUserError();
  const hasUnsavedChanges = useHasUnsavedChanges();
  const onboardingProgress = useOnboardingProgress();
  const analytics = useUserAnalytics();

  // Get store actions
  const {
    loadProfile,
    saveProfile,
    createProfile,
    updateUser,
    updateUserField,
    saveOnboardingProgress,
    loadOnboardingProgress,
    clearOnboardingProgress,
    goToStep,
    completeStep,
    updateAnalytics,
    resetStore,
    clearError,
    setLoading,
    setSaving
  } = useUserStore();

  // Load profile on mount
  useEffect(() => {
    const initializeProfile = async () => {
      setLoading(true);
      try {
        const result = await loadProfile();
        if (!result.success) {
          // Profile doesn't exist, create new one
          await createProfile({
            profileCompletionPercentage: 0,
            onboardingStep: 1,
            gdprConsentStatus: false,
            emailVerificationStatus: false
          });
        }
        
        // Load onboarding progress
        await loadOnboardingProgress();
      } catch (error) {
        console.error('Failed to initialize profile:', error);
      } finally {
        setLoading(false);
      }
    };

    initializeProfile();
  }, []);

  // Auto-save functionality
  useEffect(() => {
    if (hasUnsavedChanges && !isSaving) {
      const saveTimeout = setTimeout(() => {
        saveProfile();
      }, 2000); // Save after 2 seconds of inactivity

      return () => clearTimeout(saveTimeout);
    }
  }, [user, hasUnsavedChanges, isSaving]);

  const handleOnboardingComplete = async (userData: Partial<UserProfile>) => {
    try {
      // Update user data
      updateUser(userData);
      
      // Save final profile
      const saveResult = await saveProfile();
      if (saveResult.success) {
        // Clear onboarding progress
        clearOnboardingProgress();
        
        // Notify parent of completion
        onComplete?.(userData);
      }
    } catch (error) {
      console.error('Failed to complete onboarding:', error);
    }
  };

  const handleStepChange = async (step: number, data: Partial<UserProfile>) => {
    try {
      // Update user data
      updateUser(data);
      
      // Update onboarding progress
      const completedSteps = [...onboardingProgress.completedSteps];
      if (!completedSteps.includes(step - 1) && step > 1) {
        completedSteps.push(step - 1);
      }
      
      useUserStore.getState().updateOnboardingProgress(step, completedSteps, data);
      
      // Save progress
      await saveOnboardingProgress();
    } catch (error) {
      console.error('Failed to update step:', error);
    }
  };

  const handleSave = async (data: Partial<UserProfile>) => {
    try {
      updateUser(data);
      const result = await saveProfile();
      
      if (result.success) {
        console.log('Profile saved successfully');
      } else {
        console.error('Failed to save profile:', result.error);
      }
    } catch (error) {
      console.error('Error saving profile:', error);
    }
  };

  // Example of field-specific updates
  const updateField = (field: keyof UserProfile, value: any) => {
    updateUserField(field, value);
  };

  // Example of bulk updates
  const updateMultipleFields = (fields: Partial<UserProfile>) => {
    updateUser(fields);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading your profile...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header with status indicators */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-6 py-4">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">MINGUS Profile</h1>
              <p className="text-gray-600">Complete your profile to get started</p>
            </div>
            
            <div className="flex items-center space-x-4">
              {/* Save status */}
              {isSaving && (
                <div className="flex items-center text-blue-600">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></div>
                  <span className="text-sm">Saving...</span>
                </div>
              )}
              
              {hasUnsavedChanges && !isSaving && (
                <div className="flex items-center text-yellow-600">
                  <div className="w-2 h-2 bg-yellow-400 rounded-full mr-2"></div>
                  <span className="text-sm">Unsaved changes</span>
                </div>
              )}
              
              {/* Completion percentage */}
              <div className="text-right">
                <div className="text-2xl font-bold text-blue-600">
                  {analytics.completionPercentage}%
                </div>
                <div className="text-xs text-gray-500">Complete</div>
              </div>
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

      {/* Analytics summary */}
      <div className="max-w-4xl mx-auto px-6 py-4">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Profile Completion Summary</h2>
          
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-4">
            {Object.entries(analytics.categoryCompletions).map(([category, percentage]) => (
              <div key={category} className="text-center">
                <div className="text-2xl font-bold text-blue-600">{percentage}%</div>
                <div className="text-sm text-gray-600 capitalize">{category}</div>
              </div>
            ))}
          </div>
          
          {analytics.nextRecommendedFields.length > 0 && (
            <div className="p-4 bg-blue-50 rounded-lg">
              <p className="text-sm text-blue-800">
                <strong>Next recommended:</strong> {analytics.nextRecommendedFields.join(', ')}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Main onboarding flow */}
      <OnboardingFlow
        onComplete={handleOnboardingComplete}
        onStepChange={handleStepChange}
        onSave={handleSave}
        initialData={user}
        autoSave={true}
        showAnalytics={true}
        allowSkip={true}
      />

      {/* Debug panel (development only) */}
      {process.env.NODE_ENV === 'development' && (
        <div className="max-w-4xl mx-auto px-6 py-4">
          <div className="bg-gray-100 rounded-lg p-4">
            <h3 className="font-medium text-gray-900 mb-2">Debug Information</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div>
                <strong>Current Step:</strong> {onboardingProgress.currentStep}
                <br />
                <strong>Completed Steps:</strong> {onboardingProgress.completedSteps.join(', ')}
                <br />
                <strong>Profile Completion:</strong> {analytics.completionPercentage}%
                <br />
                <strong>Has Unsaved Changes:</strong> {hasUnsavedChanges ? 'Yes' : 'No'}
              </div>
              <div>
                <strong>Missing Fields:</strong> {analytics.missingFields.length}
                <br />
                <strong>Is Loading:</strong> {isLoading ? 'Yes' : 'No'}
                <br />
                <strong>Is Saving:</strong> {isSaving ? 'Yes' : 'No'}
                <br />
                <strong>Error:</strong> {error || 'None'}
              </div>
            </div>
            
            <div className="mt-4 space-x-2">
              <button
                onClick={() => updateField('firstName', 'John')}
                className="px-3 py-1 bg-blue-600 text-white rounded text-xs hover:bg-blue-700"
              >
                Set First Name
              </button>
              <button
                onClick={() => updateMultipleFields({ firstName: 'Jane', lastName: 'Doe' })}
                className="px-3 py-1 bg-green-600 text-white rounded text-xs hover:bg-green-700"
              >
                Set Name
              </button>
              <button
                onClick={() => goToStep(3)}
                className="px-3 py-1 bg-purple-600 text-white rounded text-xs hover:bg-purple-700"
              >
                Go to Step 3
              </button>
              <button
                onClick={resetStore}
                className="px-3 py-1 bg-red-600 text-white rounded text-xs hover:bg-red-700"
              >
                Reset Store
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}; 