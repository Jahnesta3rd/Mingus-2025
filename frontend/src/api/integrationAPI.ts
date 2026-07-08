import { csrfHeaders } from '../utils/csrfHeaders';

export interface IccToDf1HandoffRequest {
  iccAssessmentId: string;
  personId: string;
  selectedJob: string;
  df1JobType: string;
  targetMonthlyIncome: number;
  gapCoveragePct: number;
}

export interface IccToDf1HandoffResponse {
  success: boolean;
  commitment_id: string;
  handoff_url: string;
  message: string;
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

export async function createIccToDf1Handoff(
  params: IccToDf1HandoffRequest,
  options?: {
    getAccessToken?: () => string | null;
    fetchFn?: FetchFn;
  },
): Promise<IccToDf1HandoffResponse> {
  const fetchFn = options?.fetchFn ?? fetch;
  const response = await fetchFn('/api/integration/icc-to-df1-handoff', {
    method: 'POST',
    credentials: 'include',
    headers: buildHeaders(options?.getAccessToken),
    body: JSON.stringify({
      icc_assessment_id: params.iccAssessmentId,
      person_id: params.personId,
      selected_job: params.selectedJob,
      df1_job_type: params.df1JobType,
      target_monthly_income: params.targetMonthlyIncome,
      gap_coverage_pct: params.gapCoveragePct,
    }),
  });

  if (!response.ok) {
    const text = await response.text().catch(() => '');
    throw new Error(text || `Request failed: ${response.status}`);
  }

  return response.json() as Promise<IccToDf1HandoffResponse>;
}
