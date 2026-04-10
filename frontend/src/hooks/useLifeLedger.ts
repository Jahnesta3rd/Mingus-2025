import { useCallback, useEffect, useState } from 'react';

function csrfHeaders(): Record<string, string> {
  const token =
    document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || 'test-token';
  return { 'X-CSRF-Token': token };
}

function getAuthHeadersJson(): HeadersInit {
  const token = localStorage.getItem('mingus_token') || '';
  const h: Record<string, string> = {
    'Content-Type': 'application/json',
    ...csrfHeaders(),
  };
  if (token) h.Authorization = `Bearer ${token}`;
  return h;
}

function getAuthHeadersGet(): HeadersInit {
  const token = localStorage.getItem('mingus_token') || '';
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export interface LifeLedgerInsightItem {
  id: string;
  module: string;
  insight_type: string;
  message: string;
  action_url: string | null;
  dismissed: boolean;
}

export interface LifeLedgerProfile {
  id: string;
  user_id: number;
  vibe_score: number | null;
  body_score: number | null;
  roof_score: number | null;
  vehicle_score: number | null;
  life_ledger_score: number;
  vibe_lead_id: string | null;
  vibe_annual_projection: number | null;
  body_health_cost_projection: number | null;
  roof_housing_wealth_gap: number | null;
  vehicle_annual_maintenance: number | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface UseLifeLedgerResult {
  profile: LifeLedgerProfile | null;
  insights: LifeLedgerInsightItem[];
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

export function useLifeLedger(enabled: boolean): UseLifeLedgerResult {
  const [profile, setProfile] = useState<LifeLedgerProfile | null>(null);
  const [insights, setInsights] = useState<LifeLedgerInsightItem[]>([]);
  const [loading, setLoading] = useState(() => !!enabled);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(async () => {
    if (!enabled) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/life-ledger/profile', {
        credentials: 'include',
        headers: getAuthHeadersGet(),
      });
      if (!res.ok) {
        let msg = `Could not load Life Ledger (${res.status})`;
        try {
          const j = (await res.json()) as { error?: string };
          if (j.error) msg = j.error;
        } catch {
          /* ignore */
        }
        throw new Error(msg);
      }
      const data = (await res.json()) as LifeLedgerProfile & { insights?: LifeLedgerInsightItem[] };
      const { insights: ins = [], ...rest } = data;
      setProfile(rest);
      setInsights(Array.isArray(ins) ? ins : []);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load Life Ledger');
      setProfile(null);
      setInsights([]);
    } finally {
      setLoading(false);
    }
  }, [enabled]);

  useEffect(() => {
    if (!enabled) {
      setLoading(false);
      return;
    }
    void refetch();
  }, [enabled, refetch]);

  return { profile, insights, loading, error, refetch };
}

export { getAuthHeadersJson };
