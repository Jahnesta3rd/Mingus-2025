import { useCallback, useEffect, useState } from 'react';
import { useAuth } from './useAuth';
import { csrfHeaders } from '../utils/csrfHeaders';

export interface SpiritCheckinRow {
  id: number;
  user_id: number;
  checked_in_date: string;
  practice_type: string;
  duration_minutes: number;
  feeling_before: number | null;
  feeling_after: number;
  intention_text: string | null;
  practice_score: number;
  created_at: string | null;
}

export interface SpiritStreak {
  current_streak: number;
  longest_streak: number;
  total_checkins: number;
  last_checkin_date: string | null;
}

export interface SubmitCheckinPayload {
  practice_type: 'prayer' | 'meditation' | 'gratitude' | 'affirmation';
  duration_minutes: number;
  feeling_after: number;
  feeling_before?: number;
  intention_text?: string | null;
}

export interface SubmitCheckinResult {
  checkin: SpiritCheckinRow;
  streak: SpiritStreak;
  practice_score: number;
}

function buildHeaders(getAccessToken: () => string | null, json = false): HeadersInit {
  const h: Record<string, string> = {
    ...csrfHeaders(),
  };
  if (json) {
    h['Content-Type'] = 'application/json';
  }
  const token = getAccessToken();
  if (token) {
    h.Authorization = `Bearer ${token}`;
  }
  return h;
}

export function useSpiritCheckin() {
  const { getAccessToken, isAuthenticated } = useAuth();
  const [checkedInToday, setCheckedInToday] = useState(false);
  const [todayCheckin, setTodayCheckin] = useState<SpiritCheckinRow | null>(null);
  const [streak, setStreak] = useState<SpiritStreak | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refreshStreak = useCallback(async () => {
    const res = await fetch('/api/spirit/streak', {
      method: 'GET',
      credentials: 'include',
      headers: buildHeaders(getAccessToken),
    });
    if (!res.ok) {
      const errJson = await res.json().catch(() => ({}));
      throw new Error((errJson as { error?: string }).error || res.statusText || 'Failed to load streak');
    }
    const data = (await res.json()) as SpiritStreak;
    setStreak(data);
    return data;
  }, [getAccessToken]);

  const loadToday = useCallback(async () => {
    const res = await fetch('/api/spirit/checkin/today', {
      method: 'GET',
      credentials: 'include',
      headers: buildHeaders(getAccessToken),
    });
    if (!res.ok) {
      const errJson = await res.json().catch(() => ({}));
      throw new Error((errJson as { error?: string }).error || res.statusText || 'Failed to load today status');
    }
    const data = (await res.json()) as { checked_in: boolean; checkin?: SpiritCheckinRow };
    setCheckedInToday(data.checked_in === true);
    setTodayCheckin(data.checked_in && data.checkin ? data.checkin : null);
  }, [getAccessToken]);

  useEffect(() => {
    if (!isAuthenticated) {
      setIsLoading(false);
      setCheckedInToday(false);
      setTodayCheckin(null);
      setStreak(null);
      return;
    }

    let cancelled = false;
    setIsLoading(true);
    setError(null);

    void (async () => {
      try {
        await Promise.all([loadToday(), refreshStreak()]);
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : 'Failed to load spirit check-in');
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
  }, [isAuthenticated, loadToday, refreshStreak]);

  const submitCheckin = useCallback(
    async (payload: SubmitCheckinPayload): Promise<SubmitCheckinResult> => {
      const res = await fetch('/api/spirit/checkin', {
        method: 'POST',
        credentials: 'include',
        headers: buildHeaders(getAccessToken, true),
        body: JSON.stringify(payload),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        const msg =
          (data as { message?: string; error?: string }).message ||
          (data as { error?: string }).error ||
          res.statusText;
        throw new Error(msg || 'Check-in failed');
      }
      const result = data as SubmitCheckinResult;
      setCheckedInToday(true);
      setTodayCheckin(result.checkin);
      setStreak(result.streak);
      return result;
    },
    [getAccessToken]
  );

  return {
    checkedInToday,
    todayCheckin,
    streak,
    isLoading,
    error,
    submitCheckin,
    refreshStreak,
  };
}
