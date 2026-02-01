import React, { useState, useEffect } from 'react';
import { ClipboardList } from 'lucide-react';
import { CircularProgressRing } from './CircularProgressRing';
import { ScoreChangeIndicator } from './ScoreChangeIndicator';
import { CategoryScoreCard, getScoreTier } from './CategoryScoreCard';

export interface WellnessScores {
  physical_score: number;
  mental_score: number;
  relational_score: number;
  financial_feeling_score: number;
  overall_wellness_score: number;
  physical_change: number;
  mental_change: number;
  relational_change: number;
  overall_change: number;
  /** Optional; if omitted, Financial Feel card shows 0 change */
  financial_feeling_change?: number;
  week_ending_date: string;
}

const TIER_COLORS: Record<string, string> = {
  thriving: '#10B981',
  growing: '#F59E0B',
  building: '#F97316',
  attention: '#EF4444',
};

const TIER_LABELS: Record<string, string> = {
  thriving: 'Thriving',
  growing: 'Growing',
  building: 'Building',
  attention: 'Needs attention',
};

function formatWeekLabel(isoDate: string): string {
  try {
    const d = new Date(isoDate);
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  } catch {
    return isoDate;
  }
}

export interface WellnessScoreCardProps {
  /** Scores for the latest week, or null for empty state */
  scores: WellnessScores | null;
  /** Called when user taps "Start check-in" in empty state */
  onStartCheckin?: () => void;
  /** Optional class for the card container */
  className?: string;
}

/**
 * Dashboard wellness score card: hero ring, overall score, change, week label,
 * and 2x2 (mobile) / 4x1 (desktop) category grid. Empty state with CTA.
 */
export const WellnessScoreCard: React.FC<WellnessScoreCardProps> = ({
  scores,
  onStartCheckin,
  className = '',
}) => {
  const [displayOverall, setDisplayOverall] = useState(0);

  const overall = scores?.overall_wellness_score ?? 0;
  const tier = getScoreTier(overall);
  const ringColor = TIER_COLORS[tier] ?? TIER_COLORS.attention;
  const tierLabel = TIER_LABELS[tier] ?? TIER_LABELS.attention;

  useEffect(() => {
    if (!scores) {
      setDisplayOverall(0);
      return;
    }
    const duration = 1200;
    const start = performance.now();
    const raf = (now: number) => {
      const elapsed = now - start;
      const t = Math.min(1, elapsed / duration);
      const eased = 1 - (1 - t) * (1 - t);
      setDisplayOverall(Math.round(overall * eased));
      if (t < 1) requestAnimationFrame(raf);
    };
    requestAnimationFrame(raf);
  }, [scores, overall]);

  if (!scores) {
    return (
      <div
        className={`
          rounded-2xl bg-slate-800/80 border border-slate-700 p-8
          flex flex-col items-center justify-center text-center min-h-[280px]
          ${className}
        `}
        role="region"
        aria-label="Wellness score"
      >
        <div className="text-slate-400 mb-4" aria-hidden>
          <ClipboardList className="w-14 h-14 mx-auto" strokeWidth={1.5} />
        </div>
        <h3 className="text-lg font-semibold text-slate-200 mb-2">
          Complete your first check-in to see your wellness score
        </h3>
        <p className="text-slate-400 text-sm mb-6 max-w-sm">
          Track physical, mental, relationship, and financial wellness in one place.
        </p>
        {onStartCheckin && (
          <button
            type="button"
            onClick={onStartCheckin}
            className="
              min-h-[44px] px-6 rounded-xl font-semibold
              bg-violet-600 text-white hover:bg-violet-500
              focus:outline-none focus:ring-2 focus:ring-violet-500 focus:ring-offset-2 focus:ring-offset-slate-900
            "
            aria-label="Start weekly check-in"
          >
            Start check-in
          </button>
        )}
      </div>
    );
  }

  const weekLabel = formatWeekLabel(scores.week_ending_date);
  const overallChange = scores.overall_change ?? 0;

  return (
    <div
      className={`rounded-2xl bg-slate-800/80 border border-slate-700 p-6 ${className}`}
      role="region"
      aria-label="Wellness score"
    >
      {/* Hero: circular ring + overall score + change + week */}
      <div className="flex flex-col items-center mb-8">
        <div className="relative inline-flex items-center justify-center">
          <CircularProgressRing
            value={overall}
            size={160}
            strokeWidth={10}
            color={ringColor}
            trackColor="rgba(148, 163, 184, 0.2)"
            pulse
            animationDuration={1200}
            ariaLabel={`Overall wellness score: ${Math.round(overall)} out of 100, ${tierLabel}`}
          />
          <div
            className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none"
            aria-hidden
          >
            <span
              className="text-4xl font-bold tabular-nums"
              style={{ color: ringColor }}
            >
              {displayOverall}
            </span>
            <span className="text-slate-400 text-sm font-medium mt-0.5">
              {tierLabel}
            </span>
          </div>
        </div>
        <div className="mt-4 flex flex-col items-center gap-1">
          <ScoreChangeIndicator
            change={overallChange}
            ariaLabel={
              overallChange > 0
                ? `Up ${overallChange} from last week`
                : overallChange < 0
                  ? `Down ${Math.abs(overallChange)} from last week`
                  : 'No change from last week'
            }
          />
          <p className="text-slate-500 text-sm">Week of {weekLabel}</p>
        </div>
      </div>

      {/* Category grid: 2x2 mobile, 4x1 desktop */}
      <div
        className="grid grid-cols-2 md:grid-cols-4 gap-3"
        role="list"
        aria-label="Wellness categories"
      >
        <div role="listitem">
          <CategoryScoreCard
            label="Physical"
            icon="💪"
            score={scores.physical_score}
            change={scores.physical_change}
          />
        </div>
        <div role="listitem">
          <CategoryScoreCard
            label="Mental"
            icon="🧠"
            score={scores.mental_score}
            change={scores.mental_change}
          />
        </div>
        <div role="listitem">
          <CategoryScoreCard
            label="Relational"
            icon="❤️"
            score={scores.relational_score}
            change={scores.relational_change}
          />
        </div>
        <div role="listitem">
          <CategoryScoreCard
            label="Financial Feel"
            icon="💰"
            score={scores.financial_feeling_score}
            change={scores.financial_feeling_change ?? 0}
          />
        </div>
      </div>
    </div>
  );
};

export default WellnessScoreCard;
