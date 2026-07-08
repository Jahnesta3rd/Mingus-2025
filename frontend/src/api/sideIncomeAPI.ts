import { csrfHeaders } from '../utils/csrfHeaders';

export interface SideIncomeIccImpact {
  closes_monthly_gap: boolean;
  gap_coverage_pct: number;
  timeline_acceleration_months: number;
}

export interface SideIncomeInterimHousingCombo {
  roommate_rent_savings?: number;
  new_gap_with_roommate: number;
  months_to_startup_with_roommate: number | null;
}

export interface SideIncomeJob {
  title: string;
  type: 'gig' | 'part_time' | 'freelance' | 'contract' | string;
  hourly_range: string;
  hours_per_week: number;
  monthly_income: number;
  schedule_fit: string;
  why_it_fits: string;
  first_step: string;
  startup_cost: string;
  icc_impact: SideIncomeIccImpact;
  interim_housing_combo: SideIncomeInterimHousingCombo;
}

export interface SideIncomeContext {
  relationship_exit_urgency: 'high' | 'medium' | 'low' | string;
  timeline_pressure: string;
  total_monthly_gap: number;
  startup_cost: number;
  current_job?: string;
  city?: string | null;
}

export interface SideIncomeResponse {
  matches: SideIncomeJob[];
  recommendation: SideIncomeJob | null;
  context: SideIncomeContext;
}

export interface SideIncomeRequestParams {
  monthlyGap: number;
  hoursPerWeekAvailable: number;
  startupCostNeeded: number;
  timelineMonths: number;
}

type FetchFn = typeof fetch;

function buildHeaders(getAccessToken?: () => string | null): HeadersInit {
  const token = getAccessToken?.() ?? null;
  return {
    'Content-Type': 'application/json',
    ...csrfHeaders(),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

export async function getSideIncomeRecommendations(
  params: SideIncomeRequestParams,
  options?: {
    getAccessToken?: () => string | null;
    fetchFn?: FetchFn;
  },
): Promise<SideIncomeResponse> {
  const fetchFn = options?.fetchFn ?? fetch;
  const response = await fetchFn('/api/independence-cost/side-income-recommendations', {
    method: 'POST',
    credentials: 'include',
    headers: buildHeaders(options?.getAccessToken),
    body: JSON.stringify({
      monthly_gap: params.monthlyGap,
      hours_per_week_available: params.hoursPerWeekAvailable,
      startup_cost_needed: params.startupCostNeeded,
      timeline_months: params.timelineMonths,
    }),
  });

  if (!response.ok) {
    const text = await response.text().catch(() => '');
    throw new Error(text || `Request failed: ${response.status}`);
  }

  return response.json() as Promise<SideIncomeResponse>;
}
