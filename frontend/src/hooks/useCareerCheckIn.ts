import { useCallback, useEffect, useState } from 'react';

export interface CareerProfileSummary {
  currentRole: string | null;
  industry: string | null;
  seniorityLevel: string | null;
  yearsExperience: number | null;
  targetComp: number | null;
  openToMove: boolean;
  profileComplete: boolean;
}

export interface UseCareerCheckInResult {
  data: CareerProfileSummary | null;
  loading: boolean;
  error: boolean;
  refetch: () => void;
}

interface ProfileSummaryApiProfile {
  current_role?: string | null;
  industry?: string | null;
  seniority_level?: string | null;
  years_experience?: number | null;
  target_comp?: number | null;
  open_to_move?: boolean;
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

function mapProfile(raw: ProfileSummaryApiProfile): CareerProfileSummary {
  return {
    currentRole: raw.current_role ?? null,
    industry: raw.industry ?? null,
    seniorityLevel: raw.seniority_level ?? null,
    yearsExperience:
      typeof raw.years_experience === 'number' ? raw.years_experience : null,
    targetComp: typeof raw.target_comp === 'number' ? raw.target_comp : null,
    openToMove: Boolean(raw.open_to_move),
    profileComplete: Boolean(raw.profile_complete),
  };
}

async function fetchProfileSummary(): Promise<CareerProfileSummary> {
  const res = await fetch('/api/career/profile-summary', {
    credentials: 'include',
    headers: buildAuthHeaders(),
  });
  if (!res.ok) {
    throw new Error('Failed to load career profile summary');
  }
  const json = (await res.json()) as ProfileSummaryResponse;
  return mapProfile(json.profile ?? {});
}

const noopRefetch = () => {};

export function useCareerCheckIn(
  userEmail: string,
  userTier: 'budget' | 'mid_tier' | 'professional'
): UseCareerCheckInResult {
  const [data, setData] = useState<CareerProfileSummary | null>(null);
  const [loading, setLoading] = useState(
    userTier !== 'budget' && Boolean(userEmail.trim())
  );
  const [error, setError] = useState(false);
  const [fetchKey, setFetchKey] = useState(0);

  const refetch = useCallback(() => {
    if (userTier === 'budget') return;
    setFetchKey((k) => k + 1);
  }, [userTier]);

  useEffect(() => {
    if (userTier === 'budget') {
      setData(null);
      setLoading(false);
      setError(false);
      return;
    }

    const email = userEmail.trim();
    if (!email) {
      setData(null);
      setLoading(false);
      setError(false);
      return;
    }

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
  }, [userEmail, userTier, fetchKey]);

  if (userTier === 'budget') {
    return { data: null, loading: false, error: false, refetch: noopRefetch };
  }

  return { data, loading, error, refetch };
}
