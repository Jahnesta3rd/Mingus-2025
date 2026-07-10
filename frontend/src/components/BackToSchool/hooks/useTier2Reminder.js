import { useCallback, useEffect, useState } from 'react';
import { csrfHeaders } from '../../../utils/csrfHeaders';

function resolveToken(getAccessToken) {
  const fromAuth = getAccessToken?.();
  if (fromAuth) return fromAuth;
  return (
    localStorage.getItem('auth_token') ||
    localStorage.getItem('mingus_token') ||
    null
  );
}

/**
 * Fetch + dismiss Tier 2 reminder banner state (BTS8).
 *
 * @param {string|null|undefined} sessionId
 * @param {{ getAccessToken?: () => string|null, tier2Date?: string|null }} [options]
 */
export function useTier2Reminder(sessionId, options = {}) {
  const [shouldShow, setShouldShow] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [reminder, setReminder] = useState(null);

  const fetchReminder = useCallback(async () => {
    if (!sessionId) {
      setShouldShow(false);
      setReminder(null);
      return null;
    }

    try {
      const token = resolveToken(options.getAccessToken);
      if (!token) {
        setError('Not logged in. Please log in first.');
        setShouldShow(false);
        return null;
      }

      const response = await fetch(
        `/api/bts/tier2-reminder/${encodeURIComponent(sessionId)}`,
        {
          method: 'GET',
          credentials: 'include',
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
            ...csrfHeaders(),
          },
        },
      );

      if (!response.ok) {
        setShouldShow(false);
        return null;
      }

      const data = await response.json();
      setReminder(data);
      setError(null);

      // Prefer server flag; also enforce local date gate as a safety net
      let show = Boolean(data.shouldShowTier2Reminder);
      const tier2Date = data.tier2Date || options.tier2Date;
      if (show && tier2Date) {
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        const tier2Day = new Date(`${String(tier2Date).slice(0, 10)}T00:00:00`);
        if (Number.isNaN(tier2Day.getTime()) || today < tier2Day) {
          show = false;
        }
      }
      setShouldShow(show);
      return data;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to check reminder');
      setShouldShow(false);
      return null;
    }
  }, [sessionId, options.getAccessToken, options.tier2Date]);

  const dismissReminder = async () => {
    if (!sessionId) return false;
    setLoading(true);
    setError(null);
    try {
      const token = resolveToken(options.getAccessToken);
      if (!token) throw new Error('Not logged in. Please log in and try again.');

      const response = await fetch(
        `/api/bts/dismiss-tier2-reminder/${encodeURIComponent(sessionId)}`,
        {
          method: 'POST',
          credentials: 'include',
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
            ...csrfHeaders(),
          },
          body: JSON.stringify({}),
        },
      );

      if (!response.ok) {
        let message = 'Failed to dismiss reminder';
        try {
          const body = await response.json();
          message = body?.error || message;
        } catch {
          /* ignore */
        }
        throw new Error(message);
      }

      setShouldShow(false);
      setReminder((prev) =>
        prev
          ? {
              ...prev,
              tier2ReminderDismissed: true,
              shouldShowTier2Reminder: false,
            }
          : prev,
      );
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to dismiss reminder');
      return false;
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReminder();
  }, [fetchReminder]);

  return {
    shouldShow,
    dismissReminder,
    loading,
    error,
    reminder,
    refresh: fetchReminder,
  };
}

export default useTier2Reminder;
