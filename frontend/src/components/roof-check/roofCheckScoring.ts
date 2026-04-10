export type HousingWealthGapResult = {
  annual_wealth_gap: number;
  verdict: string;
  ten_year_gap: number;
};

export function calculateRoofScore(answers: Record<string, number>): number {
  const keys = Object.keys(answers).sort((a, b) => Number(a) - Number(b));
  if (keys.length !== 12) {
    throw new Error("Roof Check requires exactly 12 answers");
  }
  const total = Object.values(answers).reduce((sum, v) => sum + v, 0);
  return Math.round((total / (12 * 3)) * 100);
}

export function calculateHousingWealthGap(score: number): HousingWealthGapResult {
  if (score >= 75) {
    return { annual_wealth_gap: 0, verdict: "Equity Builder", ten_year_gap: 0 };
  }
  if (score >= 55) {
    return { annual_wealth_gap: 4800, verdict: "Stability Zone", ten_year_gap: 72000 };
  }
  if (score >= 35) {
    return { annual_wealth_gap: 12000, verdict: "House Neutral", ten_year_gap: 180000 };
  }
  return { annual_wealth_gap: 24000, verdict: "House Poor", ten_year_gap: 360000 };
}
