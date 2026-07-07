import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { fetchGoalPlanningAnalysis } from '../services/goalPlanningApi.js';
import { runGoalPlanningPipeline } from '../services/goalPlanningPipeline.js';

export { mapEnrichmentToPaths } from '../utils/goalPlanningEnrichment.js';

/**
 * @typedef {'idle' | 'analyzing' | 'generating' | 'enriching' | 'complete' | 'error'} GoalAnalysisStatus
 */

/**
 * @typedef {Object} UseGoalAnalysisOptions
 * @property {boolean} [enableCache=true]
 * @property {boolean} [useBackendProxy=true]
 * @property {() => string | null} [getAccessToken]
 * @property {number} [debounceMs]
 * @property {number} [timeoutMs]
 * @property {number} [llmRetries]
 * @property {(prompt: string, opts?: object) => Promise<string | null>} [llmClient]
 * @property {typeof fetch} [fetchFn]
 * @property {string} [apiKey]
 * @property {(status: GoalAnalysisStatus, meta?: Record<string, unknown>) => void} [onStatusChange]
 */

const DEFAULT_DEBOUNCE_MS = 300;
const DEFAULT_TIMEOUT_MS = 30000;
const DEFAULT_LLM_RETRIES = 2;
const MAX_CACHE_ENTRIES = 20;

const analysisCache = new Map();

/**
 * Clears in-memory goal analysis cache (primarily for tests).
 */
export function clearGoalAnalysisCache() {
  analysisCache.clear();
}

/**
 * @param {unknown} value
 * @returns {string}
 */
function stableSerialize(value) {
  try {
    return JSON.stringify(value);
  } catch {
    return String(value);
  }
}

/**
 * @param {Record<string, unknown> | null | undefined} userProfile
 * @param {object} goal
 * @returns {string}
 */
function buildCacheKey(userProfile, goal) {
  return stableSerialize({
    userId: userProfile?.id ?? 'anonymous',
    goalType: goal?.type,
    parameters: goal?.parameters ?? {},
    timeline: goal?.timeline,
  });
}

/**
 * @param {*} result
 * @returns {boolean}
 */
function isCompleteAnalysisResult(result) {
  return Boolean(result?.goalAnalysis && result?.recommendations);
}

/**
 * Stores analysis result in LRU-style cache.
 * @param {string} cacheKey
 * @param {*} result
 */
function writeCache(cacheKey, result) {
  if (analysisCache.has(cacheKey)) {
    analysisCache.delete(cacheKey);
  }
  analysisCache.set(cacheKey, result);
  if (analysisCache.size > MAX_CACHE_ENTRIES) {
    const oldestKey = analysisCache.keys().next().value;
    analysisCache.delete(oldestKey);
  }
}

/**
 * @param {*} result
 * @param {number} requestId
 */
function applyAnalysisResult(result, requestId, requestIdRef, mountedRef, setters, updateStatus) {
  const {
    setGoalAnalysis,
    setRecommendations,
    setJobSuggestions,
    setGigSuggestions,
    setExpenseSuggestions,
    setError,
    setProgress,
  } = setters;

  if (requestId !== requestIdRef.current || !mountedRef.current) {
    return null;
  }

  setGoalAnalysis(result.goalAnalysis);
  setRecommendations(result.recommendations);
  setJobSuggestions(result.jobSuggestions);
  setGigSuggestions(result.gigSuggestions);
  setExpenseSuggestions(result.expenseSuggestions);

  const partialErrors = result.partialErrors ?? [];
  setError(partialErrors.length > 0 ? partialErrors.join('; ') : null);
  setProgress('Analysis complete');
  updateStatus('complete', { partialErrors: partialErrors.length, source: result.source });

  return result;
}

/**
 * Orchestrates goal analysis, recommendations, and enrichment services.
 * @param {Record<string, unknown> | null | undefined} userProfile
 * @param {UseGoalAnalysisOptions} [options]
 */
export function useGoalAnalysis(userProfile, options = {}) {
  const {
    enableCache = true,
    useBackendProxy = true,
    getAccessToken,
    debounceMs = DEFAULT_DEBOUNCE_MS,
    timeoutMs = DEFAULT_TIMEOUT_MS,
    llmRetries = DEFAULT_LLM_RETRIES,
    llmClient,
    onStatusChange,
  } = options;

  const [status, setStatus] = useState('idle');
  const [goalAnalysis, setGoalAnalysis] = useState(null);
  const [recommendations, setRecommendations] = useState({
    paths: [],
    selectedPath: null,
    source: null,
    generatedAt: null,
  });
  const [jobSuggestions, setJobSuggestions] = useState({ global: null, byPathId: {} });
  const [gigSuggestions, setGigSuggestions] = useState({ global: null, byPathId: {} });
  const [expenseSuggestions, setExpenseSuggestions] = useState({ global: null, byPathId: {} });
  const [error, setError] = useState(null);
  const [progress, setProgress] = useState(null);

  const mountedRef = useRef(true);
  const requestIdRef = useRef(0);
  const debounceTimerRef = useRef(null);
  const inFlightRef = useRef(null);

  const serviceOptions = useMemo(
    () => ({ llmClient, fetchFn: options.fetchFn, apiKey: options.apiKey }),
    [llmClient, options.fetchFn, options.apiKey],
  );

  const setters = useMemo(
    () => ({
      setGoalAnalysis,
      setRecommendations,
      setJobSuggestions,
      setGigSuggestions,
      setExpenseSuggestions,
      setError,
      setProgress,
    }),
    [],
  );

  const updateStatus = useCallback((nextStatus, meta) => {
    if (!mountedRef.current) {
      return;
    }
    setStatus(nextStatus);
    onStatusChange?.(nextStatus, meta);
  }, [onStatusChange]);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
      requestIdRef.current += 1;
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, []);

  const clearAnalysis = useCallback(() => {
    requestIdRef.current += 1;
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
      debounceTimerRef.current = null;
    }
    setStatus('idle');
    setGoalAnalysis(null);
    setRecommendations({ paths: [], selectedPath: null, source: null, generatedAt: null });
    setJobSuggestions({ global: null, byPathId: {} });
    setGigSuggestions({ global: null, byPathId: {} });
    setExpenseSuggestions({ global: null, byPathId: {} });
    setError(null);
    setProgress(null);
  }, []);

  const selectRecommendationPath = useCallback((pathId) => {
    setRecommendations((prev) => ({
      ...prev,
      selectedPath: pathId,
    }));
  }, []);

  const runClientPipeline = useCallback(async (goal, requestId) => {
    updateStatus('analyzing', { phase: 'goal_analysis' });
    setProgress('Analyzing goal gaps and feasibility');

    const result = await runGoalPlanningPipeline(userProfile, goal, {
      ...serviceOptions,
      llmRetries,
      timeoutMs,
      onProgress: (phase, message) => {
        if (requestId !== requestIdRef.current || !mountedRef.current) {
          return;
        }
        if (phase === 'generating') {
          updateStatus('generating', { phase: 'recommendations' });
        } else if (phase === 'enriching') {
          updateStatus('enriching', { phase: 'enrichment' });
        } else {
          updateStatus('analyzing', { phase: 'goal_analysis' });
        }
        setProgress(message);
      },
    });

    return { ...result, source: 'client' };
  }, [llmRetries, serviceOptions, timeoutMs, updateStatus, userProfile]);

  const runPipeline = useCallback(async (goal, requestId) => {
    if (!userProfile || !goal) {
      throw new Error('User profile and goal are required.');
    }

    const cacheKey = buildCacheKey(userProfile, goal);
    if (enableCache && analysisCache.has(cacheKey)) {
      const cached = analysisCache.get(cacheKey);
      if (isCompleteAnalysisResult(cached) && requestId === requestIdRef.current) {
        applyAnalysisResult(
          cached,
          requestId,
          requestIdRef,
          mountedRef,
          setters,
          updateStatus,
        );
        setProgress('Loaded cached analysis');
        updateStatus('complete', { cached: true });
        return cached;
      }
    }

    let result = null;

    if (useBackendProxy) {
      updateStatus('analyzing', { phase: 'backend_proxy' });
      setProgress('Analyzing your goal on secure servers');

      try {
        result = await fetchGoalPlanningAnalysis({
          goal,
          userProfile,
          getAccessToken,
          fetchFn: options.fetchFn,
        });
        result = { ...result, source: 'backend' };
      } catch (backendError) {
        if (requestId !== requestIdRef.current || !mountedRef.current) {
          return null;
        }
        result = await runClientPipeline(goal, requestId);
        result = {
          ...result,
          source: 'client_fallback',
          partialErrors: [
            ...(result.partialErrors ?? []),
            `Backend unavailable: ${backendError instanceof Error ? backendError.message : 'unknown error'}`,
          ],
        };
      }
    } else {
      result = await runClientPipeline(goal, requestId);
    }

    if (!result) {
      throw new Error('Failed to generate recommendations.');
    }

    if (enableCache) {
      writeCache(cacheKey, result);
    }

    return applyAnalysisResult(
      result,
      requestId,
      requestIdRef,
      mountedRef,
      setters,
      updateStatus,
    );
  }, [
    enableCache,
    getAccessToken,
    options.fetchFn,
    runClientPipeline,
    setters,
    updateStatus,
    useBackendProxy,
    userProfile,
  ]);

  const analyzeGoal = useCallback((goal) => {
    const requestId = requestIdRef.current + 1;
    requestIdRef.current = requestId;
    setError(null);

    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    const execute = async () => {
      try {
        inFlightRef.current = execute;
        return await runPipeline(goal, requestId);
      } catch (pipelineError) {
        if (requestId !== requestIdRef.current || !mountedRef.current) {
          return null;
        }
        const message = pipelineError instanceof Error
          ? pipelineError.message
          : 'Goal analysis failed.';
        setError(message);
        updateStatus('error', { message });
        setProgress(null);
        return null;
      } finally {
        if (inFlightRef.current === execute) {
          inFlightRef.current = null;
        }
      }
    };

    if (debounceMs <= 0) {
      return execute();
    }

    return new Promise((resolve) => {
      debounceTimerRef.current = setTimeout(() => {
        execute().then(resolve);
      }, debounceMs);
    });
  }, [debounceMs, runPipeline, updateStatus]);

  return {
    status,
    goalAnalysis,
    recommendations,
    jobSuggestions,
    gigSuggestions,
    expenseSuggestions,
    error,
    progress,
    analyzeGoal,
    selectRecommendationPath,
    clearAnalysis,
  };
}

export default useGoalAnalysis;
