import { supabase } from '../lib/supabaseClient';

export interface TourState {
  id: string;
  userId: string;
  tourType: 'dashboard' | 'onboarding' | 'features';
  currentStep: number;
  completedSteps: string[];
  isCompleted: boolean;
  lastAccessed: string;
  preferences: {
    autoStart: boolean;
    showHints: boolean;
    skipIntro: boolean;
  };
}

export interface TourStep {
  id: string;
  title: string;
  description: string;
  target: string;
  position: 'top' | 'bottom' | 'left' | 'right' | 'center';
  action?: {
    type: 'click' | 'scroll' | 'highlight' | 'navigate';
    target?: string;
    text?: string;
  };
  required?: boolean;
  skipable?: boolean;
}

export class TourService {
  private static instance: TourService;
  private currentTour: TourState | null = null;

  static getInstance(): TourService {
    if (!TourService.instance) {
      TourService.instance = new TourService();
    }
    return TourService.instance;
  }

  async initializeTour(userId: string, tourType: 'dashboard' | 'onboarding' | 'features'): Promise<TourState> {
    try {
      // Check if user has existing tour state
      const { data: existingTour } = await supabase
        .from('user_tours')
        .select('*')
        .eq('user_id', userId)
        .eq('tour_type', tourType)
        .single();

      if (existingTour) {
        this.currentTour = existingTour;
        return existingTour;
      }

      // Create new tour state
      const newTour: TourState = {
        id: crypto.randomUUID(),
        userId,
        tourType,
        currentStep: 0,
        completedSteps: [],
        isCompleted: false,
        lastAccessed: new Date().toISOString(),
        preferences: {
          autoStart: true,
          showHints: true,
          skipIntro: false
        }
      };

      const { data, error } = await supabase
        .from('user_tours')
        .insert([newTour])
        .select()
        .single();

      if (error) throw error;

      this.currentTour = data;
      return data;
    } catch (error) {
      console.error('Error initializing tour:', error);
      throw error;
    }
  }

  async getCurrentTour(): Promise<TourState | null> {
    return this.currentTour;
  }

  async updateTourProgress(stepId: string, completed: boolean = true): Promise<void> {
    if (!this.currentTour) return;

    try {
      const updatedSteps = completed
        ? [...new Set([...this.currentTour.completedSteps, stepId])]
        : this.currentTour.completedSteps.filter(id => id !== stepId);

      const { error } = await supabase
        .from('user_tours')
        .update({
          completed_steps: updatedSteps,
          current_step: this.currentTour.currentStep + 1,
          last_accessed: new Date().toISOString()
        })
        .eq('id', this.currentTour.id);

      if (error) throw error;

      this.currentTour = {
        ...this.currentTour,
        completedSteps: updatedSteps,
        currentStep: this.currentTour.currentStep + 1
      };
    } catch (error) {
      console.error('Error updating tour progress:', error);
      throw error;
    }
  }

  async completeTour(): Promise<void> {
    if (!this.currentTour) return;

    try {
      const { error } = await supabase
        .from('user_tours')
        .update({
          is_completed: true,
          last_accessed: new Date().toISOString()
        })
        .eq('id', this.currentTour.id);

      if (error) throw error;

      this.currentTour = {
        ...this.currentTour,
        isCompleted: true
      };
    } catch (error) {
      console.error('Error completing tour:', error);
      throw error;
    }
  }

  async skipTour(): Promise<void> {
    if (!this.currentTour) return;

    try {
      const { error } = await supabase
        .from('user_tours')
        .update({
          is_completed: true,
          last_accessed: new Date().toISOString()
        })
        .eq('id', this.currentTour.id);

      if (error) throw error;

      this.currentTour = {
        ...this.currentTour,
        isCompleted: true
      };
    } catch (error) {
      console.error('Error skipping tour:', error);
      throw error;
    }
  }

  async updateTourPreferences(preferences: Partial<TourState['preferences']>): Promise<void> {
    if (!this.currentTour) return;

    try {
      const updatedPreferences = { ...this.currentTour.preferences, ...preferences };

      const { error } = await supabase
        .from('user_tours')
        .update({
          preferences: updatedPreferences,
          last_accessed: new Date().toISOString()
        })
        .eq('id', this.currentTour.id);

      if (error) throw error;

      this.currentTour = {
        ...this.currentTour,
        preferences: updatedPreferences
      };
    } catch (error) {
      console.error('Error updating tour preferences:', error);
      throw error;
    }
  }

  async shouldShowTour(userId: string, tourType: string): Promise<boolean> {
    try {
      const { data: tour } = await supabase
        .from('user_tours')
        .select('is_completed, preferences')
        .eq('user_id', userId)
        .eq('tour_type', tourType)
        .single();

      if (!tour) return true; // New user, show tour
      if (tour.is_completed) return false; // Already completed
      
      return tour.preferences?.autoStart ?? true;
    } catch (error) {
      console.error('Error checking tour status:', error);
      return true; // Default to showing tour on error
    }
  }

  getDashboardTourSteps(): TourStep[] {
    return [
      {
        id: 'welcome',
        title: 'Welcome to Your Dashboard!',
        description: 'This is your financial wellness command center. Let\'s explore the key features that will help you achieve your goals.',
        target: '.dashboard-container',
        position: 'center',
        required: true,
        skipable: false
      },
      {
        id: 'job-security',
        title: 'Job Security Score',
        description: 'Your career stability score helps you understand your professional situation and plan for the future. Higher scores mean more stability.',
        target: '#job-security-card',
        position: 'bottom',
        action: {
          type: 'highlight',
          text: 'Click to see detailed insights'
        },
        required: false,
        skipable: true
      },
      {
        id: 'emergency-fund',
        title: 'Emergency Fund Tracker',
        description: 'Track your emergency savings progress. This helps you build financial security for unexpected expenses.',
        target: '#emergency-fund-card',
        position: 'bottom',
        action: {
          type: 'highlight',
          text: 'View your savings progress'
        },
        required: false,
        skipable: true
      },
      {
        id: 'cash-flow',
        title: 'Cash Flow Insights',
        description: 'Monitor your income and expenses to understand your spending patterns and identify opportunities to save.',
        target: '#cash-flow-card',
        position: 'top',
        action: {
          type: 'highlight',
          text: 'Analyze your spending'
        },
        required: false,
        skipable: true
      },
      {
        id: 'community',
        title: 'Community Features',
        description: 'Connect with others on similar financial journeys. Share experiences and get support from the community.',
        target: '#community-card',
        position: 'left',
        action: {
          type: 'highlight',
          text: 'Join community discussions'
        },
        required: false,
        skipable: true
      },
      {
        id: 'notifications',
        title: 'Stay Updated',
        description: 'Set up notifications to get personalized insights, goal reminders, and important updates.',
        target: '.notification-settings',
        position: 'right',
        action: {
          type: 'click',
          target: '.notification-settings',
          text: 'Set up notifications'
        },
        required: false,
        skipable: true
      },
      {
        id: 'accounts',
        title: 'Connect Your Accounts',
        description: 'Link your bank accounts for automatic tracking and more accurate insights.',
        target: '.account-connection',
        position: 'left',
        action: {
          type: 'click',
          target: '.account-connection',
          text: 'Connect accounts'
        },
        required: false,
        skipable: true
      },
      {
        id: 'complete',
        title: 'You\'re All Set!',
        description: 'You now know your way around the dashboard. Start exploring and take control of your financial wellness journey!',
        target: '.dashboard-container',
        position: 'center',
        required: true,
        skipable: false
      }
    ];
  }

  async getPersonalizedTourSteps(userId: string): Promise<TourStep[]> {
    // This would typically fetch user data and customize tour steps
    // For now, return the standard dashboard tour steps
    return this.getDashboardTourSteps();
  }

  async trackTourEvent(event: string, stepId?: string): Promise<void> {
    if (!this.currentTour) return;

    try {
      await supabase
        .from('tour_events')
        .insert([{
          tour_id: this.currentTour.id,
          user_id: this.currentTour.userId,
          event_type: event,
          step_id: stepId,
          timestamp: new Date().toISOString()
        }]);
    } catch (error) {
      console.error('Error tracking tour event:', error);
    }
  }
} 