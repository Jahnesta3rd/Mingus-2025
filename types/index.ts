// types/index.ts
// Main user profile types
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
  FormSubmission
} from './user';

// Meme splash page types
export type {
  Meme,
  MemeAnalytics,
  MemePreferences,
  MemeSplashPageProps,
  MemeApiResponse,
  MemeAnalyticsResponse,
  MemePreferencesResponse,
  MemeError,
  MemeLoadingState,
  MemeInteraction,
  MemeAccessibilityProps,
  MemeAnimationProps,
  MemeThemeProps
} from './meme';

// Specific enum types
export type {
  IncomeFrequency,
  CreditScoreRange,
  AgeRange,
  MaritalStatus,
  YearsOfExperience,
  RiskToleranceLevel,
  FinancialKnowledgeLevel,
  HealthCheckinFrequency
} from './user';

// Constants and utilities
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
} from './user-constants';

// API types
export type {
  ApiResponse,
  ApiError,
  ValidationError,
  GetUserProfileRequest,
  UpdateUserProfileRequest,
  CreateUserProfileRequest,
  DeleteUserProfileRequest,
  GetUserProfileResponse,
  UpdateUserProfileResponse,
  CreateUserProfileResponse,
  DeleteUserProfileResponse,
  BulkUpdateUserProfilesRequest,
  BulkUpdateUserProfilesResponse,
  SearchUserProfilesRequest,
  UserProfileFilters,
  SearchUserProfilesResponse,
  UserProfileAnalyticsRequest,
  UserProfileAnalyticsResponse,
  OnboardingProgressRequest,
  OnboardingProgressResponse,
  GDPRConsentRequest,
  GDPRConsentResponse,
  DataExportRequest,
  DataExportResponse,
  UpdateNotificationPreferencesRequest,
  UpdateNotificationPreferencesResponse,
  WellnessCheckinRequest,
  WellnessCheckinResponse
} from './user-api';

// API constants
export {
  USER_PROFILE_ERROR_CODES,
  USER_PROFILE_ENDPOINTS
} from './user-api';

// Re-export everything for convenience
export * from './user';
export * from './user-constants';
export * from './user-api'; 