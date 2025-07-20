export interface CompletionData {
  user_name: string;
  goals_count: number;
  profile_completion: number;
  first_checkin_date?: string;
  mobile_app_available: boolean;
  community_stats: {
    total_members: number;
    active_this_week: number;
    average_savings: number;
  };
}

export interface ReminderPreferences {
  enabled: boolean;
  frequency: 'weekly' | 'biweekly' | 'monthly';
  day: string;
  time: string;
  email: boolean;
  push: boolean;
}

export class OnboardingCompletionService {
  private static instance: OnboardingCompletionService;
  private baseUrl: string;

  private constructor() {
    this.baseUrl = '/api/onboarding/completion';
  }

  public static getInstance(): OnboardingCompletionService {
    if (!OnboardingCompletionService.instance) {
      OnboardingCompletionService.instance = new OnboardingCompletionService();
    }
    return OnboardingCompletionService.instance;
  }

  async getCompletionData(userId: string): Promise<CompletionData> {
    try {
      const response = await fetch(`${this.baseUrl}/data/${userId}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch completion data: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching completion data:', error);
      // Return default data if API fails
      return {
        user_name: 'User',
        goals_count: 3,
        profile_completion: 100,
        mobile_app_available: true,
        community_stats: {
          total_members: 15420,
          active_this_week: 8234,
          average_savings: 247
        }
      };
    }
  }

  async scheduleFirstCheckin(userId: string, preferences: ReminderPreferences): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/schedule-checkin`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          user_id: userId,
          preferences: preferences
        })
      });

      if (!response.ok) {
        throw new Error(`Failed to schedule check-in: ${response.statusText}`);
      }

      const result = await response.json();
      return result.success;
    } catch (error) {
      console.error('Error scheduling check-in:', error);
      return false;
    }
  }

  async saveEngagementPreferences(userId: string, preferences: ReminderPreferences): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/preferences`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          user_id: userId,
          preferences: preferences
        })
      });

      if (!response.ok) {
        throw new Error(`Failed to save preferences: ${response.statusText}`);
      }

      const result = await response.json();
      return result.success;
    } catch (error) {
      console.error('Error saving preferences:', error);
      return false;
    }
  }

  async markOnboardingComplete(userId: string): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/complete`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          user_id: userId,
          completed_at: new Date().toISOString()
        })
      });

      if (!response.ok) {
        throw new Error(`Failed to mark onboarding complete: ${response.statusText}`);
      }

      const result = await response.json();
      return result.success;
    } catch (error) {
      console.error('Error marking onboarding complete:', error);
      return false;
    }
  }

  async getMobileAppInfo(): Promise<{
    ios_url: string;
    android_url: string;
    qr_code_url: string;
    available: boolean;
  }> {
    try {
      const response = await fetch(`${this.baseUrl}/mobile-app`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch mobile app info: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching mobile app info:', error);
      // Return default mobile app info
      return {
        ios_url: 'https://apps.apple.com/app/mingus-financial-wellness',
        android_url: 'https://play.google.com/store/apps/details?id=com.mingus.app',
        qr_code_url: '/static/images/mobile-app-qr.png',
        available: true
      };
    }
  }

  async getCommunityStats(): Promise<{
    total_members: number;
    active_this_week: number;
    average_savings: number;
    new_members_today: number;
    top_achievement: string;
  }> {
    try {
      const response = await fetch(`${this.baseUrl}/community-stats`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch community stats: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching community stats:', error);
      // Return default community stats
      return {
        total_members: 15420,
        active_this_week: 8234,
        average_savings: 247,
        new_members_today: 156,
        top_achievement: 'Emergency fund goal reached by 73% of members this month'
      };
    }
  }

  async sendWelcomeEmail(userId: string): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/welcome-email`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          user_id: userId
        })
      });

      if (!response.ok) {
        throw new Error(`Failed to send welcome email: ${response.statusText}`);
      }

      const result = await response.json();
      return result.success;
    } catch (error) {
      console.error('Error sending welcome email:', error);
      return false;
    }
  }

  async createFirstCheckinReminder(userId: string, scheduledDate: string): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/create-reminder`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          user_id: userId,
          scheduled_date: scheduledDate,
          reminder_type: 'first_checkin'
        })
      });

      if (!response.ok) {
        throw new Error(`Failed to create reminder: ${response.statusText}`);
      }

      const result = await response.json();
      return result.success;
    } catch (error) {
      console.error('Error creating reminder:', error);
      return false;
    }
  }
} 