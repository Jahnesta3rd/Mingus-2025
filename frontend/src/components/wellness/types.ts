/** Payload for POST /api/wellness/checkin */
export interface CheckinPayload {
  exercise_days: number;
  exercise_intensity: 'light' | 'moderate' | 'intense' | null;
  sleep_quality: number;
  meditation_minutes: number;
  stress_level: number;
  overall_mood: number;
  relationship_satisfaction: number;
  social_interactions: number;
  financial_stress: number;
  spending_control: number;
  groceries_estimate: number | null;
  dining_estimate: number | null;
  entertainment_estimate: number | null;
  shopping_estimate: number | null;
  transport_estimate: number | null;
  utilities_estimate: number | null;
  other_estimate: number | null;
  had_impulse_purchases: boolean;
  impulse_spending: number | null;
  had_stress_purchases: boolean;
  stress_spending: number | null;
  celebration_spending: number | null;
  biggest_unnecessary_purchase: number | null;
  biggest_unnecessary_category: string | null;
  wins: string | null;
  challenges: string | null;
  completion_time_seconds: number;
}

/** Response from POST /api/wellness/checkin */
export interface CheckinResponse {
  checkin_id: string;
  week_ending_date: string;
  wellness_scores: {
    physical_score: number;
    mental_score: number;
    relational_score: number;
    financial_feeling_score: number;
    overall_wellness_score: number;
    physical_change?: number;
    mental_change?: number;
    relational_change?: number;
    overall_change?: number;
  };
  streak_info: {
    current_streak: number;
    longest_streak: number;
    last_checkin_date: string | null;
    total_checkins: number;
  };
  insights: Array<{
    type: string;
    title: string;
    message: string;
    suggestion?: string;
    confidence?: string;
  }>;
}

/** Baselines from GET /api/wellness/spending/baselines */
export interface SpendingBaselines {
  avg_groceries: number | null;
  avg_dining: number | null;
  avg_entertainment: number | null;
  avg_shopping: number | null;
  avg_transport: number | null;
  avg_total: number | null;
  avg_impulse: number | null;
  weeks_of_data: number;
}
