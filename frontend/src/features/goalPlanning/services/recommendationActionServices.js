/**
 * Rule-based action suggestions for recommendation paths.
 * Job suggestions delegate to jobRecommendationService knowledge base (sync).
 */

import { getKnowledgeBaseSuggestions } from './jobRecommendationService.js';
import { getKnowledgeBaseSideGigs } from './sideGigService.js';
import { getKnowledgeBaseExpenseCuts } from './expenseReductionService.js';

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
 * Suggests job opportunities to close an annual income gap (sync KB wrapper).
 * @param {Record<string, unknown>} userProfile
 * @param {number} incomeGap - Annual income shortfall
 * @param {string} [goalType]
 * @returns {Array<Record<string, unknown>>}
 */
export function suggestJobsForIncomeGoal(userProfile, incomeGap, goalType = 'general') {
  return getKnowledgeBaseSuggestions(userProfile, incomeGap, goalType);
}

/**
 * Suggests side gig opportunities (sync KB wrapper).
 * Supports legacy signature: suggestSideGigs(skills[], monthlyNeeded)
 * or full profile: suggestSideGigs(userProfile, monthlyTarget, availableHours)
 * @param {Record<string, unknown> | string[]} skillsOrProfile
 * @param {number} [monthlyNeeded=0]
 * @param {number} [availableHours=10]
 * @returns {Array<Record<string, unknown>>}
 */
export function suggestSideGigs(skillsOrProfile, monthlyNeeded = 0, availableHours = 10) {
  const profile = Array.isArray(skillsOrProfile)
    ? { skills: skillsOrProfile }
    : skillsOrProfile ?? { skills: [] };

  const hours = Array.isArray(skillsOrProfile)
    ? availableHours
    : toNumber(profile.availableHours, availableHours);

  return getKnowledgeBaseSideGigs(profile, monthlyNeeded, hours);
}

/**
 * Suggests expense cuts (sync KB wrapper).
 * Supports legacy signature: suggestExpenseCuts(monthlyExpenses, target)
 * or full profile: suggestExpenseCuts(userProfile, targetMonthlyReduction)
 * @param {Record<string, unknown> | number} expensesOrProfile
 * @param {number} [targetMonthlyReduction=0]
 * @returns {Array<Record<string, unknown>>}
 */
export function suggestExpenseCuts(expensesOrProfile, targetMonthlyReduction = 0) {
  const profile = typeof expensesOrProfile === 'number'
    ? { expenses: expensesOrProfile }
    : expensesOrProfile ?? {};

  return getKnowledgeBaseExpenseCuts(profile, targetMonthlyReduction);
}
