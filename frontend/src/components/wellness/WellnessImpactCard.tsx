import React, { useEffect, useRef } from 'react';
import { Sparkles } from 'lucide-react';
import { InsightCard } from './InsightCard';
import { InsightProgressBar } from './InsightProgressBar';
import { InsightSkeleton } from './InsightSkeleton';
import type { WellnessInsight } from './InsightCard';

const WEEKS_NEEDED = 4;

export interface WellnessImpactCardProps {
  /** List of insights (shown in priority order, max 3) */
  insights: WellnessInsight[];
  loading?: boolean;
  /** Weeks of check-in data available; if < 4, show unlock message */
  weeksOfData?: number;
  className?: string;
}

/**
 * Wellness–money connection card: header, up to 3 insight cards (priority order),
 * loading skeleton, insufficient-data state with progress bar, empty state.
 */
export const WellnessImpactCard: React.FC<WellnessImpactCardProps> = ({
  insights,
  loading = false,
  weeksOfData = 0,
  className = '',
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const hasEnoughData = weeksOfData >= WEEKS_NEEDED;
  const sortedInsights = [...insights].sort((a, b) => a.priority - b.priority).slice(0, 3);

  useEffect(() => {
    if (sortedInsights.length > 0 && containerRef.current) {
      const live = containerRef.current.querySelector('[role="status"]');
      if (live) {
        live.setAttribute('aria-live', 'polite');
      }
    }
  }, [sortedInsights.length]);

  if (loading) {
    return (
      <div
        className={`rounded-2xl bg-slate-800/80 border border-slate-700 p-6 ${className}`}
        role="region"
        aria-label="Wellness-money connection"
      >
        <h2 className="text-lg font-semibold text-slate-200 mb-4 flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-violet-400" aria-hidden />
          Your Wellness-Money Connection
        </h2>
        <InsightSkeleton count={3} />
      </div>
    );
  }

  if (!hasEnoughData) {
    return (
      <div
        className={`rounded-2xl bg-slate-800/80 border border-slate-700 p-6 ${className}`}
        role="region"
        aria-label="Wellness-money connection"
      >
        <h2 className="text-lg font-semibold text-slate-200 mb-2 flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-violet-400" aria-hidden />
          Your Wellness-Money Connection
        </h2>
        <p className="text-slate-300 text-sm mb-4">
          Complete a few more weekly check-ins to unlock personalized insights!
        </p>
        <p className="text-slate-400 text-sm mb-4">
          We need about {WEEKS_NEEDED} weeks of data to find patterns.
        </p>
        <InsightProgressBar
          weeksCompleted={Math.min(weeksOfData, WEEKS_NEEDED)}
          weeksRequired={WEEKS_NEEDED}
          ariaLabel={`${Math.min(weeksOfData, WEEKS_NEEDED)} of ${WEEKS_NEEDED} weeks completed. ${Math.max(0, WEEKS_NEEDED - weeksOfData)} more to unlock personalized insights.`}
        />
      </div>
    );
  }

  if (sortedInsights.length === 0) {
    return (
      <div
        className={`rounded-2xl bg-slate-800/80 border border-slate-700 p-6 ${className}`}
        role="region"
        aria-label="Wellness-money connection"
      >
        <h2 className="text-lg font-semibold text-slate-200 mb-2 flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-violet-400" aria-hidden />
          Your Wellness-Money Connection
        </h2>
        <p className="text-slate-300 text-sm">
          No strong patterns found yet. Keep checking in — insights often emerge after 6–8 weeks!
        </p>
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className={`rounded-2xl bg-slate-800/80 border border-slate-700 p-6 ${className}`}
      role="region"
      aria-label="Wellness-money connection"
    >
      <h2 className="text-lg font-semibold text-slate-200 mb-4 flex items-center gap-2">
        <Sparkles className="w-5 h-5 text-violet-400" aria-hidden />
        Your Wellness-Money Connection
      </h2>
      <div
        className="space-y-4"
        role="list"
        aria-label="Personalized insights"
      >
        {sortedInsights.map((insight, i) => (
          <div key={`${insight.type}-${insight.title}-${i}`} role="listitem">
            <InsightCard insight={insight} index={i} />
          </div>
        ))}
      </div>
      <p className="sr-only" role="status" aria-live="polite">
        {sortedInsights.length} new insight{sortedInsights.length !== 1 ? 's' : ''} available.
      </p>
    </div>
  );
};

export default WellnessImpactCard;
