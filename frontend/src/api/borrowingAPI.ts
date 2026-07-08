import { csrfHeaders } from '../utils/csrfHeaders';

export interface BorrowingSustainability {
  sustainable: boolean;
  reasoning: string;
  max_affordable_payment: number;
  debt_service_ratio: number | null;
}

export interface BorrowingOption {
  key: string;
  name: string;
  safety_rank: number;
  safety_level: string;
  recommended: boolean;
  blocked: boolean;
  allowed: boolean;
  terms: Record<string, unknown>;
  monthly_payment: number;
  term_months: number;
  apr_percent: number;
  total_repayment: number;
  pros: string[];
  cons: string[];
  sustainability: BorrowingSustainability;
  rule_messages: string[];
}

export interface BorrowingAnalyzeResponse {
  allowed: boolean;
  options: BorrowingOption[];
  warnings: string[];
  hard_rules: string[];
  forbidden_products: Array<{ key: string; label: string; blocked: boolean; reason: string }>;
  recommendation: string;
  amount_needed: number;
  monthly_income: number;
  side_income: number;
  resources: {
    family_loan_template: string;
    credit_union_locator_url: string;
    nfcc_counseling_url: string;
  };
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

export async function analyzeBorrowing(
  params: {
    amountNeeded: number;
    monthlyIncome: number;
    sideIncome?: number;
    borrowingReason?: string;
    relationshipUnsafe?: boolean;
    incomeStable?: boolean;
    accelerateTimeline?: boolean;
  },
  options?: { getAccessToken?: () => string | null; fetchFn?: FetchFn },
): Promise<BorrowingAnalyzeResponse> {
  const fetchFn = options?.fetchFn ?? fetch;
  const response = await fetchFn('/api/borrowing/analyze', {
    method: 'POST',
    credentials: 'include',
    headers: buildHeaders(options?.getAccessToken),
    body: JSON.stringify({
      amount_needed: params.amountNeeded,
      monthly_income: params.monthlyIncome,
      side_income: params.sideIncome ?? 0,
      borrowing_reason: params.borrowingReason ?? 'bridge_startup',
      relationship_unsafe: params.relationshipUnsafe ?? false,
      income_stable: params.incomeStable ?? true,
      accelerate_timeline: params.accelerateTimeline ?? false,
    }),
  });
  if (!response.ok) {
    const text = await response.text().catch(() => '');
    throw new Error(text || `Request failed: ${response.status}`);
  }
  return response.json() as Promise<BorrowingAnalyzeResponse>;
}
