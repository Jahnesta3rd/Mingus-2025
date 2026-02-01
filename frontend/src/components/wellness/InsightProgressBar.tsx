import React from 'react';

export interface InsightProgressBarProps {
  /** Weeks completed (0-4) */
  weeksCompleted: number;
  /** Weeks required to unlock (default 4) */
  weeksRequired?: number;
  className?: string;
  /** Accessible label */
  ariaLabel?: string;
}

/**
 * Progress bar showing weeks until insights unlock (e.g. "2 of 4 weeks completed").
 */
export const InsightProgressBar: React.FC<InsightProgressBarProps> = ({
  weeksCompleted,
  weeksRequired = 4,
  className = '',
  ariaLabel,
}) => {
  const clamped = Math.min(weeksRequired, Math.max(0, weeksCompleted));
  const percent = weeksRequired > 0 ? (clamped / weeksRequired) * 100 : 0;

  const label =
    ariaLabel ??
    `${clamped} of ${weeksRequired} weeks completed. ${weeksRequired - clamped} more to unlock personalized insights.`;

  return (
    <div className={`space-y-2 ${className}`} role="progressbar" aria-valuenow={clamped} aria-valuemin={0} aria-valuemax={weeksRequired} aria-label={label}>
      <div className="flex justify-between text-sm">
        <span className="text-slate-300 font-medium">
          {clamped} of {weeksRequired} weeks completed
        </span>
        <span className="text-slate-400 tabular-nums">
          {Math.round(percent)}%
        </span>
      </div>
      <div className="h-2.5 w-full bg-slate-700 rounded-full overflow-hidden">
        <div
          className="h-full bg-violet-500 rounded-full transition-all duration-500 ease-out"
          style={{ width: `${percent}%` }}
        />
      </div>
    </div>
  );
};

export default InsightProgressBar;
