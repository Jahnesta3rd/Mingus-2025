import { getAuthHeadersJson } from '../../hooks/useLifeLedger';

export const CHECKUPS_HUB_PATH = '/dashboard/vibe-checkups';

export function csrfHeaders(): Record<string, string> {
  const token =
    document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || 'test-token';
  return { 'X-CSRF-Token': token };
}

export function authJsonHeaders(): Record<string, string> {
  return {
    ...getAuthHeadersJson(),
    ...csrfHeaders(),
  } as Record<string, string>;
}

/** Parse API date or datetime strings; returns null if invalid. */
export function parseApiDate(iso: string | null | undefined): Date | null {
  if (!iso || typeof iso !== 'string') return null;
  const normalized = iso.length === 10 ? `${iso}T12:00:00Z` : iso;
  const d = new Date(normalized);
  return Number.isNaN(d.getTime()) ? null : d;
}

/** Human-readable relative time for a past calendar event. */
export function formatRelativeLastUpdate(iso: string | null | undefined): string | null {
  const then = parseApiDate(iso);
  if (!then) return null;
  const now = new Date();
  const diffMs = now.getTime() - then.getTime();
  if (diffMs < 0) return null;
  const dayMs = 86400000;
  const days = Math.floor(diffMs / dayMs);
  if (days === 0) return 'today';
  if (days === 1) return 'yesterday';
  if (days < 14) return `${days} days ago`;
  if (days < 60) return `${Math.round(days / 7)} weeks ago`;
  if (days < 365) return `${Math.round(days / 30)} months ago`;
  return `${Math.round(days / 365)} years ago`;
}

async function postCheckup<T>(path: string, payload: unknown): Promise<T> {
  const res = await fetch(path, {
    method: 'POST',
    headers: authJsonHeaders(),
    credentials: 'include',
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    let msg = `Could not save check-in (${res.status})`;
    try {
      const j = (await res.json()) as { error?: string };
      if (j.error) msg = j.error;
    } catch {
      /* ignore */
    }
    throw new Error(msg);
  }
  return (await res.json()) as T;
}

export type BodyCheckupPayload = {
  body_energy_rating: number;
  body_work_impact: string;
  body_ongoing_health_cost: boolean;
};

export async function submitBodyCheckup(
  payload: BodyCheckupPayload
): Promise<{ body_score: number }> {
  return postCheckup('/api/checkups/body', payload);
}

export type MindMoodPayload = {
  mood_stress_triggered_purchase: string;
  mood_avoided_finances: boolean;
  mood_coping_methods: string[];
  spending_intentionality_rating: number;
};

export async function submitMindMoodCheckin(payload: MindMoodPayload): Promise<void> {
  await postCheckup('/api/checkups/mind-mood', payload);
}

export type SpiritCalmPayload = {
  practice_had_moments: boolean;
  practice_affected_finances: string;
  spirit_financially_anxious: string;
};

export async function submitSpiritCalmCheckin(payload: SpiritCalmPayload): Promise<void> {
  await postCheckup('/api/checkups/spirit-calm', payload);
}

export type HousingCheckupPayload = {
  housing_stability_rating: number;
  housing_tenure: string;
  housing_lease_end_horizon?: string | null;
  housing_cost_changed: string;
  housing_down_payment_status?: string | null;
  housing_unexpected_cost: boolean;
  housing_unexpected_cost_amount?: number | null;
};

export async function submitHousingCheckup(
  payload: HousingCheckupPayload
): Promise<{ roof_score: number }> {
  return postCheckup('/api/checkups/housing-roof', payload);
}

export type VehicleCheckupPayload = {
  vehicle_satisfaction_rating: number;
  vehicle_maintenance_confidence: number;
  vehicle_recent_concern: boolean;
  vehicle_concern_description?: string | null;
  vehicle_weekly_miles: number;
  vehicle_last_service_horizon: string;
  vehicle_insurance_known: boolean;
  vehicle_insurance_premium?: number | null;
  vehicle_insurance_last_shopped?: string | null;
  vehicle_decision_horizon: string;
  vehicle_reliability_rating: number;
  vehicle_value_perception: number;
};

export async function submitVehicleCheckup(
  payload: VehicleCheckupPayload
): Promise<{ vehicle_score: number }> {
  return postCheckup('/api/checkups/vehicle', payload);
}

export type RelationshipsCheckupPayload = {
  relationship_friction_type: string;
  relationship_spending_this_week: boolean;
  relationship_spending_amount?: number | null;
  relationship_spending_type?: string | null;
  relationship_direction: string;
  relationship_cost_awareness: string;
  relationship_future_intention: string;
};

export async function submitRelationshipsCheckup(payload: RelationshipsCheckupPayload): Promise<void> {
  await postCheckup('/api/checkups/relationships', payload);
}
