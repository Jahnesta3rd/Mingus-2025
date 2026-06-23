import { useCallback, useEffect, useState } from 'react';
import { useAuth } from './useAuth';
import { csrfHeaders } from '../utils/csrfHeaders';
import type { CareerRiskData } from '../types/snapshot';
import {
  computeSeparationProbability,
  marketMultiplier,
  msaSlugFromZip,
  occupationMultiplier,
  selfReportEmployerMultiplier,
  type CareerProfileForRisk,
  type EmployerHealthApiResponse,
} from '../utils/careerRiskCompute';

type ProfileResponse = {
  profile?: CareerProfileForRisk & {
    zip_code?: string | null;
    employer_name?: string | null;
  };
};

async function fetchEmployerHealth(
  cik: string,
  token: string | null,
): Promise<EmployerHealthApiResponse | null> {
  try {
    const res = await fetch(`/api/career-risk/employer/${encodeURIComponent(cik)}`, {
      credentials: 'include',
      headers: {
        ...csrfHeaders(),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    });
    if (!res.ok) return null;
    return (await res.json()) as EmployerHealthApiResponse;
  } catch {
    return null;
  }
}

export async function fetchCareerRiskData(
  getAccessToken: () => string | null,
): Promise<CareerRiskData | null> {
  const token = getAccessToken();
  const headers: Record<string, string> = {
    ...csrfHeaders(),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };

  const profileRes = await fetch('/api/user/profile', { credentials: 'include', headers });
  if (!profileRes.ok) return null;
  const profileJson = (await profileRes.json()) as ProfileResponse;
  const profile = profileJson.profile ?? {};

  const occupationMult = occupationMultiplier(profile.occupation_key);
  const msaSlug = msaSlugFromZip(profile.zip_code);
  const marketMult = marketMultiplier(msaSlug);

  let employerMult = 1.0;
  let data_source: CareerRiskData['data_source'] = 'user_reported';
  let employerHealthScore: number | undefined;
  let employerLayoffEvent: CareerRiskData['employer_layoff_event'] = null;
  let employerHealthComponents: CareerRiskData['employer_health_components'] | undefined;
  let resolvedEmployerName =
    profile.employer_name_text?.trim() ||
    profile.employer_name?.trim() ||
    '';

  if (profile.employer_cik) {
    const eh = await fetchEmployerHealth(profile.employer_cik, token);
    if (eh?.name?.trim()) resolvedEmployerName = eh.name.trim();
    if (eh) {
      if (eh.recent_layoff_event) {
        employerMult = 1.6;
        data_source = '8k_filing';
        employerLayoffEvent = eh.recent_layoff_event;
      } else if (eh.health_score !== null && !eh.is_stale) {
        employerMult = eh.multiplier;
        data_source = 'sec_edgar';
        employerHealthScore = eh.health_score;
        employerHealthComponents = eh.components;
      } else {
        employerMult = selfReportEmployerMultiplier(profile.satisfaction);
        data_source = 'user_reported';
      }
    } else {
      employerMult = selfReportEmployerMultiplier(profile.satisfaction);
      data_source = 'user_reported';
    }
  } else if (profile.employer_type === 'public_company') {
    data_source = 'unresolved';
    employerMult = selfReportEmployerMultiplier(profile.satisfaction);
  } else if (
    profile.employer_type &&
    ['federal_government', 'state_local_nonprofit', 'self_employed'].includes(
      profile.employer_type,
    )
  ) {
    data_source = 'unsupported';
    employerMult = selfReportEmployerMultiplier(profile.satisfaction);
  } else {
    employerMult = selfReportEmployerMultiplier(profile.satisfaction);
    data_source = 'user_reported';
  }

  const probability = computeSeparationProbability(
    marketMult,
    occupationMult,
    employerMult,
  );

  let pipeline_credit = 0;
  let commitment_type: CareerRiskData['commitment_type'] = null;
  let classification_rationale: string | null = null;
  let career_risk_band: CareerRiskData['career_risk_band'] = null;
  try {
    const commitmentRes = await fetch('/api/career-risk/commitment-context', {
      credentials: 'include',
      headers,
    });
    if (commitmentRes.ok) {
      const commitmentJson = (await commitmentRes.json()) as {
        pipeline_credit?: number;
        commitment_type?: CareerRiskData['commitment_type'];
        classification_rationale?: string | null;
        career_risk_band?: CareerRiskData['career_risk_band'];
      };
      pipeline_credit = Number(commitmentJson.pipeline_credit ?? 0);
      commitment_type = commitmentJson.commitment_type ?? null;
      classification_rationale = commitmentJson.classification_rationale ?? null;
      career_risk_band = commitmentJson.career_risk_band ?? null;
    }
  } catch {
    // Optional attribution fields — omit on failure.
  }

  return {
    probability_12mo: probability,
    market_multiplier: marketMult,
    occupation_multiplier: occupationMult,
    employer_multiplier: employerMult,
    data_source,
    employer_health_score: employerHealthScore,
    employer_layoff_event: employerLayoffEvent,
    employer_health_components: employerHealthComponents,
    employer_name: resolvedEmployerName || undefined,
    pipeline_credit,
    commitment_type,
    classification_rationale,
    career_risk_band,
  };
}

export function useCareerRiskData() {
  const { user, getAccessToken } = useAuth();
  const [data, setData] = useState<CareerRiskData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const load = useCallback(async () => {
    if (!user?.id) {
      setData(null);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(false);
    try {
      const result = await fetchCareerRiskData(getAccessToken);
      setData(result);
    } catch {
      setError(true);
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [user?.id, getAccessToken]);

  useEffect(() => {
    void load();
  }, [load]);

  return { data, loading, error, reload: load };
}
