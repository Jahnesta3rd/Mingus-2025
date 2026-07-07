import { csrfHeaders } from '../../../utils/csrfHeaders.ts';

/**
 * @param {object} params
 * @param {object} params.goal
 * @param {Record<string, unknown>} params.userProfile
 * @param {() => string | null} [params.getAccessToken]
 * @param {typeof fetch} [params.fetchFn]
 * @returns {Promise<object>}
 */
export async function fetchGoalPlanningAnalysis({
  goal,
  userProfile,
  getAccessToken,
  fetchFn = fetch,
}) {
  const token = getAccessToken?.() ?? null;
  const headers = {
    'Content-Type': 'application/json',
    ...csrfHeaders(),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };

  const response = await fetchFn('/api/goal-planning/analyze', {
    method: 'POST',
    credentials: 'include',
    headers,
    body: JSON.stringify({ goal, userProfile }),
  });

  if (!response.ok) {
    let message = `Goal planning request failed (${response.status})`;
    try {
      const payload = await response.json();
      if (payload?.message) {
        message = payload.message;
      } else if (payload?.error) {
        message = payload.error;
      }
    } catch {
      // ignore parse errors
    }
    throw new Error(message);
  }

  return response.json();
}

export default fetchGoalPlanningAnalysis;
