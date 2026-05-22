// These are seed values for beta launch.
// MSA_DATA: refresh quarterly from BLS LAUS (https://www.bls.gov/web/metro/laummtrk.htm)
// OCCUPATION_REPLACEABILITY: derived from O*NET Automation/AI Exposure scores. Expand as user research adds SOC codes.
// NATIONAL_AVERAGES: refresh annually from BLS

export type MsaData = {
  unemployment_rate: number;
  duration_weeks: number;
  trend: 'rising' | 'stable' | 'falling';
};

export const MSA_DATA: Record<string, MsaData> = {
  atlanta: { unemployment_rate: 3.6, duration_weeks: 10, trend: 'stable' },
  houston: { unemployment_rate: 4.2, duration_weeks: 11, trend: 'rising' },
  dc_metro: { unemployment_rate: 2.8, duration_weeks: 9, trend: 'stable' },
  dfw: { unemployment_rate: 3.7, duration_weeks: 10, trend: 'stable' },
  new_york: { unemployment_rate: 4.1, duration_weeks: 12, trend: 'rising' },
  philadelphia: { unemployment_rate: 4.0, duration_weeks: 11, trend: 'stable' },
  chicago: { unemployment_rate: 4.5, duration_weeks: 12, trend: 'rising' },
  charlotte: { unemployment_rate: 3.5, duration_weeks: 10, trend: 'falling' },
  miami: { unemployment_rate: 3.4, duration_weeks: 10, trend: 'stable' },
  baltimore: { unemployment_rate: 3.3, duration_weeks: 10, trend: 'stable' },
};

export const NATIONAL_AVERAGES = {
  unemployment_rate: 4.0,
  duration_weeks: 10,
  separation_rate: 0.14,
};

// Technology: software_developer 1.10, data_analyst 1.30, data_scientist 0.95, qa_tester 1.45, it_support 1.20
// Marketing & Creative: marketing_coordinator 1.20, marketing_manager 0.85, content_writer 1.40, social_media_manager 1.10, graphic_designer 1.25
// Operations & Admin: admin_assistant 1.45, data_entry 1.55, operations_coordinator 1.05
// Management: program_manager 0.85, project_manager 0.90, operations_manager 0.80, director 0.75, vp_or_above 0.70
// Government / Public Administration: public_administrator 0.75, policy_analyst 0.85, federal_program_mgr 0.70
// Finance / Consulting / Sales: financial_analyst 1.00, consultant 0.90, account_executive 0.95, sales_rep 1.05
// Fallback: _default 1.00
export const OCCUPATION_REPLACEABILITY: Record<string, number> = {
  software_developer: 1.1,
  data_analyst: 1.3,
  data_scientist: 0.95,
  qa_tester: 1.45,
  it_support: 1.2,
  marketing_coordinator: 1.2,
  marketing_manager: 0.85,
  content_writer: 1.4,
  social_media_manager: 1.1,
  graphic_designer: 1.25,
  admin_assistant: 1.45,
  data_entry: 1.55,
  operations_coordinator: 1.05,
  program_manager: 0.85,
  project_manager: 0.9,
  operations_manager: 0.8,
  director: 0.75,
  vp_or_above: 0.7,
  public_administrator: 0.75,
  policy_analyst: 0.85,
  federal_program_mgr: 0.7,
  financial_analyst: 1.0,
  consultant: 0.9,
  account_executive: 0.95,
  sales_rep: 1.05,
  _default: 1.0,
};

export const EMPLOYER_SIGNAL_MULTIPLIERS: Record<string, number> = {
  none: 1.0,
  hiring_freeze: 1.3,
  layoff_announced: 1.6,
  leadership_change: 1.15,
  missed_earnings: 1.25,
  growing: 0.75,
};

export const RISK_MODEL = Object.freeze({
  national_separation_rate: 0.14,
  msa_normalization: 4.0,
  wage_haircut_pct: 0.1,
  min_probability: 0.02,
  max_probability: 0.5,
  horizon_months: 12,
});
