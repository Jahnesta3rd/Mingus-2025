import React from 'react';
import { MiniSpendingChart } from './MiniSpendingChart';

export type CategoryVsAverage = 'below' | 'average' | 'above' | 'much_above';

function getVsAverageStatus(
  current: number | null,
  average: number
): CategoryVsAverage {
  if (current === null || current === undefined) return 'average';
  if (average <= 0) return 'average';
  const ratio = (current / average) * 100;
  if (ratio < 80) return 'below';
  if (ratio <= 120) return 'average';
  if (ratio <= 150) return 'above';
  return 'much_above';
}

const STATUS_COLORS: Record<CategoryVsAverage, string> = {
  below: 'bg-emerald-500',
  average: 'bg-slate-500',
  above: 'bg-amber-500',
  much_above: 'bg-red-500',
};

const STATUS_LABELS: Record<CategoryVsAverage, string> = {
  below: 'Below average',
  average: 'About average',
  above: 'Above average',
  much_above: 'Well above average',
};

export interface SpendingCategoryBarProps {
  label: string;
  amount: number | null;
  /** Average for this category (from baselines). If null, no comparison. */
  average: number | null;
  /** Max value for bar scale (e.g. max of all categories this week) */
  maxAmount: number;
  /** Optional sparkline data (recent weeks) for mini chart */
  history?: number[];
  className?: string;
  /** Callback when category is tapped (optional) */
  onTap?: () => void;
}

/**
 * Single category row: name, amount, mini bar, vs-average indicator.
 * Highlights categories significantly above average (>150%).
 */
export const SpendingCategoryBar: React.FC<SpendingCategoryBarProps> = ({
  label,
  amount,
  average,
  maxAmount,
  history = [],
  className = '',
  onTap,
}) => {
  const hasValue = amount !== null && amount !== undefined && !Number.isNaN(amount);
  const value = hasValue ? amount! : 0;
  const avg = average ?? 0;
  const status = getVsAverageStatus(hasValue ? value : null, avg);
  const barWidthPercent = maxAmount > 0 ? Math.min(100, (value / maxAmount) * 100) : 0;

  const content = (
    <>
      <div className="flex items-center justify-between gap-2 min-w-0">
        <span className="text-slate-300 text-sm font-medium truncate">{label}</span>
        <span
          className={`text-sm font-semibold tabular-nums shrink-0 ${
            !hasValue ? 'text-slate-500' : 'text-slate-100'
          }`}
        >
          {hasValue ? `$${Math.round(value)}` : '—'}
        </span>
      </div>
      <div className="flex items-center gap-2 mt-1">
        <div className="flex-1 min-w-0 h-2 bg-slate-700 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-300 ${STATUS_COLORS[status]}`}
            style={{ width: `${barWidthPercent}%` }}
            role="presentation"
          />
        </div>
        {average !== null && average > 0 && hasValue && (
          <span
            className={`text-xs shrink-0 ${
              status === 'below'
                ? 'text-emerald-500'
                : status === 'average'
                  ? 'text-slate-400'
                  : status === 'above'
                    ? 'text-amber-500'
                    : 'text-red-500'
            }`}
            title={STATUS_LABELS[status]}
          >
            {value <= avg
              ? '↓'
              : value / avg <= 1.5
                ? '↑'
                : '↑↑'}
          </span>
        )}
      </div>
      {history.length > 0 && (
        <div className="mt-1 flex justify-end">
          <MiniSpendingChart
            data={history}
            width={56}
            height={16}
            ariaLabel={`${label} last ${history.length} weeks`}
          />
        </div>
      )}
    </>
  );

  const wrapperClass = `
    rounded-lg p-2.5 border border-slate-700/80
    ${status === 'much_above' ? 'bg-red-500/5 border-red-500/20' : 'bg-slate-800/50'}
    ${onTap ? 'cursor-pointer hover:bg-slate-700/50 focus:ring-2 focus:ring-violet-500/50 focus:ring-offset-2 focus:ring-offset-slate-900' : ''}
    ${className}
  `;

  if (onTap) {
    return (
      <button
        type="button"
        onClick={onTap}
        className={`w-full text-left ${wrapperClass}`}
        aria-label={`${label}: $${hasValue ? Math.round(value) : 'no data'}. ${STATUS_LABELS[status]}`}
      >
        {content}
      </button>
    );
  }

  return (
    <div className={wrapperClass} role="listitem" aria-label={`${label}: $${hasValue ? Math.round(value) : 'no data'}`}>
      {content}
    </div>
  );
};

export default SpendingCategoryBar;
