import React from 'react';

export interface SpiritScoreCardProps {
  score: number;
  percentile: number;
  change: number;
}

export const SpiritScoreCard: React.FC<SpiritScoreCardProps> = ({ score, percentile, change }) => {
  const changeRounded = Math.round(change);
  const changeLabel =
    changeRounded > 0 ? `+${changeRounded}` : changeRounded < 0 ? `${changeRounded}` : '+0';

  return (
    <div className="rounded-xl bg-[#0f172a] px-6 py-6 text-[#f8fafc] shadow-md">
      <p className="text-xs font-medium uppercase tracking-wide text-slate-400">Spirit score</p>
      <div className="mt-2 flex items-baseline gap-1">
        <span className="font-display text-5xl font-semibold tabular-nums text-[#C4A064] sm:text-6xl">
          {Math.round(Math.min(100, Math.max(0, score)))}
        </span>
        <span className="text-lg font-medium text-slate-400">/ 100</span>
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        <span className="inline-flex rounded-full border border-[#C4A064]/40 bg-[#C4A064]/10 px-3 py-1 text-xs font-semibold text-[#C4A064]">
          Top {Math.min(99, Math.max(1, Math.round(percentile)))}% of users
        </span>
        <span className="inline-flex rounded-full border border-slate-600 bg-slate-800/80 px-3 py-1 text-xs font-semibold text-slate-200">
          {changeLabel} pts this month
        </span>
      </div>
      <p className="mt-4 text-xs leading-relaxed text-slate-400">
        Based on consistency, duration, mood lift, and correlation strength over 30 days.
      </p>
    </div>
  );
};
