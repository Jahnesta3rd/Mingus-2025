import { useEffect, useState } from 'react';
import { csrfHeaders } from '../../../utils/csrfHeaders';

/**
 * @typedef {Object} TierItem
 * @property {string} category
 * @property {number} quantity
 * @property {number} estimatedCost
 * @property {string} [priority]
 * @property {string} [note]
 */

/**
 * @typedef {Object} TierBlock
 * @property {number} budget
 * @property {string} purchaseBy
 * @property {string} [justification]
 * @property {string} [contingency]
 * @property {TierItem[]} items
 * @property {number} totalEstimated
 * @property {number} remaining
 */

/**
 * @typedef {Object} PurchasePlan
 * @property {string} [sessionId]
 * @property {TierBlock} tier1
 * @property {TierBlock} tier2
 * @property {TierBlock} tier3
 * @property {{
 *   totalBudgetAvailable: number,
 *   totalEstimatedSpend: number,
 *   bufferRemaining: number,
 *   jobDependent?: boolean,
 *   jobEarningsRequired?: number,
 *   fallbackIfJobFails?: string,
 * }} summary
 * @property {string[]} [warnings]
 */

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
    return 'Plan not found. Have you completed the plan generation?';
  }
  if (status === 500) return 'Server error. Please try again later.';
  return `Failed to load plan (${status})`;
}

/**
 * Fetch BTS2 purchase plan for a session.
 *
 * @param {string|null|undefined} sessionId
 * @param {{ getAccessToken?: () => string|null }} [options]
 */
export function usePurchasePlan(sessionId, options = {}) {
  const [plan, setPlan] = useState(null);
  const [loading, setLoading] = useState(Boolean(sessionId));
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!sessionId) {
      setPlan(null);
      setError('Session ID is required');
      setLoading(false);
      return undefined;
    }

    let cancelled = false;

    async function fetchPlan() {
      setLoading(true);
      setError(null);

      try {
        const token = resolveToken(options.getAccessToken);
        if (!token) {
          if (!cancelled) {
            setError('Not logged in. Please log in first.');
            setPlan(null);
            setLoading(false);
          }
          return;
        }

        const response = await fetch(`/api/bts/purchase-plan/${encodeURIComponent(sessionId)}`, {
          method: 'GET',
          credentials: 'include',
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
            ...csrfHeaders(),
          },
        });

        if (!response.ok) {
          throw new Error(messageForStatus(response.status));
        }

        const data = await response.json();
        // Support both flattened BTS2 shape and legacy { plan: { planData } }.
        const normalized =
          data?.tier1 && data?.tier2 && data?.tier3
            ? data
            : data?.plan?.planData?.tier1
              ? {
                  status: 'success',
                  sessionId: data.plan.sessionId,
                  ...data.plan.planData,
                }
              : null;

        if (!normalized?.tier1 || !normalized?.tier2 || !normalized?.tier3) {
          throw new Error('Invalid plan structure from server');
        }

        if (!cancelled) {
          setPlan(normalized);
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setPlan(null);
          setError(err instanceof Error ? err.message : 'Unknown error occurred');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    fetchPlan();
    return () => {
      cancelled = true;
    };
  }, [sessionId, options.getAccessToken]);

  return { plan, loading, error };
}

export default usePurchasePlan;
