import React from 'react';

export interface DollarHighlightProps {
  /** Amount to display (e.g. 85 for "$85 more") */
  amount: number;
  /** Optional suffix (e.g. " more", " saved") */
  suffix?: string;
  /** Optional prefix (e.g. "~") */
  prefix?: string;
  className?: string;
  /** Accessible label */
  ariaLabel?: string;
}

/**
 * Styled dollar amount: larger font, bold. Used in insight cards.
 */
export const DollarHighlight: React.FC<DollarHighlightProps> = ({
  amount,
  suffix = '',
  prefix = '',
  className = '',
  ariaLabel,
}) => {
  const display = `${prefix}$${Math.round(amount)}${suffix}`;
  const label = ariaLabel ?? `$${Math.round(amount)}${suffix}`;

  return (
    <span
      className={`text-xl font-bold tabular-nums text-slate-100 ${className}`}
      role="text"
      aria-label={label}
    >
      {display}
    </span>
  );
};

export default DollarHighlight;
