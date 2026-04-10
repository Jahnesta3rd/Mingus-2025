import { useCallback, useEffect, useState } from 'react';

function csrfHeaders(): Record<string, string> {
  const token =
    document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || 'test-token';
  return { 'X-CSRF-Token': token };
}

function getAuthHeadersGet(): HeadersInit {
  const token = localStorage.getItem('mingus_token') || '';
  return token ? { Authorization: `Bearer ${token}`, ...csrfHeaders() } : { ...csrfHeaders() };
}

export interface LifeScoreSnapshot {
  id: string;
  user_id: number;
  snapshot_date: string;
  trigger: string;
  body_score: number | null;
  roof_score: number | null;
  vehicle_score: number | null;
  life_ledger_score: number | null;
  best_vibe_emotional_score: number | null;
  best_vibe_financial_score: number | null;
  best_vibe_combined_score: number | null;
  active_tracked_people_count: number | null;
  monthly_savings_rate: number | null;
  net_worth_estimate: number | null;
  relationship_monthly_cost: number | null;
  avg_wellness_score: number | null;
  avg_stress_level: number | null;
  created_at: string;
}

export interface LifeCorrelationItem {
  type: string;
  strength: string;
  description: string;
  insight_message: string;
}

export interface LifeCorrelationSummary {
  snapshots_count: number;
  date_range_days?: number;
  has_sufficient_data: boolean;
  headline_insight: string;
  correlations: LifeCorrelationItem[];
  message?: string;
  deltas?: Record<string, number | null>;
}

export interface UseLifeCorrelationResult {
  summary: LifeCorrelationSummary | null;
  snapshots: LifeScoreSnapshot[] | null;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

export function useLifeCorrelation(enabled: boolean, tier: 'budget' | 'mid_tier' | 'professional'): UseLifeCorrelationResult {
  const [summary, setSummary] = useState<LifeCorrelationSummary | null>(null);
  const [snapshots, setSnapshots] = useState<LifeScoreSnapshot[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!enabled || tier === 'budget') {
      setSummary(null);
      setSnapshots(null);
      setError(null);
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const res = await fetch('/api/life-correlation/summary', {
        method: 'GET',
        credentials: 'include',
        headers: getAuthHeadersGet(),
      });

      if (!res.ok) {
        const errBody = await res.json().catch(() => ({}));
        const msg =
          typeof errBody.message === 'string'
            ? errBody.message
            : `Failed to load life correlation (${res.status})`;
        throw new Error(msg);
      }

      const data = (await res.json()) as LifeCorrelationSummary;
      setSummary(data);

      const needSnapshots =
        tier === 'professional' &&
        data.has_sufficient_data === true;

      if (needSnapshots) {
        const snapRes = await fetch('/api/life-correlation/snapshots', {
          method: 'GET',
          credentials: 'include',
          headers: getAuthHeadersGet(),
        });
        if (!snapRes.ok) {
          setSnapshots([]);
        } else {
          const snapJson = (await snapRes.json()) as { snapshots?: LifeScoreSnapshot[] };
          setSnapshots(snapJson.snapshots ?? []);
        }
      } else {
        setSnapshots(null);
      }
    } catch (e) {
      console.error('useLifeCorrelation', e);
      setError(e instanceof Error ? e.message : 'Failed to load life correlation');
      setSummary(null);
      setSnapshots(null);
    } finally {
      setLoading(false);
    }
  }, [enabled, tier]);

  useEffect(() => {
    void load();
  }, [load]);

  return { summary, snapshots, loading, error, refetch: load };
}
