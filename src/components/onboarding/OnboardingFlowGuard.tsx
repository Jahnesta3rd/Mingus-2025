import React, { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { OnboardingFlowService } from '../../services/OnboardingFlowService';
import { NavigationContext } from '../../types/onboarding';

interface OnboardingFlowGuardProps {
  children: React.ReactNode;
  stepId: string;
  userId: string;
}

export const OnboardingFlowGuard: React.FC<OnboardingFlowGuardProps> = ({
  children,
  stepId,
  userId
}) => {
  const [navigationContext, setNavigationContext] = useState<NavigationContext | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();
  const location = useLocation();
  const flowService = OnboardingFlowService.getInstance();

  useEffect(() => {
    checkAccess();
  }, [stepId, userId, location.pathname]);

  const checkAccess = async () => {
    try {
      setIsLoading(true);
      const context = await flowService.getNavigationContext(userId, stepId);
      setNavigationContext(context);

      // If user can't access this step, redirect
      if (!context.canAccess && context.redirectTo) {
        navigate(context.redirectTo, { replace: true });
        return;
      }
    } catch (error) {
      console.error('Error checking step access:', error);
      // On error, redirect to welcome
      navigate('/onboarding/welcome', { replace: true });
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Validating step access...</p>
        </div>
      </div>
    );
  }

  if (!navigationContext?.canAccess) {
    return null; // Will redirect in useEffect
  }

  return <>{children}</>;
};

export default OnboardingFlowGuard; 