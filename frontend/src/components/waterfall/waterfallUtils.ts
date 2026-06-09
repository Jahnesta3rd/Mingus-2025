import type { WaterfallContext } from '../fluency/types';

export type AllocationPercents = {
  fixed: number;
  discretionary: number;
  debt: number;
  savings: number;
};

export const DEFAULT_ALLOCATIONS: AllocationPercents = {
  fixed: 40,
  discretionary: 25,
  debt: 15,
  savings: 10,
};

export function totalAllocated(p: AllocationPercents): number {
  return p.fixed + p.discretionary + p.debt + p.savings;
}

export function surplusPercent(p: AllocationPercents): number {
  return Math.max(0, 100 - totalAllocated(p));
}

export function bucketAmount(monthlyIncome: number, pct: number): number {
  return Math.round((monthlyIncome * pct) / 100);
}

/** Future value of monthly surplus invested for 60 months at annual rate. */
export function fiveYearCompoundedSurplus(
  monthlySurplus: number,
  annualRate = 0.07
): number {
  if (monthlySurplus <= 0) return 0;
  const r = annualRate / 12;
  const n = 60;
  return Math.round(monthlySurplus * ((Math.pow(1 + r, n) - 1) / r));
}

export function formatUsd(amount: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  }).format(amount);
}

/**
 * Personalized optimized split from check-in signals.
 * Does not mutate the user's actual slider state.
 */
export function computeOptimizedAllocations(
  current: AllocationPercents,
  ctx: WaterfallContext | null
): AllocationPercents {
  if (!ctx) return { ...current };

  let discretionary = current.discretionary;
  let savings = current.savings;

  if (ctx.discretionary_risk === 'high' || ctx.discretionary_risk === 'watch') {
    discretionary = Math.max(0, discretionary - 5);
    savings += 5;
  }
  if (ctx.surplus_trajectory === 'at_risk') {
    savings += 3;
    discretionary = Math.max(0, discretionary - 3);
  }
  const dp = ctx.down_payment_status;
  if (dp === 'not_started' || dp === 'not_saving') {
    savings += 5;
    discretionary = Math.max(0, discretionary - 5);
  }

  let total = current.fixed + discretionary + current.debt + savings;
  if (total > 100) {
    const overflow = total - 100;
    discretionary = Math.max(0, discretionary - overflow);
    total = current.fixed + discretionary + current.debt + savings;
  }

  return {
    fixed: current.fixed,
    discretionary,
    debt: current.debt,
    savings,
  };
}

export function isVehicleSellTimeline(decision: WaterfallContext['vehicle_decision']): boolean {
  return (
    decision === 'selling' ||
    decision === 'considering_replace' ||
    decision === 'actively_shopping'
  );
}

export function isDownPaymentNotStarted(
  status: WaterfallContext['down_payment_status']
): boolean {
  return status === 'not_started' || status === 'not_saving';
}
