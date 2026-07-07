/**
 * @typedef {'home_purchase' | 'car_purchase' | 'apartment_move' | 'baby' | 'business' | 'sabbatical'} GoalType
 */

/**
 * @typedef {Object} Goal
 * @property {GoalType | string} type
 * @property {number} [homePrice]
 * @property {number} [carPrice]
 * @property {number} [monthlyRent]
 * @property {number} [movingCosts]
 * @property {number} [preparationCost]
 * @property {number} [initialInvestment]
 * @property {number} [monthlyCost]
 * @property {number} [downPaymentAmount]
 */

/**
 * @typedef {Object} UserProfile
 * @property {number} [savings]
 * @property {number} [income] - Monthly income used for feasibility checks
 * @property {number} [expenses]
 */

/**
 * @typedef {Object} CostResult
 * @property {number} totalCost
 * @property {Record<string, number>} breakdown
 */

/**
 * @typedef {Object} GapResult
 * @property {number} totalNeeded
 * @property {number} haveNow
 * @property {number} gap
 * @property {number} monthlyToSave
 * @property {number} yearlyToSave
 * @property {boolean} feasible
 */

/**
 * @typedef {Object} IncomeNeededResult
 * @property {number} neededAnnualIncome
 * @property {number} neededMonthly
 * @property {number | null} insufficientBy
 */

/**
 * @typedef {Object} ExpenseIncreaseResult
 * @property {number} currentMonthly
 * @property {number} newMonthly
 * @property {number} monthlyIncrease
 * @property {number} annualIncrease
 */

/**
 * @typedef {Object} SavingsProjectionPoint
 * @property {number} year
 * @property {number} cumulativeSavings
 * @property {boolean} goalReached
 */

const HOME_CLOSING_COST_RATE = 0.05;
const CAR_TAX_FEE_RATE = 0.1;
const APARTMENT_DEPOSIT_MONTHS = 3;
const BUSINESS_RUNWAY_MONTHS = 6;
const BABY_ANNUAL_EXPENSE = 15000;

const INCOME_RULES = {
  home_purchase: 0.28,
  car_purchase: 0.15,
  apartment_move: 0.3,
  baby: null,
  business: null,
  sabbatical: null,
};

const INCOME_MULTIPLIERS = {
  baby: 1.5,
  business: 2.0,
};

/**
 * Rounds a currency value to two decimal places.
 * @param {number} value
 * @returns {number}
 */
function roundCurrency(value) {
  return Math.round(value * 100) / 100;
}

/**
 * Coerces a value to a finite number, returning a fallback otherwise.
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
 * Returns true when the goal object has a usable type string.
 * @param {unknown} goal
 * @returns {goal is Goal}
 */
function isValidGoal(goal) {
  return Boolean(goal && typeof goal === 'object' && typeof goal.type === 'string' && goal.type.length > 0);
}

/**
 * Returns true when timeline is a positive finite number (years).
 * @param {unknown} timeline
 * @returns {boolean}
 */
function isValidTimeline(timeline) {
  return typeof timeline === 'number' && Number.isFinite(timeline) && timeline > 0;
}

/**
 * Calculates total cost for a financial goal.
 * @param {Goal | null | undefined} goal
 * @returns {CostResult | null}
 */
export function costCalculator(goal) {
  if (!isValidGoal(goal)) {
    return null;
  }

  const type = goal.type;

  switch (type) {
    case 'home_purchase': {
      const homePrice = toNumber(goal.homePrice, NaN);
      if (!Number.isFinite(homePrice) || homePrice < 0) {
        return null;
      }
      const closingCosts = homePrice * HOME_CLOSING_COST_RATE;
      return {
        totalCost: homePrice + closingCosts,
        breakdown: {
          homePrice,
          closingCosts,
        },
      };
    }
    case 'car_purchase': {
      const carPrice = toNumber(goal.carPrice, NaN);
      if (!Number.isFinite(carPrice) || carPrice < 0) {
        return null;
      }
      const taxesAndFees = carPrice * CAR_TAX_FEE_RATE;
      return {
        totalCost: carPrice + taxesAndFees,
        breakdown: {
          carPrice,
          taxesAndFees,
        },
      };
    }
    case 'apartment_move': {
      const monthlyRent = toNumber(goal.monthlyRent, NaN);
      if (!Number.isFinite(monthlyRent) || monthlyRent < 0) {
        return null;
      }
      const movingCosts = Math.max(0, toNumber(goal.movingCosts, 0));
      const deposit = monthlyRent * APARTMENT_DEPOSIT_MONTHS;
      return {
        totalCost: deposit + movingCosts,
        breakdown: {
          deposit,
          movingCosts,
        },
      };
    }
    case 'baby': {
      const preparationCost = toNumber(goal.preparationCost, NaN);
      if (!Number.isFinite(preparationCost) || preparationCost < 0) {
        return null;
      }
      return {
        totalCost: preparationCost,
        breakdown: {
          preparationCost,
        },
      };
    }
    case 'business': {
      const initialInvestment = toNumber(goal.initialInvestment, NaN);
      const monthlyCost = toNumber(goal.monthlyCost, NaN);
      if (
        !Number.isFinite(initialInvestment)
        || !Number.isFinite(monthlyCost)
        || initialInvestment < 0
        || monthlyCost < 0
      ) {
        return null;
      }
      const runway = monthlyCost * BUSINESS_RUNWAY_MONTHS;
      return {
        totalCost: initialInvestment + runway,
        breakdown: {
          initialInvestment,
          runway,
        },
      };
    }
    default:
      return null;
  }
}

/**
 * Calculates savings gap and monthly savings target for a goal.
 * @param {Goal | null | undefined} goal
 * @param {UserProfile | null | undefined} userProfile
 * @param {number} timeline - Timeline in years (fractional values supported, e.g. 0.5 = 6 months)
 * @returns {GapResult | null}
 */
export function gapCalculator(goal, userProfile, timeline) {
  if (!isValidGoal(goal) || !isValidTimeline(timeline)) {
    return null;
  }

  const cost = costCalculator(goal);
  if (!cost) {
    return null;
  }

  const profile = userProfile ?? {};
  const downPaymentAmount = toNumber(goal.downPaymentAmount, NaN);
  const haveNow = Number.isFinite(downPaymentAmount)
    ? downPaymentAmount
    : Math.max(0, toNumber(profile.savings, 0));

  const totalNeeded = cost.totalCost;
  const gap = totalNeeded - haveNow;
  const months = timeline * 12;
  const monthlyToSave = gap / months;
  const yearlyToSave = gap / timeline;
  const monthlyIncome = Math.max(0, toNumber(profile.income, 0));
  const feasible = monthlyToSave < monthlyIncome / 2;

  return {
    totalNeeded,
    haveNow,
    gap,
    monthlyToSave,
    yearlyToSave,
    feasible,
  };
}

/**
 * Estimates income required to support future monthly expenses for a goal state.
 * @param {Goal | string | null | undefined} goal - Goal object or goal type string
 * @param {number} futureExpenses - Projected monthly expenses after the goal
 * @param {number} [currentAnnualIncome] - Optional current annual income for insufficientBy
 * @returns {IncomeNeededResult | null}
 */
export function incomeNeededCalculator(goal, futureExpenses, currentAnnualIncome) {
  const goalType = typeof goal === 'string' ? goal : goal?.type;
  if (!goalType || typeof goalType !== 'string') {
    return null;
  }

  const monthlyExpenses = toNumber(futureExpenses, NaN);
  if (!Number.isFinite(monthlyExpenses) || monthlyExpenses < 0) {
    return null;
  }

  let neededMonthly = null;

  if (goalType in INCOME_RULES && INCOME_RULES[goalType] !== null) {
    neededMonthly = monthlyExpenses / INCOME_RULES[goalType];
  } else if (goalType in INCOME_MULTIPLIERS) {
    neededMonthly = monthlyExpenses * INCOME_MULTIPLIERS[goalType];
  } else if (goalType === 'sabbatical') {
    neededMonthly = monthlyExpenses;
  } else {
    return null;
  }

  const neededMonthlyRounded = roundCurrency(neededMonthly);
  const neededAnnualIncome = roundCurrency(neededMonthlyRounded * 12);
  const currentIncome = toNumber(currentAnnualIncome, NaN);
  const insufficientBy = Number.isFinite(currentIncome)
    ? roundCurrency(Math.max(0, neededAnnualIncome - currentIncome))
    : null;

  return {
    neededAnnualIncome,
    neededMonthly: neededMonthlyRounded,
    insufficientBy,
  };
}

/**
 * Estimates how monthly and annual expenses change after a goal.
 * @param {Goal | null | undefined} goal
 * @param {number} currentExpenses - Current annual expenses
 * @returns {ExpenseIncreaseResult | null}
 */
export function expenseIncreaseCalculator(goal, currentExpenses) {
  if (!isValidGoal(goal)) {
    return null;
  }

  const annualExpenses = toNumber(currentExpenses, NaN);
  if (!Number.isFinite(annualExpenses) || annualExpenses < 0) {
    return null;
  }

  const currentMonthly = annualExpenses / 12;
  let annualIncrease = 0;

  switch (goal.type) {
    case 'home_purchase': {
      const homePrice = toNumber(goal.homePrice, NaN);
      if (!Number.isFinite(homePrice) || homePrice < 0) {
        return null;
      }
      annualIncrease = homePrice * 0.005;
      break;
    }
    case 'car_purchase': {
      const carPrice = toNumber(goal.carPrice, NaN);
      if (!Number.isFinite(carPrice) || carPrice < 0) {
        return null;
      }
      annualIncrease = carPrice * 0.08;
      break;
    }
    case 'apartment_move': {
      const monthlyRent = toNumber(goal.monthlyRent, NaN);
      if (!Number.isFinite(monthlyRent) || monthlyRent < 0) {
        return null;
      }
      annualIncrease = monthlyRent * 12;
      break;
    }
    case 'baby':
      annualIncrease = BABY_ANNUAL_EXPENSE;
      break;
    case 'sabbatical':
      annualIncrease = 0;
      break;
    case 'business':
      annualIncrease = Math.max(0, toNumber(goal.monthlyCost, 0)) * 12;
      break;
    default:
      return null;
  }

  const monthlyIncrease = annualIncrease / 12;
  const newMonthly = currentMonthly + monthlyIncrease;

  return {
    currentMonthly,
    newMonthly,
    monthlyIncrease,
    annualIncrease,
  };
}

/**
 * Projects cumulative savings year-by-year toward a goal.
 * @param {{ income?: number, savings?: number } | null | undefined} presentState
 * @param {Goal | null | undefined} goal
 * @param {number} timeline - Timeline in years
 * @param {number} monthlyBoost - Additional monthly savings toward the goal
 * @returns {SavingsProjectionPoint[]}
 */
export function projectSavingsOverTime(presentState, goal, timeline, monthlyBoost) {
  if (!isValidGoal(goal) || !isValidTimeline(timeline)) {
    return [];
  }

  const cost = costCalculator(goal);
  if (!cost) {
    return [];
  }

  const boost = toNumber(monthlyBoost, NaN);
  if (!Number.isFinite(boost)) {
    return [];
  }

  const target = cost.totalCost;
  let cumulativeSavings = Math.max(0, toNumber(presentState?.savings, 0));
  const projection = [];

  const fullYears = Math.floor(timeline);
  const fractionalYears = timeline - fullYears;
  const totalIterations = fractionalYears > 0 ? fullYears + 1 : fullYears;

  for (let year = 1; year <= totalIterations; year += 1) {
    const monthsInPeriod = year <= fullYears
      ? 12
      : Math.max(1, Math.round(fractionalYears * 12));

    cumulativeSavings += boost * monthsInPeriod;

    projection.push({
      year,
      cumulativeSavings,
      goalReached: cumulativeSavings >= target,
    });
  }

  return projection;
}
