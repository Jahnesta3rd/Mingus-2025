import React from 'react';
import { Flame } from 'lucide-react';

export interface StreakCounterProps {
  /** Current streak in weeks */
  count: number;
  /** Animate fire when streak > 2 */
  animate?: boolean;
  className?: string;
  /** Accessible label */
  ariaLabel?: string;
}

/**
 * Animated streak display with fire emoji/icon.
 * Optional bounce/pulse when streak > 2.
 */
export const StreakCounter: React.FC<StreakCounterProps> = ({
  count,
  animate = true,
  className = '',
  ariaLabel,
}) => {
  const showAnimation = animate && count > 2;
  const label = ariaLabel ?? `${count} week streak`;

  return (
    <span
      className={`
        inline-flex items-center gap-1.5 font-bold tabular-nums
        ${showAnimation ? 'animate-bounce-slow' : ''}
        ${className}
      `}
      role="status"
      aria-label={label}
    >
      <Flame
        className={`w-5 h-5 text-amber-400 shrink-0 ${showAnimation ? 'animate-pulse' : ''}`}
        aria-hidden
      />
      <span>{count}</span>
      <span className="font-normal text-sm opacity-90">
        week{count !== 1 ? 's' : ''}
      </span>
    </span>
  );
};

export default StreakCounter;
