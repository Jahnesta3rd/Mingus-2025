import React from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

export type ComparisonStatus = 'below' | 'average' | 'above' | 'much_above';

export interface SpendingComparisonBadgeProps {
  /** Percent change vs average (e.g. 15 for 15% above, -8 for 8% below) */
  percentChange: number | null;
  /** Whether we have enough baseline data to show comparison */
  hasBaseline: boolean;
  className?: string;
  /** Accessible label */
  ariaLabel?: string;
}

function getStatus(percent: number): ComparisonStatus {
  if (percent < -10) return 'below';
  if (percent <= 20) return 'average';
  if (percent <= 50) return 'above';
  return 'much_above';
}

const STATUS_CONFIG: Record<
  ComparisonStatus,
  { label: string; icon: React.ElementType; colorClass: string }
> = {
  below: {
    label: 'vs your average',
    icon: TrendingDown,
    colorClass: 'text-emerald-500 bg-emerald-500/10',
  },
  average: {
    label: 'About average',
    icon: Minus,
    colorClass: 'text-slate-400 bg-slate-500/10',
  },
  above: {
    label: 'vs your average',
    icon: TrendingUp,
    colorClass: 'text-amber-500 bg-amber-500/10',
  },
  much_above: {
    label: 'vs your average',
    icon: TrendingUp,
    colorClass: 'text-red-500 bg-red-500/10',
  },
};

/**
 * Badge showing total spending vs average: ↑ 15%, ↓ 8%, or "About average".
 * Green (below), gray (about), yellow (above), red (much above).
 */
export const SpendingComparisonBadge: React.FC<SpendingComparisonBadgeProps> = ({
  percentChange,
  hasBaseline,
  className = '',
  ariaLabel,
}) => {
  if (!hasBaseline) {
    return (
      <span
        className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm text-slate-400 bg-slate-500/10 ${className}`}
        role="status"
        aria-label="Not enough data yet to compare to your average"
      >
        <Minus className="w-4 h-4" aria-hidden />
        After 3 weeks, we&apos;ll show how this compares
      </span>
    );
  }

  if (percentChange === null) {
    return (
      <span
        className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm text-slate-400 bg-slate-500/10 ${className}`}
        role="status"
        aria-label="About average"
      >
        <Minus className="w-4 h-4" aria-hidden />
        About average
      </span>
    );
  }

  const status = getStatus(percentChange);
  const config = STATUS_CONFIG[status];
  const Icon = config.icon;
  const displayText =
    status === 'average'
      ? 'About average'
      : `${percentChange > 0 ? '↑' : '↓'} ${Math.abs(Math.round(percentChange))}% ${config.label}`;

  const label =
    ariaLabel ??
    (status === 'average'
      ? 'Spending is about average'
      : `${percentChange > 0 ? 'Up' : 'Down'} ${Math.abs(percentChange)}% vs your average`);

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium ${config.colorClass} ${className}`}
      role="status"
      aria-label={label}
    >
      <Icon className="w-4 h-4 shrink-0" aria-hidden />
      <span>{displayText}</span>
    </span>
  );
};

export default SpendingComparisonBadge;
