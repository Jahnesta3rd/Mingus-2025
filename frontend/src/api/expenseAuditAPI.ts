import { csrfHeaders } from '../utils/csrfHeaders';

export interface ExpenseAuditCut {
  label: string;
  monthly_savings: number;
  example: string;
}

export interface ExpenseAuditTier {
  monthly_savings: number;
  difficulty: string;
  sustainability: 'green' | 'yellow' | 'red' | string;
  cuts: ExpenseAuditCut[];
  summary: string;
}

export interface ExpenseAuditAnalyzeResponse {
  snapshot_id: string;
  days_lookback: number;
  spending_by_category: Record<string, number>;
  total_monthly: number;
  spending_leaks: Array<Record<string, unknown>>;
  tier_recommendations: Record<'A' | 'B' | 'C', ExpenseAuditTier>;
  combined_savings: Record<string, number>;
  replacement_activities: Array<{ category: string; ideas: string[] }>;
}

export interface ExpenseAuditIccApplyResponse {
  success: boolean;
  snapshot_id: string;
  selected_tiers: string;
  total_monthly_savings: number;
  original_monthly_gap: number;
  new_gap_after_cuts: number;
  original_timeline_months: number | null;
  new_timeline_months: number | null;
  waterfall_link: string;
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

export async function analyzeExpenses(
  daysLookback = 90,
  options?: { getAccessToken?: () => string | null; fetchFn?: FetchFn },
): Promise<ExpenseAuditAnalyzeResponse> {
  const fetchFn = options?.fetchFn ?? fetch;
  const response = await fetchFn('/api/expense-audit/analyze', {
    method: 'POST',
    credentials: 'include',
    headers: buildHeaders(options?.getAccessToken),
    body: JSON.stringify({ days_lookback: daysLookback }),
  });
  if (!response.ok) {
    const text = await response.text().catch(() => '');
    throw new Error(text || `Request failed: ${response.status}`);
  }
  return response.json() as Promise<ExpenseAuditAnalyzeResponse>;
}

export async function applyExpenseAuditToIcc(
  params: {
    iccAssessmentId: string;
    selectedTiers: string[];
    snapshotId?: string;
  },
  options?: { getAccessToken?: () => string | null; fetchFn?: FetchFn },
): Promise<ExpenseAuditIccApplyResponse> {
  const fetchFn = options?.fetchFn ?? fetch;
  const response = await fetchFn('/api/integration/expense-audit-to-icc-dashboard', {
    method: 'POST',
    credentials: 'include',
    headers: buildHeaders(options?.getAccessToken),
    body: JSON.stringify({
      icc_assessment_id: params.iccAssessmentId,
      selected_tiers: params.selectedTiers,
      snapshot_id: params.snapshotId,
    }),
  });
  if (!response.ok) {
    const text = await response.text().catch(() => '');
    throw new Error(text || `Request failed: ${response.status}`);
  }
  return response.json() as Promise<ExpenseAuditIccApplyResponse>;
}

export function resolveCombinedTierKey(selected: Set<string>): string {
  const hasA = selected.has('A');
  const hasB = selected.has('B');
  const hasC = selected.has('C');
  if (hasA && hasB && hasC) return 'A+B+C';
  if (hasA && hasB) return 'A+B';
  if (hasA) return 'A';
  if (hasB) return 'B';
  if (hasC) return 'C';
  return 'A';
}
