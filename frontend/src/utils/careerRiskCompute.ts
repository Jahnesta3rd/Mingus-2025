import {
  MSA_DATA,
  NATIONAL_AVERAGES,
  OCCUPATION_REPLACEABILITY,
  EMPLOYER_SIGNAL_MULTIPLIERS,
  RISK_MODEL,
} from '../constants/careerRisk';
import type { CareerRiskData } from '../types/snapshot';

/** ZIP prefix → MSA_DATA slug (seed metros). */
const ZIP_PREFIX_TO_MSA_SLUG: Record<string, string> = {
  '303': 'atlanta',
  '200': 'dc_metro',
  '222': 'dc_metro',
  '223': 'dc_metro',
  '208': 'dc_metro',
  '770': 'houston',
  '752': 'dfw',
  '760': 'dfw',
  '100': 'new_york',
  '101': 'new_york',
  '102': 'new_york',
  '103': 'new_york',
  '104': 'new_york',
  '112': 'new_york',
  '606': 'chicago',
  '607': 'chicago',
  '282': 'charlotte',
  '331': 'miami',
  '330': 'miami',
  '212': 'baltimore',
  '191': 'philadelphia',
};

export type CareerProfileForRisk = {
  occupation_key?: string | null;
  employer_cik?: string | null;
  employer_name_text?: string | null;
  employer_type?: string | null;
  satisfaction?: number | null;
  zip_code?: string | null;
};

export type EmployerHealthApiResponse = {
  health_score: number | null;
  multiplier: number;
  is_stale: boolean;
  name?: string | null;
  components?: CareerRiskData['employer_health_components'];
  recent_layoff_event?: CareerRiskData['employer_layoff_event'];
};

export function msaSlugFromZip(zip: string | null | undefined): string | null {
  if (!zip) return null;
  const digits = zip.replace(/\D/g, '').slice(0, 3);
  return ZIP_PREFIX_TO_MSA_SLUG[digits] ?? null;
}

export function marketMultiplier(msaSlug: string | null): number {
  const data = msaSlug ? MSA_DATA[msaSlug] : undefined;
  const unemployment =
    data?.unemployment_rate ?? NATIONAL_AVERAGES.unemployment_rate;
  let mult = unemployment / RISK_MODEL.msa_normalization;
  if (data?.trend === 'rising') mult *= 1.05;
  else if (data?.trend === 'falling') mult *= 0.95;
  return mult;
}

export function occupationMultiplier(occupationKey: string | null | undefined): number {
  if (!occupationKey) return OCCUPATION_REPLACEABILITY._default;
  return OCCUPATION_REPLACEABILITY[occupationKey] ?? OCCUPATION_REPLACEABILITY._default;
}

/** Self-report employer signal from career satisfaction / assessment proxy. */
export function selfReportEmployerMultiplier(satisfaction: number | null | undefined): number {
  if (satisfaction == null) return EMPLOYER_SIGNAL_MULTIPLIERS.none;
  if (satisfaction <= 2) return EMPLOYER_SIGNAL_MULTIPLIERS.missed_earnings;
  if (satisfaction === 3) return EMPLOYER_SIGNAL_MULTIPLIERS.none;
  return EMPLOYER_SIGNAL_MULTIPLIERS.growing;
}

export function computeSeparationProbability(
  marketMult: number,
  occupationMult: number,
  employerMult: number,
): number {
  const raw =
    RISK_MODEL.national_separation_rate * marketMult * occupationMult * employerMult;
  return Math.max(
    RISK_MODEL.min_probability,
    Math.min(RISK_MODEL.max_probability, raw),
  );
}
