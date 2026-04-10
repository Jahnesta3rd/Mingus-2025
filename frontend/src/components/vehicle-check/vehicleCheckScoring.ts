/** Mirrors backend/services/vehicle_check_service.py scoring helpers. */

export type VehicleCheckAnswers = Record<string, number>;

const RISK_BY_Q_VALUE: Record<string, Record<number, string>> = {
  "1": {
    0: "Older vehicle (12+ years) — higher failure and repair probability",
    1: "Mid-life vehicle (7–12 years) — watch for wear-related costs",
    2: "Vehicle is 3–7 years — stay ahead of scheduled maintenance",
  },
  "2": {
    0: "High mileage — major service due soon",
    1: "Elevated mileage — budget for upcoming major services",
    2: "Moderate mileage — keep up with interval services",
  },
  "3": {
    0: "No maintenance history — unknown failure risk",
    1: "Maintenance backlog — catch-up reduces surprise repairs",
    2: "Some maintenance gaps — document and close them",
  },
  "4": {
    0: "Multiple known issues need immediate attention",
    1: "Known issues present — address before they cascade",
    2: "Minor issue on the books — fix early to avoid compound cost",
  },
  "5": {
    0: "Frequent breakdowns — budgeting and backup transport matter",
    1: "Multiple breakdowns — reliability risk to cash flow",
    2: "Recent breakdown — investigate root cause",
  },
  "6": {
    0: "No or lapsed insurance — legal and financial exposure",
    1: "Thin coverage — a serious incident could be expensive",
    2: "Coverage gaps — review limits vs. vehicle value",
  },
  "7": {
    0: "Heavy or commercial use accelerates wear and operating cost",
    1: "High annual miles — faster wear and higher upkeep",
    2: "Regular commuting — plan for tires, brakes, and fluids",
  },
  "8": {
    0: "Poor fuel economy — fuel spend is a steady drain",
    1: "Average MPG — efficiency upgrades or driving habits can help",
    2: "Fuel costs add up — track miles and budget fuel",
  },
  "9": {
    0: "No car emergency fund — repairs may hit cash flow hard",
    1: "Thin car savings — one repair can disrupt the month",
    2: "Limited car cushion — build toward 1–2 months of ownership cost",
  },
  "10": {
    0: "No replacement plan — surprise costs or rushed buying risk",
    1: "Uncertain timeline — start a simple replace-or-repair rule",
    2: "Near-term change possible — align savings with next step",
  },
};

export function calculateVehicleScore(answers: VehicleCheckAnswers): number {
  const keys = Object.keys(answers).sort((a, b) => Number(a) - Number(b));
  if (keys.length !== 10) {
    throw new Error("answers must contain exactly 10 entries");
  }
  let total = 0;
  for (const k of keys) {
    total += answers[k];
  }
  return Math.round((total / (10 * 3)) * 100);
}

function buildTopRisks(answers: VehicleCheckAnswers): string[] {
  const ranked: { v: number; i: number; msg: string }[] = [];
  for (let i = 1; i <= 10; i += 1) {
    const k = String(i);
    const v = answers[k];
    const byV = RISK_BY_Q_VALUE[k] ?? {};
    let msg = byV[v];
    if (msg === undefined && v < 3) {
      msg = "This area scored below ideal — worth a closer look";
    }
    if (msg) {
      ranked.push({ v, i, msg });
    }
  }
  ranked.sort((a, b) => (a.v !== b.v ? a.v - b.v : a.i - b.i));
  const out: string[] = [];
  const seen = new Set<string>();
  for (const { msg } of ranked) {
    if (seen.has(msg)) continue;
    seen.add(msg);
    out.push(msg);
    if (out.length >= 3) break;
  }
  return out;
}

export type AnnualMaintenanceResult = {
  annual_cost: number;
  risk_level: "Low" | "Moderate" | "High" | "Critical";
  top_risks: string[];
};

export function calculateAnnualMaintenance(
  answers: VehicleCheckAnswers,
  score: number
): AnnualMaintenanceResult {
  let tier: { annual_cost: number; risk_level: AnnualMaintenanceResult["risk_level"] };
  if (score >= 75) {
    tier = { annual_cost: 800, risk_level: "Low" };
  } else if (score >= 55) {
    tier = { annual_cost: 1800, risk_level: "Moderate" };
  } else if (score >= 35) {
    tier = { annual_cost: 3600, risk_level: "High" };
  } else {
    tier = { annual_cost: 6000, risk_level: "Critical" };
  }
  return { ...tier, top_risks: buildTopRisks(answers) };
}
