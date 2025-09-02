import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { OnboardingFlowService } from '../../services/OnboardingFlowService';

interface UniversalContinueButtonProps {
  userId: string;
  currentStep: string;
  completionData: Record<string, any>;
  isValid: boolean;
  className?: string;
  children?: React.ReactNode;
  onSuccess?: (result: { route: string; isComplete: boolean }) => void;
  onError?: (error: string) => void;
}

export const UniversalContinueButton: React.FC<UniversalContinueButtonProps> = ({
  userId,
  currentStep,
  completionData,
  isValid,
  className = '',
  children = 'Continue',
  onSuccess,
  onError
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const flowService = OnboardingFlowService.getInstance();

  const handleContinue = async () => {
    if (!isValid || isLoading) return;

    try {
      setIsLoading(true);
      const result = await flowService.proceedToNextStep(userId, currentStep, completionData);
      
      if (onSuccess) {
        onSuccess(result);
      } else {
        if (result.isComplete) {
          // Show completion celebration or go to dashboard
          navigate('/onboarding/complete');
        } else {
          navigate(result.route);
        }
      }
    } catch (error) {
      console.error('Error proceeding to next step:', error);
      const errorMessage = error instanceof Error ? error.message : 'Something went wrong. Please try again.';
      
      if (onError) {
        onError(errorMessage);
      } else {
        alert(errorMessage);
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <button
      onClick={handleContinue}
      disabled={!isValid || isLoading}
      className={`
        px-6 py-3 bg-blue-600 text-white rounded-lg font-medium
        hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed
        transition-colors duration-200 flex items-center justify-center
        ${className}
      `}
    >
      {isLoading ? (
        <>
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
          Processing...
        </>
      ) : (
        children
      )}
    </button>
  );
};

export default UniversalContinueButton; 