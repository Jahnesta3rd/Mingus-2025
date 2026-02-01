import React from 'react';
import { Sparkles } from 'lucide-react';

const WEEKS_NEEDED = 4;

export interface InsightUnlockProgressProps {
  /** Weeks of check-in data (0-3 for "X more to go") */
  weeksOfData: number;
  weeksRequired?: number;
  className?: string;
  /** Compact single-line display */
  compact?: boolean;
  /** Accessible label */
  ariaLabel?: string;
}

/**
 * "X more weeks to unlock insights" indicator.
 * Only meaningful when weeksOfData < weeksRequired.
 */
export const InsightUnlockProgress: React.FC<InsightUnlockProgressProps> = ({
  weeksOfData,
  weeksRequired = WEEKS_NEEDED,
  className = '',
  compact = false,
  ariaLabel,
}) => {
  const remaining = Math.max(0, weeksRequired - Math.min(weeksOfData, weeksRequired));
  const label =
    ariaLabel ??
    `${remaining} more week${remaining !== 1 ? 's' : ''} of check-ins to unlock personalized insights.`;

  if (remaining <= 0) return null;

  if (compact) {
    return (
      <span
        className={`inline-flex items-center gap-1.5 text-sm text-white/90 ${className}`}
        role="status"
        aria-label={label}
      >
        <Sparkles className="w-4 h-4 text-amber-300 shrink-0" aria-hidden />
        <span>just {remaining} more until we can find your patterns!</span>
      </span>
    );
  }

  return (
    <div
      className={`flex items-center gap-2 ${className}`}
      role="status"
      aria-label={label}
    >
      <Sparkles className="w-4 h-4 text-amber-300 shrink-0" aria-hidden />
      <span className="text-sm text-white/90">
        Just <strong>{remaining}</strong> more week{remaining !== 1 ? 's' : ''} until we can find your patterns!
      </span>
    </div>
  );
};

export default InsightUnlockProgress;
