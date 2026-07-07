/**
 * Utilities for TimelineProjection chart data and styling.
 */

import { formatCurrency } from './recommendationDisplayUtils.js';

/** @type {Record<string, string>} */
export const FEASIBILITY_COLORS = {
  'Very High': '#059669',
  High: '#10B981',
  Medium: '#D97706',
  Low: '#DC2626',
};

const FALLBACK_COLORS = ['#583FBC', '#2563EB', '#0891B2', '#7C3AED', '#DB2777'];

/**
 * @param {object | null | undefined} path
 * @returns {string}
 */
export function getPathKey(path) {
  return String(path?.pathId ?? path?.id ?? path?.title ?? 'path');
}

/**
 * @param {string | undefined} feasibility
 * @param {number} index
 * @returns {string}
 */
export function getPathColor(feasibility, index = 0) {
  if (feasibility && FEASIBILITY_COLORS[feasibility]) {
    return FEASIBILITY_COLORS[feasibility];
  }
  return FALLBACK_COLORS[index % FALLBACK_COLORS.length];
}

/**
 * @param {object | null | undefined} goal
 * @param {object | null | undefined} analysis
 * @param {number} [currentSavings=0]
 * @returns {number}
 */
export function resolveGoalThreshold(goal, analysis, currentSavings = 0) {
  if (typeof goal?.totalNeeded === 'number' && Number.isFinite(goal.totalNeeded)) {
    return goal.totalNeeded;
  }

  const future = analysis?.futureState ?? {};
  if (typeof future.savingsTarget === 'number' && Number.isFinite(future.savingsTarget)) {
    return future.savingsTarget;
  }

  const gaps = analysis?.gaps ?? {};
  const savings = currentSavings
    ?? analysis?.presentState?.savings
    ?? 0;
  const savingsGap = gaps.savingsGap ?? 0;
  return savings + Math.max(0, savingsGap);
}

/**
 * @param {object} path
 * @param {number} year
 * @param {number} startingSavings
 * @returns {number}
 */
export function getPathSavingsAtYear(path, year, startingSavings) {
  if (year <= 0) {
    return startingSavings;
  }

  const projections = Array.isArray(path?.projections) ? path.projections : [];
  if (projections.length === 0) {
    return startingSavings;
  }

  const exact = projections.find((row) => row.year === year);
  if (exact) {
    return exact.cumulativeSavings ?? startingSavings;
  }

  const prior = projections.filter((row) => row.year <= year).at(-1);
  if (prior) {
    return prior.cumulativeSavings ?? startingSavings;
  }

  return startingSavings;
}

/**
 * @param {object} path
 * @param {number} goalThreshold
 * @returns {number | null}
 */
export function getGoalReachedYear(path, goalThreshold) {
  if (typeof path?.goalReachedYear === 'number') {
    return path.goalReachedYear;
  }

  const hit = (path?.projections ?? []).find((row) => row.goalReached);
  if (hit) {
    return hit.year;
  }

  const threshold = goalThreshold > 0 ? goalThreshold : null;
  if (!threshold) {
    return null;
  }

  const crossed = (path?.projections ?? []).find(
    (row) => (row.cumulativeSavings ?? 0) >= threshold,
  );
  return crossed?.year ?? null;
}

/**
 * @param {object} params
 * @param {object | null | undefined} params.goal
 * @param {object[]} params.paths
 * @param {object | null | undefined} [params.analysis]
 * @param {number} [params.currentSavings=0]
 * @returns {{
 *   chartData: Array<Record<string, number>>,
 *   goalThreshold: number,
 *   timelineYears: number,
 *   pathMeta: Array<Record<string, unknown>>,
 * }}
 */
export function buildTimelineProjectionData({
  goal,
  paths,
  analysis,
  currentSavings = 0,
}) {
  const timelineYears = Math.max(
    1,
    Math.ceil(goal?.timeline ?? analysis?.futureState?.timelineYears ?? 5),
  );
  const goalThreshold = resolveGoalThreshold(goal, analysis, currentSavings);
  const startSavings = Math.max(
    0,
    currentSavings ?? analysis?.presentState?.savings ?? 0,
  );

  const chartData = [];
  for (let year = 0; year <= timelineYears; year += 1) {
    /** @type {Record<string, number>} */
    const row = {
      year,
      goalThreshold,
      currentSavings: startSavings,
    };

    (paths ?? []).forEach((path) => {
      const key = getPathKey(path);
      row[key] = getPathSavingsAtYear(path, year, startSavings);
    });

    chartData.push(row);
  }

  const pathMeta = (paths ?? []).map((path, index) => {
    const pathId = getPathKey(path);
    const finalRow = chartData.at(-1);
    const totalSavings = finalRow?.[pathId] ?? startSavings;
    const goalReachedYear = getGoalReachedYear(path, goalThreshold);
    const progressPercent = goalThreshold > 0
      ? Math.min(100, Math.round((totalSavings / goalThreshold) * 100))
      : 0;

    return {
      pathId,
      title: path.title ?? pathId,
      color: getPathColor(path.feasibility, index),
      feasibility: path.feasibility ?? 'Medium',
      monthlyBoost: path.monthlyBoost ?? 0,
      mostRealistic: Boolean(path.mostRealistic),
      goalReachedYear,
      totalSavings,
      progressPercent,
    };
  });

  return {
    chartData,
    goalThreshold,
    timelineYears,
    pathMeta,
  };
}

/**
 * @param {number} value
 * @param {number} goalThreshold
 * @returns {number}
 */
export function progressToGoal(value, goalThreshold) {
  if (!goalThreshold || goalThreshold <= 0) {
    return 0;
  }
  return Math.min(100, Math.round((value / goalThreshold) * 100));
}

/**
 * @param {number} value
 * @returns {string}
 */
export function formatAxisCurrency(value) {
  if (typeof value !== 'number' || !Number.isFinite(value)) {
    return '$0';
  }
  if (value >= 1_000_000) {
    return `$${(value / 1_000_000).toFixed(1)}M`;
  }
  if (value >= 1000) {
    return `$${Math.round(value / 1000)}k`;
  }
  return formatCurrency(value);
}

export default buildTimelineProjectionData;
