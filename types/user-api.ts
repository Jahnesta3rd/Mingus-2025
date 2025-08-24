// types/user-api.ts
import type { UserProfile, UserProfileUpdate, CreateUserProfile } from './user';

// API Response wrapper
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: ApiError;
  message?: string;
  timestamp: string;
  requestId?: string;
}

// API Error structure
export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, any>;
  field?: string;
  validationErrors?: ValidationError[];
}

// Validation error for specific fields
export interface ValidationError {
  field: string;
  message: string;
  code: string;
  value?: any;
}

// User Profile API Requests
export interface GetUserProfileRequest {
  userId: string;
  includeSensitiveData?: boolean;
}

export interface UpdateUserProfileRequest {
  userId: string;
  updates: UserProfileUpdate;
  validateOnly?: boolean;
}

export interface CreateUserProfileRequest {
  profile: CreateUserProfile;
  sendWelcomeEmail?: boolean;
  startOnboarding?: boolean;
}

export interface DeleteUserProfileRequest {
  userId: string;
  reason?: string;
  anonymizeData?: boolean;
}

// User Profile API Responses
export interface GetUserProfileResponse {
  profile: UserProfile;
  lastUpdated: string;
  profileCompletion: {
    percentage: number;
    missingFields: string[];
    nextRecommendedFields: string[];
  };
}

export interface UpdateUserProfileResponse {
  profile: UserProfile;
  updatedFields: string[];
  profileCompletion: {
    percentage: number;
    improved: boolean;
    previousPercentage: number;
  };
  validationWarnings?: ValidationError[];
}

export interface CreateUserProfileResponse {
  profile: UserProfile;
  onboardingUrl?: string;
  welcomeEmailSent: boolean;
}

export interface DeleteUserProfileResponse {
  success: boolean;
  deletionDate: string;
  dataAnonymized: boolean;
}

// Bulk operations
export interface BulkUpdateUserProfilesRequest {
  updates: Array<{
    userId: string;
    updates: UserProfileUpdate;
  }>;
  validateOnly?: boolean;
}

export interface BulkUpdateUserProfilesResponse {
  results: Array<{
    userId: string;
    success: boolean;
    error?: ApiError;
    updatedFields?: string[];
  }>;
  summary: {
    total: number;
    successful: number;
    failed: number;
  };
}

// Search and filtering
export interface SearchUserProfilesRequest {
  query?: string;
  filters?: UserProfileFilters;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
  page?: number;
  limit?: number;
  includeSensitiveData?: boolean;
}

export interface UserProfileFilters {
  ageRange?: string[];
  maritalStatus?: string[];
  employmentStatus?: string[];
  incomeRange?: {
    min?: number;
    max?: number;
  };
  creditScoreRange?: string[];
  riskToleranceLevel?: string[];
  profileCompletionRange?: {
    min?: number;
    max?: number;
  };
  onboardingStep?: number[];
  gdprConsentStatus?: boolean;
  createdDateRange?: {
    start?: string;
    end?: string;
  };
  lastActiveRange?: {
    start?: string;
    end?: string;
  };
}

export interface SearchUserProfilesResponse {
  profiles: UserProfile[];
  total: number;
  page: number;
  limit: number;
  totalPages: number;
  hasNext: boolean;
  hasPrevious: boolean;
}

// Analytics and reporting
export interface UserProfileAnalyticsRequest {
  dateRange?: {
    start: string;
    end: string;
  };
  groupBy?: 'ageRange' | 'maritalStatus' | 'employmentStatus' | 'riskToleranceLevel' | 'profileCompletion';
  filters?: UserProfileFilters;
}

export interface UserProfileAnalyticsResponse {
  summary: {
    totalUsers: number;
    activeUsers: number;
    averageProfileCompletion: number;
    averageOnboardingStep: number;
  };
  demographics: {
    ageDistribution: Record<string, number>;
    maritalStatusDistribution: Record<string, number>;
    employmentStatusDistribution: Record<string, number>;
  };
  financial: {
    averageIncome: number;
    incomeDistribution: Record<string, number>;
    creditScoreDistribution: Record<string, number>;
    riskToleranceDistribution: Record<string, number>;
  };
  engagement: {
    profileCompletionDistribution: Record<string, number>;
    onboardingStepDistribution: Record<string, number>;
    gdprConsentRate: number;
  };
  trends: {
    newUsersPerDay: Array<{ date: string; count: number }>;
    profileCompletionsPerDay: Array<{ date: string; count: number }>;
    onboardingProgressPerDay: Array<{ date: string; averageStep: number }>;
  };
}

// Onboarding specific types
export interface OnboardingProgressRequest {
  userId: string;
  step: number;
  data: Record<string, any>;
}

export interface OnboardingProgressResponse {
  currentStep: number;
  completedSteps: number[];
  nextStep?: {
    step: number;
    title: string;
    fields: any[];
  };
  profileCompletion: {
    percentage: number;
    missingFields: string[];
  };
  canSkip: boolean;
  isComplete: boolean;
}

// GDPR and privacy
export interface GDPRConsentRequest {
  userId: string;
  consentStatus: boolean;
  consentVersion: string;
  dataSharingPreferences: Record<string, boolean>;
}

export interface GDPRConsentResponse {
  success: boolean;
  consentDate: string;
  dataSharingPreferences: Record<string, boolean>;
  nextReviewDate?: string;
}

export interface DataExportRequest {
  userId: string;
  format: 'json' | 'csv' | 'pdf';
  includeSensitiveData?: boolean;
}

export interface DataExportResponse {
  exportId: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  downloadUrl?: string;
  expiresAt: string;
  recordCount: number;
}

// Notification preferences
export interface UpdateNotificationPreferencesRequest {
  userId: string;
  preferences: Record<string, boolean>;
  frequency?: 'immediate' | 'daily' | 'weekly' | 'monthly';
  quietHours?: {
    enabled: boolean;
    startTime?: string;
    endTime?: string;
  };
}

export interface UpdateNotificationPreferencesResponse {
  success: boolean;
  updatedPreferences: Record<string, boolean>;
  frequency: string;
  quietHours?: {
    enabled: boolean;
    startTime?: string;
    endTime?: string;
  };
}

// Health and wellness
export interface WellnessCheckinRequest {
  userId: string;
  stressLevel: number;
  mood: number;
  energy: number;
  notes?: string;
}

export interface WellnessCheckinResponse {
  success: boolean;
  checkinDate: string;
  trends: {
    stressTrend: 'improving' | 'stable' | 'worsening';
    moodTrend: 'improving' | 'stable' | 'worsening';
    energyTrend: 'improving' | 'stable' | 'worsening';
  };
  recommendations: string[];
}

// Error codes
export const USER_PROFILE_ERROR_CODES = {
  USER_NOT_FOUND: 'USER_NOT_FOUND',
  INVALID_PROFILE_DATA: 'INVALID_PROFILE_DATA',
  DUPLICATE_EMAIL: 'DUPLICATE_EMAIL',
  INVALID_PHONE_NUMBER: 'INVALID_PHONE_NUMBER',
  INVALID_ZIP_CODE: 'INVALID_ZIP_CODE',
  PROFILE_UPDATE_FAILED: 'PROFILE_UPDATE_FAILED',
  GDPR_CONSENT_REQUIRED: 'GDPR_CONSENT_REQUIRED',
  DATA_EXPORT_FAILED: 'DATA_EXPORT_FAILED',
  ONBOARDING_STEP_INVALID: 'ONBOARDING_STEP_INVALID',
  WELLNESS_CHECKIN_FAILED: 'WELLNESS_CHECKIN_FAILED',
  NOTIFICATION_PREFERENCES_INVALID: 'NOTIFICATION_PREFERENCES_INVALID',
  BULK_UPDATE_FAILED: 'BULK_UPDATE_FAILED',
  SEARCH_FAILED: 'SEARCH_FAILED',
  ANALYTICS_FAILED: 'ANALYTICS_FAILED'
} as const;

// API endpoints
export const USER_PROFILE_ENDPOINTS = {
  GET_PROFILE: '/api/users/:userId/profile',
  UPDATE_PROFILE: '/api/users/:userId/profile',
  CREATE_PROFILE: '/api/users/profile',
  DELETE_PROFILE: '/api/users/:userId/profile',
  BULK_UPDATE: '/api/users/profiles/bulk-update',
  SEARCH_PROFILES: '/api/users/profiles/search',
  GET_ANALYTICS: '/api/users/profiles/analytics',
  ONBOARDING_PROGRESS: '/api/users/:userId/onboarding',
  GDPR_CONSENT: '/api/users/:userId/gdpr-consent',
  DATA_EXPORT: '/api/users/:userId/data-export',
  NOTIFICATION_PREFERENCES: '/api/users/:userId/notifications',
  WELLNESS_CHECKIN: '/api/users/:userId/wellness-checkin'
} as const;

// Export all types
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
}; 