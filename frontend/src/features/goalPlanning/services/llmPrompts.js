/**
 * LLM prompt templates and response validation for goal-planning services.
 */

const FEASIBILITY_LEVELS = new Set(['Low', 'Medium', 'High', 'Very High']);
const DIFFICULTY_LEVELS = new Set(['Easy', 'Medium', 'Hard']);
const LIFESTYLE_IMPACT_LEVELS = new Set(['None', 'Minor', 'Moderate']);
const REQUIRED_RECOMMENDATION_PATH_IDS = [
  'career_advancement',
  'side_income',
  'combined',
  'alternative',
];

/**
 * @param {unknown} value
 * @param {number} [fallback=0]
 * @returns {number}
 */
export function toNumber(value, fallback = 0) {
  if (typeof value === 'number' && Number.isFinite(value)) {
    return value;
  }
  if (typeof value === 'string' && value.trim() !== '') {
    const parsed = Number(value.replace(/,/g, ''));
    return Number.isFinite(parsed) ? parsed : fallback;
  }
  return fallback;
}

/**
 * @param {number} value
 * @returns {string}
 */
export function formatMoney(value) {
  return toNumber(value, 0).toLocaleString('en-US', { maximumFractionDigits: 0 });
}

/**
 * @param {unknown} value
 * @param {string} [fallback='Not specified']
 * @returns {string}
 */
export function safeText(value, fallback = 'Not specified') {
  if (typeof value === 'string' && value.trim()) {
    return value.trim();
  }
  return fallback;
}

/**
 * @param {unknown} value
 * @param {string} [fallback='None listed']
 * @returns {string}
 */
export function safeJoinList(value, fallback = 'None listed') {
  if (!Array.isArray(value) || value.length === 0) {
    return fallback;
  }
  return value.map((item) => safeText(item)).join(', ');
}

/**
 * @param {object | null | undefined} goal
 * @returns {number}
 */
export function getGoalTimelineYears(goal) {
  return Math.max(
    1,
    toNumber(goal?.timeline, toNumber(goal?.parameters?.timeline, 5)),
  );
}

/**
 * @param {object | null | undefined} goal
 * @param {object | null | undefined} analysis
 * @returns {string}
 */
export function getGoalDescription(goal, analysis) {
  return safeText(
    goal?.description
      ?? analysis?.goalDescription
      ?? `${safeText(goal?.type, 'financial').replace(/_/g, ' ')} goal`,
    'Financial goal',
  );
}

/**
 * @param {object | null | undefined} analysis
 * @param {Record<string, unknown>} userProfile
 * @returns {{
 *   totalNeeded: number,
 *   savingsGap: number,
 *   monthlyToSave: number,
 *   incomeGap: number,
 *   monthlyExpenseIncrease: number,
 *   incomeNeeded: number,
 * }}
 */
export function resolveGapContext(analysis, userProfile) {
  const gaps = analysis?.gaps ?? {};
  const present = analysis?.presentState ?? {};
  const future = analysis?.futureState ?? {};
  const savings = toNumber(userProfile?.savings, toNumber(present.savings, 0));
  const monthlyIncome = toNumber(userProfile?.income, toNumber(present.income, 0));
  const savingsGap = toNumber(gaps.savingsGap, 0);
  const totalNeeded = toNumber(
    gaps.totalNeeded,
    toNumber(future.savingsTarget, savings + Math.max(0, savingsGap)),
  );

  return {
    totalNeeded,
    savingsGap,
    monthlyToSave: toNumber(gaps.monthlyToSave, 0),
    incomeGap: toNumber(gaps.incomeGap, 0),
    monthlyExpenseIncrease: toNumber(
      gaps.monthlyExpenseIncrease,
      toNumber(gaps.expenseIncrease, 0),
    ),
    incomeNeeded: toNumber(
      gaps.incomeNeeded,
      toNumber(future.income, monthlyIncome * 12),
    ),
  };
}

/**
 * @param {object | null | undefined} analysis
 * @param {Record<string, unknown>} userProfile
 * @param {object | null | undefined} goal
 * @returns {string}
 */
export function recommendationPrompt(analysis, userProfile, goal) {
  const gap = resolveGapContext(analysis, userProfile);
  const timelineYears = getGoalTimelineYears(goal);
  const description = getGoalDescription(goal, analysis);
  const monthlyIncome = toNumber(userProfile?.income, toNumber(analysis?.presentState?.income, 0));
  const annualIncome = monthlyIncome * 12;
  const monthlyExpenses = toNumber(
    userProfile?.expenses,
    toNumber(analysis?.presentState?.monthlyExpenses, 0),
  );
  const savings = toNumber(userProfile?.savings, toNumber(analysis?.presentState?.savings, 0));
  const goalType = safeText(goal?.type, 'general');

  return `You are an expert financial advisor. Analyze this financial goal and provide strategic recommendations.

GOAL: ${description}
Goal type: ${goalType}
Timeline: ${timelineYears} years

USER'S CURRENT STATE:
- Income: $${formatMoney(annualIncome)}/year ($${formatMoney(monthlyIncome)}/month)
- Monthly expenses: $${formatMoney(monthlyExpenses)}
- Current savings: $${formatMoney(savings)}
- Job: ${safeText(userProfile?.jobTitle)} in ${safeText(userProfile?.industry)}
- Available hours for side work: ${toNumber(userProfile?.availableHours, 0)}/week
- Skills: ${safeJoinList(userProfile?.skills)}

GAP ANALYSIS:
- Total cost of goal: $${formatMoney(gap.totalNeeded)}
- Already saved: $${formatMoney(savings)}
- Gap to close: $${formatMoney(gap.savingsGap)}
- Timeline: ${timelineYears} years (${timelineYears * 12} months)
- Monthly savings needed: $${formatMoney(gap.monthlyToSave)}
- Income gap: $${formatMoney(gap.incomeGap)}/year

GOAL TYPE CONTEXT:
This is a ${goalType.replace(/_/g, ' ')} goal. For this type of goal:
- Monthly expense increase after achieving goal: $${formatMoney(gap.monthlyExpenseIncrease)}
- Income needed to support: $${formatMoney(gap.incomeNeeded)}/year

YOUR TASK:
Generate 4 distinct recommendation paths. Each path must:
1. Address the specific gap (income, savings, or both)
2. Be realistic for someone in their situation
3. Include timeline estimates
4. Show feasibility clearly
5. Be specific (not generic advice)

Paths to generate:
1. Career advancement path (role change in their industry)
2. Side income path (freelance/gig opportunities)
3. Combined path (both career + side income) — mark as RECOMMENDED
4. Alternative path (timeline extension, goal reduction, or financing)

For each path, provide:
- pathId, title, description (2 sentences max)
- monthlyBoost and annualBoost
- timeline to achieve (months/years)
- feasibility score (Low|Medium|High|Very High)
- 2-3 specific pros and cons
- year-by-year savings projection for ${Math.min(timelineYears, 5)} years

Return ONLY valid JSON with this shape (no markdown, no explanation):
{
  "paths": [
    {
      "pathId": "career_advancement",
      "title": "Career Advancement",
      "description": "Progression from current role to next role",
      "monthlyBoost": 2500,
      "annualBoost": 30000,
      "timeline": "3-6 months",
      "feasibility": "Medium",
      "pros": ["Higher income", "Career growth"],
      "cons": ["Job search takes time", "May need skill development"],
      "projections": [
        {"year": 1, "cumulativeSavings": 50000, "goalReached": false}
      ]
    }
  ]
}`;
}

/**
 * Simpler fallback when the main recommendation prompt fails.
 * @param {object | null | undefined} analysis
 * @param {Record<string, unknown>} userProfile
 * @param {object | null | undefined} goal
 * @returns {string}
 */
export function fallbackRecommendationPrompt(analysis, userProfile, goal) {
  const gap = resolveGapContext(analysis, userProfile);
  const timelineYears = getGoalTimelineYears(goal);

  return `Return ONLY JSON for 4 financial goal paths (career_advancement, side_income, combined, alternative).
User saves $${formatMoney(gap.monthlyToSave)}/month toward a $${formatMoney(gap.totalNeeded)} goal over ${timelineYears} years.
Income gap: $${formatMoney(gap.incomeGap)}/year. Job: ${safeText(userProfile?.jobTitle)}.
Each path needs: pathId, title, description, monthlyBoost (number), timeline (string), feasibility (Low|Medium|High|Very High), pros (array), cons (array).
Mark combined as mostRealistic: true.
{
  "paths": [...]
}`;
}

/**
 * @param {Record<string, unknown>} userProfile
 * @param {number} incomeGap
 * @param {number} timelineYears
 * @returns {string}
 */
export function jobSuggestionPrompt(userProfile, incomeGap, timelineYears) {
  const monthlyIncome = toNumber(userProfile?.income, 0);
  const annualIncome = monthlyIncome * 12;

  return `User is a ${safeText(userProfile?.jobTitle)} in ${safeText(userProfile?.industry)} making $${formatMoney(annualIncome)}/year.
They need to increase income by $${formatMoney(incomeGap)}/year within ${toNumber(timelineYears, 5)} years.
Skills: ${safeJoinList(userProfile?.skills)}

Suggest 5 next-step job roles and specific companies.

Return JSON array only (no markdown):
[
  {
    "title": "Specific Job Title",
    "companies": ["Company A", "Company B", "Company C"],
    "expectedSalary": 105000,
    "incomeIncrease": 30000,
    "requiredSkills": ["Skill 1", "Skill 2"],
    "interviewFocus": ["Topic 1", "Topic 2"],
    "timeline": "3-6 months"
  }
]`;
}

/**
 * @param {Record<string, unknown>} userProfile
 * @param {number} incomeGap
 * @returns {string}
 */
export function fallbackJobSuggestionPrompt(userProfile, incomeGap) {
  return `Return JSON array of 3 higher-paying job titles for a ${safeText(userProfile?.jobTitle)}.
Target income increase: $${formatMoney(incomeGap)}/year.
Each item: title, expectedSalary (number), incomeIncrease (number), timeline (string).`;
}

/**
 * @param {Record<string, unknown>} userProfile
 * @param {number} targetMonthly
 * @param {number} hoursPerWeek
 * @returns {string}
 */
export function sideGigPrompt(userProfile, targetMonthly, hoursPerWeek) {
  return `Suggest side gigs for ${safeText(userProfile?.jobTitle)} with skills in: ${safeJoinList(userProfile?.skills)}
Target: $${formatMoney(targetMonthly)}/month
Available: ${toNumber(hoursPerWeek, toNumber(userProfile?.availableHours, 10))} hours/week

Return JSON array only (no markdown):
[
  {
    "type": "Type of gig",
    "platform": "Platform name",
    "estimatedMonthly": 1000,
    "hoursPerWeek": 10,
    "startup": "How to get started",
    "difficulty": "Easy|Medium|Hard"
  }
]`;
}

/**
 * @param {number} targetMonthly
 * @returns {string}
 */
export function fallbackSideGigPrompt(targetMonthly) {
  return `Return JSON array of 3 side income ideas targeting $${formatMoney(targetMonthly)}/month.
Each item: type, platform, estimatedMonthly (number), hoursPerWeek (number), difficulty (Easy|Medium|Hard).`;
}

/**
 * @param {Record<string, unknown>} userProfile
 * @param {number} targetReduction
 * @returns {string}
 */
export function expenseCutPrompt(userProfile, targetReduction) {
  const monthlyExpenses = toNumber(userProfile?.expenses, 0);

  return `Suggest spending cuts for someone with $${formatMoney(monthlyExpenses)}/month expenses.
Target reduction: $${formatMoney(targetReduction)}/month.

Return JSON array only (no markdown):
[
  {
    "category": "Category name",
    "currentSpending": 200,
    "suggestion": "Specific action",
    "potentialSavings": 100,
    "difficulty": "Easy|Medium|Hard",
    "lifestyle_impact": "None|Minor|Moderate"
  }
]`;
}

/**
 * @param {number} targetReduction
 * @returns {string}
 */
export function fallbackExpenseCutPrompt(targetReduction) {
  return `Return JSON array of 4 expense cuts totaling about $${formatMoney(targetReduction)}/month savings.
Each item: category, suggestion, potentialSavings (number), difficulty (Easy|Medium|Hard).`;
}

/**
 * @param {Record<string, unknown>} userProfile
 * @param {Array<{ id?: string, description?: string, parameters?: { timeline?: number }, timeline?: number }>} goals
 * @returns {string}
 */
export function multiGoalPrompt(userProfile, goals) {
  const goalLines = (goals ?? []).map((goalItem, index) => {
    const timeline = getGoalTimelineYears(goalItem);
    const label = getGoalDescription(goalItem, null);
    const id = safeText(goalItem?.id ?? goalItem?.type, `goal_${index + 1}`);
    return `${index + 1}. ${label} (${timeline} years) [id: ${id}]`;
  }).join('\n');

  return `User profile: ${safeText(userProfile?.jobTitle)}, $${formatMoney(toNumber(userProfile?.income, 0) * 12)}/year income, $${formatMoney(userProfile?.savings)} saved.

User has ${(goals ?? []).length} financial goals:
${goalLines || '1. Unspecified goal (5 years)'}

Which should they prioritize? How should they sequence them?

Return JSON only (no markdown):
{
  "priority": ["goal_id1", "goal_id2"],
  "rationale": "Explanation",
  "conflicts": ["Any conflicts between goals"],
  "strategy": "Overall strategy"
}`;
}

/**
 * @param {string} rawResponse
 * @returns {unknown | null}
 */
export function parseLlmJsonResponse(rawResponse) {
  if (!rawResponse || typeof rawResponse !== 'string') {
    return null;
  }

  let text = rawResponse.trim();
  const fenceMatch = text.match(/```(?:json)?\s*([\s\S]*?)```/i);
  if (fenceMatch) {
    text = fenceMatch[1].trim();
  }

  const objectStart = text.indexOf('{');
  const arrayStart = text.indexOf('[');
  let start = -1;
  if (objectStart === -1) {
    start = arrayStart;
  } else if (arrayStart === -1) {
    start = objectStart;
  } else {
    start = Math.min(objectStart, arrayStart);
  }

  if (start === -1) {
    return null;
  }

  const isArray = text[start] === '[';
  const end = isArray ? text.lastIndexOf(']') : text.lastIndexOf('}');
  if (end === -1 || end < start) {
    return null;
  }

  try {
    return JSON.parse(text.slice(start, end + 1));
  } catch {
    return null;
  }
}

/**
 * @param {unknown} salary
 * @param {number} [min=20000]
 * @param {number} [max=1000000]
 * @returns {boolean}
 */
export function isValidSalaryRange(salary, min = 20000, max = 1000000) {
  const value = toNumber(salary, NaN);
  return Number.isFinite(value) && value >= min && value <= max;
}

/**
 * @param {unknown} timeline
 * @returns {boolean}
 */
export function isValidTimelineEstimate(timeline) {
  if (typeof timeline !== 'string' || !timeline.trim()) {
    return false;
  }
  return /(\d+\s*-\s*\d+|\d+|immediate|month|year)/i.test(timeline);
}

/**
 * @param {unknown} feasibility
 * @returns {boolean}
 */
export function isValidFeasibility(feasibility) {
  return typeof feasibility === 'string' && FEASIBILITY_LEVELS.has(feasibility);
}

/**
 * @param {unknown} path
 * @returns {boolean}
 */
export function validateRecommendationPath(path) {
  if (!path || typeof path !== 'object') {
    return false;
  }

  const record = /** @type {Record<string, unknown>} */ (path);
  const timeline = record.timeline ?? record.totalTimeline;

  if (!isValidTimelineEstimate(timeline)) {
    return false;
  }

  if (!isValidFeasibility(record.feasibility)) {
    return false;
  }

  const monthlyBoost = toNumber(record.monthlyBoost, NaN);
  if (!Number.isFinite(monthlyBoost) || monthlyBoost < 0 || monthlyBoost > 50000) {
    return false;
  }

  return Boolean(
    typeof record.pathId === 'string'
    && typeof record.title === 'string'
    && typeof record.description === 'string'
    && Array.isArray(record.pros)
    && Array.isArray(record.cons),
  );
}

/**
 * Accepts either { paths: [] } or a raw paths array.
 * @param {unknown} parsed
 * @returns {boolean}
 */
export function validateRecommendationPaths(parsed) {
  const paths = Array.isArray(parsed)
    ? parsed
    : (parsed && typeof parsed === 'object' ? /** @type {{ paths?: unknown[] }} */ (parsed).paths : null);

  if (!Array.isArray(paths) || paths.length === 0) {
    return false;
  }

  const validPathIds = paths
    .filter(validateRecommendationPath)
    .map((path) => path.pathId);

  return REQUIRED_RECOMMENDATION_PATH_IDS.every((id) => validPathIds.includes(id));
}

/**
 * @param {unknown} parsed
 * @returns {boolean}
 */
export function validateJobSuggestions(parsed) {
  if (!Array.isArray(parsed) || parsed.length === 0) {
    return false;
  }

  return parsed.every((job) => {
    if (!job || typeof job !== 'object') {
      return false;
    }
    const record = /** @type {Record<string, unknown>} */ (job);
    return Boolean(
      typeof record.title === 'string'
      && isValidSalaryRange(record.expectedSalary)
      && isValidTimelineEstimate(record.timeline ?? '3-6 months')
      && toNumber(record.incomeIncrease, 0) >= 0,
    );
  });
}

/**
 * @param {unknown} parsed
 * @returns {boolean}
 */
export function validateSideGigSuggestions(parsed) {
  if (!Array.isArray(parsed) || parsed.length === 0) {
    return false;
  }

  return parsed.every((gig) => {
    if (!gig || typeof gig !== 'object') {
      return false;
    }
    const record = /** @type {Record<string, unknown>} */ (gig);
    const estimated = toNumber(record.estimatedMonthly, NaN);
    const difficulty = record.difficulty;
    return Boolean(
      typeof record.type === 'string'
      && Number.isFinite(estimated)
      && estimated >= 0
      && estimated <= 50000
      && (typeof difficulty !== 'string' || DIFFICULTY_LEVELS.has(difficulty)),
    );
  });
}

/**
 * @param {unknown} parsed
 * @returns {boolean}
 */
export function validateExpenseCutSuggestions(parsed) {
  if (!Array.isArray(parsed) || parsed.length === 0) {
    return false;
  }

  return parsed.every((cut) => {
    if (!cut || typeof cut !== 'object') {
      return false;
    }
    const record = /** @type {Record<string, unknown>} */ (cut);
    const savings = toNumber(record.potentialSavings, NaN);
    const impact = record.lifestyle_impact;
    return Boolean(
      typeof record.category === 'string'
      && typeof record.suggestion === 'string'
      && Number.isFinite(savings)
      && savings >= 0
      && (typeof impact !== 'string' || LIFESTYLE_IMPACT_LEVELS.has(impact)),
    );
  });
}

/**
 * @param {unknown} parsed
 * @returns {boolean}
 */
export function validateMultiGoalResponse(parsed) {
  if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
    return false;
  }

  const record = /** @type {Record<string, unknown>} */ (parsed);
  return Boolean(
    Array.isArray(record.priority)
    && record.priority.length > 0
    && typeof record.rationale === 'string'
    && typeof record.strategy === 'string'
    && Array.isArray(record.conflicts),
  );
}

export default {
  recommendationPrompt,
  fallbackRecommendationPrompt,
  jobSuggestionPrompt,
  fallbackJobSuggestionPrompt,
  sideGigPrompt,
  fallbackSideGigPrompt,
  expenseCutPrompt,
  fallbackExpenseCutPrompt,
  multiGoalPrompt,
  parseLlmJsonResponse,
  validateRecommendationPaths,
  validateJobSuggestions,
  validateSideGigSuggestions,
  validateExpenseCutSuggestions,
  validateMultiGoalResponse,
};
