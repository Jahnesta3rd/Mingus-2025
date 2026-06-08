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

export async function submitBodyCheckAnswers(
  answers: Record<string, number>
): Promise<{ body_score: number }> {
  const res = await fetch('/api/life-ledger/body-check/submit', {
    method: 'POST',
    headers: authJsonHeaders(),
    credentials: 'include',
    body: JSON.stringify({ answers }),
  });
  if (!res.ok) {
    let msg = `Could not save Body Check (${res.status})`;
    try {
      const j = (await res.json()) as { error?: string };
      if (j.error) msg = j.error;
    } catch {
      /* ignore */
    }
    throw new Error(msg);
  }
  return (await res.json()) as { body_score: number };
}

export async function submitRoofCheckAnswers(
  answers: Record<string, number>
): Promise<{ roof_score: number }> {
  const res = await fetch('/api/life-ledger/roof-check/submit', {
    method: 'POST',
    headers: authJsonHeaders(),
    credentials: 'include',
    body: JSON.stringify({ answers }),
  });
  if (!res.ok) {
    let msg = `Could not save Roof Check (${res.status})`;
    try {
      const j = (await res.json()) as { error?: string };
      if (j.error) msg = j.error;
    } catch {
      /* ignore */
    }
    throw new Error(msg);
  }
  return (await res.json()) as { roof_score: number };
}

export async function submitVehicleCheckAnswers(
  answers: Record<string, number>
): Promise<{ vehicle_score: number }> {
  const res = await fetch('/api/life-ledger/vehicle-check/submit', {
    method: 'POST',
    headers: authJsonHeaders(),
    credentials: 'include',
    body: JSON.stringify({ answers }),
  });
  if (!res.ok) {
    let msg = `Could not save Vehicle Check (${res.status})`;
    try {
      const j = (await res.json()) as { error?: string };
      if (j.error) msg = j.error;
    } catch {
      /* ignore */
    }
    throw new Error(msg);
  }
  return (await res.json()) as { vehicle_score: number };
}

export type MindMoodPayload = {
  mood_rating: number;
  stress_level: number;
  mood_stress_triggered_purchase: string;
  mood_avoided_finances: boolean;
  mood_coping_methods: string[];
  spending_intentionality_rating: number;
};

export async function submitMindMoodCheckin(payload: MindMoodPayload): Promise<void> {
  const res = await fetch('/api/checkups/mind-mood', {
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
}

export type SpiritCalmSupplementPayload = {
  practice_felt_grounding: boolean;
  meditation_minutes_total: number;
};

export async function submitSpiritCalmSupplement(
  payload: SpiritCalmSupplementPayload
): Promise<void> {
  const res = await fetch('/api/checkups/spirit-calm', {
    method: 'POST',
    headers: authJsonHeaders(),
    credentials: 'include',
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    let msg = `Could not save practice notes (${res.status})`;
    try {
      const j = (await res.json()) as { error?: string };
      if (j.error) msg = j.error;
    } catch {
      /* ignore */
    }
    throw new Error(msg);
  }
}
