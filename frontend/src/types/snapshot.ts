// ─── Vibe Check ──────────────────────────────────────────────
export interface VibeCheckData {
  score: number;
  verdict: string;
  wellness_score: number;
  financial_score: number;
  emotional_score: number;
  headline_insight: string | null;
}

// ─── Faith Card ───────────────────────────────────────────────
export interface FaithCardData {
  verse_text: string;
  verse_reference: string;
  bridge_sentence: string;
  is_favorited: boolean;
  balance_status: string;
  goal: string;
}

// ─── Cash Now ────────────────────────────────────────────────
export interface CashNowData {
  todays_balance: number;
  balance_30_day: number;
  net_change_30: number;
  balance_status: "healthy" | "warning" | "danger";
  worst_status_30: "healthy" | "warning" | "danger";
}

// ─── Spending ────────────────────────────────────────────────
export interface SpendingCategory {
  name: string;
  amount: number;
  pct_of_income: number;
}

export interface SpendingData {
  income_monthly: number;
  top_categories: SpendingCategory[];
}

// ─── Roster ──────────────────────────────────────────────────
export interface RosterPerson {
  nickname: string;
  emoji: string;
  estimated_annual_cost: number;
  trend: "rising" | "falling" | "stable";
}

export interface RosterData {
  total_annual_cost: number;
  total_monthly_cost: number;
  relationship_cost_delta: number;
  people: RosterPerson[];
  has_financial_drag: boolean;
}

// ─── Milestones ───────────────────────────────────────────────
export interface MilestoneEvent {
  title: string;
  date: string;
  cost: number;
  days_away: number;
  impact: "covered" | "tight" | "shortfall" | null;
}

export interface MilestonesData {
  upcoming: MilestoneEvent[];
  current_streak: number;
}

// ─── Career / Jobs ────────────────────────────────────────────
export interface JobOption {
  id: string;
  title: string;
  company_type: string;
  location: string;
  salary_low: number;
  salary_high: number;
  match_score: number;
  income_lift_pct: number;
  monthly_takehome_delta: number;  // tier-specific after-tax rate

  // ROI fields — computed in useSnapshotData
  total_expected_return: number;
  roi_multiple: number;
  payback_days: number;
  capital_equivalent: number;
  job_probability: number;
}

export interface CareerData {
  current_salary: number;
  jobs: JobOption[];
}

// ─── Action ───────────────────────────────────────────────────
export interface ActionData {
  action_text: string;
  action_source: string;
  ctas: Array<{
    label: string;
    tab: string;
    urgency: "high" | "medium" | "low";
  }>;
}

// ─── Root Types ───────────────────────────────────────────────
export interface SnapshotData {
  faith: FaithCardData | null;
  vibe: VibeCheckData | null;
  cash: CashNowData | null;
  spending: SpendingData | null;
  roster: RosterData | null;
  milestones: MilestonesData | null;
  career: CareerData | null;
  action: ActionData | null;
}

export type CardLoadState = "loading" | "ready" | "error";

export interface SnapshotLoadStates {
  faith: CardLoadState;
  vibe: CardLoadState;
  cash: CardLoadState;
  spending: CardLoadState;
  roster: CardLoadState;
  milestones: CardLoadState;
  career: CardLoadState;
  action: CardLoadState;
}
