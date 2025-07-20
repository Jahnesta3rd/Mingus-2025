import { OnboardingStep, OnboardingProgress, StepCompletionResult, NavigationContext } from '../types/onboarding';

export class OnboardingFlowService {
  private static instance: OnboardingFlowService;
  private steps: OnboardingStep[];
  private baseUrl = '/api/onboarding';

  private constructor() {
    this.steps = this.defineSteps();
  }

  public static getInstance(): OnboardingFlowService {
    if (!OnboardingFlowService.instance) {
      OnboardingFlowService.instance = new OnboardingFlowService();
    }
    return OnboardingFlowService.instance;
  }

  private defineSteps(): OnboardingStep[] {
    return [
      {
        id: 'welcome',
        name: 'welcome',
        title: 'Welcome & Introduction',
        description: 'Introduction to Mingus and onboarding process explanation',
        route: '/onboarding/welcome',
        stepNumber: 1,
        required: true,
        estimatedTime: 2,
        weight: 5,
        completionCriteria: ['viewed_welcome_screen', 'clicked_get_started']
      },
      {
        id: 'choice',
        name: 'choice',
        title: 'Setup Choice',
        description: 'Choose your onboarding experience',
        route: '/onboarding/choice',
        stepNumber: 2,
        required: true,
        estimatedTime: 1,
        weight: 5,
        completionCriteria: ['choice_made'],
        dependencies: ['welcome']
      },
      {
        id: 'profile_setup',
        name: 'profile_setup',
        title: 'Basic Profile Setup',
        description: 'Name, age, location, employment status',
        route: '/onboarding/profile',
        stepNumber: 3,
        required: true,
        estimatedTime: 3,
        weight: 10,
        completionCriteria: ['name_provided', 'age_provided', 'location_provided', 'employment_status_provided'],
        dependencies: ['choice']
      },
      {
        id: 'verification',
        name: 'verification',
        title: 'Phone Verification',
        description: 'Verify your phone number for account security',
        route: '/onboarding/verification',
        stepNumber: 4,
        required: false,
        estimatedTime: 2,
        weight: 8,
        completionCriteria: ['phone_verified', 'verification_code_entered'],
        dependencies: ['profile_setup']
      },
      {
        id: 'preferences',
        name: 'preferences',
        title: 'Preferences & Settings',
        description: 'Risk tolerance, notification preferences, privacy settings',
        route: '/onboarding/preferences',
        stepNumber: 5,
        required: true,
        estimatedTime: 3,
        weight: 10,
        completionCriteria: ['risk_tolerance_set', 'notifications_configured', 'privacy_settings_set'],
        dependencies: ['profile_setup', 'verification']
      },
      {
        id: 'expenses',
        name: 'expenses',
        title: 'Monthly Expenses',
        description: 'Track your monthly expenses',
        route: '/onboarding/expenses',
        stepNumber: 6,
        required: true,
        estimatedTime: 4,
        weight: 15,
        completionCriteria: ['expenses_provided', 'categories_set'],
        dependencies: ['preferences']
      },
      {
        id: 'goals_setup',
        name: 'goals_setup',
        title: 'Financial Goals Setting',
        description: 'Short-term and long-term financial objectives',
        route: '/onboarding/goals',
        stepNumber: 7,
        required: true,
        estimatedTime: 4,
        weight: 15,
        completionCriteria: ['short_term_goals_set', 'long_term_goals_set', 'timeline_provided'],
        dependencies: ['expenses']
      },
      {
        id: 'financial_questionnaire',
        name: 'financial_questionnaire',
        title: 'Financial Assessment',
        description: 'Complete financial questionnaire',
        route: '/onboarding/financial-questionnaire',
        stepNumber: 8,
        required: true,
        estimatedTime: 3,
        weight: 15,
        completionCriteria: ['questionnaire_completed', 'risk_assessment_done'],
        dependencies: ['goals_setup']
      },
      {
        id: 'lifestyle_questionnaire',
        name: 'lifestyle_questionnaire',
        title: 'Lifestyle Assessment',
        description: 'Share your lifestyle preferences',
        route: '/onboarding/lifestyle-questionnaire',
        stepNumber: 9,
        required: true,
        estimatedTime: 3,
        weight: 15,
        completionCriteria: ['lifestyle_assessment_completed', 'wellness_baseline_set'],
        dependencies: ['financial_questionnaire']
      },
      {
        id: 'complete',
        name: 'complete',
        title: 'Onboarding Complete',
        description: 'Setup complete - welcome to Mingus!',
        route: '/onboarding/complete',
        stepNumber: 10,
        required: true,
        estimatedTime: 1,
        weight: 5,
        completionCriteria: ['onboarding_finished'],
        dependencies: ['lifestyle_questionnaire']
      }
    ];
  }

  // Backend API calls
  async fetchProgress(userId: string): Promise<OnboardingProgress> {
    try {
      const response = await fetch(`${this.baseUrl}/progress/steps`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch progress: ${response.statusText}`);
      }

      const data = await response.json();
      
      // Transform legacy format to new format
      if (data.step_status) {
        const completedSteps = Object.entries(data.step_status)
          .filter(([_, status]: [string, any]) => status.completed)
          .map(([step, _]) => step);
        
        return {
          userId,
          currentStep: this.getCurrentStepFromLegacy(data.step_status),
          completedSteps,
          progressPercentage: this.calculateProgressPercentage(completedSteps),
          isCompleted: completedSteps.length === this.steps.length,
          stepCompletionData: data.step_status,
          estimatedTimeRemaining: this.calculateTimeRemaining(completedSteps),
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
          // Legacy support
          stepStatus: data.step_status
        };
      }

      return data;
    } catch (error) {
      console.error('Error fetching onboarding progress:', error);
      throw error;
    }
  }

  async completeStep(userId: string, stepName: string, completionData: Record<string, any>): Promise<StepCompletionResult> {
    try {
      const response = await fetch(`${this.baseUrl}/step/${stepName}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          completed: true,
          responses: completionData
        })
      });

      if (!response.ok) {
        throw new Error(`Failed to complete step: ${response.statusText}`);
      }

      const data = await response.json();
      
      // Get updated progress
      const progress = await this.fetchProgress(userId);
      const nextStep = this.getNextStep(progress);
      
      return {
        success: true,
        stepCompleted: stepName,
        newProgressPercentage: progress.progressPercentage,
        nextStep,
        isOnboardingComplete: progress.isCompleted
      };
    } catch (error) {
      console.error('Error completing step:', error);
      return {
        success: false,
        stepCompleted: stepName,
        newProgressPercentage: 0,
        nextStep: null,
        isOnboardingComplete: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  // Navigation Logic
  async getNavigationContext(userId: string, requestedStep: string): Promise<NavigationContext> {
    const progress = await this.fetchProgress(userId);
    const step = this.getStepById(requestedStep);
    
    if (!step) {
      return {
        currentStep: requestedStep,
        nextStep: null,
        canProceed: false,
        canAccess: false,
        redirectTo: '/onboarding/welcome'
      };
    }

    const canAccess = this.canAccessStep(requestedStep, progress);
    const nextStep = this.getNextStep(progress);
    
    // If trying to access a step they can't access, redirect to correct step
    if (!canAccess) {
      const correctStep = this.getCurrentAccessibleStep(progress);
      return {
        currentStep: requestedStep,
        nextStep,
        canProceed: false,
        canAccess: false,
        redirectTo: correctStep.route
      };
    }

    return {
      currentStep: requestedStep,
      nextStep,
      canProceed: true,
      canAccess: true
    };
  }

  async proceedToNextStep(userId: string, currentStep: string, completionData: Record<string, any>): Promise<{ route: string; isComplete: boolean }> {
    // Complete current step
    const result = await this.completeStep(userId, currentStep, completionData);
    
    if (!result.success) {
      throw new Error(result.error || 'Failed to complete step');
    }

    // If onboarding is complete
    if (result.isOnboardingComplete) {
      return { route: '/dashboard', isComplete: true };
    }

    // Get next step route
    if (result.nextStep) {
      const nextStepInfo = this.getStepById(result.nextStep);
      return { route: nextStepInfo?.route || '/dashboard', isComplete: false };
    }

    return { route: '/dashboard', isComplete: true };
  }

  // Utility methods
  getStepById(stepId: string): OnboardingStep | undefined {
    return this.steps.find(step => step.id === stepId);
  }

  getStepByRoute(route: string): OnboardingStep | undefined {
    return this.steps.find(step => step.route === route);
  }

  canAccessStep(stepId: string, progress: OnboardingProgress): boolean {
    const step = this.getStepById(stepId);
    if (!step) return false;

    // Check if all dependencies are completed
    if (step.dependencies) {
      return step.dependencies.every(dep => progress.completedSteps.includes(dep));
    }

    return true;
  }

  getNextStep(progress: OnboardingProgress): string | null {
    // Find first incomplete step that user can access
    for (const step of this.steps) {
      if (!progress.completedSteps.includes(step.id) && this.canAccessStep(step.id, progress)) {
        return step.id;
      }
    }
    return null;
  }

  getCurrentAccessibleStep(progress: OnboardingProgress): OnboardingStep {
    const nextStep = this.getNextStep(progress);
    if (nextStep) {
      return this.getStepById(nextStep)!;
    }
    // If no next step, return the last step (complete) or welcome
    return this.steps[this.steps.length - 1] || this.steps[0];
  }

  getAllSteps(): OnboardingStep[] {
    return [...this.steps];
  }

  getProgressSummary(progress: OnboardingProgress) {
    const totalSteps = this.steps.filter(s => s.required).length;
    const completedRequiredSteps = progress.completedSteps.filter(stepId => {
      const step = this.getStepById(stepId);
      return step?.required;
    }).length;

    return {
      totalSteps,
      completedSteps: completedRequiredSteps,
      progressPercentage: progress.progressPercentage,
      estimatedTimeRemaining: progress.estimatedTimeRemaining,
      currentStep: this.getStepById(progress.currentStep),
      nextStep: this.getNextStep(progress)
    };
  }

  // Legacy support methods
  private getCurrentStepFromLegacy(stepStatus: Record<string, any>): string {
    for (const step of this.steps) {
      if (!stepStatus[step.id]?.completed) {
        return step.id;
      }
    }
    return 'complete';
  }

  private calculateProgressPercentage(completedSteps: string[]): number {
    const requiredSteps = this.steps.filter(s => s.required);
    const completedRequired = completedSteps.filter(stepId => {
      const step = this.getStepById(stepId);
      return step?.required;
    }).length;
    
    return Math.round((completedRequired / requiredSteps.length) * 100);
  }

  private calculateTimeRemaining(completedSteps: string[]): number {
    const remainingSteps = this.steps.filter(step => 
      !completedSteps.includes(step.id) && step.required
    );
    
    return remainingSteps.reduce((total, step) => total + step.estimatedTime, 0);
  }
} 