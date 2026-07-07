import { callClaudeApi, CLAUDE_MODEL } from './claudeClient.js';

/**
 * @typedef {Object} ExpenseCategory
 * @property {string} categoryId
 * @property {string} category
 * @property {number} currentMonthly
 */

/**
 * @typedef {Object} ExpenseCutSuggestion
 * @property {string} categoryId
 * @property {string} category
 * @property {number} currentMonthly
 * @property {string} suggestionId
 * @property {string} suggestion
 * @property {number} potentialSavings
 * @property {'Easy' | 'Medium' | 'Hard'} difficulty
 * @property {'None' | 'Minor' | 'Moderate' | 'Significant'} impactOnLifestyle
 * @property {'Immediate' | '30 days' | 'Gradual'} timeline
 * @property {string[]} pros
 * @property {string[]} cons
 * @property {string[]} actionSteps
 * @property {string[]} warningFlags
 * @property {string} [source]
 */

const DIFFICULTY_SCORE = { Easy: 1, Medium: 2, Hard: 3 };
const LIFESTYLE_SCORE = { None: 0, Minor: 1, Moderate: 2, Significant: 3 };

const DEFAULT_ALLOCATION = {
  housing: 0.35,
  dining: 0.15,
  subscriptions: 0.04,
  transport: 0.12,
  entertainment: 0.08,
  insurance: 0.08,
  groceries: 0.12,
  utilities: 0.06,
};

/**
 * Cut knowledge base templates per category.
 */
const CUT_KB = [
  {
    categoryId: 'housing',
    category: 'housing',
    suggestionId: 'housing_roommate',
    suggestion: 'Add a roommate or house share to split rent',
    savingsRate: 0.4,
    savingsMin: 400,
    savingsMax: 600,
    difficulty: 'Hard',
    impactOnLifestyle: 'Significant',
    timeline: '30 days',
    pros: ['Largest housing savings lever', 'Can accelerate savings quickly'],
    cons: ['Less privacy', 'Requires compatible roommate search'],
    actionSteps: ['List spare room on local housing groups', 'Screen candidates and set house rules', 'Split utilities in writing'],
    warningFlags: ['Review lease terms before subletting'],
    healthSafetyRisk: false,
  },
  {
    categoryId: 'housing',
    category: 'housing',
    suggestionId: 'housing_refinance',
    suggestion: 'Refinance mortgage if rates improved since origination',
    savingsRate: 0.08,
    savingsMin: 50,
    savingsMax: 200,
    difficulty: 'Medium',
    impactOnLifestyle: 'None',
    timeline: '30 days',
    pros: ['No daily lifestyle change', 'Savings persist monthly'],
    cons: ['Closing costs and paperwork', 'Approval not guaranteed'],
    actionSteps: ['Compare 3 lender quotes', 'Calculate break-even on closing costs', 'Lock rate if savings exceed fees'],
    warningFlags: [],
    healthSafetyRisk: false,
  },
  {
    categoryId: 'housing',
    category: 'housing',
    suggestionId: 'housing_cheaper_area',
    suggestion: 'Move to a lower-cost neighborhood when lease renews',
    savingsRate: 0.25,
    savingsMin: 200,
    savingsMax: 500,
    difficulty: 'Hard',
    impactOnLifestyle: 'Moderate',
    timeline: 'Gradual',
    pros: ['Structural cost reduction', 'Frees budget for goals'],
    cons: ['Moving costs', 'Possible longer commute'],
    actionSteps: ['Research rent benchmarks by ZIP', 'Tour 3 cheaper areas', 'Plan move around lease end date'],
    warningFlags: ['Factor commute time and transit costs into savings math'],
    healthSafetyRisk: false,
  },
  {
    categoryId: 'dining',
    category: 'dining',
    suggestionId: 'dining_reduce_eating_out',
    suggestion: 'Reduce eating out from twice per week to once per week',
    savingsRate: 0.25,
    savingsMin: 100,
    savingsMax: 150,
    difficulty: 'Easy',
    impactOnLifestyle: 'Minor',
    timeline: 'Immediate',
    pros: ['Easy to start this week', 'Still allows social meals'],
    cons: ['Requires meal planning habit'],
    actionSteps: ['Pick one restaurant night per week', 'Plan home meals for other nights', 'Track dining spend weekly'],
    warningFlags: ["Don't cut too much food spending — maintain balanced nutrition"],
    healthSafetyRisk: false,
  },
  {
    categoryId: 'dining',
    category: 'dining',
    suggestionId: 'dining_skip_daily_coffee',
    suggestion: 'Replace daily coffee shop purchases with home brew',
    savingsRate: 0.15,
    savingsMin: 80,
    savingsMax: 100,
    difficulty: 'Easy',
    impactOnLifestyle: 'Minor',
    timeline: 'Immediate',
    pros: ['Immediate savings', 'Minimal behavior change'],
    cons: ['Less convenience'],
    actionSteps: ['Buy beans and a travel mug', 'Prep coffee the night before', 'Limit café visits to weekends'],
    warningFlags: [],
    healthSafetyRisk: false,
  },
  {
    categoryId: 'dining',
    category: 'dining',
    suggestionId: 'dining_bulk_meals',
    suggestion: 'Cook bulk meals and pack lunches',
    savingsRate: 0.3,
    savingsMin: 150,
    savingsMax: 200,
    difficulty: 'Medium',
    impactOnLifestyle: 'Minor',
    timeline: 'Gradual',
    pros: ['Pairs well with grocery optimization', 'Healthier options'],
    cons: ['Sunday prep time required'],
    actionSteps: ['Plan 4 dinners and 4 lunches', 'Batch cook proteins and grains', 'Store portions for the week'],
    warningFlags: ["Don't cut too much food spending — maintain balanced nutrition"],
    healthSafetyRisk: false,
  },
  {
    categoryId: 'groceries',
    category: 'groceries',
    suggestionId: 'groceries_meal_prep_combo',
    suggestion: 'Combine meal prep with a focused grocery list to reduce waste',
    savingsRate: 0.15,
    savingsMin: 80,
    savingsMax: 120,
    difficulty: 'Medium',
    impactOnLifestyle: 'Minor',
    timeline: 'Gradual',
    pros: ['Stacks with dining cuts', 'Reduces impulse purchases'],
    cons: ['Requires weekly planning'],
    actionSteps: ['Shop from a list only', 'Use store brands for staples', 'Freeze leftovers within 24 hours'],
    warningFlags: ["Don't cut too much food spending — maintain balanced nutrition"],
    healthSafetyRisk: false,
  },
  {
    categoryId: 'subscriptions',
    category: 'subscriptions',
    suggestionId: 'subscriptions_streaming_audit',
    suggestion: 'Reduce streaming services to one or two essentials',
    savingsRate: 0.35,
    savingsMin: 40,
    savingsMax: 50,
    difficulty: 'Easy',
    impactOnLifestyle: 'None',
    timeline: 'Immediate',
    pros: ['Very easy win', 'No lifestyle disruption'],
    cons: ['Less content variety'],
    actionSteps: ['List all recurring subscriptions', 'Cancel duplicates for 30 days', 'Keep one streaming + one music service max'],
    warningFlags: [],
    healthSafetyRisk: false,
  },
  {
    categoryId: 'subscriptions',
    category: 'subscriptions',
    suggestionId: 'subscriptions_gym_alternative',
    suggestion: 'Replace paid gym with home or outdoor workouts',
    savingsRate: 0.35,
    savingsMin: 40,
    savingsMax: 50,
    difficulty: 'Easy',
    impactOnLifestyle: 'Minor',
    timeline: 'Immediate',
    pros: ['Saves monthly fee quickly', 'Flexible schedule'],
    cons: ['Less equipment access'],
    actionSteps: ['Cancel gym after backup plan', 'Use free YouTube or park workouts', 'Set 3 weekly exercise blocks'],
    warningFlags: ['Maintain regular exercise for health — do not eliminate fitness entirely'],
    healthSafetyRisk: false,
  },
  {
    categoryId: 'subscriptions',
    category: 'subscriptions',
    suggestionId: 'subscriptions_app_audit',
    suggestion: 'Audit apps and cancel unused software subscriptions',
    savingsRate: 0.2,
    savingsMin: 20,
    savingsMax: 30,
    difficulty: 'Easy',
    impactOnLifestyle: 'None',
    timeline: 'Immediate',
    pros: ['Fast audit', 'Often overlooked savings'],
    cons: ['May need to re-subscribe later'],
    actionSteps: ['Review bank and App Store subscriptions', 'Cancel anything unused 30+ days', 'Set calendar reminder quarterly'],
    warningFlags: [],
    healthSafetyRisk: false,
  },
  {
    categoryId: 'transport',
    category: 'transport',
    suggestionId: 'transport_carpool',
    suggestion: 'Carpool or rideshare commute costs with coworkers',
    savingsRate: 0.33,
    savingsMin: 80,
    savingsMax: 100,
    difficulty: 'Easy',
    impactOnLifestyle: 'Minor',
    timeline: '30 days',
    pros: ['Moderate savings with low effort', 'Social benefit'],
    cons: ['Schedule coordination'],
    actionSteps: ['Find coworkers on similar schedule', 'Split fuel and parking', 'Set backup plan for late days'],
    warningFlags: [],
    healthSafetyRisk: false,
  },
  {
    categoryId: 'transport',
    category: 'transport',
    suggestionId: 'transport_public_transit',
    suggestion: 'Use public transit instead of driving for commute days',
    savingsRate: 0.5,
    savingsMin: 120,
    savingsMax: 150,
    difficulty: 'Medium',
    impactOnLifestyle: 'Moderate',
    timeline: '30 days',
    pros: ['Strong fuel and parking savings', 'Predictable monthly pass cost'],
    cons: ['Longer commute time possible'],
    actionSteps: ['Compare monthly transit pass vs fuel', 'Trial 2 weeks before committing', 'Keep one backup ride option'],
    warningFlags: ['Choose safe, well-lit routes for night travel'],
    healthSafetyRisk: false,
  },
  {
    categoryId: 'transport',
    category: 'transport',
    suggestionId: 'transport_bike_commute',
    suggestion: 'Bike commute for short trips when weather allows',
    savingsRate: 0.45,
    savingsMin: 120,
    savingsMax: 200,
    difficulty: 'Medium',
    impactOnLifestyle: 'Moderate',
    timeline: 'Gradual',
    pros: ['Saves fuel and maintenance', 'Health benefits'],
    cons: ['Weather dependent', 'Safety gear needed'],
    actionSteps: ['Get lights and helmet', 'Map safe bike route', 'Start with 2 days per week'],
    warningFlags: ['Use lights and helmet — do not compromise safety gear'],
    healthSafetyRisk: false,
  },
  {
    categoryId: 'entertainment',
    category: 'entertainment',
    suggestionId: 'entertainment_reduce_events',
    suggestion: 'Reduce paid concerts and ticketed events by half',
    savingsRate: 0.4,
    savingsMin: 50,
    savingsMax: 100,
    difficulty: 'Easy',
    impactOnLifestyle: 'Minor',
    timeline: 'Immediate',
    pros: ['Flexible cut', 'Easy to adjust month to month'],
    cons: ['Fewer big nights out'],
    actionSteps: ['Pick one paid event per month', 'Rotate free community events', 'Set entertainment cap in budget app'],
    warningFlags: [],
    healthSafetyRisk: false,
  },
  {
    categoryId: 'entertainment',
    category: 'entertainment',
    suggestionId: 'entertainment_free_activities',
    suggestion: 'Shift to free activities like parks, hiking, and home gatherings',
    savingsRate: 0.5,
    savingsMin: 80,
    savingsMax: 100,
    difficulty: 'Easy',
    impactOnLifestyle: 'Minor',
    timeline: 'Immediate',
    pros: ['Maintains social life', 'Low cost'],
    cons: ['Requires planning'],
    actionSteps: ['List free local events', 'Host potluck instead of restaurants', 'Use library passes for museums'],
    warningFlags: [],
    healthSafetyRisk: false,
  },
  {
    categoryId: 'insurance',
    category: 'insurance',
    suggestionId: 'insurance_higher_deductible',
    suggestion: 'Raise auto insurance deductibles if emergency fund can cover them',
    savingsRate: 0.15,
    savingsMin: 30,
    savingsMax: 50,
    difficulty: 'Easy',
    impactOnLifestyle: 'None',
    timeline: '30 days',
    pros: ['Lower premium immediately', 'No daily behavior change'],
    cons: ['Higher out-of-pocket if claim occurs'],
    actionSteps: ['Confirm emergency fund size', 'Get quotes at higher deductible', 'Only raise if fund covers gap'],
    warningFlags: ['Do not drop required coverage — maintain legal minimums'],
    healthSafetyRisk: false,
  },
  {
    categoryId: 'insurance',
    category: 'insurance',
    suggestionId: 'insurance_shop_around',
    suggestion: 'Shop auto and renters insurance with 3 providers',
    savingsRate: 0.3,
    savingsMin: 50,
    savingsMax: 100,
    difficulty: 'Easy',
    impactOnLifestyle: 'None',
    timeline: '30 days',
    pros: ['Often overlooked savings', 'No lifestyle trade-off'],
    cons: ['Paperwork and comparison time'],
    actionSteps: ['Gather current declarations page', 'Request quotes from 3 insurers', 'Match coverage apples-to-apples before switching'],
    warningFlags: ['Do not drop required coverage — maintain legal minimums'],
    healthSafetyRisk: false,
  },
  {
    categoryId: 'utilities',
    category: 'utilities',
    suggestionId: 'utilities_negotiate_bills',
    suggestion: 'Negotiate phone, internet, and utility plans',
    savingsRate: 0.12,
    savingsMin: 40,
    savingsMax: 60,
    difficulty: 'Easy',
    impactOnLifestyle: 'None',
    timeline: '30 days',
    pros: ['Keeps same service level', 'One-time call effort'],
    cons: ['Promotional rates may expire'],
    actionSteps: ['Call provider retention line', 'Ask for loyalty or competitor match rate', 'Set renewal reminder before promo ends'],
    warningFlags: [],
    healthSafetyRisk: false,
  },
];

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
 * Estimates implementation difficulty label.
 * @param {Record<string, unknown>} cut
 * @returns {'Easy' | 'Medium' | 'Hard'}
 */
export function estimateDifficulty(cut) {
  if (DIFFICULTY_SCORE[cut.difficulty]) {
    return cut.difficulty;
  }
  return 'Medium';
}

/**
 * Estimates lifestyle impact label.
 * @param {Record<string, unknown>} cut
 * @returns {'None' | 'Minor' | 'Moderate' | 'Significant'}
 */
export function calculateLifestyleImpact(cut) {
  if (LIFESTYLE_SCORE[cut.impactOnLifestyle] !== undefined) {
    return cut.impactOnLifestyle;
  }
  return 'Minor';
}

/**
 * Groups user spending into categories.
 * @param {Record<string, unknown>} userProfile
 * @returns {ExpenseCategory[]}
 */
export function analyzeExpenseCategories(userProfile) {
  const breakdown = userProfile?.expenseBreakdown
    ?? userProfile?.monthlyExpenses
    ?? userProfile?.monthly_expenses;

  const totalExpenses = toNumber(userProfile?.expenses, 0);

  if (breakdown && typeof breakdown === 'object' && !Array.isArray(breakdown)) {
    return Object.entries(breakdown)
      .map(([key, value]) => ({
        categoryId: key.toLowerCase(),
        category: key.toLowerCase(),
        currentMonthly: roundCurrency(toNumber(value, 0)),
      }))
      .filter((item) => item.currentMonthly > 0);
  }

  if (totalExpenses <= 0) {
    return Object.entries(DEFAULT_ALLOCATION).map(([categoryId, rate]) => ({
      categoryId,
      category: categoryId,
      currentMonthly: 0,
    }));
  }

  return Object.entries(DEFAULT_ALLOCATION).map(([categoryId, rate]) => ({
    categoryId,
    category: categoryId,
    currentMonthly: roundCurrency(totalExpenses * rate),
  }));
}

/**
 * Computes realistic savings for a cut given category spend.
 * @param {Record<string, unknown>} cut
 * @param {number} categoryMonthly
 * @returns {number}
 */
function computePotentialSavings(cut, categoryMonthly) {
  if (categoryMonthly <= 0) {
    return 0;
  }

  const byRate = roundCurrency(categoryMonthly * toNumber(cut.savingsRate, 0));
  const min = toNumber(cut.savingsMin, 0);
  const max = toNumber(cut.savingsMax, byRate);
  const capped = Math.min(byRate, categoryMonthly * 0.5);
  const bounded = Math.max(min, Math.min(max, capped));

  return roundCurrency(Math.min(bounded, categoryMonthly));
}

/**
 * Materializes KB cuts for a user profile.
 * @param {Record<string, unknown>} userProfile
 * @returns {ExpenseCutSuggestion[]}
 */
function materializeCuts(userProfile) {
  const categories = analyzeExpenseCategories(userProfile);
  const categoryMap = Object.fromEntries(
    categories.map((item) => [item.categoryId, item.currentMonthly]),
  );

  return CUT_KB
    .filter((cut) => !cut.healthSafetyRisk)
    .map((cut) => {
      const currentMonthly = toNumber(categoryMap[cut.categoryId], 0);
      const potentialSavings = computePotentialSavings(cut, currentMonthly);

      return {
        categoryId: cut.categoryId,
        category: cut.category,
        currentMonthly,
        suggestionId: cut.suggestionId,
        suggestion: cut.suggestion,
        potentialSavings,
        difficulty: estimateDifficulty(cut),
        impactOnLifestyle: calculateLifestyleImpact(cut),
        timeline: cut.timeline,
        pros: cut.pros,
        cons: cut.cons,
        actionSteps: cut.actionSteps,
        warningFlags: cut.warningFlags,
        source: 'knowledge_base',
      };
    })
    .filter((cut) => cut.potentialSavings > 0);
}

/**
 * Ranks cuts by savings, ease, and lifestyle impact.
 * @param {ExpenseCutSuggestion[]} cuts
 * @returns {ExpenseCutSuggestion[]}
 */
export function rankByImpact(cuts) {
  return [...cuts].sort((a, b) => {
    const scoreA = a.potentialSavings * 2
      - DIFFICULTY_SCORE[a.difficulty] * 15
      - LIFESTYLE_SCORE[a.impactOnLifestyle] * 10;
    const scoreB = b.potentialSavings * 2
      - DIFFICULTY_SCORE[b.difficulty] * 15
      - LIFESTYLE_SCORE[b.impactOnLifestyle] * 10;
    return scoreB - scoreA;
  });
}

/**
 * Minimum number of suggestions to return for a target amount.
 * @param {number} target
 * @returns {number}
 */
function getMinSuggestionCount(target) {
  if (target >= 800) return 4;
  if (target >= 300) return 3;
  return 1;
}

/**
 * Orders cuts for greedy selection based on target size.
 * @param {ExpenseCutSuggestion[]} rankedCuts
 * @param {number} targetMonthlyReduction
 * @returns {ExpenseCutSuggestion[]}
 */
function getSelectionOrder(rankedCuts, targetMonthlyReduction) {
  const target = Math.max(0, toNumber(targetMonthlyReduction, 0));

  if (target <= 250) {
    return [...rankedCuts].sort((a, b) => {
      const difficultyDelta = DIFFICULTY_SCORE[a.difficulty] - DIFFICULTY_SCORE[b.difficulty];
      if (difficultyDelta !== 0) {
        return difficultyDelta;
      }
      const lifestyleDelta = LIFESTYLE_SCORE[a.impactOnLifestyle] - LIFESTYLE_SCORE[b.impactOnLifestyle];
      if (lifestyleDelta !== 0) {
        return lifestyleDelta;
      }
      return b.potentialSavings - a.potentialSavings;
    });
  }

  return rankedCuts;
}

/**
 * Builds a combination of cuts to reach a monthly target.
 * @param {ExpenseCutSuggestion[]} rankedCuts
 * @param {number} targetMonthlyReduction
 * @returns {{ suggestions: ExpenseCutSuggestion[], cumulativeSavings: number, gapRemaining: number }}
 */
export function buildCombinations(rankedCuts, targetMonthlyReduction) {
  const target = Math.max(0, toNumber(targetMonthlyReduction, 0));
  const minSuggestions = getMinSuggestionCount(target);
  const orderedCuts = getSelectionOrder(rankedCuts, target);
  const categoryEasyCount = new Map();
  const usedCategories = new Set();
  const suggestions = [];
  let cumulativeSavings = 0;

  const tryAddCut = (cut) => {
    if (suggestions.some((item) => item.suggestionId === cut.suggestionId)) {
      return false;
    }
    if (cut.potentialSavings <= 0) {
      return false;
    }

    const easyUsedInCategory = categoryEasyCount.get(cut.categoryId) ?? 0;
    if (cut.difficulty !== 'Easy' && easyUsedInCategory > 0) {
      return false;
    }
    if (cut.difficulty === 'Easy' && easyUsedInCategory >= 2) {
      return false;
    }
    if (
      cut.difficulty === 'Hard'
      && target <= 300
      && cumulativeSavings >= target * 0.6
    ) {
      return false;
    }

    const remaining = Math.max(0, target - cumulativeSavings);
    if (
      cumulativeSavings >= target
      && suggestions.length >= minSuggestions
      && usedCategories.has(cut.categoryId)
    ) {
      return false;
    }
    if (
      cumulativeSavings < target
      && remaining > 0
      && cut.potentialSavings > remaining * 2.5
      && orderedCuts.some((other) =>
        other.suggestionId !== cut.suggestionId
        && !suggestions.some((item) => item.suggestionId === other.suggestionId)
        && other.potentialSavings <= remaining * 1.5
        && other.potentialSavings > 0,
      )
    ) {
      return false;
    }

    suggestions.push(cut);
    cumulativeSavings = roundCurrency(cumulativeSavings + cut.potentialSavings);
    categoryEasyCount.set(cut.categoryId, easyUsedInCategory + 1);
    usedCategories.add(cut.categoryId);
    return true;
  };

  orderedCuts.forEach((cut) => {
    if (cumulativeSavings >= target && suggestions.length >= minSuggestions) {
      return;
    }
    tryAddCut(cut);
  });

  if (cumulativeSavings < target || suggestions.length < minSuggestions) {
    rankedCuts.forEach((cut) => {
      if (cumulativeSavings >= target && suggestions.length >= minSuggestions) {
        return;
      }
      tryAddCut(cut);
    });
  }

  return {
    suggestions,
    cumulativeSavings,
    gapRemaining: roundCurrency(Math.max(0, target - cumulativeSavings)),
  };
}

/**
 * Builds LLM prompt for personalized expense cuts.
 * @param {Record<string, unknown>} userProfile
 * @param {number} targetMonthlyReduction
 * @param {ExpenseCategory[]} categories
 * @returns {string}
 */
export function buildExpenseCutPrompt(userProfile, targetMonthlyReduction, categories) {
  const categoryLines = categories
    .map((item) => `- ${item.category}: $${item.currentMonthly}/month`)
    .join('\n');

  return `Analyze this user's monthly spending and suggest realistic expense reductions.

Monthly spending categories:
${categoryLines}
Total monthly expenses: $${toNumber(userProfile?.expenses, 0)}
Target monthly reduction: $${targetMonthlyReduction}

Rules:
- Never suggest cuts that hurt health or safety
- Prefer easy wins first
- Be realistic, not optimistic
- Explain trade-offs honestly

Return only JSON array:
[
  {
    "categoryId": "string",
    "category": "string",
    "suggestionId": "string",
    "suggestion": "string",
    "potentialSavings": number,
    "difficulty": "Easy|Medium|Hard",
    "impactOnLifestyle": "None|Minor|Moderate|Significant",
    "timeline": "Immediate|30 days|Gradual",
    "pros": ["string"],
    "cons": ["string"],
    "actionSteps": ["string"],
    "warningFlags": ["string"]
  }
]`;
}

/**
 * Parses LLM expense cut JSON.
 * @param {string} rawResponse
 * @returns {Array<Record<string, unknown>> | null}
 */
export function parseExpenseCutSuggestions(rawResponse) {
  if (!rawResponse || typeof rawResponse !== 'string') {
    return null;
  }

  let text = rawResponse.trim();
  const fenceMatch = text.match(/```(?:json)?\s*([\s\S]*?)```/i);
  if (fenceMatch) {
    text = fenceMatch[1].trim();
  }

  const arrayStart = text.indexOf('[');
  const arrayEnd = text.lastIndexOf(']');
  if (arrayStart === -1 || arrayEnd === -1) {
    return null;
  }

  try {
    const parsed = JSON.parse(text.slice(arrayStart, arrayEnd + 1));
    return Array.isArray(parsed) ? parsed : null;
  } catch {
    return null;
  }
}

/**
 * Normalizes LLM cut records and filters unsafe suggestions.
 * @param {Array<Record<string, unknown>>} cuts
 * @param {ExpenseCategory[]} categories
 * @returns {ExpenseCutSuggestion[]}
 */
function normalizeLlmCuts(cuts, categories) {
  const categoryMap = Object.fromEntries(
    categories.map((item) => [item.categoryId, item.currentMonthly]),
  );

  const unsafePatterns = [/skip meals/i, /no food/i, /drop insurance entirely/i, /no health/i];

  return cuts
    .filter((cut) => {
      const text = `${cut.suggestion ?? ''} ${(cut.warningFlags ?? []).join(' ')}`;
      return !unsafePatterns.some((pattern) => pattern.test(text));
    })
    .map((cut, index) => ({
      categoryId: String(cut.categoryId ?? cut.category ?? 'other').toLowerCase(),
      category: String(cut.category ?? 'other').toLowerCase(),
      currentMonthly: roundCurrency(toNumber(categoryMap[cut.categoryId ?? cut.category], 0)),
      suggestionId: String(cut.suggestionId ?? `llm_cut_${index + 1}`),
      suggestion: String(cut.suggestion ?? 'Reduce discretionary spending'),
      potentialSavings: roundCurrency(toNumber(cut.potentialSavings, 0)),
      difficulty: DIFFICULTY_SCORE[cut.difficulty] ? cut.difficulty : 'Medium',
      impactOnLifestyle: LIFESTYLE_SCORE[cut.impactOnLifestyle] !== undefined
        ? cut.impactOnLifestyle
        : 'Minor',
      timeline: ['Immediate', '30 days', 'Gradual'].includes(cut.timeline)
        ? cut.timeline
        : 'Gradual',
      pros: Array.isArray(cut.pros) ? cut.pros.map(String) : [],
      cons: Array.isArray(cut.cons) ? cut.cons.map(String) : [],
      actionSteps: Array.isArray(cut.actionSteps) ? cut.actionSteps.map(String) : [],
      warningFlags: Array.isArray(cut.warningFlags) ? cut.warningFlags.map(String) : [],
      source: 'llm',
    }))
    .filter((cut) => cut.potentialSavings > 0);
}

/**
 * Returns all ranked expense cut options before target filtering.
 * @param {Record<string, unknown>} userProfile
 * @returns {ExpenseCutSuggestion[]}
 */
export function getAllExpenseCutOptions(userProfile) {
  return rankByImpact(materializeCuts(userProfile ?? {}));
}

/**
 * Knowledge-base expense cuts (sync).
 * @param {Record<string, unknown>} userProfile
 * @param {number} targetMonthlyReduction
 * @returns {ExpenseCutSuggestion[]}
 */
export function getKnowledgeBaseExpenseCuts(userProfile, targetMonthlyReduction) {
  const ranked = rankByImpact(materializeCuts(userProfile ?? {}));
  const { suggestions } = buildCombinations(ranked, targetMonthlyReduction);
  return suggestions;
}

/**
 * Suggests expense reductions to reach a monthly savings target.
 * @param {Record<string, unknown>} userProfile
 * @param {number} targetMonthlyReduction
 * @param {Object} [options]
 * @param {(prompt: string, opts?: object) => Promise<string | null>} [options.llmClient]
 * @returns {Promise<{ suggestions: ExpenseCutSuggestion[], cumulativeSavings: number, gapRemaining: number, source: 'llm' | 'knowledge_base' }>}
 */
export async function suggestExpenseCuts(userProfile, targetMonthlyReduction, options = {}) {
  const profile = userProfile ?? {};
  const target = Math.max(0, toNumber(targetMonthlyReduction, 0));
  const categories = analyzeExpenseCategories(profile);

  const llmClient = options.llmClient
    ?? ((text) => callClaudeApi(text, { apiKey: options.apiKey, fetchFn: options.fetchFn }));

  const prompt = buildExpenseCutPrompt(profile, target, categories);
  const rawResponse = await llmClient(prompt, options);
  const parsed = rawResponse ? parseExpenseCutSuggestions(rawResponse) : null;

  if (parsed && parsed.length > 0) {
    const llmCuts = rankByImpact(normalizeLlmCuts(parsed, categories));
    const combo = buildCombinations(llmCuts, target);
    if (combo.suggestions.length > 0) {
      return { ...combo, source: 'llm' };
    }
  }

  const ranked = rankByImpact(materializeCuts(profile));
  const combo = buildCombinations(ranked, target);
  return { ...combo, suggestions: combo.suggestions, source: 'knowledge_base' };
}

export { CLAUDE_MODEL };
export default suggestExpenseCuts;
