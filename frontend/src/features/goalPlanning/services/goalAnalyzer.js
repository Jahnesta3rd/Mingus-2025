import {
  costCalculator,
  expenseIncreaseCalculator,
  gapCalculator,
  incomeNeededCalculator,
} from './calculators/index.js';

/**
 * @typedef {Object} AnalyzerUserProfile
 * @property {string} [id]
 * @property {number} [income] - Monthly income
 * @property {number} [savings]
 * @property {number} [expenses] - Monthly expenses
 * @property {string} [jobTitle]
 * @property {string} [industry]
 * @property {string[]} [skills]
 * @property {number} [availableHours] - Hours per week available for extra work
 */

/**
 * @typedef {Object} AnalyzerGoal
 * @property {string} type
 * @property {Record<string, unknown>} [parameters]
 * @property {number} [timeline] - Timeline in years
 * @property {string[]} [constraints]
 */

const GOAL_DESCRIPTIONS = {
  home_purchase: 'Buy a home',
  car_purchase: 'Purchase a vehicle',
  apartment_move: 'Move to a new apartment',
  baby: 'Prepare for a new baby',
  business: 'Launch a business',
  sabbatical: 'Take a sabbatical',
};

const REQUIRED_GOAL_FIELDS = {
  home_purchase: ['homePrice'],
  car_purchase: ['carPrice'],
  apartment_move: ['monthlyRent'],
  baby: ['preparationCost'],
  business: ['initialInvestment', 'monthlyCost'],
};

const REQUIRED_PROFILE_FIELDS = ['income', 'savings', 'expenses'];
const OPTIONAL_PROFILE_FIELDS = ['jobTitle', 'industry', 'skills', 'availableHours'];

/**
 * Rounds a currency value to two decimal places.
 * @param {number} value
 * @returns {number}
 */
function roundCurrency(value) {
  return Math.round(value * 100) / 100;
}

/**
 * Coerces a value to a finite number.
 * @param {unknown} value
 * @param {number} fallback
 * @returns {number}
 */
function toNumber(value, fallback = 0) {
  if (typeof value !== 'number' || !Number.isFinite(value)) {
    return fallback;
  }
  return value;
}

/**
 * Formats a number as a compact USD currency string.
 * @param {number} value
 * @returns {string}
 */
function formatCurrency(value) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  }).format(Math.round(value));
}

/**
 * Merges goal type and parameters into a flat calculator-compatible object.
 * @param {AnalyzerGoal | null | undefined} goal
 * @returns {Record<string, unknown> | null}
 */
export function extractGoalParameters(goal) {
  if (!goal || typeof goal !== 'object' || typeof goal.type !== 'string' || !goal.type) {
    return null;
  }

  const parameters = goal.parameters && typeof goal.parameters === 'object'
    ? goal.parameters
    : {};

  return {
    type: goal.type,
    ...parameters,
  };
}

/**
 * Generates a stable goal identifier.
 * @param {AnalyzerUserProfile | null | undefined} userProfile
 * @param {AnalyzerGoal | null | undefined} goal
 * @returns {string}
 */
function generateGoalId(userProfile, goal) {
  const userId = userProfile?.id ?? 'user';
  const goalType = goal?.type ?? 'unknown';
  const timeline = toNumber(goal?.timeline, 0);
  return `goal-${userId}-${goalType}-${timeline}`;
}

/**
 * Builds a human-readable goal description.
 * @param {AnalyzerGoal | null | undefined} goal
 * @param {Record<string, unknown> | null} flatGoal
 * @returns {string}
 */
function buildGoalDescription(goal, flatGoal) {
  const base = GOAL_DESCRIPTIONS[goal?.type ?? ''] ?? 'Reach a financial goal';
  if (!flatGoal) {
    return base;
  }

  switch (goal?.type) {
    case 'home_purchase':
      return `${base} at ${formatCurrency(toNumber(flatGoal.homePrice, 0))}`;
    case 'car_purchase':
      return `${base} for ${formatCurrency(toNumber(flatGoal.carPrice, 0))}`;
    case 'apartment_move':
      return `${base} with rent of ${formatCurrency(toNumber(flatGoal.monthlyRent, 0))}/mo`;
    case 'baby':
      return `${base} with ${formatCurrency(toNumber(flatGoal.preparationCost, 0))} preparation budget`;
    case 'business':
      return `${base} with ${formatCurrency(toNumber(flatGoal.initialInvestment, 0))} startup capital`;
    default:
      return base;
  }
}

/**
 * Calculates savings rate as a percentage of monthly income.
 * @param {number} monthlyIncome
 * @param {number} monthlyExpenses
 * @returns {number}
 */
function calculateSavingsRate(monthlyIncome, monthlyExpenses) {
  if (monthlyIncome <= 0) {
    return 0;
  }
  const rate = ((monthlyIncome - monthlyExpenses) / monthlyIncome) * 100;
  return roundCurrency(Math.max(-100, Math.min(100, rate)));
}

/**
 * Assesses how complete the input data is for analysis.
 * @param {AnalyzerUserProfile | null | undefined} userProfile
 * @param {AnalyzerGoal | null | undefined} goal
 * @param {Record<string, unknown> | null} flatGoal
 * @returns {{ required: number, optional: number, missingFields: string[] }}
 */
function assessDataCompleteness(userProfile, goal, flatGoal) {
  const missingFields = [];

  const requiredGoalFields = REQUIRED_GOAL_FIELDS[goal?.type ?? ''] ?? [];
  requiredGoalFields.forEach((field) => {
    const value = flatGoal?.[field];
    if (typeof value !== 'number' || !Number.isFinite(value)) {
      missingFields.push(`goal.parameters.${field}`);
    }
  });

  if (!goal?.timeline || !Number.isFinite(goal.timeline) || goal.timeline <= 0) {
    missingFields.push('goal.timeline');
  }

  REQUIRED_PROFILE_FIELDS.forEach((field) => {
    const value = userProfile?.[field];
    if (typeof value !== 'number' || !Number.isFinite(value)) {
      missingFields.push(`userProfile.${field}`);
    }
  });

  const requiredTotal = requiredGoalFields.length + 1 + REQUIRED_PROFILE_FIELDS.length;
  const requiredPresent = requiredTotal - missingFields.length;
  const required = requiredTotal > 0 ? Math.max(0, requiredPresent / requiredTotal) : 0;

  let optionalPresent = 0;
  OPTIONAL_PROFILE_FIELDS.forEach((field) => {
    const value = userProfile?.[field];
    if (field === 'skills') {
      if (Array.isArray(value) && value.length > 0) {
        optionalPresent += 1;
      }
      return;
    }
    if (typeof value === 'string' && value.trim()) {
      optionalPresent += 1;
      return;
    }
    if (typeof value === 'number' && Number.isFinite(value) && value > 0) {
      optionalPresent += 1;
    }
  });

  const optional = OPTIONAL_PROFILE_FIELDS.length > 0
    ? optionalPresent / OPTIONAL_PROFILE_FIELDS.length
    : 0;

  return {
    required: roundCurrency(required),
    optional: roundCurrency(optional),
    missingFields,
  };
}

/**
 * Computes a 0–100 feasibility score from savings and income constraints.
 * @param {Object} params
 * @param {number} params.savingsGap
 * @param {boolean} params.savingsFeasible
 * @param {number} params.incomeGap
 * @param {number} params.monthlyIncome
 * @param {number} params.monthlyToSave
 * @param {number} params.savingsRate
 * @returns {number}
 */
export function calculateFeasibilityScore({
  savingsGap,
  savingsFeasible,
  incomeGap,
  monthlyIncome,
  monthlyToSave,
  savingsRate,
}) {
  if (savingsGap <= 0) {
    return incomeGap > 0 ? Math.max(40, 100 - Math.min(60, incomeGap / 1000)) : 100;
  }

  let score = 100;

  if (!savingsFeasible) {
    const burdenRatio = monthlyIncome > 0 ? monthlyToSave / (monthlyIncome / 2) : 2;
    score -= Math.min(45, Math.max(20, burdenRatio * 20));
  }

  if (incomeGap > 0 && monthlyIncome > 0) {
    const incomeGapRatio = incomeGap / (monthlyIncome * 12);
    score -= Math.min(35, incomeGapRatio * 100);
  }

  if (savingsRate < 5) {
    score -= 10;
  } else if (savingsRate >= 20) {
    score += 5;
  }

  return Math.max(0, Math.min(100, Math.round(score)));
}

/**
 * Generates a narrative summary of the goal analysis.
 * @param {Object} params
 * @param {string} params.goalDescription
 * @param {number} params.savingsTarget
 * @param {number} params.timelineYears
 * @param {number} params.currentSavings
 * @param {number} params.savingsGap
 * @param {number} params.projectedSavingsOnCurrentPath
 * @returns {string}
 */
export function generateAnalysisSummary({
  goalDescription,
  savingsTarget,
  timelineYears,
  currentSavings,
  savingsGap,
  projectedSavingsOnCurrentPath,
}) {
  const timelineLabel = timelineYears === 1 ? '1 year' : `${timelineYears} years`;

  if (savingsGap <= 0) {
    return `You already have enough saved for ${goalDescription.toLowerCase()} (${formatCurrency(currentSavings)} vs ${formatCurrency(savingsTarget)} needed).`;
  }

  return `You need ${formatCurrency(savingsTarget)} in ${timelineLabel} for ${goalDescription.toLowerCase()}. Your current savings path gets you about ${formatCurrency(projectedSavingsOnCurrentPath)}.`;
}

/**
 * Identifies primary challenges blocking goal achievement.
 * @param {Object} params
 * @param {number} params.savingsGap
 * @param {boolean} params.savingsFeasible
 * @param {number} params.incomeGap
 * @param {number} params.monthlyToSave
 * @param {number} params.monthlyIncome
 * @param {number} params.expenseIncrease
 * @param {number} params.savingsRate
 * @param {number} params.timelineYears
 * @returns {string[]}
 */
export function identifyChallenges({
  savingsGap,
  savingsFeasible,
  incomeGap,
  monthlyToSave,
  monthlyIncome,
  expenseIncrease,
  savingsRate,
  timelineYears,
}) {
  const challenges = [];

  if (savingsGap <= 0 && incomeGap <= 0) {
    return challenges;
  }

  if (!savingsFeasible && savingsGap > 0) {
    challenges.push(
      `Timeline may be too short — saving ${formatCurrency(monthlyToSave)}/mo exceeds half your monthly income.`,
    );
  }

  if (incomeGap > 0) {
    challenges.push(
      `Income may be too low — you need about ${formatCurrency(incomeGap)} more per year to support this goal.`,
    );
  }

  if (savingsRate < 10 && savingsGap > 0) {
    challenges.push('Low savings rate leaves little room to fund this goal on your current budget.');
  }

  if (expenseIncrease > 0 && monthlyIncome > 0 && expenseIncrease > monthlyIncome * 0.15) {
    challenges.push(
      `Monthly expenses would rise by ${formatCurrency(expenseIncrease)}, adding significant budget pressure.`,
    );
  }

  if (timelineYears < 1 && savingsGap > 0) {
    challenges.push('Aggressive timeline under one year leaves limited time to build savings.');
  }

  if (challenges.length === 0 && savingsGap > 0) {
    challenges.push('Closing the savings gap still requires consistent contributions every month.');
  }

  return challenges;
}

/**
 * Identifies opportunities to accelerate goal progress.
 * @param {Object} params
 * @param {AnalyzerUserProfile | null | undefined} userProfile
 * @param {number} params.incomeGap
 * @param {number} params.savingsGap
 * @param {number} params.savingsRate
 * @param {string} [params.goalType]
 * @returns {string[]}
 */
export function identifyOpportunities(userProfile, {
  incomeGap,
  savingsGap,
  savingsRate,
  goalType,
}) {
  const opportunities = [];
  const skills = Array.isArray(userProfile?.skills) ? userProfile.skills : [];
  const availableHours = toNumber(userProfile?.availableHours, 0);

  if (savingsGap <= 0) {
    opportunities.push('Savings target is already met — focus on maintaining your emergency buffer.');
    return opportunities;
  }

  if (incomeGap > 0) {
    opportunities.push('A raise, promotion, or job change could close your income gap fastest.');
    if (userProfile?.industry) {
      opportunities.push(`Explore higher-paying roles in ${userProfile.industry}.`);
    }
  }

  if (availableHours >= 5) {
    opportunities.push('Side income from freelance or gig work could boost monthly savings.');
  }

  if (skills.length > 0) {
    opportunities.push(`Monetize skills like ${skills.slice(0, 3).join(', ')} for extra income.`);
  }

  if (savingsRate < 15) {
    opportunities.push('Trim discretionary spending to free up more monthly savings.');
  } else if (savingsRate >= 20) {
    opportunities.push('Strong savings habits — redirect part of your current surplus toward this goal.');
  }

  if (goalType === 'home_purchase') {
    opportunities.push('Consider down-payment assistance programs or a longer timeline to reduce monthly pressure.');
  }

  if (goalType === 'business' && skills.length > 0) {
    opportunities.push('Start lean with a minimum viable offer before committing full startup costs.');
  }

  if (opportunities.length === 0) {
    opportunities.push('Automate monthly transfers to keep savings consistent.');
  }

  return opportunities;
}

/**
 * Picks the most important insight from gap and income analysis.
 * @param {Object} params
 * @param {number} params.savingsGap
 * @param {number} params.incomeGap
 * @param {boolean} params.savingsFeasible
 * @param {number} params.monthlyToSave
 * @returns {string}
 */
function generateKeyInsight({ savingsGap, incomeGap, savingsFeasible, monthlyToSave }) {
  if (savingsGap <= 0 && incomeGap <= 0) {
    return 'You are financially positioned for this goal — execution and timing are your main focus.';
  }

  if (incomeGap > 0 && (!savingsFeasible || incomeGap > monthlyToSave * 12)) {
    return `Your main constraint is income. You may need about ${formatCurrency(incomeGap)}/year more to support this goal comfortably.`;
  }

  if (!savingsFeasible) {
    return `Your main constraint is time — saving ${formatCurrency(monthlyToSave)}/mo on your current timeline is aggressive.`;
  }

  if (savingsGap > 0) {
    return `Your main lever is savings discipline — set aside ${formatCurrency(monthlyToSave)}/mo to stay on track.`;
  }

  return 'Review your timeline and budget to keep this goal achievable.';
}

/**
 * Analyzes a financial goal against a user profile.
 * @param {AnalyzerUserProfile | null | undefined} userProfile
 * @param {AnalyzerGoal | null | undefined} goal
 * @returns {object | null}
 */
export function analyzeGoal(userProfile, goal) {
  const flatGoal = extractGoalParameters(goal);
  if (!flatGoal || !goal?.timeline || !Number.isFinite(goal.timeline) || goal.timeline <= 0) {
    return null;
  }

  const cost = costCalculator(flatGoal);
  if (!cost) {
    return null;
  }

  const monthlyIncome = Math.max(0, toNumber(userProfile?.income, 0));
  const monthlyExpenses = Math.max(0, toNumber(userProfile?.expenses, 0));
  const savings = Math.max(0, toNumber(userProfile?.savings, 0));
  const annualIncome = monthlyIncome * 12;
  const annualExpenses = monthlyExpenses * 12;
  const savingsRate = calculateSavingsRate(monthlyIncome, monthlyExpenses);
  const timelineYears = goal.timeline;

  const calculatorProfile = {
    savings,
    income: monthlyIncome,
    expenses: monthlyExpenses,
  };

  const gap = gapCalculator(flatGoal, calculatorProfile, timelineYears);
  if (!gap) {
    return null;
  }

  const expenseChange = expenseIncreaseCalculator(flatGoal, annualExpenses);
  const futureMonthlyExpenses = expenseChange?.newMonthly ?? monthlyExpenses;
  const incomeNeeded = incomeNeededCalculator(goal.type, futureMonthlyExpenses, annualIncome);

  const savingsGap = roundCurrency(gap.gap);
  const incomeGap = roundCurrency(incomeNeeded?.insufficientBy ?? 0);
  const expenseIncrease = roundCurrency(expenseChange?.monthlyIncrease ?? 0);
  const monthlyToSave = roundCurrency(gap.monthlyToSave);
  const savingsFeasible = gap.feasible;
  const incomeFeasible = incomeGap <= 0;
  const feasible = (savingsGap <= 0 || savingsFeasible) && incomeFeasible;

  const monthlySurplus = Math.max(0, monthlyIncome - monthlyExpenses);
  const projectedSavingsOnCurrentPath = roundCurrency(
    savings + monthlySurplus * timelineYears * 12,
  );

  const futureIncome = roundCurrency(
    incomeNeeded?.neededMonthly ?? monthlyIncome,
  );

  const feasibilityScore = calculateFeasibilityScore({
    savingsGap,
    savingsFeasible,
    incomeGap,
    monthlyIncome,
    monthlyToSave,
    savingsRate,
  });

  const goalDescription = buildGoalDescription(goal, flatGoal);
  const dataCompleteness = assessDataCompleteness(userProfile, goal, flatGoal);

  const analysisParams = {
    savingsGap,
    savingsFeasible,
    incomeGap,
    monthlyToSave,
    monthlyIncome,
    expenseIncrease,
    savingsRate,
    timelineYears,
  };

  const summary = generateAnalysisSummary({
    goalDescription,
    savingsTarget: cost.totalCost,
    timelineYears,
    currentSavings: savings,
    savingsGap,
    projectedSavingsOnCurrentPath,
  });

  return {
    goalId: generateGoalId(userProfile, goal),
    goalType: goal.type,
    goalDescription,

    presentState: {
      income: roundCurrency(monthlyIncome),
      monthlyExpenses: roundCurrency(monthlyExpenses),
      savings: roundCurrency(savings),
      savingsRate,
      jobTitle: userProfile?.jobTitle ?? '',
      skills: Array.isArray(userProfile?.skills) ? [...userProfile.skills] : [],
      availableHours: toNumber(userProfile?.availableHours, 0),
    },

    futureState: {
      income: futureIncome,
      monthlyExpenses: roundCurrency(futureMonthlyExpenses),
      savingsTarget: roundCurrency(cost.totalCost),
      timelineYears,
    },

    gaps: {
      savingsGap,
      incomeGap,
      expenseIncrease,
      monthlyToSave,
      feasible,
      feasibilityScore,
    },

    analysis: {
      summary,
      keyInsight: generateKeyInsight({
        savingsGap,
        incomeGap,
        savingsFeasible,
        monthlyToSave,
      }),
      challenges: identifyChallenges(analysisParams),
      opportunities: identifyOpportunities(userProfile, {
        incomeGap,
        savingsGap,
        savingsRate,
        goalType: goal.type,
      }),
    },

    dataCompleteness,
  };
}

export default analyzeGoal;
