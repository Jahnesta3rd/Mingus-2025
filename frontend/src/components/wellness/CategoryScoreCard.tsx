import React from 'react';
import { ScoreChangeIndicator } from './ScoreChangeIndicator';

export type ScoreTier = 'thriving' | 'growing' | 'building' | 'attention';

const TIER_COLORS: Record<ScoreTier, string> = {
  thriving: '#10B981',
  growing: '#F59E0B',
  building: '#F97316',
  attention: '#EF4444',
};

export function getScoreTier(score: number): ScoreTier {
  if (score >= 75) return 'thriving';
  if (score >= 50) return 'growing';
  if (score >= 25) return 'building';
  return 'attention';
}

export interface CategoryScoreCardProps {
  /** Category label (e.g. "Physical") */
  label: string;
  /** Emoji or icon character */
  icon: string;
  /** Score 0-100 */
  score: number;
  /** Week-over-week change */
  change: number;
  className?: string;
}

/**
 * Individual category display: icon, label, score, mini change indicator.
 * Left border color matches score tier (green/yellow/orange/red).
 */
export const CategoryScoreCard: React.FC<CategoryScoreCardProps> = ({
  label,
  icon,
  score,
  change,
  className = '',
}) => {
  const tier = getScoreTier(score);
  const borderColor = TIER_COLORS[tier];

  return (
    <div
      className={`
        relative rounded-xl bg-slate-800/80 p-4
        border border-slate-700
        focus-within:ring-2 focus-within:ring-violet-500/50 focus-within:ring-offset-2 focus-within:ring-offset-slate-900
        ${className}
      `}
      style={{ borderLeftWidth: '4px', borderLeftColor: borderColor }}
      role="article"
      aria-label={`${label}: ${Math.round(score)} out of 100`}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-2xl shrink-0" aria-hidden>
            {icon}
          </span>
          <span className="text-slate-200 font-semibold truncate">{label}</span>
        </div>
        <div className="flex flex-col items-end shrink-0">
          <span
            className="text-xl font-bold tabular-nums"
            style={{ color: borderColor }}
          >
            {Math.round(score)}
          </span>
          <ScoreChangeIndicator change={change} compact ariaLabel={`${label} change: ${change >= 0 ? '+' : ''}${change} from last week`} />
        </div>
      </div>
    </div>
  );
};

export default CategoryScoreCard;
