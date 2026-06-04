import { useCallback, useEffect, useState } from 'react';

export interface HousingProfileSummary {
  housingType: 'rent' | 'own' | null;
  monthlyCost: number | null;
  zipOrCity: string | null;
  hasBuyGoal: boolean;
  targetPrice: number | null;
  targetTimelineMonths: number | null;
  profileComplete: boolean;
}

export interface UseHousingCheckInResult {
  data: HousingProfileSummary | null;
  loading: boolean;
  error: boolean;
  refetch: () => void;
}

interface ProfileSummaryApiProfile {
  housing_type?: 'rent' | 'own' | null;
  monthly_cost?: number | null;
  zip_or_city?: string | null;
  has_buy_goal?: boolean;
  target_price?: number | null;
  target_timeline_months?: number | null;
  profile_complete?: boolean;
}

interface ProfileSummaryResponse {
  success?: boolean;
  profile?: ProfileSummaryApiProfile;
}

function buildAuthHeaders(): HeadersInit {
  const token = localStorage.getItem('mingus_token');
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    'X-CSRF-Token': token || 'test-token',
  };
  if (token) {
    (headers as Record<string, string>).Authorization = `Bearer ${token}`;
  }
  return headers;
}

function mapProfile(raw: ProfileSummaryApiProfile): HousingProfileSummary {
  const housingType =
    raw.housing_type === 'rent' || raw.housing_type === 'own' ? raw.housing_type : null;
  return {
    housingType,
    monthlyCost: typeof raw.monthly_cost === 'number' ? raw.monthly_cost : null,
    zipOrCity: raw.zip_or_city ?? null,
    hasBuyGoal: Boolean(raw.has_buy_goal),
    targetPrice: typeof raw.target_price === 'number' ? raw.target_price : null,
    targetTimelineMonths:
      typeof raw.target_timeline_months === 'number' ? raw.target_timeline_months : null,
    profileComplete: Boolean(raw.profile_complete),
  };
}

async function fetchProfileSummary(): Promise<HousingProfileSummary> {
  const res = await fetch('/api/housing/profile-summary', {
    credentials: 'include',
    headers: buildAuthHeaders(),
  });
  if (!res.ok) {
    throw new Error('Failed to load housing profile summary');
  }
  const json = (await res.json()) as ProfileSummaryResponse;
  return mapProfile(json.profile ?? {});
}

export function useHousingCheckIn(): UseHousingCheckInResult {
  const [data, setData] = useState<HousingProfileSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [fetchKey, setFetchKey] = useState(0);

  const refetch = useCallback(() => {
    setFetchKey((k) => k + 1);
  }, []);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(false);

    fetchProfileSummary()
      .then((summary) => {
        if (cancelled) return;
        setData(summary);
        setError(false);
      })
      .catch(() => {
        if (cancelled) return;
        setData(null);
        setError(true);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [fetchKey]);

  return { data, loading, error, refetch };
}
