/** @type {readonly string[]} */
export const ENRICHMENT_PATH_IDS = [
  'career_advancement',
  'side_income',
  'combined',
  'alternative',
  'expense_reduction',
  'timeline_extension',
  'goal_scope_reduction',
  'financing',
];

/**
 * @param {string} pathId
 * @returns {{ includeJobs: boolean, includeGigs: boolean, includeExpenses: boolean }}
 */
export function getPathEnrichmentNeeds(pathId) {
  switch (pathId) {
    case 'career_advancement':
      return { includeJobs: true, includeGigs: false, includeExpenses: false };
    case 'side_income':
      return { includeJobs: false, includeGigs: true, includeExpenses: false };
    case 'combined':
      return { includeJobs: true, includeGigs: true, includeExpenses: true };
    case 'alternative':
    case 'expense_reduction':
    case 'timeline_extension':
    case 'goal_scope_reduction':
      return { includeJobs: false, includeGigs: false, includeExpenses: true };
    default:
      return { includeJobs: true, includeGigs: true, includeExpenses: true };
  }
}

/**
 * Maps global enrichment results onto recommendation paths.
 * @param {Array<Record<string, unknown>>} paths
 * @param {{ jobs: unknown[], source?: string }} jobsResult
 * @param {{ gigs: unknown[], source?: string }} gigsResult
 * @param {{ suggestions: unknown[], source?: string, cumulativeSavings?: number, gapRemaining?: number }} expenseResult
 * @returns {{ jobByPathId: Record<string, unknown>, gigByPathId: Record<string, unknown>, expenseByPathId: Record<string, unknown> }}
 */
export function mapEnrichmentToPaths(paths, jobsResult, gigsResult, expenseResult) {
  const jobByPathId = {};
  const gigByPathId = {};
  const expenseByPathId = {};

  (paths ?? []).forEach((path) => {
    const pathId = String(path.pathId ?? '');
    const needs = getPathEnrichmentNeeds(pathId);

    if (needs.includeJobs) {
      jobByPathId[pathId] = {
        jobs: jobsResult.jobs ?? [],
        source: jobsResult.source ?? 'knowledge_base',
      };
    }
    if (needs.includeGigs) {
      gigByPathId[pathId] = {
        gigs: gigsResult.gigs ?? [],
        source: gigsResult.source ?? 'knowledge_base',
      };
    }
    if (needs.includeExpenses) {
      expenseByPathId[pathId] = {
        suggestions: expenseResult.suggestions ?? [],
        cumulativeSavings: expenseResult.cumulativeSavings ?? 0,
        gapRemaining: expenseResult.gapRemaining ?? 0,
        source: expenseResult.source ?? 'knowledge_base',
      };
    }
  });

  ENRICHMENT_PATH_IDS.forEach((pathId) => {
    if (!jobByPathId[pathId] && paths?.some((path) => path.pathId === pathId)) {
      jobByPathId[pathId] = { jobs: [], source: 'unavailable' };
    }
  });

  return { jobByPathId, gigByPathId, expenseByPathId };
}

export default mapEnrichmentToPaths;
