import { projectPathOverTime } from './recommendationPaths.js';
import recommendationPaths from './recommendationPaths.js';
import { callClaudeApi } from './claudeClient.js';
import { recommendationPrompt } from './llmPrompts.js';
import {
  suggestExpenseCuts,
  suggestJobsForIncomeGoal,
  suggestSideGigs,
} from './recommendationActionServices.js';

export { callClaudeApi, CLAUDE_MODEL, ANTHROPIC_MESSAGES_URL } from './claudeClient.js';

const REQUIRED_PATH_IDS = ['career_advancement', 'side_income', 'combined', 'alternative'];
const FEASIBILITY_LEVELS = new Set(['Low', 'Medium', 'High', 'Very High']);

/**
 * @param {number} value
 * @returns {number}
 */
function roundCurrency(value) {
  return Math.round(value * 100) / 100;
}

/**
 * @param {unknown} value
 * @param {number} [fallback=0]
 * @returns {number}
 */
function toNumber(value, fallback = 0) {
  if (typeof value !== 'number' || !Number.isFinite(value)) {
    return fallback;
  }
  return value;
}

/**
 * @param {unknown} gapAnalysis
 * @param {Record<string, unknown>} userProfile
 * @param {Object} goal
 * @returns {Record<string, unknown>}
 */
function buildGapContext(gapAnalysis, userProfile, goal) {
  const gaps = gapAnalysis?.gaps ?? {};
  const present = gapAnalysis?.presentState ?? {};
  const future = gapAnalysis?.futureState ?? {};

  const savings = toNumber(present.savings, toNumber(userProfile?.savings, 0));
  const savingsGap = toNumber(gaps.savingsGap, 0);
  const totalNeeded = toNumber(future.savingsTarget, savings + Math.max(0, savingsGap));
  const timeline = toNumber(future.timelineYears, toNumber(goal?.timeline, 1));

  return {
    totalNeeded,
    haveNow: savings,
    savingsGap,
    incomeGap: toNumber(gaps.incomeGap, 0),
    monthlyToSave: toNumber(gaps.monthlyToSave, 0),
    timeline,
    feasible: Boolean(gaps.feasible),
    feasibilityScore: toNumber(gaps.feasibilityScore, 0),
  };
}

/**
 * Builds the Claude prompt for recommendation generation.
 * @param {unknown} gapAnalysis - Output from analyzeGoal()
 * @param {Record<string, unknown>} userProfile
 * @param {Object} goal
 * @returns {string}
 */
export function buildRecommendationPrompt(gapAnalysis, userProfile, goal) {
  return recommendationPrompt(gapAnalysis, userProfile, goal);
}

/**
 * Strips markdown fences and parses LLM JSON output.
 * @param {string} rawResponse
 * @returns {{ paths: Array<Record<string, unknown>> } | null}
 */
export function parseRecommendationResponse(rawResponse) {
  if (!rawResponse || typeof rawResponse !== 'string') {
    return null;
  }

  let text = rawResponse.trim();
  const fenceMatch = text.match(/```(?:json)?\s*([\s\S]*?)```/i);
  if (fenceMatch) {
    text = fenceMatch[1].trim();
  }

  const jsonStart = text.indexOf('{');
  const jsonEnd = text.lastIndexOf('}');
  if (jsonStart === -1 || jsonEnd === -1) {
    return null;
  }

  try {
    const parsed = JSON.parse(text.slice(jsonStart, jsonEnd + 1));
    if (!parsed || !Array.isArray(parsed.paths)) {
      return null;
    }
    return parsed;
  } catch {
    return null;
  }
}

/**
 * Validates a single recommendation path from the LLM.
 * @param {unknown} path
 * @returns {boolean}
 */
function isValidPath(path) {
  if (!path || typeof path !== 'object') {
    return false;
  }

  const record = /** @type {Record<string, unknown>} */ (path);
  const timeline = record.timeline ?? record.totalTimeline;
  return Boolean(
    typeof record.pathId === 'string'
    && typeof record.title === 'string'
    && typeof record.description === 'string'
    && typeof record.monthlyBoost === 'number'
    && Number.isFinite(record.monthlyBoost)
    && typeof timeline === 'string'
    && typeof record.feasibility === 'string'
    && FEASIBILITY_LEVELS.has(record.feasibility)
    && Array.isArray(record.pros)
    && Array.isArray(record.cons),
  );
}

/**
 * Validates parsed LLM recommendation payload.
 * @param {{ paths?: unknown[] } | null} parsed
 * @returns {boolean}
 */
export function validateRecommendationPayload(parsed) {
  if (!parsed || !Array.isArray(parsed.paths) || parsed.paths.length === 0) {
    return false;
  }

  const pathIds = parsed.paths
    .filter(isValidPath)
    .map((path) => path.pathId);

  return REQUIRED_PATH_IDS.every((id) => pathIds.includes(id));
}

/**
 * Maps local recommendation path to LLM-compatible shape.
 * @param {Record<string, unknown> | null} localPath
 * @param {string} pathId
 * @returns {Record<string, unknown> | null}
 */
function mapLocalPathToLlmShape(localPath, pathId) {
  if (!localPath) {
    return null;
  }

  const base = {
    pathId,
    title: localPath.title,
    description: localPath.description,
    monthlyBoost: localPath.monthlyBoost,
    timeline: localPath.timeline,
    feasibility: localPath.feasibility,
    pros: localPath.pros ?? [],
    cons: localPath.cons ?? [],
    details: localPath.tradeoff ?? localPath.description,
  };

  if (pathId === 'alternative') {
    return {
      ...base,
      pathId: 'alternative',
      title: localPath.title ?? 'Faster Alternative',
      requires: localPath.tradeoff ?? 'Adjusting goal scope or timeline',
      details: localPath.description,
    };
  }

  if (pathId === 'combined') {
    return {
      ...base,
      mostRealistic: true,
      whyRecommended: 'Balances income growth, side work, and spending discipline',
      components: (localPath.combinedPaths ?? []).map((type) => ({
        type,
        boost: localPath.monthlyBoost,
        timeline: localPath.timeline,
      })),
      totalTimeline: localPath.timeline,
    };
  }

  return base;
}

/**
 * Rule-based recommendations when LLM is unavailable or returns invalid output.
 * @param {Record<string, unknown>} userProfile
 * @param {Object} goal
 * @param {unknown} gapAnalysis
 * @returns {{ paths: Array<Record<string, unknown>>, source: 'fallback' }}
 */
export function fallbackRecommendations(userProfile, goal, gapAnalysis) {
  const gap = gapAnalysis?.gaps ?? {};
  const gapForPaths = {
    savingsGap: toNumber(gap.savingsGap, 0),
    incomeGap: toNumber(gap.incomeGap, 0),
    monthlyToSave: toNumber(gap.monthlyToSave, 0),
    expenseIncrease: toNumber(gap.expenseIncrease, 0),
    feasible: Boolean(gap.feasible),
    feasibilityScore: toNumber(gap.feasibilityScore, 0),
  };

  const career = recommendationPaths.careerAdvancement(userProfile, goal, gapForPaths);
  const side = recommendationPaths.sideIncome(userProfile, goal, gapForPaths);
  const combined = recommendationPaths.combined(userProfile, goal, gapForPaths);
  const alternative = recommendationPaths.timelineExtension(goal, gapForPaths)
    ?? recommendationPaths.goalScopeReduction(goal, gapForPaths);

  const paths = [
    mapLocalPathToLlmShape(career, 'career_advancement'),
    mapLocalPathToLlmShape(side, 'side_income'),
    mapLocalPathToLlmShape(combined, 'combined'),
    mapLocalPathToLlmShape(alternative, 'alternative'),
  ].filter(Boolean);

  return {
    source: 'fallback',
    paths,
  };
}

/**
 * Enhances recommendation paths with local calculations and action suggestions.
 * @param {Array<Record<string, unknown>>} paths
 * @param {Record<string, unknown>} userProfile
 * @param {Object} goal
 * @param {unknown} gapAnalysis
 * @returns {Array<Record<string, unknown>>}
 */
export function enhanceWithDetails(paths, userProfile, goal, gapAnalysis) {
  const gap = buildGapContext(gapAnalysis, userProfile, goal);
  const gapForPaths = {
    savingsGap: gap.savingsGap,
    incomeGap: gap.incomeGap,
    monthlyToSave: gap.monthlyToSave,
    feasible: gap.feasible,
    feasibilityScore: gap.feasibilityScore,
  };

  const localCareer = recommendationPaths.careerAdvancement(userProfile, goal, gapForPaths);
  const localSide = recommendationPaths.sideIncome(userProfile, goal, gapForPaths);
  const localExpense = recommendationPaths.expenseReduction(userProfile, goal, gapForPaths);
  const localCombined = recommendationPaths.combined(userProfile, goal, gapForPaths);

  const localById = {
    career_advancement: localCareer,
    side_income: localSide,
    combined: localCombined,
    alternative: recommendationPaths.timelineExtension(goal, gapForPaths)
      ?? recommendationPaths.goalScopeReduction(goal, gapForPaths),
  };

  const monthlyExpenses = toNumber(
    userProfile?.expenses,
    toNumber(gapAnalysis?.presentState?.monthlyExpenses, 0),
  );
  const skills = Array.isArray(userProfile?.skills) ? userProfile.skills : [];
  const savings = toNumber(userProfile?.savings, toNumber(gapAnalysis?.presentState?.savings, 0));

  return paths.map((path) => {
    const pathId = path.pathId;
    const local = localById[pathId] ?? null;
    const monthlyBoost = roundCurrency(
      toNumber(local?.monthlyBoost, toNumber(path.monthlyBoost, 0)),
    );

    const enhanced = {
      ...path,
      monthlyBoost,
      actionItems: local?.actionItems ?? [],
      action: local?.action ?? null,
      projections: local?.projections ?? projectPathOverTime({
        startingSavings: savings,
        savingsTarget: gap.totalNeeded,
        timelineYears: gap.timeline,
        monthlyBoost,
        rampMonths: pathId === 'career_advancement' || pathId === 'combined' ? 6 : 0,
      }),
      goalReachedYear: (local?.projections ?? []).find((point) => point.goalReached)?.year ?? null,
    };

    if (pathId === 'career_advancement' || pathId === 'combined') {
      enhanced.jobSuggestions = suggestJobsForIncomeGoal(userProfile, gap.incomeGap);
      enhanced.action = enhanced.action
        ?? `suggestJobsForIncomeGoal(userProfile, ${gap.incomeGap})`;
    }

    if (pathId === 'side_income' || pathId === 'combined') {
      enhanced.gigSuggestions = suggestSideGigs(skills, gap.monthlyToSave);
      enhanced.action = pathId === 'side_income'
        ? `suggestSideGigs(${JSON.stringify(skills)}, ${gap.monthlyToSave})`
        : enhanced.action;
    }

    if (pathId === 'alternative' || pathId === 'combined') {
      enhanced.expenseCutSuggestions = suggestExpenseCuts(monthlyExpenses, gap.monthlyToSave);
    }

    if (pathId === 'career_advancement' && localCareer) {
      enhanced.localMonthlyBoost = localCareer.monthlyBoost;
    }
    if (pathId === 'side_income' && localSide) {
      enhanced.localMonthlyBoost = localSide.monthlyBoost;
      enhanced.hoursPerWeek = enhanced.hoursPerWeek ?? toNumber(userProfile?.availableHours, 10);
    }
    if (pathId === 'combined' && localCombined) {
      enhanced.mostRealistic = true;
      enhanced.localMonthlyBoost = localCombined.monthlyBoost;
      enhanced.expenseCutSuggestions = suggestExpenseCuts(monthlyExpenses, gap.monthlyToSave);
    }

    return enhanced;
  });
}

/**
 * Generates AI-enhanced recommendation paths for a financial goal.
 * @param {unknown} gapAnalysis - Output from analyzeGoal()
 * @param {Record<string, unknown>} userProfile
 * @param {Object} goal
 * @param {Object} [options]
 * @param {(prompt: string, opts?: object) => Promise<string | null>} [options.llmClient]
 * @param {string} [options.apiKey]
 * @param {typeof fetch} [options.fetchFn]
 * @returns {Promise<{ source: string, paths: Array<Record<string, unknown>>, prompt?: string, generatedAt: string } | null>}
 */
export async function generateRecommendations(gapAnalysis, userProfile, goal, options = {}) {
  if (!gapAnalysis || !userProfile || !goal) {
    return null;
  }

  const prompt = buildRecommendationPrompt(gapAnalysis, userProfile, goal);
  const llmClient = options.llmClient
    ?? ((text) => callClaudeApi(text, { apiKey: options.apiKey, fetchFn: options.fetchFn }));

  let source = 'fallback';
  let paths = [];

  const rawResponse = await llmClient(prompt, options);
  const parsed = rawResponse ? parseRecommendationResponse(rawResponse) : null;

  if (parsed && validateRecommendationPayload(parsed)) {
    source = 'llm';
    paths = parsed.paths.filter(isValidPath);
  } else {
    const fallback = fallbackRecommendations(userProfile, goal, gapAnalysis);
    paths = fallback.paths;
    source = fallback.source;
  }

  const enhancedPaths = enhanceWithDetails(paths, userProfile, goal, gapAnalysis);

  return {
    source,
    paths: enhancedPaths,
    prompt,
    generatedAt: new Date().toISOString(),
    goalId: gapAnalysis?.goalId ?? null,
    goalType: gapAnalysis?.goalType ?? goal?.type ?? null,
  };
}

export default generateRecommendations;
