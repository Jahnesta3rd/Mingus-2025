import { csrfHeaders } from '../utils/csrfHeaders';

export type VibeTrend = 'declining' | 'stable' | 'improving';
export type FeelsSafe = 'yes' | 'mostly' | 'sometimes' | 'no' | 'unsafe';

export type EmergencySignalKey =
  | 'abuse_escalation'
  | 'physical_threat'
  | 'substance_abuse'
  | 'infidelity'
  | 'financial_control'
  | 'isolation'
  | 'emotional_abuse'
  | 'imminent_danger'
  | 'stalking_or_monitoring'
  | 'sexual_coercion';

export interface RelationshipCheckinRequest {
  personId: string;
  vibeTrend: VibeTrend;
  feelsSafe: FeelsSafe;
  needsToLeaveSooner: boolean;
  onTrackSavings: boolean;
  preferLeaveNow: boolean;
  emergencySignals?: Partial<Record<EmergencySignalKey, boolean>>;
}

export interface SafetyResource {
  name: string;
  phone: string;
  url: string;
  type: string;
}

export interface RelationshipCheckinResponse {
  status: 'on_track' | 'accelerate' | 'emergency' | 'improving';
  emergency_alert: boolean;
  emergency_flags: string[];
  next_steps: string[];
  resources_if_needed: SafetyResource[];
  checkin_id: string;
  tier_recommendation: string | null;
}

export interface QuarterlyReassessmentResponse {
  partner_name: string;
  vibe_scores: number[];
  checkin_history: Array<{
    date: string;
    status: string;
    vibe_trend: string;
    feels_safe: string;
  }>;
  timeline: {
    original_months: number | null;
    current_months: number | null;
    monthly_gap: number | null;
    startup_cost: number | null;
  };
  progress_notes: string[];
  celebrate_progress: boolean;
  improvement_path: {
    available: boolean;
    options: string[];
  } | null;
  resources: SafetyResource[];
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

export async function submitRelationshipCheckin(
  params: RelationshipCheckinRequest,
  options?: { getAccessToken?: () => string | null; fetchFn?: FetchFn },
): Promise<RelationshipCheckinResponse> {
  const fetchFn = options?.fetchFn ?? fetch;
  const response = await fetchFn('/api/relationship-checkin/assess', {
    method: 'POST',
    credentials: 'include',
    headers: buildHeaders(options?.getAccessToken),
    body: JSON.stringify({
      person_id: params.personId,
      vibe_trend: params.vibeTrend,
      feels_safe: params.feelsSafe,
      needs_to_leave_sooner: params.needsToLeaveSooner,
      on_track_savings: params.onTrackSavings,
      prefer_leave_now: params.preferLeaveNow,
      emergency_signals: params.emergencySignals,
    }),
  });
  if (!response.ok) {
    const text = await response.text().catch(() => '');
    throw new Error(text || `Request failed: ${response.status}`);
  }
  return response.json() as Promise<RelationshipCheckinResponse>;
}

export async function getQuarterlyReassessment(
  personId: string,
  options?: { getAccessToken?: () => string | null; fetchFn?: FetchFn },
): Promise<QuarterlyReassessmentResponse> {
  const fetchFn = options?.fetchFn ?? fetch;
  const response = await fetchFn(
    `/api/relationship-checkin/quarterly-reassessment?person_id=${encodeURIComponent(personId)}`,
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
  return response.json() as Promise<QuarterlyReassessmentResponse>;
}

export const DV_RESOURCES: SafetyResource[] = [
  {
    name: 'National Domestic Violence Hotline',
    phone: '1-800-799-7233',
    url: 'https://www.thehotline.org',
    type: 'hotline',
  },
  {
    name: 'Crisis Text Line',
    phone: 'Text HOME to 741741',
    url: 'https://www.crisistextline.org',
    type: 'text',
  },
  {
    name: 'Safety plan template',
    phone: '',
    url: 'https://www.thehotline.org/plan-for-safety/',
    type: 'safety_plan',
  },
  {
    name: 'Local shelter finder',
    phone: '1-800-799-7233',
    url: 'https://www.domesticshelters.org',
    type: 'shelter',
  },
  {
    name: 'Free counseling (SAMHSA)',
    phone: '1-800-662-4357',
    url: 'https://www.samhsa.gov/find-help',
    type: 'counseling',
  },
];
