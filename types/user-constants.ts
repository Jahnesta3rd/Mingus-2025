// types/user-constants.ts
import type {
  IncomeFrequency,
  CreditScoreRange,
  AgeRange,
  MaritalStatus,
  YearsOfExperience,
  RiskToleranceLevel,
  FinancialKnowledgeLevel,
  HealthCheckinFrequency,
  OnboardingStep,
  FormField
} from './user';

// Constants for enum values
export const INCOME_FREQUENCIES: { value: IncomeFrequency; label: string }[] = [
  { value: 'weekly', label: 'Weekly' },
  { value: 'bi-weekly', label: 'Bi-Weekly' },
  { value: 'semi-monthly', label: 'Semi-Monthly' },
  { value: 'monthly', label: 'Monthly' },
  { value: 'annually', label: 'Annually' }
];

export const CREDIT_SCORE_RANGES: { value: CreditScoreRange; label: string; description: string }[] = [
  { value: 'excellent', label: 'Excellent (800-850)', description: 'Exceptional credit history' },
  { value: 'good', label: 'Good (670-799)', description: 'Above average credit history' },
  { value: 'fair', label: 'Fair (580-669)', description: 'Average credit history' },
  { value: 'poor', label: 'Poor (300-579)', description: 'Below average credit history' },
  { value: 'very_poor', label: 'Very Poor (300-499)', description: 'Significant credit issues' },
  { value: 'unknown', label: 'Unknown', description: 'Credit score not available' }
];

export const AGE_RANGES: { value: AgeRange; label: string }[] = [
  { value: '18-24', label: '18-24 years' },
  { value: '25-34', label: '25-34 years' },
  { value: '35-44', label: '35-44 years' },
  { value: '45-54', label: '45-54 years' },
  { value: '55-64', label: '55-64 years' },
  { value: '65+', label: '65+ years' }
];

export const MARITAL_STATUSES: { value: MaritalStatus; label: string }[] = [
  { value: 'single', label: 'Single' },
  { value: 'married', label: 'Married' },
  { value: 'partnership', label: 'Domestic Partnership' },
  { value: 'divorced', label: 'Divorced' },
  { value: 'widowed', label: 'Widowed' },
  { value: 'prefer_not_to_say', label: 'Prefer not to say' }
];

export const YEARS_OF_EXPERIENCE: { value: YearsOfExperience; label: string }[] = [
  { value: 'less_than_1', label: 'Less than 1 year' },
  { value: '1-3', label: '1-3 years' },
  { value: '4-7', label: '4-7 years' },
  { value: '8-12', label: '8-12 years' },
  { value: '13-20', label: '13-20 years' },
  { value: '20+', label: '20+ years' }
];

export const RISK_TOLERANCE_LEVELS: { value: RiskToleranceLevel; label: string; description: string }[] = [
  { value: 'conservative', label: 'Conservative', description: 'Prefer low-risk, stable investments' },
  { value: 'moderate', label: 'Moderate', description: 'Balance of growth and stability' },
  { value: 'aggressive', label: 'Aggressive', description: 'Seek maximum growth potential' },
  { value: 'unsure', label: 'Unsure', description: 'Need guidance to determine risk tolerance' }
];

export const FINANCIAL_KNOWLEDGE_LEVELS: { value: FinancialKnowledgeLevel; label: string; description: string }[] = [
  { value: 'beginner', label: 'Beginner', description: 'New to financial planning' },
  { value: 'intermediate', label: 'Intermediate', description: 'Some financial knowledge' },
  { value: 'advanced', label: 'Advanced', description: 'Experienced with finances' },
  { value: 'expert', label: 'Expert', description: 'Professional financial knowledge' }
];

export const HEALTH_CHECKIN_FREQUENCIES: { value: HealthCheckinFrequency; label: string; description: string }[] = [
  { value: 'daily', label: 'Daily', description: 'Check in every day' },
  { value: 'weekly', label: 'Weekly', description: 'Check in once a week' },
  { value: 'monthly', label: 'Monthly', description: 'Check in once a month' },
  { value: 'on_demand', label: 'On Demand', description: 'Check in when needed' },
  { value: 'never', label: 'Never', description: 'No health check-ins' }
];

// Common employment statuses
export const EMPLOYMENT_STATUSES = [
  'Full-time Employee',
  'Part-time Employee',
  'Self-employed',
  'Freelancer',
  'Contractor',
  'Unemployed',
  'Student',
  'Retired',
  'Military',
  'Other'
] as const;

// Common education levels
export const EDUCATION_LEVELS = [
  'High School',
  'Some College',
  'Associate Degree',
  'Bachelor\'s Degree',
  'Master\'s Degree',
  'Doctorate',
  'Professional Degree',
  'Trade School',
  'Other'
] as const;

// Common industries
export const INDUSTRIES = [
  'Technology',
  'Healthcare',
  'Finance',
  'Education',
  'Manufacturing',
  'Retail',
  'Real Estate',
  'Government',
  'Non-profit',
  'Entertainment',
  'Transportation',
  'Construction',
  'Agriculture',
  'Energy',
  'Other'
] as const;

// Common financial goals
export const FINANCIAL_GOALS = [
  'Save for Emergency Fund',
  'Pay Off Debt',
  'Save for Retirement',
  'Buy a Home',
  'Start a Business',
  'Save for Education',
  'Travel',
  'Invest in Stocks',
  'Build Credit Score',
  'Create Passive Income',
  'Other'
] as const;

// Contact methods
export const CONTACT_METHODS = [
  'Email',
  'SMS',
  'Phone Call',
  'In-App Notification',
  'Push Notification'
] as const;

// Default notification preferences
export const DEFAULT_NOTIFICATION_PREFERENCES = {
  weeklyInsights: true,
  monthlySpendingSummaries: true,
  goalProgressUpdates: true,
  billPaymentReminders: true,
  marketUpdates: false,
  educationalContent: true,
  productUpdates: false
} as const;

// Profile completion thresholds
export const PROFILE_COMPLETION_THRESHOLDS = {
  BASIC: 25,
  STANDARD: 50,
  COMPREHENSIVE: 75,
  COMPLETE: 90
} as const;

// Onboarding step definitions
export const ONBOARDING_STEPS: OnboardingStep[] = [
  {
    step: 1,
    title: 'Welcome to Mingus',
    subtitle: 'Let\'s get to know you better',
    category: 'critical',
    isRequired: true,
    fields: [
      {
        name: 'firstName',
        type: 'text',
        label: 'First Name',
        placeholder: 'Enter your first name',
        required: true,
        validation: {
          min: 1,
          max: 50,
          message: 'First name is required and must be between 1-50 characters'
        }
      },
      {
        name: 'lastName',
        type: 'text',
        label: 'Last Name',
        placeholder: 'Enter your last name',
        required: true,
        validation: {
          min: 1,
          max: 50,
          message: 'Last name is required and must be between 1-50 characters'
        }
      }
    ]
  },
  {
    step: 2,
    title: 'Financial Basics',
    subtitle: 'Help us understand your financial situation',
    category: 'critical',
    isRequired: true,
    fields: [
      {
        name: 'monthlyIncome',
        type: 'currency',
        label: 'Monthly Income',
        placeholder: 'Enter your monthly income',
        required: true,
        validation: {
          min: 0,
          message: 'Monthly income must be a positive number'
        }
      },
      {
        name: 'incomeFrequency',
        type: 'select',
        label: 'How often do you receive income?',
        required: true,
        options: INCOME_FREQUENCIES
      }
    ]
  },
  {
    step: 3,
    title: 'Financial Goals',
    subtitle: 'What are your primary financial objectives?',
    category: 'important',
    isRequired: false,
    fields: [
      {
        name: 'primaryFinancialGoal',
        type: 'select',
        label: 'Primary Financial Goal',
        required: false,
        options: FINANCIAL_GOALS.map(goal => ({ value: goal, label: goal }))
      },
      {
        name: 'riskToleranceLevel',
        type: 'radio',
        label: 'Investment Risk Tolerance',
        required: false,
        options: RISK_TOLERANCE_LEVELS.map(level => ({ value: level.value, label: level.label }))
      }
    ]
  },
  {
    step: 4,
    title: 'Demographics',
    subtitle: 'Help us personalize your experience',
    category: 'enhanced',
    isRequired: false,
    fields: [
      {
        name: 'ageRange',
        type: 'select',
        label: 'Age Range',
        required: false,
        options: AGE_RANGES
      },
      {
        name: 'maritalStatus',
        type: 'select',
        label: 'Marital Status',
        required: false,
        options: MARITAL_STATUSES
      }
    ]
  },
  {
    step: 5,
    title: 'Contact Preferences',
    subtitle: 'How would you like us to reach you?',
    category: 'important',
    isRequired: false,
    fields: [
      {
        name: 'phoneNumber',
        type: 'tel',
        label: 'Phone Number',
        placeholder: 'Enter your phone number',
        required: false,
        validation: {
          pattern: '^\\+?[1-9]\\d{1,14}$',
          message: 'Please enter a valid phone number'
        }
      },
      {
        name: 'preferredContactMethod',
        type: 'select',
        label: 'Preferred Contact Method',
        required: false,
        options: CONTACT_METHODS.map(method => ({ value: method, label: method }))
      }
    ]
  }
];

// Utility functions
export const getProfileCompletionPercentage = (profile: Partial<UserProfile>): number => {
  const totalFields = 25;
  let completedFields = 0;

  // Check required fields
  if (profile.firstName) completedFields++;
  if (profile.lastName) completedFields++;
  if (profile.dateOfBirth) completedFields++;
  if (profile.zipCode) completedFields++;
  if (profile.phoneNumber) completedFields++;
  if (profile.monthlyIncome) completedFields++;
  if (profile.incomeFrequency) completedFields++;
  if (profile.primaryIncomeSource) completedFields++;
  if (profile.currentSavingsBalance) completedFields++;
  if (profile.totalDebtAmount) completedFields++;
  if (profile.creditScoreRange) completedFields++;
  if (profile.employmentStatus) completedFields++;
  if (profile.ageRange) completedFields++;
  if (profile.maritalStatus) completedFields++;
  if (profile.educationLevel) completedFields++;
  if (profile.occupation) completedFields++;
  if (profile.industry) completedFields++;
  if (profile.yearsOfExperience) completedFields++;
  if (profile.primaryFinancialGoal) completedFields++;
  if (profile.riskToleranceLevel) completedFields++;
  if (profile.financialKnowledgeLevel) completedFields++;
  if (profile.preferredContactMethod) completedFields++;
  if (profile.healthCheckinFrequency) completedFields++;
  if (profile.stressLevelBaseline) completedFields++;

  return Math.round((completedFields / totalFields) * 100);
};

export const getNextRecommendedFields = (profile: Partial<UserProfile>): string[] => {
  const recommendations: string[] = [];

  if (!profile.firstName) recommendations.push('firstName');
  if (!profile.lastName) recommendations.push('lastName');
  if (!profile.monthlyIncome) recommendations.push('monthlyIncome');
  if (!profile.incomeFrequency) recommendations.push('incomeFrequency');
  if (!profile.primaryFinancialGoal) recommendations.push('primaryFinancialGoal');
  if (!profile.riskToleranceLevel) recommendations.push('riskToleranceLevel');
  if (!profile.phoneNumber) recommendations.push('phoneNumber');
  if (!profile.ageRange) recommendations.push('ageRange');

  return recommendations.slice(0, 3); // Return top 3 recommendations
};

export const validateUserProfile = (profile: Partial<UserProfile>): { isValid: boolean; errors: string[] } => {
  const errors: string[] = [];

  // Required field validations
  if (!profile.email) errors.push('Email is required');
  if (profile.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(profile.email)) {
    errors.push('Invalid email format');
  }

  // Phone number validation
  if (profile.phoneNumber && !/^\+?[1-9]\d{1,14}$/.test(profile.phoneNumber)) {
    errors.push('Invalid phone number format');
  }

  // Zip code validation
  if (profile.zipCode && !/^\d{5}(-\d{4})?$/.test(profile.zipCode)) {
    errors.push('Invalid zip code format');
  }

  // Numeric validations
  if (profile.dependentsCount && (profile.dependentsCount < 0 || profile.dependentsCount > 20)) {
    errors.push('Dependents count must be between 0 and 20');
  }

  if (profile.householdSize && (profile.householdSize < 1 || profile.householdSize > 20)) {
    errors.push('Household size must be between 1 and 20');
  }

  if (profile.stressLevelBaseline && (profile.stressLevelBaseline < 1 || profile.stressLevelBaseline > 10)) {
    errors.push('Stress level must be between 1 and 10');
  }

  return {
    isValid: errors.length === 0,
    errors
  };
};

// Export all constants
export {
  INCOME_FREQUENCIES,
  CREDIT_SCORE_RANGES,
  AGE_RANGES,
  MARITAL_STATUSES,
  YEARS_OF_EXPERIENCE,
  RISK_TOLERANCE_LEVELS,
  FINANCIAL_KNOWLEDGE_LEVELS,
  HEALTH_CHECKIN_FREQUENCIES,
  EMPLOYMENT_STATUSES,
  EDUCATION_LEVELS,
  INDUSTRIES,
  FINANCIAL_GOALS,
  CONTACT_METHODS,
  DEFAULT_NOTIFICATION_PREFERENCES,
  PROFILE_COMPLETION_THRESHOLDS,
  ONBOARDING_STEPS,
  getProfileCompletionPercentage,
  getNextRecommendedFields,
  validateUserProfile
}; 