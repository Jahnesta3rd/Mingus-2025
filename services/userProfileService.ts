// services/userProfileService.ts
import { 
  ApiResponse,
  GetUserProfileResponse,
  UpdateUserProfileResponse,
  SearchUserProfilesRequest,
  SearchUserProfilesResponse,
  UserProfileAnalyticsRequest,
  UserProfileAnalyticsResponse,
  OnboardingProgressRequest,
  OnboardingProgressResponse,
  GDPRConsentRequest,
  GDPRConsentResponse,
  UpdateNotificationPreferencesRequest,
  UpdateNotificationPreferencesResponse,
  WellnessCheckinRequest,
  WellnessCheckinResponse
} from '../types/user-api';
import { 
  UserProfile, 
  UserProfileUpdate, 
  CreateUserProfile
} from '../types/user';

export class UserProfileService {
  private baseUrl: string;
  private apiKey?: string;

  constructor(baseUrl: string = '/api', apiKey?: string) {
    this.baseUrl = baseUrl;
    this.apiKey = apiKey;
  }

  private async makeRequest<T>(
    endpoint: string, 
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (this.apiKey) {
      headers['Authorization'] = `Bearer ${this.apiKey}`;
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || `HTTP ${response.status}`);
      }

      return data;
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  /**
   * Get user profile
   */
  async getUserProfile(userId: string, includeSensitiveData: boolean = false): Promise<GetUserProfileResponse> {
    const params = new URLSearchParams();
    if (includeSensitiveData) {
      params.append('includeSensitiveData', 'true');
    }

    const response = await this.makeRequest<GetUserProfileResponse>(
      `/users/${userId}/profile?${params.toString()}`
    );

    return response.data!;
  }

  /**
   * Update user profile
   */
  async updateUserProfile(
    userId: string, 
    updates: UserProfileUpdate, 
    validateOnly: boolean = false
  ): Promise<UpdateUserProfileResponse> {
    const response = await this.makeRequest<UpdateUserProfileResponse>(
      `/users/${userId}/profile`,
      {
        method: 'PATCH',
        body: JSON.stringify({ updates, validateOnly }),
      }
    );

    return response.data!;
  }

  /**
   * Create new user profile
   */
  async createUserProfile(
    profile: CreateUserProfile, 
    sendWelcomeEmail: boolean = true, 
    startOnboarding: boolean = true
  ): Promise<UserProfile> {
    const response = await this.makeRequest<UserProfile>(
      '/users/profile',
      {
        method: 'POST',
        body: JSON.stringify({ 
          profile, 
          sendWelcomeEmail, 
          startOnboarding 
        }),
      }
    );

    return response.data!;
  }

  /**
   * Delete user profile
   */
  async deleteUserProfile(
    userId: string, 
    reason?: string, 
    anonymizeData: boolean = true
  ): Promise<boolean> {
    const response = await this.makeRequest<{ success: boolean }>(
      `/users/${userId}/profile`,
      {
        method: 'DELETE',
        body: JSON.stringify({ reason, anonymizeData }),
      }
    );

    return response.data!.success;
  }

  /**
   * Search user profiles
   */
  async searchUserProfiles(request: SearchUserProfilesRequest): Promise<SearchUserProfilesResponse> {
    const response = await this.makeRequest<SearchUserProfilesResponse>(
      '/users/profiles/search',
      {
        method: 'POST',
        body: JSON.stringify(request),
      }
    );

    return response.data!;
  }

  /**
   * Get user profile analytics
   */
  async getUserProfileAnalytics(request: UserProfileAnalyticsRequest): Promise<UserProfileAnalyticsResponse> {
    const response = await this.makeRequest<UserProfileAnalyticsResponse>(
      '/users/profiles/analytics',
      {
        method: 'POST',
        body: JSON.stringify(request),
      }
    );

    return response.data!;
  }

  /**
   * Update onboarding progress
   */
  async updateOnboardingProgress(request: OnboardingProgressRequest): Promise<OnboardingProgressResponse> {
    const response = await this.makeRequest<OnboardingProgressResponse>(
      `/users/${request.userId}/onboarding`,
      {
        method: 'POST',
        body: JSON.stringify(request),
      }
    );

    return response.data!;
  }

  /**
   * Update GDPR consent
   */
  async updateGDPRConsent(request: GDPRConsentRequest): Promise<GDPRConsentResponse> {
    const response = await this.makeRequest<GDPRConsentResponse>(
      `/users/${request.userId}/gdpr-consent`,
      {
        method: 'POST',
        body: JSON.stringify(request),
      }
    );

    return response.data!;
  }

  /**
   * Update notification preferences
   */
  async updateNotificationPreferences(
    request: UpdateNotificationPreferencesRequest
  ): Promise<UpdateNotificationPreferencesResponse> {
    const response = await this.makeRequest<UpdateNotificationPreferencesResponse>(
      `/users/${request.userId}/notifications`,
      {
        method: 'POST',
        body: JSON.stringify(request),
      }
    );

    return response.data!;
  }

  /**
   * Submit wellness check-in
   */
  async submitWellnessCheckin(request: WellnessCheckinRequest): Promise<WellnessCheckinResponse> {
    const response = await this.makeRequest<WellnessCheckinResponse>(
      `/users/${request.userId}/wellness-checkin`,
      {
        method: 'POST',
        body: JSON.stringify(request),
      }
    );

    return response.data!;
  }

  /**
   * Bulk update user profiles
   */
  async bulkUpdateUserProfiles(
    updates: Array<{ userId: string; updates: UserProfileUpdate }>,
    validateOnly: boolean = false
  ): Promise<{ results: Array<{ userId: string; success: boolean; error?: any }> }> {
    const response = await this.makeRequest<{ results: Array<{ userId: string; success: boolean; error?: any }> }>(
      '/users/profiles/bulk-update',
      {
        method: 'POST',
        body: JSON.stringify({ updates, validateOnly }),
      }
    );

    return response.data!;
  }

  /**
   * Export user data
   */
  async exportUserData(
    userId: string, 
    format: 'json' | 'csv' | 'pdf' = 'json',
    includeSensitiveData: boolean = false
  ): Promise<{ exportId: string; downloadUrl?: string }> {
    const response = await this.makeRequest<{ exportId: string; downloadUrl?: string }>(
      `/users/${userId}/data-export`,
      {
        method: 'POST',
        body: JSON.stringify({ format, includeSensitiveData }),
      }
    );

    return response.data!;
  }

  /**
   * Get profile completion analytics for a user
   */
  async getProfileCompletionAnalytics(userId: string): Promise<{
    completionPercentage: number;
    missingFields: string[];
    nextRecommendedFields: string[];
    categoryCompletions: Record<string, number>;
  }> {
    const response = await this.makeRequest<{
      completionPercentage: number;
      missingFields: string[];
      nextRecommendedFields: string[];
      categoryCompletions: Record<string, number>;
    }>(`/users/${userId}/profile/completion-analytics`);

    return response.data!;
  }

  /**
   * Validate user profile data
   */
  async validateUserProfileData(data: Partial<UserProfile>): Promise<{
    isValid: boolean;
    errors: Array<{ field: string; message: string; code: string }>;
    warnings: Array<{ field: string; message: string; code: string }>;
  }> {
    const response = await this.makeRequest<{
      isValid: boolean;
      errors: Array<{ field: string; message: string; code: string }>;
      warnings: Array<{ field: string; message: string; code: string }>;
    }>('/users/profile/validate', {
      method: 'POST',
      body: JSON.stringify(data),
    });

    return response.data!;
  }

  /**
   * Get onboarding recommendations
   */
  async getOnboardingRecommendations(userId: string): Promise<{
    recommendedSteps: number[];
    estimatedTimeToComplete: number;
    priorityFields: string[];
  }> {
    const response = await this.makeRequest<{
      recommendedSteps: number[];
      estimatedTimeToComplete: number;
      priorityFields: string[];
    }>(`/users/${userId}/onboarding/recommendations`);

    return response.data!;
  }

  /**
   * Save onboarding progress
   */
  async saveOnboardingProgress(
    userId: string,
    step: number,
    data: Record<string, any>
  ): Promise<{
    success: boolean;
    nextStep?: number;
    completionPercentage: number;
  }> {
    const response = await this.makeRequest<{
      success: boolean;
      nextStep?: number;
      completionPercentage: number;
    }>(`/users/${userId}/onboarding/progress`, {
      method: 'POST',
      body: JSON.stringify({ step, data }),
    });

    return response.data!;
  }

  /**
   * Get user activity summary
   */
  async getUserActivitySummary(userId: string): Promise<{
    lastLogin: string;
    loginCount: number;
    featuresUsed: string[];
    engagementScore: number;
    timeSpent: Array<{ feature: string; duration: number; date: string }>;
  }> {
    const response = await this.makeRequest<{
      lastLogin: string;
      loginCount: number;
      featuresUsed: string[];
      engagementScore: number;
      timeSpent: Array<{ feature: string; duration: number; date: string }>;
    }>(`/users/${userId}/activity-summary`);

    return response.data!;
  }

  /**
   * Update user preferences
   */
  async updateUserPreferences(
    userId: string,
    preferences: Record<string, any>
  ): Promise<{ success: boolean; updatedPreferences: Record<string, any> }> {
    const response = await this.makeRequest<{
      success: boolean;
      updatedPreferences: Record<string, any>;
    }>(`/users/${userId}/preferences`, {
      method: 'PATCH',
      body: JSON.stringify(preferences),
    });

    return response.data!;
  }

  /**
   * Get financial health assessment
   */
  async getFinancialHealthAssessment(userId: string): Promise<{
    score: number;
    category: string;
    factors: Record<string, number>;
    recommendations: string[];
    riskFactors: string[];
  }> {
    const response = await this.makeRequest<{
      score: number;
      category: string;
      factors: Record<string, number>;
      recommendations: string[];
      riskFactors: string[];
    }>(`/users/${userId}/financial-health-assessment`);

    return response.data!;
  }
}

// Export singleton instance
export const userProfileService = new UserProfileService(); 