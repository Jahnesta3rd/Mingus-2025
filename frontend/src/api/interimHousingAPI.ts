import { csrfHeaders } from '../utils/csrfHeaders';

export interface InterimHousingScenario {
  key: string;
  name: string;
  monthly_rent: number;
  monthly_rent_range?: { min: number; max: number } | null;
  startup_cost: number;
  monthly_savings_vs_solo: number;
  startup_savings_vs_solo: number;
  reduced_monthly_gap: number;
  timeline_months: number | null;
  difficulty: string;
  pros: string[];
  cons: string[];
  features: Record<string, string | boolean>;
}

export interface InterimHousingPhase {
  phase: number;
  label: string;
  scenario_key: string;
  duration_months: number;
  monthly_savings?: number;
  cumulative_savings?: number;
  remaining_startup_target?: number;
  goal: string;
}

export interface InterimHousingSoloComparison {
  label: string;
  monthly_rent: number;
  monthly_gap: number;
  startup_cost_needed: number;
  timeline_months: number | null;
}

export interface InterimHousingConversationTemplate {
  title: string;
  summary: string;
  talking_points?: string[];
  sample_opener?: string;
  checklist?: string[];
  red_flags?: string[];
  must_haves?: string[];
}

export interface InterimHousingScenariosResponse {
  zip_code: string;
  market_rent_2br: number;
  market_rent_source?: string;
  solo_comparison: InterimHousingSoloComparison;
  scenarios: InterimHousingScenario[];
  phased_exit_plan: {
    phases: InterimHousingPhase[];
    total_months_to_solo_readiness: number;
    solo_baseline_months: number | null;
    months_saved_vs_solo: number | null;
    summary: string;
  };
  conversation_templates: Record<string, InterimHousingConversationTemplate>;
  feature_matrix_keys: string[];
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

export async function getInterimHousingScenarios(
  params?: {
    zipCode?: string;
    startupCostNeeded?: number;
    monthlyGap?: number;
  },
  options?: { getAccessToken?: () => string | null; fetchFn?: FetchFn },
): Promise<InterimHousingScenariosResponse> {
  const fetchFn = options?.fetchFn ?? fetch;
  const search = new URLSearchParams();
  if (params?.zipCode) search.set('zip_code', params.zipCode);
  if (params?.startupCostNeeded != null) {
    search.set('startup_cost_needed', String(params.startupCostNeeded));
  }
  if (params?.monthlyGap != null) {
    search.set('monthly_gap', String(params.monthlyGap));
  }
  const query = search.toString();
  const response = await fetchFn(
    `/api/interim-housing/scenarios${query ? `?${query}` : ''}`,
    {
      method: 'GET',
      credentials: 'include',
      headers: buildHeaders(options?.getAccessToken),
    },
  );
  if (!response.ok) {
    const text = await response.text().catch(() => '');
    throw new Error(text || `Request failed: ${response.status}`);
  }
  return response.json() as Promise<InterimHousingScenariosResponse>;
}
