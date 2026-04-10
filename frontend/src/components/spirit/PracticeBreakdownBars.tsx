import React from 'react';

export type PracticeBreakdownEntry = { type: string; count: number; pct: number };

export interface PracticeBreakdownBarsProps {
  breakdown: PracticeBreakdownEntry[];
}

const BAR_COLORS: Record<string, string> = {
  prayer: 'bg-amber-500',
  meditation: 'bg-emerald-600',
  gratitude: 'bg-[#0f172a]',
  affirmation: 'bg-slate-500',
};

function barColor(type: string): string {
  const key = type.toLowerCase();
  return BAR_COLORS[key] ?? 'bg-slate-400';
}

function labelFor(type: string): string {
  const t = type.toLowerCase();
  if (t === 'affirmation') return 'Affirmations';
  return t.charAt(0).toUpperCase() + t.slice(1);
}

export const PracticeBreakdownBars: React.FC<PracticeBreakdownBarsProps> = ({ breakdown }) => {
  if (!breakdown.length) {
    return (
      <p className="text-center text-sm text-slate-500">
        Practice mix will appear after you log a few check-ins.
      </p>
    );
  }

  return (
    <ul className="space-y-4">
      {breakdown.map((row) => (
        <li key={row.type}>
          <div className="mb-1 flex items-baseline justify-between gap-2 text-sm">
            <span className="font-medium text-[#0f172a]">{labelFor(row.type)}</span>
            <span className="tabular-nums text-slate-600">{Math.round(row.pct)}%</span>
          </div>
          <div className="h-2.5 w-full overflow-hidden rounded-full bg-slate-100">
            <div
              className={`h-full rounded-full transition-[width] duration-500 ${barColor(row.type)}`}
              style={{ width: `${Math.min(100, Math.max(0, row.pct))}%` }}
            />
          </div>
        </li>
      ))}
    </ul>
  );
};
