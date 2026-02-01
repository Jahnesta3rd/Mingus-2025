import React from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

export interface ScoreChangeIndicatorProps {
  /** Change from previous period (e.g. +5.2, -3.1, 0) */
  change: number;
  /** Compact mode for category cards */
  compact?: boolean;
  className?: string;
  /** Accessible label */
  ariaLabel?: string;
}

/**
 * Arrow with change value: ↑ green (positive), ↓ red (negative), → gray (zero).
 */
export const ScoreChangeIndicator: React.FC<ScoreChangeIndicatorProps> = ({
  change,
  compact = false,
  className = '',
  ariaLabel,
}) => {
  const rounded = Math.round(change * 10) / 10;
  const isPositive = rounded > 0;
  const isNegative = rounded < 0;
  const isZero = rounded === 0;

  const colorClass = isPositive
    ? 'text-emerald-500'
    : isNegative
      ? 'text-red-500'
      : 'text-slate-400';

  const Icon = isPositive ? TrendingUp : isNegative ? TrendingDown : Minus;
  const text = isZero ? '0' : `${isPositive ? '+' : ''}${rounded}`;

  const label = ariaLabel ?? (isZero ? 'No change' : `${isPositive ? 'Up' : 'Down'} ${Math.abs(rounded)} from last week`);

  if (compact) {
    return (
      <span
        className={`inline-flex items-center gap-0.5 text-sm font-medium ${colorClass} ${className}`}
        role="status"
        aria-label={label}
      >
        <Icon className="w-3.5 h-3.5" aria-hidden />
        <span>{text}</span>
      </span>
    );
  }

  return (
    <span
      className={`inline-flex items-center gap-1.5 font-semibold ${colorClass} ${className}`}
      role="status"
      aria-label={label}
    >
      <Icon className="w-5 h-5" aria-hidden />
      <span>{text}</span>
      <span className="text-slate-400 font-normal text-sm">from last week</span>
    </span>
  );
};

export default ScoreChangeIndicator;
