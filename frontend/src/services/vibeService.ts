export interface VibeData {
  vibe_id: string;
  title: string;
  image_url: string;
  alt_text: string;
  category: string;
  category_display: string;
  sentiment: string;
  day_of_week: string;
  date: string;
  tags: string[];
}

export interface VibeResponse {
  has_vibe: boolean;
  vibe?: VibeData;
  message?: string;
}

export interface ReactionResponse {
  success: boolean;
  reaction: string;
  date: string;
  streak: number;
}

export interface VibeSummary {
  streak: number;
  has_today_vibe: boolean;
  total_reactions?: number;
  recent_sentiment?: string;
  [key: string]: unknown;
}

export const getAuthHeaders = (): HeadersInit => ({
  'Content-Type': 'application/json',
  Authorization: `Bearer ${localStorage.getItem('auth_token')}`,
});

const API_BASE = '/api/vibe';

/**
 * GET /api/vibe/daily — fetch the daily vibe for the current user.
 */
export async function getDailyVibe(): Promise<VibeResponse> {
  const response = await fetch(`${API_BASE}/daily`, {
    method: 'GET',
    headers: getAuthHeaders(),
  });
  if (!response.ok) {
    throw new Error(`getDailyVibe failed: ${response.status}`);
  }
  return response.json();
}

/**
 * POST /api/vibe/react — record a reaction (like/dislike/skip) for a vibe.
 */
export async function recordReaction(
  vibeId: string,
  reaction: 'like' | 'dislike' | 'skip',
  responseTimeMs?: number
): Promise<ReactionResponse> {
  const body: { vibe_id: string; reaction: string; response_time_ms?: number } = {
    vibe_id: vibeId,
    reaction,
  };
  if (responseTimeMs !== undefined) {
    body.response_time_ms = responseTimeMs;
  }
  const response = await fetch(`${API_BASE}/react`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error(`recordReaction failed: ${response.status}`);
  }
  return response.json();
}

/**
 * GET /api/vibe/vibe-summary — mood data for dashboard widget.
 */
export async function getVibeSummary(): Promise<VibeSummary> {
  const response = await fetch(`${API_BASE}/vibe-summary`, {
    method: 'GET',
    headers: getAuthHeaders(),
  });
  if (!response.ok) {
    throw new Error(`getVibeSummary failed: ${response.status}`);
  }
  return response.json();
}
