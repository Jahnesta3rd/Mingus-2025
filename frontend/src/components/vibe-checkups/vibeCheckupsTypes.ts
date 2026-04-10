export type Verdict = {
  emotional_score: number;
  financial_score: number;
  verdict_label: string;
  verdict_emoji: string;
  verdict_description: string;
};

export type ProjectionRow = {
  month: number;
  event: string;
  monthly_cost: number;
  cumulative_cost: number;
};

export type CaptureEmailResponse = Verdict & { lead_id: string };
