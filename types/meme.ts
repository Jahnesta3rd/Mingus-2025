// types/meme.ts
// TypeScript types for the meme splash page feature

export interface Meme {
  id: string;
  image_url: string;
  caption: string;
  category: string;
  alt_text: string;
  tags?: string[];
  source_attribution?: string;
  created_at?: string;
  updated_at?: string;
}

export interface MemeAnalytics {
  meme_id: string;
  interaction_type: 'viewed' | 'skipped' | 'continued' | 'liked' | 'shared' | 'reported';
  time_spent_seconds?: number;
  source_page?: string;
  device_type?: string;
  user_agent?: string;
  ip_address?: string;
  session_id?: string;
}

export interface MemePreferences {
  daily_memes_enabled: boolean;
  preferred_categories?: string[];
  opt_out_reason?: string;
  opt_out_source?: string;
  last_interaction_date?: string;
  total_interactions?: number;
}

export interface MemeSplashPageProps {
  onOptOut?: () => void;
  onContinue?: () => void;
  onSkip?: () => void;
  autoAdvanceSeconds?: number;
  showOptOutModal?: boolean;
  customApiEndpoints?: {
    fetchMeme?: string;
    trackAnalytics?: string;
    updatePreferences?: string;
  };
}

export interface MemeApiResponse {
  success: boolean;
  meme?: Meme;
  message?: string;
  error?: string;
  timestamp?: string;
  next_available?: string;
}

export interface MemeAnalyticsResponse {
  success: boolean;
  message?: string;
  error?: string;
  interaction_id?: string;
}

export interface MemePreferencesResponse {
  success: boolean;
  preferences?: MemePreferences;
  message?: string;
  error?: string;
}

// Error types
export interface MemeError {
  type: 'fetch_error' | 'network_error' | 'api_error' | 'validation_error';
  message: string;
  status?: number;
  details?: any;
}

// Loading states
export interface MemeLoadingState {
  isLoading: boolean;
  isImageLoading: boolean;
  isOptOutLoading: boolean;
  hasImageError: boolean;
}

// User interaction tracking
export interface MemeInteraction {
  meme_id: string;
  interaction_type: MemeAnalytics['interaction_type'];
  timestamp: number;
  time_spent_seconds: number;
  user_agent?: string;
  screen_size?: {
    width: number;
    height: number;
  };
  device_type?: 'mobile' | 'tablet' | 'desktop';
}

// Accessibility props
export interface MemeAccessibilityProps {
  'aria-label'?: string;
  'aria-describedby'?: string;
  'aria-live'?: 'polite' | 'assertive' | 'off';
  role?: string;
  tabIndex?: number;
}

// Animation and transition props
export interface MemeAnimationProps {
  animationDuration?: number;
  animationDelay?: number;
  animationEasing?: string;
  enableHoverEffects?: boolean;
  enableFocusEffects?: boolean;
}

// Theme and styling props
export interface MemeThemeProps {
  primaryColor?: string;
  secondaryColor?: string;
  backgroundColor?: string;
  textColor?: string;
  borderRadius?: string;
  shadowIntensity?: 'none' | 'light' | 'medium' | 'heavy';
}

// Export all types
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
};
