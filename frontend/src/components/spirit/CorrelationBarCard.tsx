import React from 'react';

export interface SpiritCorrelationBarItem {
  label: string;
  value: number;
  direction: 'positive' | 'negative';
  strength: 'strong' | 'moderate' | 'weak';
}

const strengthBadgeClass: Record<SpiritCorrelationBarItem['strength'], string> = {
  strong: 'bg-emerald-100 text-emerald-800 ring-1 ring-emerald-200',
  moderate: 'bg-amber-100 text-amber-900 ring-1 ring-amber-200',
  weak: 'bg-slate-100 text-slate-600 ring-1 ring-slate-200',
};

const strengthLabel: Record<SpiritCorrelationBarItem['strength'], string> = {
  strong: 'Strong',
  moderate: 'Moderate',
  weak: 'Weak',
};

export interface CorrelationBarCardProps {
  correlations: SpiritCorrelationBarItem[];
}

export function CorrelationBarCard({ correlations }: CorrelationBarCardProps) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm sm:p-6">
      <ul className="space-y-6">
        {correlations.map((c) => {
          const widthPct = `${Math.min(100, Math.abs(c.value) * 100)}%`;
          const fillClass =
            c.direction === 'positive' ? 'bg-[#C4A064]' : 'bg-[#2A7A52]';
          return (
            <li key={c.label}>
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span className="text-sm font-medium text-[#0f172a]">{c.label}</span>
                <span
                  className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-semibold ${strengthBadgeClass[c.strength]}`}
                >
                  {strengthLabel[c.strength]}
                </span>
              </div>
              <div className="mt-2">
                <div className="relative h-3 w-full overflow-hidden rounded-full bg-slate-100">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${fillClass}`}
                    style={{ width: widthPct }}
                    role="progressbar"
                    aria-valuenow={Math.round(Math.abs(c.value) * 100)}
                    aria-valuemin={0}
                    aria-valuemax={100}
                    aria-label={`${c.label} correlation strength`}
                  />
                </div>
                <div className="mt-1 flex justify-between text-[10px] font-medium uppercase tracking-wide text-slate-400">
                  <span>No correlation</span>
                  <span>Perfect correlation</span>
                </div>
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
