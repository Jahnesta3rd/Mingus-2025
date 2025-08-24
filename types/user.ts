// types/user.ts
export interface UserProfile {
  // Authentication & Profile
  id: string;
  email: string;
  firstName?: string;
  lastName?: string;
  dateOfBirth?: Date;
  zipCode?: string;
  phoneNumber?: string;
  emailVerificationStatus: boolean;

  // Financial Data
  monthlyIncome?: number;
  incomeFrequency?: 'weekly' | 'bi-weekly' | 'semi-monthly' | 'monthly' | 'annually';
  primaryIncomeSource?: string;
  currentSavingsBalance?: number;
  totalDebtAmount?: number;
  creditScoreRange?: 'excellent' | 'good' | 'fair' | 'poor' | 'very_poor' | 'unknown';
  employmentStatus?: string;

  // Demographics
  ageRange?: '18-24' | '25-34' | '35-44' | '45-54' | '55-64' | '65+';
  maritalStatus?: 'single' | 'married' | 'partnership' | 'divorced' | 'widowed' | 'prefer_not_to_say';
  dependentsCount?: number;
  householdSize?: number;
  educationLevel?: string;
  occupation?: string;
  industry?: string;
  yearsOfExperience?: 'less_than_1' | '1-3' | '4-7' | '8-12' | '13-20' | '20+';

  // Goals & Preferences
  primaryFinancialGoal?: string;
  riskToleranceLevel?: 'conservative' | 'moderate' | 'aggressive' | 'unsure';
  financialKnowledgeLevel?: 'beginner' | 'intermediate' | 'advanced' | 'expert';
  preferredContactMethod?: string;
  notificationPreferences?: NotificationPreferences;

  // Health & Wellness
  healthCheckinFrequency?: 'daily' | 'weekly' | 'monthly' | 'on_demand' | 'never';
  stressLevelBaseline?: number;
  wellnessGoals?: string[];

  // Meta
  profileCompletionPercentage: number;
  onboardingStep: number;
  gdprConsentStatus: boolean;
  dataSharingPreferences?: string;
}

export interface NotificationPreferences {
  weeklyInsights: boolean;
  monthlySpendingSummaries: boolean;
  goalProgressUpdates: boolean;
  billPaymentReminders: boolean;
  marketUpdates: boolean;
  educationalContent: boolean;
  productUpdates: boolean;
}

export interface OnboardingStep {
  step: number;
  title: string;
  subtitle?: string;
  fields: FormField[];
  isRequired: boolean;
  category: 'critical' | 'important' | 'enhanced';
}

export interface FormField {
  name: string;
  type: 'text' | 'email' | 'tel' | 'date' | 'number' | 'select' | 'checkbox' | 'radio' | 'slider' | 'currency';
  label: string;
  placeholder?: string;
  subtitle?: string;
  required: boolean;
  options?: { value: string; label: string }[];
  validation?: {
    min?: number;
    max?: number;
    pattern?: string;
    message?: string;
  };
}

// Additional utility types for better type safety
export type IncomeFrequency = 'weekly' | 'bi-weekly' | 'semi-monthly' | 'monthly' | 'annually';
export type CreditScoreRange = 'excellent' | 'good' | 'fair' | 'poor' | 'very_poor' | 'unknown';
export type AgeRange = '18-24' | '25-34' | '35-44' | '45-54' | '55-64' | '65+';
export type MaritalStatus = 'single' | 'married' | 'partnership' | 'divorced' | 'widowed' | 'prefer_not_to_say';
export type YearsOfExperience = 'less_than_1' | '1-3' | '4-7' | '8-12' | '13-20' | '20+';
export type RiskToleranceLevel = 'conservative' | 'moderate' | 'aggressive' | 'unsure';
export type FinancialKnowledgeLevel = 'beginner' | 'intermediate' | 'advanced' | 'expert';
export type HealthCheckinFrequency = 'daily' | 'weekly' | 'monthly' | 'on_demand' | 'never';

// Type for partial user profile updates
export type UserProfileUpdate = Partial<Omit<UserProfile, 'id' | 'email' | 'profileCompletionPercentage'>>;

// Type for creating new user profiles
export type CreateUserProfile = Omit<UserProfile, 'id' | 'profileCompletionPercentage' | 'onboardingStep' | 'emailVerificationStatus' | 'gdprConsentStatus'> & {
  emailVerificationStatus?: boolean;
  gdprConsentStatus?: boolean;
};

// Type for onboarding progress tracking
export interface OnboardingProgress {
  userId: string;
  currentStep: number;
  completedSteps: number[];
  profileCompletionPercentage: number;
  lastUpdated: Date;
  estimatedTimeToComplete?: number; // in minutes
}

// Type for profile completion analytics
export interface ProfileCompletionAnalytics {
  totalFields: number;
  completedFields: number;
  completionPercentage: number;
  missingFields: string[];
  nextRecommendedFields: string[];
  categoryCompletions: {
    personal: number;
    financial: number;
    demographics: number;
    goals: number;
    health: number;
    compliance: number;
  };
}

// Type for user preferences validation
export interface UserPreferencesValidation {
  isValid: boolean;
  errors: {
    field: string;
    message: string;
    code: string;
  }[];
  warnings: {
    field: string;
    message: string;
    code: string;
  }[];
}

// Type for notification preferences with more granular control
export interface DetailedNotificationPreferences extends NotificationPreferences {
  frequency: 'immediate' | 'daily' | 'weekly' | 'monthly';
  quietHours: {
    enabled: boolean;
    startTime?: string; // HH:mm format
    endTime?: string; // HH:mm format
    timezone?: string;
  };
  channels: {
    email: boolean;
    sms: boolean;
    push: boolean;
    inApp: boolean;
  };
}

// Type for wellness goals with more structure
export interface WellnessGoal {
  id: string;
  category: 'physical' | 'mental' | 'financial' | 'social';
  title: string;
  description?: string;
  targetValue?: number;
  currentValue?: number;
  unit?: string;
  deadline?: Date;
  isActive: boolean;
  progress: number; // 0-100
}

// Type for comprehensive wellness data
export interface WellnessData {
  goals: WellnessGoal[];
  stressLevelBaseline: number;
  stressLevelCurrent?: number;
  lastCheckin?: Date;
  checkinFrequency: HealthCheckinFrequency;
  moodTrend?: {
    date: Date;
    mood: number; // 1-10 scale
    stress: number; // 1-10 scale
    energy: number; // 1-10 scale
  }[];
}

// Type for financial health assessment
export interface FinancialHealthAssessment {
  score: number; // 0-100
  category: 'excellent' | 'good' | 'fair' | 'poor' | 'critical';
  factors: {
    incomeStability: number;
    debtToIncomeRatio: number;
    savingsRate: number;
    emergencyFund: number;
    creditScore: number;
    investmentDiversification: number;
  };
  recommendations: string[];
  riskFactors: string[];
  lastUpdated: Date;
}

// Type for user activity tracking
export interface UserActivity {
  userId: string;
  lastLogin: Date;
  loginCount: number;
  featuresUsed: string[];
  timeSpent: {
    feature: string;
    duration: number; // in minutes
    date: Date;
  }[];
  engagementScore: number; // 0-100
}

// Type for GDPR compliance tracking
export interface GDPRCompliance {
  userId: string;
  consentStatus: boolean;
  consentDate?: Date;
  consentVersion: string;
  dataSharingPreferences: {
    marketing: boolean;
    analytics: boolean;
    thirdParty: boolean;
    research: boolean;
  };
  dataRetentionPreferences: {
    accountDeletion: 'immediate' | '30_days' | '90_days' | '1_year';
    dataAnonymization: boolean;
  };
  lastUpdated: Date;
}

// Type for onboarding flow configuration
export interface OnboardingFlow {
  steps: OnboardingStep[];
  version: string;
  isActive: boolean;
  targetAudience: 'new_users' | 'returning_users' | 'premium_users';
  estimatedDuration: number; // in minutes
  requiredFields: string[];
  optionalFields: string[];
}

// Type for form validation rules
export interface ValidationRule {
  type: 'required' | 'min' | 'max' | 'pattern' | 'custom';
  value?: any;
  message: string;
  field: string;
}

// Type for form submission
export interface FormSubmission {
  userId: string;
  step: number;
  fields: {
    name: string;
    value: any;
    validationErrors?: string[];
  }[];
  submittedAt: Date;
  isValid: boolean;
  progress: number; // 0-100
}

// Export all types for easy importing
export type {
  UserProfile,
  NotificationPreferences,
  OnboardingStep,
  FormField,
  UserProfileUpdate,
  CreateUserProfile,
  OnboardingProgress,
  ProfileCompletionAnalytics,
  UserPreferencesValidation,
  DetailedNotificationPreferences,
  WellnessGoal,
  WellnessData,
  FinancialHealthAssessment,
  UserActivity,
  GDPRCompliance,
  OnboardingFlow,
  ValidationRule,
  FormSubmission,
}; 