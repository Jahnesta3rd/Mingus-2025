/**
 * Back-to-school orchestrator API client.
 */

import { csrfHeaders } from '../utils/csrfHeaders';

/**
 * @typedef {Object} TierBalance
 * @property {string} date
 * @property {number} forecastedBalance
 * @property {'healthy'|'warning'|'danger'|string} status
 */

/**
 * @typedef {Object} SecondJobRecommendation
 * @property {string} jobId
 * @property {string} title
 * @property {number} hourlyRate
 * @property {number} hoursPerWeek
 * @property {number} weeklyIncome
 * @property {string} startupCost
 * @property {number} rampUpDays
 * @property {string} couldEarnBy
 * @property {number} potentialEarnings
 * @property {boolean} [coversShortfall]
 */

/**
 * @typedef {Object} BTSSetupResponse
 * @property {string} sessionId
 * @property {string} btsDate
 * @property {string} tier1Date
 * @property {string} tier2Date
 * @property {string} tier3Date
 * @property {{ tier1: TierBalance, tier2: TierBalance, tier3: TierBalance }} availableBalances
 * @property {number} daysUntilSchool
 * @property {number} shortfall
 * @property {number} [estimatedBudget]
 * @property {SecondJobRecommendation[]} recommendedSecondJobs
 * @property {{ name?: string|null, age?: number|null, gender?: string|null }} [child]
 */

/**
 * @typedef {Object} TimelinePoint
 * @property {string} key
 * @property {string} label
 * @property {string} date
 * @property {number} forecastedBalance
 * @property {string} status
 * @property {number} daysFromToday
 */

/**
 * @typedef {Object} ForecastTimelineResponse
 * @property {string} userId
 * @property {string} btsDate
 * @property {string} tier1Date
 * @property {string} tier2Date
 * @property {string} tier3Date
 * @property {TimelinePoint[]} timeline
 * @property {number} daysUntilSchool
 */

/**
 * @typedef {Object} BTSSetupParams
 * @property {string} userId
 * @property {string} btsDate
 * @property {string} [childName]
 * @property {number} [childAge]
 * @property {string} [childGender]
 */

/**
 * @param {(() => string|null)|undefined} getAccessToken
 * @returns {HeadersInit}
 */
function buildHeaders(getAccessToken) {
  const token = getAccessToken?.() ?? localStorage.getItem('mingus_token');
  return {
    'Content-Type': 'application/json',
    ...csrfHeaders(),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

/**
 * Create a BTS planning session and return tier balances.
 *
 * @param {BTSSetupParams} params
 * @param {{ getAccessToken?: () => string|null, fetchFn?: typeof fetch }} [options]
 * @returns {Promise<BTSSetupResponse>}
 */
export async function setupBtsDate(params, options = {}) {
  const fetchFn = options.fetchFn ?? fetch;
  const response = await fetchFn('/api/bts/setup', {
    method: 'POST',
    credentials: 'include',
    headers: buildHeaders(options.getAccessToken),
    body: JSON.stringify({
      userId: params.userId,
      btsDate: params.btsDate,
      childName: params.childName,
      childAge: params.childAge,
      childGender: params.childGender,
    }),
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.error || `BTS setup failed (${response.status})`);
  }

  return /** @type {Promise<BTSSetupResponse>} */ (response.json());
}

/**
 * Fetch the 3-week cash forecast timeline for a BTS date.
 *
 * @param {string} userId
 * @param {string} btsDate YYYY-MM-DD
 * @param {{ getAccessToken?: () => string|null, fetchFn?: typeof fetch }} [options]
 * @returns {Promise<ForecastTimelineResponse>}
 */
export async function getForecastTimeline(userId, btsDate, options = {}) {
  const fetchFn = options.fetchFn ?? fetch;
  const url = `/api/bts/forecast-timeline/${encodeURIComponent(userId)}/${encodeURIComponent(btsDate)}`;
  const response = await fetchFn(url, {
    method: 'GET',
    credentials: 'include',
    headers: buildHeaders(options.getAccessToken),
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.error || `Forecast timeline failed (${response.status})`);
  }

  return /** @type {Promise<ForecastTimelineResponse>} */ (response.json());
}
