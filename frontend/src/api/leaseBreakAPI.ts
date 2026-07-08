import { csrfHeaders } from '../utils/csrfHeaders';

export interface LeaseBreakScenarioDetail {
  key: string;
  label: string;
  total_cost: number;
  remaining_rent?: number;
  move_out_cost?: number;
  break_fee?: number;
  interim_housing_monthly?: number;
  interim_housing_total?: number;
  moving_buffer?: number;
}

export interface LeaseBreakTimelineImpact {
  months_remaining: number;
  monthly_cashflow_delta_if_break: number;
  total_cash_released_if_break: number;
  break_even_month: number | null;
}

export interface LeaseBreakNegotiationScript {
  talking_points: string[];
  email_template: string;
  phone_script: string;
}

export interface LeaseBreakAnalyzeResponse {
  analysis_id: string | null;
  months_remaining: number;
  monthly_rent: number;
  break_fee_percent: number;
  scenario_a: LeaseBreakScenarioDetail;
  scenario_b: LeaseBreakScenarioDetail;
  scenario_a_cost: number;
  scenario_b_cost: number;
  recommendation: 'break_early' | 'stay_through_lease' | 'either' | string;
  recommendation_label: string;
  savings: number;
  timeline_impact: LeaseBreakTimelineImpact;
  negotiation_script: LeaseBreakNegotiationScript;
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

export async function analyzeLeaseBreak(
  params: {
    monthsRemaining: number;
    monthlyRent: number;
    breakFeePercent?: number;
  },
  options?: { getAccessToken?: () => string | null; fetchFn?: FetchFn },
): Promise<LeaseBreakAnalyzeResponse> {
  const fetchFn = options?.fetchFn ?? fetch;
  const response = await fetchFn('/api/lease-break/analyze', {
    method: 'POST',
    credentials: 'include',
    headers: buildHeaders(options?.getAccessToken),
    body: JSON.stringify({
      months_remaining: params.monthsRemaining,
      monthly_rent: params.monthlyRent,
      break_fee_percent: params.breakFeePercent ?? 1.5,
    }),
  });
  if (!response.ok) {
    const text = await response.text().catch(() => '');
    throw new Error(text || `Request failed: ${response.status}`);
  }
  return response.json() as Promise<LeaseBreakAnalyzeResponse>;
}
