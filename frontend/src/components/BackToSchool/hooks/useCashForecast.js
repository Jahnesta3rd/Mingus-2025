import { useCallback, useEffect, useState } from 'react';
import {
  getForecastTimeline,
  setupBtsDate,
} from '../../api/bts-orchestrator-api';

/**
 * Fetch BTS setup + forecast timeline for a given school start date.
 *
 * @param {{
 *   userId: string,
 *   btsDate: string|null,
 *   childName?: string,
 *   childAge?: number|null,
 *   childGender?: string,
 *   enabled?: boolean,
 *   getAccessToken?: () => string|null,
 * }} options
 */
export function useCashForecast({
  userId,
  btsDate,
  childName,
  childAge,
  childGender,
  enabled = true,
  getAccessToken,
}) {
  const [setup, setSetup] = useState(null);
  const [timeline, setTimeline] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [fetchKey, setFetchKey] = useState(0);

  const refetch = useCallback(() => {
    setFetchKey((k) => k + 1);
  }, []);

  useEffect(() => {
    if (!enabled || !userId || !btsDate) {
      setSetup(null);
      setTimeline(null);
      setLoading(false);
      setError(null);
      return undefined;
    }

    let cancelled = false;
    setLoading(true);
    setError(null);

    const opts = { getAccessToken };

    Promise.all([
      setupBtsDate(
        {
          userId,
          btsDate,
          childName,
          childAge: childAge ?? undefined,
          childGender,
        },
        opts,
      ),
      getForecastTimeline(userId, btsDate, opts),
    ])
      .then(([setupResult, timelineResult]) => {
        if (cancelled) return;
        setSetup(setupResult);
        setTimeline(timelineResult);
      })
      .catch((err) => {
        if (cancelled) return;
        setSetup(null);
        setTimeline(null);
        setError(err instanceof Error ? err.message : 'Failed to load forecast');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [
    userId,
    btsDate,
    childName,
    childAge,
    childGender,
    enabled,
    getAccessToken,
    fetchKey,
  ]);

  return {
    setup,
    timeline,
    loading,
    error,
    refetch,
    tier1Balance: setup?.availableBalances?.tier1?.forecastedBalance ?? null,
    shortfall: setup?.shortfall ?? 0,
    daysUntilSchool: setup?.daysUntilSchool ?? null,
  };
}

export default useCashForecast;
