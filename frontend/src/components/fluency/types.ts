export type UserTier = 'budget' | 'mid_tier' | 'professional';

export type FluencyDomain =
  | 'mood'
  | 'body'
  | 'housing'
  | 'vehicle'
  | 'spirit'
  | 'relationships';

export interface WaterfallContext {
  fixed_bills_pressure: 'elevated' | 'normal';
  discretionary_risk: 'high' | 'watch' | 'normal';
  surplus_trajectory: 'positive' | 'watch' | 'at_risk';
  vehicle_decision: 'keeping' | 'unsure' | 'selling' | 'keeping_years' | 'considering_replace' | 'actively_shopping' | null;
  lease_renewal_imminent: boolean;
  down_payment_status: 'on_track' | 'behind' | 'not_started' | 'not_saving' | 'started' | 'owner' | null;
  body_work_impact: boolean | null;
  body_ongoing_health_cost: boolean | null;
  financially_anxious: boolean | null;
  relationship_direction_signal: 'positive' | 'neutral' | 'watch' | null;
  stress_spend_pattern_detected: boolean;
  user_tier: UserTier;
  data_completeness: number;
  last_updated: string;
}

export interface FluencyCueEntry {
  id: string;
  triggerField: keyof WaterfallContext;
  triggerValue: string | boolean;
  tier: UserTier | 'all';
  domain: FluencyDomain;
  headline: string;
  body: string | null;
  expandable: boolean;
  actionLabel: string | null;
  actionRoute: string | null;
}
