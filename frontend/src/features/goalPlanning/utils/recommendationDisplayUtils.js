/**
 * Display helpers for recommendation path UI.
 */

/** @type {Record<string, string>} */
export const EXPENSE_CATEGORY_LABELS = {
  housing: 'Housing',
  dining: 'Dining out',
  groceries: 'Groceries',
  subscriptions: 'Subscriptions',
  transport: 'Transport',
  insurance: 'Insurance',
  debt: 'Debt payments',
  utilities: 'Utilities',
  healthcare: 'Healthcare',
  childcare: 'Childcare',
  other: 'Other',
};

/**
 * @param {number | null | undefined} value
 * @returns {string}
 */
export function formatCurrency(value) {
  const numeric = typeof value === 'number' && Number.isFinite(value) ? value : 0;
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  }).format(numeric);
}

/**
 * @param {string} feasibility
 * @returns {string}
 */
export function feasibilityClassName(feasibility) {
  switch (feasibility) {
    case 'Very High':
    case 'High':
      return 'feasibilityHigh';
    case 'Medium':
      return 'feasibilityMedium';
    default:
      return 'feasibilityLow';
  }
}

/**
 * Filters expense cuts to categories the user actually tracks.
 * @param {Array<Record<string, unknown>>} suggestions
 * @param {string[]} trackedCategories
 * @returns {Array<Record<string, unknown>>}
 */
export function filterExpenseSuggestions(suggestions, trackedCategories) {
  if (!Array.isArray(suggestions) || suggestions.length === 0) {
    return [];
  }
  if (!Array.isArray(trackedCategories) || trackedCategories.length === 0) {
    return suggestions;
  }

  const tracked = new Set(trackedCategories.map((category) => category.toLowerCase()));
  return suggestions.filter((suggestion) => {
    const categoryId = String(suggestion.categoryId ?? suggestion.category ?? '').toLowerCase();
    return categoryId && tracked.has(categoryId);
  });
}

/**
 * @param {string} pathId
 * @param {object} jobSuggestions
 * @param {object} gigSuggestions
 * @param {object} expenseSuggestions
 * @param {string[]} trackedCategories
 */
export function getPathEnrichment(pathId, jobSuggestions, gigSuggestions, expenseSuggestions, trackedCategories) {
  const jobs = jobSuggestions?.byPathId?.[pathId]?.jobs
    ?? jobSuggestions?.global?.jobs
    ?? [];
  const gigs = gigSuggestions?.byPathId?.[pathId]?.gigs
    ?? gigSuggestions?.global?.gigs
    ?? [];
  const rawExpenses = expenseSuggestions?.byPathId?.[pathId]?.suggestions
    ?? expenseSuggestions?.global?.suggestions
    ?? [];

  return {
    jobs,
    gigs,
    expenses: filterExpenseSuggestions(rawExpenses, trackedCategories),
    allExpensesFiltered: rawExpenses.length > 0 && filterExpenseSuggestions(rawExpenses, trackedCategories).length === 0,
  };
}

/**
 * @param {object | null | undefined} goal
 * @param {object | null | undefined} analysis
 * @returns {string}
 */
export function buildGoalSummaryText(goal, analysis) {
  if (analysis?.summary) {
    return analysis.summary;
  }
  if (analysis?.goalDescription && goal?.timeline) {
    return `${analysis.goalDescription} in ${goal.timeline} years.`;
  }
  if (analysis?.goalDescription) {
    return analysis.goalDescription;
  }
  if (goal?.type) {
    return `Reach your ${String(goal.type).replace(/_/g, ' ')} goal.`;
  }
  return 'We analyzed your finances and mapped realistic paths to get there.';
}

/**
 * Extracts tracked expense category ids from onboarding/profile data.
 * @param {object | null | undefined} onboardingData
 * @returns {string[]}
 */
export function extractTrackedExpenseCategories(onboardingData) {
  const categories = onboardingData?.recurring_expenses?.categories;
  if (!categories || typeof categories !== 'object') {
    return [];
  }
  return Object.entries(categories)
    .filter(([, amount]) => typeof amount === 'number' && amount > 0)
    .map(([categoryId]) => categoryId);
}

export default {
  formatCurrency,
  filterExpenseSuggestions,
  getPathEnrichment,
  buildGoalSummaryText,
  extractTrackedExpenseCategories,
};
