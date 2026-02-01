import { useState, useCallback, useEffect } from 'react';

/** Response from GET /api/wellness/scores/latest */
export interface WellnessScoresResponse {
  week_ending_date: string;
  physical_score: number | null;
  mental_score: number | null;
  relational_score: number | null;
  financial_feeling_score: number | null;
  overall_wellness_score: number | null;
  physical_change: number | null;
  mental_change: number | null;
  relational_change: number | null;
  overall_change: number | null;
}

/** Response from GET /api/wellness/insights */
export interface WellnessInsightsResponse {
  insights: Array<{
    type: string;
    title: string;
    message: string;
    data_backing: string;
    action: string;
    priority: number;
    category: string;
    dollar_amount?: number;
  }>;
  message?: string;
  weeks_of_data?: number;
}

/** Response from GET /api/wellness/streak */
export interface WellnessStreakResponse {
  current_streak: number;
  longest_streak: number;
  last_checkin_date: string | null;
  total_checkins: number;
}

/** Current week check-in (from GET /api/wellness/checkin/current-week) */
export interface CurrentWeekCheckinResponse {
  week_ending_date: string;
  [key: string]: unknown;
}

export interface UseWellnessDataReturn {
  scores: WellnessScoresResponse | null;
  insights: WellnessInsightsResponse['insights'];
  streak: WellnessStreakResponse | null;
  currentWeekCheckin: CurrentWeekCheckinResponse | null;
  weeksOfData: number;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

const SCORES_URL = '/api/wellness/scores/latest';
const INSIGHTS_URL = '/api/wellness/insights';
const STREAK_URL = '/api/wellness/streak';
const CURRENT_WEEK_URL = '/api/wellness/checkin/current-week';

/**
 * Fetches wellness dashboard data: scores, insights, streak, current-week check-in.
 * Refetch after check-in submission. No React Query/SWR - plain fetch with refetch.
 */
export function useWellnessData(): UseWellnessDataReturn {
  const [scores, setScores] = useState<WellnessScoresResponse | null>(null);
  const [insights, setInsights] = useState<WellnessInsightsResponse['insights']>([]);
  const [streak, setStreak] = useState<WellnessStreakResponse | null>(null);
  const [currentWeekCheckin, setCurrentWeekCheckin] = useState<CurrentWeekCheckinResponse | null>(null);
  const [weeksOfData, setWeeksOfData] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAll = useCallback(async () => {
    setError(null);
    setLoading(true);
    const opts = { credentials: 'include' as RequestCredentials };

    try {
      const [scoresRes, insightsRes, streakRes, currentRes] = await Promise.all([
        fetch(SCORES_URL, opts),
        fetch(INSIGHTS_URL, opts),
        fetch(STREAK_URL, opts),
        fetch(CURRENT_WEEK_URL, opts),
      ]);

      if (scoresRes.ok) {
        const data = await scoresRes.json();
        setScores(data);
      } else {
        setScores(null);
      }

      if (insightsRes.ok) {
        const data = await insightsRes.json();
        setInsights(data.insights ?? []);
        if (typeof data.weeks_of_data === 'number') setWeeksOfData(data.weeks_of_data);
      } else {
        setInsights([]);
      }

      if (streakRes.ok) {
        const data = await streakRes.json();
        setStreak(data);
        if (typeof data.total_checkins === 'number') setWeeksOfData(data.total_checkins);
      } else {
        setStreak(null);
      }

      if (currentRes.ok) {
        const data = await currentRes.json();
        setCurrentWeekCheckin(data);
      } else {
        setCurrentWeekCheckin(null);
      }
    } catch (e) {
      console.error('Wellness data fetch error:', e);
      setError(e instanceof Error ? e.message : 'Unable to load wellness data');
      setScores(null);
      setInsights([]);
      setStreak(null);
      setCurrentWeekCheckin(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  const refetch = useCallback(async () => {
    await fetchAll();
  }, [fetchAll]);

  return {
    scores,
    insights,
    streak,
    currentWeekCheckin,
    weeksOfData: weeksOfData || (streak?.total_checkins ?? 0),
    loading,
    error,
    refetch,
  };
}

export default useWellnessData;
