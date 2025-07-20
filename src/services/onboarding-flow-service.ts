import { OnboardingStep, StepStatus } from '../types/onboarding';

export interface OnboardingFlowConfig {
  steps: OnboardingStep[];
  allowSkip: boolean;
  requireCompletion: boolean;
}

export interface FlowValidationResult {
  canProceed: boolean;
  nextStep?: string;
  requiredSteps?: string[];
  message?: string;
}

export class OnboardingFlowService {
  private static readonly STEP_ORDER = [
    'welcome',
    'choice',
    'profile',
    'preferences',
    'expenses',
    'goals',
    'financial_questionnaire',
    'lifestyle_questionnaire',
    'complete'
  ];

  private static readonly STEP_DEPENDENCIES: Record<string, string[]> = {
    'profile': ['choice'],
    'preferences': ['profile'],
    'expenses': ['preferences'],
    'goals': ['expenses'],
    'financial_questionnaire': ['goals'],
    'lifestyle_questionnaire': ['financial_questionnaire'],
    'complete': ['lifestyle_questionnaire']
  };

  private static readonly STEP_ROUTES: Record<string, string> = {
    'welcome': '/onboarding/welcome',
    'choice': '/onboarding/choice',
    'profile': '/onboarding/profile',
    'preferences': '/onboarding/preferences',
    'expenses': '/onboarding/expenses',
    'goals': '/onboarding/goals',
    'financial_questionnaire': '/onboarding/financial-questionnaire',
    'lifestyle_questionnaire': '/onboarding/lifestyle-questionnaire',
    'complete': '/onboarding/complete'
  };

  /**
   * Get the next step based on current progress
   */
  static async getNextStep(currentStep: string, stepStatus: Record<string, StepStatus>): Promise<string | null> {
    const currentIndex = this.STEP_ORDER.indexOf(currentStep);
    if (currentIndex === -1) return null;

    // Find the next incomplete step
    for (let i = currentIndex + 1; i < this.STEP_ORDER.length; i++) {
      const nextStep = this.STEP_ORDER[i];
      if (!stepStatus[nextStep]?.completed) {
        return nextStep;
      }
    }

    return null; // All steps completed
  }

  /**
   * Validate if user can proceed to a specific step
   */
  static validateStepAccess(targetStep: string, stepStatus: Record<string, StepStatus>): FlowValidationResult {
    const targetIndex = this.STEP_ORDER.indexOf(targetStep);
    if (targetIndex === -1) {
      return {
        canProceed: false,
        message: 'Invalid step'
      };
    }

    // Check dependencies
    const dependencies = this.STEP_DEPENDENCIES[targetStep] || [];
    const missingDependencies = dependencies.filter(dep => !stepStatus[dep]?.completed);

    if (missingDependencies.length > 0) {
      return {
        canProceed: false,
        requiredSteps: missingDependencies,
        message: `Complete ${missingDependencies.join(', ')} first`
      };
    }

    return {
      canProceed: true,
      nextStep: targetStep
    };
  }

  /**
   * Get the route for a step
   */
  static getStepRoute(stepName: string): string {
    return this.STEP_ROUTES[stepName] || '/onboarding/welcome';
  }

  /**
   * Get the current step from step status
   */
  static getCurrentStep(stepStatus: Record<string, StepStatus>): string {
    for (const step of this.STEP_ORDER) {
      if (!stepStatus[step]?.completed) {
        return step;
      }
    }
    return 'complete';
  }

  /**
   * Calculate completion percentage
   */
  static calculateCompletionPercentage(stepStatus: Record<string, StepStatus>): number {
    const completedSteps = Object.values(stepStatus).filter(status => status.completed).length;
    return Math.round((completedSteps / this.STEP_ORDER.length) * 100);
  }

  /**
   * Check if onboarding is complete
   */
  static isOnboardingComplete(stepStatus: Record<string, StepStatus>): boolean {
    return this.STEP_ORDER.every(step => stepStatus[step]?.completed);
  }

  /**
   * Get step display information
   */
  static getStepInfo(stepName: string): OnboardingStep {
    const stepInfo: Record<string, OnboardingStep> = {
      welcome: {
        name: 'welcome',
        displayName: 'Welcome',
        description: 'Get started with Mingus',
        icon: '👋',
        isRequired: true,
        canSkip: false
      },
      choice: {
        name: 'choice',
        displayName: 'Setup Choice',
        description: 'Choose your onboarding experience',
        icon: '🎯',
        isRequired: true,
        canSkip: false
      },
      profile: {
        name: 'profile',
        displayName: 'Profile',
        description: 'Tell us about yourself',
        icon: '👤',
        isRequired: true,
        canSkip: false
      },
      preferences: {
        name: 'preferences',
        displayName: 'Preferences',
        description: 'Set your financial preferences',
        icon: '⚙️',
        isRequired: true,
        canSkip: false
      },
      expenses: {
        name: 'expenses',
        displayName: 'Expenses',
        description: 'Track your monthly expenses',
        icon: '💰',
        isRequired: true,
        canSkip: false
      },
      goals: {
        name: 'goals',
        displayName: 'Goals',
        description: 'Set your financial goals',
        icon: '🎯',
        isRequired: true,
        canSkip: false
      },
      financial_questionnaire: {
        name: 'financial_questionnaire',
        displayName: 'Financial Assessment',
        description: 'Complete financial questionnaire',
        icon: '📊',
        isRequired: true,
        canSkip: false
      },
      lifestyle_questionnaire: {
        name: 'lifestyle_questionnaire',
        displayName: 'Lifestyle Assessment',
        description: 'Share your lifestyle preferences',
        icon: '🌱',
        isRequired: true,
        canSkip: false
      },
      complete: {
        name: 'complete',
        displayName: 'Complete',
        description: 'Onboarding complete',
        icon: '✅',
        isRequired: true,
        canSkip: false
      }
    };

    return stepInfo[stepName] || {
      name: stepName,
      displayName: stepName,
      description: 'Unknown step',
      icon: '❓',
      isRequired: false,
      canSkip: true
    };
  }

  /**
   * Mark a step as completed
   */
  static async markStepCompleted(stepName: string, responses?: any): Promise<boolean> {
    try {
      const response = await fetch(`/api/onboarding/step/${stepName}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          completed: true,
          responses
        }),
      });

      if (response.ok) {
        return true;
      } else {
        console.error('Failed to mark step as completed:', await response.text());
        return false;
      }
    } catch (error) {
      console.error('Error marking step as completed:', error);
      return false;
    }
  }

  /**
   * Get onboarding progress from backend
   */
  static async getOnboardingProgress(): Promise<Record<string, StepStatus> | null> {
    try {
      const response = await fetch('/api/onboarding/progress/steps');
      if (response.ok) {
        const data = await response.json();
        return data.step_status || {};
      } else {
        console.error('Failed to fetch onboarding progress:', await response.text());
        return null;
      }
    } catch (error) {
      console.error('Error fetching onboarding progress:', error);
      return null;
    }
  }

  /**
   * Navigate to the next step
   */
  static async navigateToNextStep(currentStep: string): Promise<string | null> {
    const stepStatus = await this.getOnboardingProgress();
    if (!stepStatus) return null;

    const nextStep = await this.getNextStep(currentStep, stepStatus);
    if (nextStep) {
      const route = this.getStepRoute(nextStep);
      window.location.href = route;
      return nextStep;
    }

    return null;
  }

  /**
   * Navigate to a specific step with validation
   */
  static async navigateToStep(targetStep: string): Promise<boolean> {
    const stepStatus = await this.getOnboardingProgress();
    if (!stepStatus) return false;

    const validation = this.validateStepAccess(targetStep, stepStatus);
    if (validation.canProceed) {
      const route = this.getStepRoute(targetStep);
      window.location.href = route;
      return true;
    } else {
      console.warn('Cannot navigate to step:', validation.message);
      return false;
    }
  }

  /**
   * Get all steps with their status
   */
  static async getAllStepsWithStatus(): Promise<OnboardingStep[]> {
    const stepStatus = await this.getOnboardingProgress();
    if (!stepStatus) return [];

    return this.STEP_ORDER.map(stepName => {
      const stepInfo = this.getStepInfo(stepName);
      const status = stepStatus[stepName];
      
      return {
        ...stepInfo,
        completed: status?.completed || false,
        completedAt: status?.completed_at,
        isCurrent: this.getCurrentStep(stepStatus) === stepName
      };
    });
  }
} 