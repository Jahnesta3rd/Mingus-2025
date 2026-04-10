/** Mirrors backend/services/body_check_service.py scoring helpers. */

export type BodyCheckAnswers = Record<string, number>;

export function calculateBodyScore(answers: BodyCheckAnswers): number {
  const keys = Object.keys(answers).sort((a, b) => Number(a) - Number(b));
  if (keys.length !== 15) {
    throw new Error("answers must contain exactly 15 entries");
  }
  let total = 0;
  for (const k of keys) {
    total += answers[k];
  }
  return Math.round((total / (15 * 3)) * 100);
}

export function calculateHealthCostProjection(score: number): number {
  if (score >= 75) return 2400;
  if (score >= 55) return 4800;
  if (score >= 35) return 8400;
  return 14400;
}

export type ProductivityImpact = {
  lost_days_per_month: number;
  annual_income_impact_pct: number;
};

export function calculateProductivityImpact(score: number): ProductivityImpact {
  if (score >= 75) return { lost_days_per_month: 0.5, annual_income_impact_pct: 0.01 };
  if (score >= 55) return { lost_days_per_month: 1.5, annual_income_impact_pct: 0.03 };
  if (score >= 35) return { lost_days_per_month: 3.0, annual_income_impact_pct: 0.06 };
  return { lost_days_per_month: 5.0, annual_income_impact_pct: 0.12 };
}
