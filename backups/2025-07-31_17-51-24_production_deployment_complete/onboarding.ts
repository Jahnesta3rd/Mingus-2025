// config/onboarding.ts
import { OnboardingStep } from '../types/user';

export const ONBOARDING_STEPS: OnboardingStep[] = [
  {
    step: 1,
    title: "Let's get to know you",
    subtitle: "We'll start with some basic information",
    category: 'critical',
    isRequired: true,
    fields: [
      {
        name: 'firstName',
        type: 'text',
        label: "What's your first name?",
        placeholder: 'Enter your first name',
        required: true,
        validation: {
          min: 2,
          max: 50,
          pattern: '^[a-zA-Z]+$',
          message: 'Please enter a valid first name'
        }
      },
      {
        name: 'lastName',
        type: 'text',
        label: "What's your last name?",
        placeholder: 'Enter your last name',
        required: true,
        validation: {
          min: 2,
          max: 50,
          pattern: '^[a-zA-Z]+$',
          message: 'Please enter a valid last name'
        }
      },
      {
        name: 'dateOfBirth',
        type: 'date',
        label: 'When were you born?',
        subtitle: 'We use this to provide age-appropriate financial advice',
        required: true,
        validation: {
          message: 'You must be 18 or older to use this service'
        }
      },
      {
        name: 'zipCode',
        type: 'text',
        label: "What's your ZIP code?",
        subtitle: 'This helps us provide location-specific financial insights',
        placeholder: '12345',
        required: true,
        validation: {
          pattern: '^\\d{5}$',
          message: 'Please enter a valid 5-digit ZIP code'
        }
      },
      {
        name: 'phoneNumber',
        type: 'tel',
        label: "What's your phone number?",
        subtitle: 'For account security and important notifications',
        placeholder: '(555) 123-4567',
        required: true
      }
    ]
  },
  {
    step: 2,
    title: "Tell us about your finances",
    subtitle: "This helps us provide personalized insights",
    category: 'critical',
    isRequired: true,
    fields: [
      {
        name: 'monthlyIncome',
        type: 'currency',
        label: "What's your monthly income before taxes?",
        subtitle: 'Include all sources of income',
        placeholder: '$5,000',
        required: true,
        validation: {
          min: 0,
          max: 999999,
          message: 'Please enter a valid income amount'
        }
      },
      {
        name: 'incomeFrequency',
        type: 'select',
        label: 'How often do you receive income?',
        required: true,
        options: [
          { value: 'weekly', label: 'Weekly' },
          { value: 'bi-weekly', label: 'Bi-weekly (every 2 weeks)' },
          { value: 'semi-monthly', label: 'Semi-monthly (twice a month)' },
          { value: 'monthly', label: 'Monthly' },
          { value: 'annually', label: 'Annually' }
        ]
      },
      {
        name: 'primaryIncomeSource',
        type: 'select',
        label: "What's your primary source of income?",
        required: true,
        options: [
          { value: 'full-time-employment', label: 'Full-time employment' },
          { value: 'part-time-employment', label: 'Part-time employment' },
          { value: 'self-employment', label: 'Self-employment/Freelancing' },
          { value: 'business-ownership', label: 'Business ownership' },
          { value: 'investment-income', label: 'Investment income' },
          { value: 'retirement', label: 'Retirement/Pension' },
          { value: 'government-benefits', label: 'Government benefits' },
          { value: 'other', label: 'Other' }
        ]
      },
      {
        name: 'employmentStatus',
        type: 'select',
        label: "What's your current employment status?",
        required: true,
        options: [
          { value: 'employed-full-time', label: 'Employed full-time' },
          { value: 'employed-part-time', label: 'Employed part-time' },
          { value: 'self-employed', label: 'Self-employed' },
          { value: 'unemployed', label: 'Unemployed' },
          { value: 'student', label: 'Student' },
          { value: 'retired', label: 'Retired' },
          { value: 'unable-to-work', label: 'Unable to work' }
        ]
      }
    ]
  },
  {
    step: 3,
    title: "Your financial picture",
    subtitle: "Help us understand your current financial situation",
    category: 'critical',
    isRequired: true,
    fields: [
      {
        name: 'currentSavingsBalance',
        type: 'currency',
        label: 'How much do you currently have in savings?',
        subtitle: 'Include checking, savings, and money market accounts',
        placeholder: '$10,000',
        required: false
      },
      {
        name: 'totalDebtAmount',
        type: 'currency',
        label: "What's your total debt amount?",
        subtitle: 'Include credit cards, loans, mortgage, etc.',
        placeholder: '$25,000',
        required: false
      },
      {
        name: 'creditScoreRange',
        type: 'select',
        label: "What's your approximate credit score?",
        required: false,
        options: [
          { value: 'excellent', label: 'Excellent (750+)' },
          { value: 'good', label: 'Good (700-749)' },
          { value: 'fair', label: 'Fair (650-699)' },
          { value: 'poor', label: 'Poor (600-649)' },
          { value: 'very_poor', label: 'Very Poor (Below 600)' },
          { value: 'unknown', label: "I don't know" }
        ]
      }
    ]
  },
  {
    step: 4,
    title: "Your demographics",
    subtitle: "Help us personalize your experience",
    category: 'important',
    isRequired: false,
    fields: [
      {
        name: 'ageRange',
        type: 'select',
        label: 'What age range are you in?',
        required: false,
        options: [
          { value: '18-24', label: '18-24 years' },
          { value: '25-34', label: '25-34 years' },
          { value: '35-44', label: '35-44 years' },
          { value: '45-54', label: '45-54 years' },
          { value: '55-64', label: '55-64 years' },
          { value: '65+', label: '65+ years' }
        ]
      },
      {
        name: 'maritalStatus',
        type: 'select',
        label: 'What is your marital status?',
        required: false,
        options: [
          { value: 'single', label: 'Single' },
          { value: 'married', label: 'Married' },
          { value: 'partnership', label: 'Domestic Partnership' },
          { value: 'divorced', label: 'Divorced' },
          { value: 'widowed', label: 'Widowed' },
          { value: 'prefer_not_to_say', label: 'Prefer not to say' }
        ]
      },
      {
        name: 'dependentsCount',
        type: 'number',
        label: 'How many dependents do you have?',
        subtitle: 'Children or others you financially support',
        placeholder: '0',
        required: false,
        validation: {
          min: 0,
          max: 20,
          message: 'Please enter a number between 0 and 20'
        }
      },
      {
        name: 'householdSize',
        type: 'number',
        label: 'How many people are in your household?',
        subtitle: 'Including yourself',
        placeholder: '1',
        required: false,
        validation: {
          min: 1,
          max: 20,
          message: 'Please enter a number between 1 and 20'
        }
      }
    ]
  },
  {
    step: 5,
    title: "Education & Career",
    subtitle: "Tell us about your background",
    category: 'important',
    isRequired: false,
    fields: [
      {
        name: 'educationLevel',
        type: 'select',
        label: 'What is your highest level of education?',
        required: false,
        options: [
          { value: 'high-school', label: 'High School' },
          { value: 'some-college', label: 'Some College' },
          { value: 'associate-degree', label: 'Associate Degree' },
          { value: 'bachelors-degree', label: "Bachelor's Degree" },
          { value: 'masters-degree', label: "Master's Degree" },
          { value: 'doctorate', label: 'Doctorate' },
          { value: 'professional-degree', label: 'Professional Degree' },
          { value: 'trade-school', label: 'Trade School' },
          { value: 'other', label: 'Other' }
        ]
      },
      {
        name: 'occupation',
        type: 'text',
        label: 'What is your current job title?',
        placeholder: 'e.g., Software Engineer, Teacher, Manager',
        required: false,
        validation: {
          max: 100,
          message: 'Job title must be less than 100 characters'
        }
      },
      {
        name: 'industry',
        type: 'select',
        label: 'What industry do you work in?',
        required: false,
        options: [
          { value: 'technology', label: 'Technology' },
          { value: 'healthcare', label: 'Healthcare' },
          { value: 'finance', label: 'Finance' },
          { value: 'education', label: 'Education' },
          { value: 'manufacturing', label: 'Manufacturing' },
          { value: 'retail', label: 'Retail' },
          { value: 'real-estate', label: 'Real Estate' },
          { value: 'government', label: 'Government' },
          { value: 'non-profit', label: 'Non-profit' },
          { value: 'entertainment', label: 'Entertainment' },
          { value: 'transportation', label: 'Transportation' },
          { value: 'construction', label: 'Construction' },
          { value: 'agriculture', label: 'Agriculture' },
          { value: 'energy', label: 'Energy' },
          { value: 'other', label: 'Other' }
        ]
      },
      {
        name: 'yearsOfExperience',
        type: 'select',
        label: 'How many years of work experience do you have?',
        required: false,
        options: [
          { value: 'less_than_1', label: 'Less than 1 year' },
          { value: '1-3', label: '1-3 years' },
          { value: '4-7', label: '4-7 years' },
          { value: '8-12', label: '8-12 years' },
          { value: '13-20', label: '13-20 years' },
          { value: '20+', label: '20+ years' }
        ]
      }
    ]
  },
  {
    step: 6,
    title: "Your financial goals",
    subtitle: "What are you working towards?",
    category: 'important',
    isRequired: false,
    fields: [
      {
        name: 'primaryFinancialGoal',
        type: 'select',
        label: 'What is your primary financial goal?',
        required: false,
        options: [
          { value: 'save-for-emergency-fund', label: 'Save for Emergency Fund' },
          { value: 'pay-off-debt', label: 'Pay Off Debt' },
          { value: 'save-for-retirement', label: 'Save for Retirement' },
          { value: 'buy-a-home', label: 'Buy a Home' },
          { value: 'start-a-business', label: 'Start a Business' },
          { value: 'save-for-education', label: 'Save for Education' },
          { value: 'travel', label: 'Travel' },
          { value: 'invest-in-stocks', label: 'Invest in Stocks' },
          { value: 'build-credit-score', label: 'Build Credit Score' },
          { value: 'create-passive-income', label: 'Create Passive Income' },
          { value: 'other', label: 'Other' }
        ]
      },
      {
        name: 'riskToleranceLevel',
        type: 'select',
        label: 'How would you describe your investment risk tolerance?',
        subtitle: 'This helps us recommend appropriate financial products',
        required: false,
        options: [
          { value: 'conservative', label: 'Conservative - I prefer low-risk, stable investments' },
          { value: 'moderate', label: 'Moderate - I want a balance of growth and stability' },
          { value: 'aggressive', label: 'Aggressive - I seek maximum growth potential' },
          { value: 'unsure', label: 'Unsure - I need guidance to determine my risk tolerance' }
        ]
      },
      {
        name: 'financialKnowledgeLevel',
        type: 'select',
        label: 'How would you rate your financial knowledge?',
        required: false,
        options: [
          { value: 'beginner', label: 'Beginner - New to financial planning' },
          { value: 'intermediate', label: 'Intermediate - Some financial knowledge' },
          { value: 'advanced', label: 'Advanced - Experienced with finances' },
          { value: 'expert', label: 'Expert - Professional financial knowledge' }
        ]
      }
    ]
  },
  {
    step: 7,
    title: "Communication preferences",
    subtitle: "How would you like us to reach you?",
    category: 'important',
    isRequired: false,
    fields: [
      {
        name: 'preferredContactMethod',
        type: 'select',
        label: 'What is your preferred method of contact?',
        required: false,
        options: [
          { value: 'email', label: 'Email' },
          { value: 'sms', label: 'SMS/Text Message' },
          { value: 'phone-call', label: 'Phone Call' },
          { value: 'in-app-notification', label: 'In-App Notification' },
          { value: 'push-notification', label: 'Push Notification' }
        ]
      }
    ]
  },
  {
    step: 8,
    title: "Health & Wellness",
    subtitle: "We care about your overall well-being",
    category: 'enhanced',
    isRequired: false,
    fields: [
      {
        name: 'healthCheckinFrequency',
        type: 'select',
        label: 'How often would you like health check-ins?',
        subtitle: 'We can help you manage stress and maintain work-life balance',
        required: false,
        options: [
          { value: 'daily', label: 'Daily' },
          { value: 'weekly', label: 'Weekly' },
          { value: 'monthly', label: 'Monthly' },
          { value: 'on_demand', label: 'On Demand' },
          { value: 'never', label: 'Never' }
        ]
      },
      {
        name: 'stressLevelBaseline',
        type: 'slider',
        label: 'On a scale of 1-10, how would you rate your current stress level?',
        subtitle: '1 = Very relaxed, 10 = Extremely stressed',
        required: false,
        validation: {
          min: 1,
          max: 10,
          message: 'Please select a stress level between 1 and 10'
        }
      }
    ]
  },
  {
    step: 9,
    title: "Privacy & Data Preferences",
    subtitle: "Your privacy is important to us",
    category: 'critical',
    isRequired: true,
    fields: [
      {
        name: 'gdprConsentStatus',
        type: 'checkbox',
        label: 'I consent to the processing of my personal data',
        subtitle: 'This allows us to provide personalized financial insights and recommendations',
        required: true
      },
      {
        name: 'dataSharingPreferences',
        type: 'select',
        label: 'How would you like us to use your data?',
        subtitle: 'We use this to improve our services and provide better recommendations',
        required: false,
        options: [
          { value: 'essential-only', label: 'Essential services only' },
          { value: 'personalized-insights', label: 'Personalized insights and recommendations' },
          { value: 'research-improvement', label: 'Research and service improvement' },
          { value: 'marketing-communications', label: 'Marketing and communications' }
        ]
      }
    ]
  },
  {
    step: 10,
    title: "Almost done!",
    subtitle: "Let's review your information",
    category: 'critical',
    isRequired: true,
    fields: [
      {
        name: 'emailVerificationStatus',
        type: 'checkbox',
        label: 'I confirm that all the information I provided is accurate',
        subtitle: 'You can update this information anytime in your profile settings',
        required: true
      }
    ]
  }
];

// Helper function to get step by number
export const getOnboardingStep = (stepNumber: number): OnboardingStep | undefined => {
  return ONBOARDING_STEPS.find(step => step.step === stepNumber);
};

// Helper function to get total steps
export const getTotalOnboardingSteps = (): number => {
  return ONBOARDING_STEPS.length;
};

// Helper function to get required steps
export const getRequiredOnboardingSteps = (): OnboardingStep[] => {
  return ONBOARDING_STEPS.filter(step => step.isRequired);
};

// Helper function to get step progress
export const getOnboardingProgress = (currentStep: number): number => {
  return Math.round((currentStep / ONBOARDING_STEPS.length) * 100);
};

// Helper function to validate step completion
export const validateStepCompletion = (step: OnboardingStep, data: Record<string, any>): boolean => {
  const requiredFields = step.fields.filter(field => field.required);
  
  return requiredFields.every(field => {
    const value = data[field.name];
    return value !== undefined && value !== null && value !== '';
  });
};

// Helper function to get next recommended step
export const getNextRecommendedStep = (completedSteps: number[]): OnboardingStep | undefined => {
  const nextStepNumber = Math.max(...completedSteps, 0) + 1;
  return getOnboardingStep(nextStepNumber);
}; 