export interface OesPercentiles {
  pct_10: number;
  pct_25: number;
  pct_50: number;
  pct_75: number;
  pct_90: number;
}

/** Interpolate an integer percentile (1–99) from OES wage bands. */
export function interpolatePercentile(salary: number, bands: OesPercentiles): number {
  const { pct_10, pct_25, pct_50, pct_75, pct_90 } = bands;
  const ordered: Array<[number, number]> = [
    [10, pct_10],
    [25, pct_25],
    [50, pct_50],
    [75, pct_75],
    [90, pct_90],
  ];

  if (salary <= pct_10) {
    if (pct_10 <= 0) return 1;
    return Math.max(1, Math.min(10, Math.round((salary / pct_10) * 10)));
  }

  if (salary >= pct_90) {
    if (pct_90 <= 0) return 99;
    const excess = salary - pct_90;
    const span = Math.max(pct_90 * 0.25, 1);
    return Math.min(99, 90 + Math.round((excess / span) * 9));
  }

  let prevPct = 10;
  let prevWage = pct_10;
  for (let i = 1; i < ordered.length; i += 1) {
    const [pct, wage] = ordered[i];
    if (salary <= wage) {
      if (wage <= prevWage) return pct;
      const frac = (salary - prevWage) / (wage - prevWage);
      return Math.max(prevPct, Math.min(pct, Math.round(prevPct + frac * (pct - prevPct))));
    }
    prevPct = pct;
    prevWage = wage;
  }

  return 90;
}

export function oesPercentilesFromPersonal(personal: {
  pct_10: number;
  pct_25: number;
  pct_50: number;
  pct_75: number;
  pct_90: number;
}): OesPercentiles {
  return {
    pct_10: personal.pct_10,
    pct_25: personal.pct_25,
    pct_50: personal.pct_50,
    pct_75: personal.pct_75,
    pct_90: personal.pct_90,
  };
}
