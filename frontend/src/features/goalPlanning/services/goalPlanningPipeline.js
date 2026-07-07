import { analyzeGoal as runGoalAnalysis } from './goalAnalyzer.js';
import { generateRecommendations } from './recommendationGenerator.js';
import { suggestJobsForIncomeGoal } from './jobRecommendationService.js';
import { suggestSideGigs } from './sideGigService.js';
import { suggestExpenseCuts } from './expenseReductionService.js';
import { mapEnrichmentToPaths } from '../utils/goalPlanningEnrichment.js';

const DEFAULT_TIMEOUT_MS = 30000;
const DEFAULT_LLM_RETRIES = 2;

/**
 * @template T
 * @param {Promise<T>} promise
 * @param {number} timeoutMs
 * @param {string} label
 * @returns {Promise<T>}
 */
function withTimeout(promise, timeoutMs, label) {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      reject(new Error(`${label} timed out after ${timeoutMs}ms`));
    }, timeoutMs);

    promise
      .then((value) => {
        clearTimeout(timer);
        resolve(value);
      })
      .catch((error) => {
        clearTimeout(timer);
        reject(error);
      });
  });
}

/**
 * @template T
 * @param {() => Promise<T>} operation
 * @param {number} retries
 * @returns {Promise<T>}
 */
async function withRetry(operation, retries) {
  let lastError = null;

  for (let attempt = 0; attempt <= retries; attempt += 1) {
    try {
      return await operation();
    } catch (error) {
      lastError = error;
      if (attempt === retries) {
        break;
      }
      await new Promise((resolve) => setTimeout(resolve, 250 * (attempt + 1)));
    }
  }

  throw lastError ?? new Error('Operation failed');
}

/**
 * @param {PromiseSettledResult<unknown>} result
 * @param {*} fallback
 * @returns {*}
 */
function settledValue(result, fallback) {
  return result.status === 'fulfilled' ? result.value : fallback;
}

/**
 * Runs the full goal-planning analysis pipeline.
 * Shared by the React hook and the backend Node runner.
 *
 * @param {Record<string, unknown>} userProfile
 * @param {object} goal
 * @param {object} [options]
 * @param {(prompt: string, opts?: object) => Promise<string | null>} [options.llmClient]
 * @param {string} [options.apiKey]
 * @param {typeof fetch} [options.fetchFn]
 * @param {number} [options.timeoutMs]
 * @param {number} [options.llmRetries]
 * @param {(phase: string, message: string) => void} [options.onProgress]
 * @returns {Promise<{
 *   goalAnalysis: object,
 *   recommendations: object,
 *   jobSuggestions: object,
 *   gigSuggestions: object,
 *   expenseSuggestions: object,
 *   partialErrors: string[],
 * }>}
 */
export async function runGoalPlanningPipeline(userProfile, goal, options = {}) {
  if (!userProfile || !goal) {
    throw new Error('User profile and goal are required.');
  }

  const {
    llmClient,
    apiKey,
    fetchFn,
    timeoutMs = DEFAULT_TIMEOUT_MS,
    llmRetries = DEFAULT_LLM_RETRIES,
    onProgress,
  } = options;

  const serviceOptions = { llmClient, fetchFn, apiKey };

  onProgress?.('analyzing', 'Analyzing goal gaps and feasibility');

  const analysis = runGoalAnalysis(userProfile, goal);
  if (!analysis) {
    throw new Error('Unable to analyze goal. Check goal parameters and timeline.');
  }

  onProgress?.('generating', 'Generating recommendation paths');

  const recommendationResult = await withTimeout(
    withRetry(
      () => generateRecommendations(analysis, userProfile, goal, serviceOptions),
      llmRetries,
    ),
    timeoutMs,
    'Recommendation generation',
  );

  if (!recommendationResult) {
    throw new Error('Failed to generate recommendations.');
  }

  const paths = recommendationResult.paths ?? [];
  const recommendationsState = {
    paths,
    selectedPath: paths.find((path) => path.mostRealistic)?.pathId
      ?? paths[0]?.pathId
      ?? null,
    source: recommendationResult.source ?? 'fallback',
    generatedAt: recommendationResult.generatedAt ?? new Date().toISOString(),
  };

  onProgress?.('enriching', 'Adding job, gig, and expense suggestions');

  const incomeGap = analysis?.gaps?.incomeGap ?? 0;
  const monthlyToSave = Math.max(0, analysis?.gaps?.monthlyToSave ?? 0);
  const availableHours = userProfile?.availableHours ?? 10;
  const timelineYears = goal?.timeline ?? analysis?.futureState?.timelineYears ?? 5;

  const [jobsSettled, gigsSettled, expensesSettled] = await Promise.allSettled([
    withTimeout(
      withRetry(
        () => suggestJobsForIncomeGoal(
          userProfile,
          incomeGap,
          goal?.type ?? analysis?.goalType ?? 'general',
          { ...serviceOptions, timelineYears },
        ),
        llmRetries,
      ),
      timeoutMs,
      'Job suggestions',
    ),
    withTimeout(
      withRetry(
        () => suggestSideGigs(userProfile, monthlyToSave, availableHours, serviceOptions),
        llmRetries,
      ),
      timeoutMs,
      'Side gig suggestions',
    ),
    withTimeout(
      withRetry(
        () => suggestExpenseCuts(userProfile, monthlyToSave, serviceOptions),
        llmRetries,
      ),
      timeoutMs,
      'Expense reduction suggestions',
    ),
  ]);

  const partialErrors = [];
  if (jobsSettled.status === 'rejected') {
    partialErrors.push(`Job suggestions unavailable: ${jobsSettled.reason?.message ?? 'unknown error'}`);
  }
  if (gigsSettled.status === 'rejected') {
    partialErrors.push(`Gig suggestions unavailable: ${gigsSettled.reason?.message ?? 'unknown error'}`);
  }
  if (expensesSettled.status === 'rejected') {
    partialErrors.push(`Expense suggestions unavailable: ${expensesSettled.reason?.message ?? 'unknown error'}`);
  }

  const jobsResult = settledValue(jobsSettled, { jobs: [], source: 'unavailable' });
  const gigsResult = settledValue(gigsSettled, { gigs: [], source: 'unavailable' });
  const expenseResult = settledValue(expensesSettled, {
    suggestions: [],
    cumulativeSavings: 0,
    gapRemaining: monthlyToSave,
    source: 'unavailable',
  });

  const { jobByPathId, gigByPathId, expenseByPathId } = mapEnrichmentToPaths(
    paths,
    jobsResult,
    gigsResult,
    expenseResult,
  );

  const jobState = { global: jobsResult, byPathId: jobByPathId };
  const gigState = { global: gigsResult, byPathId: gigByPathId };
  const expenseState = { global: expenseResult, byPathId: expenseByPathId };

  return {
    goalAnalysis: analysis,
    recommendations: recommendationsState,
    jobSuggestions: jobState,
    gigSuggestions: gigState,
    expenseSuggestions: expenseState,
    partialErrors,
  };
}

export default runGoalPlanningPipeline;
