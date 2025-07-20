export interface StepStatus {
  completed: boolean;
  completed_at?: string;
}

export interface OnboardingStep {
  id: string;
  name: string;
  title: string;
  description: string;
  route: string;
  stepNumber: number;
  required: boolean;
  estimatedTime: number;
  weight: number;
  completionCriteria: string[];
  dependencies?: string[];
  displayName?: string;
  icon?: string;
  isRequired?: boolean;
  canSkip?: boolean;
  completed?: boolean;
  completedAt?: string;
  isCurrent?: boolean;
}

export interface OnboardingProgress {
  userId: string;
  currentStep: string;
  completedSteps: string[];
  progressPercentage: number;
  isCompleted: boolean;
  stepCompletionData: Record<string, any>;
  estimatedTimeRemaining: number;
  createdAt: string;
  updatedAt: string;
  // Legacy support
  totalSteps?: number;
  completedStepsCount?: number;
  stepStatus?: Record<string, StepStatus>;
}

export interface StepCompletionResult {
  success: boolean;
  stepCompleted: string;
  newProgressPercentage: number;
  nextStep: string | null;
  isOnboardingComplete: boolean;
  error?: string;
}

export interface NavigationContext {
  currentStep: string;
  nextStep: string | null;
  canProceed: boolean;
  canAccess: boolean;
  redirectTo?: string;
}

export interface OnboardingChoice {
  choice: 'deep' | 'brief';
  timestamp: string;
}

export interface ProfileData {
  monthly_income: string;
  income_frequency: string;
  primary_income_source: string;
  age_range: string;
  location_state: string;
  location_city: string;
  household_size: string;
  employment_status: string;
  current_savings: string;
  current_debt: string;
  credit_score_range: string;
}

export interface PreferencesData {
  risk_tolerance: string;
  investment_experience: string;
  financial_goals: string[];
  preferred_communication: string;
  notification_preferences: string[];
}

export interface ExpenseData {
  housing: string;
  transportation: string;
  food: string;
  utilities: string;
  healthcare: string;
  entertainment: string;
  shopping: string;
  debt_payments: string;
  savings: string;
  other: string;
}

export interface OnboardingResponse {
  success: boolean;
  message?: string;
  error?: string;
  data?: any;
} 