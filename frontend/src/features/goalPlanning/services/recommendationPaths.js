import { costCalculator } from './calculators/index.js';
import { extractGoalParameters } from './goalAnalyzer.js';

/**
 * @typedef {'Low' | 'Medium' | 'High' | 'Very High'} PathFeasibility
 */

/**
 * @typedef {Object} RecommendationGap
 * @property {number} [savingsGap]
 * @property {number} [incomeGap]
 * @property {number} [expenseIncrease]
 * @property {number} [monthlyToSave]
 * @property {boolean} [feasible]
 * @property {number} [feasibilityScore]
 */

/**
 * @typedef {Object} PathProjection
 * @property {number} year
 * @property {number} cumulativeSavings
 * @property {boolean} goalReached
 * @property {number} monthlyBoostApplied
 */

/**
 * @typedef {Object} RecommendationPath
 * @property {string} pathId
 * @property {string} title
 * @property {string} description
 * @property {number} monthlyBoost
 * @property {string} timeline
 * @property {PathFeasibility} feasibility
 * @property {string[]} pros
 * @property {string[]} cons
 * @property {string} action
 * @property {string[]} actionItems
 * @property {PathProjection[]} projections
 * @property {string} [tradeoff]
 * @property {number} [newTimeline]
 * @property {number} [monthlyAfter]
 * @property {Array<Record<string, unknown>>} [options]
 * @property {boolean} [mostRealistic]
 * @property {string[]} [combinedPaths]
 */

const PROJECTION_YEARS = 5;
const SIDE_GIG_HOURLY_RATE = 35;
const SIDE_GIG_WEEKS_PER_MONTH = 4.33;
const EXPENSE_CUT_RATE = 0.15;
const CAREER_RAMP_MONTHS = 6;

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
 * @param {unknown} gap
 * @returns {boolean}
 */
function isValidGap(gap) {
  return Boolean(gap && typeof gap === 'object');
}

/**
 * @param {unknown} goal
 * @returns {boolean}
 */
function isValidGoal(goal) {
  return Boolean(goal && typeof goal === 'object' && typeof goal.type === 'string');
}

/**
 * @param {RecommendationGap} gap
 * @returns {number}
 */
function getMonthlyNeeded(gap) {
  return Math.max(0, toNumber(gap.monthlyToSave, 0));
}

/**
 * @param {Record<string, unknown>} userProfile
 * @param {RecommendationGap} gap
 * @returns {number}
 */
function getSavingsTarget(userProfile, gap) {
  const savings = Math.max(0, toNumber(userProfile?.savings, 0));
  const savingsGap = toNumber(gap.savingsGap, 0);
  return roundCurrency(savings + Math.max(0, savingsGap));
}

/**
 * Estimates monthly income boost from a career move based on annual income gap.
 * @param {number} incomeGap - Annual income shortfall
 * @param {number} [monthlyIncome] - Current monthly income
 * @returns {number}
 */
export function calculateMonthlyBoostFromCareerMove(incomeGap, monthlyIncome = 0) {
  const annualGap = Math.max(0, toNumber(incomeGap, 0));
  if (annualGap === 0) {
    return 0;
  }

  const rawMonthly = annualGap / 12;
  const cappedByIncome = monthlyIncome > 0 ? monthlyIncome * 0.35 : rawMonthly;
  return roundCurrency(Math.min(rawMonthly * 0.75, cappedByIncome));
}

/**
 * Estimates monthly boost from freelance/side work based on available hours.
 * @param {number} availableHoursPerWeek
 * @param {string[]} [skills]
 * @param {number} [monthlyNeeded]
 * @returns {number}
 */
export function calculateMonthlyBoostFromSideGigs(
  availableHoursPerWeek,
  skills = [],
  monthlyNeeded = 0,
) {
  const hours = typeof availableHoursPerWeek === 'number' && Number.isFinite(availableHoursPerWeek)
    ? Math.min(15, Math.max(0, availableHoursPerWeek))
    : 10;
  if (hours === 0) {
    return 0;
  }

  const skillMultiplier = skills.length >= 3 ? 1.2 : skills.length > 0 ? 1.1 : 1;
  const hourlyRate = SIDE_GIG_HOURLY_RATE * skillMultiplier;
  const estimated = hours * SIDE_GIG_WEEKS_PER_MONTH * hourlyRate;

  if (monthlyNeeded > 0) {
    return roundCurrency(Math.min(estimated, monthlyNeeded));
  }

  return roundCurrency(estimated);
}

/**
 * Estimates monthly boost from expense reductions.
 * @param {number} monthlyExpenses
 * @param {number} [monthlyNeeded]
 * @returns {number}
 */
export function calculateMonthlyBoostFromExpenseCuts(monthlyExpenses, monthlyNeeded = 0) {
  const expenses = Math.max(0, toNumber(monthlyExpenses, 0));
  if (expenses === 0) {
    return 0;
  }

  const potentialCuts = expenses * EXPENSE_CUT_RATE;
  if (monthlyNeeded > 0) {
    return roundCurrency(Math.min(potentialCuts, monthlyNeeded * 0.4));
  }

  return roundCurrency(potentialCuts);
}

/**
 * Projects cumulative savings over time for a recommendation path.
 * @param {Object} params
 * @param {number} params.startingSavings
 * @param {number} params.savingsTarget
 * @param {number} params.timelineYears
 * @param {number} params.monthlyBoost
 * @param {number} [params.years=5]
 * @param {number} [params.rampMonths=0] - Months before full monthly boost applies
 * @returns {PathProjection[]}
 */
export function projectPathOverTime({
  startingSavings,
  savingsTarget,
  timelineYears,
  monthlyBoost,
  years = PROJECTION_YEARS,
  rampMonths = 0,
}) {
  const start = Math.max(0, toNumber(startingSavings, 0));
  const target = Math.max(0, toNumber(savingsTarget, 0));
  const boost = Math.max(0, toNumber(monthlyBoost, 0));
  const projectionYears = Math.max(1, Math.ceil(toNumber(years, PROJECTION_YEARS)));
  const ramp = Math.max(0, toNumber(rampMonths, 0));

  let cumulativeSavings = start;
  const projections = [];

  for (let year = 1; year <= projectionYears; year += 1) {
    for (let month = 1; month <= 12; month += 1) {
      const monthIndex = (year - 1) * 12 + month;
      const rampFactor = ramp > 0 ? Math.min(1, monthIndex / ramp) : 1;
      cumulativeSavings += boost * rampFactor;
    }

    projections.push({
      year,
      cumulativeSavings: roundCurrency(cumulativeSavings),
      goalReached: cumulativeSavings >= target,
      monthlyBoostApplied: roundCurrency(boost),
    });
  }

  const unusedTimeline = toNumber(timelineYears, 0);
  if (unusedTimeline > projectionYears) {
    // timeline param reserved for future milestone annotations
  }

  return projections;
}

/**
 * Merges multiple recommendation paths into a combined strategy.
 * @param {RecommendationPath[]} paths
 * @param {Object} [options]
 * @param {number} [options.monthlyNeeded]
 * @returns {Partial<RecommendationPath>}
 */
export function combinePaths(paths, options = {}) {
  const validPaths = (paths ?? []).filter((path) => path && typeof path === 'object');
  const monthlyNeeded = Math.max(0, toNumber(options.monthlyNeeded, 0));

  const monthlyBoost = roundCurrency(
    validPaths.reduce((sum, path) => sum + toNumber(path.monthlyBoost, 0), 0),
  );
  const cappedBoost = monthlyNeeded > 0
    ? Math.min(monthlyBoost, monthlyNeeded * 1.1)
    : monthlyBoost;

  const pros = [...new Set(validPaths.flatMap((path) => path.pros ?? []))];
  const cons = [...new Set(validPaths.flatMap((path) => path.cons ?? []))];
  const actionItems = validPaths.flatMap((path) => path.actionItems ?? []);

  return {
    monthlyBoost: roundCurrency(cappedBoost),
    pros: pros.slice(0, 6),
    cons: cons.slice(0, 4),
    combinedPaths: validPaths.map((path) => path.pathId),
    actionItems: [...new Set(actionItems)].slice(0, 8),
  };
}

/**
 * Builds scope-reduction options based on goal type.
 * @param {Object} goal
 * @param {Record<string, unknown>} flatGoal
 * @param {RecommendationGap} gap
 * @returns {Array<Record<string, unknown>>}
 */
function buildScopeReductionOptions(goal, flatGoal, gap) {
  const timeline = Math.max(1, toNumber(goal.timeline, 1));
  const options = [];

  switch (goal.type) {
    case 'car_purchase': {
      const carPrice = toNumber(flatGoal.carPrice, 0);
      const cheaperPrice = roundCurrency(carPrice * 0.7);
      options.push({
        name: 'Buy cheaper car',
        saves: roundCurrency(carPrice - cheaperPrice),
        newPrice: cheaperPrice,
      });
      break;
    }
    case 'apartment_move': {
      const monthlyRent = toNumber(flatGoal.monthlyRent, 0);
      const cheaperRent = roundCurrency(monthlyRent * 0.85);
      options.push({
        name: 'Find cheaper apartment',
        saves: roundCurrency((monthlyRent - cheaperRent) * 3),
        newMonthlyRent: cheaperRent,
      });
      break;
    }
    case 'home_purchase': {
      const homePrice = toNumber(flatGoal.homePrice, 0);
      const cheaperHome = roundCurrency(homePrice * 0.85);
      options.push({
        name: 'Target a lower-priced home',
        saves: roundCurrency((homePrice - cheaperHome) * 1.05),
        newPrice: cheaperHome,
      });
      break;
    }
    case 'baby':
      options.push({
        name: 'Reduce preparation budget',
        saves: roundCurrency(toNumber(flatGoal.preparationCost, 0) * 0.25),
        newPreparationCost: roundCurrency(toNumber(flatGoal.preparationCost, 0) * 0.75),
      });
      break;
    case 'business':
      options.push({
        name: 'Start with a leaner launch',
        saves: roundCurrency(toNumber(flatGoal.initialInvestment, 0) * 0.35),
        newInitialInvestment: roundCurrency(toNumber(flatGoal.initialInvestment, 0) * 0.65),
      });
      break;
    default:
      break;
  }

  options.push({
    name: 'Delay by 2 years',
    saves: roundCurrency(Math.max(0, toNumber(gap.savingsGap, 0)) * 0.3),
    extendsTimelineByYears: 2,
  });

  return options;
}

/**
 * Builds financing options based on goal type.
 * @param {Object} goal
 * @param {Record<string, unknown>} flatGoal
 * @returns {Array<Record<string, unknown>>}
 */
function buildFinancingOptions(goal, flatGoal) {
  switch (goal.type) {
    case 'home_purchase': {
      const homePrice = toNumber(flatGoal.homePrice, 0);
      const downPayment = roundCurrency(homePrice * 0.2);
      const closingCosts = roundCurrency(homePrice * 0.05);
      return [{
        name: '30-year mortgage',
        description: 'Finance most of the purchase and reduce upfront cash need',
        upfrontNeeded: roundCurrency(downPayment + closingCosts),
        reducesUpfrontBy: roundCurrency(homePrice - downPayment),
        termYears: 30,
      }];
    }
    case 'car_purchase': {
      const carPrice = toNumber(flatGoal.carPrice, 0);
      const downPayment = roundCurrency(carPrice * 0.15);
      return [{
        name: 'Auto loan (5–7 years)',
        description: 'Spread vehicle cost over monthly payments',
        upfrontNeeded: downPayment,
        reducesUpfrontBy: roundCurrency(carPrice - downPayment),
        termYears: 6,
      }];
    }
    case 'baby':
      return [{
        name: 'Personal loan',
        description: 'Cover upfront baby preparation costs with installment payments',
        upfrontNeeded: 0,
        interestConsideration: 'Compare APR and monthly payment affordability',
      }];
    case 'business':
      return [
        {
          name: 'Business loan',
          description: 'Fund startup costs while preserving cash reserves',
          upfrontNeeded: roundCurrency(toNumber(flatGoal.initialInvestment, 0) * 0.5),
        },
        {
          name: 'Investor or partner',
          description: 'Trade equity for capital and reduce personal cash need',
          upfrontNeeded: roundCurrency(toNumber(flatGoal.initialInvestment, 0) * 0.4),
        },
      ];
    case 'apartment_move':
      return [{
        name: 'Payment plan for move-in costs',
        description: 'Negotiate deposit timing or use a low-interest line of credit',
        upfrontNeeded: roundCurrency(toNumber(flatGoal.monthlyRent, 0) * 2),
      }];
    default:
      return [];
  }
}

/**
 * @param {Record<string, unknown>} userProfile
 * @param {Object} goal
 * @param {RecommendationGap} gap
 * @returns {RecommendationPath | null}
 */
export function careerAdvancement(userProfile, goal, gap) {
  if (!isValidGap(gap) || !isValidGoal(goal)) {
    return null;
  }

  const monthlyNeeded = getMonthlyNeeded(gap);
  const monthlyIncome = toNumber(userProfile?.income, 0);
  const monthlyBoost = calculateMonthlyBoostFromCareerMove(gap.incomeGap, monthlyIncome);
  const savingsTarget = getSavingsTarget(userProfile, gap);
  const timelineYears = Math.max(1, toNumber(goal.timeline, 1));

  return {
    pathId: 'career_advancement',
    title: 'Career Advancement',
    description: 'Move to a higher-paying role to close your income and savings gap',
    monthlyBoost,
    timeline: '3-6 months',
    feasibility: monthlyBoost > 0 ? 'Medium' : 'Low',
    pros: [
      'Largest long-term upside for income growth',
      'Improves financial flexibility beyond this goal',
      'Compounding benefit on future goals',
    ],
    cons: [
      'Takes months to interview and transition',
      'Not guaranteed — offer timing is uncertain',
      'Can be stressful alongside current workload',
    ],
    action: `suggestJobsForIncomeGoal(userProfile, ${roundCurrency(toNumber(gap.incomeGap, 0))})`,
    actionItems: [
      'Update resume and LinkedIn for roles with higher compensation',
      'Target positions that pay at least 15–25% more than current income',
      'Schedule 2–3 networking conversations per week',
      'Practice salary negotiation before accepting offers',
    ],
    projections: projectPathOverTime({
      startingSavings: toNumber(userProfile?.savings, 0),
      savingsTarget,
      timelineYears,
      monthlyBoost,
      rampMonths: CAREER_RAMP_MONTHS,
    }),
  };
}

/**
 * @param {Record<string, unknown>} userProfile
 * @param {Object} goal
 * @param {RecommendationGap} gap
 * @returns {RecommendationPath | null}
 */
export function sideIncome(userProfile, goal, gap) {
  if (!isValidGap(gap) || !isValidGoal(goal)) {
    return null;
  }

  const monthlyNeeded = getMonthlyNeeded(gap);
  const skills = Array.isArray(userProfile?.skills) ? userProfile.skills : [];
  const rawHours = userProfile?.availableHours;
  const availableHours = typeof rawHours === 'number' && Number.isFinite(rawHours)
    ? Math.max(0, rawHours)
    : 10;
  const monthlyBoost = calculateMonthlyBoostFromSideGigs(availableHours, skills, monthlyNeeded);
  const savingsTarget = getSavingsTarget(userProfile, gap);
  const timelineYears = Math.max(1, toNumber(goal.timeline, 1));

  return {
    pathId: 'side_income',
    title: 'Side Income',
    description: 'Earn extra income through freelance or gig work in your spare hours',
    monthlyBoost,
    timeline: 'Immediate',
    feasibility: monthlyBoost > 0 ? 'High' : 'Low',
    pros: [
      'Can start within days',
      'Flexible schedule around current job',
      'Directly increases monthly savings capacity',
    ],
    cons: [
      'Time-intensive and can lead to burnout',
      'Income may fluctuate month to month',
      'Hourly rates vary by market demand',
    ],
    action: `suggestSideGigs(${JSON.stringify(skills)}, ${roundCurrency(monthlyNeeded)})`,
    actionItems: [
      `Block ${Math.min(15, availableHours)} hours per week for paid side work`,
      'List services on freelance platforms using your top skills',
      'Set a minimum hourly rate that makes the effort worthwhile',
      'Track side income separately and route it to this goal',
    ],
    projections: projectPathOverTime({
      startingSavings: toNumber(userProfile?.savings, 0),
      savingsTarget,
      timelineYears,
      monthlyBoost,
    }),
  };
}

/**
 * @param {Record<string, unknown>} userProfile
 * @param {Object} goal
 * @param {RecommendationGap} gap
 * @returns {RecommendationPath | null}
 */
export function expenseReduction(userProfile, goal, gap) {
  if (!isValidGap(gap) || !isValidGoal(goal)) {
    return null;
  }

  const monthlyNeeded = getMonthlyNeeded(gap);
  const monthlyExpenses = toNumber(userProfile?.expenses, 0);
  const monthlyBoost = calculateMonthlyBoostFromExpenseCuts(monthlyExpenses, monthlyNeeded);
  const savingsTarget = getSavingsTarget(userProfile, gap);
  const timelineYears = Math.max(1, toNumber(goal.timeline, 1));

  return {
    pathId: 'expense_reduction',
    title: 'Expense Reduction',
    description: 'Trim recurring and discretionary spending to free up monthly savings',
    monthlyBoost,
    timeline: 'Immediate',
    feasibility: monthlyBoost > 0 ? 'High' : 'Low',
    pros: [
      'Immediate impact on cash flow',
      'No extra hours required',
      'Creates sustainable savings habits',
    ],
    cons: [
      'Limited upside if expenses are already lean',
      'May reduce quality of life if cuts are too aggressive',
      'Harder to maintain without a budget system',
    ],
    action: `suggestExpenseCuts(${roundCurrency(monthlyExpenses)}, ${roundCurrency(monthlyNeeded)})`,
    actionItems: [
      'Audit subscriptions and cancel unused services',
      'Set weekly spending limits for dining and entertainment',
      'Renegotiate insurance, phone, and utility bills',
      'Redirect every dollar saved directly to this goal',
    ],
    projections: projectPathOverTime({
      startingSavings: toNumber(userProfile?.savings, 0),
      savingsTarget,
      timelineYears,
      monthlyBoost,
    }),
  };
}

/**
 * @param {Object} goal
 * @param {RecommendationGap} gap
 * @returns {RecommendationPath | null}
 */
export function timelineExtension(goal, gap) {
  if (!isValidGap(gap) || !isValidGoal(goal)) {
    return null;
  }

  const currentTimeline = toNumber(goal.timeline, 0);
  if (currentTimeline <= 0) {
    return null;
  }

  const newTimeline = roundCurrency(currentTimeline * 1.5);
  const monthlyAfter = roundCurrency(toNumber(gap.monthlyToSave, 0) * (currentTimeline / newTimeline));
  const savingsTarget = Math.max(0, toNumber(gap.savingsGap, 0));

  return {
    pathId: 'timeline_extension',
    title: 'Extend Timeline',
    description: 'Give yourself more time to save and reduce monthly pressure',
    monthlyBoost: 0,
    monthlyAfter,
    newTimeline,
    timeline: 'Immediate',
    feasibility: 'Very High',
    tradeoff: 'Takes longer to reach goal',
    pros: [
      'Lowers required monthly savings immediately',
      'Reduces risk of financial strain',
      'Works even when income options are limited',
    ],
    cons: [
      'Delays goal achievement',
      'Life circumstances may change over a longer horizon',
      'Motivation can fade with distant deadlines',
    ],
    action: `adjustGoalTimeline(goalId, ${newTimeline})`,
    actionItems: [
      `Extend goal timeline from ${currentTimeline} to ${newTimeline} years`,
      `New monthly savings target: ${monthlyAfter}`,
      'Set quarterly check-ins to stay on track',
    ],
    projections: projectPathOverTime({
      startingSavings: 0,
      savingsTarget,
      timelineYears: newTimeline,
      monthlyBoost: monthlyAfter,
    }),
  };
}

/**
 * @param {Object} goal
 * @param {RecommendationGap} gap
 * @returns {RecommendationPath | null}
 */
export function goalScopeReduction(goal, gap) {
  if (!isValidGap(gap) || !isValidGoal(goal)) {
    return null;
  }

  const flatGoal = extractGoalParameters(goal);
  if (!flatGoal) {
    return null;
  }

  const options = buildScopeReductionOptions(goal, flatGoal, gap);
  const bestOption = options.reduce((best, option) => {
    const saves = toNumber(option.saves, 0);
    return saves > toNumber(best?.saves, 0) ? option : best;
  }, options[0]);

  const monthlyBoost = roundCurrency(
    toNumber(bestOption?.saves, 0) / Math.max(1, toNumber(goal.timeline, 1) * 12),
  );

  return {
    pathId: 'goal_scope_reduction',
    title: 'Reduce Goal Scope',
    description: 'Achieve the goal sooner by adjusting price, scope, or timing expectations',
    monthlyBoost,
    timeline: '1-3 months',
    feasibility: 'High',
    tradeoff: 'Get less, but achieve sooner',
    options,
    pros: [
      'Meaningfully lowers total cash required',
      'Keeps goal within reach on current income',
      'Flexible — mix price cuts and timeline shifts',
    ],
    cons: [
      'May not match original vision',
      'Tradeoffs can affect quality of outcome',
      'Requires resetting expectations',
    ],
    action: 'presentScopeReductionOptions(goalId, options)',
    actionItems: options.map((option) => `Evaluate: ${option.name}`),
    projections: projectPathOverTime({
      startingSavings: 0,
      savingsTarget: Math.max(0, toNumber(gap.savingsGap, 0) - toNumber(bestOption?.saves, 0)),
      timelineYears: toNumber(goal.timeline, 1),
      monthlyBoost,
    }),
  };
}

/**
 * @param {Object} goal
 * @param {RecommendationGap} gap
 * @param {Record<string, unknown>} userProfile
 * @returns {RecommendationPath | null}
 */
export function financing(goal, gap, userProfile) {
  if (!isValidGap(gap) || !isValidGoal(goal)) {
    return null;
  }

  const flatGoal = extractGoalParameters(goal);
  if (!flatGoal) {
    return null;
  }

  const cost = costCalculator(flatGoal);
  const options = buildFinancingOptions(goal, flatGoal);
  if (!cost || options.length === 0) {
    return null;
  }

  const bestOption = options[0];
  const upfrontNeeded = toNumber(bestOption.upfrontNeeded, cost.totalCost);
  const savings = Math.max(0, toNumber(userProfile?.savings, 0));
  const financedGap = Math.max(0, upfrontNeeded - savings);
  const timelineYears = Math.max(1, toNumber(goal.timeline, 1));
  const monthlyBoost = roundCurrency(financedGap / (timelineYears * 12));

  return {
    pathId: 'financing',
    title: 'Use Financing',
    description: 'Leverage loans or financing to reduce upfront cash requirements',
    monthlyBoost,
    timeline: '2-8 weeks',
    feasibility: 'Very High',
    tradeoff: 'Pay interest, achieve goal faster',
    options,
    pros: [
      'Achieves goal with less upfront savings',
      'Preserves cash for emergencies',
      'Works well for large purchases like homes and cars',
    ],
    cons: [
      'Interest increases total lifetime cost',
      'Adds monthly debt obligations',
      'Approval depends on credit and income',
    ],
    action: `suggestFinancingOptions(${goal.type}, ${roundCurrency(upfrontNeeded)})`,
    actionItems: [
      'Compare APR, term length, and monthly payment across lenders',
      'Stress-test payments against future monthly expenses',
      'Keep total debt payments below 36% of gross income',
    ],
    projections: projectPathOverTime({
      startingSavings: savings,
      savingsTarget: upfrontNeeded,
      timelineYears,
      monthlyBoost,
    }),
  };
}

/**
 * @param {Record<string, unknown>} userProfile
 * @param {Object} goal
 * @param {RecommendationGap} gap
 * @returns {RecommendationPath | null}
 */
export function combined(userProfile, goal, gap) {
  if (!isValidGap(gap) || !isValidGoal(goal)) {
    return null;
  }

  const monthlyNeeded = getMonthlyNeeded(gap);
  const career = careerAdvancement(userProfile, goal, gap);
  const side = sideIncome(userProfile, goal, gap);
  const expenses = expenseReduction(userProfile, goal, gap);

  const merged = combinePaths(
    [career, side, expenses].filter(Boolean),
    { monthlyNeeded },
  );

  const savingsTarget = getSavingsTarget(userProfile, gap);
  const timelineYears = Math.max(1, toNumber(goal.timeline, 1));

  return {
    pathId: 'combined',
    title: 'RECOMMENDED - Combined Strategy',
    description: 'Mix of career growth, side income, and expense cuts for the most realistic path',
    monthlyBoost: merged.monthlyBoost ?? 0,
    timeline: '3-12 months to full effect',
    feasibility: 'High',
    mostRealistic: true,
    combinedPaths: merged.combinedPaths ?? [],
    pros: merged.pros ?? [],
    cons: merged.cons ?? [],
    action: 'buildCombinedActionPlan(userProfile, goal, gap)',
    actionItems: merged.actionItems ?? [],
    projections: projectPathOverTime({
      startingSavings: toNumber(userProfile?.savings, 0),
      savingsTarget,
      timelineYears,
      monthlyBoost: merged.monthlyBoost ?? 0,
      rampMonths: CAREER_RAMP_MONTHS,
    }),
  };
}

/** @type {Record<string, Function>} */
export const recommendationPaths = {
  careerAdvancement,
  sideIncome,
  expenseReduction,
  timelineExtension,
  goalScopeReduction,
  financing,
  combined,
};

export default recommendationPaths;
