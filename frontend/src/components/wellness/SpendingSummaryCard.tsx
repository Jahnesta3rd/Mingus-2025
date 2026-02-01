import React, { useState } from 'react';
import { DollarSign, AlertTriangle, ChevronDown, ChevronUp, ExternalLink } from 'lucide-react';
import { SpendingComparisonBadge } from './SpendingComparisonBadge';
import { SpendingCategoryBar } from './SpendingCategoryBar';

export interface SpendingData {
  week_ending_date: string;
  groceries: number | null;
  dining: number | null;
  entertainment: number | null;
  shopping: number | null;
  transport: number | null;
  other: number | null;
  total: number;
  impulse_spending: number | null;
  stress_spending: number | null;
}

export interface SpendingBaselines {
  avg_groceries: number;
  avg_dining: number;
  avg_entertainment: number;
  avg_shopping: number;
  avg_transport: number;
  avg_other?: number;
  avg_total: number;
  avg_impulse: number;
  weeks_of_data: number;
}

export interface SpendingSummaryCardProps {
  current: SpendingData | null;
  baselines: SpendingBaselines | null;
  loading?: boolean;
  /** Optional: link to full spending history */
  onSeeDetails?: () => void;
  /** Optional: link to start check-in (for empty state) */
  onStartCheckin?: () => void;
  /** Optional: per-category history for sparklines (e.g. last 6 weeks) */
  categoryHistory?: Partial<Record<keyof Pick<SpendingData, 'groceries' | 'dining' | 'entertainment' | 'shopping' | 'transport' | 'other'>, number[]>>;
  className?: string;
}

const CATEGORIES: Array<{
  key: keyof Pick<SpendingData, 'groceries' | 'dining' | 'entertainment' | 'shopping' | 'transport' | 'other'>;
  label: string;
  baselineKey: keyof SpendingBaselines;
}> = [
  { key: 'groceries', label: 'Groceries', baselineKey: 'avg_groceries' },
  { key: 'dining', label: 'Dining & Takeout', baselineKey: 'avg_dining' },
  { key: 'entertainment', label: 'Entertainment', baselineKey: 'avg_entertainment' },
  { key: 'shopping', label: 'Shopping', baselineKey: 'avg_shopping' },
  { key: 'transport', label: 'Transport', baselineKey: 'avg_transport' },
  { key: 'other', label: 'Other', baselineKey: 'avg_other' },
];

/**
 * Dashboard card: this week's spending, comparison to average, category breakdown,
 * impulse/stress highlights. Empty and insufficient-baseline states.
 */
export const SpendingSummaryCard: React.FC<SpendingSummaryCardProps> = ({
  current,
  baselines,
  loading = false,
  onSeeDetails,
  onStartCheckin,
  categoryHistory = {},
  className = '',
}) => {
  const [categoriesExpanded, setCategoriesExpanded] = useState(true);

  const hasBaseline = baselines != null && baselines.weeks_of_data >= 3;
  const avgTotal = baselines?.avg_total ?? 0;
  const percentChange =
    current && avgTotal > 0
      ? ((current.total - avgTotal) / avgTotal) * 100
      : null;

  if (loading) {
    return (
      <div
        className={`rounded-2xl bg-slate-800/80 border border-slate-700 p-6 animate-pulse ${className}`}
        role="region"
        aria-label="Spending summary"
      >
        <div className="h-6 w-48 bg-slate-700 rounded mb-4" />
        <div className="h-10 w-32 bg-slate-700 rounded mb-6" />
        <div className="space-y-3">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="h-14 bg-slate-700 rounded-lg" />
          ))}
        </div>
      </div>
    );
  }

  if (!current) {
    return (
      <div
        className={`rounded-2xl bg-slate-800/80 border border-slate-700 p-6 ${className}`}
        role="region"
        aria-label="Spending summary"
      >
        <h3 className="text-lg font-semibold text-slate-200 mb-2 flex items-center gap-2">
          <DollarSign className="w-5 h-5 text-slate-400" aria-hidden />
          This Week&apos;s Spending 💸
        </h3>
        <p className="text-slate-400 text-sm mb-4">
          Complete your check-in to track spending and compare to your average.
        </p>
        {onStartCheckin && (
          <button
            type="button"
            onClick={onStartCheckin}
            className="min-h-[44px] px-4 rounded-xl font-semibold bg-violet-600 text-white hover:bg-violet-500 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:ring-offset-2 focus:ring-offset-slate-900"
            aria-label="Start check-in to track spending"
          >
            Complete check-in
          </button>
        )}
      </div>
    );
  }

  const maxCategoryAmount = Math.max(
    ...[
      current.groceries,
      current.dining,
      current.entertainment,
      current.shopping,
      current.transport,
      current.other,
    ].filter((n): n is number => n != null && !Number.isNaN(n)),
    1
  );

  const getAvg = (baselineKey: keyof SpendingBaselines): number => {
    const v = baselines?.[baselineKey];
    return typeof v === 'number' && !Number.isNaN(v) ? v : 0;
  };

  const impulseAboveAvg =
    hasBaseline &&
    current.impulse_spending != null &&
    current.impulse_spending > 0 &&
    (baselines?.avg_impulse ?? 0) > 0 &&
    current.impulse_spending > (baselines?.avg_impulse ?? 0);

  return (
    <div
      className={`rounded-2xl bg-slate-800/80 border border-slate-700 p-6 ${className}`}
      role="region"
      aria-label="Spending summary"
    >
      {/* Header + total + comparison */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-6">
        <h3 className="text-lg font-semibold text-slate-200 flex items-center gap-2">
          <DollarSign className="w-5 h-5 text-slate-400" aria-hidden />
          This Week&apos;s Spending 💸
        </h3>
        <div className="flex flex-col sm:items-end gap-2">
          <span className="text-2xl font-bold text-slate-100 tabular-nums">
            ${Math.round(current.total)}
          </span>
          <SpendingComparisonBadge
            percentChange={percentChange}
            hasBaseline={hasBaseline}
            ariaLabel={
              !hasBaseline
                ? undefined
                : percentChange === null
                  ? 'About average'
                  : `${percentChange > 0 ? 'Up' : 'Down'} ${Math.abs(Math.round(percentChange ?? 0))}% vs your average`
            }
          />
        </div>
      </div>

      {!hasBaseline && (
        <p className="text-slate-500 text-sm mb-4">
          After 3 weeks, we&apos;ll show how this compares to your average.
        </p>
      )}

      {/* Category breakdown: collapsible on mobile */}
      <div className="space-y-2">
        <button
          type="button"
          onClick={() => setCategoriesExpanded((e) => !e)}
          className="md:hidden w-full flex items-center justify-between py-2 text-slate-300 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-violet-500/50 rounded"
          aria-expanded={categoriesExpanded}
          aria-controls="spending-categories"
        >
          <span>Category breakdown</span>
          {categoriesExpanded ? (
            <ChevronUp className="w-4 h-4" aria-hidden />
          ) : (
            <ChevronDown className="w-4 h-4" aria-hidden />
          )}
        </button>
        <div
          id="spending-categories"
          className={`grid gap-2 ${!categoriesExpanded ? 'hidden md:grid' : ''}`}
          role="list"
          aria-label="Spending by category"
        >
          {CATEGORIES.map(({ key, label, baselineKey }) => (
            <SpendingCategoryBar
              key={key}
              label={label}
              amount={current[key]}
              average={baselines ? getAvg(baselineKey) : null}
              maxAmount={maxCategoryAmount}
              history={categoryHistory[key]}
            />
          ))}
        </div>
      </div>

      {/* Impulse / Stress section */}
      {(current.impulse_spending != null && current.impulse_spending > 0) ||
      (current.stress_spending != null && current.stress_spending > 0) ? (
        <div className="mt-6 pt-4 border-t border-slate-700 space-y-2">
          <p className="text-slate-400 text-sm font-medium">Watch categories</p>
          <div className="flex flex-wrap gap-3">
            {current.impulse_spending != null && current.impulse_spending > 0 && (
              <span
                className={`inline-flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium ${
                  impulseAboveAvg
                    ? 'bg-amber-500/10 text-amber-500 border border-amber-500/20'
                    : 'bg-slate-700/50 text-slate-300'
                }`}
              >
                {impulseAboveAvg && (
                  <AlertTriangle className="w-4 h-4 shrink-0" aria-hidden />
                )}
                Impulse: ${Math.round(current.impulse_spending)}
              </span>
            )}
            {current.stress_spending != null && current.stress_spending > 0 && (
              <span className="inline-flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium bg-slate-700/50 text-slate-300">
                Stress spending: ${Math.round(current.stress_spending)}
              </span>
            )}
          </div>
        </div>
      ) : null}

      {/* See details */}
      {onSeeDetails && (
        <div className="mt-6 pt-4 border-t border-slate-700">
          <button
            type="button"
            onClick={onSeeDetails}
            className="inline-flex items-center gap-2 text-sm font-medium text-violet-400 hover:text-violet-300 focus:outline-none focus:ring-2 focus:ring-violet-500/50 rounded"
            aria-label="See full spending history"
          >
            <ExternalLink className="w-4 h-4" aria-hidden />
            See details
          </button>
        </div>
      )}
    </div>
  );
};

export default SpendingSummaryCard;
