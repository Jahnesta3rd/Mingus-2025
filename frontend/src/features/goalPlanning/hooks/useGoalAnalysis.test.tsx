import React from 'react';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useGoalAnalysis, mapEnrichmentToPaths, clearGoalAnalysisCache } from './useGoalAnalysis';

jest.mock('../services/goalPlanningApi.js', () => ({
  fetchGoalPlanningAnalysis: jest.fn(),
}));

jest.mock('../services/goalPlanningPipeline.js', () => ({
  runGoalPlanningPipeline: jest.fn(),
}));

import { fetchGoalPlanningAnalysis } from '../services/goalPlanningApi.js';
import { runGoalPlanningPipeline } from '../services/goalPlanningPipeline.js';

const mockedFetchBackend = fetchGoalPlanningAnalysis as jest.MockedFunction<typeof fetchGoalPlanningAnalysis>;
const mockedRunPipeline = runGoalPlanningPipeline as jest.MockedFunction<typeof runGoalPlanningPipeline>;

const userProfile = {
  id: 'user-1',
  income: 8000,
  savings: 25000,
  expenses: 5200,
  jobTitle: 'Software Engineer',
  industry: 'Technology',
  skills: ['JavaScript', 'React'],
  availableHours: 10,
};

const goal = {
  type: 'home_purchase',
  parameters: { homePrice: 400000 },
  timeline: 5,
};

const mockAnalysis = {
  goalId: 'goal-1',
  goalType: 'home_purchase',
  gaps: {
    savingsGap: 395000,
    incomeGap: 24000,
    monthlyToSave: 6583.33,
    feasible: false,
  },
  futureState: { timelineYears: 5 },
};

const mockPaths = [
  { pathId: 'career_advancement', title: 'Career Advancement', monthlyBoost: 1500 },
  { pathId: 'side_income', title: 'Side Income', monthlyBoost: 1000 },
  { pathId: 'combined', title: 'RECOMMENDED - Combined Strategy', monthlyBoost: 2200, mostRealistic: true },
  { pathId: 'alternative', title: 'Faster Alternative', monthlyBoost: 0 },
];

const pipelineResult = {
  goalAnalysis: mockAnalysis,
  recommendations: {
    paths: mockPaths,
    selectedPath: 'combined',
    source: 'fallback',
    generatedAt: '2026-07-07T00:00:00.000Z',
  },
  jobSuggestions: {
    global: { jobs: [{ jobId: 'job-1', title: 'Senior Engineer' }], source: 'knowledge_base' },
    byPathId: { career_advancement: { jobs: [{ jobId: 'job-1' }], source: 'knowledge_base' } },
  },
  gigSuggestions: {
    global: { gigs: [{ gigId: 'gig-1', title: 'Freelance React' }], source: 'knowledge_base' },
    byPathId: { side_income: { gigs: [{ gigId: 'gig-1' }], source: 'knowledge_base' } },
  },
  expenseSuggestions: {
    global: { suggestions: [{ suggestionId: 'cut-1' }], source: 'knowledge_base', cumulativeSavings: 400 },
    byPathId: { combined: { suggestions: [{ suggestionId: 'cut-1' }], source: 'knowledge_base' } },
  },
  partialErrors: [],
};

describe('mapEnrichmentToPaths', () => {
  it('maps global enrichment data onto relevant paths', () => {
    const mapped = mapEnrichmentToPaths(
      mockPaths,
      { jobs: [{ jobId: 'job-1' }], source: 'knowledge_base' },
      { gigs: [{ gigId: 'gig-1' }], source: 'knowledge_base' },
      { suggestions: [{ suggestionId: 'cut-1' }], source: 'knowledge_base', cumulativeSavings: 400 },
    );

    expect(mapped.jobByPathId.career_advancement?.jobs).toHaveLength(1);
    expect(mapped.gigByPathId.side_income?.gigs).toHaveLength(1);
    expect(mapped.expenseByPathId.combined?.suggestions).toHaveLength(1);
    expect(mapped.expenseByPathId.alternative?.suggestions).toHaveLength(1);
  });
});

describe('useGoalAnalysis', () => {
  beforeEach(() => {
    clearGoalAnalysisCache();
    jest.clearAllMocks();
    mockedFetchBackend.mockResolvedValue(pipelineResult);
    mockedRunPipeline.mockResolvedValue(pipelineResult);
  });

  it('starts in idle state', () => {
    const { result } = renderHook(() => useGoalAnalysis(userProfile));
    expect(result.current.status).toBe('idle');
    expect(result.current.goalAnalysis).toBeNull();
    expect(result.current.recommendations.paths).toEqual([]);
  });

  it('orchestrates analysis through backend when proxy is enabled', async () => {
    const onStatusChange = jest.fn();
    const { result } = renderHook(() => useGoalAnalysis(userProfile, {
      debounceMs: 0,
      onStatusChange,
      getAccessToken: () => 'token',
    }));

    await act(async () => {
      await result.current.analyzeGoal(goal);
    });

    await waitFor(() => {
      expect(result.current.status).toBe('complete');
    });

    expect(mockedFetchBackend).toHaveBeenCalledWith({
      goal,
      userProfile,
      getAccessToken: expect.any(Function),
      fetchFn: undefined,
    });
    expect(mockedRunPipeline).not.toHaveBeenCalled();
    expect(result.current.goalAnalysis?.goalType).toBe('home_purchase');
    expect(result.current.recommendations.paths).toHaveLength(4);
    expect(result.current.recommendations.selectedPath).toBe('combined');
    expect(result.current.jobSuggestions.global?.jobs).toHaveLength(1);
    expect(onStatusChange).toHaveBeenCalledWith('complete', expect.any(Object));
  });

  it('falls back to client pipeline when backend fails', async () => {
    mockedFetchBackend.mockRejectedValue(new Error('backend down'));

    const { result } = renderHook(() => useGoalAnalysis(userProfile, {
      debounceMs: 0,
      enableCache: false,
    }));

    await act(async () => {
      await result.current.analyzeGoal(goal);
    });

    await waitFor(() => expect(result.current.status).toBe('complete'));
    expect(mockedRunPipeline).toHaveBeenCalled();
    expect(result.current.error).toContain('Backend unavailable');
  });

  it('uses client pipeline when backend proxy is disabled', async () => {
    const { result } = renderHook(() => useGoalAnalysis(userProfile, {
      debounceMs: 0,
      useBackendProxy: false,
    }));

    await act(async () => {
      await result.current.analyzeGoal(goal);
    });

    await waitFor(() => expect(result.current.status).toBe('complete'));
    expect(mockedFetchBackend).not.toHaveBeenCalled();
    expect(mockedRunPipeline).toHaveBeenCalled();
  });

  it('caches analysis results for identical goals', async () => {
    const { result } = renderHook(() => useGoalAnalysis(userProfile, { debounceMs: 0 }));

    await act(async () => {
      await result.current.analyzeGoal(goal);
    });

    await waitFor(() => expect(result.current.status).toBe('complete'));

    jest.clearAllMocks();

    await act(async () => {
      await result.current.analyzeGoal(goal);
    });

    await waitFor(() => expect(result.current.status).toBe('complete'));
    expect(mockedFetchBackend).not.toHaveBeenCalled();
    expect(mockedRunPipeline).not.toHaveBeenCalled();
  });

  it('continues with partial results when enrichment services fail', async () => {
    mockedRunPipeline.mockResolvedValue({
      ...pipelineResult,
      partialErrors: ['Job suggestions unavailable: jobs down'],
    });
    mockedFetchBackend.mockRejectedValue(new Error('backend down'));

    const { result } = renderHook(() => useGoalAnalysis(userProfile, {
      debounceMs: 0,
      enableCache: false,
    }));

    await act(async () => {
      await result.current.analyzeGoal(goal);
    });

    await waitFor(() => expect(result.current.status).toBe('complete'));
    expect(result.current.recommendations.paths.length).toBeGreaterThan(0);
    expect(result.current.error).toContain('Job suggestions unavailable');
  });

  it('sets error state when goal analysis fails', async () => {
    mockedFetchBackend.mockRejectedValue(new Error('backend down'));
    mockedRunPipeline.mockRejectedValue(new Error('Unable to analyze goal'));

    const { result } = renderHook(() => useGoalAnalysis(userProfile, {
      debounceMs: 0,
      enableCache: false,
    }));

    await act(async () => {
      await result.current.analyzeGoal(goal);
    });

    await waitFor(() => expect(result.current.status).toBe('error'));
    expect(result.current.error).toContain('Unable to analyze goal');
  });

  it('supports selecting a recommendation path and clearing analysis', async () => {
    const { result } = renderHook(() => useGoalAnalysis(userProfile, { debounceMs: 0 }));

    await act(async () => {
      await result.current.analyzeGoal(goal);
    });
    await waitFor(() => expect(result.current.status).toBe('complete'));

    act(() => {
      result.current.selectRecommendationPath('side_income');
    });
    expect(result.current.recommendations.selectedPath).toBe('side_income');

    act(() => {
      result.current.clearAnalysis();
    });
    expect(result.current.status).toBe('idle');
    expect(result.current.goalAnalysis).toBeNull();
  });

  it('debounces rapid analyzeGoal calls', async () => {
    jest.useFakeTimers();
    const { result } = renderHook(() => useGoalAnalysis(userProfile, { debounceMs: 300 }));

    act(() => {
      result.current.analyzeGoal(goal);
      result.current.analyzeGoal({ ...goal, timeline: 6 });
    });

    expect(mockedFetchBackend).not.toHaveBeenCalled();

    await act(async () => {
      jest.advanceTimersByTime(300);
    });

    await waitFor(() => expect(mockedFetchBackend).toHaveBeenCalledTimes(1));
    expect(mockedFetchBackend).toHaveBeenCalledWith(expect.objectContaining({
      goal: { ...goal, timeline: 6 },
    }));

    jest.useRealTimers();
  });
});
