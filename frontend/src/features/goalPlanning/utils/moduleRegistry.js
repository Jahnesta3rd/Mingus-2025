/**
 * Mingus module registry for goal-planning recommendation deep-links.
 * Maps recommendation paths to real dashboard modules from the module audit.
 */

/** @type {Record<string, { id: string, name: string, description: string, path: string }>} */
export const MINGUS_MODULES = {
  'cash-forecast': {
    id: 'cash-forecast',
    name: 'Cash Forecast',
    description: 'See your 90-day cash projection and track balance changes.',
    path: '/dashboard/forecast',
  },
  waterfall: {
    id: 'waterfall',
    name: 'Income Waterfall',
    description: 'Allocate income across fixed costs, debt, savings, and surplus.',
    path: '/dashboard/waterfall',
  },
  'debt-analyzer': {
    id: 'debt-analyzer',
    name: 'Debt Analyzer',
    description: 'Model payoff strategies and reduce monthly debt payments.',
    path: '/dashboard/tools?tab=debt',
  },
  housing: {
    id: 'housing',
    name: 'Housing',
    description: 'Track buy-goal progress, readiness, and rent vs buy scenarios.',
    path: '/dashboard/tools?tab=housing',
  },
  vehicle: {
    id: 'vehicle',
    name: 'Vehicle',
    description: 'Review vehicle costs, maintenance, and purchase planning.',
    path: '/dashboard/tools?tab=vehicle',
  },
  'job-recommendations': {
    id: 'job-recommendations',
    name: 'Job Recommendations',
    description: 'Explore higher-paying roles matched to your skills.',
    path: '/dashboard/tools?tab=discover',
  },
  'income-profile': {
    id: 'income-profile',
    name: 'Income & Profile',
    description: 'Update income streams and career details in your profile.',
    path: '/dashboard/tools?tab=you&focus=income',
  },
  'plans-milestones': {
    id: 'plans-milestones',
    name: 'Plans & Milestones',
    description: 'Add dated milestones and track spending streaks toward goals.',
    path: '/dashboard/tools?tab=plans',
  },
  wellness: {
    id: 'wellness',
    name: 'Wellness Spending',
    description: 'Review mood-linked spending and weekly wellness check-ins.',
    path: '/dashboard/tools?tab=wellness',
  },
  onboarding: {
    id: 'onboarding',
    name: 'Complete Onboarding',
    description: 'Fill in missing income, housing, and expense details.',
    path: '/onboarding',
  },
};

/** @type {Record<string, { core: string[], supporting: string[] }>} */
export const PATH_MODULE_MAP = {
  career_advancement: {
    core: ['job-recommendations', 'income-profile'],
    supporting: ['cash-forecast', 'plans-milestones'],
  },
  side_income: {
    core: ['job-recommendations', 'income-profile'],
    supporting: ['cash-forecast', 'plans-milestones'],
  },
  expense_reduction: {
    core: ['cash-forecast', 'debt-analyzer'],
    supporting: ['waterfall', 'wellness'],
  },
  timeline_extension: {
    core: ['plans-milestones', 'cash-forecast'],
    supporting: ['income-profile'],
  },
  goal_scope_reduction: {
    core: ['housing', 'vehicle', 'plans-milestones'],
    supporting: ['cash-forecast'],
  },
  financing: {
    core: ['debt-analyzer', 'cash-forecast'],
    supporting: ['housing', 'waterfall'],
  },
  combined: {
    core: ['job-recommendations', 'cash-forecast', 'debt-analyzer'],
    supporting: ['waterfall', 'plans-milestones', 'income-profile'],
  },
  alternative: {
    core: ['cash-forecast', 'plans-milestones'],
    supporting: ['job-recommendations', 'waterfall'],
  },
};

/** @type {Record<string, string[]>} */
export const GOAL_TYPE_MODULES = {
  home_purchase: ['housing', 'cash-forecast', 'waterfall', 'debt-analyzer'],
  car_purchase: ['vehicle', 'cash-forecast', 'debt-analyzer'],
  apartment_move: ['housing', 'cash-forecast', 'plans-milestones'],
  baby: ['plans-milestones', 'cash-forecast', 'wellness'],
  business: ['income-profile', 'cash-forecast', 'waterfall', 'job-recommendations'],
};

/**
 * @param {string} pathId
 * @returns {{ core: object[], supporting: object[] }}
 */
export function getModulesForPath(pathId) {
  const mapping = PATH_MODULE_MAP[pathId] ?? PATH_MODULE_MAP.alternative;
  return {
    core: mapping.core.map((id) => MINGUS_MODULES[id]).filter(Boolean),
    supporting: mapping.supporting.map((id) => MINGUS_MODULES[id]).filter(Boolean),
  };
}

/**
 * @param {string} goalType
 * @returns {object[]}
 */
export function getModulesForGoalType(goalType) {
  const ids = GOAL_TYPE_MODULES[goalType] ?? ['cash-forecast', 'plans-milestones'];
  return ids.map((id) => MINGUS_MODULES[id]).filter(Boolean);
}

export default MINGUS_MODULES;
