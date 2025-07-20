// Validation Types for Ratchet Money Questionnaire

export interface ValidationRule {
  required?: boolean
  minLength?: number
  maxLength?: number
  pattern?: RegExp
  custom?: (value: any) => boolean
  message?: string
}

export interface ValidationState {
  isValid: boolean
  errorMessage: string
  isDirty: boolean
  isTouched: boolean
}

export interface FormValidationState {
  [fieldName: string]: ValidationState
}

export interface ValidationConfig {
  [fieldName: string]: ValidationRule[]
}

export interface FormData {
  email: string
  firstName: string
  lastName: string
  phoneNumber: string
  age: string
  income: string
  occupation: string
  relationshipStatus: string
  financialGoals: string[]
  stressLevel: string
  spendingHabits: string[]
  emergencyFund: string
  debtAmount: string
  investmentExperience: string
  preferredContactMethod: 'email' | 'phone' | 'both'
  betaInterest: 'very' | 'somewhat' | 'not'
  marketingConsent: boolean
}

export interface SavedProgress {
  formData: Partial<FormData>
  currentStep: number
  timestamp: number
  sessionId: string
}

export interface ValidationError {
  field: string
  message: string
  type: 'required' | 'format' | 'range' | 'custom'
}

export interface SubmissionState {
  isSubmitting: boolean
  isSubmitted: boolean
  error: string | null
  successMessage: string | null
}

// Validation Messages
export const VALIDATION_MESSAGES = {
  required: 'This field is required to continue',
  email: 'Please enter a valid email address',
  phone: 'Please enter a valid phone number',
  age: 'Please enter an age between 25 and 35',
  income: 'Please select your income range',
  minLength: (min: number) => `Please enter at least ${min} characters`,
  maxLength: (max: number) => `Please enter no more than ${max} characters`,
  pattern: 'Please check the format and try again',
  custom: 'Please check this field and try again'
} as const

// Encouraging Error Messages
export const ENCOURAGING_MESSAGES = {
  email: {
    empty: 'We\'d love to send you your personalized results!',
    invalid: 'Almost there! Please check your email format',
    duplicate: 'Great! You\'re already in our system. Let\'s continue!'
  },
  phone: {
    empty: 'Your phone number helps us provide better support',
    invalid: 'Let\'s make sure we can reach you when needed'
  },
  age: {
    empty: 'Your age helps us personalize your experience',
    tooYoung: 'We\'re excited to work with you! Please note our target age range',
    tooOld: 'Your wisdom is valuable! We\'re currently focused on ages 25-35'
  },
  income: {
    empty: 'This helps us provide the most relevant resources for you'
  },
  general: {
    required: 'We need this to create your personalized plan',
    network: 'Connection issue - let\'s try again!',
    success: 'Excellent! Your information has been saved successfully'
  }
} as const

// Accessibility Labels
export const ACCESSIBILITY_LABELS = {
  email: 'Email address for receiving your personalized results',
  firstName: 'First name for personalizing your experience',
  lastName: 'Last name for account setup',
  phoneNumber: 'Phone number for support and updates',
  age: 'Age for demographic targeting (25-35 preferred)',
  income: 'Income range for personalized recommendations',
  occupation: 'Occupation for career-specific advice',
  relationshipStatus: 'Relationship status for targeted strategies',
  financialGoals: 'Financial goals for personalized planning',
  stressLevel: 'Current financial stress level',
  spendingHabits: 'Spending habits for behavioral analysis',
  emergencyFund: 'Emergency fund status',
  debtAmount: 'Current debt amount',
  investmentExperience: 'Investment experience level',
  preferredContactMethod: 'Preferred method of contact',
  betaInterest: 'Interest level in beta access',
  marketingConsent: 'Consent for marketing communications'
} as const 