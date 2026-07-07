import { csrfHeaders } from '../../../utils/csrfHeaders.js';

const FREQUENCY_TO_MONTHLY = {
  weekly: 52 / 12,
  biweekly: 26 / 12,
  semimonthly: 2,
  monthly: 1,
  annual: 1 / 12,
};

/**
 * @param {unknown} value
 * @param {number} [fallback=0]
 * @returns {number}
 */
function toNumber(value, fallback = 0) {
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
 * @param {Record<string, unknown>} monthlyExpenses
 * @returns {number}
 */
function sumLegacyExpenses(monthlyExpenses) {
  if (!monthlyExpenses || typeof monthlyExpenses !== 'object') {
    return 0;
  }
  return Object.values(monthlyExpenses).reduce(
    (total, value) => total + toNumber(value, 0),
    0,
  );
}

/**
 * @param {Array<{ amount?: unknown, frequency?: string }>} sources
 * @returns {number}
 */
function sumIncomeSources(sources) {
  if (!Array.isArray(sources)) {
    return 0;
  }
  return sources.reduce((total, source) => {
    const amount = toNumber(source.amount, 0);
    const multiplier = FREQUENCY_TO_MONTHLY[source.frequency ?? 'monthly'] ?? 1;
    return total + amount * multiplier;
  }, 0);
}

/**
 * Builds an analyzer-compatible profile from Mingus API responses.
 * @param {object} params
 * @param {string} params.userId
 * @param {() => string | null} params.getAccessToken
 * @returns {Promise<Record<string, unknown>>}
 */
export async function buildGoalAnalysisProfile({ userId, getAccessToken }) {
  const token = getAccessToken?.() ?? null;
  const headers = {
    ...csrfHeaders(),
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };

  let profile = {};
  let incomeSources = [];

  try {
    const profileRes = await fetch(
      `/api/user/profile?userId=${encodeURIComponent(userId)}`,
      { credentials: 'include', headers },
    );
    if (profileRes.ok) {
      const data = await profileRes.json();
      profile = data?.profile ?? data ?? {};
    }
  } catch {
    /* use defaults */
  }

  try {
    const incomeRes = await fetch('/api/financial-setup/income', {
      credentials: 'include',
      headers,
    });
    if (incomeRes.ok) {
      const incomeData = await incomeRes.json();
      incomeSources = incomeData?.sources ?? incomeData?.income_sources ?? [];
    }
  } catch {
    /* use defaults */
  }

  const financialInfo = profile.financial_info ?? {};
  const monthlyExpenses = profile.monthly_expenses ?? {};
  const careerProfile = profile.career_profile ?? profile.careerProfile ?? {};
  const personalInfo = profile.personal_info ?? profile.personalInfo ?? {};

  const incomeFromStreams = sumIncomeSources(incomeSources);
  const incomeFromProfile = toNumber(
    profile.user_income?.monthly_takehome
      ?? financialInfo.monthlyTakehome
      ?? (toNumber(financialInfo.annualIncome, 0) / 12),
    0,
  );
  const income = incomeFromStreams > 0 ? incomeFromStreams : incomeFromProfile;

  const savings = toNumber(
    profile.current_balance ?? financialInfo.currentSavings,
    0,
  );

  const expensesFromLegacy = sumLegacyExpenses(monthlyExpenses);
  const expenses = expensesFromLegacy > 0
    ? expensesFromLegacy
    : Math.max(0, income * 0.65);

  const skillsRaw = careerProfile.skills ?? profile.skills;
  const skills = Array.isArray(skillsRaw)
    ? skillsRaw.map(String)
    : typeof skillsRaw === 'string'
      ? skillsRaw.split(',').map((item) => item.trim()).filter(Boolean)
      : [];

  return {
    id: userId,
    income: Math.round(income),
    savings: Math.round(savings),
    expenses: Math.round(expenses),
    jobTitle: careerProfile.current_role
      ?? careerProfile.occupation_key
      ?? personalInfo.occupation
      ?? 'Professional',
    industry: careerProfile.industry ?? personalInfo.industry ?? 'General',
    skills: skills.length > 0 ? skills : ['Communication', 'Problem solving'],
    availableHours: toNumber(profile.available_hours ?? profile.availableHours, 10),
  };
}

export default buildGoalAnalysisProfile;
