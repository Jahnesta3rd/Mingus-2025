import { useCallback, useEffect, useState } from 'react';
import { useAuth } from './useAuth';
import { csrfHeaders } from '../utils/csrfHeaders';

export interface SpiritWeeklyApiRow {
  week_label: string;
  practice_score: number;
  checkin_count?: number;
  savings_rate?: number | null;
  impulse_spend?: number | null;
  stress_index?: number | null;
  bills_ontime?: number | null;
}

/** Response shape varies by tier; fields absent on lower tiers. */
export interface SpiritCorrelationData {
  corr_practice_savings: number | null;
  corr_practice_stress: number | null;
  corr_practice_impulse?: number | null;
  corr_practice_bills_ontime?: number | null;
  insight_summary?: string[];
  id?: number;
  user_id?: number;
  computed_at?: string | null;
  weeks_analyzed?: number | null;
  weekly_data?: SpiritWeeklyApiRow[];
  avg_practice_score_high_weeks?: number | null;
  avg_impulse_miss_days?: number | null;
  avg_impulse_checkin_days?: number | null;
}

function buildHeaders(getAccessToken: () => string | null): HeadersInit {
  const h: Record<string, string> = {
    ...csrfHeaders(),
  };
  const token = getAccessToken();
  if (token) {
    h.Authorization = `Bearer ${token}`;
  }
  return h;
}

export function useSpiritCorrelation() {
  const { getAccessToken, isAuthenticated } = useAuth();
  const [correlationData, setCorrelationData] = useState<SpiritCorrelationData | null>(null);
  const [weeklyData, setWeeklyData] = useState<SpiritWeeklyApiRow[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(async () => {
    const res = await fetch('/api/spirit/correlation', {
      method: 'GET',
      credentials: 'include',
      headers: buildHeaders(getAccessToken),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const msg =
        (data as { error?: string; message?: string }).message ||
        (data as { error?: string }).error ||
        res.statusText;
      throw new Error(msg || 'Failed to load correlation');
    }
    const body = data as SpiritCorrelationData;
    setCorrelationData(body);
    setWeeklyData(Array.isArray(body.weekly_data) ? body.weekly_data : []);
  }, [getAccessToken]);

  useEffect(() => {
    if (!isAuthenticated) {
      setCorrelationData(null);
      setWeeklyData([]);
      setIsLoading(false);
      setError(null);
      return;
    }

    let cancelled = false;
    setIsLoading(true);
    setError(null);

    void (async () => {
      try {
        await refetch();
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : 'Failed to load correlation');
          setCorrelationData(null);
          setWeeklyData([]);
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [isAuthenticated, refetch]);

  return {
    correlationData,
    weeklyData,
    isLoading,
    error,
    refetch,
  };
}
