import React from 'react';

export interface InsightSkeletonProps {
  /** Number of skeleton cards to show */
  count?: number;
  className?: string;
}

/**
 * Loading placeholder for insight cards with shimmer effect.
 */
export const InsightSkeleton: React.FC<InsightSkeletonProps> = ({
  count = 3,
  className = '',
}) => {
  return (
    <div className={`space-y-4 ${className}`} role="status" aria-label="Loading insights">
      {Array.from({ length: count }, (_, i) => (
        <div
          key={i}
          className="rounded-xl border border-slate-600 bg-slate-800/80 p-4 animate-pulse overflow-hidden"
          aria-hidden
        >
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-lg bg-slate-700 shrink-0" />
            <div className="h-5 bg-slate-700 rounded w-2/3 max-w-[200px]" />
          </div>
          <div className="space-y-2 mb-3">
            <div className="h-4 bg-slate-700 rounded w-full" />
            <div className="h-4 bg-slate-700 rounded w-5/6" />
            <div className="h-4 bg-slate-700 rounded w-4/6" />
          </div>
          <div className="h-3 bg-slate-700 rounded w-1/2 mb-3" />
          <div className="h-10 bg-slate-700 rounded-lg w-full max-w-[180px]" />
        </div>
      ))}
      <span className="sr-only">Loading wellness insights…</span>
    </div>
  );
};

export default InsightSkeleton;
