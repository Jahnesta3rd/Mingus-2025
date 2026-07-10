import { csrfHeaders } from '../utils/csrfHeaders';

export type WisdomMilestoneStatus = 'on_track' | 'ahead' | 'behind' | 'no_data' | string;

export interface WisdomFinancialProjection {
  name: string;
  current_balance: number | null;
  target_amount: number | null;
  target_date: string | null;
  projected_date: string | null;
  status: WisdomMilestoneStatus;
  message: string;
  // UI helpers returned by the API
  current?: number | null;
  target?: number | null;
  progress_pct?: number | null;
  projected_date_label?: string | null;
  target_date_label?: string | null;
  weekly_need?: number | null;
  shortfall?: number | null;
  shortfall_message?: string | null;
  weekly_saving_rate?: number | null;
}

/** @deprecated Prefer WisdomFinancialProjection */
export type WisdomMilestone = WisdomFinancialProjection & {
  current: number | null;
  target: number | null;
  progress_pct: number | null;
  projected_date_label: string | null;
  target_date_label: string | null;
  weekly_need: number | null;
  shortfall: number | null;
  shortfall_message: string | null;
};

export interface WisdomCallPayload {
  week: number;
  week_number: number;
  script: string;
  audio_url: string | null;
  format: 'text' | 'audio' | string;
  sent_at: string | null;
  listened_at: string | null;
  financial_projections: WisdomFinancialProjection[];
  milestones: WisdomMilestone[];
  projections_summary?: string | null;
  weekly_saving_rate?: number | null;
}

export interface WisdomUserStats {
  user_id: number;
  read_rate: number;
  engagement_trend: 'improving' | 'stable' | 'declining' | 'unknown' | string;
  last_read: string | null;
  sent_count?: number;
  read_count?: number;
  weeks_sampled?: number;
}

export interface WisdomSystemStats {
  delivery_rate: number;
  email_rate: number;
  read_rate: number;
  failure_rate: number;
  counts: Record<string, number>;
  top_milestones: Array<Record<string, string | number>>;
  weekly_trends: Array<Record<string, string | number>>;
  last_task_run: Record<string, unknown>;
}

export interface WisdomStatsPayload {
  user?: WisdomUserStats;
  system?: WisdomSystemStats;
}

type FetchFn = typeof fetch;

function buildHeaders(getAccessToken?: () => string | null): HeadersInit {
  const token = getAccessToken?.() ?? null;
  return {
    'Content-Type': 'application/json',
    ...csrfHeaders(),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

function normalizeProjection(raw: WisdomFinancialProjection): WisdomMilestone {
  const current = raw.current ?? raw.current_balance ?? null;
  const target = raw.target ?? raw.target_amount ?? null;
  const progress =
    raw.progress_pct ??
    (current != null && target != null && target > 0
      ? Math.round(Math.max(0, Math.min(100, (current / target) * 100)) * 10) / 10
      : null);

  return {
    ...raw,
    current,
    target,
    progress_pct: progress,
    projected_date_label: raw.projected_date_label ?? null,
    target_date_label: raw.target_date_label ?? null,
    weekly_need: raw.weekly_need ?? null,
    shortfall: raw.shortfall ?? null,
    shortfall_message: raw.shortfall_message ?? null,
    message: raw.message || '',
  };
}

function normalizeWisdomPayload(raw: Record<string, unknown>): WisdomCallPayload {
  const week = Number(raw.week ?? raw.week_number);
  const projectionsRaw = (raw.financial_projections ?? raw.milestones ?? []) as WisdomFinancialProjection[];
  const financial_projections = projectionsRaw.map(normalizeProjection);

  return {
    week,
    week_number: week,
    script: String(raw.script ?? ''),
    audio_url: (raw.audio_url as string | null) ?? null,
    format: (raw.format as string) || (raw.audio_url ? 'audio' : 'text'),
    sent_at: (raw.sent_at as string | null) ?? null,
    listened_at: (raw.listened_at as string | null) ?? null,
    financial_projections,
    milestones: financial_projections,
    projections_summary: (raw.projections_summary as string | null) ?? null,
    weekly_saving_rate: (raw.weekly_saving_rate as number | null) ?? null,
  };
}

export async function fetchWisdomCall(
  week: number | string,
  options?: { getAccessToken?: () => string | null; fetchFn?: FetchFn },
): Promise<WisdomCallPayload> {
  const fetchFn = options?.fetchFn ?? fetch;
  const response = await fetchFn(`/api/wisdom/${encodeURIComponent(String(week))}`, {
    method: 'GET',
    credentials: 'include',
    headers: buildHeaders(options?.getAccessToken),
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const message =
      typeof body?.error === 'string' ? body.error : `Failed to load wisdom call (${response.status})`;
    throw new Error(message);
  }

  const raw = (await response.json()) as Record<string, unknown>;
  return normalizeWisdomPayload(raw);
}

export async function markWisdomCallRead(
  week: number | string,
  options?: { getAccessToken?: () => string | null; fetchFn?: FetchFn },
): Promise<{ success: boolean; listened_at?: string | null }> {
  const fetchFn = options?.fetchFn ?? fetch;
  const response = await fetchFn(`/api/wisdom/${encodeURIComponent(String(week))}/read`, {
    method: 'POST',
    credentials: 'include',
    headers: buildHeaders(options?.getAccessToken),
    body: '{}',
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const message =
      typeof body?.error === 'string' ? body.error : `Failed to record read (${response.status})`;
    throw new Error(message);
  }

  return (await response.json()) as { success: boolean; listened_at?: string | null };
}

export async function fetchWisdomStats(
  options?: {
    userId?: number;
    adminKey?: string;
    getAccessToken?: () => string | null;
    fetchFn?: FetchFn;
  },
): Promise<WisdomStatsPayload> {
  const fetchFn = options?.fetchFn ?? fetch;
  const params = new URLSearchParams();
  if (options?.userId != null) params.set('user_id', String(options.userId));
  if (options?.adminKey) params.set('admin_key', options.adminKey);
  const qs = params.toString();
  const response = await fetchFn(`/api/wisdom/stats${qs ? `?${qs}` : ''}`, {
    method: 'GET',
    credentials: 'include',
    headers: {
      ...buildHeaders(options?.getAccessToken),
      ...(options?.adminKey ? { 'X-Admin-Key': options.adminKey } : {}),
    },
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const message =
      typeof body?.error === 'string' ? body.error : `Failed to load wisdom stats (${response.status})`;
    throw new Error(message);
  }

  return (await response.json()) as WisdomStatsPayload;
}
