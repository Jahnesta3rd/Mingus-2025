/**
 * useWellnessData hook tests.
 * - Data fetching (scores, insights, streak, current-week)
 * - Loading and then data
 * - Refetch
 * - Error states
 */

import { renderHook, waitFor, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import { useWellnessData } from '../useWellnessData';

const mockFetch = global.fetch as jest.Mock;

const mockScores = {
  week_ending_date: '2025-02-02',
  physical_score: 70,
  mental_score: 75,
  relational_score: 65,
  financial_feeling_score: 72,
  overall_wellness_score: 71,
  physical_change: 5,
  mental_change: -2,
  relational_change: 0,
  overall_change: 3,
};

const mockInsights = {
  insights: [
    { type: 'correlation', title: 'Stress & Spending', message: 'Pattern.', data_backing: '8 weeks', action: 'Consider pause.', priority: 2, category: 'financial' },
  ],
  weeks_of_data: 6,
};

const mockStreak = {
  current_streak: 3,
  longest_streak: 5,
  last_checkin_date: '2025-01-26',
  total_checkins: 12,
};

const mockCurrentWeek = { week_ending_date: '2025-02-02' };

function mockAllOk() {
  mockFetch
    .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(mockScores) })
    .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(mockInsights) })
    .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(mockStreak) })
    .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(mockCurrentWeek) });
}

beforeEach(() => {
  mockFetch.mockReset();
});

describe('useWellnessData', () => {
  describe('data fetching', () => {
    it('starts with loading true then returns data', async () => {
      mockAllOk();
      const { result } = renderHook(() => useWellnessData());
      expect(result.current.loading).toBe(true);
      expect(result.current.scores).toBeNull();
      expect(result.current.error).toBeNull();

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });
      expect(result.current.scores).toEqual(mockScores);
      expect(result.current.insights).toEqual(mockInsights.insights);
      expect(result.current.streak).toEqual(mockStreak);
      expect(result.current.currentWeekCheckin).toEqual(mockCurrentWeek);
      expect(result.current.weeksOfData).toBeGreaterThanOrEqual(0);
      expect(result.current.error).toBeNull();
    });

    it('calls all four API endpoints', async () => {
      mockAllOk();
      renderHook(() => useWellnessData());
      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith('/api/wellness/scores/latest', expect.any(Object));
        expect(mockFetch).toHaveBeenCalledWith('/api/wellness/insights', expect.any(Object));
        expect(mockFetch).toHaveBeenCalledWith('/api/wellness/streak', expect.any(Object));
        expect(mockFetch).toHaveBeenCalledWith('/api/wellness/checkin/current-week', expect.any(Object));
      });
    });
  });

  describe('refetch', () => {
    it('refetch calls fetch again', async () => {
      mockAllOk();
      mockAllOk();
      const { result } = renderHook(() => useWellnessData());
      await waitFor(() => expect(result.current.loading).toBe(false));
      const firstCallCount = mockFetch.mock.calls.length;
      await act(async () => {
        await result.current.refetch();
      });
      expect(mockFetch.mock.calls.length).toBeGreaterThan(firstCallCount);
    });
  });

  describe('error states', () => {
    it('sets error when fetch throws', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'));
      const { result } = renderHook(() => useWellnessData());
      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });
      expect(result.current.error).toMatch(/network error|unable to load wellness data/i);
      expect(result.current.scores).toBeNull();
      expect(result.current.insights).toEqual([]);
    });

    it('handles non-ok responses without throwing', async () => {
      mockFetch
        .mockResolvedValueOnce({ ok: false })
        .mockResolvedValueOnce({ ok: false })
        .mockResolvedValueOnce({ ok: false })
        .mockResolvedValueOnce({ ok: false });
      const { result } = renderHook(() => useWellnessData());
      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });
      expect(result.current.scores).toBeNull();
      expect(result.current.insights).toEqual([]);
      expect(result.current.streak).toBeNull();
      expect(result.current.currentWeekCheckin).toBeNull();
    });
  });

  describe('return shape', () => {
    it('returns refetch function', async () => {
      mockAllOk();
      const { result } = renderHook(() => useWellnessData());
      expect(typeof result.current.refetch).toBe('function');
      await waitFor(() => expect(result.current.loading).toBe(false));
      expect(typeof result.current.refetch).toBe('function');
    });

    it('weeksOfData falls back to streak.total_checkins', async () => {
      mockFetch
        .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(mockScores) })
        .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve({ insights: [], weeks_of_data: undefined }) })
        .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(mockStreak) })
        .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(mockCurrentWeek) });
      const { result } = renderHook(() => useWellnessData());
      await waitFor(() => expect(result.current.loading).toBe(false));
      expect(result.current.weeksOfData).toBe(mockStreak.total_checkins);
    });
  });
});
