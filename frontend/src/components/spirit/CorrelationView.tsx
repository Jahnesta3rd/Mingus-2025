import React, { useMemo } from 'react';
import { Link } from 'react-router-dom';
import type { SpiritCorrelationData, SpiritWeeklyApiRow } from '../../hooks/useSpiritCorrelation';
import { useSpiritCorrelation } from '../../hooks/useSpiritCorrelation';
import { CorrelationBarCard, type SpiritCorrelationBarItem } from './CorrelationBarCard';
import { ImpulseSpendChart, type ImpulseSpendPoint } from './ImpulseSpendChart';
import { PracticeVsSavingsChart, type PracticeVsSavingsPoint } from './PracticeVsSavingsChart';
import { TierGateOverlay } from './TierGateOverlay';

export interface CorrelationViewProps {
  userTier?: string | null;
  isBeta?: boolean;
}

function normalizeTier(tier: string | null | undefined, isBeta?: boolean): 'budget' | 'mid_tier' | 'professional' {
  if (isBeta) return 'professional';
  const t = (tier || 'budget').trim().toLowerCase();
  if (t === 'professional') return 'professional';
  if (t === 'mid_tier') return 'mid_tier';
  return 'budget';
}

function shortWeekLabel(label: string): string {
  const m = /^(\d{4})-W(\d{2})$/.exec(label);
  return m ? `W${m[2]}` : label;
}

function mapWeeklyToCharts(rows: SpiritWeeklyApiRow[]): {
  practiceVsSavings: PracticeVsSavingsPoint[];
  impulse: ImpulseSpendPoint[];
} {
  return {
    practiceVsSavings: rows.map((r) => ({
      week: shortWeekLabel(r.week_label),
      practiceScore: r.practice_score,
      savingsRate: r.savings_rate ?? null,
    })),
    impulse: rows.map((r) => ({
      week: shortWeekLabel(r.week_label),
      practiceScore: r.practice_score,
      impulseSpend: r.impulse_spend ?? null,
    })),
  };
}

function strengthForR(r: number | null | undefined): SpiritCorrelationBarItem['strength'] {
  if (r == null || Number.isNaN(r)) return 'weak';
  const a = Math.abs(r);
  if (a >= 0.5) return 'strong';
  if (a >= 0.25) return 'moderate';
  return 'weak';
}

function barItem(label: string, r: number | null | undefined): SpiritCorrelationBarItem {
  const v = r == null || Number.isNaN(r) ? 0 : Math.max(-1, Math.min(1, r));
  return {
    label,
    value: v,
    direction: v >= 0 ? 'positive' : 'negative',
    strength: strengthForR(r),
  };
}

function buildBarItems(tier: 'budget' | 'mid_tier' | 'professional', data: SpiritCorrelationData | null): SpiritCorrelationBarItem[] {
  if (!data) return [];
  const savings = barItem('Practice → Savings Rate', data.corr_practice_savings ?? null);
  const stress = barItem('Practice → Stress Index', data.corr_practice_stress ?? null);
  if (tier === 'budget') {
    return [savings, stress];
  }
  const impulse = barItem('Practice → Impulse Spend', data.corr_practice_impulse ?? null);
  const bills = barItem('Practice → Bills On-Time', data.corr_practice_bills_ontime ?? null);
  return [savings, stress, impulse, bills];
}

function BudgetExtraCorrelationsLock() {
  return (
    <div className="relative mt-4 overflow-hidden rounded-xl border border-dashed border-slate-300 bg-white">
      <div className="pointer-events-none space-y-5 p-5 blur-sm select-none opacity-50" aria-hidden>
        <div className="h-10 rounded-lg bg-slate-200" />
        <div className="h-10 rounded-lg bg-slate-200" />
      </div>
      <div className="absolute inset-0 flex items-center justify-center bg-white/65 p-4 backdrop-blur-[2px]">
        <div className="text-center">
          <p className="text-sm font-semibold text-[#0f172a]">
            Upgrade to Mid-tier for impulse spend and bills on-time correlations
          </p>
          <Link
            to="/settings/upgrade"
            className="mt-2 inline-flex text-sm font-semibold text-[#C4A064] underline-offset-2 hover:underline"
          >
            Upgrade
          </Link>
        </div>
      </div>
    </div>
  );
}

export function CorrelationView({ userTier, isBeta }: CorrelationViewProps) {
  const tier = normalizeTier(userTier ?? null, isBeta);
  const isPro = tier === 'professional';
  const { correlationData, weeklyData, isLoading, error, refetch } = useSpiritCorrelation();

  const barItems = useMemo(() => buildBarItems(tier, correlationData), [tier, correlationData]);
  const { practiceVsSavings, impulse } = useMemo(() => mapWeeklyToCharts(weeklyData), [weeklyData]);

  return (
    <div className="space-y-8 text-left">
      <p className="text-sm leading-relaxed text-slate-600">
        Your spiritual practice score is correlated weekly against 5 financial variables using an 8-week Pearson r
        window.
      </p>

      {isLoading && (
        <div className="rounded-xl border border-slate-200 bg-white/80 p-6 text-center text-sm text-slate-500">
          Loading correlations…
        </div>
      )}

      {!isLoading && error && (
        <div className="rounded-xl border border-red-200 bg-red-50/80 p-4 text-sm text-red-800">
          <p>{error}</p>
          <button
            type="button"
            onClick={() => void refetch()}
            className="mt-2 text-sm font-semibold text-red-900 underline"
          >
            Try again
          </button>
        </div>
      )}

      {!isLoading && !error && (
        <>
          <div>
            <CorrelationBarCard correlations={barItems} />
            {tier === 'budget' ? <BudgetExtraCorrelationsLock /> : null}
          </div>

          <div className="relative min-h-[280px]">
            {practiceVsSavings.length > 0 ? (
              <div
                className={`grid grid-cols-1 gap-6 lg:grid-cols-2 lg:items-start ${
                  !isPro ? 'pointer-events-none select-none opacity-90' : ''
                }`}
              >
                <PracticeVsSavingsChart data={practiceVsSavings} />
                <ImpulseSpendChart data={impulse} />
              </div>
            ) : (
              <p className="flex min-h-[200px] items-center justify-center rounded-xl border border-slate-200 bg-white/80 p-6 text-center text-sm text-slate-500">
                Weekly chart data will appear once enough spirit and financial check-ins are available.
              </p>
            )}
            {!isPro && (
              <TierGateOverlay requiredTier="professional" feature="weekly correlation charts" />
            )}
          </div>
        </>
      )}

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <h3 className="text-sm font-semibold text-[#0f172a]">Practice score (input)</h3>
          <p className="mt-2 text-xs leading-relaxed text-slate-600">
            Each check-in score combines practice type weight, duration multiplier, and your post-practice mood
            (1–5) into a single number, so consistency and depth both count.
          </p>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <h3 className="text-sm font-semibold text-[#0f172a]">Financial variables (output)</h3>
          <ul className="mt-2 list-inside list-disc text-xs leading-relaxed text-slate-600">
            <li>Weekly savings rate vs. income</li>
            <li>Impulse / discretionary spending</li>
            <li>Financial stress index (wellness check-in)</li>
            <li>Bills &amp; spending control score</li>
            <li>Category spend mix used to derive savings rate</li>
          </ul>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <h3 className="text-sm font-semibold text-[#0f172a]">Pearson correlation (r)</h3>
          <p className="mt-2 text-xs leading-relaxed text-slate-600">
            For each metric we compute Pearson&apos;s r between weekly practice aggregates and that financial
            series over a rolling 8-week window. Values range from -1 (move opposite) to +1 (move together); values
            near 0 mean little linear relationship in that window.
          </p>
        </div>
      </div>
    </div>
  );
}
