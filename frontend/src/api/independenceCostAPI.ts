import { csrfHeaders } from '../utils/csrfHeaders';

export interface IndependenceRecommendation {
  should_recommend: boolean;
  icc_assessment_id?: string;
  partner_id?: string;
  partner_name?: string;
  city?: string;
  monthly_cost?: number;
  current_cost?: number;
  gap?: number;
  startup_cost?: number;
  message?: string;
  cta?: string;
}

export interface IndependenceMonthlyCosts {
  housing?: number;
  utilities?: number;
  food?: number;
  transportation?: number;
  phone_internet?: number;
  other?: number;
  other_essentials?: number;
  total_monthly?: number;
}

export interface IndependenceStartupTransportation {
  car_purchase?: number;
  car_insurance_deposit?: number;
  registration?: number;
  maintenance_fund?: number;
}

export interface IndependenceStartupCosts {
  moving?: number;
  utilities_deposits?: number;
  rental_deposits?: number;
  phone_internet?: number;
  furniture_basics?: number;
  kitchen_appliances?: number;
  household_items?: number;
  car_purchase?: number;
  car_insurance_deposit?: number;
  registration?: number;
  car_maintenance_fund?: number;
  emergency_fund?: number;
  total_startup_cost?: number;
  total_with_car?: number;
  total_without_car?: number;
  transportation?: IndependenceStartupTransportation;
}

export interface IndependenceVibeData {
  is_declining_12_weeks?: boolean;
  emotional_scores?: number[];
  scores_12_weeks?: number[];
  emotional_trend?: string;
  partner_name?: string;
}

export interface IndependenceAssessment {
  icc_assessment_id?: string;
  monthly_costs: IndependenceMonthlyCosts;
  startup_costs: IndependenceStartupCosts;
  current_situation?: Record<string, unknown>;
  gap?: number;
  timeline_months?: number | null;
  vibe_data?: IndependenceVibeData;
  location?: Record<string, unknown>;
  market_rent?: Record<string, unknown>;
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

async function parseJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const text = await response.text().catch(() => '');
    throw new Error(text || `Request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function getShouldRecommend(options?: {
  getAccessToken?: () => string | null;
  fetchFn?: FetchFn;
}): Promise<IndependenceRecommendation> {
  const fetchFn = options?.fetchFn ?? fetch;
  const response = await fetchFn('/api/independence-cost/should-recommend', {
    method: 'GET',
    credentials: 'include',
    headers: buildHeaders(options?.getAccessToken),
  });
  return parseJson<IndependenceRecommendation>(response);
}

export async function getAssessment(
  personId: string,
  options?: {
    getAccessToken?: () => string | null;
    fetchFn?: FetchFn;
  },
): Promise<IndependenceAssessment> {
  const fetchFn = options?.fetchFn ?? fetch;
  const response = await fetchFn(
    `/api/independence-cost/assess?person_id=${encodeURIComponent(personId)}`,
    {
      method: 'GET',
      credentials: 'include',
      headers: buildHeaders(options?.getAccessToken),
    },
  );
  return parseJson<IndependenceAssessment>(response);
}

export async function dismissCard(options?: {
  getAccessToken?: () => string | null;
  fetchFn?: FetchFn;
}): Promise<{ success: boolean }> {
  const fetchFn = options?.fetchFn ?? fetch;
  const response = await fetchFn('/api/independence-cost/dismiss', {
    method: 'POST',
    credentials: 'include',
    headers: buildHeaders(options?.getAccessToken),
    body: JSON.stringify({}),
  });
  return parseJson<{ success: boolean }>(response);
}

export async function getIndependenceStatus(options?: {
  getAccessToken?: () => string | null;
  fetchFn?: FetchFn;
}): Promise<{
  dismissed: boolean;
  can_calculate: boolean;
  has_assessment_today: boolean;
  partner_id: string | null;
}> {
  const fetchFn = options?.fetchFn ?? fetch;
  const response = await fetchFn('/api/independence-cost/status', {
    method: 'GET',
    credentials: 'include',
    headers: buildHeaders(options?.getAccessToken),
  });
  return parseJson(response);
}
