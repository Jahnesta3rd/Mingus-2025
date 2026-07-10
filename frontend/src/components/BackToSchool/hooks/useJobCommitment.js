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

async function parseError(response, fallback) {
  try {
    const body = await response.json();
    return body?.error || fallback;
  } catch {
    return fallback;
  }
}

/**
 * Fetch + manage BTS7 job commitment for a session.
 *
 * @param {string|null|undefined} sessionId
 * @param {{ getAccessToken?: () => string|null }} [options]
 */
export function useJobCommitment(sessionId, options = {}) {
  const [commitment, setCommitment] = useState(null);
  const [tier2Status, setTier2Status] = useState(null);
  const [loading, setLoading] = useState(Boolean(sessionId));
  const [error, setError] = useState(null);

  const fetchCommitment = useCallback(async () => {
    if (!sessionId) return null;
    try {
      const token = resolveToken(options.getAccessToken);
      if (!token) {
        setError('Not logged in. Please log in first.');
        setCommitment(null);
        return null;
      }

      const response = await fetch(
        `/api/bts/job-commitment/${encodeURIComponent(sessionId)}`,
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
        throw new Error(await parseError(response, 'Failed to fetch commitment'));
      }

      const data = await response.json();
      if (data?.status === 'no_commitment') {
        setCommitment(null);
        return null;
      }
      setCommitment(data);
      setError(null);
      return data;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch commitment');
      return null;
    }
  }, [sessionId, options.getAccessToken]);

  const fetchTier2Status = useCallback(async () => {
    if (!sessionId) return null;
    try {
      const token = resolveToken(options.getAccessToken);
      if (!token) return null;

      const response = await fetch(
        `/api/bts/tier2-status/${encodeURIComponent(sessionId)}`,
        {
          method: 'GET',
          credentials: 'include',
          headers: {
            Authorization: `Bearer ${token}`,
            ...csrfHeaders(),
          },
        },
      );

      if (!response.ok) return null;
      const data = await response.json();
      setTier2Status(data);
      return data;
    } catch {
      return null;
    }
  }, [sessionId, options.getAccessToken]);

  const createCommitment = async ({
    jobId,
    jobTitle,
    tier2Date,
    tier2BaseBudget,
    targetEarnings,
  }) => {
    setLoading(true);
    setError(null);
    try {
      const token = resolveToken(options.getAccessToken);
      if (!token) throw new Error('Not logged in. Please log in and try again.');

      const response = await fetch('/api/bts/job-commitment', {
        method: 'POST',
        credentials: 'include',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
          ...csrfHeaders(),
        },
        body: JSON.stringify({
          sessionId,
          jobId,
          jobTitle,
          tier2Date,
          tier2BaseBudget,
          targetEarnings,
        }),
      });

      if (!response.ok) {
        throw new Error(await parseError(response, 'Failed to create commitment'));
      }

      const data = await response.json();
      setCommitment(data);
      await fetchTier2Status();
      return data;
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Failed to create commitment';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const recordDecision = async (decision) => {
    setLoading(true);
    setError(null);
    try {
      const token = resolveToken(options.getAccessToken);
      if (!token) throw new Error('Not logged in. Please log in and try again.');

      const response = await fetch(
        `/api/bts/tier2-decision/${encodeURIComponent(sessionId)}`,
        {
          method: 'POST',
          credentials: 'include',
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
            ...csrfHeaders(),
          },
          body: JSON.stringify({ decision }),
        },
      );

      if (!response.ok) {
        throw new Error(await parseError(response, 'Failed to record decision'));
      }

      const data = await response.json();
      if (data?.commitment) setCommitment(data.commitment);
      await fetchTier2Status();
      return data;
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Failed to record decision';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!sessionId) {
      setCommitment(null);
      setTier2Status(null);
      setLoading(false);
      return undefined;
    }

    let cancelled = false;
    (async () => {
      setLoading(true);
      await fetchCommitment();
      await fetchTier2Status();
      if (!cancelled) setLoading(false);
    })();

    const interval = setInterval(() => {
      fetchCommitment();
      fetchTier2Status();
    }, 30000);

    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [sessionId, fetchCommitment, fetchTier2Status]);

  return {
    commitment,
    tier2Status,
    loading,
    error,
    setError,
    createCommitment,
    fetchCommitment,
    fetchTier2Status,
    recordDecision,
  };
}

export default useJobCommitment;
