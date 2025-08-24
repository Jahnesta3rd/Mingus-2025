// services/onboardingService.ts
import { 
  UserProfile, 
  OnboardingStep, 
  OnboardingProgress, 
  ProfileCompletionAnalytics,
  UserPreferencesValidation 
} from '../types/user';
import { 
  ONBOARDING_STEPS, 
  getOnboardingStep, 
  getTotalOnboardingSteps,
  validateStepCompletion 
} from '../config/onboarding';

export class OnboardingService {
  private currentStep: number = 1;
  private completedSteps: number[] = [];
  private userData: Partial<UserProfile> = {};

  constructor(initialData?: Partial<UserProfile>) {
    if (initialData) {
      this.userData = { ...initialData };
      this.calculateCompletedSteps();
    }
  }

  /**
   * Get current onboarding progress
   */
  getProgress(): OnboardingProgress {
    return {
      userId: this.userData.id || '',
      currentStep: this.currentStep,
      completedSteps: this.completedSteps,
      profileCompletionPercentage: this.calculateProfileCompletion(),
      lastUpdated: new Date(),
      estimatedTimeToComplete: this.estimateTimeToComplete()
    };
  }

  /**
   * Get current step data
   */
  getCurrentStep(): OnboardingStep | undefined {
    return getOnboardingStep(this.currentStep);
  }

  /**
   * Get all onboarding steps
   */
  getAllSteps(): OnboardingStep[] {
    return ONBOARDING_STEPS;
  }

  /**
   * Move to next step
   */
  nextStep(): boolean {
    if (this.currentStep < getTotalOnboardingSteps()) {
      this.currentStep++;
      return true;
    }
    return false;
  }

  /**
   * Move to previous step
   */
  previousStep(): boolean {
    if (this.currentStep > 1) {
      this.currentStep--;
      return true;
    }
    return false;
  }

  /**
   * Jump to specific step
   */
  goToStep(stepNumber: number): boolean {
    if (stepNumber >= 1 && stepNumber <= getTotalOnboardingSteps()) {
      this.currentStep = stepNumber;
      return true;
    }
    return false;
  }

  /**
   * Update user data for current step
   */
  updateStepData(stepData: Record<string, any>): void {
    this.userData = { ...this.userData, ...stepData };
    this.calculateCompletedSteps();
  }

  /**
   * Get current user data
   */
  getUserData(): Partial<UserProfile> {
    return { ...this.userData };
  }

  /**
   * Validate current step
   */
  validateCurrentStep(): UserPreferencesValidation {
    const currentStep = this.getCurrentStep();
    if (!currentStep) {
      return {
        isValid: false,
        errors: [{ field: 'step', message: 'Invalid step', code: 'INVALID_STEP' }],
        warnings: []
      };
    }

    const errors: Array<{ field: string; message: string; code: string }> = [];
    const warnings: Array<{ field: string; message: string; code: string }> = [];

    currentStep.fields.forEach(field => {
      const value = this.userData[field.name as keyof UserProfile];
      
      // Check required fields
      if (field.required && (!value || value === '' || value === null || value === undefined)) {
        errors.push({
          field: field.name,
          message: `${field.label} is required`,
          code: 'REQUIRED_FIELD'
        });
        return;
      }

      // Skip validation if field is empty and not required
      if (!value || value === '' || value === null || value === undefined) {
        return;
      }

      // Validate based on field type and validation rules
      if (field.validation) {
        const { min, max, pattern, message } = field.validation;

        if (min !== undefined) {
          if (typeof value === 'number' && value < min) {
            errors.push({
              field: field.name,
              message: message || `Minimum value is ${min}`,
              code: 'MIN_VALUE'
            });
          }
        }

        if (max !== undefined) {
          if (typeof value === 'number' && value > max) {
            errors.push({
              field: field.name,
              message: message || `Maximum value is ${max}`,
              code: 'MAX_VALUE'
            });
          }
        }

        if (pattern && typeof value === 'string') {
          const regex = new RegExp(pattern);
          if (!regex.test(value)) {
            errors.push({
              field: field.name,
              message: message || 'Invalid format',
              code: 'INVALID_FORMAT'
            });
          }
        }
      }

      // Type-specific validations
      switch (field.type) {
        case 'email':
          if (typeof value === 'string' && !this.isValidEmail(value)) {
            errors.push({
              field: field.name,
              message: 'Please enter a valid email address',
              code: 'INVALID_EMAIL'
            });
          }
          break;

        case 'tel':
          if (typeof value === 'string' && !this.isValidPhoneNumber(value)) {
            errors.push({
              field: field.name,
              message: 'Please enter a valid phone number',
              code: 'INVALID_PHONE'
            });
          }
          break;

        case 'currency':
          if (typeof value === 'number' && value < 0) {
            errors.push({
              field: field.name,
              message: 'Amount cannot be negative',
              code: 'NEGATIVE_AMOUNT'
            });
          }
          break;
      }
    });

    return {
      isValid: errors.length === 0,
      errors,
      warnings
    };
  }

  /**
   * Check if current step can be completed
   */
  canCompleteCurrentStep(): boolean {
    const validation = this.validateCurrentStep();
    return validation.isValid;
  }

  /**
   * Check if onboarding is complete
   */
  isOnboardingComplete(): boolean {
    return this.currentStep >= getTotalOnboardingSteps() && this.canCompleteCurrentStep();
  }

  /**
   * Get profile completion analytics
   */
  getProfileCompletionAnalytics(): ProfileCompletionAnalytics {
    const totalFields = ONBOARDING_STEPS.flatMap(step => step.fields).length;
    const completedFields = Object.keys(this.userData).filter(key => {
      const value = this.userData[key as keyof UserProfile];
      return value !== undefined && value !== null && value !== '';
    }).length;

    const missingFields = this.getMissingFields();
    const nextRecommendedFields = this.getNextRecommendedFields();

    return {
      totalFields,
      completedFields,
      completionPercentage: Math.round((completedFields / totalFields) * 100),
      missingFields,
      nextRecommendedFields,
      categoryCompletions: this.getCategoryCompletions()
    };
  }

  /**
   * Get missing required fields
   */
  private getMissingFields(): string[] {
    const missingFields: string[] = [];

    ONBOARDING_STEPS.forEach(step => {
      step.fields.forEach(field => {
        if (field.required) {
          const value = this.userData[field.name as keyof UserProfile];
          if (!value || value === '' || value === null || value === undefined) {
            missingFields.push(field.name);
          }
        }
      });
    });

    return missingFields;
  }

  /**
   * Get next recommended fields to complete
   */
  private getNextRecommendedFields(): string[] {
    const missingFields = this.getMissingFields();
    const priorityFields = [
      'firstName', 'lastName', 'monthlyIncome', 'incomeFrequency',
      'primaryFinancialGoal', 'riskToleranceLevel', 'phoneNumber', 'ageRange'
    ];

    // Return priority fields that are missing, up to 3
    return priorityFields
      .filter(field => missingFields.includes(field))
      .slice(0, 3);
  }

  /**
   * Get completion percentage by category
   */
  private getCategoryCompletions(): ProfileCompletionAnalytics['categoryCompletions'] {
    const categories = {
      personal: ['firstName', 'lastName', 'dateOfBirth', 'zipCode', 'phoneNumber'],
      financial: ['monthlyIncome', 'incomeFrequency', 'primaryIncomeSource', 'currentSavingsBalance', 'totalDebtAmount', 'creditScoreRange', 'employmentStatus'],
      demographics: ['ageRange', 'maritalStatus', 'dependentsCount', 'householdSize', 'educationLevel', 'occupation', 'industry', 'yearsOfExperience'],
      goals: ['primaryFinancialGoal', 'riskToleranceLevel', 'financialKnowledgeLevel', 'preferredContactMethod'],
      health: ['healthCheckinFrequency', 'stressLevelBaseline'],
      compliance: ['gdprConsentStatus', 'dataSharingPreferences']
    };

    const completions: any = {};

    Object.entries(categories).forEach(([category, fields]) => {
      const completed = fields.filter(field => {
        const value = this.userData[field as keyof UserProfile];
        return value !== undefined && value !== null && value !== '';
      }).length;
      
      completions[category] = Math.round((completed / fields.length) * 100);
    });

    return completions;
  }

  /**
   * Calculate profile completion percentage
   */
  private calculateProfileCompletion(): number {
    const analytics = this.getProfileCompletionAnalytics();
    return analytics.completionPercentage;
  }

  /**
   * Calculate completed steps
   */
  private calculateCompletedSteps(): void {
    this.completedSteps = [];

    ONBOARDING_STEPS.forEach(step => {
      if (validateStepCompletion(step, this.userData)) {
        this.completedSteps.push(step.step);
      }
    });
  }

  /**
   * Estimate time to complete onboarding
   */
  private estimateTimeToComplete(): number {
    const remainingSteps = getTotalOnboardingSteps() - this.currentStep;
    const averageTimePerStep = 2; // minutes
    return remainingSteps * averageTimePerStep;
  }

  /**
   * Validate email format
   */
  private isValidEmail(email: string): boolean {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  }

  /**
   * Validate phone number format
   */
  private isValidPhoneNumber(phone: string): boolean {
    const phoneRegex = /^\+?[1-9]\d{1,14}$/;
    return phoneRegex.test(phone.replace(/\D/g, ''));
  }

  /**
   * Reset onboarding progress
   */
  reset(): void {
    this.currentStep = 1;
    this.completedSteps = [];
    this.userData = {};
  }

  /**
   * Save onboarding progress to storage
   */
  saveProgress(): void {
    const progress = {
      currentStep: this.currentStep,
      completedSteps: this.completedSteps,
      userData: this.userData,
      timestamp: new Date().toISOString()
    };

    try {
      localStorage.setItem('onboarding-progress', JSON.stringify(progress));
    } catch (error) {
      console.error('Failed to save onboarding progress:', error);
    }
  }

  /**
   * Load onboarding progress from storage
   */
  loadProgress(): boolean {
    try {
      const saved = localStorage.getItem('onboarding-progress');
      if (saved) {
        const progress = JSON.parse(saved);
        this.currentStep = progress.currentStep || 1;
        this.completedSteps = progress.completedSteps || [];
        this.userData = progress.userData || {};
        return true;
      }
    } catch (error) {
      console.error('Failed to load onboarding progress:', error);
    }
    return false;
  }

  /**
   * Clear saved progress
   */
  clearProgress(): void {
    try {
      localStorage.removeItem('onboarding-progress');
    } catch (error) {
      console.error('Failed to clear onboarding progress:', error);
    }
  }
}

// Export singleton instance
export const onboardingService = new OnboardingService(); 