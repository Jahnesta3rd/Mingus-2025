import { useEffect, useState } from 'react';
import { csrfHeaders } from '../../../utils/csrfHeaders';

/**
 * Normalize route/state tier values to "tier1" | "tier2" | "tier3".
 * @param {string|number|undefined|null} raw
 */
export function normalizeTierKey(raw) {
  if (raw == null || raw === '') return null;
  const s = String(raw).trim().toLowerCase();
  if (s === '1' || s === 'tier1') return 'tier1';
  if (s === '2' || s === 'tier2') return 'tier2';
  if (s === '3' || s === 'tier3') return 'tier3';
  return null;
}

export function tierNumberFromKey(tierKey) {
  if (!tierKey) return 1;
  const n = Number.parseInt(String(tierKey).replace('tier', ''), 10);
  return Number.isFinite(n) ? n : 1;
}

function resolveToken(getAccessToken) {
  const fromAuth = getAccessToken?.();
  if (fromAuth) return fromAuth;
  const fromStorage = localStorage.getItem('mingus_token');
  if (fromStorage) return fromStorage;
  const cookies = document.cookie.split('; ');
  const tokenCookie = cookies.find((row) => row.startsWith('mingus_token='));
  return tokenCookie?.split('=')[1] || null;
}

function messageForStatus(status) {
  if (status === 401) return 'Not logged in. Please log in and try again.';
  if (status === 404) {
    return 'Recommendations not found. Have you completed the plan?';
  }
  if (status === 400) {
    return 'Could not build recommendations for this tier. Check that a purchase plan exists.';
  }
  if (status === 500) return 'Server error. Please try again later.';
  return `Failed to load recommendations (${status})`;
}

/**
 * Fetch BTS5 product recommendations for a session + tier.
 *
 * @param {string|null|undefined} sessionId
 * @param {string|number|null|undefined} tier
 * @param {{ getAccessToken?: () => string|null }} [options]
 */
export function useProductRecommendations(sessionId, tier, options = {}) {
  const [recommendations, setRecommendations] = useState(null);
  const [loading, setLoading] = useState(Boolean(sessionId && tier));
  const [error, setError] = useState(null);

  const tierKey = normalizeTierKey(tier);

  useEffect(() => {
    if (!sessionId || !tierKey) {
      setRecommendations(null);
      setError(!sessionId ? 'Session ID is required' : 'Invalid tier');
      setLoading(false);
      return undefined;
    }

    let cancelled = false;

    async function fetchRecommendations() {
      setLoading(true);
      setError(null);

      try {
        const token = resolveToken(options.getAccessToken);
        if (!token) {
          if (!cancelled) {
            setError('Not logged in. Please log in first.');
            setRecommendations(null);
            setLoading(false);
          }
          return;
        }

        const response = await fetch(`/api/bts/recommendations/${tierKey}`, {
          method: 'POST',
          credentials: 'include',
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
            ...csrfHeaders(),
          },
          body: JSON.stringify({ sessionId, tier: tierKey }),
        });

        if (!response.ok) {
          throw new Error(messageForStatus(response.status));
        }

        const data = await response.json();
        if (!data?.recommendations || !data?.summary) {
          throw new Error('Invalid recommendation structure');
        }

        if (!cancelled) {
          setRecommendations(data);
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setRecommendations(null);
          setError(err instanceof Error ? err.message : 'Unknown error');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    fetchRecommendations();
    return () => {
      cancelled = true;
    };
  }, [sessionId, tierKey, options.getAccessToken]);

  return { recommendations, loading, error, tierKey };
}

export { resolveToken };
export default useProductRecommendations;
