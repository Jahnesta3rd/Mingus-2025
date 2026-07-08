import { csrfHeaders } from '../utils/csrfHeaders';

export interface PhasedIndependenceTier {
  tier: number;
  name: string;
  incremental_cost: number;
  cumulative_cost: number;
  target_leave_months: number;
  description: string;
  furniture_summary: string;
  includes_car: boolean;
  gap_to_full_icc_startup: number;
}

export interface PhasedIndependenceScenario {
  key: string;
  label: string;
  target_months: number;
  tier_levels: number[];
  tier_breakdown: Array<{ tier: number; name: string; cost: number }>;
  cumulative_startup: number;
  housing: string;
  housing_label: string;
  months_to_fund: number | null;
  on_track: boolean;
  shortfall_at_target: number;
  monthly_savings_assumed: number;
  monthly_gap_reference: number;
}

export interface PhasedIndependenceBuyingItem {
  item: string;
  budget: number;
}

export interface PhasedIndependenceBuyingCategory {
  name: string;
  budget: number;
  items: PhasedIndependenceBuyingItem[];
}

export interface PhasedIndependenceBuyingGuide {
  tier: number;
  title: string;
  budget_target: number;
  strategy: string;
  categories: PhasedIndependenceBuyingCategory[];
  retailers: Array<{ name: string; url: string; tip: string }>;
  printable_title: string;
}

export interface PhasedIndependenceContingency {
  key: string;
  label: string;
  adjusted_monthly_savings?: number;
  adjusted_startup?: number;
  extra_saved?: number;
  new_shortfall?: number;
  months_to_fund?: number | null;
  still_on_track?: boolean;
  delta_months?: number | null;
}

export interface PhasedIndependenceTimelineResponse {
  total_monthly_gap: number;
  monthly_savings: number;
  startup_cost_full: number;
  tier_definitions: Record<string, PhasedIndependenceTier | Record<string, number>>;
  scenarios: PhasedIndependenceScenario[];
  buying_guides: Record<string, PhasedIndependenceBuyingGuide>;
  contingency_scenarios: PhasedIndependenceContingency[];
  default_scenario_key: string;
  selected_scenario_key: string;
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

export async function getPhasedIndependenceTimeline(
  params: {
    totalGap: number;
    monthlySavings?: number;
    startupCostFull?: number;
    scenarioKey?: string;
  },
  options?: { getAccessToken?: () => string | null; fetchFn?: FetchFn },
): Promise<PhasedIndependenceTimelineResponse> {
  const fetchFn = options?.fetchFn ?? fetch;
  const search = new URLSearchParams();
  search.set('total_gap', String(params.totalGap));
  if (params.monthlySavings != null) {
    search.set('monthly_savings', String(params.monthlySavings));
  }
  if (params.startupCostFull != null) {
    search.set('startup_cost_full', String(params.startupCostFull));
  }
  if (params.scenarioKey) {
    search.set('scenario_key', params.scenarioKey);
  }

  const response = await fetchFn(`/api/phased-independence/timeline?${search.toString()}`, {
    method: 'GET',
    credentials: 'include',
    headers: buildHeaders(options?.getAccessToken),
  });
  if (!response.ok) {
    const text = await response.text().catch(() => '');
    throw new Error(text || `Request failed: ${response.status}`);
  }
  return response.json() as Promise<PhasedIndependenceTimelineResponse>;
}
