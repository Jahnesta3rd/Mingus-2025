import React from 'react';
import { useAuth } from '../hooks/useAuth';
import { ModularOnboarding } from './ModularOnboarding';
import ExistingOnboardingForm from '../pages/OnboardingPage';

export interface OnboardingRouterProps {
  onComplete: () => void;
}

export default function OnboardingRouter({ onComplete }: OnboardingRouterProps) {
  const { userTier, loading } = useAuth();

  if (loading || userTier === null) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div
          className="h-8 w-8 animate-spin rounded-full border-2 border-neutral-200 border-t-neutral-600"
          role="status"
          aria-label="Loading"
        />
      </div>
    );
  }

  if (userTier === 'mid_tier' || userTier === 'professional') {
    return <ModularOnboarding onComplete={onComplete} />;
  }

  return <ExistingOnboardingForm onComplete={onComplete} />;
}
